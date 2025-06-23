"""
LLM metadata extractor - streamlined without schemas
"""
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import streamlit as st
import requests
from config import LLM_CONFIG

try:
    from langchain_ollama import OllamaLLM
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class LLMMetadataExtractor:
    """LLM-powered metadata extractor for resumes using Ollama"""
    
    def __init__(self, model_name: str = None, base_url: str = None):
        """Initialize the LLM metadata extractor"""
        self.model_name = model_name or LLM_CONFIG['default_model']
        self.base_url = base_url or LLM_CONFIG['default_url']
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
                temperature=LLM_CONFIG['temperature'],
                num_predict=LLM_CONFIG['num_predict'],
                top_k=LLM_CONFIG['top_k'],
                top_p=LLM_CONFIG['top_p']
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
            4. Verify Ollama is accessible at the configured URL
            """)
            return False
    
    def extract_metadata(self, resume_text: str, development_mode: bool = False) -> Optional[Dict[str, Any]]:
        """Extract structured metadata from resume text using LLM"""
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
                metadata = {}
                
                # Extract each section progressively
                metadata['personal_information'] = self._extract_personal_information(resume_text, development_mode)
                metadata['work_experience'] = self._extract_work_experience(resume_text, development_mode)
                metadata['education'] = self._extract_education(resume_text, development_mode)
                metadata['skills'] = self._extract_skills(resume_text, development_mode)
                metadata['certifications'] = self._extract_certifications(resume_text, development_mode)
                metadata['projects'] = self._extract_projects(resume_text, development_mode)
                metadata['additional_information'] = self._extract_additional_information(resume_text, development_mode)
                
                # Calculate analysis metadata
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
        
        return self._execute_extraction("Personal Information", prompt, dev_mode, {})
    
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
        
        return self._execute_extraction("Work Experience", prompt, dev_mode, [])
    
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
        
        return self._execute_extraction("Education", prompt, dev_mode, [])
    
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
        
        default_skills = {
            "programming_languages": [], "frameworks_libraries": [], "databases": [],
            "tools_platforms": [], "operating_systems": [], "methodologies": [],
            "soft_skills": [], "languages": [], "domain_knowledge": []
        }
        
        result = self._execute_extraction("Skills", prompt, dev_mode, default_skills)
        
        # Ensure all required keys exist
        for key in default_skills:
            if key not in result:
                result[key] = []
        
        return result
    
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
        
        return self._execute_extraction("Certifications", prompt, dev_mode, [])
    
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
        
        return self._execute_extraction("Projects", prompt, dev_mode, [])
    
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
        
        default_additional = {
            "awards": [], "publications": [], "volunteer_experience": [],
            "professional_memberships": [], "interests_hobbies": [], "references": []
        }
        
        result = self._execute_extraction("Additional Information", prompt, dev_mode, default_additional)
        
        # Ensure all required keys exist
        for key in default_additional:
            if key not in result:
                result[key] = []
        
        return result
    
    def _execute_extraction(self, section_name: str, prompt: str, dev_mode: bool, default_value) -> Any:
        """Execute LLM extraction with error handling"""
        try:
            if dev_mode:
                st.write(f"🔍 **Extracting {section_name}...**")
            
            response = self.llm.invoke(prompt)
            
            if dev_mode:
                with st.expander(f"🔍 {section_name} - Raw LLM Response"):
                    st.code(response)
            
            # Clean and parse JSON
            json_text = self._clean_json_response(response)
            parsed_result = json.loads(json_text)
            
            if dev_mode:
                if isinstance(parsed_result, list):
                    st.success(f"✅ {section_name} extracted: {len(parsed_result)} entries")
                elif isinstance(parsed_result, dict):
                    if section_name == "Skills":
                        total_skills = sum(len(v) for v in parsed_result.values() if isinstance(v, list))
                        st.success(f"✅ {section_name} extracted: {total_skills} total skills")
                    else:
                        filled_fields = len([v for v in parsed_result.values() if v])
                        st.success(f"✅ {section_name} extracted: {filled_fields} fields filled")
                
            return parsed_result
            
        except Exception as e:
            if dev_mode:
                st.error(f"❌ {section_name} extraction failed: {str(e)}")
            return default_value
    
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