"""
Career transition extractor for analyzing career progression and field changes.
"""
from typing import Type, Dict, Any, List
from .base_extractor import BaseExtractor
from models import CareerProgressionAnalysis


class CareerTransitionExtractor(BaseExtractor):
    """Extractor for career transition and progression analysis."""
    
    def get_model(self) -> Type[CareerProgressionAnalysis]:
        """Get the Pydantic model for career transition extraction."""
        return CareerProgressionAnalysis
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for career transition extraction."""
        return """
You are an expert career analyst specializing in career progression patterns and professional transitions.

Analyze the work experience history to understand the candidate's career journey, field transitions, and professional development.

For each work experience entry provided, analyze:

1. **Career Field Classification**: Determine the professional field for each role:
   - Data Science & Analytics
   - Software Engineering/Development  
   - Product Management
   - Business/Sales/Marketing
   - Finance & Accounting
   - Operations & Supply Chain
   - Human Resources
   - Design & Creative
   - Healthcare & Medical
   - Education & Training
   - Legal & Compliance
   - Consulting
   - Management & Leadership
   - Research & Development
   - Other (specify)

2. **Career Transitions**: Identify transitions between different fields:
   - **Transition Type**: 
     * "vertical" (promotion within same field)
     * "horizontal" (same level, different company/role in same field)  
     * "pivot" (complete field change)
     * "lateral" (related field with skill overlap)
   - **Skill Overlap**: What transferable skills enabled the transition
   - **Rationale**: Likely reasons (career growth, better opportunities, industry shift, etc.)

3. **Career Path Analysis**:
   - **Career Path Type**:
     * "linear" (steady progression in one field)
     * "zigzag" (multiple field changes with some inconsistency)
     * "specialized" (deep expertise in one area)
     * "diverse" (intentional multi-field experience)
     * "early_career" (still exploring, limited experience)
   
   - **Career Coherence Score** (1-10): How focused and coherent is the career path?
     * 8-10: Very focused, clear specialization
     * 6-7: Mostly focused with some strategic diversification
     * 4-5: Mixed focus, some scattered experience
     * 1-3: Highly scattered, unclear direction

   - **Growth Trajectory**:
     * "ascending" (clear upward progression in responsibility/seniority)
     * "lateral" (same level moves for experience/skills)
     * "mixed" (combination of upward and lateral moves)
     * "unclear" (insufficient information or inconsistent progression)

4. **Strengths & Concerns Assessment**:
   - **Strengths from Transitions**: What positive attributes come from career changes
   - **Potential Concerns**: Any red flags from transition patterns (job hopping, lack of focus, etc.)

5. **Field Expertise Areas**: What specific domains has the candidate built expertise in

Return your analysis as a JSON object following the provided schema.

**Work Experience Data:**
{text}

{format_instructions}
"""
    
    def get_input_variables(self) -> List[str]:
        """Get the input variables for the prompt template."""
        return ["text"]
    
    def prepare_input_data(self, work_experiences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare work experience data for analysis."""
        # Convert work experience objects to readable text
        experience_text = []
        
        for i, exp in enumerate(work_experiences, 1):
            exp_text = f"Experience {i}:\n"
            exp_text += f"  Job Title: {exp.get('job_title', 'Not specified')}\n"
            exp_text += f"  Company: {exp.get('company', 'Not specified')}\n"
            exp_text += f"  Duration: {exp.get('duration', 'Not specified')}\n"
            exp_text += f"  Start Date: {exp.get('start_date', 'Not specified')}\n"
            exp_text += f"  End Date: {exp.get('end_date', 'Not specified')}\n"
            exp_text += f"  Location: {exp.get('location', 'Not specified')}\n"
            exp_text += f"  Industry: {exp.get('industry', 'Not specified')}\n"
            exp_text += f"  Employment Type: {exp.get('employment_type', 'Not specified')}\n"
            
            if exp.get('responsibilities'):
                exp_text += f"  Responsibilities:\n"
                for resp in exp['responsibilities']:
                    exp_text += f"    - {resp}\n"
            
            if exp.get('technologies'):
                exp_text += f"  Technologies: {', '.join(exp['technologies'])}\n"
            
            exp_text += "\n"
            experience_text.append(exp_text)
        
        return {"text": "\n".join(experience_text)}
    
    def extract_from_work_experiences(self, work_experiences: List[Dict[str, Any]], development_mode: bool = False) -> Dict[str, Any]:
        """Extract career transition analysis from work experience data."""
        if not work_experiences:
            # Return default analysis for no experience
            return {
                'careerprogressionanalysis': {
                    'transitions': [],
                    'career_path_type': 'early_career',
                    'primary_career_field': 'Unknown',
                    'career_coherence_score': 5,
                    'growth_trajectory': 'unclear',
                    'field_expertise_areas': [],
                    'transition_summary': 'No work experience found for analysis.',
                    'strengths_from_transitions': [],
                    'potential_concerns': ['No work experience to evaluate']
                }
            }
        
        input_data = self.prepare_input_data(work_experiences)
        
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
        Note: This method parses the full resume text to find work experience.
        For more accurate results, use extract_from_work_experiences() directly.
        """
        # This is a fallback method - ideally use extract_from_work_experiences()
        input_data = {"text": extracted_text}
        
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
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the career transition analysis output."""
        return output 