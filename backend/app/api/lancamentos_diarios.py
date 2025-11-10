from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.auth import User
from app.models.lancamento_diario import (
    LancamentoDiarioCreate,
    LancamentoDiarioUpdate,
    TransactionType,
)
from app.services.dependencies import get_current_active_user
from app.services.lancamento_diario_service import LancamentoDiarioService

router = APIRouter()


def _user_context(user: User) -> tuple[str, str]:
    tenant_id = str(user.tenant_id)
    business_unit_id = getattr(user, "business_unit_id", None)
    if not business_unit_id:
        raise HTTPException(
            status_code=400,
            detail="Usuário precisa selecionar uma unidade de negócio antes de acessar lançamentos diários.",
        )
    return tenant_id, str(business_unit_id)

@router.post("/api/v1/lancamentos-diarios", response_model=dict)
async def create_lancamento_diario(
    lancamento_data: LancamentoDiarioCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Criar novo lançamento diário"""
    try:
        tenant_id, business_unit_id = _user_context(current_user)
        result = LancamentoDiarioService.create_lancamento(
            db=db,
            lancamento_data=lancamento_data,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id,
            user_id=str(current_user.id)
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/api/v1/lancamentos-diarios", response_model=dict)
async def get_lancamentos_diarios(
    start_date: Optional[str] = Query(None, description="Data inicial (ISO format)"),
    end_date: Optional[str] = Query(None, description="Data final (ISO format)"),
    conta_id: Optional[str] = Query(None, description="ID da conta"),
    subgrupo_id: Optional[str] = Query(None, description="ID do subgrupo"),
    grupo_id: Optional[str] = Query(None, description="ID do grupo"),
    transaction_type: Optional[TransactionType] = Query(None, description="Tipo de transação"),
    page: int = Query(1, ge=1, description="Página"),
    per_page: int = Query(50, ge=1, le=100, description="Itens por página"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Buscar lançamentos diários com filtros"""
    try:
        # Converter datas se fornecidas
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        tenant_id, business_unit_id = _user_context(current_user)
        result = LancamentoDiarioService.get_lancamentos(
            db=db,
            tenant_id=tenant_id,
            business_unit_id=business_unit_id,
            start_date=start_dt,
            end_date=end_dt,
            conta_id=conta_id,
            subgrupo_id=subgrupo_id,
            grupo_id=grupo_id,
            transaction_type=transaction_type,
            page=page,
            per_page=per_page
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/api/v1/lancamentos-diarios/plano-contas", response_model=dict)
async def get_plano_contas_hierarchy(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Buscar hierarquia do plano de contas para formulário"""
    try:
        tenant_id, _ = _user_context(current_user)
        result = LancamentoDiarioService.get_plano_contas_hierarchy(
            db=db,
            tenant_id=tenant_id
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/api/v1/lancamentos-diarios/{lancamento_id}", response_model=dict)
async def get_lancamento_diario(
    lancamento_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Buscar lançamento diário específico"""
    try:
        from app.models.lancamento_diario import LancamentoDiario
        
        tenant_id, business_unit_id = _user_context(current_user)
        lancamento = db.query(LancamentoDiario).filter(
            LancamentoDiario.id == lancamento_id,
            LancamentoDiario.tenant_id == tenant_id,
            LancamentoDiario.business_unit_id == business_unit_id
        ).first()
        
        if not lancamento:
            raise HTTPException(status_code=404, detail="Lançamento não encontrado")
        
        return {
            "success": True,
            "lancamento": {
                "id": lancamento.id,
                "data_movimentacao": lancamento.data_movimentacao.isoformat(),
                "valor": str(lancamento.valor),
                "liquidacao": lancamento.liquidacao.isoformat() if lancamento.liquidacao else None,
                "observacoes": lancamento.observacoes,
                "conta_id": lancamento.conta_id,
                "conta_nome": lancamento.conta.name,
                "conta_codigo": lancamento.conta.code,
                "subgrupo_id": lancamento.subgrupo_id,
                "subgrupo_nome": lancamento.subgrupo.name,
                "subgrupo_codigo": lancamento.subgrupo.code,
                "grupo_id": lancamento.grupo_id,
                "grupo_nome": lancamento.grupo.name,
                "grupo_codigo": lancamento.grupo.code,
                "transaction_type": lancamento.transaction_type.value,
                "status": lancamento.status.value,
                "tenant_id": lancamento.tenant_id,
                "business_unit_id": lancamento.business_unit_id,
                "created_by": lancamento.created_by,
                "is_active": lancamento.is_active,
                "created_at": lancamento.created_at.isoformat(),
                "updated_at": lancamento.updated_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.put("/api/v1/lancamentos-diarios/{lancamento_id}", response_model=dict)
async def update_lancamento_diario(
    lancamento_id: str,
    lancamento_data: LancamentoDiarioUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Atualizar lançamento diário"""
    try:
        from app.models.lancamento_diario import LancamentoDiario
        tenant_id, business_unit_id = _user_context(current_user)
        # Buscar lançamento
        lancamento = db.query(LancamentoDiario).filter(
            LancamentoDiario.id == lancamento_id,
            LancamentoDiario.tenant_id == tenant_id,
            LancamentoDiario.business_unit_id == business_unit_id
        ).first()
        
        if not lancamento:
            raise HTTPException(status_code=404, detail="Lançamento não encontrado")
        
        # Atualizar campos fornecidos
        if lancamento_data.data_movimentacao:
            lancamento.data_movimentacao = datetime.fromisoformat(lancamento_data.data_movimentacao.replace('Z', '+00:00'))
        if lancamento_data.valor:
            lancamento.valor = lancamento_data.valor
        if lancamento_data.liquidacao:
            lancamento.liquidacao = datetime.fromisoformat(lancamento_data.liquidacao.replace('Z', '+00:00'))
        if lancamento_data.observacoes is not None:
            lancamento.observacoes = lancamento_data.observacoes
        if lancamento_data.status:
            lancamento.status = lancamento_data.status
        
        # Se mudou conta/subgrupo/grupo, validar consistência
        if any([lancamento_data.conta_id, lancamento_data.subgrupo_id, lancamento_data.grupo_id]):
            conta_id = lancamento_data.conta_id or lancamento.conta_id
            subgrupo_id = lancamento_data.subgrupo_id or lancamento.subgrupo_id
            grupo_id = lancamento_data.grupo_id or lancamento.grupo_id
            
            is_valid, message = LancamentoDiarioService.validate_plano_contas_consistency(
                db, conta_id, subgrupo_id, grupo_id, tenant_id
            )
            
            if not is_valid:
                raise HTTPException(status_code=400, detail=message)
            
            # Atualizar campos do plano de contas
            if lancamento_data.conta_id:
                lancamento.conta_id = lancamento_data.conta_id
            if lancamento_data.subgrupo_id:
                lancamento.subgrupo_id = lancamento_data.subgrupo_id
            if lancamento_data.grupo_id:
                lancamento.grupo_id = lancamento_data.grupo_id
                
                # Recalcular tipo de transação
                from app.models.chart_of_accounts import ChartAccountGroup
                grupo = db.query(ChartAccountGroup).filter(
                    ChartAccountGroup.id == lancamento_data.grupo_id
                ).first()
                
                if grupo:
                    lancamento.transaction_type = LancamentoDiarioService.determine_transaction_type(grupo.name)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Lançamento atualizado com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.delete("/api/v1/lancamentos-diarios/{lancamento_id}", response_model=dict)
async def delete_lancamento_diario(
    lancamento_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Excluir lançamento diário (soft delete)"""
    try:
        from app.models.lancamento_diario import LancamentoDiario
        tenant_id, business_unit_id = _user_context(current_user)
        lancamento = db.query(LancamentoDiario).filter(
            LancamentoDiario.id == lancamento_id,
            LancamentoDiario.tenant_id == tenant_id,
            LancamentoDiario.business_unit_id == business_unit_id
        ).first()
        
        if not lancamento:
            raise HTTPException(status_code=404, detail="Lançamento não encontrado")
        
        lancamento.is_active = False
        db.commit()
        
        return {
            "success": True,
            "message": "Lançamento excluído com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/api/v1/lancamentos-diarios/resumo", response_model=dict)
async def get_lancamentos_resumo(
    start_date: Optional[str] = Query(None, description="Data inicial (ISO format)"),
    end_date: Optional[str] = Query(None, description="Data final (ISO format)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Resumo dos lançamentos diários para dashboard"""
    try:
        from app.models.lancamento_diario import LancamentoDiario
        from sqlalchemy import func
        tenant_id, business_unit_id = _user_context(current_user)
        
        # Query base
        query = db.query(LancamentoDiario).filter(
            LancamentoDiario.tenant_id == tenant_id,
            LancamentoDiario.business_unit_id == business_unit_id,
            LancamentoDiario.is_active == True
        )
        
        # Aplicar filtros de data
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(LancamentoDiario.data_movimentacao >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(LancamentoDiario.data_movimentacao <= end_dt)
        
        # Calcular totais por tipo
        receitas = query.filter(LancamentoDiario.transaction_type == TransactionType.RECEITA).with_entities(func.sum(LancamentoDiario.valor)).scalar() or 0
        despesas = query.filter(LancamentoDiario.transaction_type == TransactionType.DESPESA).with_entities(func.sum(LancamentoDiario.valor)).scalar() or 0
        
        # Contar lançamentos
        total_lancamentos = query.count()
        
        return {
            "success": True,
            "resumo": {
                "total_lancamentos": total_lancamentos,
                "total_receitas": float(receitas),
                "total_despesas": float(despesas),
                "saldo_liquido": float(receitas - despesas)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
