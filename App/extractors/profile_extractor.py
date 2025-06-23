"""
Profile extractor for personal information.
"""
from typing import Type, Dict, Any
from .base_extractor import BaseExtractor
from models import Profile


class ProfileExtractor(BaseExtractor):
    """Extractor for profile/personal information."""
    
    def get_model(self) -> Type[Profile]:
        """Get the Pydantic model for profile extraction."""
        return Profile
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for profile extraction."""
        return """
You are an assistant that extracts personal/profile information from resume text.
Focus on contact information, personal details, and online profiles.

Extract the following information if available:
- Full name
- Contact number/phone
- Email address
- Physical address details (address, city, state, country, postal code)
- Online profiles (LinkedIn, GitHub, portfolio)
- Personal information (nationality, date of birth)

Return your output as a JSON object with the schema provided below.
Use null for any field that cannot be found in the resume.

{format_instructions}

Resume Text:
{text}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the profile extraction output."""
        return output 