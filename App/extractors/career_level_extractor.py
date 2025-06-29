"""
Simple CareerLevelExtractor using LLM for career level analysis.
"""
from typing import Type, Dict, Any, List
from .base_extractor import BaseExtractor
from models import Profile
from pydantic import BaseModel, Field


class CareerLevelAnalysis(BaseModel):
    """Model for career level analysis."""
    career_level: str = Field(description="Determined career level: Entry Level, Junior Level, Mid Level, Senior Level, Expert Level")
    confidence_score: int = Field(ge=1, le=10, description="Confidence in career level assessment (1-10)")
    reasoning: str = Field(description="Brief explanation of career level determination")


class CareerLevelExtractor(BaseExtractor):
    """Simple extractor for career level analysis using LLM."""
    
    def get_model(self) -> Type[CareerLevelAnalysis]:
        """Get the Pydantic model."""
        return CareerLevelAnalysis
    
    def get_prompt_template(self) -> str:
        """Get the prompt template."""
        return """
Analyze the career level based on the work experience information provided.

CAREER LEVELS:
- Entry Level: 0-2 years experience, junior positions
- Junior Level: 2-4 years experience, some responsibility
- Mid Level: 4-8 years experience, solid expertise
- Senior Level: 8+ years experience, leadership roles
- Expert Level: 10+ years experience, high-level expertise

INSTRUCTIONS:
1. Analyze the work experience and job titles
2. Consider years of experience if mentioned
3. Look for leadership indicators and responsibilities
4. Determine the most appropriate career level
5. Provide confidence score and reasoning

Work Experience Data:
{text}

{format_instructions}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the output."""
        return {'careerlevelanalysis': output} 