#!/usr/bin/env python3
"""
Wrapper para executar seed via Cloud Run Job.

Lê variáveis de ambiente e chama o script de seed principal.
"""

import sys
import os
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

def main():
    """Executa seed lendo variáveis de ambiente."""
    
    # Ler variáveis de ambiente
    excel_file = os.getenv("SEED_EXCEL_FILE", "data/fluxo_caixa_2025.xlsx")
    tenant_name = os.getenv("SEED_TENANT_NAME", "FinaFlow Staging")
    reset_data = os.getenv("SEED_RESET_DATA", "false").lower() == "true"
    
    # Validar arquivo existe
    excel_path = backend_path / excel_file
    if not excel_path.exists():
        print(f"❌ Erro: Arquivo Excel não encontrado: {excel_path}")
        sys.exit(1)
    
    print(f"🌱 Iniciando seed do banco de dados...")
    print(f"   Arquivo: {excel_file}")
    print(f"   Tenant: {tenant_name}")
    print(f"   Reset dados: {reset_data}")
    print("")
    
    # Importar e chamar o script de seed
    try:
        from scripts.seed_from_client_sheet import main as seed_main
        
        # Construir argumentos como se fossem CLI
        sys.argv = [
            "seed_from_client_sheet.py",
            "--file", str(excel_path),
        ]
        
        if reset_data:
            sys.argv.append("--reset-data")
        
        # Executar seed (já faz sys.exit internamente em caso de erro)
        seed_main()
        
        # Se chegou aqui, foi sucesso
        print("\n✅ Seed concluído com sucesso!")
        sys.exit(0)
        
    except SystemExit as e:
        # Re-raise SystemExit para preservar exit code
        raise
    except Exception as e:
        import traceback
        print(f"❌ Erro ao executar seed: {e}")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()

