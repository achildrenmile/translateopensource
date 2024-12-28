# api/model.py
import torch
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from typing import List

class TranslationModel:
    def __init__(self, model_path="api/models/m2m100"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load tokenizer and model
        self.tokenizer = M2M100Tokenizer.from_pretrained(model_path)
        self.model = M2M100ForConditionalGeneration.from_pretrained(model_path)
        self.model = self.model.to(self.device)
        
        # Performance optimizations
        self.model.eval()  # Set to evaluation mode
        self.cache = {}    # Simple cache for repeated translations
        
        # Optimize generation parameters
        self.generation_config = {
            'max_length': 128,
            'num_beams': 2,        # Reduced from default 5
            'early_stopping': True,
            'use_cache': True,     # Enable model caching
            'length_penalty': 1.0   # Neutral length penalty
        }

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text with optimizations"""
        # Check cache
        cache_key = f"{text}|{source_lang}|{target_lang}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Translate with optimizations
        with torch.no_grad():  # Disable gradient calculations
            self.tokenizer.src_lang = source_lang
            
            # Tokenize with optimized settings
            encoded = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.generation_config['max_length']
            ).to(self.device)
            
            # Generate translation
            generated_tokens = self.model.generate(
                **encoded,
                forced_bos_token_id=self.tokenizer.get_lang_id(target_lang),
                **self.generation_config
            )
            
            # Decode translation
            translation = self.tokenizer.batch_decode(
                generated_tokens,
                skip_special_tokens=True
            )[0]
            
            # Cache the result
            self.cache[cache_key] = translation
            return translation

    def translate_batch(self, texts: List[str], source_lang: str, target_lang: str) -> List[str]:
        """Translate a batch of texts efficiently"""
        if not texts:
            return []

        # Check cache for all texts
        translations = []
        texts_to_translate = []
        indices_to_translate = []

        for i, text in enumerate(texts):
            cache_key = f"{text}|{source_lang}|{target_lang}"
            if cache_key in self.cache:
                translations.append(self.cache[cache_key])
            else:
                texts_to_translate.append(text)
                indices_to_translate.append(i)

        # If all texts were cached, return early
        if not texts_to_translate:
            return translations

        # Translate uncached texts
        with torch.no_grad():
            self.tokenizer.src_lang = source_lang
            
            encoded = self.tokenizer(
                texts_to_translate,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.generation_config['max_length']
            ).to(self.device)

            generated_tokens = self.model.generate(
                **encoded,
                forced_bos_token_id=self.tokenizer.get_lang_id(target_lang),
                **self.generation_config
            )

            new_translations = self.tokenizer.batch_decode(
                generated_tokens,
                skip_special_tokens=True
            )

            # Cache and insert new translations
            for i, (text, translation) in enumerate(zip(texts_to_translate, new_translations)):
                cache_key = f"{text}|{source_lang}|{target_lang}"
                self.cache[cache_key] = translation
                translations.insert(indices_to_translate[i], translation)

        return translations