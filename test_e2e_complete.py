#!/usr/bin/env python3
"""
🧪 TESTE END-TO-END COMPLETO - FinaFlow
========================================

Teste abrangente para mapear todas as funcionalidades do sistema FinaFlow,
identificar dados mock, CRUDs não operacionais e criar diagnóstico completo.

Contexto: SaaS para pequenas e médias empresas baseado na metodologia
financeira da contadora Ana Paula.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import sys

class FinaFlowE2ETest:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.frontend_url = "http://localhost:3000"
        self.auth_token = None
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "authentication": {},
            "crud_operations": {},
            "business_logic": {},
            "mock_data": {},
            "api_endpoints": {},
            "frontend_pages": {},
            "issues": [],
            "recommendations": []
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log com timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_health_check(self):
        """Testar health check do backend"""
        self.log("🏥 Testando health check...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.test_results["api_endpoints"]["health"] = {
                    "status": "✅ OK",
                    "response": data
                }
                self.log(f"✅ Health check OK: {data}")
                return True
            else:
                self.log(f"❌ Health check falhou: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Erro no health check: {e}", "ERROR")
            return False
    
    def test_api_documentation(self):
        """Testar documentação da API"""
        self.log("📚 Testando documentação da API...")
        try:
            # Testar OpenAPI docs
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            if response.status_code == 200:
                self.test_results["api_endpoints"]["docs"] = "✅ OK"
                self.log("✅ Documentação da API acessível")
            else:
                self.test_results["api_endpoints"]["docs"] = f"❌ Status: {response.status_code}"
                
            # Testar root endpoint
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.test_results["api_endpoints"]["root"] = {
                    "status": "✅ OK",
                    "response": data
                }
                self.log(f"✅ Root endpoint OK: {data}")
                
        except Exception as e:
            self.log(f"❌ Erro na documentação: {e}", "ERROR")
    
    def test_authentication(self):
        """Testar sistema de autenticação"""
        self.log("🔐 Testando sistema de autenticação...")
        
        # Testar endpoint de login
        try:
            login_data = {
                "username": "admin",
                "password": "test"
            }
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.test_results["authentication"]["login"] = {
                    "status": "✅ OK",
                    "token_received": bool(self.auth_token),
                    "response_keys": list(data.keys())
                }
                self.log(f"✅ Login bem-sucedido: {list(data.keys())}")
                
                # Testar token em endpoint protegido
                if self.auth_token:
                    headers = {"Authorization": f"Bearer {self.auth_token}"}
                    response = requests.get(
                        f"{self.base_url}/api/v1/financial/accounts",
                        headers=headers,
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        self.test_results["authentication"]["protected_access"] = "✅ OK"
                        self.log("✅ Acesso a endpoint protegido OK")
                    else:
                        self.test_results["authentication"]["protected_access"] = f"❌ Status: {response.status_code}"
                        self.log(f"❌ Falha no acesso protegido: {response.status_code}")
                        
            else:
                self.test_results["authentication"]["login"] = {
                    "status": f"❌ Status: {response.status_code}",
                    "response": response.text[:200]
                }
                self.log(f"❌ Login falhou: {response.status_code}")
                
        except Exception as e:
            self.log(f"❌ Erro na autenticação: {e}", "ERROR")
            self.test_results["authentication"]["error"] = str(e)
    
    def test_crud_operations(self):
        """Testar operações CRUD"""
        self.log("📝 Testando operações CRUD...")
        
        if not self.auth_token:
            self.log("❌ Token de autenticação não disponível", "ERROR")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Testar CRUD de Contas
        self.test_crud_accounts(headers)
        
        # Testar CRUD de Transações
        self.test_crud_transactions(headers)
        
        # Testar CRUD de Grupos
        self.test_crud_groups(headers)
        
        # Testar CRUD de Subgrupos
        self.test_crud_subgroups(headers)
        
        # Testar CRUD de Previsões
        self.test_crud_forecasts(headers)
    
    def test_crud_accounts(self, headers: Dict[str, str]):
        """Testar CRUD de contas"""
        self.log("💰 Testando CRUD de contas...")
        
        try:
            # GET - Listar contas
            response = requests.get(f"{self.base_url}/api/v1/financial/accounts", headers=headers)
            if response.status_code == 200:
                accounts = response.json()
                self.test_results["crud_operations"]["accounts_get"] = {
                    "status": "✅ OK",
                    "count": len(accounts) if isinstance(accounts, list) else 0,
                    "sample": accounts[:2] if isinstance(accounts, list) and len(accounts) > 0 else None
                }
                self.log(f"✅ GET contas: {len(accounts) if isinstance(accounts, list) else 0} registros")
                
                # Identificar dados mock
                if isinstance(accounts, list) and len(accounts) > 0:
                    self.analyze_mock_data("accounts", accounts)
            else:
                self.test_results["crud_operations"]["accounts_get"] = f"❌ Status: {response.status_code}"
                
            # POST - Criar conta (se endpoint existir)
            new_account = {
                "name": "Conta Teste E2E",
                "subgroup_id": "test_subgroup",
                "balance": 1000.00
            }
            response = requests.post(f"{self.base_url}/api/v1/financial/accounts", 
                                   json=new_account, headers=headers)
            
            if response.status_code in [200, 201]:
                self.test_results["crud_operations"]["accounts_post"] = "✅ OK"
                self.log("✅ POST conta: Criada com sucesso")
            elif response.status_code == 422:
                self.test_results["crud_operations"]["accounts_post"] = "⚠️ Validation Error"
                self.log("⚠️ POST conta: Erro de validação (esperado)")
            else:
                self.test_results["crud_operations"]["accounts_post"] = f"❌ Status: {response.status_code}"
                
        except Exception as e:
            self.log(f"❌ Erro no CRUD contas: {e}", "ERROR")
    
    def test_crud_transactions(self, headers: Dict[str, str]):
        """Testar CRUD de transações"""
        self.log("💳 Testando CRUD de transações...")
        
        try:
            # GET - Listar transações
            response = requests.get(f"{self.base_url}/api/v1/financial/transactions", headers=headers)
            if response.status_code == 200:
                transactions = response.json()
                self.test_results["crud_operations"]["transactions_get"] = {
                    "status": "✅ OK",
                    "count": len(transactions) if isinstance(transactions, list) else 0,
                    "sample": transactions[:2] if isinstance(transactions, list) and len(transactions) > 0 else None
                }
                self.log(f"✅ GET transações: {len(transactions) if isinstance(transactions, list) else 0} registros")
                
                if isinstance(transactions, list) and len(transactions) > 0:
                    self.analyze_mock_data("transactions", transactions)
            else:
                self.test_results["crud_operations"]["transactions_get"] = f"❌ Status: {response.status_code}"
                
        except Exception as e:
            self.log(f"❌ Erro no CRUD transações: {e}", "ERROR")
    
    def test_crud_groups(self, headers: Dict[str, str]):
        """Testar CRUD de grupos"""
        self.log("📊 Testando CRUD de grupos...")
        
        try:
            response = requests.get(f"{self.base_url}/api/v1/financial/groups", headers=headers)
            if response.status_code == 200:
                groups = response.json()
                self.test_results["crud_operations"]["groups_get"] = {
                    "status": "✅ OK",
                    "count": len(groups) if isinstance(groups, list) else 0,
                    "sample": groups[:2] if isinstance(groups, list) and len(groups) > 0 else None
                }
                self.log(f"✅ GET grupos: {len(groups) if isinstance(groups, list) else 0} registros")
                
                if isinstance(groups, list) and len(groups) > 0:
                    self.analyze_mock_data("groups", groups)
            else:
                self.test_results["crud_operations"]["groups_get"] = f"❌ Status: {response.status_code}"
                
        except Exception as e:
            self.log(f"❌ Erro no CRUD grupos: {e}", "ERROR")
    
    def test_crud_subgroups(self, headers: Dict[str, str]):
        """Testar CRUD de subgrupos"""
        self.log("📋 Testando CRUD de subgrupos...")
        
        try:
            response = requests.get(f"{self.base_url}/api/v1/financial/subgroups", headers=headers)
            if response.status_code == 200:
                subgroups = response.json()
                self.test_results["crud_operations"]["subgroups_get"] = {
                    "status": "✅ OK",
                    "count": len(subgroups) if isinstance(subgroups, list) else 0,
                    "sample": subgroups[:2] if isinstance(subgroups, list) and len(subgroups) > 0 else None
                }
                self.log(f"✅ GET subgrupos: {len(subgroups) if isinstance(subgroups, list) else 0} registros")
                
                if isinstance(subgroups, list) and len(subgroups) > 0:
                    self.analyze_mock_data("subgroups", subgroups)
            else:
                self.test_results["crud_operations"]["subgroups_get"] = f"❌ Status: {response.status_code}"
                
        except Exception as e:
            self.log(f"❌ Erro no CRUD subgrupos: {e}", "ERROR")
    
    def test_crud_forecasts(self, headers: Dict[str, str]):
        """Testar CRUD de previsões"""
        self.log("🔮 Testando CRUD de previsões...")
        
        try:
            response = requests.get(f"{self.base_url}/api/v1/financial/forecast", headers=headers)
            if response.status_code == 200:
                forecasts = response.json()
                self.test_results["crud_operations"]["forecasts_get"] = {
                    "status": "✅ OK",
                    "count": len(forecasts) if isinstance(forecasts, list) else 0,
                    "sample": forecasts[:2] if isinstance(forecasts, list) and len(forecasts) > 0 else None
                }
                self.log(f"✅ GET previsões: {len(forecasts) if isinstance(forecasts, list) else 0} registros")
                
                if isinstance(forecasts, list) and len(forecasts) > 0:
                    self.analyze_mock_data("forecasts", forecasts)
            else:
                self.test_results["crud_operations"]["forecasts_get"] = f"❌ Status: {response.status_code}"
                
        except Exception as e:
            self.log(f"❌ Erro no CRUD previsões: {e}", "ERROR")
    
    def analyze_mock_data(self, entity_type: str, data: List[Dict]):
        """Analisar dados para identificar se são mock"""
        self.log(f"🔍 Analisando dados mock em {entity_type}...")
        
        mock_indicators = {
            "test": ["test", "teste", "mock", "fake", "demo"],
            "generic_names": ["exemplo", "sample", "demo", "placeholder"],
            "generic_values": [0, 1, 100, 1000, 999.99]
        }
        
        mock_count = 0
        total_count = len(data)
        
        for item in data:
            is_mock = False
            
            # Verificar campos de texto
            for key, value in item.items():
                if isinstance(value, str):
                    if any(indicator in value.lower() for indicator in mock_indicators["test"]):
                        is_mock = True
                        break
                    if any(indicator in value.lower() for indicator in mock_indicators["generic_names"]):
                        is_mock = True
                        break
                        
            # Verificar valores genéricos
            if not is_mock:
                for key, value in item.items():
                    if isinstance(value, (int, float)):
                        if value in mock_indicators["generic_values"]:
                            is_mock = True
                            break
                            
            if is_mock:
                mock_count += 1
        
        mock_percentage = (mock_count / total_count * 100) if total_count > 0 else 0
        
        self.test_results["mock_data"][entity_type] = {
            "total_records": total_count,
            "mock_records": mock_count,
            "mock_percentage": round(mock_percentage, 2),
            "sample_record": data[0] if data else None
        }
        
        self.log(f"📊 {entity_type}: {mock_count}/{total_count} ({mock_percentage:.1f}%) dados mock")
    
    def test_business_logic(self):
        """Testar lógica de negócio baseada na metodologia Ana Paula"""
        self.log("🏢 Testando lógica de negócio...")
        
        # Baseado na planilha da Ana Paula, verificar estrutura de contas
        expected_groups = [
            "Receita",
            "Receita Financeira", 
            "Deduções",
            "Custos",
            "Despesas Operacionais",
            "Despesas Financeiras",
            "Investimentos",
            "Patrimônio"
        ]
        
        expected_subgroups = [
            "Receita",
            "Receita Financeira",
            "Deduções da receita",
            "Custos com Mercadorias Vendidas",
            "Custos com Serviços Prestados",
            "Despesas com Pessoal",
            "Despesas Comerciais",
            "Despesas Marketing",
            "Despesas Administrativas"
        ]
        
        self.test_results["business_logic"]["expected_structure"] = {
            "groups": expected_groups,
            "subgroups": expected_subgroups
        }
        
        self.log(f"📋 Estrutura esperada: {len(expected_groups)} grupos, {len(expected_subgroups)} subgrupos")
        
        # Verificar se há dados sobre metodologia específica
        if self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            try:
                # Verificar se existe endpoint de relatórios
                response = requests.get(f"{self.base_url}/api/v1/financial/reports", headers=headers)
                if response.status_code == 200:
                    self.test_results["business_logic"]["reports_endpoint"] = "✅ OK"
                    self.log("✅ Endpoint de relatórios disponível")
                else:
                    self.test_results["business_logic"]["reports_endpoint"] = f"❌ Status: {response.status_code}"
                    
                # Verificar se existe endpoint de fluxo de caixa
                response = requests.get(f"{self.base_url}/api/v1/financial/cash-flow", headers=headers)
                if response.status_code == 200:
                    self.test_results["business_logic"]["cash_flow_endpoint"] = "✅ OK"
                    self.log("✅ Endpoint de fluxo de caixa disponível")
                else:
                    self.test_results["business_logic"]["cash_flow_endpoint"] = f"❌ Status: {response.status_code}"
                    
            except Exception as e:
                self.log(f"❌ Erro na lógica de negócio: {e}", "ERROR")
    
    def test_frontend_pages(self):
        """Testar páginas do frontend"""
        self.log("🌐 Testando páginas do frontend...")
        
        pages_to_test = [
            "/",
            "/login",
            "/dashboard", 
            "/transactions",
            "/accounts",
            "/groups",
            "/subgroups",
            "/forecast",
            "/reports",
            "/settings"
        ]
        
        for page in pages_to_test:
            try:
                response = requests.get(f"{self.frontend_url}{page}", timeout=5)
                if response.status_code == 200:
                    self.test_results["frontend_pages"][page] = "✅ OK"
                    self.log(f"✅ Página {page}: OK")
                else:
                    self.test_results["frontend_pages"][page] = f"❌ Status: {response.status_code}"
                    self.log(f"❌ Página {page}: {response.status_code}")
            except Exception as e:
                self.test_results["frontend_pages"][page] = f"❌ Error: {str(e)}"
                self.log(f"❌ Erro na página {page}: {e}", "ERROR")
    
    def generate_recommendations(self):
        """Gerar recomendações baseadas nos testes"""
        self.log("💡 Gerando recomendações...")
        
        recommendations = []
        
        # Analisar autenticação
        if not self.auth_token:
            recommendations.append({
                "priority": "HIGH",
                "category": "Authentication",
                "issue": "Sistema de autenticação não funcional",
                "recommendation": "Implementar autenticação JWT funcional com credenciais de teste"
            })
        
        # Analisar dados mock
        total_mock = sum(
            data.get("mock_percentage", 0) 
            for data in self.test_results["mock_data"].values()
        )
        if total_mock > 50:
            recommendations.append({
                "priority": "HIGH", 
                "category": "Data",
                "issue": f"Alto percentual de dados mock ({total_mock:.1f}%)",
                "recommendation": "Implementar dados reais baseados na metodologia Ana Paula"
            })
        
        # Analisar CRUDs não funcionais
        failed_cruds = [
            key for key, value in self.test_results["crud_operations"].items()
            if isinstance(value, str) and "❌" in value
        ]
        if failed_cruds:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "CRUD Operations", 
                "issue": f"CRUDs não funcionais: {', '.join(failed_cruds)}",
                "recommendation": "Implementar operações CRUD completas para todas as entidades"
            })
        
        # Analisar lógica de negócio
        if not self.test_results["business_logic"].get("reports_endpoint", "").startswith("✅"):
            recommendations.append({
                "priority": "HIGH",
                "category": "Business Logic",
                "issue": "Relatórios financeiros não implementados",
                "recommendation": "Implementar relatórios baseados na metodologia Ana Paula (DRE, Fluxo de Caixa, etc.)"
            })
        
        # Analisar frontend
        failed_pages = [
            page for page, status in self.test_results["frontend_pages"].items()
            if not status.startswith("✅")
        ]
        if failed_pages:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Frontend",
                "issue": f"Páginas com problemas: {', '.join(failed_pages)}",
                "recommendation": "Corrigir páginas do frontend e implementar navegação completa"
            })
        
        self.test_results["recommendations"] = recommendations
        
        self.log(f"📋 {len(recommendations)} recomendações geradas")
    
    def run_complete_test(self):
        """Executar teste completo"""
        self.log("🚀 Iniciando teste E2E completo do FinaFlow...")
        
        # Testes básicos
        if not self.test_health_check():
            self.log("❌ Health check falhou. Abortando testes.", "ERROR")
            return False
        
        self.test_api_documentation()
        
        # Testes de funcionalidade
        self.test_authentication()
        self.test_crud_operations()
        self.test_business_logic()
        self.test_frontend_pages()
        
        # Análise e recomendações
        self.generate_recommendations()
        
        # Salvar resultados
        self.save_results()
        
        self.log("✅ Teste E2E completo finalizado!")
        return True
    
    def save_results(self):
        """Salvar resultados do teste"""
        filename = f"finaflow_e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            self.log(f"💾 Resultados salvos em: {filename}")
        except Exception as e:
            self.log(f"❌ Erro ao salvar resultados: {e}", "ERROR")
    
    def print_summary(self):
        """Imprimir resumo dos resultados"""
        print("\n" + "="*80)
        print("📊 RESUMO DO TESTE E2E - FinaFlow")
        print("="*80)
        
        # Status geral
        total_tests = len(self.test_results["api_endpoints"]) + len(self.test_results["crud_operations"])
        successful_tests = sum(1 for v in self.test_results["api_endpoints"].values() 
                              if isinstance(v, str) and "✅" in v)
        successful_tests += sum(1 for v in self.test_results["crud_operations"].values() 
                               if isinstance(v, dict) and v.get("status", "").startswith("✅"))
        
        print(f"🧪 Testes executados: {total_tests}")
        print(f"✅ Sucessos: {successful_tests}")
        print(f"❌ Falhas: {total_tests - successful_tests}")
        print(f"📈 Taxa de sucesso: {(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        # Dados mock
        if self.test_results["mock_data"]:
            print(f"\n📊 DADOS MOCK:")
            for entity, data in self.test_results["mock_data"].items():
                print(f"  {entity}: {data['mock_percentage']:.1f}% mock ({data['mock_records']}/{data['total_records']})")
        
        # Recomendações
        if self.test_results["recommendations"]:
            print(f"\n💡 PRINCIPAIS RECOMENDAÇÕES:")
            for i, rec in enumerate(self.test_results["recommendations"][:5], 1):
                print(f"  {i}. [{rec['priority']}] {rec['issue']}")
                print(f"     → {rec['recommendation']}")
        
        print("\n" + "="*80)

def main():
    """Função principal"""
    print("🧪 TESTE END-TO-END COMPLETO - FinaFlow")
    print("=" * 50)
    print("Contexto: SaaS baseado na metodologia financeira da Ana Paula")
    print("Objetivo: Mapear funcionalidades, dados mock e CRUDs")
    print("=" * 50)
    
    tester = FinaFlowE2ETest()
    
    try:
        success = tester.run_complete_test()
        tester.print_summary()
        
        if success:
            print("\n🎉 Teste concluído com sucesso!")
            print("📋 Verifique o arquivo JSON gerado para detalhes completos.")
        else:
            print("\n❌ Teste falhou. Verifique os logs acima.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Teste interrompido pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()







