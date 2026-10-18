import sys
import os
grandparent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(grandparent_dir)
from together import Together
import time
from functools import lru_cache
from text.translation_cache import TranslationCache

class TranslationManager:
    def __init__(self):
        # Load API key from environment variable or settings
        together_api_key = os.environ.get("TOGETHER_API_KEY", "")
        self.client = Together(api_key=together_api_key) if together_api_key else None
        self.last_translation = ""
        self.last_translation_time = time.time()
        self.translation_option = "both"  # Default option

    def set_translation_option(self, option):
        """تعيين خيار الترجمة"""
        self.translation_option = option

    def translate(self, text, callback=None):
        """ترجمة النص مع تصفية النتائج"""
        try:
            if not text.strip():
                return ""
            
            # البحث في التخزين المؤقت للترجمة إذا كان الخيار هو JSON أو Both
            if self.translation_option in ["json_only", "both"]:
                translated = TranslationCache.find_match(text)
                if translated:
                    return translated

            # إذا كان الخيار هو AI أو Both ولم يتم العثور على ترجمة في JSON
            if self.translation_option in ["ai_only", "both"]:
                messages = [ 
                    {
                        "role": "system",
                        "content": "ترجم الإنجليزية إلى العربية بدقة، مع الحفاظ على بنية النص والأسماء كما هي. اجعل الترجمة طبيعية، وتجنب الحرفية والتشكيل، ولا تضف أو تحذف شيئًا إلا للوضوح."
                    },
                    {
                        "role": "user",
                        "content": f"ترجم النص التالي:\n{text}"
                    }
                ]

                translated = ""
                stream = self.client.chat.completions.create(
                    model="deepseek-ai/DeepSeek-V3",
                    messages=messages,
                    temperature=0.7,
                    top_p=0.7,
                    top_k=50,
                    repetition_penalty=1,
                    stop=["\n"],
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if delta and delta.content:
                            translated += delta.content
                            if callback:
                                callback(translated)  # تمرير النص المترجم حتى الآن
                
                # تصفية النص قبل إرجاعه
                filtered_translation = self._filter_translation(translated)
                self._update_translation_state(filtered_translation.strip())
                return filtered_translation.strip()
            
            return ""  # إذا لم يتم العثور على ترجمة

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