"""API routes for CSV import operations."""

import csv
import io
import asyncio
import tempfile
import shutil
import os
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse

from app.db.bq_client import insert_many
from app.services.dependencies import get_current_user, tenant
from app.models.finance import AccountCreate, TransactionCreate
from app.services.csv_importer import load_csv_to_table

router = APIRouter(prefix="/csv", tags=["csv-import"])


def parse_currency(value: str) -> Decimal:
    """Converte string de moeda para Decimal."""
    if not value or value.strip() == "":
        return Decimal("0")
    
    # Remove espaços e caracteres especiais
    cleaned = value.strip().replace(" ", "").replace("R$", "").replace(".", "").replace(",", ".")
    
    try:
        return Decimal(cleaned)
    except:
        return Decimal("0")


def parse_date(date_str: str) -> str:
    """Converte string de data para formato ISO."""
    if not date_str or date_str.strip() == "":
        return datetime.now().isoformat()
    
    try:
        # Tenta diferentes formatos de data
        for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"]:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.isoformat()
            except ValueError:
                continue
        return datetime.now().isoformat()
    except:
        return datetime.now().isoformat()


@router.post("/import-csv", status_code=201)
async def import_csv_generic(file: UploadFile = File(...), table: str = Form(...)):
    """Import a CSV file into a BigQuery table (generic import)."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser CSV")
    
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        
        error = await asyncio.to_thread(load_csv_to_table, tmp_path, table)
        if error:
            raise HTTPException(status_code=500, detail=error)
        
        return {"status": "success", "message": f"CSV importado com sucesso para a tabela {table}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        file.file.close()
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/import/accounts", status_code=201)
async def import_accounts_csv(
    file: UploadFile = File(...),
    current=Depends(get_current_user),
    tenant_id: str = Depends(tenant),
):
    """Importa contas a partir de um arquivo CSV."""
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser CSV")
    
    try:
        # Ler conteúdo do arquivo
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Processar CSV
        csv_reader = csv.DictReader(io.StringIO(content_str))
        
        accounts = []
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Começa em 2 pois linha 1 é cabeçalho
            try:
                # Mapear colunas do CSV para o modelo
                account_data = {
                    "subgroup_id": row.get("Subgrupo", ""),
                    "name": row.get("Conta", ""),
                    "balance": parse_currency(row.get("Saldo", "0")),
                    "tenant_id": tenant_id
                }
                
                # Validar dados obrigatórios
                if not account_data["name"]:
                    errors.append(f"Linha {row_num}: Nome da conta é obrigatório")
                    continue
                
                if not account_data["subgroup_id"]:
                    errors.append(f"Linha {row_num}: Subgrupo é obrigatório")
                    continue
                
                accounts.append(account_data)
                
            except Exception as e:
                errors.append(f"Linha {row_num}: Erro ao processar - {str(e)}")
        
        if errors:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Erros encontrados no CSV",
                    "errors": errors,
                    "processed": len(accounts)
                }
            )
        
        if not accounts:
            raise HTTPException(status_code=400, detail="Nenhuma conta válida encontrada no CSV")
        
        # Preparar registros para inserção
        records = []
        for account in accounts:
            record = {
                "id": str(uuid4()),
                "subgroup_id": account["subgroup_id"],
                "name": account["name"],
                "balance": str(account["balance"]),
                "tenant_id": account["tenant_id"],
                "created_at": datetime.utcnow().isoformat()
            }
            records.append(record)
        
        # Inserir no BigQuery
        await asyncio.to_thread(insert_many, "Accounts", records)
        
        return {
            "message": "Contas importadas com sucesso",
            "imported_count": len(records),
            "tenant_id": tenant_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar CSV: {str(e)}")


@router.post("/import/transactions", status_code=201)
async def import_transactions_csv(
    file: UploadFile = File(...),
    current=Depends(get_current_user),
    tenant_id: str = Depends(tenant),
):
    """Importa transações a partir de um arquivo CSV."""
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser CSV")
    
    try:
        # Ler conteúdo do arquivo
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Processar CSV
        csv_reader = csv.DictReader(io.StringIO(content_str))
        
        transactions = []
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Mapear colunas do CSV para o modelo
                transaction_data = {
                    "account_id": row.get("Conta", ""),
                    "amount": parse_currency(row.get("Valor", "0")),
                    "description": row.get("Descrição", ""),
                    "tenant_id": tenant_id,
                    "transaction_date": parse_date(row.get("Data Movimentação", ""))
                }
                
                # Validar dados obrigatórios
                if not transaction_data["account_id"]:
                    errors.append(f"Linha {row_num}: Conta é obrigatória")
                    continue
                
                if transaction_data["amount"] == 0:
                    errors.append(f"Linha {row_num}: Valor deve ser diferente de zero")
                    continue
                
                transactions.append(transaction_data)
                
            except Exception as e:
                errors.append(f"Linha {row_num}: Erro ao processar - {str(e)}")
        
        if errors:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Erros encontrados no CSV",
                    "errors": errors,
                    "processed": len(transactions)
                }
            )
        
        if not transactions:
            raise HTTPException(status_code=400, detail="Nenhuma transação válida encontrada no CSV")
        
        # Preparar registros para inserção
        records = []
        for transaction in transactions:
            record = {
                "id": str(uuid4()),
                "account_id": transaction["account_id"],
                "amount": str(transaction["amount"]),
                "description": transaction["description"],
                "tenant_id": transaction["tenant_id"],
                "transaction_date": transaction["transaction_date"],
                "created_at": datetime.utcnow().isoformat()
            }
            records.append(record)
        
        # Inserir no BigQuery
        await asyncio.to_thread(insert_many, "Transactions", records)
        
        return {
            "message": "Transações importadas com sucesso",
            "imported_count": len(records),
            "tenant_id": tenant_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar CSV: {str(e)}")


@router.post("/import/plan-accounts", status_code=201)
async def import_plan_accounts_csv(
    file: UploadFile = File(...),
    current=Depends(get_current_user),
    tenant_id: str = Depends(tenant),
):
    """Importa plano de contas a partir de um arquivo CSV."""
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser CSV")
    
    try:
        # Ler conteúdo do arquivo
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Processar CSV
        csv_reader = csv.DictReader(io.StringIO(content_str))
        
        groups = {}
        subgroups = {}
        accounts = []
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                group_name = row.get("Grupo", "").strip()
                subgroup_name = row.get("Subgrupo", "").strip()
                account_name = row.get("Conta", "").strip()
                use_account = row.get("Escolha", "").strip().lower() == "usar"
                
                if not group_name or not subgroup_name or not account_name:
                    errors.append(f"Linha {row_num}: Grupo, Subgrupo e Conta são obrigatórios")
                    continue
                
                # Criar grupo se não existir
                if group_name not in groups:
                    group_id = str(uuid4())
                    groups[group_name] = {
                        "id": group_id,
                        "name": group_name,
                        "description": f"Grupo: {group_name}",
                        "tenant_id": tenant_id,
                        "created_at": datetime.utcnow().isoformat()
                    }
                
                # Criar subgrupo se não existir
                if subgroup_name not in subgroups:
                    subgroup_id = str(uuid4())
                    subgroups[subgroup_name] = {
                        "id": subgroup_id,
                        "group_id": groups[group_name]["id"],
                        "name": subgroup_name,
                        "description": f"Subgrupo: {subgroup_name}",
                        "tenant_id": tenant_id,
                        "created_at": datetime.utcnow().isoformat()
                    }
                
                # Adicionar conta se marcada para usar
                if use_account:
                    account_data = {
                        "id": str(uuid4()),
                        "subgroup_id": subgroups[subgroup_name]["id"],
                        "name": account_name,
                        "balance": "0",
                        "tenant_id": tenant_id,
                        "created_at": datetime.utcnow().isoformat()
                    }
                    accounts.append(account_data)
                
            except Exception as e:
                errors.append(f"Linha {row_num}: Erro ao processar - {str(e)}")
        
        if errors:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Erros encontrados no CSV",
                    "errors": errors,
                    "processed": len(accounts)
                }
            )
        
        # Inserir grupos
        if groups:
            group_records = list(groups.values())
            await asyncio.to_thread(insert_many, "Groups", group_records)
        
        # Inserir subgrupos
        if subgroups:
            subgroup_records = list(subgroups.values())
            await asyncio.to_thread(insert_many, "Subgroups", subgroup_records)
        
        # Inserir contas
        if accounts:
            await asyncio.to_thread(insert_many, "Accounts", accounts)
        
        return {
            "message": "Plano de contas importado com sucesso",
            "groups_imported": len(groups),
            "subgroups_imported": len(subgroups),
            "accounts_imported": len(accounts),
            "tenant_id": tenant_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar CSV: {str(e)}")


@router.get("/template/accounts")
async def get_accounts_template():
    """Retorna template CSV para importação de contas."""
    template = """Conta,Subgrupo,Saldo,Descrição
Conta Exemplo,Subgrupo Exemplo,1000.00,Descrição da conta
"""
    return {"template": template, "filename": "template_accounts.csv"}


@router.get("/template/transactions")
async def get_transactions_template():
    """Retorna template CSV para importação de transações."""
    template = """Data Movimentação,Conta,Valor,Descrição
02/01/2025,Conta Exemplo,100.00,Descrição da transação
"""
    return {"template": template, "filename": "template_transactions.csv"}


@router.get("/template/plan-accounts")
async def get_plan_accounts_template():
    """Retorna template CSV para importação do plano de contas."""
    template = """Conta,Subgrupo,Grupo,Escolha
Conta Exemplo,Subgrupo Exemplo,Grupo Exemplo,Usar
"""
    return {"template": template, "filename": "template_plan_accounts.csv"}
