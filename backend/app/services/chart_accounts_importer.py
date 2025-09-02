import csv
import io
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from app.models.chart_of_accounts import ChartAccountGroup, ChartAccountSubgroup, ChartAccount

class ChartAccountsImporter:
    """Serviço para importar plano de contas do CSV"""
    
    @staticmethod
    def parse_csv_content(csv_content: str) -> List[Dict]:
        """Parse do conteúdo CSV"""
        accounts_data = []
        
        # Ler o CSV
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        for row in reader:
            # Verificar se deve usar a conta
            if row.get('Escolha', '').strip().lower() == 'usar':
                accounts_data.append({
                    'conta': row.get('Conta', '').strip(),
                    'subgrupo': row.get('Subgrupo', '').strip(),
                    'grupo': row.get('Grupo', '').strip(),
                    'descricao': row.get('Descricao', '').strip() if 'Descricao' in row else None
                })
        
        return accounts_data
    
    @staticmethod
    def determine_account_type(grupo: str, subgrupo: str) -> str:
        """Determina o tipo da conta baseado no grupo e subgrupo"""
        grupo_lower = grupo.lower()
        subgrupo_lower = subgrupo.lower()
        
        if 'receita' in grupo_lower or 'receita' in subgrupo_lower:
            return 'Receita'
        elif 'custo' in grupo_lower or 'custo' in subgrupo_lower:
            return 'Custo'
        elif 'despesa' in grupo_lower or 'despesa' in subgrupo_lower:
            return 'Despesa'
        elif 'investimento' in grupo_lower:
            return 'Investimento'
        elif 'movimentação' in grupo_lower or 'entrada' in grupo_lower or 'saída' in grupo_lower:
            return 'Movimentação'
        else:
            return 'Outro'
    
    @staticmethod
    def generate_code(name: str, existing_codes: List[str]) -> str:
        """Gera um código único baseado no nome"""
        # Remover caracteres especiais e espaços
        clean_name = ''.join(c for c in name if c.isalnum() or c.isspace()).strip()
        
        # Pegar as primeiras letras de cada palavra
        words = clean_name.split()
        if len(words) == 1:
            code = words[0][:3].upper()
        else:
            code = ''.join(word[0] for word in words[:3]).upper()
        
        # Garantir que o código seja único
        base_code = code
        counter = 1
        while code in existing_codes:
            code = f"{base_code}{counter}"
            counter += 1
        
        return code
    
    @staticmethod
    def import_chart_accounts(db: Session, csv_content: str) -> Dict:
        """Importa o plano de contas do CSV"""
        try:
            # Parse do CSV
            accounts_data = ChartAccountsImporter.parse_csv_content(csv_content)
            
            if not accounts_data:
                return {"success": False, "message": "Nenhuma conta válida encontrada no CSV"}
            
            # Coletar códigos existentes
            existing_group_codes = [g.code for g in db.query(ChartAccountGroup).all()]
            existing_subgroup_codes = [sg.code for sg in db.query(ChartAccountSubgroup).all()]
            existing_account_codes = [a.code for a in db.query(ChartAccount).all()]
            
            # Processar grupos
            groups_created = 0
            groups_updated = 0
            group_mapping = {}  # nome -> id
            
            for account in accounts_data:
                grupo = account['grupo']
                
                if grupo not in group_mapping:
                    # Verificar se o grupo já existe
                    existing_group = db.query(ChartAccountGroup).filter(
                        ChartAccountGroup.name == grupo
                    ).first()
                    
                    if existing_group:
                        group_mapping[grupo] = existing_group.id
                        groups_updated += 1
                    else:
                        # Criar novo grupo
                        code = ChartAccountsImporter.generate_code(grupo, existing_group_codes)
                        new_group = ChartAccountGroup(
                            code=code,
                            name=grupo,
                            description=f"Grupo: {grupo}"
                        )
                        db.add(new_group)
                        db.flush()  # Para obter o ID
                        
                        group_mapping[grupo] = new_group.id
                        existing_group_codes.append(code)
                        groups_created += 1
            
            # Processar subgrupos
            subgroups_created = 0
            subgroups_updated = 0
            subgroup_mapping = {}  # (grupo, subgrupo) -> id
            
            for account in accounts_data:
                grupo = account['grupo']
                subgrupo = account['subgrupo']
                group_id = group_mapping[grupo]
                
                key = (grupo, subgrupo)
                if key not in subgroup_mapping:
                    # Verificar se o subgrupo já existe
                    existing_subgroup = db.query(ChartAccountSubgroup).filter(
                        ChartAccountSubgroup.name == subgrupo,
                        ChartAccountSubgroup.group_id == group_id
                    ).first()
                    
                    if existing_subgroup:
                        subgroup_mapping[key] = existing_subgroup.id
                        subgroups_updated += 1
                    else:
                        # Criar novo subgrupo
                        code = ChartAccountsImporter.generate_code(subgrupo, existing_subgroup_codes)
                        new_subgroup = ChartAccountSubgroup(
                            code=code,
                            name=subgrupo,
                            description=f"Subgrupo: {subgrupo}",
                            group_id=group_id
                        )
                        db.add(new_subgroup)
                        db.flush()  # Para obter o ID
                        
                        subgroup_mapping[key] = new_subgroup.id
                        existing_subgroup_codes.append(code)
                        subgroups_created += 1
            
            # Processar contas
            accounts_created = 0
            accounts_updated = 0
            
            for account in accounts_data:
                grupo = account['grupo']
                subgrupo = account['subgrupo']
                conta = account['conta']
                descricao = account['descricao']
                
                group_id = group_mapping[grupo]
                subgroup_id = subgroup_mapping[(grupo, subgrupo)]
                
                # Determinar tipo da conta
                account_type = ChartAccountsImporter.determine_account_type(grupo, subgrupo)
                
                # Verificar se a conta já existe
                existing_account = db.query(ChartAccount).filter(
                    ChartAccount.name == conta,
                    ChartAccount.subgroup_id == subgroup_id
                ).first()
                
                if existing_account:
                    # Atualizar conta existente
                    existing_account.description = descricao or existing_account.description
                    existing_account.account_type = account_type
                    accounts_updated += 1
                else:
                    # Criar nova conta
                    code = ChartAccountsImporter.generate_code(conta, existing_account_codes)
                    new_account = ChartAccount(
                        code=code,
                        name=conta,
                        description=descricao,
                        subgroup_id=subgroup_id,
                        account_type=account_type
                    )
                    db.add(new_account)
                    existing_account_codes.append(code)
                    accounts_created += 1
            
            # Commit das mudanças
            db.commit()
            
            return {
                "success": True,
                "message": "Plano de contas importado com sucesso",
                "summary": {
                    "groups_created": groups_created,
                    "groups_updated": groups_updated,
                    "subgroups_created": subgroups_created,
                    "subgroups_updated": subgroups_updated,
                    "accounts_created": accounts_created,
                    "accounts_updated": accounts_updated,
                    "total_processed": len(accounts_data)
                }
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "message": f"Erro ao importar plano de contas: {str(e)}"
            }
