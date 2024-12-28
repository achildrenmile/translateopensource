# api/main.py
from starlette.background import BackgroundTask
import tempfile
import os
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.requests import Request
from pydantic import BaseModel
from .model import TranslationModel
from .document_translator import DocumentTranslator
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List
import uuid
import json
import logging

model = None
doc_translator = None

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define models
class TranslationRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str

class BatchTranslationRequest(BaseModel):
    texts: List[str]
    source_lang: str
    target_lang: str

# Store translation progress
translation_progress: Dict[str, Dict] = {}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit


logger.info("Loading translation model...")
try:

    model = TranslationModel()
    doc_translator = DocumentTranslator(model)
        
    # Warmup request
    logger.info("Performing warmup request...")
    dummy_text = "Hello, world!"
    model.translate(dummy_text, "en", "es")
        
    logger.info("Model loaded successfully!")
except Exception as e:
        logger.error(f"Error loading model: {str(e)}", exc_info=True)
        raise

# Initialize FastAPI app
app = FastAPI(title="Translation API")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/translation-progress/{task_id}")
async def translation_progress_websocket(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        while True:
            if task_id in translation_progress:
                await websocket.send_json(translation_progress[task_id])
                if translation_progress[task_id]["status"] in ["completed", "error"]:
                    break
            await asyncio.sleep(0.5)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()

@app.post("/translate/")
async def translate(req: TranslationRequest):
    try:
        logger.debug(f"Translation request: {req}")
        if model is None:
            raise HTTPException(status_code=500, detail="Translation model not initialized")
            
        translation = model.translate(
            req.text,
            req.source_lang,
            req.target_lang
        )
        return {"translation": translation}
    except Exception as e:
        logger.error(f"Translation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translate/batch/")
async def translate_batch(req: BatchTranslationRequest):
    try:
        translations = model.translate_batch(
            req.texts,
            req.source_lang,
            req.target_lang
        )
        return {"translations": translations}
    except Exception as e:
        logger.error(f"Batch translation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translate/document/")
async def translate_document(
    file: UploadFile = File(...),
    source_lang: str = "en",
    target_lang: str = "es"
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
        if not any(filename.endswith(ext) for ext in ['.docx', '.xlsx', '.pptx']):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Only .docx, .xlsx, and .pptx files are supported."
            )

        translation_progress[task_id] = {
            "status": "processing",
            "progress": 10,
            "message": "File validation completed"
        }

        if filename.endswith('.docx'):
            translated_content = await doc_translator.translate_docx_with_progress(
                content, source_lang, target_lang,
                lambda p, m: update_progress(task_id, p, m)
            )
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            output_filename = filename.replace('.docx', f'_translated_{target_lang}.docx')
        elif filename.endswith('.xlsx'):
            translated_content = await doc_translator.translate_xlsx_with_progress(
                content, source_lang, target_lang,
                lambda p, m: update_progress(task_id, p, m)
            )
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            output_filename = filename.replace('.xlsx', f'_translated_{target_lang}.xlsx')
        elif filename.endswith('.pptx'):
            translated_content = await doc_translator.translate_pptx_with_progress(
                content, source_lang, target_lang,
                lambda p, m: update_progress(task_id, p, m)
            )
            content_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            output_filename = filename.replace('.pptx', f'_translated_{target_lang}.pptx')

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(translated_content)
            tmp_path = tmp_file.name

        translation_progress[task_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Translation completed",
            "download_url": f"/download/{task_id}/{output_filename}",
            "tmp_path": tmp_path 
        }

        return {
            "task_id": task_id,
            "message": "Translation completed",
            "download_url": f"/download/{task_id}/{output_filename}"
        }

    except Exception as e:
        translation_progress[task_id] = {
            "status": "error",
            "progress": 0,
            "message": str(e)
        }
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{task_id}/{filename}")
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

@app.get("/status/")
async def check_status():
    try:
        is_ready = model is not None
        return {
            "status": "ready" if is_ready else "not_ready",
            "device": model.device if is_ready else None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/languages/")
async def get_languages():
    # Complete list of supported languages
    return {
        "languages": [
            {"code": "af", "name": "Afrikaans"},
            {"code": "am", "name": "Amharic"},
            {"code": "ar", "name": "Arabic"},
            {"code": "ast", "name": "Asturian"},
            {"code": "az", "name": "Azerbaijani"},
            {"code": "ba", "name": "Bashkir"},
            {"code": "be", "name": "Belarusian"},
            {"code": "bg", "name": "Bulgarian"},
            {"code": "bn", "name": "Bengali"},
            {"code": "br", "name": "Breton"},
            {"code": "bs", "name": "Bosnian"},
            {"code": "ca", "name": "Catalan"},
            {"code": "ceb", "name": "Cebuano"},
            {"code": "cs", "name": "Czech"},
            {"code": "cy", "name": "Welsh"},
            {"code": "da", "name": "Danish"},
            {"code": "de", "name": "German"},
            {"code": "el", "name": "Greek"},
            {"code": "en", "name": "English"},
            {"code": "es", "name": "Spanish"},
            {"code": "et", "name": "Estonian"},
            {"code": "fa", "name": "Persian"},
            {"code": "ff", "name": "Fulah"},
            {"code": "fi", "name": "Finnish"},
            {"code": "fr", "name": "French"},
            {"code": "fy", "name": "Western Frisian"},
            {"code": "ga", "name": "Irish"},
            {"code": "gd", "name": "Scottish Gaelic"},
            {"code": "gl", "name": "Galician"},
            {"code": "gu", "name": "Gujarati"},
            {"code": "ha", "name": "Hausa"},
            {"code": "he", "name": "Hebrew"},
            {"code": "hi", "name": "Hindi"},
            {"code": "hr", "name": "Croatian"},
            {"code": "ht", "name": "Haitian Creole"},
            {"code": "hu", "name": "Hungarian"},
            {"code": "hy", "name": "Armenian"},
            {"code": "id", "name": "Indonesian"},
            {"code": "ig", "name": "Igbo"},
            {"code": "ilo", "name": "Iloko"},
            {"code": "is", "name": "Icelandic"},
            {"code": "it", "name": "Italian"},
            {"code": "ja", "name": "Japanese"},
            {"code": "jv", "name": "Javanese"},
            {"code": "ka", "name": "Georgian"},
            {"code": "kk", "name": "Kazakh"},
            {"code": "km", "name": "Central Khmer"},
            {"code": "kn", "name": "Kannada"},
            {"code": "ko", "name": "Korean"},
            {"code": "lb", "name": "Luxembourgish"},
            {"code": "lg", "name": "Ganda"},
            {"code": "ln", "name": "Lingala"},
            {"code": "lo", "name": "Lao"},
            {"code": "lt", "name": "Lithuanian"},
            {"code": "lv", "name": "Latvian"},
            {"code": "mg", "name": "Malagasy"},
            {"code": "mk", "name": "Macedonian"},
            {"code": "ml", "name": "Malayalam"},
            {"code": "mn", "name": "Mongolian"},
            {"code": "mr", "name": "Marathi"},
            {"code": "ms", "name": "Malay"},
            {"code": "my", "name": "Burmese"},
            {"code": "ne", "name": "Nepali"},
            {"code": "nl", "name": "Dutch"},
            {"code": "no", "name": "Norwegian"},
            {"code": "ns", "name": "Northern Sotho"},
            {"code": "oc", "name": "Occitan"},
            {"code": "or", "name": "Oriya"},
            {"code": "pa", "name": "Punjabi"},
            {"code": "pl", "name": "Polish"},
            {"code": "ps", "name": "Pashto"},
            {"code": "pt", "name": "Portuguese"},
            {"code": "ro", "name": "Romanian"},
            {"code": "ru", "name": "Russian"},
            {"code": "sd", "name": "Sindhi"},
            {"code": "si", "name": "Sinhala"},
            {"code": "sk", "name": "Slovak"},
            {"code": "sl", "name": "Slovenian"},
            {"code": "so", "name": "Somali"},
            {"code": "sq", "name": "Albanian"},
            {"code": "sr", "name": "Serbian"},
            {"code": "ss", "name": "Swati"},
            {"code": "su", "name": "Sundanese"},
            {"code": "sv", "name": "Swedish"},
            {"code": "sw", "name": "Swahili"},
            {"code": "ta", "name": "Tamil"},
            {"code": "th", "name": "Thai"},
            {"code": "tl", "name": "Tagalog"},
            {"code": "tn", "name": "Tswana"},
            {"code": "tr", "name": "Turkish"},
            {"code": "uk", "name": "Ukrainian"},
            {"code": "ur", "name": "Urdu"},
            {"code": "uz", "name": "Uzbek"},
            {"code": "vi", "name": "Vietnamese"},
            {"code": "wo", "name": "Wolof"},
            {"code": "xh", "name": "Xhosa"},
            {"code": "yi", "name": "Yiddish"},
            {"code": "yo", "name": "Yoruba"},
            {"code": "zh", "name": "Chinese"},
            {"code": "zu", "name": "Zulu"}
        ]
    }
