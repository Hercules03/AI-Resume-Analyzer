"""
Updated intent analysis specialist that includes SFC license checking.
"""
from typing import Type, Optional, Dict, Any
from .base_specialist import BaseSpecialist
from .models import IntentAnalysis, IntentType
from pydantic import BaseModel


class IntentSpecialist(BaseSpecialist):
    """Specialist for analyzing user intent in HR queries including SFC license checking."""
    
    def get_model(self) -> Optional[Type[BaseModel]]:
        """Get the Pydantic model for intent analysis."""
        return IntentAnalysis
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for intent analysis."""
        return """You are an intent classifier for an HR candidate search system. Your task is to analyze user messages and accurately determine their intent.

**INTENT CATEGORIES:**

1. **search:** The user wants to find candidates based on specific criteria.
   * **Keywords/Phrases:** "find," "need," "show me," "looking for," "search for," "candidates with," "developers," "engineers," "specialists."
   * **Examples:**
     * "Find Python developers."
     * "I need ML engineers with 5+ years experience."
     * "Show me senior frontend developers in California."
     * "Looking for data scientists."

2. **info:** The user is asking for specific details about one or more existing candidates.
   * **Keywords/Phrases:** "what's," "tell me about," "contact details," "show me," "resume," "email address," "phone number," "experience of," "education," "background," "details," "qualifications."
   * **Pattern:** Usually contains a person's name AND asks for specific information about them.
   * **Examples:**
     * "What's John's email address?"
     * "Tell me about Sarah Johnson's experience."
     * "What is the education background of John Doe?"
     * "Contact details for Mike Smith."
     * "Show me Mary's resume."

3. **sfc_license:** The user wants to verify if someone holds a valid SFC (Securities and Futures Commission) license.
   * **Keywords/Phrases:** "SFC license," "SFC licensed," "SFC registration," "Securities and Futures Commission," "license check," "license verification," "licensed by SFC."
   * **Pattern:** Usually contains a person's name AND asks about SFC license status.
   * **Examples:**
     * "Does Peter Chan hold a valid SFC license?"
     * "Check John Smith's SFC license"
     * "Is Mary Wong SFC licensed?"
     * "Verify David Lee's SFC registration"
     * "Does this candidate have an SFC license?"
     * "SFC license check for Tom Wilson"

4. **general:** The user's message is a greeting, a general question about the system, or a request for help.
   * **Keywords/Phrases:** "hello," "hi," "how does this work," "what can you do," "help," "features," "what can you help me with."
   * **Examples:**
     * "Hello."
     * "How does this system work?"
     * "What can you help me with?"

**CLASSIFICATION PRIORITY:**
1. Check for SFC license queries first (most specific)
2. Then check for candidate search queries
3. Then check for candidate info queries  
4. Finally default to general if none match

**YOUR OUTPUT REQUIREMENTS:**
* **Classify the intent** as one of the categories above ("search", "info", "sfc_license", or "general").
* **Provide a confidence score** for your classification (a number between 0.0 and 1.0, where 1.0 is highly confident).

**Be precise and consistent in your classifications.**

**CRITICAL: You must ALWAYS respond with valid JSON format only. Do not include any additional text, explanations, or markdown formatting. Return only the JSON object as specified below.**"""
    
    def get_user_prompt_template(self) -> str:
        """Get the user prompt template for intent analysis."""
        return """Analyze this user message and classify the intent:

User Message: "{message}"

You must respond with ONLY valid JSON in exactly this format (no other text):

{{
    "intent": "search",
    "confidence": 0.95
}}

Where intent is one of: "search", "info", "sfc_license", or "general"
And confidence is a number between 0.0 and 1.0

Pay special attention to SFC license-related queries which should be classified as "sfc_license"."""
    
    def process_output(self, output: str, **kwargs) -> Dict[str, Any]:
        """Process the intent analysis output."""
        try:
            import json
            import re
            
            # Clean the output - remove any markdown formatting or extra text
            cleaned_output = output.strip()
            
            # Try to extract JSON from the response using regex if needed
            json_match = re.search(r'\{[^}]*\}', cleaned_output)
            if json_match:
                cleaned_output = json_match.group()
            
            # Parse JSON output
            result = json.loads(cleaned_output)
            
            # Validate and clean the result
            intent = result.get('intent', 'general').lower().strip()
            if intent not in ['search', 'info', 'general', 'sfc_license']:
                intent = 'general'
            
            confidence = float(result.get('confidence', 0.8))
            confidence = max(0.0, min(1.0, confidence))  # Clamp between 0 and 1
            
            return {
                'intent': intent,
                'confidence': confidence,
                'search_query': kwargs.get('message', '') if intent in ['search', 'info', 'sfc_license'] else '',
                'reasoning': 'LLM classification successful'
            }
            
        except (json.JSONDecodeError, ValueError, AttributeError) as e:
            # Fallback parsing if JSON fails
            message_lower = kwargs.get('message', '').lower().strip()
            
            # Check for SFC license intent first (most specific)
            sfc_keywords = ['sfc license', 'sfc licensed', 'sfc registration', 'securities and futures commission', 'license check', 'license verification']
            if any(keyword in message_lower for keyword in sfc_keywords):
                intent = 'sfc_license'
            # Check for search intent
            elif any(word in message_lower for word in ['find', 'search', 'looking', 'need', 'want', 'show me candidates', 'developer', 'developers', 'engineer', 'engineers', 'candidate', 'candidates', 'hire', 'hiring', 'recruit', 'recruiting']):
                intent = 'search'
            # Check for info intent - person name + specific info request
            elif any(word in message_lower for word in ['email', 'contact', 'about', 'tell me about', 'education', 'background', 'experience', 'qualifications', 'resume', 'details']) and any(name_indicator in message_lower for name_indicator in ['\'s', 'ronald', 'john', 'sarah', 'mike', 'mary', 'david', 'lam']):
                intent = 'info'
            # Check general patterns
            elif any(word in message_lower for word in ['hello', 'hi', 'help', 'how does', 'what can you']):
                intent = 'general'
            else:
                intent = 'general'
            
            return {
                'intent': intent,
                'confidence': 0.7,
                'search_query': kwargs.get('message', '') if intent in ['search', 'info', 'sfc_license'] else '',
                'reasoning': 'Fallback classification due to parsing error'
            }
    
    def _get_fallback_output(self, **kwargs) -> Dict[str, Any]:
        """Get fallback output when intent analysis fails."""
        return {
            'intent': 'general',
            'confidence': 0.5,
            'search_query': '',
            'reasoning': 'Fallback due to analysis failure'
        }