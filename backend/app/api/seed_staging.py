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
        # Executar seed
        cmd = [
            sys.executable,
            str(script_path),
            "--file", str(excel_file.relative_to(backend_dir))
        ]
        
        env = os.environ.copy()
        
        process = subprocess.Popen(
            cmd,
            cwd=str(backend_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        output_lines = []
        for line in process.stdout:
            output_lines.append(line)
        
        process.wait()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": process.returncode == 0,
                "return_code": process.returncode,
                "output": "".join(output_lines[-50:]),  # Últimas 50 linhas
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao executar seed: {str(e)}")

