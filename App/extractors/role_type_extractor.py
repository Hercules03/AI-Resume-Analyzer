"""
Role type extractor for determining if a candidate has technical, creative, or other role characteristics.
"""
from typing import Type, Dict, Any, List
from .base_extractor import BaseExtractor
from pydantic import BaseModel, Field


class RoleTypeAnalysis(BaseModel):
    """Model for role type analysis."""
    is_technical: bool = Field(description="Whether the candidate appears to have technical skills/experience")
    is_creative: bool = Field(description="Whether the candidate appears to have creative skills/experience")
    is_business: bool = Field(description="Whether the candidate appears to have business skills/experience")
    is_leadership: bool = Field(description="Whether the candidate appears to have leadership experience")
    technical_score: int = Field(ge=1, le=10, description="Technical role alignment score (1-10)")
    creative_score: int = Field(ge=1, le=10, description="Creative role alignment score (1-10)")
    business_score: int = Field(ge=1, le=10, description="Business role alignment score (1-10)")
    leadership_score: int = Field(ge=1, le=10, description="Leadership role alignment score (1-10)")
    primary_role_type: str = Field(description="Primary role type: Technical, Creative, Business, Leadership, or Mixed")
    role_indicators: Dict[str, List[str]] = Field(default_factory=dict, description="Evidence for each role type")
    role_explanation: str = Field(description="Detailed explanation of role type determination")


class RoleTypeExtractor(BaseExtractor):
    """Extractor for determining role type characteristics (technical, creative, business, etc.)."""
    
    def get_model(self) -> Type[RoleTypeAnalysis]:
        """Get the Pydantic model for role type analysis."""
        return RoleTypeAnalysis
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for role type analysis."""
        return """
You are an expert at analyzing professional profiles to determine role type characteristics.

Analyze the candidate's skills, work experience, and education to determine their role type alignment.

**Candidate Information:**
- Skills: {skills}
- Work Experience: {work_experience}
- Education: {education}

**Role Type Framework:**

1. **Technical Roles**:
   - Programming languages (Python, Java, JavaScript, C++, etc.)
   - Development frameworks and libraries
   - Databases and data technologies
   - Cloud platforms and infrastructure
   - Technical tools and platforms
   - Engineering and development experience
   - Technical problem-solving and architecture

2. **Creative Roles**:
   - Design tools (Photoshop, Illustrator, Figma, Sketch, etc.)
   - UI/UX design and user research
   - Graphic design and visual arts
   - Creative software and platforms
   - Portfolio and creative project experience
   - Brand development and creative strategy
   - Content creation and multimedia

3. **Business Roles**:
   - Business analysis and strategy
   - Sales and marketing experience
   - Financial analysis and planning
   - Operations and process optimization
   - Customer relationship management
   - Business development and partnerships
   - Market research and competitive analysis

4. **Leadership Roles**:
   - Team management and supervision
   - Project management and coordination
   - Strategic planning and vision
   - Organizational development
   - Change management
   - Executive decision-making
   - Mentoring and coaching

**Analysis Criteria:**

For each role type, evaluate:
- **Skills Alignment**: How well skills match role requirements
- **Experience Evidence**: Job titles, responsibilities, and achievements
- **Depth vs Breadth**: Specialist vs generalist tendencies
- **Industry Context**: Industry norms and expectations

**Scoring Guidelines (1-10):**
- **9-10**: Strong role type alignment with multiple indicators
- **7-8**: Good role type alignment with clear evidence
- **5-6**: Moderate role type alignment with some indicators
- **3-4**: Weak role type alignment with limited evidence
- **1-2**: Minimal or no role type alignment

**Primary Role Type Classification:**
- **Technical**: Primarily technical skills and experience (technical_score ≥ 7)
- **Creative**: Primarily creative skills and experience (creative_score ≥ 7)
- **Business**: Primarily business skills and experience (business_score ≥ 7)
- **Leadership**: Primarily leadership skills and experience (leadership_score ≥ 7)
- **Mixed**: Multiple role types with similar high scores

**Special Considerations:**
- Many modern roles blend multiple types (e.g., Technical + Business)
- Leadership can be present across all other types
- Early career professionals may show potential rather than proven experience
- Consider both hard skills and soft skills evidence

Provide detailed analysis with specific evidence for each role type determination.

{format_instructions}
"""
    
    def get_input_variables(self) -> List[str]:
        """Get the input variables for the prompt template."""
        return ["skills", "work_experience", "education"]
    
    def prepare_input_data(self, skills: List[str], work_experiences: List[Dict[str, Any]] = None, 
                          educations: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare data for role type analysis."""
        
        # Format skills
        skills_text = ", ".join(skills) if skills else "No skills specified"
        
        # Format work experience
        work_exp_text = []
        if work_experiences:
            for i, exp in enumerate(work_experiences, 1):
                exp_text = f"Position {i}: {exp.get('job_title', 'Unknown')} at {exp.get('company', 'Unknown')}"
                if exp.get('duration'):
                    exp_text += f" ({exp['duration']})"
                if exp.get('responsibilities'):
                    exp_text += f". Key responsibilities: {'; '.join(exp['responsibilities'][:3])}"
                if exp.get('technologies'):
                    exp_text += f". Technologies: {', '.join(exp['technologies'][:5])}"
                work_exp_text.append(exp_text)
        
        work_experience_text = "\n".join(work_exp_text) if work_exp_text else "No work experience specified"
        
        # Format education
        education_text = []
        if educations:
            for i, edu in enumerate(educations, 1):
                edu_text = f"Education {i}: {edu.get('degree', 'Unknown')} in {edu.get('field_of_study', 'Unknown')}"
                if edu.get('institution'):
                    edu_text += f" from {edu['institution']}"
                education_text.append(edu_text)
        
        education_formatted = "\n".join(education_text) if education_text else "No education specified"
        
        return {
            "skills": skills_text,
            "work_experience": work_experience_text,
            "education": education_formatted
        }
    
    def analyze_role_type(self, skills: List[str], work_experiences: List[Dict[str, Any]] = None, 
                         educations: List[Dict[str, Any]] = None, development_mode: bool = False) -> Dict[str, Any]:
        """Analyze role type characteristics from skills and experience."""
        
        input_data = self.prepare_input_data(skills, work_experiences, educations)
        
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
        Note: This method requires structured input. Use analyze_role_type() for direct usage.
        """
        # This is a fallback method - ideally use analyze_role_type()
        input_data = {"text": extracted_text}
        
        # Import llm_service here to avoid circular imports
        from llm_service import llm_service
        
        # Use a simplified prompt for raw text analysis
        simplified_prompt = """
        Analyze the following resume text to determine role type characteristics:
        
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
        """Process the role type analysis output."""
        return output
    
    @staticmethod
    def appears_technical_fallback(skills: List[str]) -> bool:
        """
        Fallback technical role detection using keyword matching.
        Used when LLM extractor fails.
        """
        if not skills:
            return False
        
        technical_keywords = ['python', 'java', 'javascript', 'sql', 'aws', 'docker', 'react', 'api', 
                             'database', 'programming', 'software', 'developer', 'engineer']
        skills_text = ' '.join(skills).lower()
        return any(keyword in skills_text for keyword in technical_keywords)
    
    @staticmethod
    def appears_creative_fallback(skills: List[str]) -> bool:
        """
        Fallback creative role detection using keyword matching.
        Used when LLM extractor fails.
        """
        if not skills:
            return False
        
        creative_keywords = ['design', 'photoshop', 'illustrator', 'figma', 'ui', 'ux', 'graphic', 
                            'creative', 'adobe', 'sketch', 'portfolio']
        skills_text = ' '.join(skills).lower()
        return any(keyword in skills_text for keyword in creative_keywords) 