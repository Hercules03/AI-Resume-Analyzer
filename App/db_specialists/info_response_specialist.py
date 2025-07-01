"""
Info response specialist for generating detailed responses about specific candidates.
"""
from typing import Type, Optional, Dict, Any, List
from .base_specialist import BaseSpecialist
from pydantic import BaseModel


class InfoResponseSpecialist(BaseSpecialist):
    """Specialist for generating detailed information responses about specific candidates."""
    
    def get_model(self) -> Optional[Type[BaseModel]]:
        """No structured output needed for response generation."""
        return None
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for info response generation."""
        return """You are an expert HR assistant specializing in **candidate information and profile analysis**. Your primary role is to provide detailed, comprehensive information about specific candidates when HR professionals need to learn more about them.

**Your Specialization:**

* **Candidate Profiles:** Present complete candidate information in a structured, professional format
* **Resume Analysis:** Extract and highlight the most important details from candidate data
* **Contact Information:** Always provide complete contact details when available
* **Experience Summary:** Clearly summarize work history and achievements
* **Skills Assessment:** List and categorize relevant skills and competencies
* **Educational Background:** Present education details clearly
* **Suitability Analysis:** Help HR professionals understand if a candidate fits their needs

**Response Format for Candidate Information:**

1. **Candidate Overview:** Name, contact info, current role/status
2. **Professional Summary:** Brief overview of their background and expertise
3. **Contact Information:** Email, phone, LinkedIn (if available)
4. **Experience Details:** 
   - Years of experience
   - Key roles and responsibilities
   - Notable achievements or projects
5. **Skills & Competencies:** Technical and soft skills
6. **Education:** Degrees, certifications, institutions
7. **Additional Information:** Any other relevant details
8. **Assessment:** Your professional opinion on their strengths and potential fit

**When Multiple Candidates Match:**
- If multiple candidates have similar names, list all matches
- Clearly distinguish between different candidates
- Ask for clarification if needed

**Your responses should be:**
- **Detailed and comprehensive**
- **Professionally formatted**
- **Contact-information focused**
- **Analytical and insightful**
- **Helpful for making interview decisions**"""
    
    def get_user_prompt_template(self) -> str:
        """Get the user prompt template for info response generation."""
        return """User Information Request: {user_message}

Candidate Information Found:
{context}

Please provide a detailed information response that includes:
1. Complete candidate profile with all available information
2. Professional summary highlighting key qualifications
3. Full contact information for reaching out
4. Detailed experience and skills breakdown
5. Your assessment of their background and potential fit
6. Recommendations for next steps (interview, additional screening, etc.)

If multiple candidates match the request, clearly present each one separately.
Format your response to help HR professionals make informed decisions about candidate outreach."""
    
    def prepare_input_data(self, **kwargs) -> Dict[str, Any]:
        """Prepare input data for info response generation."""
        return {
            'user_message': kwargs.get('user_message', ''),
            'context': kwargs.get('context', 'No candidate information available.')
        }
    
    def process_output(self, output: str, **kwargs) -> str:
        """Process the info response generation output."""
        return output.strip()
    
    def _get_fallback_output(self, **kwargs) -> str:
        """Get fallback output when info response generation fails."""
        return """I'm unable to retrieve the specific candidate information you requested at the moment.

**Possible reasons:**
1. The candidate name might not match exactly with our database records
2. There might be no candidates with that name in our system
3. The candidate data might be incomplete

**Suggested next steps:**
1. Try searching with just the first or last name
2. Check the spelling of the candidate's name
3. Use the general search function to find similar candidates
4. Contact support if you believe the candidate should be in our database

Would you like me to help you search for candidates in a different way?""" 