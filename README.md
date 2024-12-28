# Translation Web App

A web application for translations using the M2M-100 model. https://huggingface.co/facebook/m2m100_418M.
Clone from https://github.com/achildrenmile/translateopensource and adapted for IFX.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

3. Download the model:
```bash
python scripts/download_model.py
```

4. Run the application:
```bash
uvicorn api.main:app --reload
```

Visit http://localhost:8000 to use the application.

## Docker

Build and run with Docker:
```bash
docker build -t translation-app .
docker run -p 8000:8000 translation-app
```