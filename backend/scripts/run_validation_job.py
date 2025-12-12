#!/usr/bin/env python3
"""
Wrapper para executar validação do dashboard via Cloud Run Job.

Lê variáveis de ambiente e chama o script de validação principal.
"""

import sys
import os
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

def main():
    """Executa validação lendo variáveis de ambiente."""
    
    # Ler variáveis de ambiente
    excel_file = os.getenv("VALIDATION_EXCEL_FILE", "data/fluxo_caixa_2025.xlsx")
    year = int(os.getenv("VALIDATION_YEAR", "2025"))
    backend_url = os.getenv(
        "BACKEND_URL",
        "https://finaflow-backend-staging-642830139828.us-central1.run.app"
    )
    
    # Validar arquivo existe
    excel_path = backend_path / excel_file
    if not excel_path.exists():
        print(f"❌ Erro: Arquivo Excel não encontrado: {excel_path}")
        sys.exit(1)
    
    print(f"📊 Iniciando validação do dashboard...")
    print(f"   Arquivo: {excel_file}")
    print(f"   Ano: {year}")
    print(f"   Backend URL: {backend_url}")
    print("")
    
    # Importar e chamar o script de validação
    try:
        from scripts.validate_dashboard_against_client_sheet import main as validate_main
        
        # Construir argumentos como se fossem CLI
        sys.argv = [
            "validate_dashboard_against_client_sheet.py",
            "--file", str(excel_path),
            "--year", str(year),
            "--backend-url", backend_url
        ]
        
        # Executar validação (já faz sys.exit internamente)
        validate_main()
        
    except Exception as e:
        import traceback
        print(f"❌ Erro ao executar validação: {e}")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()

