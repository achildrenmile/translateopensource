# api/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
import logging
from .model import TranslationModel
from .document_translator import DocumentTranslator
from .routers import translation, document, websocket, system

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    # Initialize FastAPI app
    app = FastAPI(title="Translation API")
    
    # Mount static files and templates
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
    templates = Jinja2Templates(directory="frontend/templates")
    
    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})
    
    return app

def initialize_model():
    logger.info("Loading translation model...")
    try:
        model = TranslationModel()
        doc_translator = DocumentTranslator(model)
            
        # Warmup request
        logger.info("Performing warmup request...")
        dummy_text = "Hello, world!"
        model.translate(dummy_text, "en", "es")
            
        logger.info("Model loaded successfully!")
        return model, doc_translator
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}", exc_info=True)
        raise

def setup_routers(app: FastAPI, model: TranslationModel, doc_translator: DocumentTranslator):
    # Share model and doc_translator with routers
    translation.router.model = model
    document.router.model = model
    document.router.doc_translator = doc_translator
    system.router.model = model
    websocket.router.translation_progress = document.translation_progress

    # Include routers with prefixes and tags
    app.include_router(translation.router, prefix="/api", tags=["translation"])
    app.include_router(document.router, prefix="/api", tags=["document"])
    app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
    app.include_router(system.router, prefix="/api", tags=["system"])

def get_application() -> FastAPI:
    # Create FastAPI application
    app = create_application()
    
    # Initialize model and document translator
    model, doc_translator = initialize_model()
    
    # Setup routers
    setup_routers(app, model, doc_translator)
    
    return app

# Create application instance
app = get_application()