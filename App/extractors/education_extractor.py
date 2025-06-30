"""
Education extractor for academic background.
"""
from typing import Type, Dict, Any, List
from .base_extractor import BaseExtractor
from models import Education
from pydantic import BaseModel, Field


class EducationList(BaseModel):
    """Model for list of education entries."""
    educations: List[Education] = Field(default_factory=list)


class EducationExtractor(BaseExtractor):
    """Extractor for education information."""
    
    def get_model(self) -> Type[EducationList]:
        """Get the Pydantic model for education extraction."""
        return EducationList
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for education extraction."""
        return """
You are an assistant that extracts education information from resume text.

This text is from the first page of the resume, where education information is often prominently featured.

**Strictly focus on the "Education" or "Academic" or "Certificates" section and extract all educational qualifications only from these sections.** Do not extract information from other sections like "CERTIFICATION" or "CAREER HISTORY" unless they explicitly represent an academic degree or formal educational program.

For each education entry, extract:
- Degree/Qualification Type (e.g., Bachelor's Degree (B.S.), Master's Degree (M.S.), PhD (Ph.D.), Associate's Degree (A.A.), High School Diploma, Certificate, Diploma, Professional Certification, Apprenticeship, etc.)
- Field of Study/Major/Program (e.g., Business Administration, Nursing, Liberal Arts, Culinary Arts, Marketing, Fine Arts, Mechanical Engineering, Paralegal Studies, etc.)
- Institution Name (e.g., University, College, Vocational School, Academy, Training Center, High School name)
- Location (City, State/Province, Country)
- Dates Attended/Graduation Date (e.g., Month/Year - Month/Year, or simply Year of Graduation)
- GPA/Grade/Academic Achievement (if mentioned, e.g., GPA on a 4.0 scale, percentage, specific grade, "Pass," "Distinction")
- Honors/Awards/Distinctions (e.g., Cum Laude, Dean's List, Scholarships, specific academic awards, commendations)

Resume Text (First Page):
```Resume Text
{text}
```

Return your output as a JSON object with the schema provided below.
Include all education entries found in the resume.

{format_instructions}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the education extraction output."""
        return output 