"""
Simple YoeExtractor using LLM for years of experience calculation.
"""
from typing import Type, Dict, Any
from .base_extractor import BaseExtractor
from pydantic import BaseModel, Field


class YearsOfExperience(BaseModel):
    """Model for years of experience analysis."""
    total_years: float = Field(description="Total years of professional experience")
    relevant_years: float = Field(description="Years of relevant experience in primary field")
    reasoning: str = Field(description="Brief explanation of calculation")


class YoeExtractor(BaseExtractor):
    """Simple extractor for years of experience calculation using LLM."""
    
    def get_model(self) -> Type[YearsOfExperience]:
        """Get the Pydantic model."""
        return YearsOfExperience
    
    def get_prompt_template(self) -> str:
        """Get the prompt template."""
        return """
Calculate the total years of professional experience from the work history.

INSTRUCTIONS:
1. Add up all professional work experience durations
2. Calculate relevant experience in the primary field
3. Provide reasoning for the calculations

Consider:
- Full-time, part-time, contract positions
- Internships (count as partial experience)
- Overlapping periods (don't double count)
- Career gaps or breaks

Work Experience:
{text}

{format_instructions}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the output."""
        return {'YoE': output} 