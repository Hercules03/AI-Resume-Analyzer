from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime


class Education(BaseModel):
    """Education information model."""
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    institution: Optional[str] = None
    location: Optional[str] = None
    graduation_date: Optional[str] = None
    gpa: Optional[str] = None
    honors: Optional[str] = None
    relevant_coursework: List[str] = Field(default_factory=list)
    thesis_project: Optional[str] = None


class WorkExperience(BaseModel):
    """Work experience model."""
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    industry: Optional[str] = None
    employment_type: Optional[str] = None


class Profile(BaseModel):
    """Profile information model."""
    name: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None


class Skills(BaseModel):
    """Skills model."""
    programming_languages: List[str] = Field(default_factory=list)
    frameworks_libraries: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    tools_platforms: List[str] = Field(default_factory=list)
    operating_systems: List[str] = Field(default_factory=list)
    methodologies: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    domain_knowledge: List[str] = Field(default_factory=list)
    
    def get_all_skills(self) -> List[str]:
        """Get all skills as a flat list."""
        all_skills = []
        for skill_list in [
            self.programming_languages, self.frameworks_libraries, self.databases,
            self.tools_platforms, self.operating_systems, self.methodologies,
            self.soft_skills, self.languages, self.domain_knowledge
        ]:
            all_skills.extend(skill_list)
        return all_skills


class YearsOfExperience(BaseModel):
    """Years of experience model."""
    total_years: Optional[float] = None
    career_level: Optional[str] = None
    primary_field: Optional[str] = None


class CareerTransition(BaseModel):
    """Model for a single career transition."""
    from_field: str = Field(description="The career field the person transitioned from")
    to_field: str = Field(description="The career field the person transitioned to")
    transition_point: Optional[str] = Field(None, description="When the transition occurred (company/timeframe)")
    transition_type: str = Field(description="Type of transition: 'vertical', 'horizontal', 'pivot', or 'lateral'")
    skill_overlap: Optional[str] = Field(None, description="Description of transferable skills")
    rationale: Optional[str] = Field(None, description="Likely reason for the transition")


class CareerProgressionAnalysis(BaseModel):
    """Model for comprehensive career progression analysis."""
    transitions: List[CareerTransition] = Field(default_factory=list, description="List of detected career transitions")
    career_path_type: str = Field(description="Overall career path pattern: 'linear', 'zigzag', 'specialized', 'diverse', or 'early_career'")
    primary_career_field: str = Field(description="The dominant career field based on time spent and progression")
    career_coherence_score: int = Field(ge=1, le=10, description="How coherent/focused the career path is (1-10)")
    growth_trajectory: str = Field(description="Career growth pattern: 'ascending', 'lateral', 'mixed', or 'unclear'")
    field_expertise_areas: List[str] = Field(default_factory=list, description="Areas where the candidate has built expertise")
    transition_summary: str = Field(description="Human-readable summary of career transitions")
    strengths_from_transitions: List[str] = Field(default_factory=list, description="Strengths gained from career transitions")
    potential_concerns: List[str] = Field(default_factory=list, description="Potential concerns from frequent transitions")


class FieldRelevanceAnalysis(BaseModel):
    """Model for field relevance analysis."""
    is_relevant: bool = Field(description="Whether the experience is relevant to the target field")
    relevance_score: int = Field(ge=1, le=10, description="Relevance score from 1-10")
    matching_skills: List[str] = Field(default_factory=list, description="Skills that match the target field")
    transferable_skills: List[str] = Field(default_factory=list, description="Skills transferable to the target field")
    relevance_explanation: str = Field(description="Explanation of why experience is or isn't relevant")
    field_overlap_percentage: int = Field(ge=0, le=100, description="Percentage of overlap with target field")


class DurationAnalysis(BaseModel):
    """Model for duration analysis."""
    total_months: float = Field(description="Total duration in months")
    total_years: float = Field(description="Total duration in years (calculated)")
    original_text: str = Field(description="Original duration text")
    parsed_components: Dict[str, Any] = Field(default_factory=dict, description="Parsed components (years, months)")
    confidence_score: int = Field(ge=1, le=10, description="Confidence in parsing accuracy (1-10)")
    parsing_notes: str = Field(description="Notes about parsing challenges or assumptions")
    is_current: bool = Field(default=False, description="Whether this is a current/ongoing position")
    formatted_duration: str = Field(description="Human-readable formatted duration")


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


class FieldClassificationAnalysis(BaseModel):
    """Model for field classification analysis."""
    primary_field: str = Field(description="The primary professional field")
    confidence_score: int = Field(ge=1, le=10, description="Confidence in field classification (1-10)")
    field_indicators: List[str] = Field(default_factory=list, description="Evidence supporting this field classification")
    secondary_fields: List[str] = Field(default_factory=list, description="Secondary or related fields")
    field_explanation: str = Field(description="Detailed explanation of field determination")
    skill_alignment_score: int = Field(ge=1, le=10, description="How well skills align with the field (1-10)")
    experience_alignment_score: int = Field(ge=1, le=10, description="How well experience aligns with the field (1-10)")


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


class Resume(BaseModel):
    """A complete resume with all extracted information."""
    # Profile information
    name: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None
    
    # Skills
    skills: List[str] = Field(default_factory=list)
    
    # Education
    educations: List[Education] = Field(default_factory=list)
    
    # Work Experience
    work_experiences: List[WorkExperience] = Field(default_factory=list)
    
    # Years of Experience and Career Analysis
    YoE: Optional[str] = None
    career_level: Optional[str] = None
    primary_field: Optional[str] = None
    
    # Additional metadata for gap analysis
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    
    # System metadata
    file_path: Optional[str] = None
    extraction_timestamp: Optional[str] = None
    no_of_pages: Optional[int] = None
    
    @classmethod
    def from_extractors_output(
        cls,
        profile: Dict[str, Any],
        skills: Dict[str, Any],
        education: Dict[str, Any],
        experience: Dict[str, Any],
        yoe: Dict[str, Any],
        pdf_file_path: str
    ) -> "Resume":
        """Create a Resume object from extractor outputs."""
        
        # Extract profile data
        profile_data = profile.get('profile', {})
        
        # Extract skills data
        skills_data = skills.get('skills', {})
        all_skills = []
        if isinstance(skills_data, dict):
            for skill_category in skills_data.values():
                if isinstance(skill_category, list):
                    all_skills.extend(skill_category)
        
        # Extract education data
        education_data = education.get('educationlist', education.get('education', {}))
        education_list = education_data.get('educations', []) if isinstance(education_data, dict) else []
        educations = [Education(**edu) for edu in education_list if isinstance(edu, dict)]
        
        # Extract work experience data  
        experience_data = experience.get('workexperiencelist', experience.get('experience', {}))
        experience_list = experience_data.get('work_experiences', []) if isinstance(experience_data, dict) else []
        work_experiences = [WorkExperience(**exp) for exp in experience_list if isinstance(exp, dict)]
        
        # Extract YoE data (including career level and primary field)
        yoe_data = yoe.get('yoe', {})
        years_of_experience = yoe_data.get('total_years')
        yoe_str = f"{years_of_experience} years" if years_of_experience else None
        career_level = yoe_data.get('career_level')
        primary_field = yoe_data.get('primary_field')
        
        return cls(
            name=profile_data.get('name'),
            contact_number=profile_data.get('contact_number'),
            email=profile_data.get('email'),
            linkedin=profile_data.get('linkedin'),
            github=profile_data.get('github'),
            portfolio=profile_data.get('portfolio'),
            skills=all_skills,
            educations=educations,
            work_experiences=work_experiences,
            YoE=yoe_str,
            career_level=career_level,
            primary_field=primary_field,
            file_path=pdf_file_path,
            extraction_timestamp=datetime.now().isoformat(),
            no_of_pages=1  # Default, can be calculated from PDF
        )
    
    def analyze_resume_gaps(self) -> Dict[str, List[str]]:
        """
        Analyze resume for missing or incomplete information.
        Returns gaps categorized by section for HR review.
        """
        gaps = {
            "critical_missing": [],      # Must-have information that's missing
            "professional_missing": [],  # Professional profile gaps
            "detail_gaps": []           # Information present but lacks detail
        }
        
        # === CRITICAL MISSING INFORMATION ===
        if not self.name:
            gaps["critical_missing"].append("❌ Candidate name not found")
        if not self.email:
            gaps["critical_missing"].append("❌ Email address not found")
        if not self.contact_number:
            gaps["critical_missing"].append("❌ Phone number not found")
        
        # === PROFESSIONAL PROFILE GAPS ===
        if not self.linkedin:
            gaps["professional_missing"].append("🔗 LinkedIn profile not provided")
        if not self.github and self._appears_technical():
            gaps["professional_missing"].append("🔗 GitHub profile not provided (technical role indicators found)")
        if not self.portfolio and self._appears_creative():
            gaps["professional_missing"].append("🔗 Portfolio/website not provided (creative role indicators found)")
        
        # === WORK EXPERIENCE GAPS ===
        if not self.work_experiences:
            gaps["critical_missing"].append("❌ No work experience found")
        else:
            for i, exp in enumerate(self.work_experiences, 1):
                issues = []
                if not exp.job_title:
                    issues.append("job title")
                if not exp.company:
                    issues.append("company name")
                if not exp.duration and not (exp.start_date and exp.end_date):
                    issues.append("duration/dates")
                if not exp.responsibilities or len(exp.responsibilities) == 0:
                    issues.append("job responsibilities")
                
                if issues:
                    gaps["detail_gaps"].append(f"📝 Work experience #{i} missing: {', '.join(issues)}")
        
        # === EDUCATION GAPS ===
        if not self.educations:
            gaps["professional_missing"].append("🎓 No education information found")
        else:
            for i, edu in enumerate(self.educations, 1):
                issues = []
                if not edu.degree:
                    issues.append("degree type")
                if not edu.institution:
                    issues.append("institution name")
                if not edu.field_of_study:
                    issues.append("field of study")
                if not edu.graduation_date:
                    issues.append("graduation date")
                
                if issues:
                    gaps["detail_gaps"].append(f"🎓 Education #{i} missing: {', '.join(issues)}")
        
        # === SKILLS GAPS ===
        if not self.skills:
            gaps["critical_missing"].append("❌ No skills found")
        
        # === EXPERIENCE CALCULATION GAPS ===
        if not self.YoE and self.work_experiences:
            gaps["detail_gaps"].append("📊 Total experience calculation failed despite having work history")
        
        return gaps
    
    def _appears_technical(self) -> bool:
        """Check if this appears to be a technical role using LLM-based analysis."""
        try:
            from extractors import RoleTypeExtractor
            
            if not self.skills:
                return False
            
            # Convert work experiences to the format expected by extractor
            work_exp_data = []
            if self.work_experiences:
                for exp in self.work_experiences:
                    exp_dict = {
                        'job_title': exp.job_title,
                        'company': exp.company,
                        'responsibilities': exp.responsibilities or [],
                        'technologies': exp.technologies or []
                    }
                    work_exp_data.append(exp_dict)
            
            # Convert educations to the format expected by extractor
            edu_data = []
            if self.educations:
                for edu in self.educations:
                    edu_dict = {
                        'degree': edu.degree,
                        'field_of_study': edu.field_of_study,
                        'institution': edu.institution
                    }
                    edu_data.append(edu_dict)
            
            # Use LLM-based role type extractor
            role_extractor = RoleTypeExtractor()
            result = role_extractor.analyze_role_type(self.skills, work_exp_data, edu_data, development_mode=False)
            
            analysis = result.get('roletypeanalysis', {})
            return analysis.get('is_technical', False)
            
        except Exception as e:
            # Fallback to keyword matching if LLM extractor fails
            print(f"Role type extraction failed: {e}")
            return RoleTypeExtractor.appears_technical_fallback(self.skills)
    
    def _appears_creative(self) -> bool:
        """Check if this appears to be a creative role using LLM-based analysis."""
        try:
            from extractors import RoleTypeExtractor
            
            if not self.skills:
                return False
            
            # Convert work experiences to the format expected by extractor
            work_exp_data = []
            if self.work_experiences:
                for exp in self.work_experiences:
                    exp_dict = {
                        'job_title': exp.job_title,
                        'company': exp.company,
                        'responsibilities': exp.responsibilities or [],
                        'technologies': exp.technologies or []
                    }
                    work_exp_data.append(exp_dict)
            
            # Convert educations to the format expected by extractor
            edu_data = []
            if self.educations:
                for edu in self.educations:
                    edu_dict = {
                        'degree': edu.degree,
                        'field_of_study': edu.field_of_study,
                        'institution': edu.institution
                    }
                    edu_data.append(edu_dict)
            
            # Use LLM-based role type extractor
            role_extractor = RoleTypeExtractor()
            result = role_extractor.analyze_role_type(self.skills, work_exp_data, edu_data, development_mode=False)
            
            analysis = result.get('roletypeanalysis', {})
            return analysis.get('is_creative', False)
            
        except Exception as e:
            # Fallback to keyword matching if LLM extractor fails
            print(f"Role type extraction failed: {e}")
            return RoleTypeExtractor.appears_creative_fallback(self.skills)
    
    def get_completeness_summary(self) -> Dict[str, Any]:
        """Get a summary of resume completeness for HR dashboard."""
        gaps = self.analyze_resume_gaps()
        
        return {
            "has_critical_gaps": len(gaps["critical_missing"]) > 0,
            "total_gaps": sum(len(gap_list) for gap_list in gaps.values()),
            "sections_complete": {
                "basic_contact": bool(self.name and self.email and self.contact_number),
                "work_experience": len(self.work_experiences) > 0,
                "education": len(self.educations) > 0,
                "skills": len(self.skills) > 0,
                "professional_profiles": bool(self.linkedin)
            },
            "experience_years": self.YoE,
            "skills_count": len(self.skills),
            "jobs_count": len(self.work_experiences),
            "education_count": len(self.educations)
        }
    
    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy format for backward compatibility."""
        # For legacy compatibility, we'll use a simple completeness percentage
        gaps = self.analyze_resume_gaps()
        completeness_score = max(0, 100 - (len(gaps["critical_missing"]) * 20 + len(gaps["professional_missing"]) * 5))
        
        return {
            'name': self.name,
            'email': self.email,
            'phone': self.contact_number,
            'skills': self.skills,
            'education': [edu.model_dump() for edu in self.educations],
            'experience': [exp.model_dump() for exp in self.work_experiences],
            'no_of_pages': self.no_of_pages or 1
        } 