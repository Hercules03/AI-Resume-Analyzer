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
    
    # Years of Experience
    YoE: Optional[str] = None
    
    # Additional metadata
    file_path: Optional[str] = None
    extraction_timestamp: Optional[str] = None
    resume_score: Optional[int] = None
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
        education_list = education.get('educations', [])
        educations = [Education(**edu) for edu in education_list if isinstance(edu, dict)]
        
        # Extract work experience data
        experience_list = experience.get('work_experiences', [])
        work_experiences = [WorkExperience(**exp) for exp in experience_list if isinstance(exp, dict)]
        
        # Extract YoE data
        yoe_data = yoe.get('yoe', {})
        years_of_experience = yoe_data.get('total_years')
        yoe_str = f"{years_of_experience} years" if years_of_experience else None
        
        return cls(
            name=profile_data.get('name'),
            contact_number=profile_data.get('contact_number'),
            email=profile_data.get('email'),
            skills=all_skills,
            educations=educations,
            work_experiences=work_experiences,
            YoE=yoe_str,
            file_path=pdf_file_path,
            extraction_timestamp=datetime.now().isoformat(),
            resume_score=cls._calculate_resume_score(profile_data, all_skills, educations, work_experiences),
            no_of_pages=1  # Default, can be calculated from PDF
        )
    
    @staticmethod
    def _calculate_resume_score(profile: Dict, skills: List, educations: List, experiences: List) -> int:
        """Calculate a resume completeness score."""
        score = 0
        
        # Profile completeness (30 points)
        if profile.get('name'): score += 10
        if profile.get('email'): score += 10
        if profile.get('contact_number'): score += 10
        
        # Skills (25 points)
        if len(skills) > 0: score += 10
        if len(skills) >= 5: score += 10
        if len(skills) >= 10: score += 5
        
        # Education (20 points)
        if len(educations) > 0: score += 20
        
        # Experience (25 points)
        if len(experiences) > 0: score += 15
        if len(experiences) >= 2: score += 10
        
        return min(score, 100)
    
    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy format for backward compatibility."""
        return {
            'name': self.name,
            'email': self.email,
            'mobile_number': self.contact_number,
            'skills': self.skills,
            'education': [edu.dict() for edu in self.educations],
            'experience': [exp.dict() for exp in self.work_experiences],
            'no_of_pages': self.no_of_pages or 1,
            'total_experience': self.YoE
        } 