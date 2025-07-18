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

# LLM Configuration - Supports both Ollama and OpenAI
LLM_CONFIG = {
    # Default provider: 'ollama' or 'openai'
    'default_provider': 'ollama',
    
    # Ollama Configuration
    'ollama': {
        'default_model': 'gemma3:27b',
        'default_url': 'http://localhost:11434',
        'temperature': 0.1,
        'num_ctx': 16384,
        'num_predict': 16384,
        'top_k': 10,
        'top_p': 0.9,
        'timeout': 60
    },
    
    # OpenAI Configuration
    'openai': {
        'default_model': 'gpt-4o-mini',  # Cost-effective model, you can change to gpt-4 if needed
        'temperature': 0.1,
        'max_tokens': 16384,
        'top_p': 0.9,
        'timeout': 60,
        # OpenAI API key should be set as environment variable: OPENAI_API_KEY
        # You can also set it here if you prefer (not recommended for security)
        'api_key': None  # Will use environment variable OPENAI_API_KEY
    }
}

# Chatbot Specialists Configuration
SPECIALISTS_CONFIG = {
    'intent_analysis': {
        'model': 'gemma3:4b',
        'url': 'http://localhost:11434',
        'temperature': 0.0,  # Deterministic for consistent intent classification
        'num_predict': 200,
        'timeout': 30
    },
    'name_extraction': {
        'model': 'gemma3:4b',
        'url': 'http://localhost:11434',
        'temperature': 0.0,  # Deterministic for accurate name extraction
        'num_predict': 50,
        'timeout': 30
    },
    'query_enhancement': {
        'model': 'gemma3:4b',
        'url': 'http://localhost:11434',
        'temperature': 0.2,  # Slight creativity for query expansion
        'num_predict': 300,
        'timeout': 45
    },
    'response_generation': {
        'model': 'gemma3:12b',  # Larger model for better responses
        'url': 'http://localhost:11434',
        'temperature': 0.3,  # More conversational
        'num_predict': 4096,
        'timeout': 60
    },
    'search_response': {
        'model': 'gemma3:12b',  # Larger model for detailed search responses
        'url': 'http://localhost:11434',
        'temperature': 0.2,  # Structured but professional
        'num_predict': 4096,
        'timeout': 60
    },
    'info_response': {
        'model': 'gemma3:12b',  # Larger model for detailed candidate information
        'url': 'http://localhost:11434',
        'temperature': 0.2,  # Structured but professional
        'num_predict': 4096,
        'timeout': 60
    },
    'general_response': {
        'model': 'gemma3:12b',  # Medium model for general conversation
        'url': 'http://localhost:11434',
        'temperature': 0.4,  # More conversational and friendly
        'num_predict': 2048,
        'timeout': 45
    },
    'filter_matching': {
        'model': 'gemma3:4b',  # Lightweight model for semantic matching
        'url': 'http://localhost:11434',
        'temperature': 0.2,  # Structured matching with slight flexibility
        'num_predict': 512,
        'timeout': 30
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