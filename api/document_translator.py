# api/document_translator.py
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation
import tempfile
import os

class DocumentTranslator:
    def __init__(self, translation_model):
        self.model = translation_model

    async def translate_docx_with_progress(self, content: bytes, source_lang: str, target_lang: str, progress_callback):
        # Save content to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            doc = Document(tmp_path)
            total_items = len(doc.paragraphs) + sum(len(table.rows) * len(table.columns) for table in doc.tables)
            processed = 0

            # Translate paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    paragraph.text = self.model.translate(paragraph.text, source_lang, target_lang)
                processed += 1
                progress_callback(int(processed * 100 / total_items), "Translating document content...")

            # Translate tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            cell.text = self.model.translate(cell.text, source_lang, target_lang)
                        processed += 1
                        progress_callback(int(processed * 100 / total_items), "Translating tables...")

            doc.save(tmp_path)
            with open(tmp_path, 'rb') as f:
                return f.read()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    async def translate_xlsx_with_progress(self, content: bytes, source_lang: str, target_lang: str, progress_callback):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            wb = load_workbook(tmp_path)
            total_sheets = len(wb.sheetnames)
            processed_sheets = 0

            for sheet in wb.worksheets:
                rows = list(sheet.rows)
                total_cells = sum(1 for row in rows for cell in row if cell.value and isinstance(cell.value, str))
                processed_cells = 0

                for row in rows:
                    for cell in row:
                        if cell.value and isinstance(cell.value, str):
                            cell.value = self.model.translate(cell.value, source_lang, target_lang)
                            processed_cells += 1
                            progress = int((processed_sheets * 100 / total_sheets) + 
                                        (processed_cells * 100 / total_cells / total_sheets))
                            progress_callback(min(progress, 99), f"Translating sheet {sheet.title}...")

                processed_sheets += 1

            wb.save(tmp_path)
            with open(tmp_path, 'rb') as f:
                return f.read()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    async def translate_pptx_with_progress(self, content: bytes, source_lang: str, target_lang: str, progress_callback):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pptx') as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            prs = Presentation(tmp_path)
            total_slides = len(prs.slides)
            processed_slides = 0

            for slide in prs.slides:
                shapes = [shape for shape in slide.shapes if hasattr(shape, "text")]
                total_shapes = len(shapes)
                processed_shapes = 0

                for shape in shapes:
                    if shape.text.strip():
                        shape.text = self.model.translate(shape.text, source_lang, target_lang)
                    processed_shapes += 1
                    progress = int((processed_slides * 100 / total_slides) + 
                                (processed_shapes * 100 / total_shapes / total_slides))
                    progress_callback(min(progress, 99), f"Translating slide {processed_slides + 1}...")

                processed_slides += 1

            prs.save(tmp_path)
            with open(tmp_path, 'rb') as f:
                return f.read()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)