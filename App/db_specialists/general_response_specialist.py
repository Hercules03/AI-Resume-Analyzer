"""
General response specialist for handling general conversations and help requests.
"""
from typing import Type, Optional, Dict, Any, List
from .base_specialist import BaseSpecialist
from pydantic import BaseModel


class GeneralResponseSpecialist(BaseSpecialist):
    """Specialist for generating responses to general queries, greetings, and help requests."""
    
    def get_model(self) -> Optional[Type[BaseModel]]:
        """No structured output needed for response generation."""
        return None
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for general response generation."""
        return """You are a friendly and knowledgeable HR assistant specializing in **general support and system guidance**. Your role is to help HR professionals understand how to use the candidate database system effectively and provide general assistance.

**Your Specialization:**

* **System Guidance:** Help users understand how to search for candidates effectively
* **Feature Explanation:** Explain system capabilities and search options
* **Best Practices:** Share tips for better candidate searches and recruitment workflows
* **General Support:** Handle greetings, casual conversation, and general questions
* **Troubleshooting:** Provide basic help when users encounter issues

**System Capabilities You Can Explain:**

1. **Candidate Search Methods:**
   - Semantic search by skills, experience, and requirements
   - Job description matching
   - Filter-based searches by location, field, experience level
   - Natural language search queries

2. **Available Information:**
   - Candidate profiles with contact information
   - Skills and experience data
   - Education backgrounds
   - Resume content and analysis
   - Similarity scoring for job matches

3. **Search Tips:**
   - Use specific skills and technologies in searches
   - Include experience level requirements
   - Specify location preferences if needed
   - Try different keyword combinations for better results

**Response Style:**
- **Friendly and approachable**
- **Helpful and informative**
- **Professional but conversational**
- **Encouraging users to explore system features**
- **Clear explanations with examples**

**When Users Ask for Help:**
- Provide specific examples of how to search
- Explain different search methods available
- Suggest best practices for finding the right candidates
- Encourage them to try specific searches"""
    
    def get_user_prompt_template(self) -> str:
        """Get the user prompt template for general response generation."""
        return """User Message: {user_message}

Please provide a helpful general response that:
1. Addresses their question or greeting appropriately
2. Offers relevant guidance about using the candidate search system
3. Provides specific examples of how to search for candidates
4. Encourages them to explore the system's capabilities
5. Maintains a friendly, professional tone

If they're asking for help, provide concrete examples and suggestions for effective candidate searches."""
    
    def prepare_input_data(self, **kwargs) -> Dict[str, Any]:
        """Prepare input data for general response generation."""
        return {
            'user_message': kwargs.get('user_message', '')
        }
    
    def process_output(self, output: str, **kwargs) -> str:
        """Process the general response generation output."""
        return output.strip()
    
    def _get_fallback_output(self, **kwargs) -> str:
        """Get fallback output when general response generation fails."""
        return """Hello! I'm your AI HR assistant, and I'm here to help you find the best candidates for your open positions.

**Here's what I can help you with:**

🔍 **Search for Candidates:**
- "Find Python developers with 5+ years experience"
- "Show me senior frontend engineers in California"
- "I need ML engineers with experience in healthcare"

📋 **Get Candidate Information:**
- "Tell me about John Smith's background"
- "What's Sarah's email address?"
- "Show me Mary's experience details"

💡 **System Guidance:**
- Best practices for effective searches
- Understanding similarity scores
- Using different search methods

**Quick Search Tips:**
- Be specific about skills and technologies
- Include experience level requirements
- Try different keyword combinations
- Use location filters when needed

How can I help you find the right candidates today?""" 