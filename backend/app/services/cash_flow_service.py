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
        order_labels: Optional[List[str]] = None,
        saldo_ano_anterior: Optional[float] = None,
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
        def _empty_days() -> Dict[int, Decimal]:
            return {day: Decimal("0") for day in range(1, last_day + 1)}

        def _sum_groups_by_predicate(predicate) -> Dict[int, Decimal]:
            totals = _empty_days()
            for row in rows:
                if row["tipo"] != "grupo":
                    continue
                if not predicate(str(row.get("categoria", ""))):
                    continue
                for day, valor in row.get("dias", {}).items():
                    totals[day] += Decimal(str(valor))
            return totals

        def _sum_group_by_name(name: str) -> Dict[int, Decimal]:
            totals = _empty_days()
            for row in rows:
                if row["tipo"] == "grupo" and str(row.get("categoria", "")).strip().lower() == name.strip().lower():
                    for day, valor in row.get("dias", {}).items():
                        totals[day] += Decimal(str(valor))
                    break
            return totals

        def _sum_subgroup_by_name(name: str) -> Dict[int, Decimal]:
            totals = _empty_days()
            for row in rows:
                if row["tipo"] == "subgrupo" and str(row.get("categoria", "")).strip().lower() == name.strip().lower():
                    for day, valor in row.get("dias", {}).items():
                        totals[day] += Decimal(str(valor))
                    break
            return totals

        def _get_row_by_name(name: str) -> Optional[Dict[str, any]]:
            for row in rows:
                if str(row.get("categoria", "")).strip().lower() == name.strip().lower():
                    return row
            return None

        def _ensure_subtotal_row(name: str) -> Dict[str, any]:
            row = _get_row_by_name(name)
            if not row:
                row = CashFlowService._create_row(name, 0, "subtotal", last_day)
                rows.append(row)
            return row

        receita_totais = _sum_groups_by_predicate(
            lambda name: "receita" in name.lower() and "dedu" not in name.lower()
        )
        deducoes_totais = _sum_groups_by_predicate(lambda name: "dedu" in name.lower())
        custos_totais = _sum_groups_by_predicate(lambda name: "custo" in name.lower())
        despesas_operacionais_totais = _sum_group_by_name("Despesas Operacionais")
        investimentos_totais = _sum_groups_by_predicate(lambda name: "investimento" in name.lower())

        entradas_nao_op = _sum_subgroup_by_name("Entradas não Operacionais")
        saidas_nao_op = _sum_subgroup_by_name("Saídas não Operacionais")

        # Atualizar Movimentações Não Operacionais como entradas - saídas
        mov_group_row = _get_row_by_name("Movimentações Não Operacionais")
        if mov_group_row and mov_group_row.get("tipo") == "grupo":
            mov_group_row["dias"] = {
                day: float(entradas_nao_op[day] - saidas_nao_op[day]) for day in range(1, last_day + 1)
            }
            mov_group_row["total"] = sum(mov_group_row["dias"].values())

        receita_liquida = _empty_days()
        lucro_bruto = _empty_days()
        lucro_antes_invest = _empty_days()
        desembolso_total = _empty_days()
        lucro_operacional = _empty_days()
        lucro_liquido = _empty_days()

        for day in range(1, last_day + 1):
            receita_liquida[day] = receita_totais[day] - deducoes_totais[day]
            lucro_bruto[day] = receita_liquida[day] - custos_totais[day]
            lucro_antes_invest[day] = lucro_bruto[day] - despesas_operacionais_totais[day]
            desembolso_total[day] = (
                deducoes_totais[day] + custos_totais[day] + despesas_operacionais_totais[day] + investimentos_totais[day]
            )
            lucro_operacional[day] = receita_totais[day] - desembolso_total[day]
            mov = entradas_nao_op[day] - saidas_nao_op[day]
            lucro_liquido[day] = lucro_operacional[day] + mov

        def _apply_row_values(row_name: str, values: Dict[int, Decimal]) -> None:
            row = _ensure_subtotal_row(row_name)
            row["dias"] = {day: float(values[day]) for day in range(1, last_day + 1)}
            row["total"] = sum(row["dias"].values())

        _apply_row_values("Receita Líquida", receita_liquida)
        _apply_row_values("Lucro Bruto", lucro_bruto)
        _apply_row_values("Lucro antes dos investimentos", lucro_antes_invest)
        _apply_row_values("Desembolso Total", desembolso_total)
        _apply_row_values("LUCRO OPERACIONAL", lucro_operacional)
        _apply_row_values("Lucro Líquido de caixa mensal", lucro_liquido)

        saldo_anterior = Decimal(str(saldo_ano_anterior or 0))
        saldo_row = _ensure_subtotal_row("Saldo do ano anterior")
        saldo_row["dias"] = {day: 0.0 for day in range(1, last_day + 1)}
        saldo_row["dias"][1] = float(saldo_anterior)
        saldo_row["total"] = float(saldo_anterior)

        lucro_acumulado = _empty_days()
        acc = saldo_anterior
        for day in range(1, last_day + 1):
            acc += lucro_liquido[day]
            lucro_acumulado[day] = acc
        _apply_row_values("Lucro líquido acumulado (Reservas)", lucro_acumulado)

        if order_labels:
            subtotal_labels = {
                "receita líquida",
                "lucro bruto",
                "lucro antes dos investimentos",
                "desembolso total",
                "lucro operacional",
                "lucro líquido de caixa mensal",
                "lucro líquido acumulado (reservas)",
                "saldo do ano anterior",
            }
            group_map = {g.name.strip().lower(): str(g.id) for g in groups}
            subgroup_map = {sg.name.strip().lower(): str(sg.id) for sg in subgroups}
            account_map = {acc.name.strip().lower(): str(acc.id) for acc in accounts}
            row_by_label = {str(r.get("categoria", "")).strip().lower(): r for r in rows}
            current_group_id: Optional[str] = None

            for raw_label in order_labels:
                label = str(raw_label).strip()
                if not label:
                    continue
                label_key = label.lower()

                if label_key in group_map:
                    current_group_id = group_map[label_key]
                elif label_key in subgroup_map or label_key in account_map or label_key in subtotal_labels:
                    pass

                if label_key in row_by_label:
                    continue

                if label_key in group_map:
                    row_type = "grupo"
                    level = 0
                elif label_key in subgroup_map:
                    row_type = "subgrupo"
                    level = 1
                elif label_key in account_map:
                    row_type = "conta"
                    level = 2
                elif label_key in subtotal_labels:
                    row_type = "subtotal"
                    level = 0
                else:
                    row_type = "subgrupo" if current_group_id else "subtotal"
                    level = 1 if current_group_id else 0

                new_row = CashFlowService._create_row(label, level, row_type, last_day)
                rows.append(new_row)
                row_by_label[label_key] = new_row

        if order_labels:
            rows = CashFlowService._reorder_rows(rows, order_labels, strict=True)
        
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

    @staticmethod
    def _reorder_rows(
        rows: List[Dict[str, any]],
        order_labels: List[str],
        strict: bool = False,
    ) -> List[Dict[str, any]]:
        def normalize(value: str) -> str:
            return (
                value.strip()
                .lower()
                .replace("á", "a")
                .replace("à", "a")
                .replace("â", "a")
                .replace("ã", "a")
                .replace("é", "e")
                .replace("ê", "e")
                .replace("í", "i")
                .replace("ó", "o")
                .replace("ô", "o")
                .replace("õ", "o")
                .replace("ú", "u")
                .replace("ç", "c")
            )

        label_to_rows: Dict[str, List[Dict[str, any]]] = defaultdict(list)
        for row in rows:
            label_to_rows[normalize(row.get("categoria", ""))].append(row)

        ordered: List[Dict[str, any]] = []
        used_ids = set()
        for label in order_labels:
            key = normalize(label)
            if label_to_rows.get(key):
                row = label_to_rows[key].pop(0)
                ordered.append(row)
                used_ids.add(id(row))

        if not strict:
            for row in rows:
                if id(row) not in used_ids:
                    ordered.append(row)

        return ordered
    
