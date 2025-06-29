"""
Simple ExperienceExtractor using LLM for work experience extraction.
"""
from typing import Type, Dict, Any
from .base_extractor import BaseExtractor
from models import WorkExperience


class ExperienceExtractor(BaseExtractor):
    """Simple extractor for work experience using LLM."""
    
    def get_model(self) -> Type[WorkExperience]:
        """Get the Pydantic model."""
        return WorkExperience
    
    def get_prompt_template(self) -> str:
        """Get the prompt template."""
        return """
Extract all work experience information from the following resume text.

INSTRUCTIONS:
1. Extract ONLY work experience that is explicitly mentioned
2. Do NOT make up or infer any information
3. Use null for any field not found
4. Include all jobs, internships, and relevant positions

Look for:
- Job title/Position
- Company name
- Employment dates (start and end)
- Location
- Job responsibilities and achievements
- Technologies/tools used
- Employment type (full-time, part-time, contract, etc.)

Resume Text:
{text}

{format_instructions}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the output."""
        return {'work_experiences': output if isinstance(output, list) else [output]} 