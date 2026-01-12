#!/usr/bin/env python3
"""
Wrapper para executar `clean_and_onboard_llm.py` com logs verbosos das requisições HTTP.
Cria logs detalhados de URL, método, status_code e corpo de resposta.
"""
import importlib.util
import sys
from pathlib import Path
import json

SCRIPT_PATH = Path(__file__).resolve().parent / "clean_and_onboard_llm.py"

spec = importlib.util.spec_from_file_location("clean_and_onboard_llm", str(SCRIPT_PATH))
mod = importlib.util.module_from_spec(spec)
# carregar sem executar main diretamente
spec.loader.exec_module(mod)

# Guardar referências originais
_orig_get = mod.requests.get
_orig_post = mod.requests.post


def _log_response(resp):
    try:
        text = resp.text
        # tentar limitar tamanho para evitar poluição
        if len(text) > 2000:
            text = text[:2000] + "... (truncated)"
    except Exception:
        text = "<no-text>"
    try:
        body = resp.json()
        body_str = json.dumps(body, indent=2, ensure_ascii=False)
        if len(body_str) > 2000:
            body_str = body_str[:2000] + "... (truncated)"
    except Exception:
        body_str = text

    print(f"   [HTTP LOG] status={resp.status_code}")
    print(f"   [HTTP LOG] body: {body_str}")


def get_wrapper(url, *args, **kwargs):
    print(f"[HTTP GET] {url}")
    resp = _orig_get(url, *args, **kwargs)
    _log_response(resp)
    return resp


def post_wrapper(url, *args, **kwargs):
    print(f"[HTTP POST] {url}")
    # mostrar payload resumido se existir
    json_payload = kwargs.get('json') or kwargs.get('data')
    if json_payload is not None:
        try:
            s = json.dumps(json_payload, ensure_ascii=False)
            if len(s) > 400:
                s = s[:400] + '...'
            print(f"   [HTTP LOG] payload: {s}")
        except Exception:
            print("   [HTTP LOG] payload: <unserializable>")
    resp = _orig_post(url, *args, **kwargs)
    _log_response(resp)
    return resp

# Substituir
mod.requests.get = get_wrapper
mod.requests.post = post_wrapper

if __name__ == '__main__':
    sys.exit(mod.main())
