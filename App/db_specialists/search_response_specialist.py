"""
Search response specialist for generating responses to candidate search queries.
"""
from typing import Type, Optional, Dict, Any, List
from .base_specialist import BaseSpecialist
from pydantic import BaseModel


class SearchResponseSpecialist(BaseSpecialist):
    """Specialist for generating responses to candidate search queries."""
    
    def get_model(self) -> Optional[Type[BaseModel]]:
        """No structured output needed for response generation."""
        return None
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for search response generation."""
        return """You are an expert HR assistant specializing in **candidate search and recruitment**. Your primary role is to help HR professionals find the best candidates for their open positions by presenting search results in a clear, actionable format.

**Your Specialization:**

* **Candidate Search Results:** Present candidate search results in a structured, easy-to-scan format
* **Candidate Ranking:** Highlight the best matches based on qualifications and experience
* **Skill Matching:** Clearly show how candidate skills align with search criteria
* **Ranking & Recommendations:** Rank candidates by relevance and provide hiring recommendations
* **Next Steps:** Suggest concrete next steps for HR professionals

**Response Format for Search Results:**

1. **Search Summary:** Brief overview of what was searched and how many results found
2. **Top Candidates:** List the best matches with:
   - Candidate name and brief background
   - Key matching skills and experience
   - Why they're a good fit
   - How to get their contact information
3. **Additional Candidates:** Brief mention of other potential matches
4. **Recommendations:** Specific advice on which candidates to prioritize
5. **Next Steps:** Suggested actions (contact, interview, request more info)

**Contact Information Guidelines:**
- **Never assume or fabricate contact details**
- **Guide users to request specific contact information if needed**
- **Suggest asking follow-up questions like "What's [candidate name]'s email?" or "How can I contact [candidate name]?"**
- **Focus on qualifications and fit rather than contact logistics**

**Your responses should be:**
- **Professional and recruitment-focused**
- **Action-oriented with clear next steps**
- **Detailed about candidate qualifications**
- **Helpful in making hiring decisions**"""
    
    def get_user_prompt_template(self) -> str:
        """Get the user prompt template for search response generation."""
        return """User Search Request: {user_message}

Search Results Found:
{context}

Number of Results: {num_results}

Please provide a comprehensive search response that includes:
1. A summary of the search and results found
2. Detailed information about the top matching candidates (focus on qualifications, not contact details)
3. Clear explanations of why these candidates are good matches
4. Guidance on how to get contact information (suggest asking follow-up questions)
5. Specific recommendations for the HR professional
6. Suggested next steps for moving forward

**Important Guidelines:**
- DO NOT display similarity scores or percentages
- DO NOT show or assume contact information - instead guide users to ask for it
- Focus on candidate qualifications, experience, and fit
- Format your response to be immediately actionable for hiring decisions"""
    
    def prepare_input_data(self, **kwargs) -> Dict[str, Any]:
        """Prepare input data for search response generation."""
        search_results = kwargs.get('search_results', [])
        
        return {
            'user_message': kwargs.get('user_message', ''),
            'context': kwargs.get('context', 'No candidate data available.'),
            'num_results': len(search_results)
        }
    
    def process_output(self, output: str, **kwargs) -> str:
        """Process the search response generation output."""
        return output.strip()
    
    def _get_fallback_output(self, **kwargs) -> str:
        """Get fallback output when search response generation fails."""
        return """I apologize, but I'm having trouble processing your candidate search right now. 

**Suggested next steps:**
1. Try rephrasing your search with more specific requirements
2. Use different keywords or skills in your search
3. Check if there are candidates in the database matching your criteria
4. Contact support if the issue persists

How else can I help you find the right candidates?""" 