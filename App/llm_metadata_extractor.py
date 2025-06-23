import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import streamlit as st

try:
    from langchain_ollama import OllamaLLM
    from langchain.prompts import PromptTemplate
    from langchain.schema import OutputParserException
    from langchain.output_parsers import PydanticOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


# =============================================================================
# PYDANTIC SCHEMAS FOR STRUCTURED METADATA EXTRACTION
# =============================================================================

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


# =============================================================================
# LLM METADATA EXTRACTOR CLASS
# =============================================================================

class LLMMetadataExtractor:
    """LLM-powered metadata extractor for resumes using Ollama and Gemma"""
    
    def __init__(self, model_name: str = "gemma3:27b", base_url: str = "http://localhost:11434"):
        """
        Initialize the LLM metadata extractor
        
        Args:
            model_name: Ollama model name (default: gemma3:27b)
            base_url: Ollama server URL (default: http://localhost:11434)
        """
        self.model_name = model_name
        self.base_url = base_url
        self.llm = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the Ollama LLM connection"""
        if not LANGCHAIN_AVAILABLE:
            st.error("❌ LangChain not available. Please install: pip install langchain langchain-ollama")
            return False
        
        try:
            self.llm = OllamaLLM(
                model=self.model_name,
                base_url=self.base_url,
                temperature=0.1,  # Low temperature for consistent extraction
                num_predict=8192,  # Allow longer responses
                top_k=10,
                top_p=0.9
            )
            
            # Test connection
            test_response = self.llm.invoke("Test connection")
            if test_response:
                st.success(f"✅ LLM Connection established: {self.model_name}")
                return True
            else:
                st.error("❌ LLM connection test failed")
                return False
                
        except Exception as e:
            st.error(f"❌ Failed to initialize LLM: {str(e)}")
            st.info("""
            **Troubleshooting:**
            1. Make sure Ollama is running: `ollama serve`
            2. Pull the model: `ollama pull gemma2:27b`
            3. Check if the model name is correct
            4. Verify Ollama is accessible at http://localhost:11434
            """)
            return False
    
    def extract_metadata(self, resume_text: str, development_mode: bool = False) -> Optional[Dict[str, Any]]:
        """
        Extract structured metadata from resume text using LLM
        
        Args:
            resume_text: Raw text from the resume
            development_mode: Show detailed extraction process
            
        Returns:
            Dictionary containing structured metadata or None if extraction fails
        """
        if not self.llm:
            st.error("❌ LLM not initialized")
            return None
        
        if not resume_text or len(resume_text.strip()) < 100:
            st.warning("⚠️ Resume text too short for meaningful extraction")
            return None
        
        try:
            if development_mode:
                st.info("🤖 **LLM Metadata Extraction Process**")
                
            with st.spinner("🧠 Analyzing resume with AI..."):
                # Extract each section progressively
                metadata = {}
                
                # 1. Personal Information
                personal_info = self._extract_personal_information(resume_text, development_mode)
                metadata['personal_information'] = personal_info
                
                # 2. Work Experience
                work_exp = self._extract_work_experience(resume_text, development_mode)
                metadata['work_experience'] = work_exp
                
                # 3. Education
                education = self._extract_education(resume_text, development_mode)
                metadata['education'] = education
                
                # 4. Skills
                skills = self._extract_skills(resume_text, development_mode)
                metadata['skills'] = skills
                
                # 5. Certifications
                certifications = self._extract_certifications(resume_text, development_mode)
                metadata['certifications'] = certifications
                
                # 6. Projects
                projects = self._extract_projects(resume_text, development_mode)
                metadata['projects'] = projects
                
                # 7. Additional Information
                additional_info = self._extract_additional_information(resume_text, development_mode)
                metadata['additional_information'] = additional_info
                
                # 8. Calculate analysis metadata
                analysis_metadata = self._calculate_analysis_metadata(metadata)
                metadata.update(analysis_metadata)
                
                if development_mode:
                    st.success("✅ **Metadata extraction completed successfully!**")
                
                return metadata
                
        except Exception as e:
            st.error(f"❌ Metadata extraction failed: {str(e)}")
            if development_mode:
                st.exception(e)
            return None
    
    def _extract_personal_information(self, resume_text: str, dev_mode: bool = False) -> Dict[str, Any]:
        """Extract personal information using LLM"""
        
        prompt = f"""
        Extract personal information from the following resume text. Return ONLY a valid JSON object with the exact structure shown below. Do not include any additional text, explanations, or markdown formatting.

        Required JSON structure:
        {{
            "full_name": "Full name of the candidate",
            "email": "Email address",
            "phone": "Phone number",
            "address": "Full address",
            "city": "City",
            "state": "State/Province", 
            "country": "Country",
            "postal_code": "Postal/ZIP code",
            "linkedin": "LinkedIn profile URL",
            "github": "GitHub profile URL",
            "portfolio": "Portfolio website URL",
            "nationality": "Nationality",
            "date_of_birth": "Date of birth"
        }}

        Use null for any field that cannot be found in the resume.

        Resume text:
        {resume_text[:3000]}
        """
        
        try:
            if dev_mode:
                st.write("🔍 **Extracting Personal Information...**")
            
            response = self.llm.invoke(prompt)
            
            if dev_mode:
                with st.expander("🔍 Personal Info - Raw LLM Response"):
                    st.code(response)
            
            # Clean and parse JSON
            json_text = self._clean_json_response(response)
            personal_info = json.loads(json_text)
            
            if dev_mode:
                st.success("✅ Personal information extracted")
                
            return personal_info
            
        except Exception as e:
            if dev_mode:
                st.error(f"❌ Personal info extraction failed: {str(e)}")
            return {}
    
    def _extract_work_experience(self, resume_text: str, dev_mode: bool = False) -> List[Dict[str, Any]]:
        """Extract work experience using LLM"""
        
        prompt = f"""
        Extract work experience from the following resume text. Return ONLY a valid JSON array of objects with the exact structure shown below. Do not include any additional text, explanations, or markdown formatting.

        Required JSON structure:
        [
            {{
                "job_title": "Job title or position",
                "company": "Company name",
                "location": "Job location",
                "start_date": "Start date (MM/YYYY or similar)",
                "end_date": "End date (MM/YYYY or 'Present')",
                "duration": "Duration of employment",
                "responsibilities": ["List", "of", "key", "responsibilities"],
                "technologies": ["Technologies", "used"],
                "industry": "Industry sector",
                "employment_type": "Full-time/Part-time/Contract/Internship"
            }}
        ]

        Return an empty array [] if no work experience is found.

        Resume text:
        {resume_text[:4000]}
        """
        
        try:
            if dev_mode:
                st.write("🔍 **Extracting Work Experience...**")
            
            response = self.llm.invoke(prompt)
            
            if dev_mode:
                with st.expander("🔍 Work Experience - Raw LLM Response"):
                    st.code(response)
            
            # Clean and parse JSON
            json_text = self._clean_json_response(response)
            work_experience = json.loads(json_text)
            
            if not isinstance(work_experience, list):
                work_experience = []
            
            if dev_mode:
                st.success(f"✅ Work experience extracted: {len(work_experience)} entries")
                
            return work_experience
            
        except Exception as e:
            if dev_mode:
                st.error(f"❌ Work experience extraction failed: {str(e)}")
            return []
    
    def _extract_education(self, resume_text: str, dev_mode: bool = False) -> List[Dict[str, Any]]:
        """Extract education using LLM"""
        
        prompt = f"""
        Extract education information from the following resume text. Return ONLY a valid JSON array of objects with the exact structure shown below. Do not include any additional text, explanations, or markdown formatting.

        Required JSON structure:
        [
            {{
                "degree": "Degree type",
                "field_of_study": "Major or field of study",
                "institution": "University or school name",
                "location": "Institution location",
                "graduation_date": "Graduation date",
                "gpa": "GPA if mentioned",
                "honors": "Honors or distinctions",
                "relevant_coursework": ["List", "of", "relevant", "courses"],
                "thesis_project": "Thesis or project title"
            }}
        ]

        Return an empty array [] if no education is found.

        Resume text:
        {resume_text[:3000]}
        """
        
        try:
            if dev_mode:
                st.write("🔍 **Extracting Education...**")
            
            response = self.llm.invoke(prompt)
            
            if dev_mode:
                with st.expander("🔍 Education - Raw LLM Response"):
                    st.code(response)
            
            # Clean and parse JSON
            json_text = self._clean_json_response(response)
            education = json.loads(json_text)
            
            if not isinstance(education, list):
                education = []
            
            if dev_mode:
                st.success(f"✅ Education extracted: {len(education)} entries")
                
            return education
            
        except Exception as e:
            if dev_mode:
                st.error(f"❌ Education extraction failed: {str(e)}")
            return []
    
    def _extract_skills(self, resume_text: str, dev_mode: bool = False) -> Dict[str, List[str]]:
        """Extract and categorize skills using LLM"""
        
        prompt = f"""
        Extract and categorize skills from the following resume text. Return ONLY a valid JSON object with the exact structure shown below. Do not include any additional text, explanations, or markdown formatting.

        Required JSON structure:
        {{
            "programming_languages": ["Python", "Java", "JavaScript"],
            "frameworks_libraries": ["React", "Django", "TensorFlow"],
            "databases": ["MySQL", "PostgreSQL", "MongoDB"],
            "tools_platforms": ["Git", "Docker", "AWS"],
            "operating_systems": ["Windows", "Linux", "macOS"],
            "methodologies": ["Agile", "DevOps", "Scrum"],
            "soft_skills": ["Leadership", "Communication", "Problem-solving"],
            "languages": ["English (Native)", "Spanish (Intermediate)"],
            "domain_knowledge": ["Machine Learning", "Web Development"]
        }}

        Use empty arrays [] for categories where no skills are found.

        Resume text:
        {resume_text[:4000]}
        """
        
        try:
            if dev_mode:
                st.write("🔍 **Extracting Skills...**")
            
            response = self.llm.invoke(prompt)
            
            if dev_mode:
                with st.expander("🔍 Skills - Raw LLM Response"):
                    st.code(response)
            
            # Clean and parse JSON
            json_text = self._clean_json_response(response)
            skills = json.loads(json_text)
            
            # Ensure all required keys exist
            required_keys = [
                "programming_languages", "frameworks_libraries", "databases",
                "tools_platforms", "operating_systems", "methodologies",
                "soft_skills", "languages", "domain_knowledge"
            ]
            
            for key in required_keys:
                if key not in skills:
                    skills[key] = []
            
            if dev_mode:
                total_skills = sum(len(skills[key]) for key in skills)
                st.success(f"✅ Skills extracted: {total_skills} total skills")
                
            return skills
            
        except Exception as e:
            if dev_mode:
                st.error(f"❌ Skills extraction failed: {str(e)}")
            return {key: [] for key in [
                "programming_languages", "frameworks_libraries", "databases",
                "tools_platforms", "operating_systems", "methodologies",
                "soft_skills", "languages", "domain_knowledge"
            ]}
    
    def _extract_certifications(self, resume_text: str, dev_mode: bool = False) -> List[Dict[str, Any]]:
        """Extract certifications using LLM"""
        
        prompt = f"""
        Extract certifications from the following resume text. Return ONLY a valid JSON array of objects with the exact structure shown below. Do not include any additional text, explanations, or markdown formatting.

        Required JSON structure:
        [
            {{
                "name": "Certification name",
                "issuing_organization": "Organization that issued",
                "issue_date": "Date obtained",
                "expiry_date": "Expiration date if applicable",
                "credential_id": "Credential ID if provided",
                "credential_url": "Verification URL if provided",
                "status": "Active/Expired/In Progress"
            }}
        ]

        Return an empty array [] if no certifications are found.

        Resume text:
        {resume_text[:3000]}
        """
        
        try:
            if dev_mode:
                st.write("🔍 **Extracting Certifications...**")
            
            response = self.llm.invoke(prompt)
            
            if dev_mode:
                with st.expander("🔍 Certifications - Raw LLM Response"):
                    st.code(response)
            
            # Clean and parse JSON
            json_text = self._clean_json_response(response)
            certifications = json.loads(json_text)
            
            if not isinstance(certifications, list):
                certifications = []
            
            if dev_mode:
                st.success(f"✅ Certifications extracted: {len(certifications)} entries")
                
            return certifications
            
        except Exception as e:
            if dev_mode:
                st.error(f"❌ Certifications extraction failed: {str(e)}")
            return []
    
    def _extract_projects(self, resume_text: str, dev_mode: bool = False) -> List[Dict[str, Any]]:
        """Extract projects using LLM"""
        
        prompt = f"""
        Extract projects from the following resume text. Return ONLY a valid JSON array of objects with the exact structure shown below. Do not include any additional text, explanations, or markdown formatting.

        Required JSON structure:
        [
            {{
                "name": "Project name",
                "description": "Project description",
                "technologies": ["List", "of", "technologies"],
                "duration": "Project duration",
                "role": "Your role in the project",
                "team_size": "Team size if mentioned",
                "url": "Project URL or GitHub link",
                "achievements": ["Key", "achievements"]
            }}
        ]

        Return an empty array [] if no projects are found.

        Resume text:
        {resume_text[:4000]}
        """
        
        try:
            if dev_mode:
                st.write("🔍 **Extracting Projects...**")
            
            response = self.llm.invoke(prompt)
            
            if dev_mode:
                with st.expander("🔍 Projects - Raw LLM Response"):
                    st.code(response)
            
            # Clean and parse JSON
            json_text = self._clean_json_response(response)
            projects = json.loads(json_text)
            
            if not isinstance(projects, list):
                projects = []
            
            if dev_mode:
                st.success(f"✅ Projects extracted: {len(projects)} entries")
                
            return projects
            
        except Exception as e:
            if dev_mode:
                st.error(f"❌ Projects extraction failed: {str(e)}")
            return []
    
    def _extract_additional_information(self, resume_text: str, dev_mode: bool = False) -> Dict[str, List[str]]:
        """Extract additional information using LLM"""
        
        prompt = f"""
        Extract additional information from the following resume text. Return ONLY a valid JSON object with the exact structure shown below. Do not include any additional text, explanations, or markdown formatting.

        Required JSON structure:
        {{
            "awards": ["List", "of", "awards"],
            "publications": ["List", "of", "publications"],
            "volunteer_experience": ["List", "of", "volunteer", "work"],
            "professional_memberships": ["List", "of", "memberships"],
            "interests_hobbies": ["List", "of", "interests"],
            "references": ["List", "of", "references"]
        }}

        Use empty arrays [] for categories where no information is found.

        Resume text:
        {resume_text[:3000]}
        """
        
        try:
            if dev_mode:
                st.write("🔍 **Extracting Additional Information...**")
            
            response = self.llm.invoke(prompt)
            
            if dev_mode:
                with st.expander("🔍 Additional Info - Raw LLM Response"):
                    st.code(response)
            
            # Clean and parse JSON
            json_text = self._clean_json_response(response)
            additional_info = json.loads(json_text)
            
            # Ensure all required keys exist
            required_keys = [
                "awards", "publications", "volunteer_experience",
                "professional_memberships", "interests_hobbies", "references"
            ]
            
            for key in required_keys:
                if key not in additional_info:
                    additional_info[key] = []
            
            if dev_mode:
                total_items = sum(len(additional_info[key]) for key in additional_info)
                st.success(f"✅ Additional information extracted: {total_items} items")
                
            return additional_info
            
        except Exception as e:
            if dev_mode:
                st.error(f"❌ Additional information extraction failed: {str(e)}")
            return {key: [] for key in [
                "awards", "publications", "volunteer_experience",
                "professional_memberships", "interests_hobbies", "references"
            ]}
    
    def _calculate_analysis_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate analysis metadata from extracted data"""
        
        analysis = {
            "extraction_timestamp": datetime.now().isoformat(),
            "total_experience_years": None,
            "career_level": None,
            "primary_field": None
        }
        
        try:
            # Calculate total experience years
            work_exp = metadata.get('work_experience', [])
            total_months = 0
            
            for job in work_exp:
                duration = job.get('duration', '')
                # Simple parsing - can be enhanced
                if 'year' in duration.lower():
                    years = re.findall(r'(\d+)', duration)
                    if years:
                        total_months += int(years[0]) * 12
                elif 'month' in duration.lower():
                    months = re.findall(r'(\d+)', duration)
                    if months:
                        total_months += int(months[0])
            
            if total_months > 0:
                analysis["total_experience_years"] = round(total_months / 12, 1)
            
            # Determine career level
            exp_years = analysis["total_experience_years"] or 0
            if exp_years < 2:
                analysis["career_level"] = "Entry Level"
            elif exp_years < 5:
                analysis["career_level"] = "Mid Level"
            elif exp_years < 10:
                analysis["career_level"] = "Senior Level"
            else:
                analysis["career_level"] = "Executive Level"
            
            # Determine primary field based on skills and experience
            skills = metadata.get('skills', {})
            all_skills = []
            for skill_category in skills.values():
                if isinstance(skill_category, list):
                    all_skills.extend(skill_category)
            
            # Simple field classification
            if any('python' in skill.lower() or 'data' in skill.lower() or 'machine learning' in skill.lower() for skill in all_skills):
                analysis["primary_field"] = "Data Science & Analytics"
            elif any('react' in skill.lower() or 'javascript' in skill.lower() or 'web' in skill.lower() for skill in all_skills):
                analysis["primary_field"] = "Web Development"
            elif any('java' in skill.lower() or 'spring' in skill.lower() or 'backend' in skill.lower() for skill in all_skills):
                analysis["primary_field"] = "Backend Development"
            elif any('mobile' in skill.lower() or 'android' in skill.lower() or 'ios' in skill.lower() for skill in all_skills):
                analysis["primary_field"] = "Mobile Development"
            elif any('devops' in skill.lower() or 'aws' in skill.lower() or 'docker' in skill.lower() for skill in all_skills):
                analysis["primary_field"] = "DevOps & Cloud"
            else:
                analysis["primary_field"] = "General IT"
                
        except Exception as e:
            pass  # Keep default values
        
        return analysis
    
    def _clean_json_response(self, response: str) -> str:
        """Clean LLM response to extract valid JSON"""
        
        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        # Remove any text before the first { or [
        start_char = min(
            (response.find('{') if response.find('{') != -1 else len(response)),
            (response.find('[') if response.find('[') != -1 else len(response))
        )
        
        if start_char < len(response):
            response = response[start_char:]
        
        # Find the last } or ]
        last_brace = response.rfind('}')
        last_bracket = response.rfind(']')
        end_char = max(last_brace, last_bracket)
        
        if end_char != -1:
            response = response[:end_char + 1]
        
        return response.strip()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_metadata_for_display(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Format metadata for better display in Streamlit"""
    
    if not metadata:
        return {}
    
    formatted = {}
    
    # Personal Information
    personal = metadata.get('personal_information', {})
    if personal:
        formatted['Personal Information'] = {
            k.replace('_', ' ').title(): v 
            for k, v in personal.items() 
            if v is not None and v != ""
        }
    
    # Work Experience
    work_exp = metadata.get('work_experience', [])
    if work_exp:
        formatted['Work Experience'] = []
        for i, job in enumerate(work_exp, 1):
            job_formatted = {
                f"Position {i}": {
                    k.replace('_', ' ').title(): v 
                    for k, v in job.items() 
                    if v is not None and v != "" and v != []
                }
            }
            formatted['Work Experience'].append(job_formatted)
    
    # Education
    education = metadata.get('education', [])
    if education:
        formatted['Education'] = []
        for i, edu in enumerate(education, 1):
            edu_formatted = {
                f"Education {i}": {
                    k.replace('_', ' ').title(): v 
                    for k, v in edu.items() 
                    if v is not None and v != "" and v != []
                }
            }
            formatted['Education'].append(edu_formatted)
    
    # Skills
    skills = metadata.get('skills', {})
    if skills:
        formatted['Skills'] = {
            k.replace('_', ' ').title(): v 
            for k, v in skills.items() 
            if v and len(v) > 0
        }
    
    # Certifications
    certs = metadata.get('certifications', [])
    if certs:
        formatted['Certifications'] = []
        for i, cert in enumerate(certs, 1):
            cert_formatted = {
                f"Certification {i}": {
                    k.replace('_', ' ').title(): v 
                    for k, v in cert.items() 
                    if v is not None and v != ""
                }
            }
            formatted['Certifications'].append(cert_formatted)
    
    # Projects
    projects = metadata.get('projects', [])
    if projects:
        formatted['Projects'] = []
        for i, project in enumerate(projects, 1):
            project_formatted = {
                f"Project {i}": {
                    k.replace('_', ' ').title(): v 
                    for k, v in project.items() 
                    if v is not None and v != "" and v != []
                }
            }
            formatted['Projects'].append(project_formatted)
    
    # Additional Information
    additional = metadata.get('additional_information', {})
    if additional:
        formatted['Additional Information'] = {
            k.replace('_', ' ').title(): v 
            for k, v in additional.items() 
            if v and len(v) > 0
        }
    
    # Analysis Summary
    analysis = {
        'Extraction Timestamp': metadata.get('extraction_timestamp'),
        'Total Experience Years': metadata.get('total_experience_years'),
        'Career Level': metadata.get('career_level'),
        'Primary Field': metadata.get('primary_field')
    }
    
    formatted['Analysis Summary'] = {
        k: v for k, v in analysis.items() 
        if v is not None
    }
    
    return formatted


def export_metadata_to_json(metadata: Dict[str, Any], filename: str = None) -> str:
    """Export metadata to JSON string"""
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resume_metadata_{timestamp}.json"
    
    try:
        json_str = json.dumps(metadata, indent=2, ensure_ascii=False)
        return json_str
    except Exception as e:
        return f"Error exporting to JSON: {str(e)}" 