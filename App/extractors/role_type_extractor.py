"""
Simple RoleTypeExtractor using LLM for role type classification.
"""
from typing import Type, Dict, Any
from .base_extractor import BaseExtractor
from pydantic import BaseModel, Field


class RoleTypeAnalysis(BaseModel):
    """Model for role type analysis."""
    primary_role_type: str = Field(description="Primary role type classification")
    confidence_score: int = Field(ge=1, le=10, description="Confidence in role type classification (1-10)")
    reasoning: str = Field(description="Brief explanation of role type determination")


class RoleTypeExtractor(BaseExtractor):
    """Simple extractor for role type classification using LLM."""
    
    def get_model(self) -> Type[RoleTypeAnalysis]:
        """Get the Pydantic model."""
        return RoleTypeAnalysis
    
    def get_prompt_template(self) -> str:
        """Get the prompt template."""
        return """
Classify the primary role type based on the candidate's work experience and skills.

ROLE TYPE OPTIONS:
- Technical: Hands-on technical work (programming, engineering, data analysis)
- Management: People management, team leadership, strategic planning
- Creative: Design, content creation, marketing, user experience
- Business: Sales, consulting, business development, operations
- Hybrid: Combination of multiple role types

INSTRUCTIONS:
1. Analyze the job titles, responsibilities, and skills
2. Determine the dominant role type
3. Provide confidence score and reasoning

Resume Data:
{text}

{format_instructions}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the output."""
        return {'roletypeanalysis': output} 