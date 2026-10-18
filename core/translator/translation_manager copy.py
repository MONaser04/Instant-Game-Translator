import sys
import os
import requests
import json
import time
from functools import lru_cache

grandparent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(grandparent_dir)

class TranslationManager:
    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.last_translation = ""
        self.last_translation_time = time.time()

    def translate(self, text, callback=None):
        """ترجمة النص مع تصفية النتائج"""
        try:
            if not text.strip():
                return ""
            
            messages = [ 
                { 
                    "role": "system", 
                    "content": ( 
                        "You are a precise and context-aware translator that translates English to Arabic with the following guidelines:\n"
                        "- Ensure highly accurate translation with no spelling mistakes.\n"
                        "- Maintain strong and coherent phrasing suitable for game dialogues.\n"
                        "- Understand the general context, keeping character names untranslated but phonetically accurate (e.g., Witcher → ويتشر).\n"
                        "- Preserve the original line structure, even when texts are split across multiple lines.\n"
                        "- Treat consecutive lines as a continuation of the same sentence unless the context clearly indicates otherwise.\n"
                        "- Do not translate isolated words on separate lines unless they are standalone sentences or questions.\n"
                        "- Compare the input text with the last received text.\n"
                        "- Provide only the Arabic translation with no additional comments or explanations.\n"
                        "- Do not translate word-for-word but maintain accuracy while making it sound natural in Arabic.\n"
                        "- Avoid diacritics (tashkeel) unless absolutely necessary.\n"
                        "- Do not omit or add any words or details unless necessary for clarity.\n"
                        "- Keep the tone faithful to the original (formal/informal as needed)."
                    ) 
                }, 
                { 
                    "role": "user", 
                    "content": f"Translate the following text to Arabic while preserving the original line structure and ensuring maximum accuracy:\n{text}" 
                } 
            ]

            translated = ""
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional. Site URL for rankings on openrouter.ai.
                    "X-Title": "<YOUR_SITE_NAME>",  # Optional. Site title for rankings on openrouter.ai.
                },
                data=json.dumps({
                    "model": "deepseek/deepseek-chat:free",
                    "messages": messages,
                    "temperature": 0.5,
                    "top_p": 0.7,
                    "top_k": 40,
                    "repetition_penalty": 1.05,
                    "stream": True
                }),
                stream=True
            )
            
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    chunk_str = chunk.decode('utf-8')
                    if chunk_str.startswith("data:"):
                        chunk_data = json.loads(chunk_str[5:])
                        if chunk_data.get("choices") and len(chunk_data["choices"]) > 0:
                            delta = chunk_data["choices"][0].get("delta", {})
                            if delta.get("content"):
                                translated += delta["content"]
                                if callback:
                                    callback(translated)  # تمرير النص المترجم حتى الآن
            
            # تصفية النص قبل إرجاعه
            filtered_translation = self._filter_translation(translated)
            self._update_translation_state(filtered_translation.strip())
            return filtered_translation.strip()
        except Exception as e:
            print(f"Translation Error: {str(e)}")
            return ""

    def _filter_translation(self, text):
        """تصفية النص المترجم"""
        if not text:
            return ""
        
        # إزالة أي نصوص غير مرغوب فيها
        unwanted_phrases = [
            "print(",
            "debug:",
            "error:",
            "warning:",
            "note:",
            "INFO:",
            "DEBUG:",
            "ERROR:",
            "WARNING:",
            "NOTE:",
        ]
        
        for phrase in unwanted_phrases:
            text = text.replace(phrase, "")
        
        # إزالة الأسطر الفارغة
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        filtered_text = "\n".join(lines)
        
        return filtered_text

    def _update_translation_state(self, text):
        self.last_translation = text
        self.last_translation_time = time.time()