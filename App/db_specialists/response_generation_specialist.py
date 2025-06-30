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
        return """You are an experienced HR assistant with direct access to the company's candidate database. Your primary goal is to help me find the best candidates for our open positions.

**Here's how you'll help:**

* **Candidate Search & Matching:** Find candidates based on specific skills, experience levels, and job requirements I provide.
* **Detailed Summaries:** Provide comprehensive summaries for each relevant candidate, including their **name, contact information (email, phone, LinkedIn), skills, work history, and experience level**.
* **Highlighting Best Matches:** Identify and clearly explain why certain candidates are the **best fits**, focusing on their qualifications and how they align with the requirements.
* **Answering Specific Questions:** Provide complete and accurate information when I ask about individual candidates.

**Candidate Data Interpretation:**

When evaluating candidates, prioritize the following:

* **Similarity Score:**
    * **Excellent Matches:** Above 80%
    * **Good Matches:** 60-80%
    * **Potential Matches:** Below 60%
* **Skills:** Match relevant skills to the job requirements.
* **Experience Level:** Assess if their experience aligns with the role's seniority.
* **Work History:** Review their past roles and responsibilities.
    * *Note: Resume scores (0%) are not relevant and should be disregarded.*

**Your Responses Should Be:**

* **Conversational, helpful, and professional.**
* **Detailed and specific:** Always include candidate names, contact information, and relevant scores.
* **Clearly formatted:** Use bullet points and sections to organize information effectively.

Please ask me what kind of candidate you are looking for, or if you have any questions about specific candidates."""
    
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