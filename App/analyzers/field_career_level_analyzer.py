"""
Field-specific career level analyzer for determining career level within specific domains.
"""
from typing import Type, Dict, Any
from pydantic import BaseModel, Field
from .base_analyzer import BaseAnalyzer


class FieldCareerLevelAnalysis(BaseModel):
    """Model for field-specific career level analysis."""
    target_field: str = Field(description="The target field being analyzed")
    field_specific_experience_years: float = Field(description="Years of experience in the target field")
    total_experience_years: float = Field(description="Total professional experience years")
    field_career_level: str = Field(description="Career level within the target field")
    relevant_experience_percentage: float = Field(description="Percentage of total experience relevant to target field")
    skill_alignment_score: int = Field(description="Score 1-10 for how well skills align with target field")
    career_trajectory: str = Field(description="Analysis of career progression within the field")
    transferable_skills: list[str] = Field(description="Key transferable skills from other experiences")


class FieldCareerLevelAnalyzer(BaseAnalyzer):
    """Analyzer for field-specific career level assessment across all business domains."""
    
    def get_model(self) -> Type[FieldCareerLevelAnalysis]:
        """Get the Pydantic model for field career level analysis."""
        return FieldCareerLevelAnalysis
    
    def get_input_variables(self) -> list[str]:
        """Get the input variables for the prompt template."""
        return ["resume_data", "target_field"]
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for field career level analysis."""
        return """
You are an expert career analyst specializing in evaluating professional experience within specific fields and domains across ALL business sectors and industries.

Analyze the provided resume data to determine the candidate's career level specifically within the target field: **{target_field}**

**Comprehensive Field Coverage:**
This analysis should work for ANY professional field including but not limited to:
- **Technology:** Software Development, Data Science, Cybersecurity, IT Management, Product Management
- **Healthcare:** Nursing, Medical Practice, Healthcare Administration, Pharmaceuticals, Medical Research
- **Finance & Banking:** Investment Banking, Financial Analysis, Accounting, Insurance, Risk Management
- **Marketing & Sales:** Digital Marketing, Sales Management, Brand Management, Market Research, PR
- **Operations & Supply Chain:** Operations Management, Logistics, Manufacturing, Quality Assurance
- **Human Resources:** Talent Acquisition, HR Business Partnering, Compensation & Benefits, Training
- **Legal:** Corporate Law, Litigation, Compliance, Paralegal, Legal Research
- **Education:** Teaching, Educational Administration, Curriculum Development, Training & Development
- **Consulting:** Management Consulting, Strategy, Business Analysis, Process Improvement
- **Government & Public Service:** Public Administration, Policy Development, Regulatory Affairs
- **Non-Profit:** Program Management, Fundraising, Community Outreach, Social Services
- **Real Estate:** Property Management, Real Estate Development, Commercial Real Estate
- **Media & Communications:** Journalism, Content Creation, Public Relations, Broadcasting
- **Retail & Consumer Goods:** Retail Management, Merchandising, Customer Experience
- **Energy & Utilities:** Energy Management, Environmental Services, Utilities Operations
- **Construction & Engineering:** Civil Engineering, Project Management, Architecture
- **And many others...

**Analysis Framework:**

1. **Field Relevance Assessment:**
   - Identify which work experiences are directly relevant to the target field
   - Assess the depth and quality of field-specific responsibilities
   - Evaluate skills, tools, and knowledge alignment with field requirements
   - Consider industry-specific regulations, practices, and standards

2. **Experience Calculation:**
   - Calculate total years of experience directly relevant to the target field
   - Consider part-time, contract, and project-based work proportionally
   - Weight recent experience more heavily than older experience
   - Account for related or adjacent field experience

3. **Career Level Determination:**
   - **Entry Level (0-2 years in field):** Basic responsibilities, learning phase, limited autonomy
   - **Junior Level (2-4 years in field):** Growing independence, standard tasks, some mentoring received
   - **Mid Level (4-7 years in field):** Independent work, project ownership, mentoring others
   - **Senior Level (7-12 years in field):** Complex projects, technical/functional leadership, strategic input
   - **Expert Level (12+ years in field):** Thought leadership, strategic decisions, industry recognition
   - **Career Changer:** Significant experience in other fields but new to target field

4. **Skill Transfer Analysis:**
   - Identify transferable skills from other domains
   - Assess how cross-functional experience adds value
   - Consider industry knowledge that applies across sectors

5. **Quality Assessment:**
   - Evaluate depth vs. breadth of experience
   - Consider organization types, project complexity, and impact scope
   - Assess progression and growth within the field

**Target Field:** {target_field}

**Resume Data:**
```Resume Text
{resume_data}
```

Provide a comprehensive field-specific career level assessment with detailed reasoning that works for ANY professional field or industry.

{format_instructions}
"""
    
    def prepare_input_data(self, resume, **kwargs) -> Dict[str, Any]:
        """Prepare resume data for field-specific analysis."""
        target_field = kwargs.get("target_field", "General Business")
        
        # Prepare comprehensive resume data
        resume_summary = {
            "candidate_name": resume.name,
            "total_career_span": resume.YoE,
            "primary_field": resume.primary_field,
            "work_experiences": [],
            "skills": resume.skills,
            "education": []
        }
        
        # Add work experiences with full context
        for exp in resume.work_experiences:
            exp_data = {
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
            resume_summary["work_experiences"].append(exp_data)
        
        # Add education context
        for edu in resume.educations:
            edu_data = {
                "degree": edu.degree,
                "field_of_study": edu.field_of_study,
                "institution": edu.institution,
                "graduation_date": edu.graduation_date
            }
            resume_summary["education"].append(edu_data)
        
        return {
            "resume_data": resume_summary,
            "target_field": target_field
        }
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the field career level analysis output."""
        return output.get('fieldcareerlevelanalysis', {}) 