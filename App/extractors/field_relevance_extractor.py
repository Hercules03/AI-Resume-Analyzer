"""
Simple FieldRelevanceExtractor using LLM for field relevance analysis.
"""
from typing import Type, Dict, Any
from .base_extractor import BaseExtractor
from pydantic import BaseModel, Field


class FieldRelevanceAnalysis(BaseModel):
    """Model for field relevance analysis."""
    is_relevant: bool = Field(description="Whether the experience is relevant to the target field")
    relevance_score: int = Field(ge=1, le=10, description="Relevance score from 1-10")
    reasoning: str = Field(description="Brief explanation of relevance assessment")


class FieldRelevanceExtractor(BaseExtractor):
    """Simple extractor for field relevance analysis using LLM."""
    
    def get_model(self) -> Type[FieldRelevanceAnalysis]:
        """Get the Pydantic model."""
        return FieldRelevanceAnalysis
    
    def get_prompt_template(self) -> str:
        """Get the prompt template."""
        return """
Analyze how relevant the work experience is to the target field.

INSTRUCTIONS:
1. Consider the job title, responsibilities, and skills used
2. Determine relevance to the target field
3. Provide relevance score (1-10) and reasoning

Target Field: {target_field}
Work Experience: {text}

{format_instructions}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the output."""
        return {'fieldrelevanceanalysis': output} 