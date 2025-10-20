"""
API endpoints para importação de dados
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

from app.database import get_db
from app.models.auth import User
from app.services.dependencies import get_current_active_user
from app.services.google_sheets_importer import google_sheets_importer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/import", tags=["import"])

class ImportRequest(BaseModel):
    """Modelo para requisição de importação"""
    spreadsheet_id: str = Field(..., description="ID da planilha Google Sheets")
    import_type: Optional[str] = Field("all", description="Tipo de importação: all, accounts, transactions, reports")
    validate_only: Optional[bool] = Field(False, description="Apenas validar dados sem importar")

class ImportResponse(BaseModel):
    """Modelo para resposta de importação"""
    success: bool
    message: str
    spreadsheet_id: str
    spreadsheet_title: Optional[str] = None
    sheets_processed: Optional[list] = None
    data_imported: Optional[Dict[str, int]] = None
    errors: Optional[list] = None
    import_id: Optional[str] = None

class ValidationResponse(BaseModel):
    """Modelo para resposta de validação"""
    success: bool
    spreadsheet_id: str
    spreadsheet_title: Optional[str] = None
    sheets_found: list
    data_structure: Dict[str, Any]
    validation_errors: Optional[list] = None

@router.post("/google-sheets", response_model=ImportResponse)
async def import_from_google_sheets(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Importar dados de uma planilha Google Sheets
    
    Args:
        request: Dados da requisição de importação
        background_tasks: Tarefas em background
        current_user: Usuário autenticado
        db: Sessão do banco de dados
    
    Returns:
        Resultado da importação
    """
    try:
        logger.info(f"🚀 Iniciando importação da planilha {request.spreadsheet_id} pelo usuário {current_user.username}")
        
        # Se for apenas validação, retornar resultado da validação
        if request.validate_only:
            validation_result = await validate_google_sheets_data(
                request.spreadsheet_id,
                current_user,
                db
            )
            return ImportResponse(
                success=validation_result.success,
                message="Validação concluída",
                spreadsheet_id=request.spreadsheet_id,
                spreadsheet_title=validation_result.spreadsheet_title,
                errors=validation_result.validation_errors
            )
        
        # Executar importação
        result = google_sheets_importer.import_from_spreadsheet(
            spreadsheet_id=request.spreadsheet_id,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id
        )
        
        if result.get("success"):
            # Calcular total de dados importados
            total_imported = sum(result.get("data_imported", {}).values())
            
            return ImportResponse(
                success=True,
                message=f"Importação concluída com sucesso! {total_imported} registros importados.",
                spreadsheet_id=request.spreadsheet_id,
                spreadsheet_title=result.get("spreadsheet_title"),
                sheets_processed=result.get("sheets_processed", []),
                data_imported=result.get("data_imported", {}),
                errors=result.get("errors", [])
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erro na importação: {result.get('error', 'Erro desconhecido')}"
            )
            
    except Exception as e:
        logger.error(f"❌ Erro na importação: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )

@router.post("/google-sheets/validate", response_model=ValidationResponse)
async def validate_google_sheets_data(
    spreadsheet_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Validar estrutura de dados de uma planilha Google Sheets
    
    Args:
        spreadsheet_id: ID da planilha Google Sheets
        current_user: Usuário autenticado
        db: Sessão do banco de dados
    
    Returns:
        Resultado da validação
    """
    try:
        logger.info(f"🔍 Validando planilha {spreadsheet_id} pelo usuário {current_user.username}")
        
        # Autenticar se necessário
        if not google_sheets_importer.authenticate():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro na autenticação com Google Sheets API"
            )
        
        # Obter informações da planilha
        spreadsheet_info = google_sheets_importer._get_spreadsheet_info(spreadsheet_id)
        if not spreadsheet_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível acessar a planilha. Verifique o ID e as permissões."
            )
        
        # Analisar estrutura das abas
        sheets_analysis = []
        validation_errors = []
        
        for sheet_name in spreadsheet_info.get("sheets", []):
            try:
                data = google_sheets_importer._get_sheet_data(spreadsheet_id, sheet_name)
                sheet_type = google_sheets_importer._determine_sheet_type(sheet_name, data)
                
                sheets_analysis.append({
                    "name": sheet_name,
                    "type": sheet_type,
                    "rows": len(data),
                    "columns": len(data[0]) if data else 0,
                    "headers": data[0] if data else []
                })
                
                # Validações específicas por tipo
                if sheet_type == "account_structure" and data:
                    headers = [str(h).lower() for h in data[0]]
                    if not any("conta" in h for h in headers):
                        validation_errors.append(f"Aba '{sheet_name}': Coluna 'Conta' não encontrada")
                    if not any("grupo" in h for h in headers):
                        validation_errors.append(f"Aba '{sheet_name}': Coluna 'Grupo' não encontrada")
                
                elif sheet_type == "transactions" and data:
                    headers = [str(h).lower() for h in data[0]]
                    if not any("data" in h for h in headers):
                        validation_errors.append(f"Aba '{sheet_name}': Coluna 'Data' não encontrada")
                    if not any("valor" in h for h in headers):
                        validation_errors.append(f"Aba '{sheet_name}': Coluna 'Valor' não encontrada")
                
            except Exception as e:
                validation_errors.append(f"Erro ao analisar aba '{sheet_name}': {str(e)}")
        
        return ValidationResponse(
            success=len(validation_errors) == 0,
            spreadsheet_id=spreadsheet_id,
            spreadsheet_title=spreadsheet_info.get("title"),
            sheets_found=[sheet["name"] for sheet in sheets_analysis],
            data_structure={
                "sheets_analysis": sheets_analysis,
                "total_sheets": len(sheets_analysis),
                "supported_sheets": len([s for s in sheets_analysis if s["type"] != "unknown"])
            },
            validation_errors=validation_errors if validation_errors else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na validação: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )

@router.get("/google-sheets/sample")
async def get_sample_spreadsheet_info():
    """
    Obter informações sobre a planilha de exemplo da metodologia Ana Paula
    
    Returns:
        Informações da planilha de exemplo
    """
    return {
        "spreadsheet_id": "1yyHuP6qjnK2Rd26yPPzaOqi_OJVeRjAJnewRIOJvFVY",
        "description": "Planilha de exemplo da metodologia Ana Paula",
        "sheets": [
            "Plano de contas",
            "Lançamento Diário", 
            "Lançamentos Previstos",
            "Fluxo de caixa-2025",
            "Previsão Fluxo de caixa-2025",
            "FC-diário-Jan2025",
            "FC-diário-Fev2025",
            "FC-diário-Mar2025",
            "FC-diário-Abr2025",
            "FC-diário-Mai2025",
            "FC-diário-Jun2025",
            "FC-diário-Jul2025",
            "FC-diário-Ago2025",
            "FC-diário-Set2025",
            "FC-diário-Out2025",
            "FC-diário-Nov2025",
            "FC-diário-Dez2025",
            "Resultados Anuais"
        ],
        "instructions": [
            "1. Use o ID da planilha para importar dados",
            "2. A aba 'Plano de contas' será usada para criar a estrutura de contas",
            "3. As abas 'Lançamento Diário' e 'Lançamentos Previstos' serão usadas para importar transações",
            "4. As abas de fluxo de caixa serão analisadas para relatórios futuros"
        ]
    }

@router.get("/status/{import_id}")
async def get_import_status(
    import_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Obter status de uma importação em andamento
    
    Args:
        import_id: ID da importação
        current_user: Usuário autenticado
    
    Returns:
        Status da importação
    """
    # Por enquanto, retornar status simulado
    # Em implementação futura, isso seria armazenado no banco de dados
    return {
        "import_id": import_id,
        "status": "completed",
        "progress": 100,
        "message": "Importação concluída",
        "created_at": "2025-09-28T00:00:00Z",
        "completed_at": "2025-09-28T00:05:00Z"
    }
