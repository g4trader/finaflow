#!/usr/bin/env python3
"""
Script simples para testar se o servidor consegue iniciar
"""

import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    print("Iniciando servidor de teste...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
"""
Script simples para testar se o servidor consegue iniciar
"""

import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    print("Iniciando servidor de teste...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
"""
Script simples para testar se o servidor consegue iniciar
"""

import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    print("Iniciando servidor de teste...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
"""
Script simples para testar se o servidor consegue iniciar
"""

import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    print("Iniciando servidor de teste...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
"""
Script simples para testar se o servidor consegue iniciar
"""

import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    print("Iniciando servidor de teste...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
