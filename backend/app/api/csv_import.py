from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import asyncio
import tempfile
import shutil
import os

from app.services.csv_importer import load_csv_to_table

router = APIRouter(prefix="/import-csv", tags=["csv"])


@router.post("/", status_code=201)
async def import_csv(file: UploadFile = File(...), table: str = Form(...)):
    """Import a CSV file into a BigQuery table."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        await asyncio.to_thread(load_csv_to_table, tmp_path, table)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        file.file.close()
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
