from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.auth import User, UserRole
from app.models.lancamento_previsto import (
    LancamentoPrevisto,
    LancamentoPrevistoCreate,
    LancamentoPrevistoUpdate,
    TransactionStatus,
    TransactionType,
)
from app.services.dependencies import get_current_active_user

router = APIRouter()


def _user_context(user: User) -> Tuple[str, Optional[str]]:
    """
    Obtém o tenant_id e business_unit_id do usuário.
    Para SUPER_ADMIN, permite acesso sem business_unit_id (retorna None).
    Para outros usuários, exige business_unit_id.
    """
    tenant_id = str(user.tenant_id)
    business_unit_id = getattr(user, "business_unit_id", None)
    
    if not business_unit_id:
        if user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=400,
                detail="Usuário precisa selecionar uma unidade de negócio antes de acessar lançamentos previstos.",
            )
        # Para super_admin sem BU, retornar None (permitir acesso sem filtro de BU)
        return tenant_id, None
    
    return tenant_id, str(business_unit_id)


def _classify_transaction_type(
    grupo_nome: str,
    subgrupo_nome: Optional[str] = None,
) -> TransactionType:
    grupo_lower = grupo_nome.lower()
    subgrupo_lower = (subgrupo_nome or "").lower()

    if any(keyword in grupo_lower for keyword in ["receita", "venda", "renda", "faturamento", "vendas"]):
        return TransactionType.RECEITA
    if any(keyword in grupo_lower for keyword in ["custo", "custos"]) or any(
        keyword in subgrupo_lower for keyword in ["custo", "custos", "mercadoria", "produto"]
    ):
        return TransactionType.CUSTO
    if any(keyword in grupo_lower for keyword in ["despesa", "gasto", "operacional", "administrativa"]) or any(
        keyword in subgrupo_lower for keyword in ["despesa", "gasto", "marketing", "administrativa"]
    ):
        return TransactionType.DESPESA
    return TransactionType.DESPESA


@router.get("/api/v1/lancamentos-previstos")
def list_lancamentos_previstos(
    skip: int = 0,
    limit: int = 10000,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_id: Optional[str] = None,
    subgroup_id: Optional[str] = None,
    account_id: Optional[str] = None,
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
    cost_center_id: Optional[str] = None,
    text_search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, object]:
    tenant_id, business_unit_id = _user_context(current_user)

    query = (
        db.query(LancamentoPrevisto)
        .options(
            joinedload(LancamentoPrevisto.conta),
            joinedload(LancamentoPrevisto.subgrupo),
            joinedload(LancamentoPrevisto.grupo),
        )
        .filter(
            LancamentoPrevisto.tenant_id == tenant_id,
            LancamentoPrevisto.is_active.is_(True),
        )
    )
    # Filtrar por business_unit_id apenas se fornecido
    if business_unit_id:
        query = query.filter(LancamentoPrevisto.business_unit_id == business_unit_id)
    
    # Aplicar filtros
    if start_date:
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        query = query.filter(LancamentoPrevisto.data_prevista >= start_dt)
    if end_date:
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        query = query.filter(LancamentoPrevisto.data_prevista <= end_dt)
    if group_id:
        query = query.filter(LancamentoPrevisto.grupo_id == group_id)
    if subgroup_id:
        query = query.filter(LancamentoPrevisto.subgrupo_id == subgroup_id)
    if account_id:
        query = query.filter(LancamentoPrevisto.conta_id == account_id)
    if transaction_type:
        from app.models.lancamento_previsto import TransactionType as PrevistoType
        try:
            tipo_enum = PrevistoType(transaction_type)
            query = query.filter(LancamentoPrevisto.transaction_type == tipo_enum)
        except ValueError:
            query = query.filter(LancamentoPrevisto.transaction_type == transaction_type)
    if status:
        from app.models.lancamento_previsto import TransactionStatus
        try:
            status_enum = TransactionStatus(status)
            query = query.filter(LancamentoPrevisto.status == status_enum)
        except ValueError:
            query = query.filter(LancamentoPrevisto.status == status)
    # cost_center_id - preparar campo mesmo se não implementado ainda
    # if cost_center_id:
    #     query = query.filter(LancamentoPrevisto.cost_center_id == cost_center_id)
    
    # Filtro de busca por texto (text_search)
    if text_search:
        from sqlalchemy import or_
        from app.models.chart_of_accounts import ChartAccount, ChartAccountSubgroup, ChartAccountGroup
        search_term = f"%{text_search.lower()}%"
        # Fazer joins para buscar nos nomes de conta/subgrupo/grupo
        query = query.outerjoin(ChartAccount, LancamentoPrevisto.conta_id == ChartAccount.id)\
                    .outerjoin(ChartAccountSubgroup, LancamentoPrevisto.subgrupo_id == ChartAccountSubgroup.id)\
                    .outerjoin(ChartAccountGroup, LancamentoPrevisto.grupo_id == ChartAccountGroup.id)\
                    .filter(
                        or_(
                            LancamentoPrevisto.observacoes.ilike(search_term),
                            ChartAccount.name.ilike(search_term),
                            ChartAccountSubgroup.name.ilike(search_term),
                            ChartAccountGroup.name.ilike(search_term)
                        )
                    )
    
    query = query.order_by(LancamentoPrevisto.data_prevista.desc())

    if limit > 0:
        query = query.offset(skip).limit(limit)

    previsoes = query.all()

    def _safe_name(obj, default: str = "N/A") -> str:
        return getattr(obj, "name", default) if obj else default

    def _safe_code(obj, default: str = "N/A") -> str:
        return getattr(obj, "code", default) if obj else default

    payload = [
        {
            "id": str(prev.id),
            "data_prevista": prev.data_prevista.isoformat(),
            "valor": float(prev.valor),
            "observacoes": prev.observacoes,
            "conta_id": str(prev.conta_id),
            "conta_nome": _safe_name(prev.conta),
            "conta_codigo": _safe_code(prev.conta),
            "subgrupo_id": str(prev.subgrupo_id),
            "subgrupo_nome": _safe_name(prev.subgrupo),
            "subgrupo_codigo": _safe_code(prev.subgrupo),
            "grupo_id": str(prev.grupo_id),
            "grupo_nome": _safe_name(prev.grupo),
            "grupo_codigo": _safe_code(prev.grupo),
            "transaction_type": (prev.transaction_type.value if prev.transaction_type else None),
            "status": prev.status.value if isinstance(prev.status, TransactionStatus) else str(prev.status),
            "created_at": prev.created_at.isoformat() if prev.created_at else None,
        }
        for prev in previsoes
    ]

    return {
        "success": True,
        "previsoes": payload,
        "total": len(payload),
    }


@router.post("/api/v1/lancamentos-previstos")
async def create_lancamento_previsto(
    previsao: LancamentoPrevistoCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, object]:
    tenant_id, business_unit_id = _user_context(current_user)
    
    # Para criar previsão, business_unit_id é obrigatório (mesmo para SUPER_ADMIN)
    if not business_unit_id:
        raise HTTPException(
            status_code=400,
            detail="É necessário selecionar uma unidade de negócio para criar previsões.",
        )

    from app.models.chart_of_accounts import ChartAccountGroup, ChartAccountSubgroup, ChartAccount

    # Validar hierarquia: grupo → subgrupo → conta
    grupo = (
        db.query(ChartAccountGroup)
        .filter(
            ChartAccountGroup.id == previsao.grupo_id,
            ChartAccountGroup.tenant_id.in_([tenant_id, None]),
        )
        .first()
    )
    if not grupo:
        raise HTTPException(status_code=400, detail="Grupo não encontrado ou não pertence ao tenant atual")

    subgrupo = (
        db.query(ChartAccountSubgroup)
        .filter(
            ChartAccountSubgroup.id == previsao.subgrupo_id,
            ChartAccountSubgroup.group_id == previsao.grupo_id,  # Validar que subgrupo pertence ao grupo
            ChartAccountSubgroup.tenant_id.in_([tenant_id, None]),
        )
        .first()
    )
    if not subgrupo:
        raise HTTPException(status_code=400, detail="Subgrupo não encontrado ou não pertence ao grupo informado")

    conta = (
        db.query(ChartAccount)
        .filter(
            ChartAccount.id == previsao.conta_id,
            ChartAccount.subgroup_id == previsao.subgrupo_id,  # Validar que conta pertence ao subgrupo
            ChartAccount.tenant_id.in_([tenant_id, None]),
        )
        .first()
    )
    if not conta:
        raise HTTPException(status_code=400, detail="Conta não encontrada ou não pertence ao subgrupo informado")

    transaction_type = _classify_transaction_type(grupo.name, subgrupo.name)

    data_prevista = datetime.fromisoformat(previsao.data_prevista.replace("Z", "+00:00"))

    novo = LancamentoPrevisto(
        data_prevista=data_prevista,
        valor=previsao.valor,
        observacoes=previsao.observacoes,
        conta_id=previsao.conta_id,
        subgrupo_id=previsao.subgrupo_id,
        grupo_id=previsao.grupo_id,
        transaction_type=transaction_type,
        status=TransactionStatus.PENDENTE,
        tenant_id=tenant_id,
        business_unit_id=business_unit_id,
        created_by=str(current_user.id),
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)

    return {
        "success": True,
        "message": "Previsão criada com sucesso",
        "previsao_id": str(novo.id),
        "transaction_type": transaction_type.value,
    }


@router.put("/api/v1/lancamentos-previstos/{previsao_id}")
async def update_lancamento_previsto(
    previsao_id: str,
    payload: LancamentoPrevistoUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, object]:
    tenant_id, business_unit_id = _user_context(current_user)

    query = (
        db.query(LancamentoPrevisto)
        .filter(
            LancamentoPrevisto.id == previsao_id,
            LancamentoPrevisto.tenant_id == tenant_id,
            LancamentoPrevisto.is_active.is_(True),
        )
    )
    # Filtrar por business_unit_id apenas se fornecido
    if business_unit_id:
        query = query.filter(LancamentoPrevisto.business_unit_id == business_unit_id)
    previsao = query.first()
    
    if not previsao:
        raise HTTPException(status_code=404, detail="Previsão não encontrada")

    if payload.data_prevista:
        previsao.data_prevista = datetime.fromisoformat(payload.data_prevista.replace("Z", "+00:00"))
    if payload.valor is not None:
        previsao.valor = payload.valor
    if payload.observacoes is not None:
        previsao.observacoes = payload.observacoes
    if payload.status:
        previsao.status = payload.status
    if payload.conta_id:
        previsao.conta_id = payload.conta_id
    if payload.subgrupo_id:
        previsao.subgrupo_id = payload.subgrupo_id
    if payload.grupo_id:
        previsao.grupo_id = payload.grupo_id

    # Validar hierarquia se grupo/subgrupo/conta foram alterados
    if payload.grupo_id or payload.subgrupo_id or payload.conta_id:
        from app.models.chart_of_accounts import ChartAccountGroup, ChartAccountSubgroup, ChartAccount
        
        final_grupo_id = payload.grupo_id or previsao.grupo_id
        final_subgrupo_id = payload.subgrupo_id or previsao.subgrupo_id
        final_conta_id = payload.conta_id or previsao.conta_id
        
        # Validar que subgrupo pertence ao grupo
        if payload.grupo_id or payload.subgrupo_id:
            subgrupo = db.query(ChartAccountSubgroup).filter(
                ChartAccountSubgroup.id == final_subgrupo_id,
                ChartAccountSubgroup.group_id == final_grupo_id,
                ChartAccountSubgroup.tenant_id.in_([tenant_id, None])
            ).first()
            if not subgrupo:
                raise HTTPException(status_code=400, detail="Subgrupo não pertence ao grupo informado")
        
        # Validar que conta pertence ao subgrupo
        if payload.conta_id or payload.subgrupo_id:
            conta = db.query(ChartAccount).filter(
                ChartAccount.id == final_conta_id,
                ChartAccount.subgroup_id == final_subgrupo_id,
                ChartAccount.tenant_id.in_([tenant_id, None])
            ).first()
            if not conta:
                raise HTTPException(status_code=400, detail="Conta não pertence ao subgrupo informado")
        
        # Recalcular transaction_type se grupo mudou
        if payload.grupo_id:
            grupo = db.query(ChartAccountGroup).filter(
                ChartAccountGroup.id == final_grupo_id,
                ChartAccountGroup.tenant_id.in_([tenant_id, None])
            ).first()
            subgrupo = db.query(ChartAccountSubgroup).filter(
                ChartAccountSubgroup.id == final_subgrupo_id
            ).first() if final_subgrupo_id else None
            if grupo:
                previsao.transaction_type = _classify_transaction_type(grupo.name, subgrupo.name if subgrupo else None)

    previsao.updated_at = datetime.utcnow()

    db.commit()

    return {
        "success": True,
        "message": "Previsão atualizada com sucesso",
    }


@router.delete("/api/v1/lancamentos-previstos/{previsao_id}")
async def delete_lancamento_previsto(
    previsao_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, object]:
    tenant_id, business_unit_id = _user_context(current_user)

    query = (
        db.query(LancamentoPrevisto)
        .filter(
            LancamentoPrevisto.id == previsao_id,
            LancamentoPrevisto.tenant_id == tenant_id,
            LancamentoPrevisto.is_active.is_(True),
        )
    )
    # Filtrar por business_unit_id apenas se fornecido
    if business_unit_id:
        query = query.filter(LancamentoPrevisto.business_unit_id == business_unit_id)
    previsao = query.first()
    
    if not previsao:
        raise HTTPException(status_code=404, detail="Previsão não encontrada")

    previsao.is_active = False
    previsao.updated_at = datetime.utcnow()

    db.commit()

    return {
        "success": True,
        "message": "Previsão removida com sucesso",
    }
