from typing import Dict, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
# from app.models.lancamento_diario import (
#     LancamentoDiario, 
#     TransactionType, 
#     TransactionStatus,
#     LancamentoDiarioCreate,
#     LancamentoDiarioUpdate
# )
from app.models.chart_of_accounts import ChartAccount, ChartAccountSubgroup, ChartAccountGroup
from app.models.lancamento_diario import (
    LancamentoDiario,
    LancamentoDiarioCreate,
    LancamentoDiarioUpdate,
    TransactionStatus,
    TransactionType,
)

class LancamentoDiarioService:
    """Serviço para gerenciar lançamentos diários"""
    
    @staticmethod
    def determine_transaction_type(grupo_nome: str) -> TransactionType:
        """Determina o tipo de transação baseado no nome do grupo"""
        grupo_lower = grupo_nome.lower()
        
        if any(keyword in grupo_lower for keyword in ['receita', 'venda', 'renda']):
            return TransactionType.RECEITA
        elif any(keyword in grupo_lower for keyword in ['despesa', 'custo', 'gasto']):
            return TransactionType.DESPESA
        elif any(keyword in grupo_lower for keyword in ['ativo', 'bem', 'imobilizado']):
            return TransactionType.ATIVO
        elif any(keyword in grupo_lower for keyword in ['passivo', 'dívida', 'obrigação']):
            return TransactionType.PASSIVO
        elif any(keyword in grupo_lower for keyword in ['patrimônio', 'capital', 'lucro']):
            return TransactionType.PATRIMONIO_LIQUIDO
        else:
            # Default baseado no valor
            return TransactionType.DESPESA
    
    @staticmethod
    def validate_plano_contas_consistency(
        db: Session, 
        conta_id: str, 
        subgrupo_id: str, 
        grupo_id: str,
        tenant_id: str
    ) -> Tuple[bool, str]:
        """Valida se conta, subgrupo e grupo estão consistentes"""
        try:
            # Buscar conta
            conta = db.query(ChartAccount).filter(
                ChartAccount.id == conta_id,
                ChartAccount.tenant_id == tenant_id
            ).first()
            
            if not conta:
                return False, "Conta não encontrada"
            
            # Buscar subgrupo
            subgrupo = db.query(ChartAccountSubgroup).filter(
                ChartAccountSubgroup.id == subgrupo_id,
                ChartAccountSubgroup.tenant_id == tenant_id
            ).first()
            
            if not subgrupo:
                return False, "Subgrupo não encontrado"
            
            # Buscar grupo
            grupo = db.query(ChartAccountGroup).filter(
                ChartAccountGroup.id == grupo_id,
                ChartAccountGroup.tenant_id == tenant_id
            ).first()
            
            if not grupo:
                return False, "Grupo não encontrado"
            
            # Validar hierarquia
            if conta.subgroup_id != subgrupo_id:
                return False, "Conta não pertence ao subgrupo especificado"
            
            if subgrupo.group_id != grupo_id:
                return False, "Subgrupo não pertence ao grupo especificado"
            
            return True, "OK"
            
        except Exception as e:
            return False, f"Erro na validação: {str(e)}"
    
    @staticmethod
    def create_lancamento(
        db: Session, 
        lancamento_data: LancamentoDiarioCreate,
        tenant_id: str,
        business_unit_id: str,
        user_id: str
    ) -> Dict:
        """Cria um novo lançamento diário"""
        try:
            # Validar consistência do plano de contas
            is_valid, message = LancamentoDiarioService.validate_plano_contas_consistency(
                db, lancamento_data.conta_id, lancamento_data.subgrupo_id, 
                lancamento_data.grupo_id, tenant_id
            )
            
            if not is_valid:
                return {"success": False, "message": message}
            
            # Buscar informações do grupo para determinar tipo de transação
            grupo = db.query(ChartAccountGroup).filter(
                ChartAccountGroup.id == lancamento_data.grupo_id
            ).first()
            
            transaction_type = LancamentoDiarioService.determine_transaction_type(grupo.name)
            
            # Converter datas
            data_movimentacao = datetime.fromisoformat(lancamento_data.data_movimentacao.replace('Z', '+00:00'))
            liquidacao = None
            if lancamento_data.liquidacao:
                liquidacao = datetime.fromisoformat(lancamento_data.liquidacao.replace('Z', '+00:00'))
            
            # Criar lançamento
            lancamento = LancamentoDiario(
                data_movimentacao=data_movimentacao,
                valor=lancamento_data.valor,
                liquidacao=liquidacao,
                observacoes=lancamento_data.observacoes,
                conta_id=lancamento_data.conta_id,
                subgrupo_id=lancamento_data.subgrupo_id,
                grupo_id=lancamento_data.grupo_id,
                transaction_type=transaction_type,
                status=TransactionStatus.PENDENTE,
                tenant_id=tenant_id,
                business_unit_id=business_unit_id,
                created_by=user_id
            )
            
            db.add(lancamento)
            db.flush()
            
            return {
                "success": True, 
                "message": "Lançamento criado com sucesso",
                "lancamento_id": lancamento.id
            }
            
        except Exception as e:
            return {"success": False, "message": f"Erro ao criar lançamento: {str(e)}"}
    
    @staticmethod
    def get_lancamentos(
        db: Session,
        tenant_id: str,
        business_unit_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        conta_id: Optional[str] = None,
        subgrupo_id: Optional[str] = None,
        grupo_id: Optional[str] = None,
        transaction_type: Optional[TransactionType] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict:
        """Busca lançamentos diários com filtros"""
        try:
            from sqlalchemy.orm import joinedload
            from app.models.lancamento_diario import LancamentoDiario as LD
            
            query = (
                db.query(LD)
                .options(
                    joinedload(LD.conta),
                    joinedload(LD.subgrupo),
                    joinedload(LD.grupo),
                )
                .filter(
                    LD.tenant_id == tenant_id,
                    LD.business_unit_id == business_unit_id,
                    LD.is_active.is_(True),
                )
            )
            
            if start_date:
                query = query.filter(LD.data_movimentacao >= start_date)
            if end_date:
                query = query.filter(LD.data_movimentacao <= end_date)
            if conta_id:
                query = query.filter(LD.conta_id == conta_id)
            if subgrupo_id:
                query = query.filter(LD.subgrupo_id == subgrupo_id)
            if grupo_id:
                query = query.filter(LD.grupo_id == grupo_id)
            if transaction_type:
                value = transaction_type.value if hasattr(transaction_type, "value") else str(transaction_type)
                query = query.filter(LD.transaction_type == value)
            
            total = query.count()
            offset = (page - 1) * per_page
            lancamentos = (
                query.order_by(LD.data_movimentacao.desc(), LD.created_at.desc())
                .offset(offset)
                .limit(per_page)
                .all()
            )
            
            # Converter para response
            lancamentos_response = []
            for item in lancamentos:
                conta = item.conta
                subgrupo = item.subgrupo
                grupo = item.grupo
                lancamentos_response.append({
                    "id": item.id,
                    "data_movimentacao": item.data_movimentacao.isoformat() if item.data_movimentacao else None,
                    "valor": str(item.valor),
                    "liquidacao": item.liquidacao.isoformat() if item.liquidacao else None,
                    "observacoes": item.observacoes,
                    "conta_id": item.conta_id,
                    "conta_nome": conta.name if conta else None,
                    "conta_codigo": conta.code if conta else None,
                    "subgrupo_id": item.subgrupo_id,
                    "subgrupo_nome": subgrupo.name if subgrupo else None,
                    "subgrupo_codigo": subgrupo.code if subgrupo else None,
                    "grupo_id": item.grupo_id,
                    "grupo_nome": grupo.name if grupo else None,
                    "grupo_codigo": grupo.code if grupo else None,
                    "transaction_type": item.transaction_type.value if hasattr(item.transaction_type, "value") else item.transaction_type,
                    "status": item.status.value if hasattr(item.status, "value") else item.status,
                    "tenant_id": item.tenant_id,
                    "business_unit_id": item.business_unit_id,
                    "created_by": item.created_by,
                    "is_active": item.is_active,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None
                })
            
            return {
                "success": True,
                "lancamentos": lancamentos_response,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
            
        except Exception as e:
            return {"success": False, "message": f"Erro ao buscar lançamentos: {str(e)}"}
    
    @staticmethod
    def get_plano_contas_hierarchy(db: Session, tenant_id: str) -> Dict:
        """Busca hierarquia completa do plano de contas para o formulário"""
        try:
            # Buscar grupos
            grupos = db.query(ChartAccountGroup).filter(
                ChartAccountGroup.tenant_id == tenant_id,
                ChartAccountGroup.is_active == True
            ).order_by(ChartAccountGroup.code).all()
            
            # Buscar subgrupos
            subgrupos = db.query(ChartAccountSubgroup).filter(
                ChartAccountSubgroup.tenant_id == tenant_id,
                ChartAccountSubgroup.is_active == True
            ).order_by(ChartAccountSubgroup.code).all()
            
            # Buscar contas
            contas = db.query(ChartAccount).filter(
                ChartAccount.tenant_id == tenant_id,
                ChartAccount.is_active == True
            ).order_by(ChartAccount.code).all()
            
            return {
                "success": True,
                "grupos": [{"id": g.id, "code": g.code, "name": g.name} for g in grupos],
                "subgrupos": [{"id": s.id, "code": s.code, "name": s.name, "group_id": s.group_id} for s in subgrupos],
                "contas": [{"id": c.id, "code": c.code, "name": c.name, "subgroup_id": c.subgroup_id} for c in contas]
            }
            
        except Exception as e:
            return {"success": False, "message": f"Erro ao buscar plano de contas: {str(e)}"}
