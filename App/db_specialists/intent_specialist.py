"""
Intent analysis specialist for classifying user intents.
"""
from typing import Type, Optional, Dict, Any
from .base_specialist import BaseSpecialist
from .models import IntentAnalysis, IntentType
from pydantic import BaseModel


class IntentSpecialist(BaseSpecialist):
    """Specialist for analyzing user intent in HR queries."""
    
    def get_model(self) -> Optional[Type[BaseModel]]:
        """Get the Pydantic model for intent analysis."""
        return IntentAnalysis
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for intent analysis."""
        return """You are an intent classifier for an HR candidate search system.
Analyze the user's message and determine their intent with high accuracy.

INTENT CATEGORIES:

1. "search" - Finding candidates based on skills, experience, requirements
   Examples: 
   - "Find Python developers"
   - "I need ML engineers with 5+ years experience"
   - "Show me senior frontend developers in California"
   - "Looking for data scientists"

2. "info" - Asking for specific information about existing candidates
   Examples: 
   - "What's John's email address?"
   - "Tell me about Sarah Johnson's experience"
   - "Contact details for Mike Smith"
   - "Show me Mary's resume"

3. "general" - General questions, greetings, help requests
   Examples: 
   - "Hello", "Hi there"
   - "How does this system work?"
   - "What can you help me with?"
   - "Help me understand the features"

ANALYSIS REQUIREMENTS:
- Classify the intent accurately
- Provide confidence score (0.0-1.0)
- Extract search terms for search/info intents
- Give brief reasoning for your classification

Be precise and consistent in your classifications."""
    
    def get_user_prompt_template(self) -> str:
        """Get the user prompt template for intent analysis."""
        return """Analyze this user message and classify the intent:

User Message: "{message}"

Provide your analysis in the following JSON format:
{{
    "intent": "search|info|general",
    "confidence": 0.95,
    "search_query": "extracted terms if applicable",
    "reasoning": "brief explanation of classification"
}}"""
    
    def process_output(self, output: str, **kwargs) -> Dict[str, Any]:
        """Process the intent analysis output."""
        try:
            import json
            # Try to parse JSON output
            result = json.loads(output.strip())
            
            # Validate and clean the result
            intent = result.get('intent', 'general').lower()
            if intent not in ['search', 'info', 'general']:
                intent = 'general'
            
            confidence = float(result.get('confidence', 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp between 0 and 1
            
            search_query = result.get('search_query', '')
            if intent in ['search', 'info'] and not search_query:
                search_query = kwargs.get('message', '')
            
            return {
                'intent': intent,
                'confidence': confidence,
                'search_query': search_query,
                'reasoning': result.get('reasoning', '')
            }
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback parsing if JSON fails
            output_lower = output.lower().strip()
            if any(word in output_lower for word in ['find', 'search', 'looking', 'need', 'show me']):
                intent = 'search'
            elif any(word in output_lower for word in ['email', 'contact', 'about', 'tell me']):
                intent = 'info'
            else:
                intent = 'general'
            
            return {
                'intent': intent,
                'confidence': 0.7,
                'search_query': kwargs.get('message', '') if intent in ['search', 'info'] else '',
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