#!/usr/bin/env python3
"""
Wrapper para executar seed via Cloud Run Job.

Lê variáveis de ambiente e chama o script de seed principal.
"""

import sys
import os
from pathlib import Path

# Adicionar backend ao path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_EXCEL = os.path.join(BASE_DIR, "data", "fluxo_caixa_2025.xlsx")

sys.path.insert(0, BASE_DIR)

def main():
    """Executa seed lendo variáveis de ambiente."""
    
    # Ler variáveis de ambiente
    excel_file = os.getenv("SEED_EXCEL_FILE", DEFAULT_EXCEL)
    tenant_name = os.getenv("SEED_TENANT_NAME", "FinaFlow Staging")
    reset_data = os.getenv("SEED_RESET_DATA", "false").lower() == "true"
    
    # Converter para Path absoluto
    excel_path = Path(excel_file).resolve() if not os.path.isabs(excel_file) else Path(excel_file)
    
    # Validar arquivo existe com log claro
    if not excel_path.exists():
        print(f"[ERRO] Arquivo Excel não encontrado: {excel_path}", file=sys.stderr)
        print("[ERRO] Verifique se o arquivo foi copiado para a imagem Docker e se o caminho está correto.", file=sys.stderr)
        print(f"[INFO] Diretório atual: {os.getcwd()}", file=sys.stderr)
        print(f"[INFO] BASE_DIR: {BASE_DIR}", file=sys.stderr)
        print(f"[INFO] Tentando listar /app/data:", file=sys.stderr)
        try:
            data_dir = Path("/app/data")
            if data_dir.exists():
                print(f"[INFO] Arquivos em /app/data: {list(data_dir.iterdir())}", file=sys.stderr)
            else:
                print(f"[INFO] /app/data não existe", file=sys.stderr)
        except Exception as e:
            print(f"[INFO] Erro ao listar /app/data: {e}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"[INFO] Usando arquivo Excel: {excel_path}")
    
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

