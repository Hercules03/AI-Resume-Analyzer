"""
Configuration settings for AI Resume Analyzer
"""
import os

# ChromaDB Configuration (replacing MySQL)
CHROMA_CONFIG = {
    'persist_directory': './chroma_db',
    'collection_name_resumes': 'resume_data',
    'collection_name_feedback': 'user_feedback',
    'embedding_model': 'all-MiniLM-L6-v2',  # Lightweight embedding model
    'chunk_size': 1000,
    'chunk_overlap': 200
}

# Legacy MySQL Configuration (kept for reference/migration if needed)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root', 
    'password': '@dmin1234',
    'database': 'cv'
}

# Admin Credentials
ADMIN_CONFIG = {
    'username': 'admin',
    'password': '@dmin1234'
}

# LLM Configuration (optimized for local Ollama usage)
LLM_CONFIG = {
    'default_model': 'gemma3:12b',
    'default_url': 'http://localhost:11434',
    'temperature': 0.1,
    'num_predict': 4096,  # Reduced for better performance
    'top_k': 10,
    'top_p': 0.9,
    'timeout': 60  # Add timeout for requests
}

# File Upload Configuration
UPLOAD_CONFIG = {
    'allowed_extensions': ['pdf'],
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'upload_folder': './Uploaded_Resumes/'
}

# OCR Configuration
OCR_CONFIG = {
    'default_languages': ['en'],
    'min_confidence': 0.6,
    'dpi': 300
}

# Text Quality Thresholds
TEXT_QUALITY = {
    'min_chars': 50,
    'min_words': 10,
    'max_special_char_ratio': 0.3,
    'min_word_space_ratio': 0.5
}

# Streamlit Page Configuration
PAGE_CONFIG = {
    'page_title': "AI Resume Analyzer - HR Edition",
    'page_icon': './Logo/recommend.png',
    'layout': 'wide'
}

# Ensure necessary directories exist
os.makedirs(UPLOAD_CONFIG['upload_folder'], exist_ok=True)
os.makedirs(CHROMA_CONFIG['persist_directory'], exist_ok=True) 