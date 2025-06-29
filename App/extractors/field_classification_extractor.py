"""
Field classification extractor for determining primary field based on skills and experience.
"""
from typing import Type, Dict, Any, List
from .base_extractor import BaseExtractor
from pydantic import BaseModel, Field


class FieldClassificationAnalysis(BaseModel):
    """Model for field classification analysis."""
    primary_field: str = Field(description="The primary professional field")
    confidence_score: int = Field(ge=1, le=10, description="Confidence in field classification (1-10)")
    field_indicators: List[str] = Field(default_factory=list, description="Evidence supporting this field classification")
    secondary_fields: List[str] = Field(default_factory=list, description="Secondary or related fields")
    field_explanation: str = Field(description="Detailed explanation of field determination")
    skill_alignment_score: int = Field(ge=1, le=10, description="How well skills align with the field (1-10)")
    experience_alignment_score: int = Field(ge=1, le=10, description="How well experience aligns with the field (1-10)")


class FieldClassificationExtractor(BaseExtractor):
    """Extractor for determining primary professional field from skills and experience."""
    
    def get_model(self) -> Type[FieldClassificationAnalysis]:
        """Get the Pydantic model for field classification."""
        return FieldClassificationAnalysis
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for field classification."""
        return """
You are an expert career analyst specializing in professional field classification.

Analyze the candidate's skills, work experience, and education to determine their primary professional field.

**Candidate Information:**
- Skills: {skills}
- Work Experience: {work_experience}
- Education: {education}
- Current Primary Field (if any): {current_primary_field}

**Available Professional Fields:**
1. **Data Science & Analytics** - Data analysis, machine learning, statistics, business intelligence
2. **Software Engineering/Development** - Programming, software development, system architecture
3. **Web Development** - Frontend/backend web development, web technologies
4. **Mobile Development** - iOS/Android development, mobile app development
5. **DevOps & Cloud** - Infrastructure, cloud computing, automation, CI/CD
6. **Product Management** - Product strategy, roadmap planning, stakeholder management
7. **Business/Sales/Marketing** - Business development, sales, marketing, growth
8. **Finance & Accounting** - Financial analysis, accounting, investment, banking
9. **Operations & Supply Chain** - Operations management, logistics, supply chain
10. **Human Resources** - HR management, talent acquisition, organizational development
11. **Design & Creative** - UI/UX design, graphic design, creative services
12. **Healthcare & Medical** - Healthcare, medical, pharmaceutical, biotech
13. **Education & Training** - Teaching, training, curriculum development
14. **Legal & Compliance** - Legal services, compliance, regulatory affairs
15. **Consulting** - Management consulting, strategy consulting, advisory services
16. **Management & Leadership** - Executive leadership, team management, strategy
17. **Research & Development** - R&D, innovation, scientific research
18. **General** - Mixed or unclear field alignment

**Analysis Criteria:**

1. **Skills Analysis** (40% weight):
   - Technical skills alignment with field requirements
   - Depth and breadth of relevant skills
   - Tools and technologies used

2. **Experience Analysis** (40% weight):
   - Job titles and role responsibilities
   - Industry sectors worked in
   - Career progression pattern
   - Duration and depth of field experience

3. **Education Analysis** (20% weight):
   - Degree field alignment
   - Relevant coursework
   - Academic focus areas

**Classification Guidelines:**
- **High Confidence (8-10)**: Clear alignment across skills, experience, and education
- **Medium Confidence (5-7)**: Good alignment with some mixed elements
- **Low Confidence (1-4)**: Unclear or mixed signals, limited alignment

**Scoring Criteria:**
- **Skill Alignment (1-10)**: How well skills match field requirements
- **Experience Alignment (1-10)**: How well work history fits the field

**Special Considerations:**
- Career changers may have skills from multiple fields
- Generalists may span multiple domains
- Early career professionals may have limited field-specific experience
- Consider recent trends and emerging field boundaries

Provide a thorough analysis with clear reasoning for the field classification.

{format_instructions}
"""
    
    def get_input_variables(self) -> List[str]:
        """Get the input variables for the prompt template."""
        return ["skills", "work_experience", "education", "current_primary_field"]
    
    def prepare_input_data(self, skills: List[str], work_experiences: List[Dict[str, Any]] = None, 
                          educations: List[Dict[str, Any]] = None, current_primary_field: str = None) -> Dict[str, Any]:
        """Prepare data for field classification analysis."""
        
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
                    exp_text += f". Key responsibilities: {'; '.join(exp['responsibilities'][:2])}"
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
            "education": education_formatted,
            "current_primary_field": current_primary_field or "Not specified"
        }
    
    def classify_field(self, skills: List[str], work_experiences: List[Dict[str, Any]] = None, 
                      educations: List[Dict[str, Any]] = None, current_primary_field: str = None, 
                      development_mode: bool = False) -> Dict[str, Any]:
        """Classify the primary professional field based on skills and experience."""
        
        input_data = self.prepare_input_data(skills, work_experiences, educations, current_primary_field)
        
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
        Note: This method requires structured input. Use classify_field() for direct usage.
        """
        # This is a fallback method - ideally use classify_field()
        input_data = {"text": extracted_text}
        
        # Import llm_service here to avoid circular imports
        from llm_service import llm_service
        
        # Use a simplified prompt for raw text analysis
        simplified_prompt = """
        Analyze the following resume text to determine the primary professional field:
        
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
        """Process the field classification output."""
        return output
    
    @staticmethod
    def classify_field_fallback(skills: List[str]) -> str:
        """
        Fallback field classification using simple keyword matching.
        Used when LLM extractor fails.
        """
        if not skills:
            return "General"
        
        skills_str = " ".join(skills).lower()
        
        # Simple keyword-based fallback
        if any(skill in skills_str for skill in ['python', 'data', 'machine learning', 'analytics', 'sql', 'tableau', 'pandas']):
            return "Data Science & Analytics"
        elif any(skill in skills_str for skill in ['javascript', 'react', 'web', 'frontend', 'html', 'css', 'vue', 'angular']):
            return "Web Development"
        elif any(skill in skills_str for skill in ['java', 'backend', 'api', 'spring', 'django', 'flask', 'node.js']):
            return "Software Engineering/Development"
        elif any(skill in skills_str for skill in ['mobile', 'android', 'ios', 'swift', 'kotlin', 'react native']):
            return "Mobile Development"
        elif any(skill in skills_str for skill in ['aws', 'docker', 'kubernetes', 'devops', 'jenkins', 'terraform']):
            return "DevOps & Cloud"
        else:
            return "General" 