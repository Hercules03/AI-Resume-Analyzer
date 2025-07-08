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

1. **Identify Names in Context:** Scan the user's message for any phrases indicating a person's name.
    **Examples:**
    * **User:** "What's John's email address?"
        **Output:** John
    * **User:** "Tell me about Sarah Johnson."
        **Output:** Sarah Johnson
    * **User:** "I need contact details for Mike Smith."
        **Output:** Mike Smith
    * **User:** "Can you find Mary's resume?"
        **Output:** Mary
    * **User:** "Show me info about Dr. David Williams."
        **Output:** Dr. David Williams
    * **User:** "Email for the candidate named Jennifer."
        **Output:** Jennifer
    * **User:** "Does POON Kwok Tung have an SFC license?"
        **Output:** POON Kwok Tung
    * **User:** "Check JOHN SMITH's SFC license"
        **Output:** JOHN SMITH

2.  **Clean Extracted Names:** If a name is found, process it according to these rules:
    * **Remove Titles:** Eliminate honorifics like "Dr.", "Mr.", "Ms.", "Mrs.", "Prof.", etc.
    * **Remove Possessive Markers:** Remove "'s" at the end of a name.
    * **Retain Full Names:** Keep both first and last names when present.
    * **Handle Single Names:** If only a single name is provided, extract that single name.
    * **Handle Various Capitalizations:** Extract names in ANY capitalization (TitleCase, UPPERCASE, lowercase).

3.  **Assign Confidence Scores:**
    * **High Confidence (0.8-1.0):** The name is clearly identifiable and unambiguous (e.g., "John Smith," "Sarah", "POON Kwok Tung").
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
}}

Examples:
- "What's John's email?" → {{"name": "John", "confidence": 0.9}}
- "Tell me about Dr. Sarah Johnson" → {{"name": "Sarah Johnson", "confidence": 0.95}}
- "Does POON Kwok Tung have an SFC license?" → {{"name": "POON Kwok Tung", "confidence": 0.95}}
- "Check MARY WONG's SFC license" → {{"name": "MARY WONG", "confidence": 0.9}}
- "Find Python developers" → {{"name": "", "confidence": 0.1}}"""
    
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
            # Enhanced fallback: look for names in various capitalizations
            import re
            query = kwargs.get('query', '')
            
            # Enhanced patterns for different name formats
            patterns = [
                # "Do [NAME] have" pattern - most specific for this case
                r"(?:do|does)\s+([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*){1,2})\s+(?:have|hold|got)",
                
                # SFC license specific patterns
                r"(?:does|check|is)\s+([A-Z]+(?:\s+[A-Z]+)*(?:\s+[A-Z]+)*)\s+(?:have|hold|holds?)\s+(?:an?\s+)?sfc\s+licen[sc]e",
                r"(?:sfc\s+licen[sc]e\s+(?:verification\s+)?for|check)\s+([A-Z]+(?:\s+[A-Z]+)*(?:\s+[A-Z]+)*)",
                r"([A-Z]+(?:\s+[A-Z]+)*(?:\s+[A-Z]+)*)\s+sfc\s+licen[sc]ed?",
                r"([A-Z]+(?:\s+[A-Z]+)*(?:\s+[A-Z]+)*)'s?\s+sfc\s+licen[sc]e",
                
                # Standard name patterns (both title case and uppercase)
                r"(?:email of|contact for|about|for)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)",
                r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)'s?\s+(?:email|contact|info|resume)",
                r"(?:who is|tell me about)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)",
                
                # All caps names (like POON Kwok Tung)
                r"(?:email of|contact for|about|for)\s+([A-Z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z][a-z]+)*)",
                r"([A-Z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z][a-z]+)*)'s?\s+(?:email|contact|info|resume)",
                r"(?:who is|tell me about)\s+([A-Z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z][a-z]+)*)",
                
                # Mixed case patterns for Asian names
                r"([A-Z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+)",  # POON Kwok Tung
                r"([A-Z][a-z]+\s+[A-Z]+)",  # Wong MARY
            ]
            
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    extracted = match.group(1).strip()
                    # Additional validation: must contain at least one letter
                    if any(c.isalpha() for c in extracted):
                        return extracted
            
            # Final fallback: look for any sequence of 2-3 capitalized words
            final_pattern = r"\b([A-Z]+(?:\s+[A-Z][a-z]*){1,2})\b"
            match = re.search(final_pattern, query)
            if match:
                extracted = match.group(1).strip()
                # Validate it's likely a name (not common words)
                common_words = {'SFC', 'LICENSE', 'LICENCE', 'CHECK', 'DOES', 'HAVE', 'IS', 'THE', 'AND', 'OR'}
                words = extracted.split()
                if len(words) >= 2 and not any(word.upper() in common_words for word in words):
                    return extracted
            
            return ""
    
    def _get_fallback_output(self, **kwargs) -> str:
        """Get fallback output when name extraction fails."""
        return "" 