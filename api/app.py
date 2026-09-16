"""
FastAPI server for IntellectFlow.

Run:
    uvicorn api.app:app --reload

Endpoints:
    POST /audit          — upload a Python file, get JSON report
    POST /audit/markdown — upload a Python file, get Markdown report
    GET  /health         — liveness check
"""

import os
import tempfile

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

from orchestrator.graph import run_audit
from reports.markdown import render_markdown

load_dotenv()

app = FastAPI(
    title="IntellectFlow",
    description="Multi-agent code audit API",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


async def _save_upload(file: UploadFile) -> str:
    if not file.filename or not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py files are supported.")

    contents = await file.read()
    if len(contents) > 512_000:
        raise HTTPException(status_code=400, detail="File too large (max 512 KB).")

    tmp = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
    tmp.write(contents)
    tmp.close()
    return tmp.name


def _cleanup(path: str):
    try:
        os.unlink(path)
    except OSError:
        pass


@app.post("/audit")
async def audit(file: UploadFile = File(...)):
    tmp_path = await _save_upload(file)
    try:
        report = run_audit(tmp_path)
        report["file"] = file.filename
        return report
    finally:
        _cleanup(tmp_path)


@app.post("/audit/markdown", response_class=PlainTextResponse)
async def audit_markdown(file: UploadFile = File(...)):
    tmp_path = await _save_upload(file)
    try:
        report = run_audit(tmp_path)
        report["file"] = file.filename
        return render_markdown(report)
    finally:
        _cleanup(tmp_path)
