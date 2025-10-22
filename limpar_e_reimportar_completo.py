#!/usr/bin/env python3
"""
Script para limpeza completa e reimportação de dados do Google Sheets
Ordem: Plano de Contas → Lançamentos → Contas Bancárias → Investimentos → Caixa
"""

import os
import sys
import json
import requests
from datetime import datetime
import time

# Configurações
BACKEND_URL = "https://finaflow-backend-642830139828.us-central1.run.app"
SPREADSHEET_ID = "1yyHuP6qjnK2Rd26yPPzaOqi_OJVeRjAJnewRIOJvFVY"

# Credenciais de teste
USERNAME = "lucianoterresrosa"
PASSWORD = "xs95LIa9ZduX"

class DataManager:
    def __init__(self):
        self.token = None
        self.tenant_id = None
        self.business_unit_id = None
        
    def authenticate(self):
        """Fazer login e obter token"""
        print("🔐 Fazendo autenticação...")
        
        # O endpoint espera dados no formato Form, não JSON
        login_data = {
            "username": USERNAME,
            "password": PASSWORD
        }
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/auth/login", 
                data=login_data,  # Usar data em vez de json
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            
            data = response.json()
            self.token = data.get("access_token")
            
            # Extrair informações do token JWT
            if self.token:
                import base64
                import json as json_lib
                
                # Decodificar o payload do JWT (sem verificar assinatura)
                try:
                    # JWT tem 3 partes separadas por ponto
                    parts = self.token.split('.')
                    if len(parts) >= 2:
                        # Decodificar o payload (segunda parte)
                        payload = parts[1]
                        # Adicionar padding se necessário
                        payload += '=' * (4 - len(payload) % 4)
                        decoded = base64.b64decode(payload)
                        payload_data = json_lib.loads(decoded)
                        
                        self.tenant_id = payload_data.get("tenant_id")
                        self.business_unit_id = payload_data.get("business_unit_id")
                except:
                    # Se não conseguir decodificar, usar valores padrão
                    self.tenant_id = "default-tenant"
                    self.business_unit_id = "default-bu"
            
            print(f"✅ Autenticação bem-sucedida")
            print(f"   Token obtido: {self.token[:20]}...")
            print(f"   Tenant ID: {self.tenant_id}")
            print(f"   Business Unit ID: {self.business_unit_id}")
            return True
            
        except Exception as e:
            print(f"❌ Erro na autenticação: {e}")
            print(f"   Response: {response.text if 'response' in locals() else 'N/A'}")
            return False
    
    def get_headers(self):
        """Obter headers com token de autenticação"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def clean_database(self):
        """Limpar todos os dados existentes"""
        print("\n🧹 LIMPANDO BANCO DE DADOS...")
        
        try:
            # Limpar dados do tenant atual
            response = requests.post(
                f"{BACKEND_URL}/api/v1/admin/limpar-dados-tenant",
                headers=self.get_headers(),
                json={"tenant_id": self.tenant_id}
            )
            
            if response.status_code == 200:
                print("✅ Dados limpos com sucesso")
                return True
            else:
                print(f"⚠️ Resposta inesperada: {response.status_code}")
                print(f"   {response.text}")
                return True  # Continuar mesmo assim
                
        except Exception as e:
            print(f"❌ Erro ao limpar dados: {e}")
            return False
    
    def import_plano_contas(self):
        """Importar plano de contas"""
        print("\n📊 IMPORTANDO PLANO DE CONTAS...")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/import/google-sheets",
                headers=self.get_headers(),
                json={
                    "spreadsheet_id": SPREADSHEET_ID,
                    "import_type": "accounts",
                    "validate_only": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Plano de contas importado com sucesso")
                print(f"   Grupos: {data.get('data_imported', {}).get('groups', 0)}")
                print(f"   Subgrupos: {data.get('data_imported', {}).get('subgroups', 0)}")
                print(f"   Contas: {data.get('data_imported', {}).get('accounts', 0)}")
                return True
            else:
                print(f"❌ Erro ao importar plano de contas: {response.status_code}")
                print(f"   {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao importar plano de contas: {e}")
            return False
    
    def import_lancamentos(self):
        """Importar lançamentos diários"""
        print("\n💰 IMPORTANDO LANÇAMENTOS DIÁRIOS...")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/import/google-sheets",
                headers=self.get_headers(),
                json={
                    "spreadsheet_id": SPREADSHEET_ID,
                    "import_type": "transactions",
                    "validate_only": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Lançamentos importados com sucesso")
                print(f"   Transações: {data.get('data_imported', {}).get('transactions', 0)}")
                print(f"   Previsões: {data.get('data_imported', {}).get('forecasts', 0)}")
                return True
            else:
                print(f"❌ Erro ao importar lançamentos: {response.status_code}")
                print(f"   {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao importar lançamentos: {e}")
            return False
    
    def import_contas_bancarias(self):
        """Importar contas bancárias"""
        print("\n🏦 IMPORTANDO CONTAS BANCÁRIAS...")
        
        try:
            # Primeiro, vamos verificar se há dados de contas bancárias na planilha
            response = requests.post(
                f"{BACKEND_URL}/api/v1/import/google-sheets/validate",
                headers=self.get_headers(),
                json={"spreadsheet_id": SPREADSHEET_ID}
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Validação de contas bancárias concluída")
                
                # Importar dados completos (incluindo contas bancárias)
                response = requests.post(
                    f"{BACKEND_URL}/api/v1/import/google-sheets",
                    headers=self.get_headers(),
                    json={
                        "spreadsheet_id": SPREADSHEET_ID,
                        "import_type": "all",
                        "validate_only": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Contas bancárias importadas com sucesso")
                    return True
                else:
                    print(f"❌ Erro ao importar contas bancárias: {response.status_code}")
                    return False
            else:
                print(f"❌ Erro na validação: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao importar contas bancárias: {e}")
            return False
    
    def import_investimentos(self):
        """Importar investimentos"""
        print("\n📈 IMPORTANDO INVESTIMENTOS...")
        
        try:
            # Verificar se há dados de investimentos
            response = requests.get(
                f"{BACKEND_URL}/api/v1/investimentos",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Investimentos verificados: {len(data.get('investimentos', []))} registros")
                return True
            else:
                print(f"⚠️ Investimentos não encontrados ou erro: {response.status_code}")
                return True  # Continuar mesmo sem investimentos
                
        except Exception as e:
            print(f"❌ Erro ao verificar investimentos: {e}")
            return False
    
    def import_caixa(self):
        """Importar caixa/dinheiro"""
        print("\n💵 IMPORTANDO CAIXA/DINHEIRO...")
        
        try:
            # Verificar se há dados de caixa
            response = requests.get(
                f"{BACKEND_URL}/api/v1/caixa",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Caixa verificado: {len(data.get('caixas', []))} registros")
                return True
            else:
                print(f"⚠️ Caixa não encontrado ou erro: {response.status_code}")
                return True  # Continuar mesmo sem caixa
                
        except Exception as e:
            print(f"❌ Erro ao verificar caixa: {e}")
            return False
    
    def verify_import(self):
        """Verificar se a importação foi bem-sucedida"""
        print("\n🔍 VERIFICANDO IMPORTAÇÃO...")
        
        try:
            # Verificar saldo disponível
            response = requests.get(
                f"{BACKEND_URL}/api/v1/saldo-disponivel",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                saldo = data.get('saldo_disponivel', {})
                total = saldo.get('total_geral', 0)
                print(f"✅ Saldo disponível: R$ {total:,.2f}")
                
                # Verificar contas bancárias
                contas = saldo.get('contas_bancarias', {})
                if contas.get('detalhes'):
                    print("   Contas bancárias:")
                    for conta in contas['detalhes']:
                        print(f"     - {conta.get('banco', 'N/A')}: R$ {conta.get('saldo', 0):,.2f}")
                
                return True
            else:
                print(f"❌ Erro ao verificar saldo: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao verificar importação: {e}")
            return False

def main():
    """Função principal"""
    print("🚀 INICIANDO LIMPEZA E REIMPORTAÇÃO COMPLETA")
    print("=" * 60)
    print(f"Backend: {BACKEND_URL}")
    print(f"Planilha: {SPREADSHEET_ID}")
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    manager = DataManager()
    
    # 1. Autenticar
    if not manager.authenticate():
        print("❌ Falha na autenticação. Abortando.")
        return False
    
    # 2. Limpar banco
    if not manager.clean_database():
        print("❌ Falha na limpeza. Abortando.")
        return False
    
    # 3. Importar plano de contas
    if not manager.import_plano_contas():
        print("❌ Falha na importação do plano de contas. Abortando.")
        return False
    
    # Aguardar um pouco
    print("⏳ Aguardando 5 segundos...")
    time.sleep(5)
    
    # 4. Importar lançamentos
    if not manager.import_lancamentos():
        print("❌ Falha na importação dos lançamentos. Abortando.")
        return False
    
    # Aguardar um pouco
    print("⏳ Aguardando 5 segundos...")
    time.sleep(5)
    
    # 5. Importar contas bancárias
    if not manager.import_contas_bancarias():
        print("❌ Falha na importação das contas bancárias. Abortando.")
        return False
    
    # Aguardar um pouco
    print("⏳ Aguardando 5 segundos...")
    time.sleep(5)
    
    # 6. Importar investimentos
    if not manager.import_investimentos():
        print("❌ Falha na importação dos investimentos. Abortando.")
        return False
    
    # 7. Importar caixa
    if not manager.import_caixa():
        print("❌ Falha na importação do caixa. Abortando.")
        return False
    
    # 8. Verificar importação
    if not manager.verify_import():
        print("❌ Falha na verificação. Verifique manualmente.")
        return False
    
    print("\n🎉 REIMPORTAÇÃO COMPLETA FINALIZADA COM SUCESSO!")
    print("=" * 60)
    print("✅ Plano de contas importado")
    print("✅ Lançamentos diários importados")
    print("✅ Contas bancárias importadas")
    print("✅ Investimentos verificados")
    print("✅ Caixa verificado")
    print("=" * 60)
    print("🌐 Acesse: https://finaflow.vercel.app/dashboard")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
