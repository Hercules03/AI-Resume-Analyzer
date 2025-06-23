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
    display_clean_hr_summary, get_available_ollama_models,
    create_model_selection_ui
)

from streamlit_tags import st_tags
from PIL import Image
import nltk
nltk.download('stopwords')

# Set page configuration
st.set_page_config(**PAGE_CONFIG)

# Initialize resume processor
resume_processor = ResumeProcessor()


def run():
    """Main application function."""
    
    # Logo and navigation
    img = Image.open('./Logo/RESUM.png')
    st.image(img)
    st.sidebar.markdown("# Choose Module...")
    activities = ["Candidate Evaluation", "Feedback", "About", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    
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
            st.info("🧠 **AI-powered extraction enabled:** Using specialized extractors with concurrent processing")
    
    # LLM Configuration (only show if LLM extraction is enabled)
    if enable_llm_extraction:
        with st.expander("⚙️ **LLM Configuration**"):
            col_model, col_url = st.columns(2)
            
            with col_url:
                ollama_url = st.text_input(
                    "Ollama URL",
                    value="http://localhost:11434",
                    help="Ollama server URL"
                )
            
            with col_model:
                # Use modular model selection UI
                llm_model = create_model_selection_ui(ollama_url)
            
            # Update LLM service configuration
            if ollama_url != llm_service.base_url or llm_model != llm_service.model_name:
                llm_service.base_url = ollama_url
                llm_service.update_model(llm_model)
    
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


def display_resume_results(resume, dev_mode=False):
    """Display the results from resume processing."""
    
    # Basic information summary
    st.subheader("📊 **Resume Summary**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Resume Score", f"{resume.resume_score}/100")
    with col2:
        st.metric("Skills Found", len(resume.skills))
    with col3:
        st.metric("Work Experience", len(resume.work_experiences))
    with col4:
        st.metric("Education", len(resume.educations))
    
    # Detailed information
    if dev_mode or st.checkbox("🔍 **Show Detailed Analysis**"):
        
        # Profile Information
        if resume.name or resume.email or resume.contact_number:
            st.subheader("👤 **Profile Information**")
            col1, col2, col3 = st.columns(3)
            with col1:
                if resume.name:
                    st.write(f"**Name:** {resume.name}")
            with col2:
                if resume.email:
                    st.write(f"**Email:** {resume.email}")
            with col3:
                if resume.contact_number:
                    st.write(f"**Contact:** {resume.contact_number}")
        
        # Skills
        if resume.skills:
            st.subheader("🛠️ **Skills**")
            st.write(", ".join(resume.skills))
        
        # Work Experience
        if resume.work_experiences:
            st.subheader("💼 **Work Experience**")
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
        
        # Education
        if resume.educations:
            st.subheader("🎓 **Education**")
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
        
        # Years of Experience
        if resume.YoE:
            st.subheader("📈 **Experience Analysis**")
            st.write(f"**Total Experience:** {resume.YoE}")
    
    # Download options
    st.markdown("---")
    st.subheader("📥 **Export Options**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # JSON download
        resume_json = resume.dict()
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
    
    # Calculate enhanced data
    cand_level = "Unknown"
    reco_field = "General"
    
    # Try to determine career level from experience
    if resume.work_experiences:
        total_exp = len(resume.work_experiences)
        if total_exp >= 3:
            cand_level = "Senior Level"
        elif total_exp >= 2:
            cand_level = "Mid Level"
        else:
            cand_level = "Entry Level"
    
    # Try to determine field from skills
    if resume.skills:
        skills_str = " ".join(resume.skills).lower()
        if any(skill in skills_str for skill in ['python', 'data', 'machine learning', 'analytics']):
            reco_field = "Data Science & Analytics"
        elif any(skill in skills_str for skill in ['javascript', 'react', 'web', 'frontend']):
            reco_field = "Web Development"
        elif any(skill in skills_str for skill in ['java', 'backend', 'api']):
            reco_field = "Backend Development"
        elif any(skill in skills_str for skill in ['mobile', 'android', 'ios']):
            reco_field = "Mobile Development"
    
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
        'resume_score': str(resume.resume_score),
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