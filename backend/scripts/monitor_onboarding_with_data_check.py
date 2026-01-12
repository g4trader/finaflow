#!/usr/bin/env python3
"""
Script de monitoramento robusto do onboarding
Verifica tanto o status quanto os dados no banco para detectar progresso real
"""

import requests
import time
import json
import sys

BACKEND_URL = 'https://finaflow-backend-staging-556803510516.us-central1.run.app'
TENANT_ID = 'ed987f9e-8a32-440e-a7fc-ffeb56368d7c'
BU_ID = 'b365bbaa-7796-47a8-a8e3-a0812c694c85'

def login():
    """Faz login e retorna token"""
    response = requests.post(
        f'{BACKEND_URL}/api/v1/auth/login',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        data='username=qa@finaflow.test&password=QaFinaflow123!',
        timeout=10
    )
    if response.status_code != 200:
        raise Exception(f"Erro no login: {response.status_code}")
    return response.json()['access_token']

def get_status(headers):
    """Busca status do onboarding"""
    try:
        response = requests.get(
            f'{BACKEND_URL}/api/v1/onboarding/status/{TENANT_ID}/{BU_ID}',
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_data_counts(headers):
    """Busca contagem de dados no banco"""
    try:
        # Selecionar BU
        select_response = requests.post(
            f'{BACKEND_URL}/api/v1/auth/select-business-unit',
            headers=headers,
            json={'business_unit_id': BU_ID},
            timeout=10
        )
        
        if select_response.status_code != 200:
            return None
        
        new_token = select_response.json()['access_token']
        headers_data = {'Authorization': f'Bearer {new_token}'}
        
        # Buscar contagens
        diarios_response = requests.get(
            f'{BACKEND_URL}/api/v1/lancamentos-diarios?limit=1',
            headers=headers_data,
            timeout=10
        )
        
        previstos_response = requests.get(
            f'{BACKEND_URL}/api/v1/lancamentos-previstos?limit=1',
            headers=headers_data,
            timeout=10
        )
        
        diarios_count = 0
        previstos_count = 0
        
        if diarios_response.status_code == 200:
            diarios_count = diarios_response.json().get('total', 0)
        
        if previstos_response.status_code == 200:
            previstos_count = previstos_response.json().get('total', 0)
        
        return {
            'diarios': diarios_count,
            'previstos': previstos_count
        }
    except Exception as e:
        print(f"⚠️  Erro ao buscar dados: {e}")
        return None

def main():
    print("="*80)
    print("📊 MONITORAMENTO ROBUSTO DO ONBOARDING")
    print("="*80)
    print(f"Tenant ID: {TENANT_ID}")
    print(f"Business Unit ID: {BU_ID}")
    print("="*80)
    print()
    
    # Login
    print("🔐 Fazendo login...")
    token = login()
    headers = {'Authorization': f'Bearer {token}'}
    print("✅ Login bem-sucedido\n")
    
    # Variáveis de monitoramento
    last_status_progress = -1
    last_diarios_count = 0
    last_previstos_count = 0
    stuck_count = 0
    data_changing = False
    
    print("📊 Iniciando monitoramento...")
    print("   (Verificando status E dados no banco a cada 30 segundos)\n")
    
    start_time = time.time()
    max_duration = 3600  # 1 hora
    
    for i in range(max_duration // 30):  # Verificar a cada 30 segundos por até 1 hora
        elapsed = time.time() - start_time
        elapsed_min = int(elapsed // 60)
        elapsed_sec = int(elapsed % 60)
        
        # Buscar status
        status = get_status(headers)
        
        # Buscar dados
        data_counts = get_data_counts(headers)
        
        # Processar status
        if status:
            progress = status.get('progress', 0)
            step = status.get('current_step', '')
            message = status.get('message', '')
            status_type = status.get('status', '')
            
            # Verificar se status mudou
            status_changed = progress != last_status_progress or step != last_status_progress
            
            # Processar dados
            if data_counts:
                diarios_count = data_counts['diarios']
                previstos_count = data_counts['previstos']
                
                # Verificar se dados estão mudando
                diarios_changing = diarios_count > last_diarios_count
                previstos_changing = previstos_count > last_previstos_count
                data_changing = diarios_changing or previstos_changing
                
                # Log estruturado
                print(f"[{elapsed_min:02d}:{elapsed_sec:02d}] Status: {progress}% | {step}")
                if message:
                    print(f"         Mensagem: {message}")
                print(f"         Dados no banco: Diários={diarios_count} (+{diarios_count - last_diarios_count}) | Previstos={previstos_count} (+{previstos_count - last_previstos_count})")
                
                if data_changing:
                    print(f"         ✅ DADOS ESTÃO SENDO IMPORTADOS (progresso real detectado)")
                    stuck_count = 0
                elif status_changed:
                    print(f"         📊 Status atualizado")
                    stuck_count = 0
                else:
                    stuck_count += 1
                    if stuck_count > 2:
                        print(f"         ⚠️  Sem mudanças há {stuck_count * 30} segundos")
                
                last_diarios_count = diarios_count
                last_previstos_count = previstos_count
            else:
                print(f"[{elapsed_min:02d}:{elapsed_sec:02d}] Status: {progress}% | {step}")
                if message:
                    print(f"         Mensagem: {message}")
                print(f"         ⚠️  Não foi possível verificar dados no banco")
            
            last_status_progress = progress
            
            # Verificar conclusão
            if status_type == 'completed':
                print("\n" + "="*80)
                print("✅✅✅ ONBOARDING CONCLUÍDO!")
                print("="*80)
                
                if status.get('stats'):
                    print("\n📊 Estatísticas do onboarding:")
                    for key, value in status['stats'].items():
                        print(f"   {key}: {value}")
                
                if data_counts:
                    print(f"\n📊 Dados finais no banco:")
                    print(f"   Lançamentos Diários: {data_counts['diarios']}")
                    print(f"   Lançamentos Previstos: {data_counts['previstos']}")
                
                # Buscar totais financeiros
                try:
                    select_response = requests.post(
                        f'{BACKEND_URL}/api/v1/auth/select-business-unit',
                        headers=headers,
                        json={'business_unit_id': BU_ID},
                        timeout=10
                    )
                    
                    if select_response.status_code == 200:
                        new_token = select_response.json()['access_token']
                        headers_final = {'Authorization': f'Bearer {new_token}'}
                        
                        annual_response = requests.get(
                            f'{BACKEND_URL}/api/v1/financial/annual-summary?year=2025',
                            headers=headers_final,
                            timeout=10
                        )
                        
                        if annual_response.status_code == 200:
                            annual_data = annual_response.json()
                            totals = annual_data.get('totals', {})
                            print(f"\n💰 Totais Financeiros 2025:")
                            print(f"   Receita: R$ {totals.get('revenue', 0):,.2f}")
                            print(f"   Despesa: R$ {totals.get('expense', 0):,.2f}")
                            print(f"   Custo: R$ {totals.get('cost', 0):,.2f}")
                            print(f"   Saldo: R$ {totals.get('balance', 0):,.2f}")
                except:
                    pass
                
                print("="*80)
                return 0
            elif status_type == 'error':
                print("\n" + "="*80)
                print("❌ ERRO NO ONBOARDING")
                print("="*80)
                print(f"Erro: {message}")
                if status.get('errors'):
                    print("\nDetalhes dos erros:")
                    for err in status['errors']:
                        print(f"   - {err}")
                print("="*80)
                return 1
        else:
            print(f"[{elapsed_min:02d}:{elapsed_sec:02d}] ⚠️  Não foi possível buscar status")
        
        print()  # Linha em branco entre verificações
        time.sleep(30)  # Aguardar 30 segundos
    
    print("\n" + "="*80)
    print("⚠️  TIMEOUT APÓS 1 HORA")
    print("="*80)
    print("Verificando estado final...")
    
    # Verificação final
    data_counts = get_data_counts(headers)
    if data_counts:
        print(f"\n📊 Dados no banco (estado final):")
        print(f"   Lançamentos Diários: {data_counts['diarios']}")
        print(f"   Lançamentos Previstos: {data_counts['previstos']}")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())



