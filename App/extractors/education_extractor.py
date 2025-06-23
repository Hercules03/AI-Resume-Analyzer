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
Focus on the Education section and extract all educational qualifications.

For each education entry, extract:
- Degree type (Bachelor's, Master's, PhD, Certificate, Diploma, etc.)
- Field of study/Major (Computer Science, Engineering, Business, etc.)
- Institution name (University, College, School name)
- Location (City, State, Country)
- Graduation date (Month/Year or Year)
- GPA/Grade (if mentioned)
- Honors/Distinctions (cum laude, dean's list, etc.)
- Relevant coursework (list of relevant courses)
- Thesis/Project title (if mentioned)

Return your output as a JSON object with the schema provided below.
Include all education entries found in the resume.

{format_instructions}

Resume Text:
{text}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the education extraction output."""
        return output 