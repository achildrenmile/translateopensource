# api/document_translator.py
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation
import tempfile
import os
from typing import List, Tuple, BinaryIO

class DocumentTranslator:
    def __init__(self, translation_model):
        self.model = translation_model

    def translate_docx(self, file: BinaryIO, source_lang: str, target_lang: str) -> bytes:
        """Translate Word document while preserving formatting"""
        # Save uploaded file to temp file
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
            tmp_file.write(file.read())
            tmp_path = tmp_file.name

        try:
            # Load the document
            doc = Document(tmp_path)
            
            # Translate each paragraph
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    # Preserve formatting by getting runs (formatted pieces)
                    runs = paragraph.runs
                    if runs:
                        # Translate the text while keeping formatting
                        translated_text = self.model.translate(
                            paragraph.text,
                            source_lang,
                            target_lang
                        )
                        
                        # Update only the first run with translated text
                        runs[0].text = translated_text
                        # Clear other runs to avoid duplication
                        for run in runs[1:]:
                            run.text = ""

            # Translate tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            if paragraph.text.strip():
                                translated_text = self.model.translate(
                                    paragraph.text,
                                    source_lang,
                                    target_lang
                                )
                                paragraph.text = translated_text

            # Save translated document
            output_path = tmp_path.replace('.docx', '_translated.docx')
            doc.save(output_path)

            # Read the file content
            with open(output_path, 'rb') as f:
                translated_content = f.read()

            return translated_content
        
        finally:
            # Cleanup temp files
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(output_path):
                os.remove(output_path)

    def translate_xlsx(self, file: BinaryIO, source_lang: str, target_lang: str) -> bytes:
        """Translate Excel file while preserving formatting"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            tmp_file.write(file.read())
            tmp_path = tmp_file.name

        try:
            # Load workbook
            wb = load_workbook(tmp_path)
            
            # Process each worksheet
            for sheet in wb.worksheets:
                for row in sheet.iter_rows():
                    for cell in row:
                        if cell.value and isinstance(cell.value, str):
                            # Translate cell content
                            translated_text = self.model.translate(
                                cell.value,
                                source_lang,
                                target_lang
                            )
                            cell.value = translated_text

            # Save translated workbook
            output_path = tmp_path.replace('.xlsx', '_translated.xlsx')
            wb.save(output_path)

            # Read the file content
            with open(output_path, 'rb') as f:
                translated_content = f.read()

            return translated_content

        finally:
            # Cleanup temp files
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(output_path):
                os.remove(output_path)

    def translate_pptx(self, file: BinaryIO, source_lang: str, target_lang: str) -> bytes:
        """Translate PowerPoint file while preserving formatting"""
        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as tmp_file:
            tmp_file.write(file.read())
            tmp_path = tmp_file.name

        try:
            # Load presentation
            prs = Presentation(tmp_path)
            
            # Process each slide
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        # Translate shape text
                        translated_text = self.model.translate(
                            shape.text,
                            source_lang,
                            target_lang
                        )
                        shape.text = translated_text

            # Save translated presentation
            output_path = tmp_path.replace('.pptx', '_translated.pptx')
            prs.save(output_path)

            # Read the file content
            with open(output_path, 'rb') as f:
                translated_content = f.read()

            return translated_content

        finally:
            # Cleanup temp files
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(output_path):
                os.remove(output_path)