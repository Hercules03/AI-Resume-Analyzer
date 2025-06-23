"""
Skills extractor for technical and soft skills.
"""
from typing import Type, Dict, Any
from .base_extractor import BaseExtractor
from models import Skills


class SkillsExtractor(BaseExtractor):
    """Extractor for skills."""
    
    def get_model(self) -> Type[Skills]:
        """Get the Pydantic model for skills extraction."""
        return Skills
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for skills extraction."""
        return """
You are an assistant that extracts and categorizes skills mentioned in resume text.
Focus on the Skills section and also extract skills mentioned throughout the resume.

Categorize skills into the following categories:
- Programming Languages (Python, Java, JavaScript, C++, etc.)
- Frameworks & Libraries (React, Django, TensorFlow, Spring, etc.)
- Databases (MySQL, PostgreSQL, MongoDB, Redis, etc.)
- Tools & Platforms (Git, Docker, AWS, Jenkins, Kubernetes, etc.)
- Operating Systems (Windows, Linux, macOS, Ubuntu, etc.)
- Methodologies (Agile, DevOps, Scrum, CI/CD, etc.)
- Soft Skills (Leadership, Communication, Problem-solving, etc.)
- Languages (English, Spanish, French, etc. with proficiency levels)
- Domain Knowledge (Machine Learning, Web Development, Data Science, etc.)

Return your output as a JSON object with the schema provided below.
Use empty arrays for categories where no skills are found.

{format_instructions}

Resume Text:
{text}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the skills extraction output."""
        return output 