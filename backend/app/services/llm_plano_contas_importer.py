"""
Importador específico do Plano de Contas da planilha LLM Lavanderia
Estrutura: Coluna A = Conta, Coluna B = Subgrupo, Coluna C = Grupo
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from app.models.chart_of_accounts import ChartAccountGroup, ChartAccountSubgroup, ChartAccount, BusinessUnitChartAccount
import uuid

class LLMPlanoContasImporter:
    def __init__(self, credentials_path="google_credentials.json"):
        self.credentials_path = credentials_path
        self.service = None
    
    def authenticate(self):
        """Autenticar com Google Sheets API"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            self.service = build('sheets', 'v4', credentials=credentials)
            return True
        except Exception as e:
            print(f"[IMPORT ERROR] Auth failed: {str(e)}")
            return False
    
    def generate_code(self, name: str, existing_codes: set) -> str:
        """Gerar código único baseado no nome"""
        # Remover acentos e caracteres especiais
        clean_name = ''.join(c for c in name if c.isalnum() or c.isspace()).strip()
        
        # Pegar iniciais
        words = clean_name.split()
        if len(words) == 1:
            code = words[0][:5].upper()
        else:
            code = ''.join(word[0] for word in words[:4]).upper()
        
        # Garantir único
        base_code = code
        counter = 1
        while code in existing_codes:
            code = f"{base_code}{counter}"
            counter += 1
        
        existing_codes.add(code)
        return code
    
    def import_plano_contas(self, spreadsheet_id: str, tenant_id: str, business_unit_id: str, db: Session):
        """
        Importar plano de contas da planilha LLM
        Estrutura: A=Conta, B=Subgrupo, C=Grupo, D=Escolha (LLM/Usar)
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return {"success": False, "error": "Falha na autenticação"}
            
            # Buscar dados
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range="'Plano de contas'!A:E"
            ).execute()
            
            values = result.get('values', [])
            
            if not values or len(values) < 2:
                return {"success": False, "error": "Aba vazia"}
            
            headers = values[0]
            rows = values[1:]
            
            print(f"[PLANO CONTAS] Encontradas {len(rows)} linhas")
            print(f"[PLANO CONTAS] Cabeçalhos: {headers}")
            
            # Mapear colunas
            col_conta = 0  # A
            col_subgrupo = 1  # B
            col_grupo = 2  # C
            col_escolha = 3  # D (LLM)
            
            # Coletar códigos existentes
            existing_group_codes = set()
            existing_subgroup_codes = set()
            existing_account_codes = set()
            
            # Estrutura para armazenar
            grupos_map = {}  # {nome: objeto}
            subgrupos_map = {}  # {(grupo_nome, subgrupo_nome): objeto}
            
            contas_criadas = 0
            grupos_criados = 0
            subgrupos_criados = 0
            
            for idx, row in enumerate(rows, start=2):
                if len(row) <= col_grupo:
                    continue
                
                # Verificar se deve usar
                escolha = row[col_escolha] if len(row) > col_escolha else ""
                if escolha.strip().lower() != "usar":
                    continue
                
                conta_nome = row[col_conta].strip() if row[col_conta] else ""
                subgrupo_nome = row[col_subgrupo].strip() if row[col_subgrupo] else ""
                grupo_nome = row[col_grupo].strip() if row[col_grupo] else ""
                
                if not conta_nome or not subgrupo_nome or not grupo_nome:
                    print(f"[PLANO CONTAS] Ignorando linha {idx}: dados incompletos")
                    continue
                
                print(f"[PLANO CONTAS] Processando: {grupo_nome} > {subgrupo_nome} > {conta_nome}")

                tenant_str = str(tenant_id)
                
                # 1. Criar/buscar Grupo
                if grupo_nome not in grupos_map:
                    # Buscar existente
                    grupo = db.query(ChartAccountGroup).filter(
                        ChartAccountGroup.name == grupo_nome,
                        ChartAccountGroup.tenant_id == tenant_str
                    ).first()
                    
                    if not grupo:
                        grupo_code = self.generate_code(grupo_nome, existing_group_codes)
                        grupo = ChartAccountGroup(
                            code=grupo_code,
                            name=grupo_nome,
                            description=f"Grupo {grupo_nome}",
                            tenant_id=tenant_str,
                            is_active=True
                        )
                        db.add(grupo)
                        db.flush()
                        grupos_criados += 1
                        print(f"   ✅ Grupo criado: {grupo_code} - {grupo_nome}")
                    
                    grupos_map[grupo_nome] = grupo
                
                grupo = grupos_map[grupo_nome]
                
                # 2. Criar/buscar Subgrupo
                subgrupo_key = (grupo_nome, subgrupo_nome)
                if subgrupo_key not in subgrupos_map:
                    # Buscar existente
                    subgrupo = db.query(ChartAccountSubgroup).filter(
                        ChartAccountSubgroup.name == subgrupo_nome,
                        ChartAccountSubgroup.group_id == grupo.id,
                        ChartAccountSubgroup.tenant_id == tenant_str
                    ).first()
                    
                    if not subgrupo:
                        subgrupo_code = self.generate_code(subgrupo_nome, existing_subgroup_codes)
                        subgrupo = ChartAccountSubgroup(
                            code=subgrupo_code,
                            name=subgrupo_nome,
                            description=f"Subgrupo {subgrupo_nome}",
                            group_id=grupo.id,
                            tenant_id=tenant_str,
                            is_active=True
                        )
                        db.add(subgrupo)
                        db.flush()
                        subgrupos_criados += 1
                        print(f"   ✅ Subgrupo criado: {subgrupo_code} - {subgrupo_nome}")
                    
                    subgrupos_map[subgrupo_key] = subgrupo
                
                subgrupo = subgrupos_map[subgrupo_key]
                
                # 3. Criar conta
                # Buscar se já existe
                conta = db.query(ChartAccount).filter(
                    ChartAccount.name == conta_nome,
                    ChartAccount.subgroup_id == subgrupo.id,
                    ChartAccount.tenant_id == tenant_str
                ).first()
                
                if not conta:
                    conta_code = self.generate_code(conta_nome, existing_account_codes)
                    
                    # Determinar tipo
                    account_type = "Outro"
                    if "receita" in grupo_nome.lower():
                        account_type = "Receita"
                    elif "custo" in grupo_nome.lower():
                        account_type = "Custo"
                    elif "despesa" in grupo_nome.lower():
                        account_type = "Despesa"
                    elif "invest" in grupo_nome.lower():
                        account_type = "Investimento"
                    elif "dedu" in grupo_nome.lower():
                        account_type = "Dedução"
                    
                    conta = ChartAccount(
                        code=conta_code,
                        name=conta_nome,
                        description=f"Conta {conta_nome}",
                        subgroup_id=subgrupo.id,
                        tenant_id=tenant_str,
                        account_type=account_type,
                        is_active=True
                    )
                    db.add(conta)
                    db.flush()
                    
                    # Criar vínculo com BU
                    if business_unit_id:
                        existing_link = db.query(BusinessUnitChartAccount).filter_by(
                            business_unit_id=business_unit_id,
                            chart_account_id=conta.id
                        ).first()
                        if not existing_link:
                            bu_link = BusinessUnitChartAccount(
                                business_unit_id=business_unit_id,
                                chart_account_id=conta.id,
                                is_active=True
                            )
                            db.add(bu_link)
                    
                    contas_criadas += 1
                    print(f"   ✅ Conta criada: {conta_code} - {conta_nome}")
            
            db.commit()
            
            print(f"\n[PLANO CONTAS] ✅ Importação concluída:")
            print(f"   Grupos criados: {grupos_criados}")
            print(f"   Subgrupos criados: {subgrupos_criados}")
            print(f"   Contas criadas: {contas_criadas}")
            
            return {
                "success": True,
                "grupos_criados": grupos_criados,
                "subgrupos_criados": subgrupos_criados,
                "contas_criadas": contas_criadas
            }
            
        except Exception as e:
            db.rollback()
            print(f"[PLANO CONTAS ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

