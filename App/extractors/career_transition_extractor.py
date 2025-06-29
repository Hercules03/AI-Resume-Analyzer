"""
Simple CareerTransitionExtractor using LLM for career transition analysis.
"""
from typing import Type, Dict, Any, List
from .base_extractor import BaseExtractor
from pydantic import BaseModel, Field


class CareerTransitionAnalysis(BaseModel):
    """Model for career transition analysis."""
    has_transitions: bool = Field(description="Whether career transitions were detected")
    transition_summary: str = Field(description="Summary of career transitions")
    career_path_type: str = Field(description="Type of career path: Linear, Transitional, Multi-field, or Exploratory")


class CareerTransitionExtractor(BaseExtractor):
    """Simple extractor for career transition analysis using LLM."""
    
    def get_model(self) -> Type[CareerTransitionAnalysis]:
        """Get the Pydantic model."""
        return CareerTransitionAnalysis
    
    def get_prompt_template(self) -> str:
        """Get the prompt template."""
        return """
Analyze the work experience to identify career transitions and progression patterns.

INSTRUCTIONS:
1. Look for changes in job roles, industries, or fields
2. Identify if the person has moved between different career areas
3. Determine the overall career path type
4. Summarize any major transitions

CAREER PATH TYPES:
- Linear: Steady progression in same field
- Transitional: Clear transition between different fields
- Multi-field: Experience across multiple related fields
- Exploratory: Experience across diverse unrelated fields

Work Experience Data:
{text}

{format_instructions}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the output."""
        return {'careerprogressionanalysis': output} 