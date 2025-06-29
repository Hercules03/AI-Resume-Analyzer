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
import time
from database import db_manager

st.set_page_config(**PAGE_CONFIG)


st.title("Candidate Evaluation")

resume_processor = ResumeProcessor()

llm_model = "gemma3:12b"

llm_service = LLMService(model_name=llm_model)

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
    """Extract career transition history to understand candidate's journey."""
    
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
    
    return "; ".join(transitions) if transitions else "No field transitions"

def _calculate_field_specific_career_level(resume, target_field):
    """Calculate career level specific to the target field, accounting for career transitions."""
    
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
    """Determine if work experience is relevant to the target field."""
    
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
    """Extract months from duration string."""
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
    
    # Use AI-extracted field, with intelligent fallbacks
    reco_field = resume.primary_field or "General"
    
    # Improved field determination if AI extraction failed
    if reco_field == "General" and resume.skills:
        skills_str = " ".join(resume.skills).lower()
        if any(skill in skills_str for skill in ['python', 'data', 'machine learning', 'analytics', 'sql', 'tableau', 'pandas']):
            reco_field = "Data Science & Analytics"
        elif any(skill in skills_str for skill in ['javascript', 'react', 'web', 'frontend', 'html', 'css', 'vue', 'angular']):
            reco_field = "Web Development"
        elif any(skill in skills_str for skill in ['java', 'backend', 'api', 'spring', 'django', 'flask', 'node.js']):
            reco_field = "Backend Development"
        elif any(skill in skills_str for skill in ['mobile', 'android', 'ios', 'swift', 'kotlin', 'react native']):
            reco_field = "Mobile Development"
        elif any(skill in skills_str for skill in ['aws', 'docker', 'kubernetes', 'devops', 'jenkins', 'terraform']):
            reco_field = "DevOps & Cloud"
    
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
                # Process resume
                resume = resume_processor.process_resume(save_image_path, False)

                if resume and resume.name != "Unknown":

                    # Display result in a structured way
                    display_resume_results(resume, False)

                    # Prepare data for database
                    user_data = prepare_user_data_from_resume(
                        resume, system_info, location_info, sec_token, pdf_name
                    )

                    # Insert into ChromaDB vector database
                    insertion_success = db_manager.insert_user_data(user_data)


                else:
                    st.warning("Resume processing completed with limited data extraction.")
            except Exception as e:
                st.error(f"Resume processing failed: {str(e)}")
        
        else:
            st.error("**LLM service not available.** Please check your Ollama configuration.")