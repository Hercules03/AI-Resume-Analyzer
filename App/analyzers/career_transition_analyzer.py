"""
Career transition analyzer for understanding candidate's career journey.
"""
from typing import Type, Dict, Any
from pydantic import BaseModel, Field
from .base_analyzer import BaseAnalyzer


class CareerTransitionAnalysis(BaseModel):
    """Model for career transition analysis."""
    transitions: str = Field(description="Description of career transitions and evolution")
    transition_count: int = Field(description="Number of significant career transitions")
    career_evolution_type: str = Field(description="Type of career evolution: Linear, Lateral, Upward, Career Change, etc.")
    fields_traversed: list[str] = Field(description="List of professional fields/domains traversed")
    transition_reasoning: str = Field(description="Analysis of reasons for transitions")


class CareerTransitionAnalyzer(BaseAnalyzer):
    """Analyzer for career transition patterns."""
    
    def get_model(self) -> Type[CareerTransitionAnalysis]:
        """Get the Pydantic model for career transition analysis."""
        return CareerTransitionAnalysis
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for career transition analysis."""
        return """
You are an expert career analyst specializing in understanding professional career journeys and transitions across all industries and business sectors.

Analyze the work experience data provided to understand the candidate's career transitions and evolution patterns.

Consider the following aspects:

1. **Career Transition Identification:**
   - Identify significant changes in job roles, industries, or professional focus
   - Look for lateral moves, promotions, industry changes, or complete career pivots
   - Consider the progression of responsibilities and seniority levels
   - Analyze transitions across various sectors: Technology, Healthcare, Finance, Education, Manufacturing, Retail, Non-profit, Government, Legal, Marketing, Sales, Operations, Human Resources, etc.

2. **Career Evolution Pattern:**
   - Linear: Steady progression within the same field/industry
   - Lateral: Movement across roles at similar levels to gain breadth
   - Upward: Clear progression in responsibility and seniority
   - Career Change: Significant shift to new field/industry
   - Portfolio: Multiple parallel career tracks or consulting/freelance work
   - Functional: Movement across different business functions (e.g., from operations to marketing)

3. **Professional Fields Analysis:**
   - Identify distinct professional domains/industries across all business sectors
   - Analyze how skills transfer between roles in different industries
   - Understand specialization vs. generalization trends
   - Consider cross-functional experience (finance + operations, marketing + technology, etc.)

4. **Transition Reasoning:**
   - Infer motivations for career changes (growth, specialization, industry shifts, economic factors, etc.)
   - Assess strategic vs. circumstantial transitions
   - Consider market factors, personal development, and industry evolution

Work Experience Data:
```Resume Text
{resume_data}
```

Provide a comprehensive analysis focusing on the career journey narrative and transition patterns across any industry or business function.

{format_instructions}
"""
    
    def prepare_input_data(self, resume, **kwargs) -> Dict[str, Any]:
        """Prepare work experience data for analysis."""
        work_exp_data = []
        
        for exp in resume.work_experiences:
            exp_info = {
                "job_title": exp.job_title,
                "company": exp.company,
                "industry": exp.industry,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "duration": exp.duration,
                "responsibilities": exp.responsibilities,
                "technologies": exp.technologies,
                "employment_type": exp.employment_type
            }
            work_exp_data.append(exp_info)
        
        # Sort by start date for chronological analysis
        work_exp_data.sort(key=lambda x: x.get("start_date") or "", reverse=False)
        
        return {"resume_data": work_exp_data}
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the career transition analysis output."""
        return output.get('careertransitionanalysis', {})