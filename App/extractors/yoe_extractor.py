"""
Years of experience extractor for career analysis.
"""
from typing import Type, Dict, Any
from .base_extractor import BaseExtractor
from models import YearsOfExperience


class YoeExtractor(BaseExtractor):
    """Extractor for years of experience and career level."""
    
    def get_model(self) -> Type[YearsOfExperience]:
        """Get the Pydantic model for YoE extraction."""
        return YearsOfExperience
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for YoE extraction."""
        return """
You are an assistant that analyzes work experience to determine total years of experience and career level.

Based on the resume text provided, calculate:

1. Total Years of Experience: Calculate the total number of years of professional work experience
   - Add up all work experience durations
   - Convert months to years (e.g., 30 months = 2.5 years)
   - Include full-time, part-time, and contract positions
   - Exclude internships unless they are the only experience

2. Career Level: Determine the career level based on experience and job titles
   - "Entry Level": 0-2 years of experience, junior positions
   - "Mid Level": 2-5 years of experience, regular positions
   - "Senior Level": 5-10 years of experience, senior positions, team lead roles
   - "Executive Level": 10+ years of experience, management, director, VP roles

3. Primary Field: Determine the primary field of expertise based on job titles and experience
   - Examples: "Software Engineering", "Data Science", "Product Management", "Sales", etc.

Analyze the entire resume text to make these determinations.

Return your output as a JSON object with the schema provided below.

{format_instructions}

Resume Text:
{text}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the YoE extraction output."""
        # The output should contain 'yearsofexperience' key with the YoE data
        yoe_data = output.get('yearsofexperience', {})
        return {'yoe': yoe_data} 