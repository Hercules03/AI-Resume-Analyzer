"""
Field relevance extractor for determining if work experience is relevant to target fields.
"""
from typing import Type, Dict, Any, List
from .base_extractor import BaseExtractor
from pydantic import BaseModel, Field


class FieldRelevanceAnalysis(BaseModel):
    """Model for field relevance analysis."""
    is_relevant: bool = Field(description="Whether the experience is relevant to the target field")
    relevance_score: int = Field(ge=1, le=10, description="Relevance score from 1-10")
    matching_skills: List[str] = Field(default_factory=list, description="Skills that match the target field")
    transferable_skills: List[str] = Field(default_factory=list, description="Skills transferable to the target field")
    relevance_explanation: str = Field(description="Explanation of why experience is or isn't relevant")
    field_overlap_percentage: int = Field(ge=0, le=100, description="Percentage of overlap with target field")


class FieldRelevanceExtractor(BaseExtractor):
    """Extractor for determining field relevance of work experience."""
    
    def get_model(self) -> Type[FieldRelevanceAnalysis]:
        """Get the Pydantic model for field relevance analysis."""
        return FieldRelevanceAnalysis
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for field relevance analysis."""
        return """
You are an expert career analyst specializing in field relevance assessment.

Analyze the provided work experience to determine its relevance to the specified target field.

**Target Field:** {target_field}

**Work Experience to Analyze:**
- Job Title: {job_title}
- Company: {company}
- Responsibilities: {responsibilities}
- Technologies: {technologies}
- Industry: {industry}

**Analysis Framework:**

1. **Direct Relevance**: Does this experience directly involve work in the target field?
   - Same job function/role type
   - Same industry sector
   - Same core responsibilities

2. **Skill Relevance**: What skills from this experience apply to the target field?
   - Technical skills that transfer
   - Domain knowledge that applies
   - Methodologies and approaches used

3. **Transferable Experience**: What aspects could be valuable in the target field?
   - Problem-solving approaches
   - Industry insights
   - Cross-functional collaboration
   - Leadership/management experience

4. **Field Overlap Assessment**: How much does this experience overlap with the target field?
   - 80-100%: Highly relevant, same or very similar field
   - 60-79%: Quite relevant, significant skill/knowledge transfer
   - 40-59%: Moderately relevant, some transferable elements
   - 20-39%: Somewhat relevant, limited but useful transfer
   - 0-19%: Minimally relevant, little direct application

**Scoring Guidelines:**
- **Relevance Score (1-10)**:
  - 9-10: Highly relevant, direct field match
  - 7-8: Very relevant, strong skill/knowledge transfer
  - 5-6: Moderately relevant, good transferable elements
  - 3-4: Somewhat relevant, limited but useful aspects
  - 1-2: Minimally relevant, little connection

Provide a thorough analysis considering both direct relevance and transferable value.

{format_instructions}
"""
    
    def get_input_variables(self) -> List[str]:
        """Get the input variables for the prompt template."""
        return ["target_field", "job_title", "company", "responsibilities", "technologies", "industry"]
    
    def prepare_input_data(self, experience: Dict[str, Any], target_field: str) -> Dict[str, Any]:
        """Prepare work experience data for field relevance analysis."""
        
        # Format responsibilities as a readable list
        responsibilities = experience.get('responsibilities', [])
        if isinstance(responsibilities, list):
            responsibilities_text = "\n".join([f"  - {resp}" for resp in responsibilities])
        else:
            responsibilities_text = str(responsibilities) if responsibilities else "Not specified"
        
        # Format technologies as a readable list
        technologies = experience.get('technologies', [])
        if isinstance(technologies, list):
            technologies_text = ", ".join(technologies)
        else:
            technologies_text = str(technologies) if technologies else "Not specified"
        
        return {
            "target_field": target_field,
            "job_title": experience.get('job_title', 'Not specified'),
            "company": experience.get('company', 'Not specified'),
            "responsibilities": responsibilities_text,
            "technologies": technologies_text,
            "industry": experience.get('industry', 'Not specified')
        }
    
    def analyze_experience_relevance(self, experience: Dict[str, Any], target_field: str, development_mode: bool = False) -> Dict[str, Any]:
        """Analyze if work experience is relevant to target field."""
        
        input_data = self.prepare_input_data(experience, target_field)
        
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
        Note: This method requires structured input. Use analyze_experience_relevance() for direct usage.
        """
        # This is a fallback method - ideally use analyze_experience_relevance()
        input_data = {"text": extracted_text}
        
        # Import llm_service here to avoid circular imports
        from llm_service import llm_service
        
        # Use a simplified prompt for raw text analysis
        simplified_prompt = """
        Analyze the following text to determine field relevance:
        
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
        """Process the field relevance analysis output."""
        return output 