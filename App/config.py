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
    'num_predict': 8192,  # Reduced for better performance
    'top_k': 10,
    'top_p': 0.9,
    'timeout': 60  # Add timeout for requests
}

# Chatbot Specialists Configuration
SPECIALISTS_CONFIG = {
    'intent_analysis': {
        'model': 'gemma3:4b',
        'url': 'http://localhost:11434',
        'temperature': 0.0,  # Deterministic for consistent intent classification
        'num_predict': 8192,
        'timeout': 30
    },
    'name_extraction': {
        'model': 'gemma3:4b',
        'url': 'http://localhost:11434',
        'temperature': 0.0,  # Deterministic for accurate name extraction
        'num_predict': 8192,
        'timeout': 30
    },
    'query_enhancement': {
        'model': 'gemma3:4b',
        'url': 'http://localhost:11434',
        'temperature': 0.2,  # Slight creativity for query expansion
        'num_predict': 8192,
        'timeout': 45
    },
    'response_generation': {
        'model': 'gemma3:12b',  # Larger model for better responses
        'url': 'http://localhost:11434',
        'temperature': 0.3,  # More conversational
        'num_predict': 8192,
        'timeout': 60
    }
}

# Resume Extractors Configuration
EXTRACTORS_CONFIG = {
    'profile_extractor': {
        'model': 'gemma3:4b',
        'url': 'http://localhost:11434',
        'temperature': 0.0,  # Deterministic for consistent personal info extraction
        'num_predict': 8192,
        'timeout': 45         # ← INCREASED timeout to handle longer processing
    },
    'skills_extractor': {
        'model': 'gemma3:12b',
        'url': 'http://localhost:11434',
        'temperature': 0.0,  # Completely deterministic - NO creativity for accurate extraction
        'num_predict': 8192,
        'timeout': 60         # ← INCREASED timeout
    },
    'education_extractor': {
        'model': 'gemma3:12b',
        'url': 'http://localhost:11434',
        'temperature': 0.0,  # Deterministic for education info
        'num_predict': 8192,
        'timeout': 45         # ← INCREASED timeout
    },
    'experience_extractor': {
        'model': 'gemma3:12b',  # Slightly larger for complex work experience parsing
        'url': 'http://localhost:11434',
        'temperature': 0.1,
        'num_predict': 8192,
        'timeout': 75           # ← INCREASED timeout
    },
    'yoe_extractor': {
        'model': 'gemma3:4b',  # Needs good calculation and reasoning
        'url': 'http://localhost:11434',
        'temperature': 0.0,  # Deterministic for calculations
        'num_predict': 8192,
        'timeout': 60           # ← INCREASED timeout
    },
    
    # Keep existing configurations for other extractors...
    'career_transition_extractor': {
        'model': 'gemma3:12b',
        'url': 'http://localhost:11434',
        'temperature': 0.2,
        'num_predict': 8192,
        'timeout': 90
    },
    'field_relevance_extractor': {
        'model': 'gemma3:4b',
        'url': 'http://localhost:11434',
        'temperature': 0.1,
        'num_predict': 8192,
        'timeout': 60
    },
    'duration_extractor': {
        'model': 'gemma3:4b',
        'url': 'http://localhost:11434',
        'temperature': 0.0,
        'num_predict': 8192,
        'timeout': 30
    },
    'career_level_extractor': {
        'model': 'gemma3:12b',
        'url': 'http://localhost:11434',
        'temperature': 0.1,
        'num_predict': 8192,
        'timeout': 90
    },
    'field_classification_extractor': {
        'model': 'gemma3:4b',
        'url': 'http://localhost:11434',
        'temperature': 0.1,
        'num_predict': 8192,
        'timeout': 60
    },
    'role_type_extractor': {
        'model': 'gemma3:4b',
        'url': 'http://localhost:11434',
        'temperature': 0.1,
        'num_predict': 8192,
        'timeout': 60
    },
    'job_role_estimation_extractor': {
        'model': 'gemma3:12b',
        'url': 'http://localhost:11434',
        'temperature': 0.2,
        'num_predict': 8192,
        'timeout': 120
    }
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
    'page_title': "iATS",
    'page_icon': "assets/noBgBlack.png",
    'layout': 'wide'
}

# Ensure necessary directories exist
os.makedirs(UPLOAD_CONFIG['upload_folder'], exist_ok=True)
os.makedirs(CHROMA_CONFIG['persist_directory'], exist_ok=True) 