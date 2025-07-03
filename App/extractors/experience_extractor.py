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

For each work experience entry, extract:

* **Job Title/Position:** (e.g., Marketing Executive, Registered Nurse, Sales Associate, Project Coordinator, Executive Assistant, etc. - Use common Hong Kong terminologies if known)
* **Company/Organization Name:** (e.g., [Hong Kong Bank Name], [Well-known Hong Kong Corporation], Self-Employed)
* **Location:** (District, Hong Kong - e.g., Central, Tsim Sha Tsui, Kwun Tong. If a different country, then City, Country)
* **Start Date:** (Month/Year format, e.g., "January 2020")
* **End Date:** (Month/Year format, or "Present" if current)
* **Duration:** (e.g., "2 years 3 months," "6 months," calculated from start and end dates)
* **Key Responsibilities and Achievements:** (List of bullet points detailing duties, accomplishments, and quantifiable results. Prioritize achievements with metrics where present. **Emphasize results-oriented achievements and contributions to the company's bottom line or efficiency, which are highly valued in Hong Kong.**)
* **Relevant Tools/Software/Equipment Used:** (Specific to the role, e.g., CRM software, medical equipment, design tools, financial platforms, manufacturing machinery, **mentioning commonly used software in Hong Kong such as Chinese input methods if relevant, specific accounting software prevalent in HK, or enterprise systems widely adopted.**)
* **Industry Sector:** (e.g., Retail, Healthcare, Finance [**mention specific financial sub-sectors like FinTech, Investment Banking, Asset Management as applicable in HK**], Education, Hospitality, Manufacturing, Non-Profit, Government, **Property Development, Logistics & Shipping, Tourism, Public Utilities - these are significant sectors in Hong Kong.**)
* **Employment Type:** (e.g., Full-time, Part-time, Contract, Internship, Volunteer, Freelance, **Temporary - often used in HK for short-term engagements.**)
* **Language Proficiency Applied (if applicable):** (e.g., Cantonese, Mandarin, English - specify if daily use in professional setting, business communication, etc. **This is crucial in Hong Kong's multilingual business environment.**)
* **Notable Projects/Clients (if non-confidential):** (Specific to the Hong Kong market or regional projects if relevant. **Demonstrates local relevance and network.**)

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