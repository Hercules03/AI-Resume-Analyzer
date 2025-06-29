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
        """Check if this appears to be a technical role based on skills."""
        technical_keywords = ['python', 'java', 'javascript', 'sql', 'aws', 'docker', 'react', 'api', 'database', 'programming', 'software', 'developer', 'engineer']
        skills_text = ' '.join(self.skills).lower()
        return any(keyword in skills_text for keyword in technical_keywords)
    
    def _appears_creative(self) -> bool:
        """Check if this appears to be a creative role based on skills."""
        creative_keywords = ['design', 'photoshop', 'illustrator', 'figma', 'ui', 'ux', 'graphic', 'creative', 'adobe', 'sketch', 'portfolio']
        skills_text = ' '.join(self.skills).lower()
        return any(keyword in skills_text for keyword in creative_keywords)
    
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