#!/usr/bin/env python3
"""
🎯 TESTE FRONTEND LOCAL SIMPLES - VALIDAÇÃO RÁPIDA
"""

import requests
import time

def test_frontend_simples():
    """Teste simples do frontend local"""
    print("🎯 TESTE FRONTEND LOCAL SIMPLES - VALIDAÇÃO RÁPIDA")
    print("=" * 60)
    
    # Testar diferentes portas
    portas = [3000, 3001, 8080, 8000]
    
    for porta in portas:
        try:
            print(f"1️⃣ TESTANDO PORTA {porta}...")
            response = requests.get(f"http://localhost:{porta}", timeout=5)
            print(f"   ✅ Porta {porta} respondendo: {response.status_code}")
            
            # Testar página de login
            login_response = requests.get(f"http://localhost:{porta}/login", timeout=5)
            print(f"   ✅ Login página: {login_response.status_code}")
            
            # Testar página de transações
            transactions_response = requests.get(f"http://localhost:{porta}/transactions", timeout=5)
            print(f"   ✅ Transactions página: {transactions_response.status_code}")
            
            # Verificar conteúdo
            if "FinaFlow" in transactions_response.text or "finaFlow" in transactions_response.text:
                print(f"   ✅ Conteúdo FinaFlow encontrado na porta {porta}")
                
                # Verificar se é a nova estrutura
                new_indicators = ["Lançamentos Financeiros", "Lançamentos Diários", "Data Movimentação"]
                found = [ind for ind in new_indicators if ind in transactions_response.text]
                
                if found:
                    print(f"   🎉 NOVA ESTRUTURA DETECTADA na porta {porta}!")
                    print(f"   📋 Indicadores encontrados: {found}")
                    return porta, True
                else:
                    print(f"   ⚠️ Estrutura antiga na porta {porta}")
                    return porta, False
            else:
                print(f"   ❌ Conteúdo FinaFlow não encontrado na porta {porta}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Porta {porta} não está respondendo")
        except requests.exceptions.Timeout:
            print(f"   ❌ Porta {porta} timeout")
        except Exception as e:
            print(f"   ❌ Erro na porta {porta}: {str(e)}")
    
    return None, False

if __name__ == "__main__":
    porta, sucesso = test_frontend_simples()
    
    print("\n" + "=" * 60)
    if porta and sucesso:
        print("🎉 FRONTEND LOCAL FUNCIONANDO!")
        print(f"✅ Porta: {porta}")
        print("✅ Nova estrutura detectada")
        print("✅ Sistema refatorado funcionando localmente")
        print("\n⚠️ PROBLEMA: Vercel com falhas hoje (20/10/2025)")
        print("✅ SOLUÇÃO: Sistema funcionando localmente")
    elif porta:
        print("⚠️ FRONTEND LOCAL FUNCIONANDO COM ESTRUTURA ANTIGA")
        print(f"✅ Porta: {porta}")
        print("❌ Estrutura antiga ainda presente")
    else:
        print("❌ FRONTEND LOCAL NÃO ESTÁ FUNCIONANDO")
        print("🔍 Verifique se o frontend está rodando")
    
    print("=" * 60)
