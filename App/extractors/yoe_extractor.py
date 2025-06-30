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

1.  **Total Years of Professional Experience:**
    * Add up the durations of all professional work experiences, including full-time, part-time, contract, and relevant self-employment or consulting roles.
    * Convert months to years for precise calculation (e.g., 30 months = 2.5 years).
    * Include internships if they are substantial and directly relevant to the professional field, especially for early-career individuals. Clearly distinguish them if they are the only experience.
    * Exclude purely academic or unrelated volunteer experiences unless they demonstrably involve professional-level responsibilities.

2.  **Career Level:** Determine the career level based on the calculated experience and the nature of the job titles and responsibilities described.
    * **"Entry Level":** Typically 0-2 years of relevant professional experience. Job titles often include "Junior," "Assistant," "Associate," or foundational roles.
    * **"Mid-Level":** Typically 2-7 years of relevant professional experience. Roles often involve independent work, some project ownership, or mentoring junior staff. Job titles like "Specialist," "Coordinator," "Analyst," "Representative."
    * **"Senior Level":** Typically 7-15 years of relevant professional experience. Roles often include significant autonomy, leadership of projects or small teams, strategic input, and complex problem-solving. Job titles like "Senior," "Lead," "Manager," "Consultant."
    * **"Management/Leadership Level":** Typically 10+ years of relevant professional experience, often with a focus on managing people, departments, or significant organizational functions. Job titles like "Director," "Head of," "Vice President," "Senior Manager," "General Manager."
    * **"Executive Level":** Typically 15+ years of experience, often at a strategic, organizational-wide level, responsible for significant business units or the entire organization. Job titles like "Chief [X] Officer (CXO)," "President," "General Manager" (for a major division).

3.  **Primary Field/Domain of Expertise:** Determine the primary professional field or industry domain based on the majority of job titles, responsibilities, and industry sectors mentioned throughout the resume.
    * Examples: "Marketing & Communications," "Healthcare Management," "Financial Services," "Human Resources," "Supply Chain & Logistics," "Education Administration," "Legal Practice," "Non-Profit Leadership," "Creative Arts & Design," "Manufacturing Operations," etc.

Analyze the entire resume text, including job descriptions and achievements, to make these determinations comprehensively.

Resume Text:
```Resume Text
{text}
```

Return your output as a JSON object with the schema provided below.

{format_instructions}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the YoE extraction output."""
        # The output should contain 'yearsofexperience' key with the YoE data
        yoe_data = output.get('yearsofexperience', {})
        return {'yoe': yoe_data} 