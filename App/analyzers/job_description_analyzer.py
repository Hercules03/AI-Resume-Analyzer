"""
Job description analyzer for extracting key requirements and field information.
"""
from typing import Type, Dict, Any
from pydantic import BaseModel, Field
from .base_analyzer import BaseAnalyzer


class JobDescriptionAnalysis(BaseModel):
    """Model for job description analysis."""
    required_skills: list[str] = Field(description="Required technical skills, programming languages, frameworks, databases, tools")
    key_requirements: list[str] = Field(description="Key experience requirements, qualifications, and responsibilities")
    experience_level: str = Field(description="Required experience level: Entry/Junior/Mid/Senior/Lead")
    field: str = Field(description="Primary field/domain such as Software Development, Data Science, DevOps, etc.")
    analysis_method: str = Field(description="Method used for analysis: LLM or Keyword Extraction")


class JobDescriptionAnalyzer(BaseAnalyzer):
    """Analyzer for job description content extraction across all business domains."""
    
    def get_model(self) -> Type[JobDescriptionAnalysis]:
        """Get the Pydantic model for job description analysis."""
        return JobDescriptionAnalysis
    
    def get_input_variables(self) -> list[str]:
        """Get the input variables for the prompt template."""
        return ["job_description"]
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for job description analysis."""
        return """
You are an expert HR analyst specializing in analyzing job descriptions across ALL business sectors and industries to extract key hiring requirements.

Analyze the provided job description and extract comprehensive information about the role requirements.

**Comprehensive Industry Coverage:**
This analysis should work for ANY professional field including:
- **Technology:** Software Development, Data Science, DevOps, Backend/Frontend Development, Mobile Development, Cybersecurity, AI/ML, Product Management, IT Management
- **Healthcare:** Medical Practice, Nursing, Healthcare Administration, Pharmaceuticals, Medical Research, Biotechnology, Clinical Operations
- **Finance & Banking:** Investment Banking, Financial Analysis, Accounting, Insurance, Risk Management, Wealth Management, Fintech
- **Marketing & Sales:** Digital Marketing, Sales Management, Brand Management, Market Research, PR, Content Marketing, E-commerce
- **Operations:** Operations Management, Supply Chain, Logistics, Manufacturing, Quality Assurance, Process Improvement
- **Human Resources:** Talent Acquisition, HR Business Partnering, Compensation & Benefits, Training & Development, Employee Relations
- **Legal:** Corporate Law, Litigation, Compliance, Paralegal, Legal Research, Intellectual Property, Regulatory Affairs
- **Education:** Teaching, Educational Administration, Curriculum Development, Training & Development, Academic Research
- **Consulting:** Management Consulting, Strategy, Business Analysis, Process Improvement, Technology Consulting
- **Government & Public Service:** Public Administration, Policy Development, Regulatory Affairs, Social Services
- **And many others across all business sectors...

**Analysis Framework:**

1. **Required Technical Skills Extraction:**
   - Programming languages (Python, Java, C#, JavaScript, etc.)
   - Frameworks and libraries (.NET, React, Django, Spring, etc.)
   - Databases and data tools (SQL Server, MySQL, Oracle, Tableau, etc.)
   - Cloud platforms and DevOps tools (AWS, Azure, Docker, Kubernetes, etc.)
   - Industry-specific software and tools
   - Professional certifications and credentials
   - Domain-specific technical skills

2. **Key Requirements Analysis:**
   - Years of experience required
   - Educational qualifications (degree requirements, specific fields of study)
   - Professional certifications or licenses
   - Language requirements
   - Soft skills and competencies
   - Industry-specific knowledge requirements
   - Management or leadership experience

3. **Experience Level Classification:**
   - **Entry Level (0-2 years):** Keywords like "entry," "junior," "graduate," "trainee," "recent graduate"
   - **Junior Level (2-4 years):** Keywords like "junior," "associate," basic responsibilities
   - **Mid Level (4-7 years):** Independent work, project ownership, some leadership
   - **Senior Level (7+ years):** Keywords like "senior," "lead," complex projects, mentoring others
   - **Lead/Expert (10+ years):** Keywords like "principal," "director," "head of," "chief," strategic responsibilities

4. **Field/Domain Classification:**
   - Analyze job title, responsibilities, and required skills
   - Map to appropriate professional field or industry
   - Consider cross-functional roles and hybrid positions
   - Account for emerging fields and specialized niches

**Job Description:**
```Job Description
{job_description}
```

**Instructions:**
- Extract ALL technical skills, tools, and technologies mentioned
- Identify key qualifications and experience requirements
- Determine the appropriate experience level based on complexity and requirements
- Classify the primary professional field or domain
- Be comprehensive but concise in your analysis
- Focus on hard requirements vs. nice-to-have skills

Provide a thorough analysis that works for ANY job description across all industries and professional fields.

{format_instructions}
"""
    
    def prepare_input_data(self, job_description: str, **kwargs) -> Dict[str, Any]:
        """Prepare job description text for analysis."""
        return {"job_description": job_description}
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the job description analysis output."""
        analysis = output.get('jobdescriptionanalysis', {})
        # Add analysis method indicator for LLM success
        if analysis and analysis.get('required_skills'):
            analysis['analysis_method'] = 'LLM (AI Analysis)'
        return analysis
    
    def analyze_with_fallback(self, job_description: str, development_mode: bool = False) -> Dict[str, Any]:
        """Analyze job description with automatic fallback to keyword extraction."""
        try:
            # Try LLM analysis first
            result = self.analyze(job_description, development_mode=development_mode)
            
            # Check if LLM analysis was successful
            if (result and result.get('required_skills') and 
                len(result['required_skills']) > 0 and 
                result['required_skills'][0] not in ['Development experience', 'Technical skills']):
                return result
                
        except Exception as e:
            if development_mode:
                print(f"LLM analysis failed: {e}")
        
        # Fallback to keyword-based analysis
        return self._keyword_fallback_analysis(job_description)
    
    def _keyword_fallback_analysis(self, job_description: str) -> Dict[str, Any]:
        """Fallback keyword-based job description analysis."""
        jd_lower = job_description.lower()
        
        # Technical skills mapping
        tech_skills = {
            'programming_languages': ['c#', 'python', 'java', 'javascript', 'typescript', 'go', 'rust', 'php', 'ruby', 'swift', 'kotlin'],
            'frameworks': ['.net', 'framework', 'django', 'flask', 'react', 'angular', 'vue', 'spring', 'express', 'node.js'],
            'databases': ['sql server', 'mysql', 'oracle', 'postgresql', 'mongodb', 'redis', 'database'],
            'cloud_tools': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform'],
            'protocols': ['tcp/ip', 'ssl', 'http', 'rest', 'api', 'web services'],
            'other_skills': ['git', 'linux', 'windows', 'agile', 'scrum']
        }
        
        found_skills = []
        for category, skills in tech_skills.items():
            for skill in skills:
                if skill in jd_lower:
                    found_skills.append(skill.upper() if skill in ['c#', 'sql', 'api', 'tcp/ip', 'ssl'] else skill.title())
        
        # Remove duplicates and limit to top 10
        found_skills = list(dict.fromkeys(found_skills))[:10]
        
        # Key requirements extraction
        requirements = []
        if 'experience' in jd_lower:
            requirements.append("Professional development experience required")
        if 'degree' in jd_lower or 'bachelor' in jd_lower:
            requirements.append("Bachelor's degree or equivalent")
        if 'english' in jd_lower:
            requirements.append("Good command of English")
        if 'problem' in jd_lower and 'solving' in jd_lower:
            requirements.append("Strong problem-solving skills")
        if 'independent' in jd_lower:
            requirements.append("Ability to work independently")
        
        # Experience level determination
        experience_level = "Mid-Level"
        if any(word in jd_lower for word in ['senior', 'lead', 'architect', 'principal']):
            experience_level = "Senior Level"
        elif any(word in jd_lower for word in ['junior', 'entry', 'graduate', 'intern']):
            experience_level = "Entry Level"
        elif any(word in jd_lower for word in ['complex', 'integration', 'driver', 'external device']):
            experience_level = "Mid to Senior Level"
        
        # Field determination
        field = "Software Development"
        if any(word in jd_lower for word in ['c#', '.net', 'driver', 'device', 'integration']):
            field = "Backend Development"
        elif any(word in jd_lower for word in ['data', 'analytics', 'science']):
            field = "Data Science"
        elif any(word in jd_lower for word in ['mobile', 'android', 'ios']):
            field = "Mobile Development"
        elif any(word in jd_lower for word in ['devops', 'infrastructure', 'deployment']):
            field = "DevOps"
        
        return {
            "required_skills": found_skills if found_skills else ["Development experience", "Technical skills"],
            "key_requirements": requirements if requirements else ["Development experience", "Technical proficiency"],
            "experience_level": experience_level,
            "field": field,
            "analysis_method": "Keyword Extraction (Fallback)"
        } 