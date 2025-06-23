"""
Pydantic schemas for structured metadata extraction
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class PersonalInformation(BaseModel):
    """Schema for personal information extraction"""
    full_name: Optional[str] = Field(description="Full name of the candidate")
    email: Optional[str] = Field(description="Email address")
    phone: Optional[str] = Field(description="Phone number")
    address: Optional[str] = Field(description="Full address")
    city: Optional[str] = Field(description="City")
    state: Optional[str] = Field(description="State/Province")
    country: Optional[str] = Field(description="Country")
    postal_code: Optional[str] = Field(description="Postal/ZIP code")
    linkedin: Optional[str] = Field(description="LinkedIn profile URL")
    github: Optional[str] = Field(description="GitHub profile URL")
    portfolio: Optional[str] = Field(description="Portfolio website URL")
    nationality: Optional[str] = Field(description="Nationality")
    date_of_birth: Optional[str] = Field(description="Date of birth")


class WorkExperience(BaseModel):
    """Schema for individual work experience entry"""
    job_title: str = Field(description="Job title or position")
    company: str = Field(description="Company name")
    location: Optional[str] = Field(description="Job location")
    start_date: Optional[str] = Field(description="Start date (MM/YYYY or similar)")
    end_date: Optional[str] = Field(description="End date (MM/YYYY or 'Present')")
    duration: Optional[str] = Field(description="Duration of employment")
    responsibilities: List[str] = Field(description="List of key responsibilities and achievements")
    technologies: List[str] = Field(description="Technologies, tools, or skills used")
    industry: Optional[str] = Field(description="Industry sector")
    employment_type: Optional[str] = Field(description="Full-time, Part-time, Contract, Internship, etc.")


class Education(BaseModel):
    """Schema for individual education entry"""
    degree: str = Field(description="Degree type (Bachelor's, Master's, PhD, Certificate, etc.)")
    field_of_study: str = Field(description="Major, field of study, or specialization")
    institution: str = Field(description="University, college, or school name")
    location: Optional[str] = Field(description="Institution location")
    graduation_date: Optional[str] = Field(description="Graduation date (MM/YYYY or year)")
    gpa: Optional[str] = Field(description="GPA or grade if mentioned")
    honors: Optional[str] = Field(description="Honors, cum laude, dean's list, etc.")
    relevant_coursework: List[str] = Field(description="Relevant courses or subjects")
    thesis_project: Optional[str] = Field(description="Thesis, capstone, or major project title")


class Skills(BaseModel):
    """Schema for skills categorization"""
    programming_languages: List[str] = Field(description="Programming languages (Python, Java, JavaScript, etc.)")
    frameworks_libraries: List[str] = Field(description="Frameworks and libraries (React, Django, TensorFlow, etc.)")
    databases: List[str] = Field(description="Database technologies (MySQL, PostgreSQL, MongoDB, etc.)")
    tools_platforms: List[str] = Field(description="Development tools and platforms (Git, Docker, AWS, etc.)")
    operating_systems: List[str] = Field(description="Operating systems (Windows, Linux, macOS, etc.)")
    methodologies: List[str] = Field(description="Methodologies and practices (Agile, DevOps, Scrum, etc.)")
    soft_skills: List[str] = Field(description="Soft skills (Leadership, Communication, Problem-solving, etc.)")
    languages: List[str] = Field(description="Spoken languages and proficiency levels")
    domain_knowledge: List[str] = Field(description="Industry-specific knowledge and expertise")


class Certification(BaseModel):
    """Schema for individual certification entry"""
    name: str = Field(description="Certification name")
    issuing_organization: str = Field(description="Organization that issued the certification")
    issue_date: Optional[str] = Field(description="Date when certification was obtained")
    expiry_date: Optional[str] = Field(description="Expiration date if applicable")
    credential_id: Optional[str] = Field(description="Credential ID or license number")
    credential_url: Optional[str] = Field(description="URL to verify the certification")
    status: Optional[str] = Field(description="Active, Expired, In Progress, etc.")


class Projects(BaseModel):
    """Schema for individual project entry"""
    name: str = Field(description="Project name or title")
    description: str = Field(description="Project description")
    technologies: List[str] = Field(description="Technologies and tools used")
    duration: Optional[str] = Field(description="Project duration")
    role: Optional[str] = Field(description="Your role in the project")
    team_size: Optional[str] = Field(description="Team size if mentioned")
    url: Optional[str] = Field(description="Project URL, GitHub link, or demo link")
    achievements: List[str] = Field(description="Key achievements or outcomes")


class AdditionalInformation(BaseModel):
    """Schema for additional information"""
    awards: List[str] = Field(description="Awards and recognitions")
    publications: List[str] = Field(description="Publications, papers, articles")
    volunteer_experience: List[str] = Field(description="Volunteer work and community service")
    professional_memberships: List[str] = Field(description="Professional associations and memberships")
    interests_hobbies: List[str] = Field(description="Personal interests and hobbies")
    references: List[str] = Field(description="Professional references if provided")


class ResumeMetadata(BaseModel):
    """Complete resume metadata schema"""
    personal_information: PersonalInformation
    work_experience: List[WorkExperience]
    education: List[Education]
    skills: Skills
    certifications: List[Certification]
    projects: List[Projects]
    additional_information: AdditionalInformation
    
    # Analysis metadata
    extraction_timestamp: str = Field(description="When the extraction was performed")
    total_experience_years: Optional[float] = Field(description="Calculated total years of experience")
    career_level: Optional[str] = Field(description="Entry, Mid-level, Senior, Executive")
    primary_field: Optional[str] = Field(description="Primary field based on experience and skills") 