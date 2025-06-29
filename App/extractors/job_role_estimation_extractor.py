"""
Job role estimation extractor for suggesting best fit job roles based on resume analysis.
"""
from typing import Type, Dict, Any, List
from .base_extractor import BaseExtractor
from pydantic import BaseModel, Field


class JobRoleEstimation(BaseModel):
    """Model for job role estimation analysis."""
    primary_job_role: str = Field(description="Primary recommended job role")
    alternative_roles: List[str] = Field(default_factory=list, description="Alternative job roles that could fit")
    role_confidence_score: int = Field(ge=1, le=10, description="Confidence in primary role recommendation (1-10)")
    role_justification: str = Field(description="Detailed justification for the recommended role")
    required_skills_match: List[str] = Field(default_factory=list, description="Skills that match the recommended role")
    skill_gaps: List[str] = Field(default_factory=list, description="Skills that could enhance role suitability")
    career_progression_path: List[str] = Field(default_factory=list, description="Potential career progression from this role")
    salary_range_estimate: str = Field(description="Estimated salary range for the role")
    role_suitability_factors: Dict[str, int] = Field(default_factory=dict, description="Factors affecting role suitability (1-10 scores)")


class JobRoleEstimationExtractor(BaseExtractor):
    """Extractor for estimating best fit job roles based on comprehensive resume analysis."""
    
    def get_model(self) -> Type[JobRoleEstimation]:
        """Get the Pydantic model for job role estimation."""
        return JobRoleEstimation
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for job role estimation."""
        return """
You are an expert career counselor and talent acquisition specialist with deep knowledge of job markets across industries.

Analyze the comprehensive candidate profile to recommend the most suitable job roles.

**Candidate Profile:**
- Name: {candidate_name}
- Primary Field: {primary_field}
- Career Level: {career_level}
- Years of Experience: {years_of_experience}
- Skills: {skills}
- Work Experience Summary: {work_experience_summary}
- Education: {education_summary}
- Role Type Characteristics: {role_type_info}

**Job Role Recommendation Framework:**

**1. Technology Roles:**
- Software Engineer (Junior/Mid/Senior/Lead/Principal)
- Full Stack Developer
- Frontend Developer
- Backend Developer
- DevOps Engineer
- Data Scientist
- Data Analyst
- Machine Learning Engineer
- Cloud Architect
- Product Manager (Technical)
- Engineering Manager
- Technical Lead
- Site Reliability Engineer (SRE)
- Mobile Developer (iOS/Android)
- Web Developer

**2. Business Roles:**
- Business Analyst
- Product Manager
- Project Manager
- Operations Manager
- Business Development Manager
- Sales Manager
- Marketing Manager
- Strategy Consultant
- Account Manager
- Customer Success Manager
- Program Manager

**3. Creative Roles:**
- UI/UX Designer
- Graphic Designer
- Product Designer
- Creative Director
- User Researcher
- Brand Manager
- Content Creator
- Digital Marketing Specialist

**4. Leadership/Executive Roles:**
- Team Lead
- Department Manager
- Director of Engineering
- VP of Product
- Chief Technology Officer (CTO)
- Chief Product Officer (CPO)
- General Manager

**Analysis Criteria:**

**1. Skills Alignment (25%):**
- Technical skills match with role requirements
- Domain expertise depth
- Tool and technology proficiency
- Certification relevance

**2. Experience Relevance (25%):**
- Years of relevant experience
- Job title progression
- Responsibility level
- Industry experience

**3. Career Level Fit (20%):**
- Entry Level: Junior, Associate, Analyst roles
- Mid Level: Regular, Specialist, Consultant roles  
- Senior Level: Senior, Lead, Principal, Manager roles
- Executive Level: Director, VP, C-level roles

**4. Role Type Match (15%):**
- Technical alignment for technical roles
- Creative alignment for design roles
- Business alignment for strategy roles
- Leadership experience for management roles

**5. Growth Potential (15%):**
- Learning trajectory
- Skill development pattern
- Career progression consistency
- Industry growth prospects

**Salary Estimation Guidelines:**
- Consider experience level, location (general), industry standards
- Entry Level: $50K-$80K, Mid Level: $80K-$130K, Senior Level: $130K-$200K+
- Adjust based on role type and market demand
- Provide ranges (e.g., "$90K-$120K annually")

**Role Suitability Scoring:**
Rate each factor 1-10:
- **Skills Match**: How well skills align with role
- **Experience Fit**: How relevant experience is
- **Growth Readiness**: Readiness for next career step
- **Market Demand**: Current job market demand for this profile

**Output Requirements:**
1. **Primary Role**: Most suitable job title
2. **Alternative Roles**: 2-3 other good fits
3. **Confidence Score**: 1-10 rating for primary recommendation
4. **Justification**: Why this role fits best
5. **Skill Analysis**: Matching skills and gaps
6. **Career Path**: Potential progression opportunities
7. **Salary Estimate**: Realistic compensation range

Provide specific, actionable recommendations based on current job market trends.

{format_instructions}
"""
    
    def get_input_variables(self) -> List[str]:
        """Get the input variables for the prompt template."""
        return ["candidate_name", "primary_field", "career_level", "years_of_experience", 
                "skills", "work_experience_summary", "education_summary", "role_type_info"]
    
    def prepare_input_data(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare comprehensive resume data for job role estimation."""
        
        # Extract basic information
        candidate_name = resume_data.get('name', 'Candidate')
        primary_field = resume_data.get('primary_field', 'General')
        career_level = resume_data.get('career_level', 'Not determined')
        years_of_experience = resume_data.get('YoE', 'Not specified')
        
        # Format skills
        skills = resume_data.get('skills', [])
        skills_text = ", ".join(skills) if skills else "No skills specified"
        
        # Format work experience summary
        work_experiences = resume_data.get('work_experiences', [])
        work_summary = []
        if work_experiences:
            for i, exp in enumerate(work_experiences[:3], 1):  # Top 3 recent experiences
                exp_text = f"{i}. {exp.job_title or 'Unknown'} at {exp.company or 'Unknown'}"
                if exp.duration:
                    exp_text += f" ({exp.duration})"
                work_summary.append(exp_text)
        work_experience_summary = "\n".join(work_summary) if work_summary else "No work experience"
        
        # Format education summary
        educations = resume_data.get('educations', [])
        education_summary = []
        if educations:
            for edu in educations[:2]:  # Top 2 education entries
                edu_text = f"{edu.degree or 'Unknown'} in {edu.field_of_study or 'Unknown'}"
                if edu.institution:
                    edu_text += f" from {edu.institution}"
                education_summary.append(edu_text)
        education_text = "; ".join(education_summary) if education_summary else "No education specified"
        
        # Role type information (would be enhanced if we had role type analysis)
        role_type_info = "Analysis pending - will be determined based on skills and experience"
        
        return {
            "candidate_name": candidate_name,
            "primary_field": primary_field,
            "career_level": career_level,
            "years_of_experience": years_of_experience,
            "skills": skills_text,
            "work_experience_summary": work_experience_summary,
            "education_summary": education_text,
            "role_type_info": role_type_info
        }
    
    def estimate_job_role(self, resume_data: Dict[str, Any], development_mode: bool = False) -> Dict[str, Any]:
        """Estimate best fit job roles based on comprehensive resume analysis."""
        
        input_data = self.prepare_input_data(resume_data)
        
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
        Note: This method requires structured input. Use estimate_job_role() for direct usage.
        """
        # This is a fallback method - ideally use estimate_job_role()
        input_data = {"text": extracted_text}
        
        # Import llm_service here to avoid circular imports
        from llm_service import llm_service
        
        # Use a simplified prompt for raw text analysis
        simplified_prompt = """
        Analyze the following resume text to estimate suitable job roles:
        
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
        """Process the job role estimation output."""
        return output
    
    @staticmethod
    def estimate_job_role_fallback(resume_data: Dict[str, Any]) -> str:
        """
        Fallback job role estimation using simple heuristics.
        Used when LLM extractor fails.
        """
        skills = resume_data.get('skills', [])
        career_level = resume_data.get('career_level', 'Entry Level')
        primary_field = resume_data.get('primary_field', 'General')
        
        if not skills:
            return f"{career_level} Professional"
        
        skills_text = ' '.join(skills).lower()
        
        # Simple heuristic based on skills and career level
        level_prefix = ""
        if "senior" in career_level.lower():
            level_prefix = "Senior "
        elif "mid" in career_level.lower():
            level_prefix = ""
        elif "entry" in career_level.lower() or "junior" in career_level.lower():
            level_prefix = "Junior "
        
        # Field-based role suggestions
        if "data science" in primary_field.lower():
            if any(skill in skills_text for skill in ['machine learning', 'python', 'tensorflow']):
                return f"{level_prefix}Data Scientist"
            else:
                return f"{level_prefix}Data Analyst"
        elif "software" in primary_field.lower() or "development" in primary_field.lower():
            if any(skill in skills_text for skill in ['react', 'javascript', 'frontend']):
                return f"{level_prefix}Frontend Developer"
            elif any(skill in skills_text for skill in ['api', 'backend', 'database']):
                return f"{level_prefix}Backend Developer"
            else:
                return f"{level_prefix}Software Developer"
        elif "business" in primary_field.lower():
            return f"{level_prefix}Business Analyst"
        else:
            return f"{level_prefix}Professional" 