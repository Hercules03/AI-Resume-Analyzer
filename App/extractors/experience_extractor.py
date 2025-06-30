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
Focus on the Experience, Work History, Professional Experience, or relevant sections like "Volunteer Experience" or "Internships."

For each work experience entry, extract:
- **Job Title/Position:** (e.g., Marketing Manager, Registered Nurse, Sales Associate, Project Coordinator, Executive Assistant, etc.)
- **Company/Organization Name:** (e.g., ABC Corporation, St. Jude's Hospital, City of [City Name], Self-Employed)
- **Location:** (City, State/Province, Country - if available)
- **Start Date:** (Month/Year format, e.g., "January 2020")
- **End Date:** (Month/Year format, or "Present" if current)
- **Duration:** (e.g., "2 years 3 months," "6 months," calculated from start and end dates)
- **Key Responsibilities and Achievements:** (List of bullet points detailing duties, accomplishments, and quantifiable results. Prioritize achievements with metrics where present.)
- **Relevant Tools/Software/Equipment Used:** (Specific to the role, e.g., CRM software, medical equipment, design tools, financial platforms, manufacturing machinery, etc.)
- **Industry Sector:** (e.g., Retail, Healthcare, Finance, Education, Hospitality, Manufacturing, Non-Profit, Government, etc.)
- **Employment Type:** (e.g., Full-time, Part-time, Contract, Internship, Volunteer, Freelance)

```Resume Text
{text}
```

Return your output as a JSON object with the schema provided below.
Include all work experience entries found in the resume.

{format_instructions}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the experience extraction output."""
        return output 