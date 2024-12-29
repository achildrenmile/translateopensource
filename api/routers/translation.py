# api/routers/translation.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class TranslationRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str

class BatchTranslationRequest(BaseModel):
    texts: List[str]
    source_lang: str
    target_lang: str

@router.post("/translate/")
async def translate(req: TranslationRequest):
    try:
        logger.debug(f"Translation request: {req}")
        if not router.model:
            raise HTTPException(status_code=500, detail="Translation model not initialized")
            
        translation, metrics = router.model.translate(
            req.text,
            req.source_lang,
            req.target_lang
        )
        logger.debug(f"Translation metrics: {metrics}")
        
        return {
            "translation": translation,
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Translation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/translate/batch/")
async def translate_batch(req: BatchTranslationRequest):
    try:
        translations = router.model.translate_batch(
            req.texts,
            req.source_lang,
            req.target_lang
        )
        return {"translations": translations}
    except Exception as e:
        logger.error(f"Batch translation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))