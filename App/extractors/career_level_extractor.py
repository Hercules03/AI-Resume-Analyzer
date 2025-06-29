"""
Career level extractor for determining field-specific career progression and seniority.
"""
from typing import Type, Dict, Any, List
from .base_extractor import BaseExtractor
from pydantic import BaseModel, Field


class CareerLevelAnalysis(BaseModel):
    """Model for career level analysis."""
    career_level: str = Field(description="Determined career level")
    confidence_score: int = Field(ge=1, le=10, description="Confidence in career level assessment (1-10)")
    field_specific_experience_years: float = Field(description="Years of experience in the target field")
    total_experience_years: float = Field(description="Total years of work experience")
    level_indicators: List[str] = Field(default_factory=list, description="Factors that indicate this career level")
    progression_pattern: str = Field(description="Pattern of career progression")
    next_level_requirements: List[str] = Field(default_factory=list, description="What's needed to reach next level")
    field_expertise_depth: str = Field(description="Depth of expertise in the target field")
    leadership_experience: bool = Field(description="Whether candidate has leadership experience")
    detailed_explanation: str = Field(description="Detailed explanation of career level determination")


class CareerLevelExtractor(BaseExtractor):
    """Extractor for determining field-specific career level."""
    
    def get_model(self) -> Type[CareerLevelAnalysis]:
        """Get the Pydantic model for career level analysis."""
        return CareerLevelAnalysis
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for career level analysis."""
        return """
You are an expert career analyst specializing in career level assessment across different professional fields.

Analyze the candidate's work experience to determine their career level specifically within the target field.

**Target Field:** {target_field}

**Candidate Information:**
- Total Years of Experience: {total_years}
- Work Experience Entries: {experience_count}

**Work Experience Details:**
{experience_details}

**Career Level Framework:**

1. **Entry Level (0-2 years in field)**:
   - New to the field or recent graduate
   - Learning fundamental skills
   - Working under close supervision
   - Limited independent decision-making
   - Job titles: Junior, Associate, Entry-level, Intern, Trainee

2. **Junior Level (1-3 years in field)**:
   - Basic proficiency in core skills
   - Some independent work capability
   - Beginning to specialize
   - Minimal leadership responsibilities
   - Job titles: Junior, Associate, Analyst

3. **Mid Level (3-6 years in field)**:
   - Solid competency in field
   - Works independently on projects
   - May lead small teams or initiatives
   - Recognized expertise in specific areas
   - Job titles: Specialist, Consultant, Team Lead

4. **Senior Level (5-10 years in field)**:
   - Expert-level skills and knowledge
   - Leads major projects and teams
   - Mentors junior staff
   - Strategic thinking and planning
   - Job titles: Senior, Principal, Manager, Lead

5. **Executive Level (10+ years in field)**:
   - Deep expertise and thought leadership
   - Organizational decision-making authority
   - Cross-functional leadership
   - Industry recognition
   - Job titles: Director, VP, C-level, Principal

6. **Career Changer**:
   - Experienced professional new to this field
   - Transferable skills from other domains
   - May have senior experience in other fields
   - Accelerated learning curve expected

**Assessment Criteria:**

1. **Field-Specific Experience**: Focus on time in the target field, not total experience
2. **Job Title Progression**: Analyze title evolution and responsibilities
3. **Responsibility Growth**: Look for increasing autonomy and impact
4. **Leadership Indicators**: Team management, mentoring, strategic involvement
5. **Technical Depth**: Complexity of work and specialization
6. **Career Transitions**: Consider transitions from other fields

**Special Considerations:**
- **Career Changers**: May have senior experience but be entry-level in new field
- **Consultants/Freelancers**: May have broad experience across levels
- **Rapid Progression**: Some fields allow faster advancement
- **Industry Context**: Different industries have different progression patterns

**Confidence Scoring (1-10):**
- 9-10: Very clear indicators, consistent progression
- 7-8: Good indicators with minor ambiguity
- 5-6: Mixed signals or limited information
- 3-4: Unclear progression or conflicting evidence
- 1-2: Very limited information to make assessment

Provide a thorough analysis considering field-specific experience and career progression patterns.

{format_instructions}
"""
    
    def get_input_variables(self) -> List[str]:
        """Get the input variables for the prompt template."""
        return ["target_field", "total_years", "experience_count", "experience_details"]
    
    def prepare_input_data(self, work_experiences: List[Dict[str, Any]], target_field: str, total_years: str = None) -> Dict[str, Any]:
        """Prepare work experience data for career level analysis."""
        
        experience_details = []
        
        for i, exp in enumerate(work_experiences, 1):
            exp_text = f"Experience {i}:\n"
            exp_text += f"  Job Title: {exp.get('job_title', 'Not specified')}\n"
            exp_text += f"  Company: {exp.get('company', 'Not specified')}\n"
            exp_text += f"  Duration: {exp.get('duration', 'Not specified')}\n"
            exp_text += f"  Industry: {exp.get('industry', 'Not specified')}\n"
            exp_text += f"  Employment Type: {exp.get('employment_type', 'Not specified')}\n"
            
            if exp.get('responsibilities'):
                exp_text += f"  Key Responsibilities:\n"
                for resp in exp['responsibilities'][:3]:  # Top 3 responsibilities
                    exp_text += f"    - {resp}\n"
            
            if exp.get('technologies'):
                exp_text += f"  Technologies: {', '.join(exp['technologies'][:5])}\n"  # Top 5 technologies
            
            exp_text += "\n"
            experience_details.append(exp_text)
        
        return {
            "target_field": target_field,
            "total_years": total_years or "Not specified",
            "experience_count": len(work_experiences),
            "experience_details": "\n".join(experience_details)
        }
    
    def analyze_career_level(self, work_experiences: List[Dict[str, Any]], target_field: str, total_years: str = None, development_mode: bool = False) -> Dict[str, Any]:
        """Analyze career level for the target field."""
        
        if not work_experiences:
            # Return default analysis for no experience
            return {
                'careerlevelanalysis': {
                    'career_level': 'Entry Level',
                    'confidence_score': 10,
                    'field_specific_experience_years': 0.0,
                    'total_experience_years': 0.0,
                    'level_indicators': ['No work experience found'],
                    'progression_pattern': 'No progression to analyze',
                    'next_level_requirements': ['Gain entry-level experience in the field'],
                    'field_expertise_depth': 'No expertise established',
                    'leadership_experience': False,
                    'detailed_explanation': 'No work experience found, classified as Entry Level.'
                }
            }
        
        input_data = self.prepare_input_data(work_experiences, target_field, total_years)
        
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
        Note: This method requires structured input. Use analyze_career_level() for direct usage.
        """
        # This is a fallback method - ideally use analyze_career_level()
        input_data = {"text": extracted_text}
        
        # Import llm_service here to avoid circular imports
        from llm_service import llm_service
        
        # Use a simplified prompt for raw text analysis
        simplified_prompt = """
        Analyze the following text to determine career level:
        
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
        """Process the career level analysis output."""
        return output
    
    @staticmethod
    def calculate_career_level_fallback(work_experiences: List[Dict[str, Any]], target_field: str, total_years: str = None) -> str:
        """
        Fallback career level calculation using simple heuristics.
        Used when LLM extractor fails.
        """
        if not work_experiences:
            return "Entry Level"
        
        # Simple heuristic based on number of experiences and job titles
        experience_count = len(work_experiences)
        
        # Check for senior-level job titles
        senior_titles = ['senior', 'lead', 'principal', 'manager', 'director', 'vp', 'chief', 'head']
        mid_titles = ['specialist', 'consultant', 'team lead', 'supervisor']
        
        has_senior_titles = any(
            any(title_word in (exp.get('job_title', '').lower()) for title_word in senior_titles)
            for exp in work_experiences
        )
        
        has_mid_titles = any(
            any(title_word in (exp.get('job_title', '').lower()) for title_word in mid_titles)
            for exp in work_experiences
        )
        
        # Simple scoring
        if has_senior_titles or experience_count >= 4:
            return "Senior Level"
        elif has_mid_titles or experience_count >= 2:
            return "Mid Level"
        else:
            return "Entry Level" 