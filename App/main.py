"""
Main application entry point using the new specialized extractor architecture.
AI Resume Analyzer - HR Edition | Made with Streamlit
"""

###### Packages Used ######
import streamlit as st
import pandas as pd
import base64
import time
import plotly.express as px
import plotly.graph_objects as go

# Import configuration and services
from config import PAGE_CONFIG, ADMIN_CONFIG
from database import db_manager
from utils import (
    get_system_info, get_location_info, get_current_timestamp,
    get_csv_download_link, show_pdf, prepare_feedback_data, 
    validate_file_upload, generate_security_token
)

# Import new specialized processor
from resume_processor import ResumeProcessor
from llm_service import llm_service
from llm_utils import (
    format_metadata_for_display, export_metadata_to_json,
    display_clean_hr_summary, get_available_ollama_models
)

from streamlit_tags import st_tags
from PIL import Image
import nltk
nltk.download('stopwords')

# Set page configuration
st.set_page_config(**PAGE_CONFIG)

# Initialize resume processor (uses sequential processing optimized for local Ollama)
resume_processor = ResumeProcessor()


def run():
    """Main application function."""
    
    # Logo and navigation
    img = Image.open('./Logo/RESUM.png')
    st.image(img)
    st.sidebar.markdown("# Choose Module...")
    activities = ["Candidate Evaluation", "Feedback", "About", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    
    # Model selection in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🤖 AI Model")
    llm_model = st.sidebar.selectbox(
        "Select AI Model",
        options=["gemma3:12b", "gemma3:27b", "deepseek-r1:14b"],
        index=0,  # Default to 12b for better performance
        help="gemma3:12b is fastest, gemma3:27b is more accurate, deepseek-r1:14b is reasoning model"
    )
    
    # Update LLM service configuration if model changed
    if llm_model != llm_service.model_name:
        llm_service.update_model(llm_model)
    
    # Visitor counter
    st.sidebar.markdown('''
        <!-- site visitors -->
        <div id="sfct2xghr8ak6lfqt3kgru233378jya38dy" hidden></div>
        <noscript>
            <a href="https://www.freecounterstat.com" title="hit counter">
                <img src="https://counter9.stat.ovh/private/freecounterstat.php?c=t2xghr8ak6lfqt3kgru233378jya38dy" border="0" title="hit counter" alt="hit counter"> -->
            </a>
        </noscript>
        <p>Visitors <img src="https://counter9.stat.ovh/private/freecounterstat.php?c=t2xghr8ak6lfqt3kgru233378jya38dy" title="Free Counter" Alt="web counter" width="60px"  border="0" /></p>
    ''', unsafe_allow_html=True)

    ###### CODE FOR CLIENT SIDE (USER) ######
    if choice == 'Candidate Evaluation':
        handle_candidate_evaluation()
    
    ###### CODE FOR FEEDBACK SIDE ######
    elif choice == 'Feedback':
        handle_feedback()
    
    ###### CODE FOR ABOUT PAGE ######
    elif choice == 'About':
        handle_about()
    
    ###### CODE FOR ADMIN SIDE ######
    else:
        handle_admin()


def handle_candidate_evaluation():
    """Handle candidate evaluation using the new specialized extractor architecture."""
    
    # Get system and location info
    system_info = get_system_info()
    location_info = get_location_info()
    
    # Generate security token
    sec_token = generate_security_token()
    
    st.markdown('''<h5 style='text-align: left; color: #021659;'> Upload Candidate Resume for Evaluation</h5>''', unsafe_allow_html=True)
    
    # Configuration options
    col1, col2 = st.columns(2)
    
    with col1:
        # Development mode toggle
        dev_mode = st.checkbox(
            "🚀 **Development Mode** - Show detailed extraction process", 
            help="Display detailed information about the extraction process including individual extractor results"
        )
        if dev_mode:
            st.info("💡 **Development Mode Enabled:** You'll see detailed information about each specialized extractor.")
    
    with col2:
        # LLM extraction toggle
        enable_llm_extraction = st.checkbox(
            "🤖 **LLM-Powered Extraction** - Use AI for structured data extraction", 
            value=True, 
            help="Use specialized extractors with AI for better accuracy"
        )
        if enable_llm_extraction:
            st.info("🔄 **Sequential processing enabled:** Extractors run one at a time (optimized for local Ollama)")
    
    # Show extraction capabilities
    if dev_mode:
        st.subheader("🔧 **Extraction Capabilities**")
        capabilities = resume_processor.get_extraction_capabilities()
        for capability, description in capabilities.items():
            st.write(f"• **{capability}**: {description}")
    
    ## File upload in PDF format
    pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
    
    if pdf_file is not None:
        # Validate file
        if not validate_file_upload(pdf_file):
            return
        
        with st.spinner('🔄 Processing resume with specialized extractors...'):
            time.sleep(2)
        
        ### Save the uploaded resume
        save_image_path = './Uploaded_Resumes/' + pdf_file.name
        pdf_name = pdf_file.name
        
        with open(save_image_path, "wb") as f:
            f.write(pdf_file.getbuffer())
        
        # Display PDF
        show_pdf(save_image_path)
        
        if enable_llm_extraction and llm_service.is_available():
            # Use new specialized extractors
            st.markdown("---")
            st.header("**🤖 AI-Powered Resume Analysis with Specialized Extractors**")
            
            try:
                # Process resume using the new architecture
                resume = resume_processor.process_resume(save_image_path, dev_mode)
                
                if resume and resume.name != "Unknown":
                    st.success("✅ **Resume processed successfully using specialized extractors!**")
                    
                    # Display results in a structured way
                    display_resume_results(resume, dev_mode)
                    
                    # Prepare data for database
                    user_data = prepare_user_data_from_resume(
                        resume, system_info, location_info, sec_token, pdf_name
                    )
                    
                    # Insert into database
                    db_manager.insert_user_data(user_data)
                    
                    # Show success
                    st.balloons()
                    
                else:
                    st.warning("⚠️ Resume processing completed with limited data extraction.")
                    
            except Exception as e:
                st.error(f"❌ Resume processing failed: {str(e)}")
                if dev_mode:
                    st.exception(e)
        
        else:
            if not enable_llm_extraction:
                st.info("💡 **Enable LLM-powered extraction for AI analysis.**")
            else:
                st.error("❌ **LLM service not available.** Please check your Ollama configuration.")


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
    st.subheader("📋 **Resume Completeness Analysis**")
    
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
            st.metric("Status", "⚠️", delta="Issues Found")
        else:
            st.metric("Status", "✅", delta="Ready")
    
    # === GAP ANALYSIS SECTION ===
    if any(gap_list for gap_list in gaps.values() if gap_list):
        st.subheader("⚠️ **Gap Analysis - Missing Information**")
        
        # Critical missing information
        if gaps["critical_missing"]:
            st.error("**Critical Missing Information:**")
            for gap in gaps["critical_missing"]:
                st.write(f"  {gap}")
        
        # Professional profile gaps
        if gaps["professional_missing"]:
            st.warning("**Professional Profile Gaps:**")
            for gap in gaps["professional_missing"]:
                st.write(f"  {gap}")
        
        # Detail gaps (HR focus - what information they don't have)
        if gaps["detail_gaps"]:
            st.info("**Information Gaps for HR Review:**")
            for gap in gaps["detail_gaps"]:
                st.write(f"  {gap}")
    else:
        st.success("✅ **No Major Gaps Detected** - This resume appears complete for general screening.")
    
    # === DETAILED INFORMATION SECTIONS ===
    st.markdown("---")
    
    # Profile Information
    if resume.name or resume.email or resume.contact_number:
        with st.expander("👤 **Profile Information**", expanded=dev_mode):
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
        with st.expander(f"🛠️ **Skills ({len(resume.skills)} found)**", expanded=dev_mode):
            st.write(", ".join(resume.skills))
    
    # Work Experience
    if resume.work_experiences:
        with st.expander(f"💼 **Work Experience ({len(resume.work_experiences)} entries)**", expanded=dev_mode):
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
                        st.warning(f"⚠️ HR Note: Missing {', '.join(missing)} - may need follow-up")
    
    # Education
    if resume.educations:
        with st.expander(f"🎓 **Education ({len(resume.educations)} entries)**", expanded=dev_mode):
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
                        st.warning(f"⚠️ HR Note: Missing {', '.join(missing)} - may need follow-up")
    
    # Years of Experience & Experience Analysis
    with st.expander("📈 **Experience Analysis**", expanded=dev_mode):
        # Career Assessment Section
        st.subheader("🎯 **Career Assessment**")
        
        # Create columns for career information
        career_col1, career_col2, career_col3 = st.columns(3)
        
        with career_col1:
            if resume.YoE:
                st.write(f"**Total Experience:** {resume.YoE}")
            else:
                st.write("**Total Experience:** Not calculated")
        
        with career_col2:
            if resume.career_level:
                # Add visual indicators for career levels
                level_indicators = {
                    "Entry Level": "🟢",
                    "Mid Level": "🟡", 
                    "Senior Level": "🟠",
                    "Executive Level": "🔴"
                }
                indicator = level_indicators.get(resume.career_level, "⚪")
                st.write(f"**Career Level:** {indicator} {resume.career_level}")
            else:
                st.write("**Career Level:** Not determined")
        
        with career_col3:
            if resume.primary_field:
                st.write(f"**Primary Field:** {resume.primary_field}")
            else:
                st.write("**Primary Field:** Not determined")
        
        # Experience Breakdown
        st.subheader("📊 **Experience Breakdown**")
        
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
                        st.warning(f"⚠️ **HR Alert:** Experience discrepancy detected!")
                        st.info(f"• **AI Calculated:** {ai_years} years")
                        st.info(f"• **From Duration Data:** {actual_years:.1f} years ({actual_months} months)")
                        st.info(f"• **Discrepancy:** {abs(ai_years - actual_years):.1f} years")
                        
                        if ai_years > actual_years:
                            st.warning("💡 **HR Note:** AI may be including undated experience or making assumptions. Verify during interview.")
                        else:
                            st.warning("💡 **HR Note:** Some experience durations may not be properly extracted. Check original resume.")
                        
                        # Show which entries lack duration data
                        missing_duration = [exp for exp in resume.work_experiences if not exp.duration or exp.duration == "Duration not specified"]
                        if missing_duration:
                            st.info(f"📝 **Missing Duration Info:** {len(missing_duration)} of {len(resume.work_experiences)} positions lack duration data")
                    else:
                        st.success(f"✅ **Experience Validation:** AI calculation ({ai_years} years) matches duration data ({actual_years:.1f} years)")
                        
                except Exception as e:
                    if dev_mode:
                        st.warning(f"⚠️ **Debug:** Experience validation failed: {e}")
            
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
                            st.info(f"💡 **HR Note:** {years} years of experience may not align with {resume.career_level} classification. Consider validation during interview.")
                except:
                    pass  # Skip validation if parsing fails
                
            # Debug information for development mode
            if dev_mode and not resume.YoE and resume.work_experiences:
                st.warning("⚠️ **Debug Info:** YoE extraction may have failed. Work experience entries found but total experience not calculated.")
                for i, exp in enumerate(resume.work_experiences, 1):
                    if exp.duration:
                        st.write(f"  - Position {i}: {exp.duration}")
        else:
            st.write("**Work Experience Entries:** 0")
            st.warning("⚠️ **HR Note:** No work experience found - may indicate recent graduate or career changer")
    
    # Download options
    st.markdown("---")
    st.subheader("📥 **Export Options**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # JSON download
        resume_json = resume.model_dump()
        json_str = export_metadata_to_json(resume_json)
        st.download_button(
            label="📄 Download JSON Data",
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
            label="📋 Download Legacy Format",
            data=legacy_json,
            file_name=f"resume_legacy_{resume.name.replace(' ', '_') if resume.name else 'candidate'}.json",
            mime="application/json",
            help="Download in legacy format for compatibility"
        )


def prepare_user_data_from_resume(resume, system_info, location_info, sec_token, pdf_name):
    """Prepare user data from Resume object for database insertion."""
    
    # Use AI-extracted career level and field, with fallbacks
    cand_level = resume.career_level or "Unknown"
    reco_field = resume.primary_field or "General"
    
    # Fallback to rule-based determination if AI extraction failed
    if cand_level == "Unknown" and resume.work_experiences:
        total_exp = len(resume.work_experiences)
        if total_exp >= 3:
            cand_level = "Senior Level"
        elif total_exp >= 2:
            cand_level = "Mid Level"
        else:
            cand_level = "Entry Level"
    
    # Fallback field determination if AI extraction failed
    if reco_field == "General" and resume.skills:
        skills_str = " ".join(resume.skills).lower()
        if any(skill in skills_str for skill in ['python', 'data', 'machine learning', 'analytics']):
            reco_field = "Data Science & Analytics"
        elif any(skill in skills_str for skill in ['javascript', 'react', 'web', 'frontend']):
            reco_field = "Web Development"
        elif any(skill in skills_str for skill in ['java', 'backend', 'api']):
            reco_field = "Backend Development"
        elif any(skill in skills_str for skill in ['mobile', 'android', 'ios']):
            reco_field = "Mobile Development"
    
    # Get completeness score from legacy format for database compatibility
    legacy_data = resume.to_legacy_format()
    completeness_score = legacy_data.get('resume_score', 50)  # Default to 50 if not available
    
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
        'resume_score': str(completeness_score),
        'timestamp': get_current_timestamp(),
        'no_of_pages': str(resume.no_of_pages or 1),
        'reco_field': reco_field,
        'cand_level': cand_level,
        'skills': str(resume.skills),
        'recommended_skills': f"Specialized_Extraction_Analysis_{len(resume.skills)}_skills",
        'courses': f"AI_Recommended_Field: {reco_field}",
        'pdf_name': pdf_name
    }


def handle_feedback():
    """Handle feedback form and display feedback analytics."""
    
    timestamp = get_current_timestamp()
    
    # Feedback Form
    with st.form("my_form"):
        st.write("Feedback form")            
        feed_name = st.text_input('Name')
        feed_email = st.text_input('Email')
        feed_score = st.slider('Rate Us From 1 - 5', 1, 5)
        comments = st.text_input('Comments')
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            # Prepare feedback data
            feedback_data = prepare_feedback_data(feed_name, feed_email, feed_score, comments)
            feedback_data['timestamp'] = timestamp
            
            # Insert feedback
            db_manager.insert_feedback(feedback_data)
            st.success("Thanks! Your Feedback was recorded.") 
            st.balloons()    

    # Get feedback data
    plotfeed_data = db_manager.get_feedback_data()                        

    # Plotting pie chart for user ratings
    if plotfeed_data is not None and not plotfeed_data.empty:
        labels = plotfeed_data.feed_score.unique()
        values = plotfeed_data.feed_score.value_counts()

        st.subheader("**Past User Rating's**")
        fig = px.pie(values=values, names=labels, title="Chart of User Rating Score From 1 - 5", color_discrete_sequence=px.colors.sequential.Aggrnyl)
        st.plotly_chart(fig)

        # Fetching Comment History
        st.subheader("**HR User Comment's**")
        dff = pd.DataFrame(plotfeed_data, columns=['HR User', 'Comment'])
        st.dataframe(dff, width=1000)


def handle_about():
    """Handle about page with system information."""
    
    st.subheader("**About The Tool - AI RESUME ANALYZER (HR Edition)**")

    st.markdown('''
    <p align='justify'>
        An advanced AI-powered HR tool that analyzes candidate resumes using specialized extractors and concurrent processing. 
        The system employs a modular architecture with dedicated extractors for different resume sections, enabling 
        comprehensive evaluation and analysis for HR professionals.
    </p>

    <p align="justify">
        <b>How to use it: -</b> <br/><br/>
        <b>Candidate Evaluation -</b> <br/>
        Upload candidate resumes in PDF format for comprehensive AI-powered analysis. The system uses specialized 
        extractors that work concurrently to extract and analyze different aspects of the resume.<br/><br/>
        
        <b>New Features:</b><br/>
        • <b>Specialized Extractors:</b> Profile, Skills, Education, Experience, and YoE extractors<br/>
        • <b>Concurrent Processing:</b> All extractors run in parallel for faster analysis<br/>
        • <b>Structured Data Models:</b> Pydantic models ensure data quality and consistency<br/>
        • <b>Enhanced Error Handling:</b> Robust processing with intelligent fallbacks<br/>
        • <b>Development Mode:</b> Detailed insights into the extraction process<br/>
        • <b>Resume Scoring:</b> Intelligent completeness scoring algorithm<br/><br/>
        
        <b>Admin -</b> <br/>
        For login use <b>admin</b> as username and <b>@dmin1234</b> as password.<br/>
        Access candidate data, analytics, and system management features.
    </p><br/><br/>

    <p align="justify">
        Enhanced with cutting-edge AI architecture designed specifically for modern HR workflows and recruiting teams.
    </p>
    ''', unsafe_allow_html=True)


def handle_admin():
    """Handle admin panel with analytics and data management."""
    
    st.success('Welcome to Admin Side')

    # Admin Login
    ad_user = st.text_input("Username")
    ad_password = st.text_input("Password", type='password')

    if st.button('Login'):
        
        if ad_user == ADMIN_CONFIG['username'] and ad_password == ADMIN_CONFIG['password']:
            
            # Get analytics data
            plot_data = db_manager.get_analytics_data()
            
            # Total Candidates Count
            user_count = db_manager.get_user_count()
            st.success("Welcome HR Admin! Total %d " % user_count + " Candidates Have Been Evaluated 📊")                
            
            # Get user data
            df = db_manager.get_user_data()
            if df is not None:
                # Rename columns for better display
                df.columns = ['ID', 'Token', 'IP Address', 'HR User', 'HR Email', 'HR Contact', 'Candidate Field', 'Evaluation Date',
                              'Candidate Name', 'Candidate Email', 'Resume Score', 'Pages',  'Resume File',   
                              'Experience Level', 'Skills', 'Analysis Notes', 'Evaluation Summary',
                              'City', 'State', 'Country', 'Location', 'System OS', 'System', 'System User']

                st.header("**Candidate Evaluation Data**")
                st.dataframe(df)
                
                # Download Report
                st.markdown(get_csv_download_link(df,'Candidate_Evaluation_Report.csv','📊 Download Candidate Report'), unsafe_allow_html=True)

            # Get feedback data
            feedback_df = db_manager.get_feedback_data()
            if feedback_df is not None:
                st.header("**HR System Feedback Data**")
                st.dataframe(feedback_df)
                plotfeed_data = feedback_df
            else:
                plotfeed_data = None                        

            # Display analytics charts
            display_admin_charts(plot_data, plotfeed_data, df)

        else:
            st.error("Wrong ID & Password Provided")


def display_admin_charts(plot_data, plotfeed_data, df):
    """Display admin analytics charts."""
    
    if plotfeed_data is not None and not plotfeed_data.empty:
        # HR System ratings
        labels = plotfeed_data.feed_score.unique()
        values = plotfeed_data.feed_score.value_counts()
        
        st.subheader("**HR System Rating's**")
        fig = px.pie(values=values, names=labels, title="HR System Satisfaction Score From 1 - 5 🤗", color_discrete_sequence=px.colors.sequential.Aggrnyl)
        st.plotly_chart(fig)

    if plot_data is not None and not plot_data.empty:
        # Candidate field distribution
        labels = plot_data.Predicted_Field.unique()
        values = plot_data.Predicted_Field.value_counts()

        st.subheader("**Pie-Chart for Candidate Field Distribution**")
        fig = px.pie(df, values=values, names=labels, title='Candidate Field Classification Based on Skills 👽', color_discrete_sequence=px.colors.sequential.Aggrnyl_r)
        st.plotly_chart(fig)

        # Experience level distribution
        labels = plot_data.User_Level.unique()
        values = plot_data.User_Level.value_counts()

        st.subheader("**Pie-Chart for Candidate Experience Level Distribution**")
        fig = px.pie(df, values=values, names=labels, title="Candidate Pool 📈 Experience Level Distribution 👨‍💻", color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig)

        # Resume score distribution
        labels = plot_data.resume_score.unique()                
        values = plot_data.resume_score.value_counts()

        st.subheader("**Pie-Chart for Resume Completeness Score Distribution**")
        fig = px.pie(df, values=values, names=labels, title='Candidate Resume Quality Distribution (0-100) 💯', color_discrete_sequence=px.colors.sequential.Agsunset)
        st.plotly_chart(fig)

        # Geographic distributions
        if hasattr(plot_data, 'City'):
            labels = plot_data.City.unique()
            values = plot_data.City.value_counts()

            st.subheader("**Pie-Chart for Candidate Geographic Distribution - City**")
            fig = px.pie(df, values=values, names=labels, title='Candidate Pool Distribution by City 🌆', color_discrete_sequence=px.colors.sequential.Jet)
            st.plotly_chart(fig)


if __name__ == "__main__":
    run() 