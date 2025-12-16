"""
Serviço de Fluxo de Caixa Mensal

Replica fielmente a estrutura e ordem da planilha do cliente.
Garante que todas as contas apareçam mesmo quando zeradas.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from calendar import monthrange
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.lancamento_diario import LancamentoDiario, TransactionType
from app.models.chart_of_accounts import (
    ChartAccountGroup,
    ChartAccountSubgroup,
    ChartAccount
)


# ============================================================================
# ORDEM EXPLÍCITA BASEADA NA PLANILHA
# ============================================================================

# Ordem dos grupos conforme aparece na planilha (não alfabética)
GROUP_ORDER = [
    "Receita",
    "Receita Operacional",
    "Receita Financeira",
    "Deduções",
    "Custos",
    "Custos com Serviços Prestados",
    "Custos com Mão de Obra",
    "Despesas Operacionais",
    "Despesas Financeiras",
    "Despesas com Pessoal",
    "Despesas Administrativas",
    "Despesas Comerciais",
    "Investimentos",
    "Movimentações Não Operacionais",
]

# Mapeamento de nomes de grupos para ordem (case-insensitive)
GROUP_ORDER_MAP = {name.lower(): idx for idx, name in enumerate(GROUP_ORDER)}


def _get_group_order_index(group_name: str) -> int:
    """Retorna o índice de ordem do grupo (maior = mais abaixo na planilha)"""
    group_lower = group_name.lower()
    # Buscar correspondência exata ou parcial
    for ordered_name, idx in GROUP_ORDER_MAP.items():
        if ordered_name in group_lower or group_lower in ordered_name:
            return idx
    # Se não encontrar, colocar no final
    return len(GROUP_ORDER) + 1000


class CashFlowService:
    """Serviço para gerar fluxo de caixa mensal replicando a planilha"""

    @staticmethod
    def get_monthly_cash_flow(
        db: Session,
        tenant_id: str,
        business_unit_id: Optional[str],
        year: int,
        month: int,
    ) -> Dict[str, any]:
        """
        Gera fluxo de caixa mensal com estrutura hierárquica idêntica à planilha.
        
        Retorna:
        {
            "year": int,
            "month": int,
            "days_in_month": int,
            "rows": [
                {
                    "categoria": str,
                    "nivel": int,  # 0=grupo, 1=subgrupo, 2=conta, 3=subtotal
                    "tipo": str,   # "grupo", "subgrupo", "conta", "subtotal"
                    "dias": {1: float, 2: float, ...},  # Valores por dia
                    "total": float,  # Total do mês
                },
                ...
            ]
        }
        """
        # Validar mês
        if month < 1 or month > 12:
            raise ValueError(f"Mês inválido: {month}. Deve estar entre 1 e 12.")
        
        # Calcular range de datas
        last_day = monthrange(year, month)[1]
        start_dt = datetime(year, month, 1)
        end_dt = datetime(year, month, last_day, 23, 59, 59)
        
        # 1. Carregar estrutura completa do plano de contas (TODAS as contas, mesmo sem lançamentos)
        groups, subgroups, accounts, subgroup_by_group, account_by_subgroup = (
            CashFlowService._load_complete_plan_structure(db, tenant_id)
        )
        
        # 2. Buscar lançamentos do mês (com relacionamentos)
        from sqlalchemy.orm import joinedload
        
        query = (
            db.query(LancamentoDiario)
            .options(
                joinedload(LancamentoDiario.grupo),
                joinedload(LancamentoDiario.subgrupo),
                joinedload(LancamentoDiario.conta)
            )
            .filter(
                LancamentoDiario.tenant_id == tenant_id,
                LancamentoDiario.is_active.is_(True),
                LancamentoDiario.data_movimentacao >= start_dt,
                LancamentoDiario.data_movimentacao <= end_dt,
            )
        )
        if business_unit_id:
            query = query.filter(LancamentoDiario.business_unit_id == business_unit_id)
        
        transactions = query.all()
        
        # 3. Agregar valores por conta/subgrupo/grupo por dia
        # Estrutura: {grupo_id: {subgrupo_id: {conta_id: {day: valor}}}}
        values_by_hierarchy = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(Decimal))))
        
        for tx in transactions:
            if not tx.data_movimentacao or tx.valor is None:
                continue
            
            day = tx.data_movimentacao.day
            valor = tx.valor if isinstance(tx.valor, Decimal) else Decimal(str(tx.valor))
            
            grupo_id = str(tx.grupo_id) if tx.grupo_id else None
            subgrupo_id = str(tx.subgrupo_id) if tx.subgrupo_id else None
            conta_id = str(tx.conta_id) if tx.conta_id else None
            
            if grupo_id and subgrupo_id and conta_id:
                values_by_hierarchy[grupo_id][subgrupo_id][conta_id][day] += valor
        
        # 4. Construir estrutura hierárquica ordenada
        rows: List[Dict[str, any]] = []
        
        # Ordenar grupos pela ordem da planilha
        sorted_groups = sorted(groups, key=lambda g: _get_group_order_index(g.name))
        
        for group in sorted_groups:
            group_id = str(group.id)
            
            # Adicionar linha do grupo
            group_row = CashFlowService._create_row(
                name=group.name,
                level=0,
                row_type="grupo",
                last_day=last_day
            )
            rows.append(group_row)
            
            # Buscar subgrupos do grupo (ordenados por código/nome)
            group_subgroups = sorted(
                subgroup_by_group.get(group_id, []),
                key=lambda sg: (sg.code or "", sg.name)
            )
            
            for subgroup in group_subgroups:
                subgrupo_id = str(subgroup.id)
                
                # Adicionar linha do subgrupo
                subgroup_row = CashFlowService._create_row(
                    name=subgroup.name,
                    level=1,
                    row_type="subgrupo",
                    last_day=last_day
                )
                rows.append(subgroup_row)
                
                # Buscar contas do subgrupo (ordenadas por código/nome)
                subgroup_accounts = sorted(
                    account_by_subgroup.get(subgrupo_id, []),
                    key=lambda acc: (acc.code or "", acc.name)
                )
                
                for account in subgroup_accounts:
                    conta_id = str(account.id)
                    
                    # Adicionar linha da conta (SEMPRE, mesmo se zerada)
                    account_row = CashFlowService._create_row(
                        name=account.name,
                        level=2,
                        row_type="conta",
                        last_day=last_day
                    )
                    
                    # Preencher valores dos dias (pode ser zero)
                    account_values = values_by_hierarchy.get(group_id, {}).get(subgrupo_id, {}).get(conta_id, {})
                    for day in range(1, last_day + 1):
                        valor = float(account_values.get(day, Decimal("0")))
                        account_row["dias"][day] = valor
                        account_row["total"] += valor
                        
                        # Acumular no subgrupo
                        subgroup_row["dias"][day] += valor
                        subgroup_row["total"] += valor
                        
                        # Acumular no grupo
                        group_row["dias"][day] += valor
                        group_row["total"] += valor
                    
                    rows.append(account_row)
                
                # Atualizar total do subgrupo
                subgroup_row["total"] = sum(subgroup_row["dias"].values())
            
            # Atualizar total do grupo
            group_row["total"] = sum(group_row["dias"].values())
        
        # 5. Calcular subtotais (conforme planilha)
        # Agregar valores por tipo de transação para cálculos
        receitas_por_dia = defaultdict(Decimal)
        deducoes_por_dia = defaultdict(Decimal)
        custos_por_dia = defaultdict(Decimal)
        despesas_por_dia = defaultdict(Decimal)
        ajustes_por_dia = defaultdict(Decimal)
        
        for tx in transactions:
            if not tx.data_movimentacao or tx.valor is None:
                continue
            day = tx.data_movimentacao.day
            valor = tx.valor if isinstance(tx.valor, Decimal) else Decimal(str(tx.valor))
            
            # Obter nome do grupo (via relacionamento ou ID)
            grupo_nome = ""
            if hasattr(tx, 'grupo') and tx.grupo:
                grupo_nome = tx.grupo.name.lower()
            elif tx.grupo_id:
                # Buscar grupo se não carregado
                grupo = db.query(ChartAccountGroup).filter(ChartAccountGroup.id == tx.grupo_id).first()
                if grupo:
                    grupo_nome = grupo.name.lower()
            
            tx_type = tx.transaction_type
            
            if tx_type == TransactionType.RECEITA:
                if "dedu" not in grupo_nome:
                    receitas_por_dia[day] += valor
                else:
                    deducoes_por_dia[day] += valor
            elif tx_type == TransactionType.CUSTO:
                custos_por_dia[day] += valor
            elif tx_type == TransactionType.DESPESA:
                despesas_por_dia[day] += valor
            else:
                # Movimentações não operacionais
                if "movimenta" in grupo_nome or "não operacional" in grupo_nome:
                    ajustes_por_dia[day] += valor
        
        # Calcular subtotais por dia usando os totais dos grupos já calculados
        # Buscar totais dos grupos nas rows
        receita_total_por_dia = defaultdict(Decimal)
        deducoes_total_por_dia = defaultdict(Decimal)
        custos_total_por_dia = defaultdict(Decimal)
        despesas_total_por_dia = defaultdict(Decimal)
        ajustes_total_por_dia = defaultdict(Decimal)
        
        for row in rows:
            if row["tipo"] != "grupo":
                continue
            categoria = row["categoria"].lower()
            dias = row.get("dias", {})
            
            if "receita" in categoria and "dedu" not in categoria:
                for day, valor in dias.items():
                    receita_total_por_dia[day] += Decimal(str(valor))
            elif "dedu" in categoria:
                for day, valor in dias.items():
                    deducoes_total_por_dia[day] += Decimal(str(valor))
            elif "custo" in categoria:
                for day, valor in dias.items():
                    custos_total_por_dia[day] += Decimal(str(valor))
            elif "despesa" in categoria and "operacional" in categoria:
                for day, valor in dias.items():
                    despesas_total_por_dia[day] += Decimal(str(valor))
            elif "movimenta" in categoria or "não operacional" in categoria:
                for day, valor in dias.items():
                    ajustes_total_por_dia[day] += Decimal(str(valor))
        
        # Calcular subtotais por dia
        receita_liquida_por_dia = {}
        lucro_bruto_por_dia = {}
        resultado_operacional_por_dia = {}
        saldo_final_por_dia = {}
        
        for day in range(1, last_day + 1):
            receita_liquida_por_dia[day] = float(receita_total_por_dia[day] - deducoes_total_por_dia[day])
            lucro_bruto_por_dia[day] = receita_liquida_por_dia[day] - float(custos_total_por_dia[day])
            resultado_operacional_por_dia[day] = lucro_bruto_por_dia[day] - float(despesas_total_por_dia[day])
            saldo_final_por_dia[day] = resultado_operacional_por_dia[day] + float(ajustes_total_por_dia[day])
        
        # Inserir subtotais na ordem correta
        # Encontrar posição após "Deduções" (último subgrupo/conta de deduções)
        deducoes_end_idx = None
        for i in range(len(rows) - 1, -1, -1):
            row = rows[i]
            if row["tipo"] == "grupo" and "dedu" in row["categoria"].lower():
                # Encontrar onde termina este grupo (próximo grupo ou fim)
                for j in range(i + 1, len(rows)):
                    if rows[j]["tipo"] == "grupo" and rows[j]["nivel"] == 0:
                        deducoes_end_idx = j
                        break
                if deducoes_end_idx is None:
                    deducoes_end_idx = len(rows)
                break
        
        if deducoes_end_idx is not None:
            # Inserir Receita Líquida após Deduções
            receita_liquida_row = CashFlowService._create_row("Receita Líquida", 0, "subtotal", last_day)
            receita_liquida_row["dias"] = receita_liquida_por_dia
            receita_liquida_row["total"] = sum(receita_liquida_por_dia.values())
            rows.insert(deducoes_end_idx, receita_liquida_row)
            deducoes_end_idx += 1  # Ajustar índice
        
        # Encontrar posição após "Custos" (último subgrupo/conta de custos)
        custos_end_idx = None
        for i in range(len(rows) - 1, -1, -1):
            row = rows[i]
            if row["tipo"] == "grupo" and "custo" in row["categoria"].lower():
                # Encontrar onde termina este grupo
                for j in range(i + 1, len(rows)):
                    if rows[j]["tipo"] == "grupo" and rows[j]["nivel"] == 0:
                        custos_end_idx = j
                        break
                if custos_end_idx is None:
                    custos_end_idx = len(rows)
                break
        
        if custos_end_idx is not None:
            # Inserir Lucro Bruto após Custos
            lucro_bruto_row = CashFlowService._create_row("Lucro Bruto", 0, "subtotal", last_day)
            lucro_bruto_row["dias"] = lucro_bruto_por_dia
            lucro_bruto_row["total"] = sum(lucro_bruto_por_dia.values())
            rows.insert(custos_end_idx, lucro_bruto_row)
            custos_end_idx += 1
        
        # Encontrar posição após "Despesas Operacionais"
        despesas_end_idx = None
        for i in range(len(rows) - 1, -1, -1):
            row = rows[i]
            if row["tipo"] == "grupo" and "despesa" in row["categoria"].lower() and "operacional" in row["categoria"].lower():
                # Encontrar onde termina este grupo
                for j in range(i + 1, len(rows)):
                    if rows[j]["tipo"] == "grupo" and rows[j]["nivel"] == 0:
                        despesas_end_idx = j
                        break
                if despesas_end_idx is None:
                    despesas_end_idx = len(rows)
                break
        
        if despesas_end_idx is not None:
            # Inserir Resultado Operacional após Despesas Operacionais
            resultado_op_row = CashFlowService._create_row("Resultado Operacional", 0, "subtotal", last_day)
            resultado_op_row["dias"] = resultado_operacional_por_dia
            resultado_op_row["total"] = sum(resultado_operacional_por_dia.values())
            rows.insert(despesas_end_idx, resultado_op_row)
            despesas_end_idx += 1
        
        # Encontrar posição após "Movimentações Não Operacionais"
        ajustes_end_idx = None
        for i in range(len(rows) - 1, -1, -1):
            row = rows[i]
            if row["tipo"] == "grupo" and ("movimenta" in row["categoria"].lower() or "não operacional" in row["categoria"].lower()):
                # Encontrar onde termina este grupo
                for j in range(i + 1, len(rows)):
                    if rows[j]["tipo"] == "grupo" and rows[j]["nivel"] == 0:
                        ajustes_end_idx = j
                        break
                if ajustes_end_idx is None:
                    ajustes_end_idx = len(rows)
                break
        
        if ajustes_end_idx is not None:
            # Inserir Saldo Final após Movimentações Não Operacionais
            saldo_final_row = CashFlowService._create_row("Saldo Final", 0, "subtotal", last_day)
            saldo_final_row["dias"] = saldo_final_por_dia
            saldo_final_row["total"] = sum(saldo_final_por_dia.values())
            rows.insert(ajustes_end_idx, saldo_final_row)
        
        return {
            "year": year,
            "month": month,
            "days_in_month": last_day,
            "rows": rows,
        }
    
    @staticmethod
    def _load_complete_plan_structure(
        db: Session,
        tenant_id: str
    ) -> Tuple[
        List[ChartAccountGroup],
        List[ChartAccountSubgroup],
        List[ChartAccount],
        Dict[str, List[ChartAccountSubgroup]],
        Dict[str, List[ChartAccount]],
    ]:
        """
        Carrega estrutura COMPLETA do plano de contas (incluindo contas sem lançamentos).
        """
        def _load(model):
            # Buscar itens do tenant primeiro
            tenant_items = (
                db.query(model)
                .filter(
                    model.tenant_id == tenant_id,
                    model.is_active.is_(True),
                )
                .all()
            )
            if tenant_items:
                return tenant_items
            # Se não encontrar, buscar globais
            return (
                db.query(model)
                .filter(
                    model.tenant_id.is_(None),
                    model.is_active.is_(True),
                )
                .all()
            )
        
        groups = _load(ChartAccountGroup)
        subgroups = _load(ChartAccountSubgroup)
        accounts = _load(ChartAccount)
        
        # Organizar hierarquia
        subgroup_by_group: Dict[str, List[ChartAccountSubgroup]] = defaultdict(list)
        for sub in subgroups:
            subgroup_by_group[str(sub.group_id)].append(sub)
        
        account_by_subgroup: Dict[str, List[ChartAccount]] = defaultdict(list)
        for account in accounts:
            account_by_subgroup[str(account.subgroup_id)].append(account)
        
        return groups, subgroups, accounts, subgroup_by_group, account_by_subgroup
    
    @staticmethod
    def _create_row(
        name: str,
        level: int,
        row_type: str,
        last_day: int
    ) -> Dict[str, any]:
        """Cria uma linha vazia do fluxo de caixa"""
        return {
            "categoria": name,
            "nivel": level,
            "tipo": row_type,
            "dias": {day: 0.0 for day in range(1, last_day + 1)},
            "total": 0.0,
        }
    

