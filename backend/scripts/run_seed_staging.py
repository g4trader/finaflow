#!/usr/bin/env python3
"""
Script wrapper para executar seed no STAGING e validar resultados
Executa seed, testa idempotência e gera relatório
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
import psycopg2

# Configuração
DATABASE_URL = "postgresql://finaflow_user:Finaflow123!@34.41.169.224:5432/finaflow"
BACKEND_DIR = Path(__file__).parent.parent
LOGS_DIR = BACKEND_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

def run_seed(log_suffix=""):
    """Executa o seed e retorna o output"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"staging_seed_{log_suffix}{timestamp}.log"
    
    env = os.environ.copy()
    env["DATABASE_URL"] = DATABASE_URL
    
    cmd = [
        sys.executable,
        "-m", "scripts.seed_from_client_sheet",
        "--file", "data/fluxo_caixa_2025.xlsx"
    ]
    
    print(f"🚀 Executando seed... (log: {log_file.name})")
    
    with open(log_file, 'w') as f:
        process = subprocess.Popen(
            cmd,
            cwd=str(BACKEND_DIR),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        output_lines = []
        for line in process.stdout:
            print(line, end='')
            f.write(line)
            output_lines.append(line)
        
        process.wait()
        f.flush()
    
    return process.returncode, output_lines, log_file

def validate_database():
    """Valida dados no banco"""
    print("\n" + "="*60)
    print("🧪 VALIDAÇÃO DO BANCO DE DADOS")
    print("="*60)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        queries = {
            "Grupos": "SELECT COUNT(*) FROM chart_account_groups;",
            "Subgrupos": "SELECT COUNT(*) FROM chart_account_subgroups;",
            "Contas": "SELECT COUNT(*) FROM chart_accounts;",
            "Lançamentos Diários": "SELECT COUNT(*) FROM lancamentos_diarios;",
            "Lançamentos Previstos": "SELECT COUNT(*) FROM lancamentos_previstos;",
        }
        
        results = {}
        for name, q in queries.items():
            cur.execute(q)
            count = cur.fetchone()[0]
            results[name] = count
            print(f"✅ {name}: {count}")
        
        cur.close()
        conn.close()
        
        return results
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        return None

def main():
    """Função principal"""
    print("="*60)
    print("🌱 EXECUÇÃO DO SEED STAGING + VALIDAÇÃO")
    print("="*60)
    print(f"📁 Diretório: {BACKEND_DIR}")
    print(f"📊 Logs: {LOGS_DIR}")
    print(f"🗄️  Banco: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'STAGING'}")
    print()
    
    # 1. Primeira execução
    print("\n" + "="*60)
    print("🥇 EXECUÇÃO 1 - SEED INICIAL")
    print("="*60)
    code1, output1, log1 = run_seed("")
    
    if code1 != 0:
        print(f"\n❌ Seed falhou com código {code1}")
        print(f"📄 Ver logs em: {log1}")
        return 1
    
    # 2. Validação após primeira execução
    results1 = validate_database()
    
    # 3. Segunda execução (idempotência)
    print("\n" + "="*60)
    print("🥈 EXECUÇÃO 2 - TESTE DE IDEMPOTÊNCIA")
    print("="*60)
    code2, output2, log2 = run_seed("idempotency_")
    
    if code2 != 0:
        print(f"\n❌ Seed (idempotência) falhou com código {code2}")
        print(f"📄 Ver logs em: {log2}")
        return 1
    
    # 4. Validação após segunda execução
    results2 = validate_database()
    
    # 5. Comparar resultados
    print("\n" + "="*60)
    print("📊 COMPARAÇÃO DE RESULTADOS (IDEMPOTÊNCIA)")
    print("="*60)
    
    if results1 and results2:
        for key in results1:
            diff = results2[key] - results1[key]
            status = "✅" if diff == 0 else "⚠️"
            print(f"{status} {key}: {results1[key]} → {results2[key]} (diff: {diff})")
    
    # 6. Resumo
    print("\n" + "="*60)
    print("✅ SEED EXECUTADO COM SUCESSO!")
    print("="*60)
    print(f"📄 Log execução 1: {log1.name}")
    print(f"📄 Log execução 2: {log2.name}")
    print(f"📊 Resultados finais:")
    if results2:
        for key, value in results2.items():
            print(f"   - {key}: {value}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

