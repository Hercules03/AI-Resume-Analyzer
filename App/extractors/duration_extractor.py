"""
Simple DurationExtractor using LLM for duration analysis.
"""
from typing import Type, Dict, Any
from .base_extractor import BaseExtractor
from pydantic import BaseModel, Field


class DurationAnalysis(BaseModel):
    """Model for duration analysis."""
    total_months: int = Field(description="Total duration in months")
    duration_string: str = Field(description="Human-readable duration (e.g., '2 years 3 months')")
    is_current: bool = Field(description="Whether this is a current position")


class DurationExtractor(BaseExtractor):
    """Simple extractor for duration analysis using LLM."""
    
    def get_model(self) -> Type[DurationAnalysis]:
        """Get the Pydantic model."""
        return DurationAnalysis
    
    def get_prompt_template(self) -> str:
        """Get the prompt template."""
        return """
Extract and calculate the duration from date ranges in the work experience.

INSTRUCTIONS:
1. Parse start and end dates to calculate total duration
2. Convert to months for standardization
3. Determine if the position is current (ongoing)

Work Experience Date Information:
{text}

{format_instructions}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the output."""
        return {'durationanalysis': output} 