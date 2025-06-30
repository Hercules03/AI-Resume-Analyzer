"""
Name extraction specialist for extracting candidate names from queries.
"""
from typing import Type, Optional, Dict, Any
from .base_specialist import BaseSpecialist
from .models import NameExtraction
from pydantic import BaseModel


class NameExtractionSpecialist(BaseSpecialist):
    """Specialist for extracting candidate names from HR queries."""
    
    def get_model(self) -> Optional[Type[BaseModel]]:
        """Get the Pydantic model for name extraction."""
        return NameExtraction
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for name extraction."""
        return """You are a name extraction specialist for HR queries. Your sole task is to accurately identify and extract candidate names from user messages.

**EXTRACTION GUIDELINES:**

1.  **Identify Names in Context:** Scan the user's message for any phrases indicating a person's name.
    * **Examples:**
        * "What's John's email address?"
        * "Tell me about Sarah Johnson."
        * "I need contact details for Mike Smith."
        * "Can you find Mary's resume?"
        * "Show me info about Dr. David Williams."
        * "Email for the candidate named Jennifer."

2.  **Clean Extracted Names:** If a name is found, process it according to these rules:
    * **Remove Titles:** Eliminate honorifics like "Dr.", "Mr.", "Ms.", "Mrs.", "Prof.", etc.
    * **Remove Possessive Markers:** Remove "'s" at the end of a name.
    * **Retain Full Names:** Keep both first and last names when present.
    * **Handle Single Names:** If only a single name is provided, extract that single name.

3.  **Assign Confidence Scores:**
    * **High Confidence (0.8-1.0):** The name is clearly identifiable and unambiguous (e.g., "John Smith," "Sarah").
    * **Medium Confidence (0.5-0.8):** The name is somewhat clear but might have minor ambiguities or require slight inference (e.g., "the candidate named Alex").
    * **Low Confidence (0.0-0.5):** The name is highly uncertain, ambiguous, or no clear name is found.

4.  **Handle No Name Found:** If no candidate name can be confidently extracted, return an **empty string ("")** for the name, and a **Low Confidence** score.

**Your output should be the extracted name (cleaned) and its corresponding confidence score.**"""
    
    def get_user_prompt_template(self) -> str:
        """Get the user prompt template for name extraction.""" 
        return """Extract the candidate name from this HR query:

Query: "{query}"

Provide your analysis in the following JSON format:
{{
    "name": "extracted name or empty string",
    "confidence": 0.95,
    "reasoning": "brief explanation of extraction"
}}

Examples:
- "What's John's email?" → {{"name": "John", "confidence": 0.9, "reasoning": "Clear possessive reference to John"}}
- "Tell me about Dr. Sarah Johnson" → {{"name": "Sarah Johnson", "confidence": 0.95, "reasoning": "Full name with title removed"}}
- "Find Python developers" → {{"name": "", "confidence": 0.1, "reasoning": "No specific candidate name mentioned"}}"""
    
    def process_output(self, output: str, **kwargs) -> str:
        """Process the name extraction output."""
        try:
            import json
            # Try to parse JSON output
            result = json.loads(output.strip())
            
            name = result.get('name', '').strip()
            confidence = float(result.get('confidence', 0.0))
            
            # Additional cleaning
            if name:
                # Remove common titles
                titles = ['dr', 'mr', 'ms', 'mrs', 'miss', 'prof', 'professor', 'dr.', 'mr.', 'ms.', 'mrs.']
                words = name.split()
                cleaned_words = [word for word in words if word.lower().rstrip('.') not in titles]
                
                if cleaned_words:
                    name = " ".join(cleaned_words)
                else:
                    name = ""
            
            # Only return name if confidence is reasonable
            if confidence < 0.3 or len(name) < 2:
                return ""
            
            return name
            
        except (json.JSONDecodeError, ValueError):
            # Fallback: look for capitalized words that might be names
            import re
            query = kwargs.get('query', '')
            
            # Simple pattern matching as fallback
            patterns = [
                r"(?:email of|contact for|about|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'s?\s+(?:email|contact|info|resume)",
                r"(?:who is|tell me about)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, query)
                if match:
                    return match.group(1).strip()
            
            return ""
    
    def _get_fallback_output(self, **kwargs) -> str:
        """Get fallback output when name extraction fails."""
        return "" 