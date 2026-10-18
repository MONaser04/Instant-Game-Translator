class Processing:
    SIMILARITY_THRESHOLD = 0.5
    TEXT_CLEAN_PATTERNS = [
        r'\b\w{1}\b',  # حروف فردية
        r'[0-9]',      # أرقام
        r'[^\w\s]'     # علامات ترقيم
    ]