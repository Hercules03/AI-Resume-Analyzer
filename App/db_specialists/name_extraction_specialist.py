"""
Improved Name extraction specialist for extracting candidate names from queries.
"""
from typing import Type, Optional, Dict, Any
from .base_specialist import BaseSpecialist
from .models import NameExtraction
from pydantic import BaseModel
import re


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
    * **Direct mentions:** "John Smith", "Sarah Johnson", "Hercules Keung"
    * **Possessive references:** "John's email", "Sarah's experience", "Hercules Keung's first job"
    * **Explicit references:** "Tell me about Dr. David Williams", "Contact info for Jennifer"
    * **Contextual mentions:** "the candidate named Alex", "employee called Mike"

2.  **Clean Extracted Names:** If a name is found, process it according to these rules:
    * **Remove Titles:** Eliminate honorifics like "Dr.", "Mr.", "Ms.", "Mrs.", "Prof.", etc.
    * **Remove Possessive Markers:** Remove "'s" at the end of a name.
    * **Retain Full Names:** Keep both first and last names when present.
    * **Handle Single Names:** If only a single name is provided, extract that single name.
    * **Handle Asian Names:** Be aware of different name formats (e.g., "Hercules Keung", "Lee Ho Pan, Benny")
    * **Handle Special Characters:** Keep names with special characters intact (e.g., "Ronald 林瑋翔")

3.  **Assign Confidence Scores:**
    * **High Confidence (0.8-1.0):** The name is clearly identifiable and unambiguous
    * **Medium Confidence (0.5-0.8):** The name is somewhat clear but might have minor ambiguities
    * **Low Confidence (0.0-0.5):** The name is highly uncertain, ambiguous, or no clear name is found

4.  **Handle No Name Found:** If no candidate name can be confidently extracted, return an **empty string ("")** for the name, and a **low confidence score**.

**IMPORTANT PATTERNS TO RECOGNIZE:**
- "What's [Name]'s [something]?" → Extract [Name]
- "Tell me about [Name]" → Extract [Name]  
- "[Name]'s first job" → Extract [Name]
- "Contact details for [Name]" → Extract [Name]
- "Show me [Name]'s resume" → Extract [Name]
- "I want to know about [Name]" → Extract [Name]

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
- "Hercules Keung's first job" → {{"name": "Hercules Keung", "confidence": 0.95, "reasoning": "Clear possessive reference to full name"}}
- "I want to know about Ronald 林瑋翔" → {{"name": "Ronald 林瑋翔", "confidence": 0.9, "reasoning": "Full name with Chinese characters"}}
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
                name = self._clean_extracted_name(name)
            
            # Only return name if confidence is reasonable
            if confidence < 0.3 or len(name) < 2:
                return ""
            
            return name
            
        except (json.JSONDecodeError, ValueError):
            # Fallback: use regex patterns to extract names
            return self._fallback_name_extraction(kwargs.get('query', ''))
    
    def _clean_extracted_name(self, name: str) -> str:
        """Clean the extracted name by removing titles and possessive markers."""
        if not name:
            return ""
        
        # Remove possessive 's
        name = re.sub(r"'s$", "", name.strip())
        
        # Remove common titles (case insensitive)
        titles = ['dr', 'mr', 'ms', 'mrs', 'miss', 'prof', 'professor', 'dr.', 'mr.', 'ms.', 'mrs.']
        words = name.split()
        
        # Remove title words
        cleaned_words = []
        for word in words:
            if word.lower().rstrip('.') not in titles:
                cleaned_words.append(word)
        
        if cleaned_words:
            return " ".join(cleaned_words).strip()
        
        return ""
    
    def _fallback_name_extraction(self, query: str) -> str:
        """Fallback method using regex patterns to extract names."""
        if not query:
            return ""
        
        # Enhanced patterns for name extraction
        patterns = [
            # Possessive patterns
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[^\s,]+)*)'s?\s+(?:email|contact|info|resume|experience|job|first|background|details)",
            # About/tell me patterns  
            r"(?:about|tell me about)\s+(?:Dr\.?\s+|Mr\.?\s+|Ms\.?\s+|Mrs\.?\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[^\s,]+)*)",
            # For/contact patterns
            r"(?:email of|contact for|for|info for)\s+(?:Dr\.?\s+|Mr\.?\s+|Ms\.?\s+|Mrs\.?\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[^\s,]+)*)",
            # Want to know about patterns
            r"(?:want to know about|know about)\s+(?:Dr\.?\s+|Mr\.?\s+|Ms\.?\s+|Mrs\.?\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[^\s,]+)*)",
            # General capitalized names (be more careful with this one)
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                # Take the first match and clean it
                name = matches[0].strip()
                cleaned_name = self._clean_extracted_name(name)
                if cleaned_name and len(cleaned_name) >= 2:
                    return cleaned_name
        
        return ""
    
    def _get_fallback_output(self, **kwargs) -> str:
        """Get fallback output when name extraction fails."""
        return ""