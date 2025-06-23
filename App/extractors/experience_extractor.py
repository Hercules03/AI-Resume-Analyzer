"""
Work experience extractor for professional background.
"""
from typing import Type, Dict, Any, List
from .base_extractor import BaseExtractor
from models import WorkExperience
from pydantic import BaseModel, Field


class WorkExperienceList(BaseModel):
    """Model for list of work experience entries."""
    work_experiences: List[WorkExperience] = Field(default_factory=list)


class ExperienceExtractor(BaseExtractor):
    """Extractor for work experience information."""
    
    def get_model(self) -> Type[WorkExperienceList]:
        """Get the Pydantic model for experience extraction."""
        return WorkExperienceList
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for experience extraction."""
        return """
You are an assistant that extracts work experience information from resume text.
Focus on the Experience, Work History, or Professional Experience sections.

For each work experience entry, extract:
- Job title/Position (Software Engineer, Manager, Analyst, etc.)
- Company name
- Location (City, State, Country)
- Start date (Month/Year format)
- End date (Month/Year or "Present")
- Duration (e.g., "2 years 3 months")
- Key responsibilities and achievements (list of bullet points)
- Technologies used (programming languages, tools, frameworks)
- Industry sector (Technology, Finance, Healthcare, etc.)
- Employment type (Full-time, Part-time, Contract, Internship, etc.)

Return your output as a JSON object with the schema provided below.
Include all work experience entries found in the resume.

{format_instructions}

Resume Text:
{text}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the experience extraction output."""
        return output 