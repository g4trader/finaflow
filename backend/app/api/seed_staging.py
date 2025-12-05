"""
Endpoint temporário para executar seed no STAGING
ATENÇÃO: Remover após execução do seed
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import os
from typing import Dict, Any

from app.services.dependencies import get_current_active_user
from app.models.auth import User

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

@router.post("/seed-staging")
async def execute_seed_staging(
    current_user: User = Depends(get_current_active_user)
):
    """
    Executa o seed do STAGING
    ATENÇÃO: Endpoint temporário - remover após uso
    """
    # Verificar se é super_admin
    if current_user.role.value != "super_admin":
        raise HTTPException(status_code=403, detail="Apenas super_admin pode executar seed")
    
    # Verificar se está em STAGING
    if os.getenv("ENVIRONMENT") != "staging":
        raise HTTPException(status_code=400, detail="Seed só pode ser executado em STAGING")
    
    backend_dir = Path(__file__).parent.parent.parent
    script_path = backend_dir / "scripts" / "seed_from_client_sheet.py"
    excel_file = backend_dir / "data" / "fluxo_caixa_2025.xlsx"
    
    if not script_path.exists():
        raise HTTPException(status_code=404, detail="Script de seed não encontrado")
    
    if not excel_file.exists():
        raise HTTPException(status_code=404, detail="Arquivo Excel não encontrado")
    
    try:
        # Verificar caminhos
        script_exists = script_path.exists()
        excel_exists = excel_file.exists()
        
        # Executar seed diretamente importando o módulo (mais confiável que subprocess)
        import importlib.util
        import io
        import contextlib
        
        # Capturar stdout
        output_buffer = io.StringIO()
        
        with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
            # Importar e executar o módulo de seed
            spec = importlib.util.spec_from_file_location("seed_from_client_sheet", script_path)
            seed_module = importlib.util.module_from_spec(spec)
            
            # Configurar sys.argv para simular chamada via CLI
            original_argv = sys.argv
            sys.argv = [str(script_path), "--file", str(excel_file.relative_to(backend_dir))]
            
            try:
                spec.loader.exec_module(seed_module)
            finally:
                sys.argv = original_argv
        
        output = output_buffer.getvalue()
        
        # Verificar se houve erro (output contém "❌" ou "ERRO")
        success = "✅ SEED CONCLUÍDO COM SUCESSO!" in output or "SEED CONCLUÍDO" in output
        
        return JSONResponse(
            status_code=200 if success else 500,
            content={
                "success": success,
                "output": output[-2000:],  # Últimas 2000 caracteres
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

