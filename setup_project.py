import os
import shutil

def create_directory_structure():
    """Create the project directory structure"""
    directories = [
        "api",
        "api/models",
        "frontend/static",
        "frontend/templates",
        "scripts",
        "tests"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

def create_file(path, content):
    """Create a file with the given content"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created file: {path}")

def create_gitignore():
    content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Model files
api/models/*
!api/models/.gitkeep

# Logs
*.log
    """
    create_file(".gitignore", content.strip())

def create_requirements():
    content = """
fastapi==0.68.1
uvicorn==0.15.0
torch==2.0.1
transformers==4.31.0
sentencepiece==0.1.99
python-multipart==0.0.6
jinja2==3.0.1
    """
    create_file("requirements.txt", content.strip())

def create_dockerfile():
    content = """
FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy pre-downloaded model files
COPY api/models /app/api/models

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
    """
    create_file("Dockerfile", content.strip())

def create_init_files():
    """Create empty __init__.py files"""
    init_paths = ["api/__init__.py", "tests/__init__.py"]
    for path in init_paths:
        create_file(path, "")

def create_readme():
    content = """
# Translation Web App

A web application for translations using the M2M-100 model.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
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
    """
    create_file("README.md", content.strip())

def create_gitkeep_files():
    """Create .gitkeep files for empty directories"""
    paths = ["api/models/.gitkeep"]
    for path in paths:
        create_file(path, "")

def setup_project():
    """Set up the entire project structure"""
    print("Setting up translation web app project...")
    
    # Create directory structure
    create_directory_structure()
    
    # Create configuration files
    create_gitignore()
    create_requirements()
    create_dockerfile()
    create_init_files()
    create_readme()
    create_gitkeep_files()
    
    print("\nProject structure created successfully!")
    print("\nNext steps:")
    print("1. Run: pip install -r requirements.txt")
    print("2. Run: python scripts/download_model.py")
    print("3. Run: uvicorn api.main:app --reload")

if __name__ == "__main__":
    setup_project()