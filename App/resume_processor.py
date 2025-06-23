"""
Resume processor using specialized extractors for concurrent processing.
"""
import concurrent.futures
from typing import Dict, Any
import streamlit as st
from pdf_processing import pdf_processor
from extractors import (
    ProfileExtractor, SkillsExtractor, EducationExtractor,
    ExperienceExtractor, YoeExtractor
)
from models import Resume


class ResumeProcessor:
    """Class for processing resumes and extracting information using specialized extractors."""
    
    def __init__(self, resume_dir="./Uploaded_Resumes", output_dir="./Results"):
        """
        Initialize the resume processor.
        
        Args:
            resume_dir: Directory where resumes are stored
            output_dir: Directory where results will be saved
        """
        self.resume_dir = resume_dir
        self.output_dir = output_dir
        
        # Create specialized extractors
        self.profile_extractor = ProfileExtractor()
        self.skills_extractor = SkillsExtractor()
        self.education_extractor = EducationExtractor()
        self.experience_extractor = ExperienceExtractor()
        self.yoe_extractor = YoeExtractor()
    
    def process_resume(self, pdf_file_path: str, development_mode: bool = False) -> Resume:
        """
        Process a single resume file using concurrent extraction.
        
        Args:
            pdf_file_path: Path to the PDF resume file
            development_mode: Whether to show detailed extraction process
            
        Returns:
            Resume object with all extracted information
        """
        try:
            # Extract text from the resume
            if development_mode:
                st.info("📄 **Extracting text from PDF...**")
            
            extracted_text = pdf_processor.extract_text_hybrid(pdf_file_path, development_mode)
            
            if not extracted_text or len(extracted_text.strip()) < 100:
                st.warning("⚠️ Resume text extraction failed or text too short")
                return self._create_empty_resume(pdf_file_path)
            
            if development_mode:
                st.success(f"✅ **Text extracted successfully** ({len(extracted_text)} characters)")
                with st.expander("📄 Extracted Text Preview"):
                    st.text(extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text)
            
            # Extract information concurrently using specialized extractors
            if development_mode:
                st.info("🔄 **Starting concurrent extraction with specialized extractors...**")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                # Submit all extraction tasks concurrently
                future_profile = executor.submit(
                    self.profile_extractor.extract, extracted_text, development_mode
                )
                future_skills = executor.submit(
                    self.skills_extractor.extract, extracted_text, development_mode
                )
                future_education = executor.submit(
                    self.education_extractor.extract, extracted_text, development_mode
                )
                future_experience = executor.submit(
                    self.experience_extractor.extract, extracted_text, development_mode
                )
                future_yoe = executor.submit(
                    self.yoe_extractor.extract, extracted_text, development_mode
                )
                
                # Collect results with error handling
                results = {}
                
                try:
                    results['profile'] = future_profile.result(timeout=30)
                except Exception as e:
                    if development_mode:
                        st.error(f"❌ Profile extraction failed: {e}")
                    results['profile'] = {'profile': {}}
                
                try:
                    results['skills'] = future_skills.result(timeout=30)
                except Exception as e:
                    if development_mode:
                        st.error(f"❌ Skills extraction failed: {e}")
                    results['skills'] = {'skills': {}}
                
                try:
                    results['education'] = future_education.result(timeout=30)
                except Exception as e:
                    if development_mode:
                        st.error(f"❌ Education extraction failed: {e}")
                    results['education'] = {'educationlist': {'educations': []}}
                
                try:
                    results['experience'] = future_experience.result(timeout=30)
                except Exception as e:
                    if development_mode:
                        st.error(f"❌ Experience extraction failed: {e}")
                    results['experience'] = {'workexperiencelist': {'work_experiences': []}}
                
                try:
                    results['yoe'] = future_yoe.result(timeout=30)
                except Exception as e:
                    if development_mode:
                        st.error(f"❌ YoE extraction failed: {e}")
                    results['yoe'] = {'yoe': {}}
            
            if development_mode:
                st.success("✅ **Concurrent extraction completed!**")
                
                # Show extraction summary
                st.subheader("📊 **Extraction Summary**")
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    profile_fields = len([v for v in results['profile'].get('profile', {}).values() if v])
                    st.metric("Profile Fields", profile_fields)
                
                with col2:
                    skills_data = results['skills'].get('skills', {})
                    total_skills = sum(len(v) for v in skills_data.values() if isinstance(v, list))
                    st.metric("Total Skills", total_skills)
                
                with col3:
                    education_count = len(results['education'].get('educationlist', {}).get('educations', []))
                    st.metric("Education Entries", education_count)
                
                with col4:
                    experience_count = len(results['experience'].get('workexperiencelist', {}).get('work_experiences', []))
                    st.metric("Work Experiences", experience_count)
                
                with col5:
                    yoe_years = results['yoe'].get('yoe', {}).get('total_years', 0)
                    st.metric("Years of Experience", f"{yoe_years or 0}")
            
            # Create a Resume object from the extracted information
            resume = Resume.from_extractors_output(
                profile=results['profile'],
                skills=results['skills'],
                education=results['education'],
                experience=results['experience'],
                yoe=results['yoe'],
                pdf_file_path=pdf_file_path
            )
            
            if development_mode:
                st.success("✅ **Resume object created successfully!**")
                st.json({
                    "name": resume.name,
                    "email": resume.email,
                    "contact_number": resume.contact_number,
                    "skills_count": len(resume.skills),
                    "education_count": len(resume.educations),
                    "experience_count": len(resume.work_experiences),
                    "years_of_experience": resume.YoE,
                    "resume_score": resume.resume_score
                })
            
            return resume
            
        except Exception as e:
            if development_mode:
                st.error(f"❌ **Resume processing failed:** {str(e)}")
                st.exception(e)
            else:
                st.error("❌ Resume processing failed. Please try again.")
            
            return self._create_empty_resume(pdf_file_path)
    
    def _create_empty_resume(self, pdf_file_path: str) -> Resume:
        """Create an empty resume object as fallback."""
        return Resume(
            name="Unknown",
            contact_number=None,
            email=None,
            skills=[],
            educations=[],
            work_experiences=[],
            YoE=None,
            file_path=pdf_file_path,
            resume_score=0
        )
    
    def get_extraction_capabilities(self) -> Dict[str, str]:
        """Get information about extraction capabilities."""
        return {
            "Profile Information": "Name, contact details, online profiles",
            "Skills": "Categorized technical and soft skills",
            "Education": "Academic qualifications and details",
            "Work Experience": "Professional background and achievements",
            "Years of Experience": "Career level and experience analysis",
            "Concurrent Processing": "Fast parallel extraction",
            "Error Handling": "Robust processing with fallbacks"
        } 