#!/usr/bin/env python3
"""
Script para limpar Business Units duplicadas
Mantém apenas uma BU por tenant (a mais antiga)
"""

import os
import sys
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.database import SessionLocal
from app.models.auth import Tenant, BusinessUnit, User, UserBusinessUnitAccess
from sqlalchemy import func
from collections import defaultdict
from datetime import datetime

def clean_duplicate_business_units():
    """Remove Business Units duplicadas, mantendo apenas uma por tenant"""
    db = SessionLocal()
    
    try:
        print("🔍 Analisando Business Units duplicadas...\n")
        
        # Agrupar BUs por tenant_id e name
        all_bus = db.query(BusinessUnit).order_by(BusinessUnit.created_at).all()
        
        # Agrupar por (tenant_id, name)
        groups = defaultdict(list)
        for bu in all_bus:
            key = (bu.tenant_id, bu.name)
            groups[key].append(bu)
        
        # Identificar duplicatas
        duplicates_found = False
        total_to_delete = 0
        
        for (tenant_id, name), bus in groups.items():
            if len(bus) > 1:
                duplicates_found = True
                tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
                tenant_name = tenant.name if tenant else "Desconhecido"
                
                print(f"⚠️  Encontradas {len(bus)} BUs duplicadas:")
                print(f"   Tenant: {tenant_name} ({tenant_id})")
                print(f"   Nome da BU: {name}")
                print(f"   BUs:")
                
                # Ordenar por data de criação (mais antiga primeiro)
                bus_sorted = sorted(bus, key=lambda x: x.created_at or datetime.min)
                
                # Manter a primeira (mais antiga)
                keep_bu = bus_sorted[0]
                to_delete = bus_sorted[1:]
                
                print(f"      ✅ MANTER: {keep_bu.id} (criada em {keep_bu.created_at})")
                
                for bu in to_delete:
                    print(f"      ❌ DELETAR: {bu.id} (criada em {bu.created_at})")
                    total_to_delete += 1
                
                print()
        
        if not duplicates_found:
            print("✅ Nenhuma duplicata encontrada!")
            return
        
        print(f"\n📊 Resumo:")
        print(f"   Total de duplicatas a remover: {total_to_delete}")
        
        # Confirmar
        response = input("\n❓ Deseja prosseguir com a remoção? (sim/não): ").strip().lower()
        if response not in ['sim', 's', 'yes', 'y']:
            print("❌ Operação cancelada.")
            return
        
        # Remover duplicatas
        deleted_count = 0
        for (tenant_id, name), bus in groups.items():
            if len(bus) > 1:
                # Ordenar por data de criação
                bus_sorted = sorted(bus, key=lambda x: x.created_at or datetime.min)
                keep_bu = bus_sorted[0]
                to_delete = bus_sorted[1:]
                
                for bu in to_delete:
                    # Verificar se há usuários associados
                    users_count = db.query(User).filter(User.business_unit_id == bu.id).count()
                    access_count = db.query(UserBusinessUnitAccess).filter(
                        UserBusinessUnitAccess.business_unit_id == bu.id
                    ).count()
                    
                    if users_count > 0 or access_count > 0:
                        print(f"⚠️  BU {bu.id} tem {users_count} usuários e {access_count} acessos associados.")
                        print(f"   Migrando para BU {keep_bu.id}...")
                        
                        # Migrar usuários
                        db.query(User).filter(User.business_unit_id == bu.id).update({
                            User.business_unit_id: keep_bu.id
                        })
                        
                        # Migrar acessos
                        db.query(UserBusinessUnitAccess).filter(
                            UserBusinessUnitAccess.business_unit_id == bu.id
                        ).update({
                            UserBusinessUnitAccess.business_unit_id: keep_bu.id
                        })
                    
                    # Deletar BU
                    db.delete(bu)
                    deleted_count += 1
                    print(f"✅ BU {bu.id} removida")
        
        db.commit()
        print(f"\n✅ Limpeza concluída! {deleted_count} Business Units removidas.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    clean_duplicate_business_units()

