"""
<<<<<<< HEAD
Simple ProfileExtractor using LLM for contact information extraction.
=======
Profile extractor for personal information.
>>>>>>> parent of 1f716e87 (.)
"""
from typing import Type, Dict, Any
from .base_extractor import BaseExtractor
from models import Profile


class ProfileExtractor(BaseExtractor):
<<<<<<< HEAD
    """Simple extractor for profile information using LLM."""
=======
    """Extractor for profile/personal information."""
>>>>>>> parent of 1f716e87 (.)
    
    def get_model(self) -> Type[Profile]:
        """Get the Pydantic model for profile extraction."""
        return Profile
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for profile extraction."""
        return """
Extract contact information from the following resume text.

INSTRUCTIONS:
1. Extract ONLY information that is explicitly present in the text
2. Do NOT make up, guess, or infer any information
3. Use null for any field not found
4. Do NOT use example data

FIELDS TO EXTRACT:
- name: Full name of the person
- contact_number: Phone/mobile number
- email: Email address
- address: Full street address
- city: City name
- state: State/province
- country: Country name
- postal_code: ZIP/postal code
- linkedin: LinkedIn profile URL
- github: GitHub profile URL
- portfolio: Portfolio website URL
- nationality: Nationality if mentioned
- date_of_birth: Date of birth if mentioned

Return as JSON with the exact field names above.

Resume Text:
{text}

{format_instructions}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the profile extraction output."""
        return output 