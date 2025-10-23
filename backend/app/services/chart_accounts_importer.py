import csv
import io
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from backend.app.models.chart_of_accounts import ChartAccountGroup, ChartAccountSubgroup, ChartAccount

class ChartAccountsImporter:
    """Serviço para importar plano de contas baseado na planilha Google Sheets"""
    
    @staticmethod
    def create_default_chart_accounts(db: Session, tenant_id: str):
        """Criar plano de contas padrão baseado na planilha"""
        
        # Estrutura baseada na planilha
        chart_structure = {
            "Receita": {
                "Receita": ["Diversos", "Serviço Ivone"],
                "Receita Financeira": ["Outras Receitas Financeiras"]
            },
            "Custos": {
                "Custos com Serviços Prestados": ["Compra de material para consumo-CSP", "Serviços de terceiros-CSP"],
                "Custos com Mão de Obra": ["Salário"]
            },
            "Despesas Operacionais": {
                "Despesas Financeiras": ["Tarifas Bancárias", "Aluguel de Máquinas de Cartão"],
                "Despesas com Pessoal": ["Pró-Labore-ADM"],
                "Despesas Administrativas": ["Serviços de terceiros-ADM", "Seguros", "Telefone e Internet-ADM"],
                "Despesas Comerciais": ["Brindes", "Gasolina / Combustível-COM"]
            },
            "Movimentações Não Operacionais": {
                "Saídas não Operacionais": ["Outras saídas não operacionais"]
            }
        }
        
        created_groups = {}
        created_subgroups = {}
        created_accounts = {}
        
        # Criar grupos
        for group_name in chart_structure.keys():
            group = ChartAccountGroup(
                id=f"group_{group_name.lower().replace(' ', '_')}",
                tenant_id=tenant_id,
                code=ChartAccountsImporter._generate_group_code(group_name),
                name=group_name,
                description=f"Grupo {group_name}",
                is_active=True
            )
            db.add(group)
            created_groups[group_name] = group
        
        db.flush()
        
        # Criar subgrupos
        for group_name, subgroups in chart_structure.items():
            group = created_groups[group_name]
            for subgroup_name, accounts in subgroups.items():
                subgroup = ChartAccountSubgroup(
                    id=f"subgroup_{subgroup_name.lower().replace(' ', '_').replace('/', '_')}",
                    tenant_id=tenant_id,
                    code=ChartAccountsImporter._generate_subgroup_code(subgroup_name),
                    name=subgroup_name,
                    description=f"Subgrupo {subgroup_name}",
                    group_id=group.id,
                    is_active=True
                )
                db.add(subgroup)
                created_subgroups[subgroup_name] = subgroup
        
        db.flush()
        
        # Criar contas
        for group_name, subgroups in chart_structure.items():
            for subgroup_name, accounts in subgroups.items():
                subgroup = created_subgroups[subgroup_name]
                for account_name in accounts:
                    account = ChartAccount(
                        id=f"account_{account_name.lower().replace(' ', '_').replace('/', '_').replace('-', '_')}",
                        tenant_id=tenant_id,
                        code=ChartAccountsImporter._generate_account_code(account_name),
                        name=account_name,
                        description=f"Conta {account_name}",
                        subgroup_id=subgroup.id,
                        account_type=ChartAccountsImporter._determine_account_type(group_name, subgroup_name),
                        is_active=True
                    )
                    db.add(account)
                    created_accounts[account_name] = account
        
        db.flush()
        
        return {
            "groups": len(created_groups),
            "subgroups": len(created_subgroups),
            "accounts": len(created_accounts)
        }
    
    @staticmethod
    def _generate_group_code(group_name: str) -> str:
        """Gerar código para grupo"""
        codes = {
            "Receita": "1",
            "Custos": "2", 
            "Despesas Operacionais": "3",
            "Movimentações Não Operacionais": "4"
        }
        return codes.get(group_name, "9")
    
    @staticmethod
    def _generate_subgroup_code(subgroup_name: str) -> str:
        """Gerar código para subgrupo"""
        # Códigos baseados na estrutura da planilha
        codes = {
            "Receita": "01",
            "Receita Financeira": "02",
            "Custos com Serviços Prestados": "01",
            "Custos com Mão de Obra": "02",
            "Despesas Financeiras": "01",
            "Despesas com Pessoal": "02",
            "Despesas Administrativas": "03",
            "Despesas Comerciais": "04",
            "Saídas não Operacionais": "01"
        }
        return codes.get(subgroup_name, "99")
    
    @staticmethod
    def _generate_account_code(account_name: str) -> str:
        """Gerar código para conta"""
        # Códigos sequenciais baseados no nome
        codes = {
            "Diversos": "001",
            "Serviço Ivone": "002",
            "Outras Receitas Financeiras": "001",
            "Compra de material para consumo-CSP": "001",
            "Serviços de terceiros-CSP": "002",
            "Salário": "001",
            "Tarifas Bancárias": "001",
            "Aluguel de Máquinas de Cartão": "002",
            "Pró-Labore-ADM": "001",
            "Serviços de terceiros-ADM": "001",
            "Seguros": "002",
            "Telefone e Internet-ADM": "003",
            "Brindes": "001",
            "Gasolina / Combustível-COM": "002",
            "Outras saídas não operacionais": "001"
        }
        return codes.get(account_name, "999")
    
    @staticmethod
    def _determine_account_type(group_name: str, subgroup_name: str) -> str:
        """Determinar tipo da conta baseado no grupo e subgrupo"""
        if "Receita" in group_name:
            return "receita"
        elif "Custo" in group_name:
            return "custo"
        elif "Despesa" in group_name:
            return "despesa"
        elif "Movimentação" in group_name:
            return "movimentacao"
        else:
            return "outro"