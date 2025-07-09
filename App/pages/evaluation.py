import streamlit as st
import sys
import os

# Add the App directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_service import LLMService
from llm_utils import export_metadata_to_json
from config import PAGE_CONFIG, LLM_CONFIG
from utils import get_system_info, get_location_info, generate_security_token, validate_file_upload, show_pdf, get_current_timestamp
from resume_processor import ResumeProcessor
from analyzers import CareerTransitionAnalyzer, FieldCareerLevelAnalyzer, ExperienceRelevanceAnalyzer

import time
from database import db_manager

st.set_page_config(**PAGE_CONFIG)


st.title("Candidate Evaluation")

# === LLM CONFIGURATION (HIDDEN) ===
# Initialize LLM service with Ollama in background
if 'llm_service' not in st.session_state:
    llm_service = LLMService(provider='ollama')
    st.session_state.llm_service = llm_service
else:
    llm_service = st.session_state.llm_service

resume_processor = ResumeProcessor()

# Configure the extractors to use the selected LLM service
if 'llm_service' in st.session_state:
    # Update the global llm_service used by extractors
    import llm_service as llm_service_module
    llm_service_module.llm_service = st.session_state.llm_service

system_info = get_system_info()
location_info = get_location_info()

sec_token = generate_security_token()

st.markdown('''<h5 style='text-align: left; color: #021659;'> Upload Candidate Resume for Evaluation</h5>''', unsafe_allow_html=True)

# Debug mode toggle
debug_mode = False

if debug_mode:
    st.info("**Debug Mode Enabled**: You will see detailed LLM interactions including prompts and raw responses for each extraction step.")

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
    """Extract career transition history using LLM-powered analysis."""
    from analyzers import CareerTransitionAnalyzer
    
    if not work_experiences or len(work_experiences) < 2:
        return "No transitions detected"
    
    # Create a mock resume object with work experiences
    class MockResume:
        def __init__(self, work_experiences):
            self.work_experiences = work_experiences
    
    mock_resume = MockResume(work_experiences)
    analyzer = CareerTransitionAnalyzer()
    
    try:
        result = analyzer.analyze(mock_resume)
        transitions = result.get('transitions', 'No transitions detected')
        return transitions
    except Exception as e:
        # Fallback to simple analysis if LLM fails
        st.warning(f"LLM analysis failed, using basic analysis: {e}")
        return "Career transition analysis unavailable"

def _calculate_field_specific_career_level(resume, target_field):
    """Calculate career level specific to target field using LLM analysis."""
    from analyzers import FieldCareerLevelAnalyzer
    
    if not resume.work_experiences:
        return "Entry Level"
    
    analyzer = FieldCareerLevelAnalyzer()
    
    try:
        result = analyzer.analyze(resume, target_field=target_field)
        career_level = result.get('field_career_level', 'Entry Level')
        return career_level
    except Exception as e:
        # Fallback to basic analysis if LLM fails
        st.warning(f"LLM analysis failed, using basic analysis: {e}")
        return "Career level analysis unavailable"

def _is_experience_relevant_to_field(experience, target_field):
    """Determine if work experience is relevant to target field using LLM analysis."""
    from analyzers import ExperienceRelevanceAnalyzer
    
    if not experience.job_title and not experience.responsibilities and not experience.technologies:
        return False
    
    analyzer = ExperienceRelevanceAnalyzer()
    
    try:
        result = analyzer.analyze(experience, target_field=target_field)
        relevance_score = result.get('relevance_score', 0)
        return relevance_score >= 5  # Consider score of 5+ as relevant
    except Exception as e:
        # Fallback to basic keyword matching if LLM fails
        return _basic_keyword_relevance_check(experience, target_field)
    
def _basic_keyword_relevance_check(experience, target_field):
    """Fallback keyword-based relevance check for all business domains."""
    # Combine all text for analysis
    exp_text = f"{experience.job_title or ''} {' '.join(experience.responsibilities or [])} {' '.join(experience.technologies or [])}".lower()
    
    field_keywords = {
        # Technology Fields
        "Data Science & Analytics": ['data', 'analytics', 'scientist', 'analyst', 'machine learning', 'python', 'sql', 'tableau', 'pandas', 'numpy', 'statistics', 'modeling'],
        "Web Development": ['web', 'frontend', 'javascript', 'react', 'html', 'css', 'vue', 'angular', 'web developer', 'ui', 'ux'],
        "Backend Development": ['backend', 'api', 'server', 'java', 'python', 'node.js', 'spring', 'django', 'flask', 'database'],
        "Mobile Development": ['mobile', 'android', 'ios', 'swift', 'kotlin', 'app', 'react native', 'flutter', 'xamarin'],
        "DevOps & Cloud": ['devops', 'cloud', 'aws', 'docker', 'kubernetes', 'jenkins', 'terraform', 'infrastructure', 'ci/cd'],
        "Machine Learning": ['machine learning', 'ml', 'ai', 'tensorflow', 'pytorch', 'deep learning', 'neural network', 'nlp'],
        "Cybersecurity": ['security', 'cybersecurity', 'penetration', 'vulnerability', 'firewall', 'encryption', 'compliance'],
        "Software Engineering": ['software', 'developer', 'programming', 'code', 'development', 'engineer', 'application'],
        
        # Healthcare Fields
        "Healthcare Administration": ['healthcare', 'hospital', 'medical', 'administration', 'health system', 'patient care', 'clinical'],
        "Nursing": ['nurse', 'nursing', 'patient care', 'medical', 'clinical', 'healthcare', 'rn', 'lpn'],
        "Medical Practice": ['doctor', 'physician', 'medical', 'clinical', 'patient', 'diagnosis', 'treatment', 'medicine'],
        "Pharmaceuticals": ['pharmaceutical', 'drug', 'medicine', 'clinical trial', 'research', 'fda', 'regulatory'],
        
        # Finance & Banking
        "Investment Banking": ['investment', 'banking', 'financial', 'equity', 'debt', 'ipo', 'mergers', 'acquisitions'],
        "Financial Analysis": ['financial', 'analysis', 'budget', 'forecast', 'modeling', 'excel', 'accounting', 'finance'],
        "Accounting": ['accounting', 'bookkeeping', 'audit', 'tax', 'gaap', 'financial statements', 'cpa'],
        "Insurance": ['insurance', 'claims', 'underwriting', 'risk assessment', 'actuarial', 'policy'],
        "Risk Management": ['risk', 'compliance', 'audit', 'regulatory', 'governance', 'control'],
        
        # Marketing & Sales
        "Digital Marketing": ['marketing', 'digital', 'seo', 'sem', 'social media', 'content', 'campaigns', 'analytics'],
        "Sales Management": ['sales', 'business development', 'account management', 'revenue', 'quota', 'crm'],
        "Brand Management": ['brand', 'marketing', 'advertising', 'positioning', 'campaign', 'creative'],
        "Market Research": ['research', 'market', 'survey', 'analysis', 'consumer', 'insights', 'data'],
        "Public Relations": ['pr', 'public relations', 'media', 'communications', 'press', 'reputation'],
        
        # Operations & Supply Chain
        "Operations Management": ['operations', 'process', 'efficiency', 'improvement', 'lean', 'six sigma', 'production'],
        "Logistics": ['logistics', 'supply chain', 'warehouse', 'shipping', 'distribution', 'inventory'],
        "Manufacturing": ['manufacturing', 'production', 'quality', 'assembly', 'factory', 'industrial'],
        "Quality Assurance": ['quality', 'testing', 'inspection', 'standards', 'iso', 'compliance'],
        
        # Human Resources
        "Talent Acquisition": ['recruiting', 'talent', 'hiring', 'hr', 'recruitment', 'staffing', 'sourcing'],
        "HR Business Partnering": ['hr', 'human resources', 'employee relations', 'performance', 'development'],
        "Compensation & Benefits": ['compensation', 'benefits', 'payroll', 'salary', 'rewards', 'hr'],
        "Training & Development": ['training', 'development', 'learning', 'education', 'coaching', 'mentoring'],
        
        # Legal
        "Corporate Law": ['legal', 'law', 'attorney', 'lawyer', 'corporate', 'contracts', 'compliance'],
        "Litigation": ['litigation', 'court', 'trial', 'legal', 'dispute', 'attorney', 'law'],
        "Compliance": ['compliance', 'regulatory', 'audit', 'legal', 'governance', 'risk'],
        "Paralegal": ['paralegal', 'legal', 'research', 'documentation', 'court', 'law'],
        
        # Education
        "Teaching": ['teacher', 'teaching', 'education', 'classroom', 'curriculum', 'instruction', 'student'],
        "Educational Administration": ['education', 'administration', 'school', 'academic', 'principal', 'dean'],
        "Curriculum Development": ['curriculum', 'education', 'instructional design', 'learning', 'academic'],
        
        # Consulting
        "Management Consulting": ['consulting', 'strategy', 'management', 'advisory', 'business analysis'],
        "Strategy": ['strategy', 'strategic', 'planning', 'consulting', 'analysis', 'business'],
        "Business Analysis": ['business analyst', 'analysis', 'requirements', 'process', 'systems'],
        
        # Government & Public Service
        "Public Administration": ['government', 'public', 'administration', 'policy', 'municipal', 'federal'],
        "Policy Development": ['policy', 'government', 'regulatory', 'public', 'legislation'],
        
        # Non-Profit
        "Program Management": ['program', 'non-profit', 'nonprofit', 'community', 'social', 'outreach'],
        "Fundraising": ['fundraising', 'development', 'donations', 'grants', 'non-profit', 'charity'],
        
        # Real Estate
        "Property Management": ['property', 'real estate', 'leasing', 'rental', 'maintenance', 'tenant'],
        "Real Estate Development": ['real estate', 'development', 'construction', 'property', 'investment'],
        
        # Media & Communications
        "Journalism": ['journalism', 'reporter', 'news', 'media', 'writing', 'editor'],
        "Content Creation": ['content', 'writing', 'creative', 'media', 'digital', 'social'],
        "Broadcasting": ['broadcasting', 'television', 'radio', 'media', 'production'],
        
        # Retail & Consumer
        "Retail Management": ['retail', 'store', 'customer service', 'sales', 'merchandise', 'management'],
        "Merchandising": ['merchandising', 'retail', 'product', 'display', 'inventory', 'buying'],
        "Customer Experience": ['customer', 'service', 'experience', 'satisfaction', 'support', 'relations'],
        
        # Energy & Utilities
        "Energy Management": ['energy', 'utilities', 'power', 'renewable', 'grid', 'sustainability'],
        "Environmental Services": ['environmental', 'sustainability', 'green', 'conservation', 'climate'],
        
        # Construction & Engineering
        "Civil Engineering": ['civil', 'engineering', 'construction', 'infrastructure', 'design', 'project'],
        "Project Management": ['project management', 'pmp', 'agile', 'scrum', 'planning', 'coordination'],
        "Architecture": ['architecture', 'design', 'building', 'construction', 'planning', 'cad']
    }
    
    keywords = field_keywords.get(target_field, [])
    return any(keyword in exp_text for keyword in keywords)

def _extract_months_from_duration(duration_str):
    """Extract months from duration string, handling various formats properly."""
    if not duration_str:
        return 12
    
    duration_lower = duration_str.lower().strip()
    
    import re
    
    # First, check for explicit year/month patterns
    # Pattern: "X years Y months" or "X year Y month"
    year_month_pattern = r'(\d+)\s*(?:years?|yrs?)\s*(?:and\s*)?(?:(\d+)\s*(?:months?|mos?))?'
    match = re.search(year_month_pattern, duration_lower)
    if match:
        years = int(match.group(1))
        months = int(match.group(2)) if match.group(2) else 0
        return years * 12 + months
    
    # Pattern: "X months Y days" or just "X months"
    month_pattern = r'(\d+)\s*(?:months?|mos?)'
    match = re.search(month_pattern, duration_lower)
    if match:
        months = int(match.group(1))
        return months
    
    # Pattern: "X years" only
    year_pattern = r'(\d+)\s*(?:years?|yrs?)'
    match = re.search(year_pattern, duration_lower)
    if match:
        years = int(match.group(1))
        return years * 12
    
    # Handle date range patterns like "Jan 2020 - Dec 2022" or "2020-2023"
    date_range_patterns = [
        r'(\w+\s+\d{4})\s*[-–—to]\s*(\w+\s+\d{4})',  # "Jan 2020 - Dec 2022"
        r'(\d{1,2}/\d{4})\s*[-–—to]\s*(\d{1,2}/\d{4})',  # "01/2020 - 12/2022"
        r'(\d{4})\s*[-–—to]\s*(\d{4})',  # "2020-2023"
        r'(\d{4})\s*[-–—to]\s*present',  # "2020-Present"
    ]
    
    for pattern in date_range_patterns:
        match = re.search(pattern, duration_lower)
        if match:
            start_str = match.group(1)
            end_str = match.group(2) if len(match.groups()) > 1 else "present"
            
            # Parse years from the date range
            start_year_match = re.search(r'\d{4}', start_str)
            if end_str == "present":
                from datetime import datetime
                end_year = datetime.now().year
            else:
                end_year_match = re.search(r'\d{4}', end_str)
                end_year = int(end_year_match.group()) if end_year_match else None
            
            if start_year_match and end_year:
                start_year = int(start_year_match.group())
                years_diff = max(0, end_year - start_year)
                return years_diff * 12
    
    # Fallback: look for standalone numbers with context clues
    numbers = re.findall(r'\d+', duration_lower)
    if numbers:
        # Filter out obviously wrong numbers (like years 2020+)
        valid_numbers = [int(n) for n in numbers if int(n) < 2000]
        
        if valid_numbers:
            value = valid_numbers[0]
            
            # Use context to determine if it's years or months
            if any(keyword in duration_lower for keyword in ['year', 'yr', 'yrs']):
                return min(value * 12, 600)  # Cap at 50 years max
            elif any(keyword in duration_lower for keyword in ['month', 'mon', 'mos']):
                return min(value, 600)  # Cap at 50 years max
            else:
                # If no clear indicator, be conservative
                if value <= 12:
                    return value * 12  # Assume years for small numbers
                else:
                    return min(value, 600)  # Assume months for larger numbers, with cap
    
    # Default fallback
    return 12

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

def prepare_user_data_from_resume(resume, system_info, location_info, sec_token, pdf_name, raw_resume_text=None):
    """Prepare user data from Resume object for database insertion with field-specific career analysis and raw text."""
    
    # Use AI-extracted field, with intelligent fallbacks
    reco_field = resume.primary_field or "General"
    
    # Comprehensive field determination if AI extraction failed
    if reco_field == "General" and resume.skills:
        skills_str = " ".join(resume.skills).lower()
        job_title = (resume.work_experiences[0].job_title if resume.work_experiences else "").lower()
        
        # Technology & Engineering
        if any(skill in skills_str for skill in ['python', 'data science', 'machine learning', 'analytics', 'sql', 'tableau', 'pandas', 'numpy', 'scikit-learn']):
            reco_field = "Data Science & Analytics"
        elif any(skill in skills_str for skill in ['javascript', 'react', 'web', 'frontend', 'html', 'css', 'vue', 'angular', 'jquery']):
            reco_field = "Web Development"
        elif any(skill in skills_str for skill in ['java', 'backend', 'api', 'spring', 'django', 'flask', 'node.js', 'express', 'microservices']):
            reco_field = "Backend Development"
        elif any(skill in skills_str for skill in ['mobile', 'android', 'ios', 'swift', 'kotlin', 'react native', 'flutter', 'xamarin']):
            reco_field = "Mobile Development"
        elif any(skill in skills_str for skill in ['aws', 'docker', 'kubernetes', 'devops', 'jenkins', 'terraform', 'ansible', 'ci/cd']):
            reco_field = "DevOps & Cloud"
        elif any(skill in skills_str for skill in ['ai', 'artificial intelligence', 'deep learning', 'neural networks', 'tensorflow', 'pytorch']):
            reco_field = "AI/Artificial Intelligence"
        elif any(skill in skills_str for skill in ['cybersecurity', 'security', 'penetration testing', 'ethical hacking', 'firewall', 'encryption']):
            reco_field = "Cybersecurity"
        elif any(skill in skills_str for skill in ['blockchain', 'cryptocurrency', 'smart contracts', 'ethereum', 'solidity', 'web3']):
            reco_field = "Blockchain"
        elif any(skill in skills_str for skill in ['game development', 'unity', 'unreal engine', 'game design', 'c#', 'gamedev']):
            reco_field = "Game Development"
        
        # Business & Management
        elif any(skill in skills_str for skill in ['business analysis', 'requirements gathering', 'process improvement', 'stakeholder management']):
            reco_field = "Business Analysis"
        elif any(skill in skills_str for skill in ['project management', 'agile', 'scrum', 'pmp', 'kanban', 'jira']) or 'project manager' in job_title:
            reco_field = "Project Management"
        elif any(skill in skills_str for skill in ['product management', 'product strategy', 'roadmap', 'user stories']) or 'product manager' in job_title:
            reco_field = "Product Management"
        elif any(skill in skills_str for skill in ['human resources', 'hr', 'recruitment', 'talent acquisition', 'employee relations']):
            reco_field = "Human Resources"
        elif any(skill in skills_str for skill in ['accounting', 'financial analysis', 'finance', 'bookkeeping', 'audit', 'tax']):
            reco_field = "Finance & Accounting"
        elif any(skill in skills_str for skill in ['marketing', 'digital marketing', 'content marketing', 'brand management', 'seo', 'sem']):
            reco_field = "Marketing & Advertising"
        elif any(skill in skills_str for skill in ['sales', 'business development', 'lead generation', 'crm', 'salesforce']):
            reco_field = "Sales"
        elif any(skill in skills_str for skill in ['customer service', 'customer support', 'help desk', 'client relations']):
            reco_field = "Customer Service"
        
        # Healthcare & Science
        elif any(skill in skills_str for skill in ['nursing', 'patient care', 'medical', 'healthcare', 'clinical']):
            reco_field = "Healthcare & Medical"
        elif any(skill in skills_str for skill in ['pharmacy', 'pharmaceutical', 'drug development', 'clinical trials']):
            reco_field = "Pharmacy"
        elif any(skill in skills_str for skill in ['laboratory', 'lab', 'research', 'biotechnology', 'biology', 'chemistry']):
            reco_field = "Laboratory Science"
        
        # Creative & Media
        elif any(skill in skills_str for skill in ['graphic design', 'photoshop', 'illustrator', 'design', 'visual design']):
            reco_field = "Graphic Design"
        elif any(skill in skills_str for skill in ['ui/ux', 'user experience', 'user interface', 'figma', 'sketch']):
            reco_field = "UI/UX Design"
        elif any(skill in skills_str for skill in ['content writing', 'copywriting', 'writing', 'content creation', 'blogging']):
            reco_field = "Content Writing"
        elif any(skill in skills_str for skill in ['photography', 'photo editing', 'camera', 'video production', 'editing']):
            reco_field = "Photography"
        elif any(skill in skills_str for skill in ['architecture', 'autocad', 'architectural design', 'building design']):
            reco_field = "Architecture"
        
        # Education & Training
        elif any(skill in skills_str for skill in ['teaching', 'education', 'curriculum', 'training', 'instructor']) or 'teacher' in job_title:
            reco_field = "Education & Teaching"
        
        # Legal & Government
        elif any(skill in skills_str for skill in ['legal', 'law', 'attorney', 'lawyer', 'paralegal', 'litigation']):
            reco_field = "Legal & Law"
        elif any(skill in skills_str for skill in ['government', 'public service', 'policy', 'administration']):
            reco_field = "Government & Public Service"
        
        # Other Fields
        elif any(skill in skills_str for skill in ['manufacturing', 'production', 'quality control', 'lean', 'six sigma']):
            reco_field = "Manufacturing"
        elif any(skill in skills_str for skill in ['supply chain', 'logistics', 'procurement', 'inventory', 'warehouse']):
            reco_field = "Supply Chain & Logistics"
        elif any(skill in skills_str for skill in ['real estate', 'property management', 'real estate agent', 'broker']):
            reco_field = "Real Estate"
        elif any(skill in skills_str for skill in ['retail', 'sales associate', 'merchandising', 'store management']):
            reco_field = "Retail"
        elif any(skill in skills_str for skill in ['hospitality', 'hotel', 'restaurant', 'tourism', 'food service']):
            reco_field = "Hospitality & Tourism"
    
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
    
    print(f"Working Experience Details: {work_exp_details}")
    print("-"*50)
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
    print(f"Education Details: {education_details}")
    print("-"*50)
    
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
    
    print(f"Full Resume Summary: {full_resume_summary}")
    print("-"*50)
    
    # Debug info for raw text
    if raw_resume_text:
        print(f"Raw Resume Text Length: {len(raw_resume_text)} characters")
        print(f"Raw Resume Text Preview: {raw_resume_text[:200]}...")
    else:
        print("No raw resume text provided")
    print("-"*50)
    
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
        'contact_info': f"{resume.email or ''} | {resume.contact_number or ''} | {resume.linkedin or ''} | {resume.github or ''}",
        
        # NEW: Raw resume text for comprehensive chatbot context
        'raw_resume_text': raw_resume_text or 'Not available'
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

        if debug_mode:
            st.markdown("### 📄 **File Processing Debug Info**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**File Information:**")
                st.info(f"**File Name:** {pdf_file.name}")
                st.info(f"**File Size:** {len(pdf_file.getbuffer())} bytes")
                st.info(f"**Save Path:** {save_image_path}")
                
            with col2:
                st.markdown("**LLM Service Status:**")
                st.info(f"**Model:** {llm_model}")
                st.info(f"**Service Available:** {'✅ Yes' if llm_service.is_available() else '❌ No'}")
                st.info(f"**Connection Tested:** {'✅ Yes' if llm_service.connection_tested else '⏳ Pending'}")

        # Display PDF
        pdf_display_html = show_pdf(save_image_path)
        st.markdown(pdf_display_html, unsafe_allow_html=True)

        if llm_service.is_available():
            try:
                # Process resume with debug mode if enabled
                if debug_mode:
                    st.markdown("---")
                    st.markdown("### 🐛 **LLM Debug Information**")
                    st.markdown("Below you can see the detailed extraction process with raw prompts and responses:")
                    
                    # Show LLM Configuration Details
                    st.markdown("#### 🔧 **LLM Configuration**")
                    
                    # Current Active Configuration
                    active_config = {
                        "Model Name": llm_service.model_name,
                        "Base URL": llm_service.base_url,
                        "Temperature": llm_service.llm.temperature if llm_service.llm else "N/A",
                        "Max Tokens (num_predict)": llm_service.llm.num_predict if llm_service.llm else "N/A",
                        "Top K": llm_service.llm.top_k if llm_service.llm else "N/A", 
                        "Top P": llm_service.llm.top_p if llm_service.llm else "N/A",
                        "Connection Status": "✅ Connected" if llm_service.is_available() else "❌ Not Connected"
                    }
                    
                    # Default Configuration from config.py
                    default_config = {
                        "Default Model": LLM_CONFIG['default_model'],
                        "Default URL": LLM_CONFIG['default_url'],
                        "Default Temperature": LLM_CONFIG['temperature'],
                        "Default Max Tokens": LLM_CONFIG['num_predict'],
                        "Default Top K": LLM_CONFIG['top_k'],
                        "Default Top P": LLM_CONFIG['top_p'],
                        "Timeout": LLM_CONFIG.get('timeout', 'Not set')
                    }
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown("**Active Configuration:**")
                        st.json(active_config)
                    with col2:
                        st.markdown("**Default Configuration:**")
                        st.json(default_config)
                    with col3:
                        st.markdown("**Parameter Explanation:**")
                        st.write("• **Temperature**: Controls randomness")
                        st.write("  - 0.1 = More focused/deterministic")
                        st.write("  - 1.0 = More creative/random")
                        st.write("• **Max Tokens**: Maximum response length")
                        st.write("• **Top K**: Limits vocabulary to top K words")
                        st.write("• **Top P**: Nucleus sampling threshold")
                        st.write("• **Timeout**: Request timeout in seconds")
                
                resume, raw_extracted_text = resume_processor.process_resume(save_image_path, debug_mode)

                if resume and resume.name != "Unknown":
                    
                    if debug_mode:
                        st.markdown("---")
                        st.markdown("### ✅ **Final Extraction Summary**")
                        st.success("Resume processing completed successfully!")
                        
                        # Show extraction summary
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Profile Fields", len([v for v in [resume.name, resume.email, resume.contact_number, resume.linkedin, resume.github] if v]))
                        with col2:
                            st.metric("Skills Found", len(resume.skills))
                        with col3:
                            st.metric("Work Experiences", len(resume.work_experiences))
                        with col4:
                            st.metric("Education Entries", len(resume.educations))
                        
                        st.markdown("**Key Extracted Data:**")
                        debug_summary = {
                            "Name": resume.name or "Not found",
                            "Email": resume.email or "Not found", 
                            "Years of Experience": resume.YoE or "Not calculated",
                            "Career Level": resume.career_level or "Not determined",
                            "Primary Field": resume.primary_field or "Not determined",
                            "Skills Count": len(resume.skills),
                            "Work Experience Count": len(resume.work_experiences),
                            "Education Count": len(resume.educations)
                        }
                        st.json(debug_summary)
                        
                        # Show raw text information
                        st.markdown("**Raw Text Information:**")
                        st.info(f"Raw text captured: {len(raw_extracted_text)} characters")
                        with st.expander("Raw Text Preview (First 500 chars)"):
                            st.text(raw_extracted_text[:500] + "..." if len(raw_extracted_text) > 500 else raw_extracted_text)

                    # Display result in a structured way
                    display_resume_results(resume, debug_mode)

                    # Prepare data for database with raw text
                    user_data = prepare_user_data_from_resume(
                        resume, system_info, location_info, sec_token, pdf_name, raw_extracted_text
                    )

                    # Insert into ChromaDB vector database
                    insertion_success = db_manager.insert_user_data(user_data)


                else:
                    if debug_mode:
                        st.markdown("---")
                        st.markdown("### ❌ **Debug: Extraction Issues**")
                        st.error("Resume processing completed but no valid data was extracted.")
                        st.warning("This usually indicates:")
                        st.write("• PDF text extraction failed")
                        st.write("• LLM responses were not in the expected format")
                        st.write("• The resume format is not compatible with the extractors")
                    
                    st.warning("Resume processing completed with limited data extraction.")
            except Exception as e:
                if debug_mode:
                    st.markdown("---")
                    st.markdown("### 🚨 **Debug: Processing Error**")
                    st.error(f"Resume processing failed: {str(e)}")
                    st.exception(e)
                    st.markdown("**Troubleshooting Tips:**")
                    st.write("• Check if Ollama is running: `ollama serve`")
                    st.write("• Verify the model is available: `ollama list`")
                    st.write("• Check PDF file is not corrupted")
                    st.write("• Try with a different PDF or smaller file")
                else:
                    st.error(f"Resume processing failed: {str(e)}")
        
        else:
            if debug_mode:
                st.markdown("---")
                st.markdown("### 🚨 **Debug: LLM Service Error**")
                st.error("**LLM service not available.** Please check your Ollama configuration.")
                st.markdown("**Debug Steps:**")
                st.code("""
# Check if Ollama is running
ollama serve

# List available models  
ollama list

# Pull the required model if not available
ollama pull gemma3:12b
                """)
                st.write("**Current Configuration:**")
                st.json({
                    "Model": llm_model,
                    "Base URL": llm_service.base_url,
                    "Connection Tested": llm_service.connection_tested
                })
            else:
                st.error("**LLM service not available.** Please check your Ollama configuration.")