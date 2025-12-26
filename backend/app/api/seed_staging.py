"""
Endpoint temporário para executar seed no STAGING
ATENÇÃO: Remover após execução do seed
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import JSONResponse
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import os
from typing import Dict, Any, Optional
import traceback

from app.services.dependencies import get_current_active_user
from app.models.auth import User

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

@router.post("/run-migration-liquidation")
async def run_migration_liquidation(
    # Temporariamente sem autenticação para poder executar antes do login funcionar
    # TODO: Adicionar autenticação após migration
):
    """
    Executa a migration para adicionar liquidation_account_id à tabela lancamentos_diarios
    ATENÇÃO: Endpoint temporário sem autenticação - remover após uso
    """
    
    from sqlalchemy import text
    from app.database import engine
    
    # Executar migration diretamente via engine (sem usar modelos)
    try:
        # SQL da migration (inline para evitar problemas de arquivo)
        with engine.connect() as conn:
            # 0. Criar tabela liquidation_accounts se não existir
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS liquidation_accounts (
                        id VARCHAR(36) PRIMARY KEY,
                        tenant_id VARCHAR(36) NOT NULL,
                        business_unit_id VARCHAR(36),
                        code VARCHAR(20) NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        account_type VARCHAR(50) NOT NULL,
                        bank_name VARCHAR(100),
                        account_number VARCHAR(50),
                        current_balance NUMERIC(15, 2) DEFAULT 0,
                        initial_balance NUMERIC(15, 2) DEFAULT 0,
                        currency VARCHAR(10) DEFAULT 'BRL',
                        is_active BOOLEAN DEFAULT TRUE,
                        is_default BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT fk_liquidation_accounts_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                        CONSTRAINT fk_liquidation_accounts_bu FOREIGN KEY (business_unit_id) REFERENCES business_units(id)
                    )
                """))
                conn.commit()
            except Exception as e:
                if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                    raise
            
            # 1. Adicionar coluna se não existir
            try:
                conn.execute(text("""
                    ALTER TABLE lancamentos_diarios 
                    ADD COLUMN IF NOT EXISTS liquidation_account_id VARCHAR(36)
                """))
                conn.commit()
            except Exception as e:
                if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                    raise
            
            # 2. Adicionar foreign key se não existir (bloco DO completo)
            try:
                conn.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint 
                            WHERE conname = 'fk_lancamentos_diarios_liquidation_account'
                        ) THEN
                            ALTER TABLE lancamentos_diarios
                            ADD CONSTRAINT fk_lancamentos_diarios_liquidation_account
                            FOREIGN KEY (liquidation_account_id) 
                            REFERENCES liquidation_accounts(id);
                        END IF;
                    END $$;
                """))
                conn.commit()
            except Exception as e:
                if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                    raise
            
            # 3. Criar índice para performance
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_lancamentos_diarios_liquidation_account 
                    ON lancamentos_diarios(liquidation_account_id)
                """))
                conn.commit()
            except Exception as e:
                if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                    raise
            
            # Verificar se a coluna foi criada
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'lancamentos_diarios'
                AND column_name = 'liquidation_account_id'
            """))
            
            if result.fetchone():
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": "Migration executada com sucesso",
                        "timestamp": datetime.now().isoformat()
                    }
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error": "Coluna não encontrada após migration",
                        "timestamp": datetime.now().isoformat()
                    }
                )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Erro ao executar migration: {str(e)}",
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat()
            }
        )

@router.post("/seed-staging")
async def execute_seed_staging(
    reset_data: Optional[bool] = Body(False, description="Resetar dados antes do seed"),
    cost_debug: Optional[bool] = Body(False, description="Ativar debug de classificação de CUSTO"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Executa o seed do STAGING
    ATENÇÃO: Endpoint temporário - remover após uso
    """
    # Verificar se é super_admin
    user_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    if user_role != "super_admin":
        raise HTTPException(status_code=403, detail="Apenas super_admin pode executar seed")
    
    # Verificar se está em STAGING
    if os.getenv("ENVIRONMENT") != "staging":
        raise HTTPException(status_code=400, detail="Seed só pode ser executado em STAGING")
    
    backend_dir = Path(__file__).parent.parent.parent
    script_path = backend_dir / "scripts" / "seed_from_client_sheet.py"
    excel_file = backend_dir / "data" / "fluxo_caixa_2025.xlsx"
    
    # Diagnóstico
    script_exists = script_path.exists()
    excel_exists = excel_file.exists()
    backend_dir_exists = backend_dir.exists()
    
    # Listar arquivos para diagnóstico
    data_dir = backend_dir / "data"
    data_dir_exists = data_dir.exists()
    data_files = []
    if data_dir_exists:
        try:
            data_files = [f.name for f in data_dir.iterdir() if f.is_file()]
        except:
            pass
    
    if not script_exists:
        raise HTTPException(
            status_code=404, 
            detail=f"Script de seed não encontrado: {script_path}\nBackend dir existe: {backend_dir_exists}\nBackend dir: {backend_dir}"
        )
    
    if not excel_exists:
        raise HTTPException(
            status_code=404, 
            detail=f"Arquivo Excel não encontrado: {excel_file}\nData dir existe: {data_dir_exists}\nArquivos em data/: {data_files}"
        )
    
    try:
        # Verificar caminhos
        script_exists = script_path.exists()
        excel_exists = excel_file.exists()
        
        # Importar e executar seed diretamente
        import importlib.util
        import io
        import contextlib
        
        # Adicionar backend ao path se necessário
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        
        # Capturar stdout/stderr
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        
        # Usar subprocess de forma mais simples e robusta
        cmd = [
            sys.executable,
            "-m", "scripts.seed_from_client_sheet",
            "--file", str(excel_file.relative_to(backend_dir))
        ]
        
        if reset_data:
            cmd.append("--reset-data")
        
        env = os.environ.copy()
        env["PYTHONPATH"] = str(backend_dir)
        # Permitir COST_DEBUG via parâmetro ou env var
        if cost_debug:
            env["COST_DEBUG"] = "1"
        elif os.getenv("COST_DEBUG"):
            env["COST_DEBUG"] = os.getenv("COST_DEBUG")
        
        try:
            process = subprocess.run(
                cmd,
                cwd=str(backend_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=600,  # 10 minutos
                check=False
            )
            
            output = process.stdout
            success = process.returncode == 0 and ("✅ SEED CONCLUÍDO COM SUCESSO!" in output or "SEED CONCLUÍDO" in output)
            
        except subprocess.TimeoutExpired:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Timeout ao executar seed (mais de 10 minutos)",
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": f"Erro ao executar subprocess: {str(e)}",
                    "traceback": traceback.format_exc(),
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        full_output = output
        
        return JSONResponse(
            status_code=200 if success else 500,
            content={
                "success": success,
                "output": full_output[-3000:],  # Últimas 3000 caracteres
                "timestamp": datetime.now().isoformat(),
                "script_path": str(script_path),
                "excel_path": str(excel_file),
                "script_exists": script_exists,
                "excel_exists": excel_exists
            }
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao executar seed: {str(e)}\n\nDetalhes:\n{error_details}"
        )

