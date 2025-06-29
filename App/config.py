"""
Enhanced configuration settings for better JSON generation with Ollama models.
"""
import os

# ChromaDB Configuration (unchanged)
CHROMA_CONFIG = {
    'persist_directory': './chroma_db',
    'collection_name_resumes': 'resume_data',
    'collection_name_feedback': 'user_feedback',
    'embedding_model': 'all-MiniLM-L6-v2',
    'chunk_size': 1000,
    'chunk_overlap': 200
}

# Legacy MySQL Configuration (kept for reference)
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

# Enhanced LLM Configuration for better JSON generation
LLM_CONFIG = {
    'default_model': 'llama3.1:8b',  # Better JSON support than Gemma
    'alternative_models': ['llama3.1:8b', 'llama3.2:3b', 'qwen2.5:7b'],  # Models with good JSON support
    'default_url': 'http://localhost:11434',
<<<<<<< HEAD
    'temperature': 0.2,  # Deterministic for structured output
    'num_predict': 2048,  # Sufficient for most extractions
    'top_k': 1,  # Most deterministic
    'top_p': 0.1,  # Very focused
    'repeat_penalty': 1.1,  # Prevent repetition
    'timeout': 120,  # Increased timeout for complex extractions
    'stop_sequences': ['```', '---', '\n\n\n'],  # Stop at common terminators
=======
    'temperature': 0.1,
    'num_predict': 4096,  # Reduced for better performance
    'top_k': 10,
    'top_p': 0.9,
    'timeout': 60  # Add timeout for requests
>>>>>>> parent of 1f716e87 (.)
}

# Enhanced Specialists Configuration with optimized settings for JSON
SPECIALISTS_CONFIG = {
    'intent_analysis': {
<<<<<<< HEAD
        'model': 'llama3.1:8b',  # Better for structured tasks
        'url': 'http://localhost:11434',
        'temperature': 0.2,  # Completely deterministic
        'num_predict': 1024,  # Smaller for simple classification
        'top_k': 1,
        'top_p': 0.1,
        'timeout': 60,
        'repeat_penalty': 1.1,
        'stop': ['```', '---']
    },
    'name_extraction': {
        'model': 'llama3.1:8b',
        'url': 'http://localhost:11434',
        'temperature': 0.2,
        'num_predict': 512,  # Very small for name extraction
        'top_k': 1,
        'top_p': 0.1,
        'timeout': 45,
        'repeat_penalty': 1.1,
        'stop': ['```', '---']
    },
    'query_enhancement': {
        'model': 'llama3.1:8b',
        'url': 'http://localhost:11434',
        'temperature': 0.1,  # Slight creativity for enhancement
        'num_predict': 1024,
        'top_k': 3,
        'top_p': 0.3,
        'timeout': 60,
        'repeat_penalty': 1.1,
        'stop': ['```', '---']
=======
        'model': 'gemma3:1b',
        'url': 'http://localhost:11434',
        'temperature': 0.0,  # Deterministic for consistent intent classification
        'num_predict': 200,
        'timeout': 30
    },
    'name_extraction': {
        'model': 'gemma3:1b',
        'url': 'http://localhost:11434',
        'temperature': 0.0,  # Deterministic for accurate name extraction
        'num_predict': 50,
        'timeout': 30
    },
    'query_enhancement': {
        'model': 'gemma3:1b',
        'url': 'http://localhost:11434',
        'temperature': 0.2,  # Slight creativity for query expansion
        'num_predict': 300,
        'timeout': 45
>>>>>>> parent of 1f716e87 (.)
    },
    'response_generation': {
        'model': 'gemma3:12b',
        'url': 'http://localhost:11434',
<<<<<<< HEAD
        'temperature': 0.2,  # Slightly more creative for responses
        'num_predict': 2048,
        'top_k': 5,
        'top_p': 0.5,
        'timeout': 90,
        'repeat_penalty': 1.1,
        'stop': ['```', '---']
    }
}

# Enhanced Extractors Configuration with JSON-optimized settings
EXTRACTORS_CONFIG = {
    'profile_extractor': {
        'model': 'gemma3:27b',  # Better JSON generation
        'url': 'http://localhost:11434',
        'temperature': 0.2,  # Completely deterministic
        'num_predict': 1024,  # Profile info is usually short
        'top_k': 1,
        'top_p': 0.1,
        'timeout': 90,
        'repeat_penalty': 1.1,
        'stop': ['```', '---', '\n\n\n']
    },
    'skills_extractor': {
        'model': 'llama3.1:8b',
        'url': 'http://localhost:11434',
        'temperature': 0.2,  # Deterministic for accurate extraction
        'num_predict': 2048,  # Skills can be numerous
        'top_k': 1,
        'top_p': 0.1,
        'timeout': 120,
        'repeat_penalty': 1.1,
        'stop': ['```', '---', '\n\n\n']
    },
    'education_extractor': {
        'model': 'llama3.1:8b',
        'url': 'http://localhost:11434',
        'temperature': 0.2,
        'num_predict': 1536,
        'top_k': 1,
        'top_p': 0.1,
        'timeout': 90,
        'repeat_penalty': 1.1,
        'stop': ['```', '---', '\n\n\n']
    },
    'experience_extractor': {
        'model': 'llama3.1:8b',
        'url': 'http://localhost:11434',
        'temperature': 0.2,
        'num_predict': 3072,  # Work experience can be lengthy
        'top_k': 1,
        'top_p': 0.1,
        'timeout': 150,
        'repeat_penalty': 1.1,
        'stop': ['```', '---', '\n\n\n']
    },
    'yoe_extractor': {
        'model': 'llama3.1:8b',
        'url': 'http://localhost:11434',
        'temperature': 0.2,
        'num_predict': 512,  # YoE calculation is short
        'top_k': 1,
        'top_p': 0.1,
        'timeout': 60,
        'repeat_penalty': 1.1,
        'stop': ['```', '---', '\n\n\n']
    },
    
    # Enhanced extractors with JSON-optimized settings
    'career_transition_extractor': {
        'model': 'llama3.1:8b',
        'url': 'http://localhost:11434',
        'temperature': 0.2,  # Deterministic for analysis
        'num_predict': 2048,
        'top_k': 1,
        'top_p': 0.1,
        'timeout': 120,
        'repeat_penalty': 1.1,
        'stop': ['```', '---', '\n\n\n']
    },
    'field_relevance_extractor': {
        'model': 'llama3.1:8b',
        'url': 'http://localhost:11434',
        'temperature': 0.2,
        'num_predict': 1024,
        'top_k': 1,
        'top_p': 0.1,
        'timeout': 90,
        'repeat_penalty': 1.1,
        'stop': ['```', '---', '\n\n\n']
    },
    'duration_extractor': {
        'model': 'llama3.1:8b',
        'url': 'http://localhost:11434',
        'temperature': 0.2,
        'num_predict': 512,
        'top_k': 1,
        'top_p': 0.1,
        'timeout': 60,
        'repeat_penalty': 1.1,
        'stop': ['```', '---', '\n\n\n']
    },
    'career_level_extractor': {
        'model': 'llama3.1:8b',
        'url': 'http://localhost:11434',
        'temperature': 0.2,
        'num_predict': 1536,
        'top_k': 1,
        'top_p': 0.1,
        'timeout': 120,
        'repeat_penalty': 1.1,
        'stop': ['```', '---', '\n\n\n']
    },
    'field_classification_extractor': {
        'model': 'llama3.1:8b',
        'url': 'http://localhost:11434',
        'temperature': 0.2,
        'num_predict': 1024,
        'top_k': 1,
        'top_p': 0.1,
        'timeout': 90,
        'repeat_penalty': 1.1,
        'stop': ['```', '---', '\n\n\n']
    },
    'role_type_extractor': {
        'model': 'llama3.1:8b',
        'url': 'http://localhost:11434',
        'temperature': 0.2,
        'num_predict': 1536,
        'top_k': 1,
        'top_p': 0.1,
        'timeout': 120,
        'repeat_penalty': 1.1,
        'stop': ['```', '---', '\n\n\n']
    },
    'job_role_estimation_extractor': {
        'model': 'llama3.1:8b',
        'url': 'http://localhost:11434',
        'temperature': 0.2,
        'num_predict': 2048,
        'top_k': 1,
        'top_p': 0.1,
        'timeout': 150,
        'repeat_penalty': 1.1,
        'stop': ['```', '---', '\n\n\n']
    }
}

# File Upload Configuration (unchanged)
=======
        'temperature': 0.3,  # More conversational
        'num_predict': 4096,
        'timeout': 60
    }
}

# File Upload Configuration
>>>>>>> parent of 1f716e87 (.)
UPLOAD_CONFIG = {
    'allowed_extensions': ['pdf'],
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'upload_folder': './Uploaded_Resumes/'
}

# OCR Configuration (unchanged)
OCR_CONFIG = {
    'default_languages': ['en'],
    'min_confidence': 0.6,
    'dpi': 300
}

# Text Quality Thresholds (unchanged)
TEXT_QUALITY = {
    'min_chars': 50,
    'min_words': 10,
    'max_special_char_ratio': 0.3,
    'min_word_space_ratio': 0.5
}

# Streamlit Page Configuration (unchanged)
PAGE_CONFIG = {
    'page_title': "iATS",
    'page_icon': "assets/noBgBlack.png",
    'layout': 'wide'
}

# JSON Generation Best Practices
JSON_GENERATION_CONFIG = {
    'max_retries': 3,  # Retry failed extractions
    'validation_strict': True,  # Strict validation
    'fallback_to_empty': True,  # Use empty models on failure
    'log_failures': True,  # Log failed extractions for debugging
}

# Model Performance Recommendations
MODEL_RECOMMENDATIONS = {
    'best_for_json': ['llama3.1:8b', 'llama3.2:3b', 'qwen2.5:7b'],
    'recommended_settings': {
        'temperature': 0.2,
        'top_k': 1,
        'top_p': 0.1,
        'repeat_penalty': 1.1
    }
}

# Ensure necessary directories exist
os.makedirs(UPLOAD_CONFIG['upload_folder'], exist_ok=True)
os.makedirs(CHROMA_CONFIG['persist_directory'], exist_ok=True)