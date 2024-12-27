# api/model.py
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
import torch
import os

class TranslationModel:
    def __init__(self, model_path="api/models/m2m100"):
        """Initialize the translation model and tokenizer"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        if not os.path.exists(model_path):
            raise ValueError(
                "Model not found! Please run scripts/download_model.py first to download the model."
            )
        
        # Load tokenizer and model from local path
        self.tokenizer = M2M100Tokenizer.from_pretrained(model_path)
        self.model = M2M100ForConditionalGeneration.from_pretrained(model_path)
        self.model = self.model.to(self.device)
        
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text from source language to target language"""
        # Set source language
        self.tokenizer.src_lang = source_lang
        
        # Tokenize
        encoded = self.tokenizer(text, return_tensors="pt").to(self.device)
        
        # Generate translation
        generated_tokens = self.model.generate(
            **encoded,
            forced_bos_token_id=self.tokenizer.get_lang_id(target_lang),
            max_length=128,
            num_beams=4,
            early_stopping=True
        )
        
        # Decode translation
        translation = self.tokenizer.batch_decode(
            generated_tokens,
            skip_special_tokens=True
        )[0]
        
        return translation