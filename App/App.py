# AI Resume Analyzer - HR Edition | Made with Streamlit

###### Packages Used ######
import streamlit as st # core package used in this project
import pandas as pd
import base64
import time
import plotly.express as px # to create visualisations at the admin session
import plotly.graph_objects as go

# Import our modular classes
from config import PAGE_CONFIG, ADMIN_CONFIG
from database import db_manager
from pdf_processing import pdf_processor
from utils import (
    get_system_info, get_location_info, get_current_timestamp,
    get_csv_download_link, show_pdf, prepare_user_data, 
    prepare_feedback_data, validate_file_upload
)
from resume_parser import ResumeParser
from llm_extractor import LLMMetadataExtractor
from llm_utils import (
    format_metadata_for_display, export_metadata_to_json,
    display_clean_hr_summary, get_available_ollama_models,
    create_model_selection_ui
)
from streamlit_tags import st_tags
from PIL import Image
# Note: Course recommendations removed for HR-focused system
import nltk
nltk.download('stopwords')

st.set_page_config(**PAGE_CONFIG)

def run():
    
    # (Logo, Heading, Sidebar etc)
    img = Image.open('./Logo/RESUM.png')
    st.image(img)
    st.sidebar.markdown("# Choose Module...")
    activities = ["Candidate Evaluation", "Feedback", "About", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    # link = '<b>Built with 🤍 by <a href="https://dnoobnerd.netlify.app/" style="text-decoration: none; color: #021659;">Deepak Padhi</a></b>' 
    # st.sidebar.markdown(link, unsafe_allow_html=True)
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
        
        # Get system and location info using modular utilities
        system_info = get_system_info()
        location_info = get_location_info()
        
        # Extract individual values for backward compatibility
        from utils import generate_security_token
        sec_token = generate_security_token()
        host_name = system_info['host_name']
        ip_add = system_info['ip_add']
        dev_user = system_info['dev_user']
        os_name_ver = system_info['os_name_ver']
        latlong = location_info['latlong']
        city = location_info['city']
        state = location_info['state']
        country = location_info['country']


        # Upload Resume
        st.markdown('''<h5 style='text-align: left; color: #021659;'> Upload Candidate Resume for Evaluation</h5>''',unsafe_allow_html=True)
        
        # Configuration options
        col1, col2 = st.columns(2)
        
        with col1:
            # Development mode toggle
            dev_mode = st.checkbox("🚀 **Development Mode** - Compare extraction methods", help="Show side-by-side comparison of PyMuPDF vs EasyOCR extraction methods with detailed metrics")
            if dev_mode:
                st.info("💡 **Development Mode Enabled:** You'll see detailed comparison between PyMuPDF and EasyOCR extraction methods including performance metrics, quality analysis, and text previews.")
        
        with col2:
            # LLM metadata extraction toggle
            enable_llm_extraction = st.checkbox("🤖 **LLM Metadata Extraction** - Extract structured data with AI", value=True, help="Use Gemma 3:27b to extract structured metadata from resume")
            if enable_llm_extraction:
                st.info("🧠 **AI-powered extraction enabled:** Will extract structured metadata using Ollama + Gemma 3:27b")
        
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
                
                llm_dev_mode = st.checkbox("🔍 **Show LLM extraction process**", help="Display detailed LLM extraction steps and responses")
        
        ## file upload in pdf format
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            with st.spinner('Hang On While We Cook Magic For You...'):
                time.sleep(4)
        
            ### saving the uploaded resume to folder
            save_image_path = './Uploaded_Resumes/'+pdf_file.name
            pdf_name = pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)

            ### parsing and extracting whole resume 
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                
                ## Get the whole resume data into resume_text using modular pdf_processor
                resume_text = pdf_processor.extract_text_hybrid(save_image_path, development_mode=dev_mode)

                # =============================================================================
                # LLM METADATA EXTRACTION
                # =============================================================================
                
                llm_metadata = None
                if enable_llm_extraction:
                    st.markdown("---")
                    st.header("**🤖 AI-Powered Metadata Extraction**")
                    
                    try:
                        # Initialize LLM extractor
                        llm_extractor = LLMMetadataExtractor(
                            model_name=llm_model,
                            base_url=ollama_url
                        )
                        
                        # Extract metadata using LLM
                        llm_metadata = llm_extractor.extract_metadata(
                            resume_text, 
                            development_mode=llm_dev_mode if 'llm_dev_mode' in locals() else False
                        )
                        
                        if llm_metadata:
                            st.success("✅ **Structured metadata extracted successfully using AI!**")
                            
                            # Download options for metadata
                            st.markdown("---")
                            st.subheader("📥 **Export Options**")
                            
                            col_json, col_formatted = st.columns(2)
                            
                            with col_json:
                                # JSON download
                                json_str = export_metadata_to_json(llm_metadata)
                                st.download_button(
                                    label="📄 Download Raw JSON",
                                    data=json_str,
                                    file_name=f"resume_metadata_{resume_data['name'].replace(' ', '_') if resume_data.get('name') else 'candidate'}.json",
                                    mime="application/json",
                                    help="Download complete metadata in JSON format"
                                )
                            
                            with col_formatted:
                                # Formatted text download
                                formatted_metadata = format_metadata_for_display(llm_metadata)
                                formatted_text = ""
                                for section_name, section_data in formatted_metadata.items():
                                    formatted_text += f"\n{'='*50}\n{section_name.upper()}\n{'='*50}\n"
                                    
                                    if isinstance(section_data, dict):
                                        for key, value in section_data.items():
                                            if isinstance(value, list):
                                                formatted_text += f"\n{key}:\n"
                                                for item in value:
                                                    formatted_text += f"  • {item}\n"
                                            else:
                                                formatted_text += f"{key}: {value}\n"
                                    elif isinstance(section_data, list):
                                        for item in section_data:
                                            for title, details in item.items():
                                                formatted_text += f"\n{title}:\n"
                                                for key, value in details.items():
                                                    if isinstance(value, list):
                                                        formatted_text += f"  {key}:\n"
                                                        for val in value:
                                                            formatted_text += f"    • {val}\n"
                                                    else:
                                                        formatted_text += f"  {key}: {value}\n"
                                
                                st.download_button(
                                    label="📋 Download Formatted Report",
                                    data=formatted_text,
                                    file_name=f"resume_report_{resume_data['name'].replace(' ', '_') if resume_data.get('name') else 'candidate'}.txt",
                                    mime="text/plain",
                                    help="Download formatted text report"
                                )
                        else:
                            st.info("ℹ️ No metadata sections to display")
                            
                    except Exception as e:
                        st.error(f"❌ LLM metadata extraction failed: {str(e)}")
                        st.info("""
                        **Troubleshooting LLM Issues:**
                        1. Make sure Ollama is running: `ollama serve`
                        2. Pull the model: `ollama pull gemma2:27b`
                        3. Check if the model name is correct
                        4. Verify Ollama is accessible at the specified URL
                        5. Check your internet connection
                        """)
                
                st.markdown("---")

                # =============================================================================
                # AI-POWERED CLEAN HR SUMMARY
                # =============================================================================
                
                # Get basic data for database storage (simplified)
                cand_level = llm_metadata.get('career_level', 'Unknown') if llm_metadata else 'Unknown'
                reco_field = llm_metadata.get('primary_field', 'General') if llm_metadata else 'General'
                resume_score = 85 if llm_metadata else 50  # AI analysis gets higher base score

                ### Getting Current Date and Time using modular utility
                timestamp = get_current_timestamp()

                ## Prepare data for database insertion using modular utility
                user_data = prepare_user_data(
                    resume_data=resume_data,
                    llm_metadata=llm_metadata,
                    pdf_name=pdf_name,
                    resume_score=resume_score
                )
                
                # Add system and location info
                user_data.update({
                    'sec_token': sec_token,
                    'ip_add': ip_add,
                    'host_name': host_name,
                    'dev_user': dev_user,
                    'os_name_ver': os_name_ver,
                    'latlong': str(latlong),
                    'city': city,
                    'state': state,
                    'country': country,
                    'timestamp': timestamp
                })
                
                ## Insert data using modular database manager
                db_manager.insert_user_data(user_data)

                ## Display Clean HR Summary
                if enable_llm_extraction and llm_metadata:
                    display_clean_hr_summary(llm_metadata, resume_data)
                else:
                    st.success("**✅ Basic candidate analysis completed!**")
                    st.info("**📊 Enable LLM extraction for AI-powered analysis.**")

                ## On Successful Result 
                st.balloons()

            else:
                st.error('Something went wrong..')                


    ###### CODE FOR FEEDBACK SIDE ######
    elif choice == 'Feedback':   
        
        # Get timestamp using modular utility
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
                # Prepare feedback data using modular utility
                feedback_data = prepare_feedback_data(feed_name, feed_email, feed_score, comments)
                feedback_data['timestamp'] = timestamp
                
                ## Insert feedback using modular database manager
                db_manager.insert_feedback(feedback_data)
                ## Success Message 
                st.success("Thanks! Your Feedback was recorded.") 
                ## On Successful Submit
                st.balloons()    

        # Get feedback data using modular database manager
        plotfeed_data = db_manager.get_feedback_data()                        


        # fetching feed_score from the query and getting the unique values and total value count 
        labels = plotfeed_data.feed_score.unique()
        values = plotfeed_data.feed_score.value_counts()


        # plotting pie chart for user ratings
        st.subheader("**Past User Rating's**")
        fig = px.pie(values=values, names=labels, title="Chart of User Rating Score From 1 - 5", color_discrete_sequence=px.colors.sequential.Aggrnyl)
        st.plotly_chart(fig)


        #  Fetching Comment History
        plfeed_cmt_data = db_manager.get_feedback_data()

        st.subheader("**HR User Comment's**")
        dff = pd.DataFrame(plfeed_cmt_data, columns=['HR User', 'Comment'])
        st.dataframe(dff, width=1000)

    
    ###### CODE FOR ABOUT PAGE ######
    elif choice == 'About':   

        st.subheader("**About The Tool - AI RESUME ANALYZER (HR Edition)**")

        st.markdown('''

        <p align='justify'>
            An AI-powered HR tool that analyzes candidate resumes using advanced natural language processing and hybrid PDF extraction technologies. The system evaluates candidates by extracting key information, analyzing skills, and providing comprehensive evaluation metrics for HR professionals.
        </p>

        <p align="justify">
            <b>How to use it: -</b> <br/><br/>
            <b>Candidate Evaluation -</b> <br/>
            Upload candidate resumes in PDF format for comprehensive analysis. The system will extract candidate information, analyze skills, determine experience level, and provide completeness scoring.<br/><br/>
            <b>Features:</b><br/>
            • Hybrid PDF extraction (PyMuPDF4LLM + EasyOCR + GPU acceleration)<br/>
            • Skills analysis and field classification<br/>
            • Experience level assessment<br/>
            • Resume completeness scoring<br/>
            • Development mode for extraction method comparison<br/><br/>
            <b>Admin -</b> <br/>
            For login use <b>admin</b> as username and <b>@dmin1234</b> as password.<br/>
            Access candidate data, analytics, and system management features.
        </p><br/><br/>

        <p align="justify">
            Enhanced AI-powered resume analysis system designed specifically for HR professionals and recruiting teams.
        </p>

        ''',unsafe_allow_html=True)  


    ###### CODE FOR ADMIN SIDE (ADMIN) ######
    else:
        st.success('Welcome to Admin Side')

        #  Admin Login
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')

        if st.button('Login'):
            
            ## Credentials using modular config
            if ad_user == ADMIN_CONFIG['username'] and ad_password == ADMIN_CONFIG['password']:
                
                ### Get analytics data using modular database manager
                plot_data = db_manager.get_analytics_data()
                
                ### Total Candidates Evaluated Count with Welcome Message
                user_count = db_manager.get_user_count()
                st.success("Welcome HR Admin! Total %d " % user_count + " Candidates Have Been Evaluated 📊")                
                
                ### Get user data using modular database manager
                df = db_manager.get_user_data()
                if df is not None:
                    # Rename columns for better display
                    df.columns = ['ID', 'Token', 'IP Address', 'HR User', 'HR Email', 'HR Contact', 'Candidate Field', 'Evaluation Date',
                                  'Candidate Name', 'Candidate Email', 'Resume Score', 'Pages',  'Resume File',   
                                  'Experience Level', 'Skills', 'Analysis Notes', 'Evaluation Summary',
                                  'City', 'State', 'Country', 'Location', 'System OS', 'System', 'System User']

                    st.header("**Candidate Evaluation Data**")
                    ### Viewing the dataframe
                    st.dataframe(df)
                    
                    ### Downloading Report of candidate data in csv file
                    st.markdown(get_csv_download_link(df,'Candidate_Evaluation_Report.csv','📊 Download Candidate Report'), unsafe_allow_html=True)

                ### Get feedback data using modular database manager
                feedback_df = db_manager.get_feedback_data()
                if feedback_df is not None:
                    st.header("**HR System Feedback Data**")
                    st.dataframe(feedback_df)
                    plotfeed_data = feedback_df
                else:
                    plotfeed_data = None                        

                ### Analyzing All the Data's in pie charts

                # fetching feed_score from the query and getting the unique values and total value count 
                labels = plotfeed_data.feed_score.unique()
                values = plotfeed_data.feed_score.value_counts()
                
                # Pie chart for HR system ratings
                st.subheader("**HR System Rating's**")
                fig = px.pie(values=values, names=labels, title="HR System Satisfaction Score From 1 - 5 🤗", color_discrete_sequence=px.colors.sequential.Aggrnyl)
                st.plotly_chart(fig)

                # fetching Predicted_Field from the query and getting the unique values and total value count                 
                labels = plot_data.Predicted_Field.unique()
                values = plot_data.Predicted_Field.value_counts()

                # Pie chart for candidate field distribution
                st.subheader("**Pie-Chart for Candidate Field Distribution**")
                fig = px.pie(df, values=values, names=labels, title='Candidate Field Classification Based on Skills 👽', color_discrete_sequence=px.colors.sequential.Aggrnyl_r)
                st.plotly_chart(fig)

                # fetching User_Level from the query and getting the unique values and total value count                 
                labels = plot_data.User_Level.unique()
                values = plot_data.User_Level.value_counts()

                # Pie chart for Candidate Experience Level Distribution
                st.subheader("**Pie-Chart for Candidate Experience Level Distribution**")
                fig = px.pie(df, values=values, names=labels, title="Candidate Pool 📈 Experience Level Distribution 👨‍💻", color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig)

                # fetching resume_score from the query and getting the unique values and total value count                 
                labels = plot_data.resume_score.unique()                
                values = plot_data.resume_score.value_counts()

                # Pie chart for Resume Completeness Score Distribution
                st.subheader("**Pie-Chart for Resume Completeness Score Distribution**")
                fig = px.pie(df, values=values, names=labels, title='Candidate Resume Quality Distribution (0-100) 💯', color_discrete_sequence=px.colors.sequential.Agsunset)
                st.plotly_chart(fig)

                # fetching IP_add from the query and getting the unique values and total value count 
                labels = plot_data.IP_add.unique()
                values = plot_data.IP_add.value_counts()

                # Pie chart for HR System Usage
                st.subheader("**Pie-Chart for HR System Usage**")
                fig = px.pie(df, values=values, names=labels, title='HR System Usage by Location/Session 👥', color_discrete_sequence=px.colors.sequential.matter_r)
                st.plotly_chart(fig)

                # fetching City from the query and getting the unique values and total value count 
                labels = plot_data.City.unique()
                values = plot_data.City.value_counts()

                # Pie chart for Candidate Geographic Distribution - City
                st.subheader("**Pie-Chart for Candidate Geographic Distribution - City**")
                fig = px.pie(df, values=values, names=labels, title='Candidate Pool Distribution by City 🌆', color_discrete_sequence=px.colors.sequential.Jet)
                st.plotly_chart(fig)

                # fetching State from the query and getting the unique values and total value count 
                labels = plot_data.State.unique()
                values = plot_data.State.value_counts()

                # Pie chart for Candidate Geographic Distribution - State
                st.subheader("**Pie-Chart for Candidate Geographic Distribution - State**")
                fig = px.pie(df, values=values, names=labels, title='Candidate Pool Distribution by State 🚉', color_discrete_sequence=px.colors.sequential.PuBu_r)
                st.plotly_chart(fig)

                # fetching Country from the query and getting the unique values and total value count 
                labels = plot_data.Country.unique()
                values = plot_data.Country.value_counts()

                # Pie chart for Candidate Geographic Distribution - Country
                st.subheader("**Pie-Chart for Candidate Geographic Distribution - Country**")
                fig = px.pie(df, values=values, names=labels, title='Candidate Pool Distribution by Country 🌏', color_discrete_sequence=px.colors.sequential.Purpor_r)
                st.plotly_chart(fig)

            ## For Wrong Credentials
            else:
                st.error("Wrong ID & Password Provided")

# Calling the main (run()) function to make the whole process run
run()
