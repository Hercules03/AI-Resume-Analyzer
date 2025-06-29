"""
Duration extractor for parsing and normalizing duration strings from resumes.
"""
from typing import Type, Dict, Any, List
from .base_extractor import BaseExtractor
from pydantic import BaseModel, Field


class DurationAnalysis(BaseModel):
    """Model for duration analysis."""
    total_months: float = Field(description="Total duration in months")
    total_years: float = Field(description="Total duration in years (calculated)")
    original_text: str = Field(description="Original duration text")
    parsed_components: Dict[str, Any] = Field(default_factory=dict, description="Parsed components (years, months)")
    confidence_score: int = Field(ge=1, le=10, description="Confidence in parsing accuracy (1-10)")
    parsing_notes: str = Field(description="Notes about parsing challenges or assumptions")
    is_current: bool = Field(default=False, description="Whether this is a current/ongoing position")
    formatted_duration: str = Field(description="Human-readable formatted duration")


class DurationExtractor(BaseExtractor):
    """Extractor for parsing duration strings from work experience."""
    
    def get_model(self) -> Type[DurationAnalysis]:
        """Get the Pydantic model for duration analysis."""
        return DurationAnalysis
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for duration analysis."""
        return """
You are an expert at parsing and normalizing duration strings from resumes and work experience.

Parse the following duration text and convert it to standardized months and years.

**Duration Text to Parse:** "{duration_text}"

**Context Information:**
- Start Date: {start_date}
- End Date: {end_date}
- Job Title: {job_title}
- Company: {company}

**Parsing Guidelines:**

1. **Common Duration Formats**:
   - "2 years 3 months" → 27 months
   - "1.5 years" → 18 months
   - "6 months" → 6 months
   - "3 yrs" → 36 months
   - "2y 6m" → 30 months
   - "Jan 2020 - Dec 2022" → Calculate difference
   - "2020-2022" → ~24 months (assume full years)
   - "Present" or "Current" → Mark as ongoing

2. **Edge Cases to Handle**:
   - Approximate durations: "~2 years", "about 18 months"
   - Ranges: "2-3 years" (use midpoint = 2.5 years)
   - Partial information: "Since 2021" (calculate from start to current)
   - Multiple positions: "3 years (2 positions)" (total duration)
   - Contract/temporary: "6 month contract"

3. **Date Calculations**:
   - If start_date and end_date are provided, use them for accuracy
   - If only duration text is available, parse the text
   - Handle "Present", "Current", "Ongoing" as current positions

4. **Confidence Scoring** (1-10):
   - 9-10: Exact dates or very clear duration
   - 7-8: Clear duration text with minor ambiguity
   - 5-6: Some approximation or unclear elements
   - 3-4: Significant ambiguity or assumptions made
   - 1-2: Very unclear, mostly guesswork

5. **Assumptions for Missing Data**:
   - If no duration information: Default to 12 months (1 year)
   - If only year range (2020-2022): Assume full years
   - If approximate ("~2 years"): Use stated duration

**Output Requirements:**
- Convert everything to months (primary unit)
- Calculate years as months/12
- Provide confidence score
- Note any assumptions made
- Format a human-readable duration string

{format_instructions}
"""
    
    def get_input_variables(self) -> List[str]:
        """Get the input variables for the prompt template."""
        return ["duration_text", "start_date", "end_date", "job_title", "company"]
    
    def prepare_input_data(self, duration_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare duration data for analysis."""
        
        if context is None:
            context = {}
        
        return {
            "duration_text": duration_text or "Not specified",
            "start_date": context.get('start_date', 'Not specified'),
            "end_date": context.get('end_date', 'Not specified'),
            "job_title": context.get('job_title', 'Not specified'),
            "company": context.get('company', 'Not specified')
        }
    
    def parse_duration(self, duration_text: str, context: Dict[str, Any] = None, development_mode: bool = False) -> Dict[str, Any]:
        """Parse duration string into standardized format."""
        
        if not duration_text or duration_text.strip() == "":
            # Return default for empty duration
            return {
                'durationanalysis': {
                    'total_months': 12.0,
                    'total_years': 1.0,
                    'original_text': 'Not specified',
                    'parsed_components': {'years': 1, 'months': 0},
                    'confidence_score': 1,
                    'parsing_notes': 'No duration specified, defaulted to 1 year',
                    'is_current': False,
                    'formatted_duration': '1 year (default)'
                }
            }
        
        input_data = self.prepare_input_data(duration_text, context)
        
        # Import llm_service here to avoid circular imports
        from llm_service import llm_service
        
        # Get extractor configuration
        config = self.get_extractor_config()
        
        output = llm_service.extract_with_llm_config(
            self.get_model(),
            self.get_prompt_template(),
            self.get_input_variables(),
            input_data,
            config,
            development_mode
        )
        return self.process_output(output)
    
    def extract(self, extracted_text: str, development_mode: bool = False) -> Dict[str, Any]:
        """
        Standard extract method for compatibility with base extractor.
        Note: This method requires structured input. Use parse_duration() for direct usage.
        """
        # This is a fallback method - ideally use parse_duration()
        input_data = {"text": extracted_text}
        
        # Import llm_service here to avoid circular imports
        from llm_service import llm_service
        
        # Use a simplified prompt for raw text analysis
        simplified_prompt = """
        Parse duration information from the following text:
        
        {text}
        
        {format_instructions}
        """
        
        # Get extractor configuration
        config = self.get_extractor_config()
        
        output = llm_service.extract_with_llm_config(
            self.get_model(),
            simplified_prompt,
            ["text"],
            input_data,
            config,
            development_mode
        )
        return self.process_output(output)
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the duration analysis output."""
        return output
    
    @staticmethod
    def extract_months_fallback(duration_str: str) -> float:
        """
        Fallback duration extraction using simple regex parsing.
        Used when LLM extractor fails.
        """
        if not duration_str:
            return 12.0  # Default to 1 year
        
        duration_lower = duration_str.lower()
        
        # Handle "current" or "present" positions
        if any(keyword in duration_lower for keyword in ['current', 'present', 'ongoing']):
            # For current positions, could calculate from start date if available
            # For now, return a reasonable default
            return 24.0  # Default to 2 years for current positions
        
        # Extract numbers from the string
        import re
        numbers = re.findall(r'\d+\.?\d*', duration_lower)
        
        if not numbers:
            return 12.0  # Default to 1 year if no numbers found
        
        # Get the first number found
        try:
            value = float(numbers[0])
        except ValueError:
            return 12.0
        
        # Determine if it's years or months based on keywords
        if any(keyword in duration_lower for keyword in ['year', 'yr', 'yrs']):
            return value * 12  # Convert years to months
        elif any(keyword in duration_lower for keyword in ['month', 'mon', 'mos']):
            return value
        else:
            # If no clear indicator, assume months if value > 12, otherwise years
            if value > 12:
                return value  # Assume months
            else:
                return value * 12  # Assume years 