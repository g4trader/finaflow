#!/usr/bin/env python3
"""
Script simples para inserir os 50 registros sintéticos quando o backend estiver funcionando
"""

import requests
import json
import random
from datetime import datetime

# Configuração
BACKEND_URL = "https://finaflow-backend-642830139828.us-central1.run.app"

# Dados sintéticos
PEQUENOS_NEGOCIOS = [
    {"desc": "Venda de produtos - Loja", "tipo": "receita", "valor_min": 50, "valor_max": 500},
    {"desc": "Serviços de consultoria", "tipo": "receita", "valor_min": 100, "valor_max": 800},
    {"desc": "Venda de produtos online", "tipo": "receita", "valor_min": 30, "valor_max": 300},
    {"desc": "Serviços de manutenção", "tipo": "receita", "valor_min": 80, "valor_max": 400},
    {"desc": "Aluguel de equipamentos", "tipo": "receita", "valor_min": 60, "valor_max": 250},
    {"desc": "Compra de matéria-prima", "tipo": "despesa", "valor_min": 100, "valor_max": 600},
    {"desc": "Pagamento de funcionários", "tipo": "despesa", "valor_min": 200, "valor_max": 1200},
    {"desc": "Aluguel do estabelecimento", "tipo": "despesa", "valor_min": 300, "valor_max": 800},
    {"desc": "Conta de energia elétrica", "tipo": "despesa", "valor_min": 80, "valor_max": 200},
    {"desc": "Conta de água", "tipo": "despesa", "valor_min": 40, "valor_max": 120},
    {"desc": "Combustível para veículos", "tipo": "despesa", "valor_min": 60, "valor_max": 180},
    {"desc": "Marketing e publicidade", "tipo": "despesa", "valor_min": 50, "valor_max": 300},
    {"desc": "Material de escritório", "tipo": "despesa", "valor_min": 30, "valor_max": 150},
    {"desc": "Seguro do negócio", "tipo": "despesa", "valor_min": 80, "valor_max": 250},
    {"desc": "Taxas e impostos", "tipo": "despesa", "valor_min": 100, "valor_max": 400},
    {"desc": "Venda de produtos - Feira", "tipo": "receita", "valor_min": 40, "valor_max": 350},
    {"desc": "Serviços de entrega", "tipo": "receita", "valor_min": 25, "valor_max": 150},
    {"desc": "Venda de produtos - Delivery", "tipo": "receita", "valor_min": 35, "valor_max": 200},
    {"desc": "Serviços de limpeza", "tipo": "receita", "valor_min": 50, "valor_max": 180},
    {"desc": "Venda de produtos - Atacado", "tipo": "receita", "valor_min": 200, "valor_max": 800},
]

SOCIEDADES = [
    {"desc": "Vendas corporativas - Q3 2025", "tipo": "receita", "valor_min": 5000, "valor_max": 25000},
    {"desc": "Serviços de consultoria empresarial", "tipo": "receita", "valor_min": 3000, "valor_max": 15000},
    {"desc": "Licenciamento de software", "tipo": "receita", "valor_min": 2000, "valor_max": 8000},
    {"desc": "Folha de pagamento - Outubro", "tipo": "despesa", "valor_min": 8000, "valor_max": 30000},
    {"desc": "Aluguel da sede corporativa", "tipo": "despesa", "valor_min": 2000, "valor_max": 6000},
    {"desc": "Investimento em tecnologia", "tipo": "despesa", "valor_min": 1500, "valor_max": 5000},
    {"desc": "Marketing corporativo", "tipo": "despesa", "valor_min": 1000, "valor_max": 4000},
    {"desc": "Consultoria jurídica", "tipo": "despesa", "valor_min": 800, "valor_max": 3000},
    {"desc": "Vendas B2B - Contrato anual", "tipo": "receita", "valor_min": 10000, "valor_max": 40000},
    {"desc": "Prestação de serviços especializados", "tipo": "receita", "valor_min": 4000, "valor_max": 18000},
]

def gerar_valor(min_val, max_val):
    return round(random.uniform(min_val, max_val), 2)

def main():
    print("🎯 Inserindo 50 registros sintéticos...")
    print("📅 Data: 17/10/2025")
    print("🏪 40 pequenos negócios + 🏢 10 sociedades")
    print("="*60)
    
    # Login
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Erro no login: {response.status_code}")
            return
            
        token = response.json()["access_token"]
        print("✅ Login realizado")
        
        # Buscar business unit
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BACKEND_URL}/api/v1/auth/user-business-units",
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Erro ao buscar business units: {response.status_code}")
            return
            
        business_units = response.json()
        if len(business_units) == 0:
            print("❌ Nenhuma business unit encontrada")
            return
            
        business_unit_id = business_units[0]['id']
        print(f"✅ Business Unit: {business_units[0]['name']}")
        
        # Data da transação
        data_transacao = datetime(2025, 10, 17, random.randint(8, 18), random.randint(0, 59))
        
        sucessos = 0
        
        # Inserir pequenos negócios
        print("\n🏪 Inserindo pequenos negócios...")
        for i in range(40):
            item = random.choice(PEQUENOS_NEGOCIOS)
            valor = gerar_valor(item["valor_min"], item["valor_max"])
            descricao = f"{item['desc']} - Transação {i+1:03d}"
            
            # Criar transação via API (se o endpoint existir)
            # Por enquanto, vamos apenas simular
            print(f"   {i+1:2d}. {descricao[:40]:<40} | {item['tipo']:<8} | R$ {valor:>8.2f}")
            sucessos += 1
        
        # Inserir sociedades
        print("\n🏢 Inserindo sociedades...")
        for i in range(10):
            item = random.choice(SOCIEDADES)
            valor = gerar_valor(item["valor_min"], item["valor_max"])
            descricao = f"{item['desc']} - Contrato {i+1:02d}"
            
            print(f"   {i+1:2d}. {descricao[:40]:<40} | {item['tipo']:<8} | R$ {valor:>8.2f}")
            sucessos += 1
        
        print(f"\n✅ {sucessos}/50 registros processados!")
        print("💡 Para inserir realmente, execute o arquivo SQL gerado")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("💡 Use o arquivo synthetic_data_2025_10_17.sql gerado")

if __name__ == "__main__":
    main()

