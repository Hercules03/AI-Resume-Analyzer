"""
Resume processor using specialized extractors for sequential processing.

Key optimizations:
- Profile and Education extractors use only first page text for better focus and efficiency
- Skills, Experience, and YoE extractors use full document text for comprehensive analysis
"""
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
        Process a single resume file using sequential extraction.
        
        Args:
            pdf_file_path: Path to the PDF resume file
            development_mode: Whether to show detailed extraction process
            
        Returns:
            Resume object with all extracted information
        """
        try:
            # Extract text from the resume
            if development_mode:
                st.info("**Extracting text from PDF...**")
            
            extracted_text = pdf_processor.extract_text_hybrid(pdf_file_path, development_mode)
            
            if not extracted_text or len(extracted_text.strip()) < 100:
                st.warning("Resume text extraction failed or text too short")
                return self._create_empty_resume(pdf_file_path)
            
            # Extract first page text for profile extraction (more efficient and focused)
            first_page_text = pdf_processor.extract_first_page_with_pymupdf4llm(pdf_file_path)
            
            if development_mode:
                st.success(f"**Text extracted successfully** ({len(extracted_text)} characters)")
                if first_page_text:
                    st.info(f"**First page text extracted** ({len(first_page_text)} characters) - for profile and education extraction")
                with st.expander("Extracted Text Preview"):
                    st.text(extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text)
                if first_page_text:
                    with st.expander("First Page Text Preview"):
                        st.text(first_page_text[:500] + "..." if len(first_page_text) > 500 else first_page_text)
            
            # Process extractors
            if development_mode:
                st.info("**Starting extraction with specialized extractors...**")
            
            results = self._process_sequential(extracted_text, first_page_text, development_mode)
            
            if development_mode:
                st.success("**Extraction completed!**")
                
                # Show extraction summary
                st.subheader("**Extraction Summary**")
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
                st.success("**Resume object created successfully!**")
                st.json({
                    "name": resume.name,
                    "email": resume.email,
                    "contact_number": resume.contact_number,
                    "skills_count": len(resume.skills),
                    "education_count": len(resume.educations),
                    "experience_count": len(resume.work_experiences),
                    "years_of_experience": resume.YoE,
                })
            
            return resume
            
        except Exception as e:
            if development_mode:
                st.error(f"**Resume processing failed:** {str(e)}")
                st.exception(e)
            else:
                st.error("Resume processing failed. Please try again.")
            
            return self._create_empty_resume(pdf_file_path)
    
    def _process_sequential(self, extracted_text: str, first_page_text: str, development_mode: bool) -> Dict[str, Any]:
        """
        Process extractors sequentially (optimized for local Ollama setups).
        
        Args:
            extracted_text: The full extracted resume text
            first_page_text: The extracted first page text (for profile extraction)
            development_mode: Whether to show detailed process
            
        Returns:
            Dictionary containing all extraction results
        """
        results = {}
        extractors = [
            ("profile", self.profile_extractor),
            ("skills", self.skills_extractor),
            ("education", self.education_extractor),
            ("experience", self.experience_extractor),
            ("yoe", self.yoe_extractor)
        ]
        
        # Process each extractor one by one
        for extractor_name, extractor in extractors:
            try:
                if development_mode:
                    st.info(f"Processing {extractor_name.title()} extractor...")
                
                # Use first page text for profile and education extraction, full text for others
                if extractor_name in ["profile", "education"] and first_page_text:
                    if development_mode:
                        st.info(f"Using first page text for {extractor_name} extraction (more focused and efficient)")
                    result = extractor.extract(first_page_text, development_mode)
                elif extractor_name in ["profile", "education"] and not first_page_text:
                    if development_mode:
                        st.warning(f"First page extraction failed, using full text for {extractor_name} extraction")
                    result = extractor.extract(extracted_text, development_mode)
                else:
                    result = extractor.extract(extracted_text, development_mode)
                
                results[extractor_name] = result
                
                if development_mode:
                    st.success(f"{extractor_name.title()} extraction completed")
                    
            except Exception as e:
                if development_mode:
                    st.error(f"{extractor_name.title()} extraction failed: {e}")
                
                # Provide fallback empty results
                if extractor_name == 'profile':
                    results[extractor_name] = {'profile': {}}
                elif extractor_name == 'skills':
                    results[extractor_name] = {'skills': {}}
                elif extractor_name == 'education':
                    results[extractor_name] = {'educationlist': {'educations': []}}
                elif extractor_name == 'experience':
                    results[extractor_name] = {'workexperiencelist': {'work_experiences': []}}
                elif extractor_name == 'yoe':
                    results[extractor_name] = {'yoe': {}}
        
        return results
    
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
        )
    
    def get_extraction_capabilities(self) -> Dict[str, str]:
        """Get information about extraction capabilities."""
        return {
            "profile": "Personal information and contact details",
            "skills": "Technical and soft skills categorization",
            "education": "Academic background and qualifications",
            "experience": "Work history and responsibilities",
            "yoe": "Years of experience calculation"
        } 