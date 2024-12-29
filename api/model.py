# api/model.py
import torch
import time
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from typing import List, Dict, Tuple

class TranslationModel:
    def __init__(self, model_path="api/models/m2m100"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load tokenizer and model
        self.tokenizer = M2M100Tokenizer.from_pretrained(model_path)
        self.model = M2M100ForConditionalGeneration.from_pretrained(model_path)
        self.model = self.model.to(self.device)
        
        # Initialize cache and metrics
        self.cache = {}
        self.last_translation_metrics = {}
        
        # Performance optimizations
        self.model.eval()  # Set to evaluation mode
        
        # Optimize generation parameters
        self.generation_config = {
            'max_new_tokens': 128,
            'num_beams': 2,        # Reduced from default 5
            'early_stopping': True,
            'use_cache': True,     # Enable model caching
            'length_penalty': 1.0   # Neutral length penalty
        }

    def split_text(self, text: str, max_length: int) -> list:
        """Split text into chunks suitable for translation."""
        words = text.split()
        chunks = []
        current_chunk = []

        for word in words:
            # Add word to the current chunk
            if len(' '.join(current_chunk + [word])) <= max_length:
                current_chunk.append(word)
            else:
                # Save the current chunk and start a new one
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]

        # Add the last chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def translate(self, text: str, source_lang: str, target_lang: str) -> Tuple[str, Dict]:
        start_time = time.time()
        input_tokens = 0
        output_tokens = 0

        # Check cache
        cache_key = f"{text}|{source_lang}|{target_lang}"
        if cache_key in self.cache:
            return self.cache[cache_key], {"tokens_per_second": 0, "total_tokens": 0, "processing_time": 0, "cached": True}

        # Split text by lines to preserve line breaks
        lines = text.splitlines()
        translated_lines = []

        for line in lines:
            # Handle empty lines
            if not line.strip():
                translated_lines.append("")
                continue

            # Split line into chunks if it's too long
            chunks = self.split_text(line, self.generation_config['max_new_tokens'])
            translations = []

            for chunk in chunks:
                with torch.no_grad():
                    self.tokenizer.src_lang = source_lang

                    # Tokenize with optimized settings
                    encoded = self.tokenizer(
                        chunk,
                        return_tensors="pt",
                        padding=True,
                        truncation=True,
                        max_length=self.generation_config['max_new_tokens']
                    ).to(self.device)

                    # Count input tokens
                    input_tokens += len(encoded['input_ids'][0])

                    # Generate translation
                    generated_tokens = self.model.generate(
                        **encoded,
                        forced_bos_token_id=self.tokenizer.get_lang_id(target_lang),
                        max_new_tokens=self.generation_config['max_new_tokens']
                    )

                    # Count output tokens
                    output_tokens += len(generated_tokens[0])

                    # Decode translation
                    translation = self.tokenizer.decode(generated_tokens[0], skip_special_tokens=True)
                    translations.append(translation)

            # Combine translated chunks
            translated_lines.append(' '.join(translations))

        # Combine lines and preserve line breaks
        final_translation = '\n'.join(translated_lines)
        
        # Calculate metrics
        end_time = time.time()
        total_time = end_time - start_time
        total_tokens = input_tokens + output_tokens
        tokens_per_second = total_tokens / total_time if total_time > 0 else 0

        metrics = {
            "tokens_per_second": round(tokens_per_second, 2),
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "processing_time": round(total_time, 2),
            "cached": False
        }

        # Cache the translation
        self.cache[cache_key] = final_translation
        self.last_translation_metrics = metrics

        return final_translation, metrics
    
    def translate_batch(self, texts: List[str], source_lang: str, target_lang: str) -> Tuple[List[str], Dict]:
        """Translate a batch of texts efficiently"""
        if not texts:
            return [], {"tokens_per_second": 0, "total_tokens": 0, "processing_time": 0, "cached": False}

        start_time = time.time()
        input_tokens = 0
        output_tokens = 0

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
            return translations, {"tokens_per_second": 0, "total_tokens": 0, "processing_time": 0, "cached": True}

        # Translate uncached texts
        with torch.no_grad():
            self.tokenizer.src_lang = source_lang
            
            encoded = self.tokenizer(
                texts_to_translate,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.generation_config['max_new_tokens']
            ).to(self.device)

            # Count input tokens
            input_tokens = encoded['input_ids'].numel()

            generated_tokens = self.model.generate(
                **encoded,
                forced_bos_token_id=self.tokenizer.get_lang_id(target_lang),
                **self.generation_config
            )

            # Count output tokens
            output_tokens = generated_tokens.numel()

            new_translations = self.tokenizer.batch_decode(
                generated_tokens,
                skip_special_tokens=True
            )

            # Cache and insert new translations
            for i, (text, translation) in enumerate(zip(texts_to_translate, new_translations)):
                cache_key = f"{text}|{source_lang}|{target_lang}"
                self.cache[cache_key] = translation
                translations.insert(indices_to_translate[i], translation)

        # Calculate metrics
        end_time = time.time()
        total_time = end_time - start_time
        total_tokens = input_tokens + output_tokens
        tokens_per_second = total_tokens / total_time if total_time > 0 else 0

        metrics = {
            "tokens_per_second": round(tokens_per_second, 2),
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "processing_time": round(total_time, 2),
            "cached": False
        }

        self.last_translation_metrics = metrics
        return translations, metrics