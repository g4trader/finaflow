"""Admin endpoints for importing data from Google Sheets into the production database."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import User, Tenant, BusinessUnit
from app.services.dependencies import require_super_admin
from app.services.llm_plano_contas_importer import LLMPlanoContasImporter
from app.services.llm_sheet_importer import LLMSheetImporter


router = APIRouter(prefix="/admin", tags=["admin-import"])


class SpreadsheetImportPayload(BaseModel):
    spreadsheet_id: str = Field(..., description="Google Sheets spreadsheet ID")
    tenant_id: Optional[str] = Field(
        default=None, description="Tenant ID to associate the imported data with"
    )
    business_unit_id: Optional[str] = Field(
        default=None, description="Business Unit ID to associate the imported data with"
    )


def _resolve_tenant_and_bu(
    payload: SpreadsheetImportPayload,
    current_user: User,
    db: Session,
) -> tuple[str, str]:
    """
    Resolve tenant and business unit IDs to be used during the import.
    """
    tenant_id = payload.tenant_id or (str(current_user.tenant_id) if current_user.tenant_id else None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id é obrigatório para importação.")

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} não encontrado.")

    business_unit_id = payload.business_unit_id or (
        str(current_user.business_unit_id) if current_user.business_unit_id else None
    )
    if not business_unit_id:
        business_unit = (
            db.query(BusinessUnit)
            .filter(BusinessUnit.tenant_id == tenant_id)
            .order_by(BusinessUnit.created_at.asc())
            .first()
        )
        if not business_unit:
            raise HTTPException(
                status_code=404,
                detail="Nenhuma unidade de negócio encontrada para este tenant. Informe o business_unit_id.",
            )
        business_unit_id = str(business_unit.id)
    else:
        business_unit = (
            db.query(BusinessUnit)
            .filter(
                BusinessUnit.id == business_unit_id,
                BusinessUnit.tenant_id == tenant_id,
            )
            .first()
        )
        if not business_unit:
            raise HTTPException(
                status_code=404,
                detail=f"Business unit {business_unit_id} não encontrada para o tenant {tenant_id}.",
            )

    return tenant_id, business_unit_id


@router.post("/importar-plano-contas-planilha")
async def importar_plano_contas_planilha(
    payload: SpreadsheetImportPayload,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    importer = LLMPlanoContasImporter()
    if not importer.authenticate():
        raise HTTPException(status_code=500, detail="Falha na autenticação com Google Sheets.")

    tenant_id, business_unit_id = _resolve_tenant_and_bu(payload, current_user, db)

    result = importer.import_plano_contas(
        payload.spreadsheet_id,
        tenant_id,
        business_unit_id,
        db,
    )

    if not result.get("success"):
        return JSONResponse(
            status_code=500,
            content=jsonable_encoder(
                {
                    "success": False,
                    "message": result.get("error", "Erro desconhecido na importação"),
                    "details": result,
                }
            ),
        )

    return {
        "success": True,
        "message": "Plano de contas importado com sucesso",
        "details": result,
    }


@router.post("/importar-lancamentos-planilha")
async def importar_lancamentos_planilha(
    payload: SpreadsheetImportPayload,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    importer = LLMSheetImporter()
    if not importer.authenticate():
        raise HTTPException(status_code=500, detail="Falha na autenticação com Google Sheets.")

    tenant_id, business_unit_id = _resolve_tenant_and_bu(payload, current_user, db)

    result = importer._import_daily_transactions(
        payload.spreadsheet_id,
        "Lançamento Diário",
        tenant_id,
        business_unit_id,
        db,
        str(current_user.id),
    )

    if not result.get("success"):
        return JSONResponse(
            status_code=500,
            content=jsonable_encoder(
                {
                    "success": False,
                    "message": result.get("error", "Erro desconhecido na importação"),
                    "details": result,
                }
            ),
        )

    return {
        "success": True,
        "message": "Lançamentos importados com sucesso",
        "count": result.get("count", 0),
    }


@router.post("/importar-previsoes-planilha")
async def importar_previsoes_planilha(
    payload: SpreadsheetImportPayload,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    importer = LLMSheetImporter()
    if not importer.authenticate():
        raise HTTPException(status_code=500, detail="Falha na autenticação com Google Sheets.")

    tenant_id, business_unit_id = _resolve_tenant_and_bu(payload, current_user, db)

    result = importer._import_forecast_transactions(
        payload.spreadsheet_id,
        "Lançamentos Previstos",
        tenant_id,
        business_unit_id,
        db,
        str(current_user.id),
    )

    if not result.get("success"):
        return JSONResponse(
            status_code=500,
            content=jsonable_encoder(
                {
                    "success": False,
                    "message": result.get("error", "Erro desconhecido na importação"),
                    "details": result,
                }
            ),
        )

    return {
        "success": True,
        "message": "Previsões importadas com sucesso",
        "count": result.get("count", 0),
    }


@router.post("/importar-google-sheets")
async def importar_google_sheets(
    payload: SpreadsheetImportPayload,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """
    Endpoint combinado para importar plano de contas, lançamentos diários e previsões de uma vez.
    """
    tenant_id, business_unit_id = _resolve_tenant_and_bu(payload, current_user, db)

    plano_result = await importar_plano_contas_planilha(payload, current_user, db)
    lanc_result = await importar_lancamentos_planilha(payload, current_user, db)
    previsoes_result = await importar_previsoes_planilha(payload, current_user, db)

    return {
        "success": True,
        "results": {
            "plano_contas": plano_result,
            "lancamentos": lanc_result,
            "previsoes": previsoes_result,
        },
        "tenant_id": tenant_id,
        "business_unit_id": business_unit_id,
    }

