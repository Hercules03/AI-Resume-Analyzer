"""
Utility functions for LLM operations and metadata handling
"""
import json
from typing import Dict, Any
from datetime import datetime


def export_metadata_to_json(metadata: Dict[str, Any], filename: str = None) -> str:
    """Export metadata to JSON string"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resume_metadata_{timestamp}.json"
    
    try:
        json_str = json.dumps(metadata, indent=2, ensure_ascii=False)
        return json_str
    except Exception as e:
        return f"Error exporting to JSON: {str(e)}" 