"""
Simple JobRoleEstimationExtractor using LLM for job role estimation.
"""
from typing import Type, Dict, Any, List
from .base_extractor import BaseExtractor
from pydantic import BaseModel, Field


class JobRoleEstimation(BaseModel):
    """Model for job role estimation analysis."""
    primary_job_role: str = Field(description="Primary recommended job role")
    confidence_score: int = Field(ge=1, le=10, description="Confidence in primary role recommendation (1-10)")
    reasoning: str = Field(description="Brief justification for the recommended role")


class JobRoleEstimationExtractor(BaseExtractor):
    """Simple extractor for job role estimation using LLM."""
    
    def get_model(self) -> Type[JobRoleEstimation]:
        """Get the Pydantic model."""
        return JobRoleEstimation
    
    def get_prompt_template(self) -> str:
        """Get the prompt template."""
        return """
Analyze the resume to recommend the most suitable job role based on skills and experience.

INSTRUCTIONS:
1. Consider the candidate's skills, experience, and career level
2. Recommend a specific job role that best fits their profile
3. Provide confidence score and reasoning

EXAMPLE JOB ROLES:
- Software Engineer
- Data Scientist
- Frontend Developer
- Backend Developer
- Product Manager
- Business Analyst
- Marketing Manager
- DevOps Engineer
- UX Designer
- Project Manager

Resume Data:
{text}

{format_instructions}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the output."""
        return {'jobroleestimation': output} 