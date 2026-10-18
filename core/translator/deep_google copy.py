from deep_translator import GoogleTranslator
import os

# تعيين المسارات
input_folder = os.environ.get("INPUT_FOLDER", "./extracted_texts")
output_folder = os.environ.get("OUTPUT_FOLDER", "./translated_texts")

# التحقق من وجود مجلد الإخراج
os.makedirs(output_folder, exist_ok=True)

# إعداد المترجم
translator = GoogleTranslator(source='en', target='ar')

# تنفيذ الترجمة لكل 
for i in range(1, 243):  # من 1 إلى 242
    input_file = os.path.join(input_folder, f"extracted_texts{i}.txt")
    output_file = os.path.join(output_folder, f"translated_texts{i}.txt")
    
    # قراءة النص من الملف الأصلي
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # ترجمة النص
        translated_text = translator.translate(text)
        
        # حفظ النص المترجم في ملف جديد
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(translated_text)
        
        print(f"تمت ترجمة {input_file} بنجاح")
    except Exception as e:
        print(f"حدث خطأ أثناء معالجة {input_file}: {e}")
