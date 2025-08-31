#!/usr/bin/env python3
"""
Script simples para testar se o servidor consegue iniciar
"""

import uvicorn
from fastapi import FastAPI

app = FastAPI(title="FinaFlow Backend", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "FinaFlow Backend is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 Iniciando servidor de teste...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
"""
Script simples para testar se o servidor consegue iniciar
"""

import uvicorn
from fastapi import FastAPI

app = FastAPI(title="FinaFlow Backend", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "FinaFlow Backend is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 Iniciando servidor de teste...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
"""
Script simples para testar se o servidor consegue iniciar
"""

import uvicorn
from fastapi import FastAPI

app = FastAPI(title="FinaFlow Backend", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "FinaFlow Backend is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 Iniciando servidor de teste...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
"""
Script simples para testar se o servidor consegue iniciar
"""

import uvicorn
from fastapi import FastAPI

app = FastAPI(title="FinaFlow Backend", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "FinaFlow Backend is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 Iniciando servidor de teste...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
"""
Script simples para testar se o servidor consegue iniciar
"""

import uvicorn
from fastapi import FastAPI

app = FastAPI(title="FinaFlow Backend", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "FinaFlow Backend is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 Iniciando servidor de teste...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
