"""
Simple FieldClassificationExtractor using LLM for field classification.
"""
from typing import Type, Dict, Any, List
from .base_extractor import BaseExtractor
from pydantic import BaseModel, Field


class FieldClassificationAnalysis(BaseModel):
    """Model for field classification analysis."""
    primary_field: str = Field(description="The primary professional field")
    confidence_score: int = Field(ge=1, le=10, description="Confidence in field classification (1-10)")
    reasoning: str = Field(description="Brief explanation of field determination")


class FieldClassificationExtractor(BaseExtractor):
    """Simple extractor for field classification using LLM."""
    
    def get_model(self) -> Type[FieldClassificationAnalysis]:
        """Get the Pydantic model."""
        return FieldClassificationAnalysis
    
    def get_prompt_template(self) -> str:
        """Get the prompt template."""
        return """
Classify the primary professional field based on the skills and experience provided.

FIELD OPTIONS:
- Data Science & Analytics
- Web Development
- Backend Development
- Mobile Development
- DevOps & Cloud
- Machine Learning
- Software Engineering
- Business Analysis
- Marketing & Sales
- Finance & Accounting
- Healthcare
- Education
- General

INSTRUCTIONS:
1. Analyze the skills, job titles, and experience
2. Determine the best matching field
3. Provide confidence score and reasoning

Resume Data:
{text}

{format_instructions}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the output."""
        return {'fieldclassificationanalysis': output} 