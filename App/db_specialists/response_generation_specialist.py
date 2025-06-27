"""
Response generation specialist for creating contextual chatbot responses.
"""
from typing import Type, Optional, Dict, Any, List
from .base_specialist import BaseSpecialist
from pydantic import BaseModel


class ResponseGenerationSpecialist(BaseSpecialist):
    """Specialist for generating contextual responses with candidate data."""
    
    def get_model(self) -> Optional[Type[BaseModel]]:
        """No structured output needed for response generation."""
        return None
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for response generation."""
        return """You are an experienced HR assistant with direct access to the company's candidate database.
You have full access to all candidate information and can provide specific details when requested.

YOUR ROLE:
1. Help find candidates based on skills, experience, and requirements
2. Provide detailed candidate summaries with actionable insights
3. Suggest the best matches and explain why they're good fits
4. Give specific recommendations for next steps
5. Answer questions about specific candidates with complete information

RESPONSE GUIDELINES:
- Be conversational, helpful, and professional
- Always include specific details like names, scores, and contact information when available
- Highlight the best matches and explain their qualifications
- Provide actionable insights for HR decisions
- Use the candidate data provided to give accurate, complete answers
- Format information clearly with bullet points and sections when appropriate

CANDIDATE DATA INTERPRETATION:
- Similarity scores above 80% are excellent matches
- Scores 60-80% are good matches
- Scores below 60% are potential matches
- Resume scores are not used in this system (0% is normal and expected)
- Focus on similarity scores, skills, experience level, and work history for evaluation
- Include all relevant contact and professional information"""
    
    def get_user_prompt_template(self) -> str:
        """Get the user prompt template for response generation."""
        return """User Request: {user_message}

Intent: {intent}

Candidate Search Results:
{context}

Please provide a helpful response that addresses the user's request. Include:
1. A direct answer to their question
2. Specific candidate details (names, scores, contact info)
3. Recommendations based on the search results
4. Next steps or suggestions for the HR professional

If no candidates were found, explain this and suggest alternative search approaches."""
    
    def prepare_input_data(self, **kwargs) -> Dict[str, Any]:
        """Prepare input data for response generation."""
        return {
            'user_message': kwargs.get('user_message', ''),
            'intent': kwargs.get('intent', 'general'),
            'context': kwargs.get('context', 'No candidate data available.')
        }
    
    def process_output(self, output: str, **kwargs) -> str:
        """Process the response generation output."""
        # For response generation, we return the output as-is
        return output.strip()
    
    def _get_fallback_output(self, **kwargs) -> str:
        """Get fallback output when response generation fails."""
        intent = kwargs.get('intent', 'general')
        
        if intent == 'search':
            return "I apologize, but I'm having trouble processing your candidate search right now. Please try rephrasing your query or contact support."
        elif intent == 'info':
            return "I'm unable to retrieve the specific candidate information you requested at the moment. Please try again or contact support."
        else:
            return "Hello! I'm your AI HR assistant. I can help you find candidates, get candidate information, and answer questions about the resume database. How can I assist you today?" 