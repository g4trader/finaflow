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
import traceback

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
        
        # Executar seed em thread separada para evitar bloqueio
        import threading
        import queue
        
        result_queue = queue.Queue()
        
        def run_seed():
            try:
                with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(error_buffer):
                    # Importar módulo
                    spec = importlib.util.spec_from_file_location("seed_from_client_sheet", script_path)
                    if spec is None or spec.loader is None:
                        raise ImportError(f"Não foi possível carregar o módulo: {script_path}")
                    
                    seed_module = importlib.util.module_from_spec(spec)
                    
                    # Configurar sys.argv
                    original_argv = sys.argv.copy()
                    sys.argv = [str(script_path), "--file", str(excel_file.relative_to(backend_dir))]
                    
                    try:
                        spec.loader.exec_module(seed_module)
                        # Chamar main se existir
                        if hasattr(seed_module, 'main'):
                            seed_module.main()
                    finally:
                        sys.argv = original_argv
                
                result_queue.put(("success", output_buffer.getvalue(), error_buffer.getvalue()))
            except Exception as e:
                result_queue.put(("error", str(e), traceback.format_exc()))
        
        # Executar em thread
        thread = threading.Thread(target=run_seed, daemon=True)
        thread.start()
        thread.join(timeout=300)  # Timeout de 5 minutos
        
        if thread.is_alive():
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Timeout ao executar seed (mais de 5 minutos)",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        if result_queue.empty():
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Seed não retornou resultado",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        status, output, error_output = result_queue.get()
        
        if status == "error":
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": output,
                    "traceback": error_output,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        full_output = output + "\n" + error_output
        success = "✅ SEED CONCLUÍDO COM SUCESSO!" in full_output or "SEED CONCLUÍDO" in full_output
        
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

