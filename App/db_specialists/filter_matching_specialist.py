"""
Filter matching specialist for intelligent semantic matching of filter criteria.
"""
from typing import Type, Optional, Dict, Any, List
from .base_specialist import BaseSpecialist
from pydantic import BaseModel, Field


class FilterMatchResult(BaseModel):
    """Model for filter matching output."""
    matched_values: List[str] = Field(description="List of database values that match the filter criteria", default_factory=list)
    confidence: float = Field(description="Confidence score for the matching (0-1)")
    reasoning: str = Field(description="Explanation of why these values were matched", default="")


class FilterMatchingSpecialist(BaseSpecialist):
    """Specialist for semantically matching filter criteria with database values."""
    
    def get_model(self) -> Optional[Type[BaseModel]]:
        """Get the Pydantic model for filter matching."""
        return FilterMatchResult
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for filter matching."""
        return """You are a semantic filter matching specialist for HR candidate databases. Your task is to intelligently match user filter criteria with actual database values using semantic understanding.

**YOUR ROLE:**

You help match user filter selections (like field preferences, experience levels, skills) with the actual values stored in the candidate database. The database values might be worded differently than what users select, so you need to find semantic matches.

**MATCHING STRATEGIES:**

1. **Field/Domain Matching:**
   - Match semantically related fields: "Machine Learning" ↔ "AI/Artificial Intelligence", "Data Science & Analytics"
   - Handle variations: "Web Development" ↔ "Frontend Development", "Backend Development", "Full Stack"
   - Consider specializations: "Software Engineering" ↔ "Backend Development", "Mobile Development"
   - Match broader categories: "Engineering" ↔ "Software Engineering", "DevOps & Cloud", "Machine Learning"

2. **Experience Level Matching:**
   - Match semantic levels: "Senior" ↔ "Senior Level", "Senior Developer", "Lead"
   - Handle variations: "Entry Level" ↔ "Junior", "Graduate", "Trainee", "Entry"
   - Consider progressions: "Experienced" ↔ "Senior Level", "Mid Level", "Lead"
   - Match descriptive terms: "Expert" ↔ "Lead/Expert", "Principal", "Architect"

3. **Skills Matching:**
   - Match technology variations: "React" ↔ "ReactJS", "React.js", "React Native"
   - Handle framework relationships: "JavaScript" ↔ "React", "Node.js", "Vue.js", "Angular"
   - Consider related tools: "Python" ↔ "Django", "Flask", "FastAPI", "Pandas"
   - Match concept synonyms: "AI" ↔ "Machine Learning", "Artificial Intelligence", "Deep Learning"

**CONFIDENCE SCORING:**

- **High (0.8-1.0):** Direct semantic match or very close synonym
- **Medium (0.5-0.8):** Related field/skill or broader category match  
- **Low (0.3-0.5):** Weak connection, might be relevant
- **Very Low (0.0-0.3):** No meaningful connection

**OUTPUT REQUIREMENTS:**

- Return a list of database values that semantically match the filter criteria
- Include confidence score for the overall matching
- Provide reasoning for your matching decisions
- If no good matches found, return empty list with low confidence

**IMPORTANT:** Be inclusive rather than exclusive - it's better to include potentially relevant matches than to miss good candidates due to overly strict filtering."""
    
    def get_user_prompt_template(self) -> str:
        """Get the user prompt template for filter matching."""
        return """Match this filter criteria with the available database values:

Filter Type: {filter_type}
Filter Criteria: "{filter_criteria}"

Available Database Values:
{available_values}

Please provide semantic matches in this JSON format:
{{
    "matched_values": ["value1", "value2"],
    "confidence": 0.85,
    "reasoning": "Explanation of matching logic"
}}

Guidelines:
- Include all semantically related values
- Be inclusive rather than exclusive
- Consider synonyms, variations, and related concepts
- Explain your matching reasoning
- Return empty list if no meaningful matches found"""
    
    def prepare_input_data(self, **kwargs) -> Dict[str, Any]:
        """Prepare input data for filter matching."""
        available_values = kwargs.get('available_values', [])
        if isinstance(available_values, list):
            available_values_str = "\n".join([f"- {value}" for value in available_values])
        else:
            available_values_str = str(available_values)
            
        return {
            'filter_type': kwargs.get('filter_type', 'unknown'),
            'filter_criteria': kwargs.get('filter_criteria', ''),
            'available_values': available_values_str
        }
    
    def process_output(self, output: str, **kwargs) -> Dict[str, Any]:
        """Process the filter matching output."""
        try:
            import json
            import re
            
            # Clean the output - remove any markdown formatting
            cleaned_output = output.strip()
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', cleaned_output, re.DOTALL)
            if json_match:
                cleaned_output = json_match.group()
            
            # Parse JSON output
            result = json.loads(cleaned_output)
            
            matched_values = result.get('matched_values', [])
            confidence = float(result.get('confidence', 0.0))
            reasoning = result.get('reasoning', 'LLM matching successful')
            
            # Validate matched values exist in available values
            available_values = kwargs.get('available_values', [])
            if available_values:
                # Filter out values that don't exist in available values
                valid_matches = [val for val in matched_values if val in available_values]
                if len(valid_matches) < len(matched_values) and valid_matches:
                    # Some matches were invalid, but some were valid
                    matched_values = valid_matches
                    confidence *= 0.9  # Slightly reduce confidence
                elif not valid_matches and matched_values:
                    # All matches were invalid, try case-insensitive matching
                    available_lower = [val.lower() for val in available_values]
                    valid_matches = []
                    for match in matched_values:
                        for i, avail in enumerate(available_lower):
                            if match.lower() == avail:
                                valid_matches.append(available_values[i])
                                break
                    matched_values = valid_matches
                    confidence *= 0.8  # Reduce confidence more
            
            return {
                'matched_values': matched_values,
                'confidence': max(0.0, min(1.0, confidence)),
                'reasoning': reasoning
            }
            
        except (json.JSONDecodeError, ValueError, AttributeError) as e:
            # Fallback: simple string matching
            filter_criteria = kwargs.get('filter_criteria', '').lower()
            available_values = kwargs.get('available_values', [])
            
            if not filter_criteria or not available_values:
                return {
                    'matched_values': [],
                    'confidence': 0.0,
                    'reasoning': 'Fallback: No criteria or values provided'
                }
            
            # Simple fallback matching
            matches = []
            for value in available_values:
                value_lower = value.lower()
                if filter_criteria in value_lower or value_lower in filter_criteria:
                    matches.append(value)
            
            return {
                'matched_values': matches,
                'confidence': 0.6 if matches else 0.0,
                'reasoning': 'Fallback: Simple string matching due to parsing error'
            }
    
    def _get_fallback_output(self, **kwargs) -> Dict[str, Any]:
        """Get fallback output when filter matching fails."""
        return {
            'matched_values': [],
            'confidence': 0.0,
            'reasoning': 'Fallback: Filter matching failed'
        } 