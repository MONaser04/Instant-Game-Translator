from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
import os
from typing import List, Dict, Optional

class TranslationCache:
    def __init__(self, json_folder_path: str, threshold: float = 0.7):
        """
        Initialize the TranslationCache with a folder containing multiple JSON files.
        
        :param json_folder_path: Path to the folder containing JSON files with English-Arabic translations.
        :param threshold: Similarity threshold for matching texts (default: 0.6).
        """
        self.original: List[str] = []  # List to store English texts
        self.translated: List[str] = []  # List to store Arabic texts
        self.cache: Dict[str, str] = {}  # Cache for translations
        self.threshold: float = threshold  # Similarity threshold for matching

        # Load pre-trained sentence transformer model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        # Initialize FAISS index
        self.dimension: int = 384  # Dimension of the embeddings
        self.index = faiss.IndexFlatL2(self.dimension)

        # Load data from all JSON files in the folder and prepare embeddings if path exists
        if json_folder_path and os.path.exists(json_folder_path):
            self._load_json_folder(json_folder_path)
            self._prepare_embeddings()
        else:
            print(f"Notice: Translation cache directory '{json_folder_path}' not found or empty. Running with empty semantic cache.")

    def _load_json_folder(self, json_folder_path: str):
        """
        Load data from all JSON files in the specified folder.
        
        :param json_folder_path: Path to the folder containing JSON files.
        """
        if not json_folder_path or not os.path.exists(json_folder_path):
            print(f"Notice: Folder {json_folder_path} does not exist.")
            return

        # Iterate over all JSON files in the folder
        for filename in os.listdir(json_folder_path):
            if filename.endswith(".json"):
                file_path = os.path.join(json_folder_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Process each item in the JSON file
                    for item in data:
                        if "Arabic" in item and "English" in item:
                            self.original.append(item["English"].replace("\n", " ").strip())  # Normalize text
                            self.translated.append(item["Arabic"])  # Use Arabic as translated text
                        else:
                            print(f"Warning: Missing 'Arabic' or 'English' key in JSON item: {item}")
                except Exception as e:
                    print(f"Error loading JSON file {filename}: {e}")

    def _prepare_embeddings(self):
        """
        Generate embeddings for the English texts and add them to the FAISS index.
        """
        if not self.original:
            print("Warning: No texts found in the JSON files.")
            return

        # Generate embeddings for English texts
        self.original_embeddings = self.model.encode(self.original)
        self.index.add(np.array(self.original_embeddings))

    def find_match(self, ocr_text: str) -> Optional[str]:
        """
        Find a matching translation for the given English text using embeddings and FAISS.
        
        :param ocr_text: The English text to find a translation for.
        :return: The translated Arabic text if a match is found, otherwise None.
        """
        if not ocr_text:
            return None

        # Normalize OCR text: Remove newlines, extra spaces
        normalized_text = " ".join(ocr_text.split()).strip()

        # Check cache first
        if normalized_text in self.cache:
            return self.cache[normalized_text]

        # Generate embedding for the input text
        query_embedding = self.model.encode([normalized_text])
        query_embedding = np.array(query_embedding)

        # Search for the most similar text in the English embeddings
        D, I = self.index.search(query_embedding, k=1)
        best_match_index = I[0][0]
        best_distance = D[0][0]

        # Convert distance to similarity (assuming L2 distance)
        best_similarity = 1 / (1 + best_distance)

        # Check if the similarity meets the threshold
        if best_similarity >= self.threshold:
            best_translation = self.translated[best_match_index]
            self.cache[normalized_text] = best_translation  # Cache the result
            return best_translation

        return None  # No matching translation found

    def add_translation(self, source_text: str, translated_text: str):
        """
        Add a new translation to the cache and update the FAISS index.
        
        :param source_text: The English text.
        :param translated_text: The Arabic translation.
        """
        if not source_text or not translated_text:
            print("Warning: Source or translated text is empty.")
            return

        # Normalize source text
        source_text = " ".join(source_text.split()).strip()
        
        # Add to original and translated lists
        self.original.append(source_text)
        self.translated.append(translated_text)

        # Generate embedding for the new text and add to FAISS index
        new_embedding = self.model.encode([source_text])
        self.index.add(np.array(new_embedding))

        # Update cache
        self.cache[source_text] = translated_text

    def clear_cache(self):
        """
        Clear the translation cache.
        """
        self.cache.clear()