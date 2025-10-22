from typing import List, Dict, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
# from app.models.lancamento_diario import (
#     LancamentoDiario, 
#     TransactionType, 
#     TransactionStatus,
#     LancamentoDiarioCreate,
#     LancamentoDiarioUpdate
# )
from app.models.chart_of_accounts import ChartAccount, ChartAccountSubgroup, ChartAccountGroup
from app.models.auth import User

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
            # Usar SQL direto para evitar conflito SQLAlchemy
            from sqlalchemy import text
            
            # Construir query SQL
            where_conditions = [
                "tenant_id = :tenant_id",
                "business_unit_id = :business_unit_id", 
                "is_active = true"
            ]
            params = {
                "tenant_id": tenant_id,
                "business_unit_id": business_unit_id
            }
            
            # Aplicar filtros
            if start_date:
                where_conditions.append("data_movimentacao >= :start_date")
                params["start_date"] = start_date
            if end_date:
                where_conditions.append("data_movimentacao <= :end_date")
                params["end_date"] = end_date
            if conta_id:
                where_conditions.append("conta_id = :conta_id")
                params["conta_id"] = conta_id
            if subgrupo_id:
                where_conditions.append("subgrupo_id = :subgrupo_id")
                params["subgrupo_id"] = subgrupo_id
            if grupo_id:
                where_conditions.append("grupo_id = :grupo_id")
                params["grupo_id"] = grupo_id
            if transaction_type:
                where_conditions.append("transaction_type = :transaction_type")
                params["transaction_type"] = transaction_type.value if hasattr(transaction_type, 'value') else str(transaction_type)
            
            where_clause = " AND ".join(where_conditions)
            
            # Query para contar total
            count_query = text(f"SELECT COUNT(*) FROM lancamentos_diarios WHERE {where_clause}")
            total = db.execute(count_query, params).scalar()
            
            # Query para buscar dados com paginação
            offset = (page - 1) * per_page
            data_query = text(f"""
                SELECT * FROM lancamentos_diarios 
                WHERE {where_clause}
                ORDER BY data_movimentacao DESC
                LIMIT :limit OFFSET :offset
            """)
            params.update({"limit": per_page, "offset": offset})
            
            result = db.execute(data_query, params)
            lancamentos = result.fetchall()
            
            # Converter para response
            lancamentos_response = []
            for row in lancamentos:
                lancamentos_response.append({
                    "id": row.id,
                    "data_movimentacao": row.data_movimentacao.isoformat() if row.data_movimentacao else None,
                    "valor": str(row.valor),
                    "liquidacao": row.liquidacao.isoformat() if row.liquidacao else None,
                    "observacoes": row.observacoes,
                    "conta_id": row.conta_id,
                    "conta_nome": row.conta_name if hasattr(row, 'conta_name') else None,
                    "conta_codigo": row.conta_code if hasattr(row, 'conta_code') else None,
                    "subgrupo_id": row.subgrupo_id,
                    "subgrupo_nome": row.subgrupo_name if hasattr(row, 'subgrupo_name') else None,
                    "subgrupo_codigo": row.subgrupo_code if hasattr(row, 'subgrupo_code') else None,
                    "grupo_id": row.grupo_id,
                    "grupo_nome": row.grupo_name if hasattr(row, 'grupo_name') else None,
                    "grupo_codigo": row.grupo_code if hasattr(row, 'grupo_code') else None,
                    "transaction_type": row.transaction_type,
                    "status": row.status,
                    "tenant_id": row.tenant_id,
                    "business_unit_id": row.business_unit_id,
                    "created_by": row.created_by,
                    "is_active": row.is_active,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
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
