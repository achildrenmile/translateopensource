# api/routers/document.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask  # Changed this line
import tempfile
import os
import uuid
import logging
from typing import Dict

logger = logging.getLogger(__name__)
router = APIRouter()

# Store translation progress
translation_progress: Dict[str, Dict] = {}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit

def update_progress(task_id: str, progress: int, message: str):
    translation_progress[task_id] = {
        "status": "processing",
        "progress": progress,
        "message": message
    }

def cleanup_file(path: str, task_id: str):
    try:
        if os.path.exists(path):
            os.remove(path)
        if task_id in translation_progress:
            del translation_progress[task_id]
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")

@router.post("/translate/document/")
async def translate_document(
    file: UploadFile = File(...),
    source_lang: str = Form(...),  # Required parameter using Query
    target_lang: str = Form(...)   # Required parameter using Query
):
    task_id = str(uuid.uuid4())
    translation_progress[task_id] = {"status": "starting", "progress": 0}

    try:
        file_size = 0
        content = bytearray()
        
        while True:
            chunk = await file.read(8192)
            if not chunk:
                break
            file_size += len(chunk)
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {MAX_FILE_SIZE/1024/1024}MB"
                )
            content.extend(chunk)

        filename = file.filename.lower()
        if not any(filename.endswith(ext) for ext in ['.docx', '.xlsx', '.pptx', '.pdf', '.html', '.htm', '.txt']):
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported file type. Only .docx, .xlsx, .pptx, .pdf, .html, and .txt files are supported."
                )       

        translation_progress[task_id] = {
            "status": "processing",
            "progress": 10,
            "message": "File validation completed"
        }

        if filename.endswith('.docx'):
            content_and_metrics = await router.doc_translator.translate_docx_with_progress(
                content, source_lang, target_lang,
                lambda p, m: update_progress(task_id, p, m)
            )
            translated_content, metrics = content_and_metrics  # Unpack the tuple
            output_filename = filename.replace('.docx', f'_translated_{target_lang}.docx')
        elif filename.endswith('.xlsx'):
            content_and_metrics = await router.doc_translator.translate_xlsx_with_progress(
                content, source_lang, target_lang,
                lambda p, m: update_progress(task_id, p, m)
            )
            translated_content, metrics = content_and_metrics
            output_filename = filename.replace('.xlsx', f'_translated_{target_lang}.xlsx')
        elif filename.endswith('.pdf'):
            content_and_metrics = await router.doc_translator.translate_pdf_with_progress(
                content, source_lang, target_lang,
                lambda p, m: update_progress(task_id, p, m)
            )
            translated_content, metrics = content_and_metrics
            output_filename = filename.replace('.pdf', f'_translated_{target_lang}.pdf')        
        elif filename.endswith(('.html', '.htm')):
            content_and_metrics = await router.doc_translator.translate_html_with_progress(
                content, source_lang, target_lang,
                lambda p, m: update_progress(task_id, p, m)
            )
            translated_content, metrics = content_and_metrics
            output_filename = filename.replace(
                '.html' if filename.endswith('.html') else '.htm',
                f'_translated_{target_lang}.html'
            )   
        elif filename.endswith('.txt'):
            content_and_metrics = await router.doc_translator.translate_txt_with_progress(
                content, source_lang, target_lang,
                lambda p, m: update_progress(task_id, p, m)
            )
            translated_content, metrics = content_and_metrics
            output_filename = filename.replace('.txt', f'_translated_{target_lang}.txt')
        else:  # pptx
            content_and_metrics = await router.doc_translator.translate_pptx_with_progress(
                content, source_lang, target_lang,
                lambda p, m: update_progress(task_id, p, m)
            )
            translated_content, metrics = content_and_metrics
            output_filename = filename.replace('.pptx', f'_translated_{target_lang}.pptx')

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(translated_content)  # Now just writing the content part
            tmp_path = tmp_file.name

        translation_progress[task_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Translation completed",
            "download_url": f"/api/download/{task_id}/{output_filename}",
            "tmp_path": tmp_path,
            "metrics": metrics  # Store the metrics part
        }

        return {
            "task_id": task_id,
            "message": "Translation completed",
            "download_url": f"/api/download/{task_id}/{output_filename}"
        }

    except Exception as e:
        translation_progress[task_id] = {
            "status": "error",
            "progress": 0,
            "message": str(e)
        }
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{task_id}/{filename}")
async def download_file(task_id: str, filename: str):
    if task_id not in translation_progress or translation_progress[task_id]["status"] != "completed":
        raise HTTPException(status_code=404, detail="File not found or translation not completed")
    
    tmp_path = translation_progress[task_id].get("tmp_path")
    if not tmp_path or not os.path.exists(tmp_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        tmp_path,
        filename=filename,
        background=BackgroundTask(lambda: cleanup_file(tmp_path, task_id))
    )