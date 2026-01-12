#!/usr/bin/env python3
"""
Script para testar o seed diretamente e identificar o problema
"""

import sys
import os
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.database import SessionLocal
from app.models.auth import Tenant, BusinessUnit, User
from scripts.seed_from_client_sheet import (
    seed_plano_contas,
    seed_lancamentos_previstos,
    seed_lancamentos_diarios,
    logger
)

# IDs conhecidos
TENANT_ID = 'ed987f9e-8a32-440e-a7fc-ffeb56368d7c'
BU_ID = 'b365bbaa-7796-47a8-a8e3-a0812c694c85'

# URL da planilha
SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ/edit?gid=1158090564#gid=1158090564'

def download_spreadsheet():
    """Baixa a planilha do Google Sheets"""
    import requests
    import re
    import tempfile
    
    # Converter URL
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9_-]+)', SPREADSHEET_URL)
    if match:
        sheet_id = match.group(1)
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    else:
        export_url = SPREADSHEET_URL.replace("/edit", "/export?format=xlsx")
    
    print(f"📥 Baixando planilha de: {export_url}")
    response = requests.get(export_url, timeout=60)
    response.raise_for_status()
    
    # Salvar temporariamente
    data_dir = backend_path / "data"
    data_dir.mkdir(exist_ok=True)
    excel_file = data_dir / "test_onboarding.xlsx"
    
    with open(excel_file, "wb") as f:
        f.write(response.content)
    
    print(f"✅ Planilha salva em: {excel_file}")
    return excel_file

def main():
    print("="*80)
    print("🧪 TESTE DIRETO DO SEED")
    print("="*80)
    print()
    
    # Baixar planilha
    excel_file = download_spreadsheet()
    
    # Conectar ao banco
    db = SessionLocal()
    try:
        # Buscar tenant, BU e user
        tenant = db.query(Tenant).filter(Tenant.id == TENANT_ID).first()
        if not tenant:
            print(f"❌ Tenant {TENANT_ID} não encontrado")
            return 1
        
        business_unit = db.query(BusinessUnit).filter(BusinessUnit.id == BU_ID).first()
        if not business_unit:
            print(f"❌ Business Unit {BU_ID} não encontrado")
            return 1
        
        user = db.query(User).filter(User.email == "qa@finaflow.test").first()
        if not user:
            print(f"❌ Usuário qa@finaflow.test não encontrado")
            return 1
        
        print(f"✅ Tenant: {tenant.name}")
        print(f"✅ Business Unit: {business_unit.name}")
        print(f"✅ User: {user.email}")
        print()
        
        # Resetar stats do logger
        logger.stats = {
            'grupos_criados': 0,
            'grupos_existentes': 0,
            'subgrupos_criados': 0,
            'subgrupos_existentes': 0,
            'contas_criadas': 0,
            'contas_existentes': 0,
            'lancamentos_diarios_criados': 0,
            'lancamentos_diarios_existentes': 0,
            'lancamentos_previstos_criados': 0,
            'lancamentos_previstos_existentes': 0,
            'linhas_ignoradas': 0,
            'erros': []
        }
        
        # 1. Plano de contas
        print("1️⃣ Importando Plano de Contas...")
        grupos_map, subgrupos_map, contas_map = seed_plano_contas(db, tenant, excel_file)
        print(f"   ✅ Grupos: {len(grupos_map)}, Subgrupos: {len(subgrupos_map)}, Contas: {len(contas_map)}")
        print()
        
        # 2. Lançamentos previstos
        print("2️⃣ Importando Lançamentos Previstos...")
        previstos_before = logger.stats['lancamentos_previstos_criados']
        seed_lancamentos_previstos(db, tenant, business_unit, user, grupos_map, subgrupos_map, contas_map, excel_file)
        db.commit()
        previstos_after = logger.stats['lancamentos_previstos_criados']
        previstos_count = previstos_after - previstos_before
        print(f"   ✅ Lançamentos Previstos criados: {previstos_count}")
        print(f"   📊 Stats: {logger.stats}")
        print()
        
        # 3. Lançamentos diários
        print("3️⃣ Importando Lançamentos Diários...")
        diarios_before = logger.stats['lancamentos_diarios_criados']
        seed_lancamentos_diarios(db, tenant, business_unit, user, grupos_map, subgrupos_map, contas_map, excel_file)
        db.commit()
        diarios_after = logger.stats['lancamentos_diarios_criados']
        diarios_count = diarios_after - diarios_before
        print(f"   ✅ Lançamentos Diários criados: {diarios_count}")
        print(f"   📊 Stats: {logger.stats}")
        print()
        
        # Verificar no banco
        from app.models.lancamento_diario import LancamentoDiario
        from app.models.lancamento_previsto import LancamentoPrevisto
        
        db_diarios = db.query(LancamentoDiario).filter(
            LancamentoDiario.tenant_id == tenant.id,
            LancamentoDiario.business_unit_id == business_unit.id
        ).count()
        
        db_previstos = db.query(LancamentoPrevisto).filter(
            LancamentoPrevisto.tenant_id == tenant.id,
            LancamentoPrevisto.business_unit_id == business_unit.id
        ).count()
        
        print("="*80)
        print("📊 RESULTADO FINAL")
        print("="*80)
        print(f"Lançamentos Diários no banco: {db_diarios}")
        print(f"Lançamentos Previstos no banco: {db_previstos}")
        print(f"Stats do logger: {logger.stats}")
        print("="*80)
        
        if db_diarios == 0 and db_previstos == 0:
            print("❌ PROBLEMA: Nenhum lançamento foi criado no banco!")
            if logger.stats['erros']:
                print("\nErros encontrados:")
                for err in logger.stats['erros']:
                    print(f"   - {err}")
            return 1
        else:
            print("✅ Sucesso! Lançamentos foram criados.")
            return 0
        
    except Exception as e:
        import traceback
        print(f"❌ Erro: {e}")
        print(traceback.format_exc())
        return 1
    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(main())



