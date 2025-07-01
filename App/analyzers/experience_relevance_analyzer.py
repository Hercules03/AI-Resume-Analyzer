"""
Experience relevance analyzer for determining how relevant work experience is to a target field.
"""
from typing import Type, Dict, Any
from pydantic import BaseModel, Field
from .base_analyzer import BaseAnalyzer


class ExperienceRelevanceAnalysis(BaseModel):
    """Model for experience relevance analysis."""
    relevance_score: int = Field(description="Relevance score from 1-10 for the experience to target field")
    relevance_category: str = Field(description="Highly Relevant, Moderately Relevant, Partially Relevant, or Not Relevant")
    relevance_reasoning: str = Field(description="Detailed explanation of relevance assessment")
    transferable_skills: list[str] = Field(description="Specific skills that transfer to target field")
    direct_applications: list[str] = Field(description="Direct applications of this experience to target field")
    skill_gaps: list[str] = Field(description="Skills missing for full relevance to target field")


class ExperienceRelevanceAnalyzer(BaseAnalyzer):
    """Analyzer for assessing experience relevance to target fields across all business domains."""
    
    def get_model(self) -> Type[ExperienceRelevanceAnalysis]:
        """Get the Pydantic model for experience relevance analysis."""
        return ExperienceRelevanceAnalysis
    
    def get_input_variables(self) -> list[str]:
        """Get the input variables for the prompt template."""
        return ["experience_data", "target_field"]
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for experience relevance analysis."""
        return """
You are an expert career analyst specializing in evaluating how work experience translates to different professional fields across ALL business sectors and industries.

Analyze the provided work experience to determine its relevance to the target field: **{target_field}**

**Comprehensive Field Coverage:**
This analysis should work for ANY professional field including:
- Technology (Software, Data Science, IT, Product Management, etc.)
- Healthcare (Medical, Nursing, Administration, Pharma, Research, etc.)
- Finance & Banking (Investment, Analysis, Accounting, Insurance, Risk, etc.)
- Marketing & Sales (Digital Marketing, Sales Management, Brand, Research, PR, etc.)
- Operations (Management, Logistics, Manufacturing, Quality, Supply Chain, etc.)
- Human Resources (Recruiting, HR Business Partner, Compensation, Training, etc.)
- Legal (Corporate Law, Litigation, Compliance, Paralegal, etc.)
- Education (Teaching, Administration, Curriculum, Training, etc.)
- Consulting (Management, Strategy, Business Analysis, Process, etc.)
- Government & Public Service (Administration, Policy, Regulatory, etc.)
- Non-Profit (Program Management, Fundraising, Community, Social Services, etc.)
- Real Estate (Property Management, Development, Commercial, etc.)
- Media & Communications (Journalism, Content, PR, Broadcasting, etc.)
- Retail & Consumer (Retail Management, Merchandising, Customer Experience, etc.)
- Energy & Utilities (Energy Management, Environmental, Operations, etc.)
- Construction & Engineering (Civil, Project Management, Architecture, etc.)
- And many others across all business sectors...

**Evaluation Criteria:**

1. **Direct Relevance (8-10 points):**
   - Role directly within the target field
   - Core responsibilities align with field requirements
   - Tools, systems, and methodologies are field-standard
   - Industry knowledge directly applicable

2. **High Transferability (6-7 points):**
   - Adjacent field with significant skill overlap
   - Core competencies highly applicable
   - Similar problem-solving approaches and methodologies
   - Relevant regulatory or industry knowledge

3. **Moderate Transferability (4-5 points):**
   - Some transferable skills and concepts
   - Relevant soft skills and management methodologies
   - Industry knowledge that partially applies
   - Cross-functional experience that adds value

4. **Limited Transferability (2-3 points):**
   - Minimal direct skill transfer
   - General professional skills only (communication, teamwork, etc.)
   - Limited domain relevance
   - Basic business acumen applicable

5. **No Relevance (1 point):**
   - No meaningful skill transfer
   - Completely different domain with no overlap
   - No applicable knowledge or experience

**Analysis Framework:**
- Assess technical/functional skills and tools alignment
- Evaluate problem-solving approaches and methodologies similarity
- Consider industry domain knowledge transfer (regulations, practices, standards)
- Analyze soft skills and management approaches relevance
- Identify specific applications to target field
- Highlight areas where experience adds unique value
- Consider cross-functional and cross-industry applications

**Target Field:** {target_field}

**Work Experience to Analyze:**
```Resume Text
{experience_data}
```

Provide a detailed relevance assessment with specific examples and reasoning that works for ANY professional field or industry combination.

{format_instructions}
"""
    
    def prepare_input_data(self, experience, target_field: str, **kwargs) -> Dict[str, Any]:
        """Prepare single work experience data for relevance analysis."""
        
        experience_data = {
            "job_title": experience.job_title,
            "company": experience.company,
            "industry": experience.industry,
            "duration": experience.duration,
            "responsibilities": experience.responsibilities,
            "technologies": experience.technologies,
            "employment_type": experience.employment_type
        }
        
        return {
            "experience_data": experience_data,
            "target_field": target_field
        }
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the experience relevance analysis output."""
        return output.get('experiencerelevanceanalysis', {})