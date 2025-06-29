"""
<<<<<<< HEAD
Simple SkillsExtractor using LLM for skills extraction.
=======
Skills extractor for technical and soft skills.
>>>>>>> parent of 1f716e87 (.)
"""
from typing import Type, Dict, Any
from .base_extractor import BaseExtractor
from models import Skills


class SkillsExtractor(BaseExtractor):
<<<<<<< HEAD
    """Simple extractor for skills using LLM."""
=======
    """Extractor for skills."""
>>>>>>> parent of 1f716e87 (.)
    
    def get_model(self) -> Type[Skills]:
        """Get the Pydantic model for skills extraction."""
        return Skills
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for skills extraction."""
        return """
<<<<<<< HEAD
Extract all skills mentioned in the following resume text.

INSTRUCTIONS:
1. Extract ONLY skills that are explicitly mentioned in the text
2. Do NOT make up or infer skills
3. Categorize skills into appropriate categories
4. Include both technical and soft skills

SKILL CATEGORIES:
- Programming Languages: Python, Java, JavaScript, C++, etc.
- Databases: MySQL, PostgreSQL, MongoDB, etc.
- Cloud Platforms: AWS, Azure, Google Cloud, etc.
- Frameworks & Libraries: React, Django, Spring, etc.
- Software & Applications: Microsoft Office, Photoshop, AutoCAD, etc.
- Technical Skills: Machine Learning, Data Analysis, etc.
- Soft Skills: Leadership, Communication, Project Management, etc.
- Certifications: PMP, AWS Certified, etc.
- Languages: English, Spanish, etc.

Return as JSON with category names as keys and arrays of skills as values.
=======
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
>>>>>>> parent of 1f716e87 (.)

Resume Text:
{text}

{format_instructions}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the skills extraction output."""
<<<<<<< HEAD
        return output
=======
        return output 
>>>>>>> parent of 1f716e87 (.)
