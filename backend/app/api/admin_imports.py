"""Admin endpoints for importing data from Google Sheets into the production database."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import delete

from app.database import get_db
from app.models.auth import User, Tenant, BusinessUnit
from app.services.dependencies import require_super_admin
from app.services.llm_plano_contas_importer import LLMPlanoContasImporter
from app.services.llm_sheet_importer import LLMSheetImporter

from app.models.lancamento_diario import LancamentoDiario
from app.models.lancamento_previsto import LancamentoPrevisto
from app.models.chart_of_accounts import (
    ChartAccount,
    ChartAccountSubgroup,
    ChartAccountGroup,
    BusinessUnitChartAccount,
)
from app.models.caixa import Caixa
from app.models.conta_bancaria import ContaBancaria
from app.models.investimento import Investimento


router = APIRouter(prefix="/admin", tags=["admin-import"])


class SpreadsheetImportPayload(BaseModel):
    spreadsheet_id: str = Field(..., description="Google Sheets spreadsheet ID")
    tenant_id: Optional[str] = Field(
        default=None, description="Tenant ID to associate the imported data with"
    )
    business_unit_id: Optional[str] = Field(
        default=None, description="Business Unit ID to associate the imported data with"
    )


class ResetDataPayload(BaseModel):
    tenant_id: str = Field(..., description="Tenant ID whose data must be wiped")
    business_unit_id: str = Field(..., description="Business unit whose data must be wiped")
    wipe_chart_of_accounts: bool = Field(
        default=True,
        description="Remove também o plano de contas associado antes de reimportar.",
    )
    wipe_financial_assets: bool = Field(
        default=True,
        description="Remove registros de contas bancárias, caixas e investimentos vinculados.",
    )


class ResetSummary(BaseModel):
    lancamentos_diarios: int
    lancamentos_previstos: int
    chart_accounts: int
    chart_subgroups: int
    chart_groups: int
    bu_chart_accounts: int
    contas_bancarias: int
    caixas: int
    investimentos: int


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


@router.post("/limpar-dados")
async def limpar_dados(
    payload: ResetDataPayload,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> Dict[str, object]:
    """Remove dados importados previamente para permitir nova carga limpa."""

    tenant_id = payload.tenant_id
    business_unit_id = payload.business_unit_id

    summary = ResetSummary(
        lancamentos_diarios=0,
        lancamentos_previstos=0,
        chart_accounts=0,
        chart_subgroups=0,
        chart_groups=0,
        bu_chart_accounts=0,
        contas_bancarias=0,
        caixas=0,
        investimentos=0,
    )

    try:
        # Lançamentos previstos e diários
        summary.lancamentos_previstos = db.query(LancamentoPrevisto).filter(
            LancamentoPrevisto.tenant_id == tenant_id,
            LancamentoPrevisto.business_unit_id == business_unit_id,
        ).delete(synchronize_session=False)

        summary.lancamentos_diarios = db.query(LancamentoDiario).filter(
            LancamentoDiario.tenant_id == tenant_id,
            LancamentoDiario.business_unit_id == business_unit_id,
        ).delete(synchronize_session=False)

        # Plano de contas
        if payload.wipe_chart_of_accounts:
            summary.bu_chart_accounts = db.query(BusinessUnitChartAccount).filter(
                BusinessUnitChartAccount.business_unit_id == business_unit_id
            ).delete(synchronize_session=False)

            summary.chart_accounts = db.query(ChartAccount).filter(
                ChartAccount.tenant_id.in_([tenant_id, None])
            ).delete(synchronize_session=False)

            summary.chart_subgroups = db.query(ChartAccountSubgroup).filter(
                ChartAccountSubgroup.tenant_id.in_([tenant_id, None])
            ).delete(synchronize_session=False)

            summary.chart_groups = db.query(ChartAccountGroup).filter(
                ChartAccountGroup.tenant_id.in_([tenant_id, None])
            ).delete(synchronize_session=False)

        if payload.wipe_financial_assets:
            summary.contas_bancarias = db.query(ContaBancaria).filter(
                ContaBancaria.tenant_id == tenant_id,
                ContaBancaria.business_unit_id == business_unit_id,
            ).delete(synchronize_session=False)

            summary.caixas = db.query(Caixa).filter(
                Caixa.tenant_id == tenant_id,
                Caixa.business_unit_id == business_unit_id,
            ).delete(synchronize_session=False)

            summary.investimentos = db.query(Investimento).filter(
                Investimento.tenant_id == tenant_id,
                Investimento.business_unit_id == business_unit_id,
            ).delete(synchronize_session=False)

        db.commit()

        return {
            "success": True,
            "summary": summary.dict(),
        }

    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao limpar dados: {exc}") from exc


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

