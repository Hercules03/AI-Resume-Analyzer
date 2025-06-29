import streamlit as st
import sys
import os

# Add the App directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_service import LLMService
from llm_utils import export_metadata_to_json
from config import PAGE_CONFIG
from utils import get_system_info, get_location_info, generate_security_token, validate_file_upload, show_pdf, get_current_timestamp
from resume_processor import ResumeProcessor
from pdf_processing import pdf_processor
import time
from database import db_manager

st.set_page_config(**PAGE_CONFIG)


st.title("Candidate Evaluation")

resume_processor = ResumeProcessor()

llm_service = LLMService()

system_info = get_system_info()
location_info = get_location_info()

sec_token = generate_security_token()

st.markdown('''<h5 style='text-align: left; color: #021659;'> Upload Candidate Resume for Evaluation</h5>''', unsafe_allow_html=True)

def _create_tagged_resume_text(resume):
    """Create tagged resume text for robust embedding with metadata."""
    
    tagged_sections = []
    
    # Personal Information Section
    personal_info = []
    if resume.name:
        personal_info.append(f"[NAME] {resume.name}")
    if resume.email:
        personal_info.append(f"[EMAIL] {resume.email}")
    if resume.contact_number:
        personal_info.append(f"[PHONE] {resume.contact_number}")
    if resume.linkedin:
        personal_info.append(f"[LINKEDIN] {resume.linkedin}")
    if resume.github:
        personal_info.append(f"[GITHUB] {resume.github}")
    
    if personal_info:
        tagged_sections.append("[SECTION:PERSONAL] " + " | ".join(personal_info))
    
    # Skills Section
    if resume.skills:
        tagged_sections.append(f"[SECTION:SKILLS] {', '.join(resume.skills)}")
    
    # Work Experience Section
    if resume.work_experiences:
        for i, exp in enumerate(resume.work_experiences, 1):
            exp_parts = []
            if exp.job_title:
                exp_parts.append(f"[JOB_TITLE] {exp.job_title}")
            if exp.company:
                exp_parts.append(f"[COMPANY] {exp.company}")
            if exp.duration:
                exp_parts.append(f"[DURATION] {exp.duration}")
            if exp.location:
                exp_parts.append(f"[LOCATION] {exp.location}")
            if exp.responsibilities:
                exp_parts.append(f"[RESPONSIBILITIES] {'; '.join(exp.responsibilities)}")
            if exp.technologies:
                exp_parts.append(f"[TECHNOLOGIES] {', '.join(exp.technologies)}")
            
            if exp_parts:
                tagged_sections.append(f"[SECTION:EXPERIENCE_{i}] " + " | ".join(exp_parts))
    
    # Education Section
    if resume.educations:
        for i, edu in enumerate(resume.educations, 1):
            edu_parts = []
            if edu.degree:
                edu_parts.append(f"[DEGREE] {edu.degree}")
            if edu.field_of_study:
                edu_parts.append(f"[FIELD_OF_STUDY] {edu.field_of_study}")
            if edu.institution:
                edu_parts.append(f"[INSTITUTION] {edu.institution}")
            if edu.graduation_date:
                edu_parts.append(f"[GRADUATION] {edu.graduation_date}")
            if edu.gpa:
                edu_parts.append(f"[GPA] {edu.gpa}")
            
            if edu_parts:
                tagged_sections.append(f"[SECTION:EDUCATION_{i}] " + " | ".join(edu_parts))
    
    return " || ".join(tagged_sections)

def _extract_career_transitions(work_experiences):
    """
    Extract career transition history using LLM-based analysis.
    
    This function now uses the CareerTransitionExtractor for more robust analysis
    compared to the previous keyword-based approach.
    """
    try:
        # Import the career transition extractor
        from extractors import CareerTransitionExtractor
        
        if not work_experiences:
            return "No work experience found for analysis"
        
        if len(work_experiences) < 2:
            return "Insufficient experience entries for transition analysis"
        
        # Convert work experience objects to the format expected by the extractor
        work_exp_data = []
        for exp in work_experiences:
            exp_dict = {
                'job_title': exp.job_title,
                'company': exp.company,
                'duration': exp.duration,
                'start_date': exp.start_date,
                'end_date': exp.end_date,
                'location': exp.location,
                'industry': exp.industry,
                'employment_type': exp.employment_type,
                'responsibilities': exp.responsibilities or [],
                'technologies': exp.technologies or []
            }
            work_exp_data.append(exp_dict)
        
        # Use the LLM-based extractor for analysis
        career_extractor = CareerTransitionExtractor()
        result = career_extractor.extract_from_work_experiences(work_exp_data, development_mode=False)
        
        # Get the analysis and format for database storage
        analysis = result.get('careerprogressionanalysis', {})
        
        # Format transitions for backward compatibility with existing database field
        if analysis.get('transitions'):
            transitions_text = []
            for transition in analysis['transitions']:
                transition_str = f"{transition.get('from_field', 'Unknown')} → {transition.get('to_field', 'Unknown')}"
                if transition.get('transition_type'):
                    transition_str += f" ({transition['transition_type']})"
                transitions_text.append(transition_str)
            
            result_str = "; ".join(transitions_text)
            
            # Add career path context for richer information
            if analysis.get('career_path_type'):
                result_str += f" | Path: {analysis['career_path_type']}"
            
            if analysis.get('career_coherence_score'):
                result_str += f" | Coherence: {analysis['career_coherence_score']}/10"
            
            return result_str
        else:
            return analysis.get('transition_summary', 'No field transitions detected')
            
    except Exception as e:
        # Fallback to simple analysis if LLM extractor fails
        print(f"Career transition extraction failed: {e}")
        return _extract_career_transitions_fallback(work_experiences)

def _extract_career_transitions_fallback(work_experiences):
    """
    Fallback career transition analysis using the original keyword-based approach.
    Used when the LLM-based extractor fails.
    """
    if not work_experiences or len(work_experiences) < 2:
        return "No transitions detected"
    
    transitions = []
    fields = []
    
    for exp in work_experiences:
        # Determine field for each experience
        exp_field = "General"
        if exp.job_title:
            title_lower = exp.job_title.lower()
            if any(keyword in title_lower for keyword in ['data', 'analyst', 'scientist']):
                exp_field = "Data Science & Analytics"
            elif any(keyword in title_lower for keyword in ['developer', 'engineer', 'programmer']):
                exp_field = "Software Development"
            elif any(keyword in title_lower for keyword in ['sales', 'marketing', 'business']):
                exp_field = "Business"
            elif any(keyword in title_lower for keyword in ['manager', 'director', 'lead']):
                exp_field = "Management"
        
        fields.append(exp_field)
    
    # Identify transitions
    for i in range(1, len(fields)):
        if fields[i] != fields[i-1]:
            transitions.append(f"{fields[i-1]} → {fields[i]}")
    
    return "; ".join(transitions) if transitions else "No field transitions (fallback analysis)"

def _calculate_field_specific_career_level(resume, target_field):
    """
    Calculate career level specific to the target field using LLM-based analysis.
    
    This function now uses the CareerLevelExtractor for more accurate career level assessment
    that considers job progression, responsibilities, and field-specific experience.
    """
    try:
        # Import the career level extractor
        from extractors import CareerLevelExtractor
        
        if not resume.work_experiences:
            return "Entry Level"
        
        # Convert Resume work_experiences to the format expected by the extractor
        work_exp_data = []
        for exp in resume.work_experiences:
            exp_dict = {
                'job_title': exp.job_title,
                'company': exp.company,
                'duration': exp.duration,
                'industry': exp.industry,
                'employment_type': exp.employment_type,
                'responsibilities': exp.responsibilities or [],
                'technologies': exp.technologies or []
            }
            work_exp_data.append(exp_dict)
        
        # Use the LLM-based extractor for analysis
        career_level_extractor = CareerLevelExtractor()
        result = career_level_extractor.analyze_career_level(work_exp_data, target_field, resume.YoE, development_mode=False)
        
        # Get the analysis and return career level
        analysis = result.get('careerlevelanalysis', {})
        return analysis.get('career_level', 'Entry Level')
        
    except Exception as e:
        # Fallback to simple analysis if LLM extractor fails
        print(f"Career level extraction failed: {e}")
        return _calculate_field_specific_career_level_fallback(resume, target_field)

def _calculate_field_specific_career_level_fallback(resume, target_field):
    """
    Fallback career level calculation using the original heuristic approach.
    Used when the LLM-based extractor fails.
    """
    if not resume.work_experiences:
        return "Entry Level"
    
    # Calculate field-specific experience
    field_experience_months = 0
    total_experience_months = 0
    
    for exp in resume.work_experiences:
        # Extract duration in months (simplified)
        months = _extract_months_from_duration(exp.duration) if exp.duration else 12  # Default 1 year if no duration
        total_experience_months += months
        
        # Check if this experience is relevant to target field
        if _is_experience_relevant_to_field(exp, target_field):
            field_experience_months += months
    
    field_experience_years = field_experience_months / 12
    total_experience_years = total_experience_months / 12
    
    # Field-specific career level determination
    if field_experience_years < 1:
        return "Entry Level" if total_experience_years < 3 else "Career Changer"
    elif field_experience_years < 3:
        return "Junior Level"
    elif field_experience_years < 6:
        return "Mid Level"
    elif field_experience_years < 10:
        return "Senior Level"
    else:
        return "Expert Level"

def _is_experience_relevant_to_field(experience, target_field):
    """
    Determine if work experience is relevant to the target field using LLM-based analysis.
    
    This function now uses the FieldRelevanceExtractor for more accurate field relevance assessment
    compared to the previous keyword-based approach.
    """
    try:
        # Import the field relevance extractor
        from extractors import FieldRelevanceExtractor
        
        # Convert experience object to dictionary format
        exp_dict = {
            'job_title': experience.job_title,
            'company': experience.company,
            'responsibilities': experience.responsibilities or [],
            'technologies': experience.technologies or [],
            'industry': experience.industry
        }
        
        # Use the LLM-based extractor for analysis
        relevance_extractor = FieldRelevanceExtractor()
        result = relevance_extractor.analyze_experience_relevance(exp_dict, target_field, development_mode=False)
        
        # Get the analysis and return relevance
        analysis = result.get('fieldrelevanceanalysis', {})
        
        # Use relevance score threshold for decision
        # Score >= 5 is considered relevant (moderate to high relevance)
        relevance_score = analysis.get('relevance_score', 1)
        return relevance_score >= 5
        
    except Exception as e:
        # Fallback to simple analysis if LLM extractor fails
        print(f"Field relevance extraction failed: {e}")
        return _is_experience_relevant_to_field_fallback(experience, target_field)

def _is_experience_relevant_to_field_fallback(experience, target_field):
    """
    Fallback field relevance analysis using the original keyword-based approach.
    Used when the LLM-based extractor fails.
    """
    if not experience.job_title and not experience.responsibilities and not experience.technologies:
        return False
    
    # Combine all text for analysis
    exp_text = f"{experience.job_title or ''} {' '.join(experience.responsibilities or [])} {' '.join(experience.technologies or [])}".lower()
    
    field_keywords = {
        "Data Science & Analytics": ['data', 'analytics', 'scientist', 'analyst', 'machine learning', 'python', 'sql', 'tableau', 'pandas', 'numpy'],
        "Web Development": ['web', 'frontend', 'javascript', 'react', 'html', 'css', 'vue', 'angular', 'web developer'],
        "Backend Development": ['backend', 'api', 'server', 'java', 'python', 'node.js', 'spring', 'django', 'flask'],
        "Mobile Development": ['mobile', 'android', 'ios', 'swift', 'kotlin', 'app', 'react native', 'flutter'],
        "DevOps & Cloud": ['devops', 'cloud', 'aws', 'docker', 'kubernetes', 'jenkins', 'terraform', 'infrastructure'],
        "Machine Learning": ['machine learning', 'ml', 'ai', 'tensorflow', 'pytorch', 'deep learning', 'neural network']
    }
    
    keywords = field_keywords.get(target_field, [])
    return any(keyword in exp_text for keyword in keywords)

def _extract_months_from_duration(duration_str):
    """
    Extract months from duration string using LLM-based parsing.
    
    This function now uses the DurationExtractor for more accurate duration parsing
    compared to the previous regex-based approach.
    """
    try:
        # Import the duration extractor
        from extractors import DurationExtractor
        
        # Use the LLM-based extractor for parsing
        duration_extractor = DurationExtractor()
        result = duration_extractor.parse_duration(duration_str, development_mode=False)
        
        # Get the analysis and return total months
        analysis = result.get('durationanalysis', {})
        return analysis.get('total_months', 12.0)
        
    except Exception as e:
        # Fallback to simple regex parsing if LLM extractor fails
        print(f"Duration extraction failed: {e}")
        return _extract_months_from_duration_fallback(duration_str)

def _extract_months_from_duration_fallback(duration_str):
    """
    Fallback duration extraction using the original regex-based approach.
    Used when the LLM-based extractor fails.
    """
    if not duration_str:
        return 12
    
    duration_lower = duration_str.lower()
    
    # Extract numbers from the string
    import re
    numbers = re.findall(r'\d+', duration_lower)
    
    if not numbers:
        return 12  # Default to 1 year if no numbers found
    
    # Get the first number found
    value = int(numbers[0])
    
    # Determine if it's years or months based on keywords
    if any(keyword in duration_lower for keyword in ['year', 'yr', 'yrs']):
        return value * 12  # Convert years to months
    elif any(keyword in duration_lower for keyword in ['month', 'mon', 'mos']):
        return value
    else:
        # If no clear indicator, assume months if value > 12, otherwise years
        if value > 12:
            return value  # Assume months
        else:
            return value * 12  # Assume years

def _estimate_job_role(resume):
    """
    Estimate suitable job roles based on comprehensive resume analysis.
    
    This function uses the JobRoleEstimationExtractor for intelligent job role recommendations
    based on skills, experience, career level, and field analysis.
    """
    try:
        # Import the job role estimation extractor
        from extractors import JobRoleEstimationExtractor
        
        # Convert Resume object to dictionary format for analysis
        resume_data = {
            'name': resume.name,
            'primary_field': resume.primary_field,
            'career_level': resume.career_level,
            'YoE': resume.YoE,
            'skills': resume.skills,
            'work_experiences': resume.work_experiences,
            'educations': resume.educations
        }
        
        # Use the LLM-based extractor for analysis
        job_role_extractor = JobRoleEstimationExtractor()
        result = job_role_extractor.estimate_job_role(resume_data, development_mode=False)
        
        # Get the analysis
        analysis = result.get('jobroleestimation', {})
        return analysis
        
    except Exception as e:
        # Fallback to simple analysis if LLM extractor fails
        print(f"Job role estimation failed: {e}")
        return _estimate_job_role_fallback(resume)

def _estimate_job_role_fallback(resume):
    """
    Fallback job role estimation using simple heuristics.
    Used when the LLM-based extractor fails.
    """
    skills = resume.skills or []
    career_level = resume.career_level or 'Entry Level'
    primary_field = resume.primary_field or 'General'
    
    if not skills:
        primary_role = f"{career_level} Professional"
    else:
        skills_text = ' '.join(skills).lower()
        
        # Simple heuristic based on skills and career level
        level_prefix = ""
        if "senior" in career_level.lower():
            level_prefix = "Senior "
        elif "mid" in career_level.lower():
            level_prefix = ""
        elif "entry" in career_level.lower() or "junior" in career_level.lower():
            level_prefix = "Junior "
        
        # Field-based role suggestions
        if "data science" in primary_field.lower():
            if any(skill in skills_text for skill in ['machine learning', 'python', 'tensorflow']):
                primary_role = f"{level_prefix}Data Scientist"
            else:
                primary_role = f"{level_prefix}Data Analyst"
        elif "software" in primary_field.lower() or "development" in primary_field.lower():
            if any(skill in skills_text for skill in ['react', 'javascript', 'frontend']):
                primary_role = f"{level_prefix}Frontend Developer"
            elif any(skill in skills_text for skill in ['api', 'backend', 'database']):
                primary_role = f"{level_prefix}Backend Developer"
            else:
                primary_role = f"{level_prefix}Software Developer"
        elif "business" in primary_field.lower():
            primary_role = f"{level_prefix}Business Analyst"
        else:
            primary_role = f"{level_prefix}Professional"
    
    # Return fallback format compatible with full analysis
    return {
        'primary_job_role': primary_role,
        'alternative_roles': [],
        'role_confidence_score': 5,
        'role_justification': 'Estimated using basic heuristics due to analysis limitations',
        'required_skills_match': skills[:3] if skills else [],
        'skill_gaps': ['Professional development opportunities available'],
        'career_progression_path': ['Next level role advancement'],
        'salary_range_estimate': 'Contact HR for salary information',
        'role_suitability_factors': {'basic_analysis': 5}
    }

def _evaluate_critical_information_missing(text: str) -> bool:
    """
    Evaluate if critical resume information is missing from extracted text.
    
    Returns True if critical information appears to be missing.
    """
    if not text or len(text.strip()) < 100:
        return True
    
    text_lower = text.lower()
    
    # Check for basic resume elements
    critical_elements = {
        'name_indicators': ['name', 'resume', 'cv', 'curriculum vitae'],
        'contact_indicators': ['email', 'phone', 'contact', '@', 'tel', 'mobile'],
        'experience_indicators': ['experience', 'work', 'employment', 'position', 'role', 'job', 'company'],
        'skills_indicators': ['skills', 'technologies', 'proficient', 'programming', 'software'],
        'education_indicators': ['education', 'degree', 'university', 'college', 'school', 'bachelor', 'master']
    }
    
    missing_categories = 0
    
    for category, indicators in critical_elements.items():
        if not any(indicator in text_lower for indicator in indicators):
            missing_categories += 1
    
    # If more than 2 categories are missing, consider it critical information missing
    return missing_categories > 2

def _extract_text_with_intelligent_fallback(pdf_path: str) -> tuple[str, str]:
    """
    Enhanced PDF text extraction with intelligent fallback logic.
    
    Returns:
        tuple: (extracted_text, extraction_method_used)
    """
    # Step 1: Try PyMuPDF4LLM first
    pymupdf_text = pdf_processor.extract_with_pymupdf4llm(pdf_path)
    pymupdf_missing_critical = True
    
    if pymupdf_text:
        pymupdf_missing_critical = _evaluate_critical_information_missing(pymupdf_text)
        
        if not pymupdf_missing_critical:
            return pymupdf_text, "PyMuPDF4LLM"
        else:
            # Continue to EasyOCR if critical information is missing
            pass
    
    # Step 2: Try EasyOCR as fallback
    with st.spinner("Processing document with advanced OCR..."):
        easyocr_text = pdf_processor.extract_with_easyocr(pdf_path)
        easyocr_missing_critical = True
        
        if easyocr_text:
            easyocr_missing_critical = _evaluate_critical_information_missing(easyocr_text)
            
            if not easyocr_missing_critical:
                return easyocr_text, "EasyOCR"
    
    # Step 3: Compare results and choose the better one
    if pymupdf_text and easyocr_text:
        # Both extracted text, compare quality
        pymupdf_quality = len(pymupdf_text.strip())
        easyocr_quality = len(easyocr_text.strip())
        
        # Use length as a proxy for completeness
        if easyocr_quality > pymupdf_quality * 1.2:  # 20% more content threshold
            return easyocr_text, "EasyOCR (Enhanced)"
        else:
            return pymupdf_text, "PyMuPDF4LLM"
    
    elif pymupdf_text and not easyocr_text:
        return pymupdf_text, "PyMuPDF4LLM"
    
    elif easyocr_text and not pymupdf_text:
        return easyocr_text, "EasyOCR"
    
    else:
        # Both failed
        st.error("❌ Unable to extract text from the document")
        return "Error: Unable to extract text from the document using either method.", "Failed"



## File upload in PDF format
pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])

def _calculate_field_experience(work_experiences, target_field):
    """Calculate years of experience specifically in the target field."""
    
    if not work_experiences:
        return "0 years"
    
    field_months = 0
    for exp in work_experiences:
        if _is_experience_relevant_to_field(exp, target_field):
            months = _extract_months_from_duration(exp.duration) if exp.duration else 12
            field_months += months
    
    years = field_months / 12
    return f"{years:.1f} years in {target_field}"

def format_profile_link(url: str, platform: str) -> str:
    """
    Format profile URLs to be clickable links.
    Adds protocol if missing and creates markdown link.
    """
    if not url:
        return url
    
    # Clean up the URL
    url = url.strip()
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    # Create markdown link with platform name
    return f"[{platform} Profile]({url})"

def display_resume_results(resume, dev_mode=False):
    """Display the results from resume processing with gap analysis."""
    
    # Pre-calculate gap analysis and completeness summary to avoid loading delays
    gaps = resume.analyze_resume_gaps()
    completeness = resume.get_completeness_summary()

    # === RESUME COMPLETENESS ANALYSIS ===
    st.subheader("**Resume Completeness Analysis**")

    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Skills Found", completeness["skills_count"])
    with col2:
        st.metric("Work Experience", completeness["jobs_count"])
    with col3:
        st.metric("Education", completeness["education_count"])
    with col4:
        if resume.career_level:
            st.metric("Career Level", resume.career_level)
        else:
            st.metric("Career Level", "Not Determined")
    with col5:
        if completeness["has_critical_gaps"]:
            st.metric("Status", "Issues Found")
        else:
            st.metric("Status", "Ready")
    
    # === GAP ANALYSIS SECTION ===
    if any(gap_list for gap_list in gaps.values() if gap_list):
        st.subheader("**Gap Analysis - Missing Information**")
        
        # Critical missing information
        if gaps["critical_missing"]:
            st.error("**Critical Missing Information:**")
            for gap in gaps["critical_missing"]:
                st.write(f"  {gap}")
        
        # Professional profile gaps
        if gaps["professional_missing"]:
            for gap in gaps["professional_missing"]:
                st.write(f"  {gap}")
        
        # Detail gaps (HR focus - what information they don't have) 
        if gaps["detail_gaps"]:
            st.write("**Information Gaps for HR Review:**")
            for gap in gaps["detail_gaps"]:
                st.write(f"  {gap}")
    else:
        pass
    # === DETAILED INFORMATION SECTIONS ===
    st.markdown("---")
    
    # Profile Information
    if resume.name or resume.email or resume.contact_number:
        with st.expander("**Profile Information**", expanded=dev_mode):
            col1, col2, col3 = st.columns(3)
            with col1:
                if resume.name:
                    st.write(f"**Name:** {resume.name}")
            with col2:
                if resume.email:
                    st.markdown(f"**Email:** [Send Email](mailto:{resume.email})")
            with col3:
                if resume.contact_number:
                    st.write(f"**Contact:** {resume.contact_number}")
            
            # Professional profiles with clickable links
            if resume.linkedin or resume.github or resume.portfolio:
                st.write("**Professional Profiles:**")
                if resume.linkedin:
                    linkedin_link = format_profile_link(resume.linkedin, "LinkedIn")
                    st.markdown(f"• **LinkedIn:** {linkedin_link}")
                if resume.github:
                    github_link = format_profile_link(resume.github, "GitHub")
                    st.markdown(f"• **GitHub:** {github_link}")
                if resume.portfolio:
                    portfolio_link = format_profile_link(resume.portfolio, "Portfolio")
                    st.markdown(f"• **Portfolio:** {portfolio_link}")

    # Skills
    if resume.skills:
        with st.expander(f"**Skills ({len(resume.skills)} found)**", expanded=dev_mode):
            st.write(", ".join(resume.skills))
    
    # Work Experience
    if resume.work_experiences:
        with st.expander(f"**Work Experience ({len(resume.work_experiences)} entries)**", expanded=dev_mode):
            for i, exp in enumerate(resume.work_experiences, 1):
                with st.expander(f"Position {i}: {exp.job_title or 'Unknown'} at {exp.company or 'Unknown'}"):
                    if exp.duration:
                        st.write(f"**Duration:** {exp.duration}")
                    if exp.location:
                        st.write(f"**Location:** {exp.location}")
                    if exp.responsibilities:
                        st.write("**Responsibilities:**")
                        for resp in exp.responsibilities:
                            st.write(f"• {resp}")
                    if exp.technologies:
                        st.write(f"**Technologies:** {', '.join(exp.technologies)}")

                    # Show what information is missing for HR awareness
                    missing = []
                    if not exp.job_title: missing.append("job title")
                    if not exp.company: missing.append("company")
                    if not exp.duration and not (exp.start_date and exp.end_date): missing.append("duration")
                    if not exp.responsibilities: missing.append("responsibilities")
                    
                    if missing:
                        st.warning(f"HR Note: Missing {', '.join(missing)} - may need follow-up")
    
    # Education
    if resume.educations:
        with st.expander(f"**Education ({len(resume.educations)} entries)**", expanded=dev_mode):
            for i, edu in enumerate(resume.educations, 1):
                with st.expander(f"Education {i}: {edu.degree or 'Unknown'} in {edu.field_of_study or 'Unknown'}"):
                    if edu.institution:
                        st.write(f"**Institution:** {edu.institution}")
                    if edu.graduation_date:
                        st.write(f"**Graduation:** {edu.graduation_date}")
                    if edu.gpa:
                        st.write(f"**GPA:** {edu.gpa}")
                    if edu.honors:
                        st.write(f"**Honors:** {edu.honors}")

                    # Show what information is missing for HR awareness
                    missing = []
                    if not edu.degree: missing.append("degree")
                    if not edu.institution: missing.append("institution")
                    if not edu.field_of_study: missing.append("field of study")
                    if not edu.graduation_date: missing.append("graduation date")
                    
                    if missing:
                        st.warning(f"HR Note: Missing {', '.join(missing)} - may need follow-up")
    
    # Years of Experience & Experience Analysis
    with st.expander("**Experience Analysis**", expanded=dev_mode):
        # Career Assessment Section
        st.subheader("**Career Assessment**")

        # Create columns for career information
        career_col1, career_col2, career_col3 = st.columns(3)
        
        with career_col1:
            if resume.YoE:
                st.write(f"**Total Experience:** {resume.YoE}")
            else:
                st.write("**Total Experience:** Not calculated")
        
        with career_col2:
            if resume.career_level:
                st.write(f"**Career Level:** {resume.career_level}")
            else:
                st.write("**Career Level:** Not determined")
        
        with career_col3:
            if resume.primary_field:
                st.write(f"**Primary Field:** {resume.primary_field}")
            else:
                st.write("**Primary Field:** Not determined")
        
        # Experience Breakdown
        st.subheader("**Experience Breakdown**")

        # Show work experience count and details
        if resume.work_experiences:
            st.write(f"**Work Experience Entries:** {len(resume.work_experiences)}")

            # Calculate actual duration from extracted data for validation
            actual_months = 0
            duration_specified_count = 0

            # Show experience progression for HR insight
            if len(resume.work_experiences) > 1:
                st.write("**Career Progression:**")
            else:
                st.write("**Work Experience:**")
            
            for i, exp in enumerate(resume.work_experiences):
                title = exp.job_title or "Unknown Position"
                company = exp.company or "Unknown Company"
                duration = exp.duration or "Duration not specified"
                
                # Try to extract months from duration for validation
                if exp.duration and exp.duration.lower() != "duration not specified":
                    duration_specified_count += 1
                    # Simple parsing for common formats
                    duration_lower = exp.duration.lower()
                    if "month" in duration_lower:
                        try:
                            months = int(''.join(filter(str.isdigit, duration_lower)))
                            actual_months += months
                        except:
                            pass
                    elif "year" in duration_lower:
                        try:
                            years = float(''.join(c for c in duration_lower if c.isdigit() or c == '.'))
                            actual_months += years * 12
                        except:
                            pass
                
                if len(resume.work_experiences) > 1:
                    st.write(f"  {i+1}. {title} at {company} ({duration})")
                else:
                    st.write(f"  • {title} at {company} ({duration})")
            
            # Experience validation - Check for discrepancies
            if resume.YoE and duration_specified_count > 0:
                try:
                    ai_years = float(resume.YoE.replace(" years", ""))
                    actual_years = actual_months / 12
                    
                    # If there's a significant discrepancy (more than 6 months difference)
                    if abs(ai_years - actual_years) > 0.5:
                        st.warning("**HR Alert:** Experience discrepancy detected!")
                        
                        if ai_years > actual_years:
                            st.warning("**HR Note:** AI may be including undated experience or making assumptions. Verify during interview.")
                        else:
                            st.warning("**HR Note:** Some experience durations may not be properly extracted. Check original resume.")
                        
                        # Show which entries lack duration data
                        missing_duration = [exp for exp in resume.work_experiences if not exp.duration or exp.duration == "Duration not specified"]
                        if missing_duration:
                            pass
                    else:
                        st.success("**Experience Validation:** AI calculation ({ai_years} years) matches duration data ({actual_years:.1f} years)")
                        
                except Exception as e:
                    if dev_mode:
                        st.warning(f"**Debug:** Experience validation failed: {e}")
            
            # Career level validation
            if resume.career_level and resume.YoE:
                try:
                    years = float(resume.YoE.replace(" years", ""))
                    expected_levels = {
                        "Entry Level": (0, 2),
                        "Mid Level": (2, 5),
                        "Senior Level": (5, 10),
                        "Executive Level": (10, float('inf'))
                    }
                    
                    if resume.career_level in expected_levels:
                        min_years, max_years = expected_levels[resume.career_level]
                        if years < min_years or years > max_years:
                            pass
                except:
                    pass  # Skip validation if parsing fails

            # Debug information for development mode
            if dev_mode and not resume.YoE and resume.work_experiences:
                st.warning("**Debug Info:** YoE extraction may have failed. Work experience entries found but total experience not calculated.")
                for i, exp in enumerate(resume.work_experiences, 1):
                    if exp.duration:
                        st.write(f"  - Position {i}: {exp.duration}")
        else:
            st.write("**Work Experience Entries:** 0")
            st.warning("**HR Note:** No work experience found - may indicate recent graduate or career changer")
    
    # Job Role Estimation Section
    st.markdown("---")
    st.subheader("**Estimated Job Role**")
    
    with st.spinner('Analyzing best fit job roles...'):
        job_role_analysis = _estimate_job_role(resume)
    
    if job_role_analysis:
        # Primary role with confidence
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"### **{job_role_analysis.get('primary_job_role', 'Professional')}**")
            
        with col2:
            confidence = job_role_analysis.get('role_confidence_score', 5)
            confidence_color = "green" if confidence >= 8 else "orange" if confidence >= 6 else "red"
            st.markdown(f"**Confidence:** <span style='color: {confidence_color}'>{confidence}/10</span>", unsafe_allow_html=True)
            
        with col3:
            salary_estimate = job_role_analysis.get('salary_range_estimate', 'Not estimated')
            st.markdown(f"**Salary Range:** {salary_estimate}")
        
        # Role justification
        if job_role_analysis.get('role_justification'):
            with st.expander("**Why this role fits**", expanded=True):
                st.write(job_role_analysis['role_justification'])
        
        # Alternative roles
        alternative_roles = job_role_analysis.get('alternative_roles', [])
        if alternative_roles:
            st.write("**Alternative Role Options:**")
            for i, role in enumerate(alternative_roles[:3], 1):  # Show top 3 alternatives
                st.write(f"  {i}. {role}")
        
        # Skills analysis
        col1, col2 = st.columns(2)
        
        with col1:
            matching_skills = job_role_analysis.get('required_skills_match', [])
            if matching_skills:
                st.write("**Matching Skills:**")
                for skill in matching_skills[:5]:  # Show top 5 matching skills
                    st.write(f"  • {skill}")
        
        with col2:
            skill_gaps = job_role_analysis.get('skill_gaps', [])
            if skill_gaps:
                st.write("**Skills to Develop:**")
                for gap in skill_gaps[:5]:  # Show top 5 skill gaps
                    st.write(f"  • {gap}")
        
        # Career progression path
        career_path = job_role_analysis.get('career_progression_path', [])
        if career_path:
            with st.expander("**Career Progression Path**"):
                st.write("**Potential next steps in career development:**")
                for i, step in enumerate(career_path, 1):
                    st.write(f"  {i}. {step}")
        
        # Role suitability factors
        suitability_factors = job_role_analysis.get('role_suitability_factors', {})
        if suitability_factors:
            with st.expander("**Role Suitability Analysis**"):
                st.write("**Assessment factors (1-10 scale):**")
                for factor, score in suitability_factors.items():
                    factor_name = factor.replace('_', ' ').title()
                    score_color = "green" if score >= 8 else "orange" if score >= 6 else "red"
                    st.markdown(f"  • **{factor_name}:** <span style='color: {score_color}'>{score}/10</span>", unsafe_allow_html=True)

    # Download options
    st.markdown("---")
    st.subheader("**Export Options**")

    col1, col2 = st.columns(2)

    with col1:
        # JSON download
        resume_json = resume.model_dump()
        json_str = export_metadata_to_json(resume_json)
        st.download_button(
            label="Download JSON Data",
            data=json_str,
            file_name=f"resume_analysis_{resume.name.replace(' ', '_') if resume.name else 'candidate'}.json",
            mime="application/json",
            help="Download complete analysis in JSON format"
        )
    
    with col2:
        # Legacy format download
        legacy_data = resume.to_legacy_format()
        legacy_json = export_metadata_to_json(legacy_data)
        st.download_button(
            label="Download Legacy Format",
            data=legacy_json,
            file_name=f"resume_legacy_{resume.name.replace(' ', '_') if resume.name else 'candidate'}.json",
            mime="application/json",
            help="Download in legacy format for compatibility"
        )

def prepare_user_data_from_resume(resume, system_info, location_info, sec_token, pdf_name):
    """Prepare user data from Resume object for database insertion with field-specific career analysis."""
    
    # Use AI-extracted field, with intelligent LLM-based fallbacks
    reco_field = resume.primary_field or "General"
    
    # Enhanced field determination using LLM-based field classification if AI extraction failed
    if reco_field == "General" and resume.skills:
        try:
            from extractors import FieldClassificationExtractor
            
            # Convert work experiences to the format expected by extractor
            work_exp_data = []
            if resume.work_experiences:
                for exp in resume.work_experiences:
                    exp_dict = {
                        'job_title': exp.job_title,
                        'company': exp.company,
                        'duration': exp.duration,
                        'responsibilities': exp.responsibilities or [],
                        'technologies': exp.technologies or []
                    }
                    work_exp_data.append(exp_dict)
            
            # Convert educations to the format expected by extractor
            edu_data = []
            if resume.educations:
                for edu in resume.educations:
                    edu_dict = {
                        'degree': edu.degree,
                        'field_of_study': edu.field_of_study,
                        'institution': edu.institution
                    }
                    edu_data.append(edu_dict)
            
            # Use LLM-based field classification
            field_extractor = FieldClassificationExtractor()
            result = field_extractor.classify_field(
                skills=resume.skills,
                work_experiences=work_exp_data,
                educations=edu_data,
                current_primary_field=resume.primary_field,
                development_mode=False
            )
            
            analysis = result.get('fieldclassificationanalysis', {})
            extracted_field = analysis.get('primary_field', 'General')
            
            # Use extracted field if confidence is reasonable (≥ 5)
            confidence = analysis.get('confidence_score', 1)
            if confidence >= 5:
                reco_field = extracted_field
                
        except Exception as e:
            # Fallback to keyword-based classification if LLM extractor fails
            print(f"Field classification extraction failed: {e}")
            reco_field = FieldClassificationExtractor.classify_field_fallback(resume.skills)
    
    # IMPROVED: Field-specific career level analysis
    cand_level = _calculate_field_specific_career_level(resume, reco_field)
    
    # Prepare detailed work experience data
    work_exp_details = []
    if resume.work_experiences:
        for i, exp in enumerate(resume.work_experiences, 1):
            exp_text = f"Job {i}: {exp.job_title or 'Unknown Position'} at {exp.company or 'Unknown Company'}"
            if exp.duration:
                exp_text += f" ({exp.duration})"
            if exp.location:
                exp_text += f" in {exp.location}"
            if exp.responsibilities:
                exp_text += f". Responsibilities: {'; '.join(exp.responsibilities[:3])}"  # Top 3 responsibilities
            if exp.technologies:
                exp_text += f". Technologies: {', '.join(exp.technologies)}"
            work_exp_details.append(exp_text)
    
    # Prepare education details
    education_details = []
    if resume.educations:
        for i, edu in enumerate(resume.educations, 1):
            edu_text = f"Education {i}: {edu.degree or 'Unknown Degree'} in {edu.field_of_study or 'Unknown Field'}"
            if edu.institution:
                edu_text += f" from {edu.institution}"
            if edu.graduation_date:
                edu_text += f" (graduated {edu.graduation_date})"
            if edu.gpa:
                edu_text += f", GPA: {edu.gpa}"
            education_details.append(edu_text)
    
    # Create comprehensive resume summary for searchability
    full_resume_summary = []
    if resume.name:
        full_resume_summary.append(f"Name: {resume.name}")
    if resume.email:
        full_resume_summary.append(f"Email: {resume.email}")
    if resume.contact_number:
        full_resume_summary.append(f"Contact: {resume.contact_number}")
    if resume.linkedin:
        full_resume_summary.append(f"LinkedIn: {resume.linkedin}")
    if resume.github:
        full_resume_summary.append(f"GitHub: {resume.github}")
    if resume.portfolio:
        full_resume_summary.append(f"Portfolio: {resume.portfolio}")
    
    return {
        'sec_token': sec_token,
        'ip_add': system_info['ip_add'],
        'host_name': system_info['host_name'],
        'dev_user': system_info['dev_user'],
        'os_name_ver': system_info['os_name_ver'],
        'latlong': location_info['latlong'],
        'city': location_info['city'],
        'state': location_info['state'],
        'country': location_info['country'],
        'act_name': 'HR_AI_ANALYSIS',
        'act_mail': 'hr@ai-system.com',
        'act_mob': 'N/A',
        'name': resume.name or 'Unknown',
        'email': resume.email or 'unknown@email.com',
        'timestamp': get_current_timestamp(),
        'no_of_pages': str(resume.no_of_pages or 1),
        'reco_field': reco_field,
        'cand_level': cand_level,
        'skills': str(resume.skills),
        'pdf_name': pdf_name,
        # Enhanced fields for detailed content storage with metadata tagging
        'work_experiences': "; ".join(work_exp_details),
        'educations': "; ".join(education_details),
        'years_of_experience': resume.YoE or "Not specified",
        'field_specific_experience': _calculate_field_experience(resume.work_experiences, reco_field),
        'career_transition_history': _extract_career_transitions(resume.work_experiences),
        'primary_field': resume.primary_field or "General",
        'full_resume_data': "; ".join(full_resume_summary),
        # Metadata tags for robust searching
        'extracted_text': _create_tagged_resume_text(resume),
        'contact_info': f"{resume.email or ''} | {resume.contact_number or ''} | {resume.linkedin or ''} | {resume.github or ''}"
    }

# Add this section right after the text extraction and before resume processing
if pdf_file is not None:
    # Validate file
    if validate_file_upload(pdf_file):
        
        with st.spinner('Processing resume with AI-powered extractors...'):
            time.sleep(2)
            
        ### Save the uploaded resume
        save_image_path = './Uploaded_Resumes/' + pdf_file.name
        pdf_name = pdf_file.name

        with open(save_image_path, "wb") as f:
            f.write(pdf_file.getbuffer())

        # Display PDF
        pdf_display_html = show_pdf(save_image_path)
        st.markdown(pdf_display_html, unsafe_allow_html=True)

        if llm_service.is_available():
            try:
                # Enhanced PDF text extraction with intelligent fallback
                extracted_text, extraction_method = _extract_text_with_intelligent_fallback(save_image_path)
                
                # === DEBUG SECTION: TEXT EXTRACTION ANALYSIS ===
                st.markdown("---")
                st.subheader("🔍 **Text Extraction Debug Information**")
                
                # Show extraction method and text quality metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Extraction Method", extraction_method)
                
                with col2:
                    if not extracted_text.startswith("Error:"):
                        st.metric("Text Length", f"{len(extracted_text):,} chars")
                    else:
                        st.metric("Text Length", "0 chars")
                
                with col3:
                    if not extracted_text.startswith("Error:"):
                        word_count = len(extracted_text.split())
                        st.metric("Word Count", f"{word_count:,}")
                    else:
                        st.metric("Word Count", "0")
                
                with col4:
                    if not extracted_text.startswith("Error:"):
                        # Quick quality assessment
                        has_email = '@' in extracted_text
                        has_phone = any(char.isdigit() for char in extracted_text)
                        quality = "Good" if has_email and has_phone else "Check Needed"
                        st.metric("Quick Quality", quality)
                    else:
                        st.metric("Quick Quality", "Failed")
                
                # Text preview and download options
                if not extracted_text.startswith("Error:"):
                    
                    # Text preview
                    with st.expander("📄 **Preview Extracted Text** (First 1000 characters)", expanded=False):
                        preview_text = extracted_text[:1000]
                        if len(extracted_text) > 1000:
                            preview_text += f"\n\n... (and {len(extracted_text) - 1000:,} more characters)"
                        st.text(preview_text)
                    
                    # Download buttons
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Download raw extracted text
                        st.download_button(
                            label="📥 Download Extracted Text",
                            data=extracted_text,
                            file_name=f"extracted_text_{pdf_file.name.replace('.pdf', '')}_{extraction_method.replace(' ', '_')}.txt",
                            mime="text/plain",
                            help=f"Download the raw text extracted using {extraction_method}"
                        )
                    
                    with col2:
                        # Download with metadata
                        metadata_text = f"""=== EXTRACTION METADATA ===
PDF File: {pdf_file.name}
Extraction Method: {extraction_method}
Text Length: {len(extracted_text):,} characters
Word Count: {len(extracted_text.split()):,} words
Extraction Timestamp: {get_current_timestamp()}

=== EXTRACTED TEXT ===
{extracted_text}
"""
                        st.download_button(
                            label="📥 Download with Metadata",
                            data=metadata_text,
                            file_name=f"debug_extraction_{pdf_file.name.replace('.pdf', '')}_{extraction_method.replace(' ', '_')}.txt",
                            mime="text/plain",
                            help="Download extracted text with debugging metadata"
                        )
                    
                    with col3:
                        # Development mode toggle
                        debug_mode = st.checkbox(
                            "🔧 Enable Development Mode", 
                            value=False,
                            help="Show detailed extraction process and validation steps"
                        )
                
                else:
                    # Show error details for failed extraction
                    st.error("❌ **Text extraction failed**")
                    st.code(extracted_text, language="text")
                    
                    # Still offer download of error message for debugging
                    error_debug_text = f"""=== EXTRACTION ERROR DEBUG ===
PDF File: {pdf_file.name}
Extraction Method: {extraction_method}
Error Message: {extracted_text}
Timestamp: {get_current_timestamp()}

=== TROUBLESHOOTING TIPS ===
1. Check if PDF is corrupted or password-protected
2. Verify PDF contains readable text (not just images)
3. Try with a different PDF for comparison
4. Check Ollama and OCR dependencies
"""
                    st.download_button(
                        label="📥 Download Error Debug Info",
                        data=error_debug_text,
                        file_name=f"extraction_error_{pdf_file.name.replace('.pdf', '')}.txt",
                        mime="text/plain",
                        help="Download error information for troubleshooting"
                    )
                
                st.markdown("---")
                
                # Check if extraction was successful
                if not extracted_text.startswith("Error:"):
                    # Process resume with extracted text
                    with st.spinner('Processing resume with AI-powered extractors...'):
                        # Pass debug_mode if defined, otherwise default to False
                        development_mode = debug_mode if 'debug_mode' in locals() else False
                        resume = resume_processor.process_resume_from_text(extracted_text, save_image_path, development_mode)

                    if resume and resume.name != "Unknown":
                        # Display result in a structured way
                        display_resume_results(resume, development_mode)

                        # Prepare data for database
                        user_data = prepare_user_data_from_resume(
                            resume, system_info, location_info, sec_token, pdf_name
                        )

                        # Insert into ChromaDB vector database
                        insertion_success = db_manager.insert_user_data(user_data)

                        # Show success message
                        if insertion_success:
                            st.success("✅ **Resume analysis completed successfully**")
                        else:
                            st.warning("⚠️ Resume analysis completed but database insertion failed")

                    else:
                        st.warning("⚠️ **Resume processing completed with limited data extraction**")
                        st.info("This may be due to document quality or format. Consider providing a clearer PDF.")
                        
                        # Additional debugging info when processing fails
                        if 'debug_mode' in locals() and debug_mode:
                            st.subheader("🔧 **Additional Debug Information**")
                            
                            # Show what the resume processor actually extracted
                            if resume:
                                st.write("**What was extracted:**")
                                st.json({
                                    "name": resume.name,
                                    "email": resume.email,
                                    "skills_count": len(resume.skills) if resume.skills else 0,
                                    "experience_count": len(resume.work_experiences) if resume.work_experiences else 0,
                                    "education_count": len(resume.educations) if resume.educations else 0
                                })
                            
                            # Text quality analysis
                            st.write("**Text Quality Analysis:**")
                            critical_missing = _evaluate_critical_information_missing(extracted_text)
                            st.write(f"- Critical information missing: {'Yes' if critical_missing else 'No'}")
                            st.write(f"- Contains '@' (email indicator): {'Yes' if '@' in extracted_text else 'No'}")
                            st.write(f"- Contains digits (phone indicator): {'Yes' if any(c.isdigit() for c in extracted_text) else 'No'}")
                            st.write(f"- Contains 'experience': {'Yes' if 'experience' in extracted_text.lower() else 'No'}")
                            st.write(f"- Contains 'education': {'Yes' if 'education' in extracted_text.lower() else 'No'}")
                        
                else:
                    st.error("❌ **Text extraction failed** - Unable to process resume")
                    st.error("Please ensure the PDF is not corrupted and contains readable text.")
                    
            except Exception as e:
                st.error(f"❌ **Resume processing failed**: {str(e)}")
                st.info("Please try with a different PDF or contact support if the issue persists.")
                
                # Download error information for debugging
                error_debug_text = f"""=== PROCESSING ERROR DEBUG ===
PDF File: {pdf_file.name if 'pdf_file' in locals() else 'Unknown'}
Error Type: {type(e).__name__}
Error Message: {str(e)}
Timestamp: {get_current_timestamp()}

=== STACK TRACE ===
{e}
"""
                st.download_button(
                    label="📥 Download Error Debug Info",
                    data=error_debug_text,
                    file_name=f"processing_error_{get_current_timestamp().replace(':', '-')}.txt",
                    mime="text/plain",
                    help="Download error information for debugging"
                )
        
        else:
            st.error("❌ **LLM service not available.** Please check your Ollama configuration.")