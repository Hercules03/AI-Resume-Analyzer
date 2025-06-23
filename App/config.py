"""
Configuration settings for AI Resume Analyzer
"""
import os

# Database Configuration
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

# LLM Configuration
LLM_CONFIG = {
    'default_model': 'gemma3:12b',
    'default_url': 'http://localhost:11434',
    'temperature': 0.1,
    'num_predict': 4096,
    'top_k': 10,
    'top_p': 0.9
}

# File Upload Configuration
UPLOAD_CONFIG = {
    'allowed_extensions': ['pdf'],
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'upload_folder': './Uploaded_Resumes/'
}

# LLM Configuration
LLM_CONFIG = {
    'default_model': 'gemma3:12b',
    'default_url': 'http://localhost:11434',
    'temperature': 0.1,
    'num_predict': 8192,
    'top_k': 10,
    'top_p': 0.9
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

# Ensure upload directory exists
os.makedirs(UPLOAD_CONFIG['upload_folder'], exist_ok=True) 