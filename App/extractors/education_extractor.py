"""
Simple EducationExtractor using LLM for education information extraction.
"""
from typing import Type, Dict, Any
from .base_extractor import BaseExtractor
from models import Education


class EducationExtractor(BaseExtractor):
    """Simple extractor for education information using LLM."""
    
    def get_model(self) -> Type[Education]:
        """Get the Pydantic model."""
        return Education
    
    def get_prompt_template(self) -> str:
        """Get the prompt template."""
        return """
Extract all education information from the following resume text.

INSTRUCTIONS:
1. Extract ONLY education information that is explicitly mentioned
2. Do NOT make up or infer any information
3. Use null for any field not found
4. Include all degrees, certifications, and courses

Look for:
- Degree (Bachelor's, Master's, PhD, etc.)
- Field of study/Major
- Institution/University name
- Graduation year or dates
- GPA (if mentioned)
- Location
- Any relevant coursework or achievements

Resume Text:
{text}

{format_instructions}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the output."""
        return {'educations': output if isinstance(output, list) else [output]} 