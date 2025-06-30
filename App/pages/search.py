import streamlit as st
from streamlit_tags import st_tags
import sys
import os
import pandas as pd

# Add the App directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_service import llm_service
from config import PAGE_CONFIG
from database import db_manager

st.set_page_config(**PAGE_CONFIG)


st.title("Find Candidates")

st.markdown('''<h4 style='text-align: left; color: #021659;'>Find Candidates</h4>''', unsafe_allow_html=True)
st.markdown("**AI-powered candidate discovery with multiple search approaches**")

# Check if there are any resumes in the database
user_count = db_manager.get_user_count()
if user_count == 0:
    st.warning("**No resume data available.** Please process some resumes first using the 'Candidate Evaluation' module.")
    st.stop()

st.success(f"**{user_count} resumes** available for search")

def analyze_job_description(job_description):
    """Analyze job description to extract key requirements using LLM"""
    
    if not llm_service.is_available():
        return None
    
    try:
        analysis_prompt = f"""
        Analyze this job description and extract key information:

        Job Description:
        {job_description}

        Please extract:
        1. Required technical skills (programming languages, frameworks, tools)
        2. Key requirements (experience level, education, certifications)
        3. Experience level (Entry/Junior/Mid/Senior/Lead)
        4. Field/Domain (Web Development, Data Science, Mobile, etc.)

        Format as JSON:
        {{
            "required_skills": ["skill1", "skill2", ...],
            "key_requirements": ["requirement1", "requirement2", ...],
            "experience_level": "level",
            "field": "field_name"
        }}
        """
        
        response = llm_service.extract_simple(analysis_prompt)
        
        # Try to parse JSON response
        import json
        try:
            return json.loads(response)
        except:
            # If JSON parsing fails, create a simple analysis
            return {
                "required_skills": ["Analysis not available"],
                "key_requirements": ["Please check job description"],
                "experience_level": "Not determined",
                "field": "General"
            }
    
    except Exception as e:
        st.error(f"Job description analysis failed: {str(e)}")
        return None

def display_search_results(search_results, search_type):
    """Display search results in a consistent format"""
    
    if search_results:
        st.markdown(f"### **Found {len(search_results)} relevant candidates**")
        
        # Display search results
        for i, result in enumerate(search_results, 1):
            metadata = result['metadata']
            similarity = round(result['similarity_score'] * 100, 1)
            
            # Color-code similarity scores
            if similarity >= 80:
                similarity_color = "High"
            elif similarity >= 60:
                similarity_color = "Medium"
            else:
                similarity_color = "Low"
            
            with st.expander(f"**{i}. {metadata.get('name', 'Unknown')}** - {similarity_color} ({similarity}% match)"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Email:** {metadata.get('email', 'Not provided')}")
                    st.write(f"**Field:** {metadata.get('reco_field', 'General')}")
                    st.write(f"**Level:** {metadata.get('cand_level', 'Unknown')}")
                
                with col2:
                    st.write(f"**Location:** {metadata.get('city', '')}, {metadata.get('state', '')}")
                    st.write(f"**File:** {metadata.get('pdf_name', 'Unknown')}")
                
                with col3:
                    st.metric("Similarity", f"{similarity}%")
                
                # Show extracted content snippet
                if result.get('document'):
                    st.markdown("**Resume Content:**")
                    st.info(result['document'][:300] + "..." if len(result['document']) > 300 else result['document'])
        
        # Export functionality
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            # Create downloadable CSV
            export_data = []
            for result in search_results:
                metadata = result['metadata']
                export_data.append({
                    'Name': metadata.get('name', 'Unknown'),
                    'Email': metadata.get('email', 'Not provided'),
                    'Field': metadata.get('reco_field', 'General'),
                    'Level': metadata.get('cand_level', 'Unknown'),
                    'Similarity %': round(result['similarity_score'] * 100, 1),
                    'Location': f"{metadata.get('city', '')}, {metadata.get('state', '')}",
                    'File': metadata.get('pdf_name', 'Unknown')
                })
            
            export_df = pd.DataFrame(export_data)
            csv = export_df.to_csv(index=False)
            
            st.download_button(
                label="Download Search Results CSV",
                data=csv,
                file_name=f"candidate_search_results_{search_type.replace(' ', '_').lower()}.csv",
                mime="text/csv"
            )
        
        with col2:
            pass
    else:
        st.warning("**No candidates found.** Try refining your search query or using different keywords.")


def display_filtered_candidates(candidates):
    """Display filtered candidates in a structured format"""
    
    # Create summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fields = [c['field'] for c in candidates if c.get('field')]
        if fields:
            st.metric("Top Field", max(set(fields), key=fields.count))
    
    with col2:
        scores = [int(c['score']) for c in candidates if c.get('score') and str(c['score']).isdigit()]
        if scores:
            st.metric("Avg Resume Score", f"{sum(scores)/len(scores):.1f}%")
    
    with col3:
        levels = [c['level'] for c in candidates if c.get('level')]
        if levels:
            st.metric("Top Level", max(set(levels), key=levels.count))
    
    # Display candidates
    for i, candidate in enumerate(candidates, 1):
        with st.expander(f"**{i}. {candidate.get('name', 'Unknown')}** - {candidate.get('field', 'General')}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Email:** {candidate.get('email', 'Not provided')}")
                st.write(f"**Level:** {candidate.get('level', 'Unknown')}")
                st.write(f"**Resume Score:** {candidate.get('score', '0')}%")
            
            with col2:
                st.write(f"**Location:** {candidate.get('city', '')}, {candidate.get('state', '')}")
                st.write(f"**File:** {candidate.get('file', 'Unknown')}")
            
            with col3:
                if candidate.get('skills'):
                    skills_list = str(candidate['skills']).split(',')[:5]  # Show top 5 skills
                    st.write(f"**Top Skills:** {', '.join(skills_list)}")
    
    # Export option
    st.markdown("---")
    export_data = pd.DataFrame(candidates)
    csv = export_data.to_csv(index=False)
    
    st.download_button(
        label="Download Filtered Results CSV",
        data=csv,
        file_name="filtered_candidates.csv",
        mime="text/csv"
    )

def apply_candidate_filters(field_filter, level_filter, score_range, city_filter, state_filter, required_skills, num_results):
    """Apply filters to candidate database and return matching candidates"""
    
    try:
        # Get all user data
        user_data = db_manager.get_user_data()
        if user_data is None or user_data.empty:
            return []
        
        # Apply filters
        filtered_data = user_data.copy()
        
        # Field filter
        if field_filter != 'All Fields':
            filtered_data = filtered_data[filtered_data.iloc[:, 6] == field_filter]  # Candidate Field column
        
        # Level filter  
        if level_filter != 'All Levels':
            filtered_data = filtered_data[filtered_data.iloc[:, 13] == level_filter]  # Experience Level column
        
        # Score filter
        score_col = pd.to_numeric(filtered_data.iloc[:, 10], errors='coerce')  # Resume Score column
        filtered_data = filtered_data[(score_col >= score_range[0]) & (score_col <= score_range[1])]
        
        # Location filters
        if city_filter != 'All Cities':
            filtered_data = filtered_data[filtered_data.iloc[:, -7] == city_filter]  # City column
        
        if state_filter != 'All States':
            filtered_data = filtered_data[filtered_data.iloc[:, -6] == state_filter]  # State column
        
        # Skills filter
        if required_skills:
            skills_mask = filtered_data.iloc[:, 14].str.contains('|'.join(required_skills), case=False, na=False)  # Skills column
            filtered_data = filtered_data[skills_mask]
        
        # Limit results
        filtered_data = filtered_data.head(num_results)
        
        # Convert to list of dictionaries for display
        results = []
        for _, row in filtered_data.iterrows():
            results.append({
                'name': row.iloc[8],  # Candidate Name
                'email': row.iloc[9],  # Candidate Email  
                'field': row.iloc[6],  # Candidate Field
                'level': row.iloc[13],  # Experience Level
                'score': row.iloc[10],  # Resume Score
                'skills': row.iloc[14],  # Skills
                'city': row.iloc[-7],  # City
                'state': row.iloc[-6],  # State
                'file': row.iloc[12]  # Resume File
            })
        
        return results
        
    except Exception as e:
        st.error(f"Filter application failed: {e}")
        return []

def handle_filter_method():
    """Handle filter-based candidate search"""
    
    st.markdown('''<h5 style='text-align: left; color: #021659;'>Filter Method</h5>''', unsafe_allow_html=True)
    st.markdown("**Search candidates based on specific criteria**")

    # Filter Options
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Field & Experience**")

        field_filter = st.selectbox(
            "Field",
            ['All Fields', 'Data Science & Analytics', 'Web Development', 'Backend Development', 
             'Mobile Development', 'DevOps & Cloud', 'Machine Learning', 'General'],
            key="filter_field"
        )

        level_filter = st.selectbox(
            "Experience Level",
            ['All Levels', 'Entry Level', 'Junior', 'Mid Level', 'Senior', 'Lead/Expert'],
            key="filter_level"
        )
        
    with col2:
        st.markdown("**Location**")

        # Get unique locations from database for filter options
        try:
            user_data = db_manager.get_user_data()
            if user_data is not None and not user_data.empty:
                cities = ['All Cities'] + sorted(user_data.iloc[:, -7].dropna().unique().tolist())  # City column
                states = ['All States'] + sorted(user_data.iloc[:, -6].dropna().unique().tolist())  # State column
            else:
                cities = ['All Cities']
                states = ['All States']
        except:
            cities = ['All Cities']
            states = ['All States']
        
        city_filter = st.selectbox("City", cities, key="filter_city")
        state_filter = st.selectbox("State", states, key="filter_state")
    
    with col3:
        st.markdown("**Skills**")

        required_skills = st_tags(
            label="Required Skills",
            text="Press enter to add skills",
            value=[],
            suggestions=['Python', 'JavaScript', 'React', 'Machine Learning', 'Data Science', 
                        'Java', 'SQL', 'AWS', 'Docker', 'Node.js', 'Angular', 'Vue.js',
                        'C#', 'ASP.NET', 'Ruby', 'Rails', 'PHP', 'WordPress', 'Shopify', 'Magento', 'E-commerce'],
            maxtags=10,
            key="filter_skills"
        )
        
        num_results = st.selectbox("Max Results", [10, 20, 50, 100], index=1, key="filter_results")
        
    # Apply Filters
    if st.button("Apply Filters", type="primary"):
        with st.spinner('Filtering candidates...'):
            filtered_candidates = apply_candidate_filters(
                field_filter, level_filter, 
                city_filter, state_filter, required_skills, num_results
            )
        
        if filtered_candidates:
            display_filtered_candidates(filtered_candidates)
        else:
            st.warning("**No candidates found matching your filters.** Try broadening your criteria.")

def handle_job_description_search():
    """Handle job description based semantic search"""
    
    st.markdown("### **Job Description Search**")
    st.markdown("Paste a complete job description to find the best matching candidates")

    # Job Description Input
    col1, col2 = st.columns([2, 1])

    with col1:
        job_description = st.text_area(
            "**Job Description:**",
            placeholder="""Example:
Senior Python Developer - Remote

We are looking for an experienced Python developer to join our team:

Requirements:
• 5+ years of Python development experience
• Strong experience with Django or Flask frameworks
• Machine learning and data analysis experience preferred
• AWS cloud deployment experience
• Experience with RESTful APIs and microservices
• Strong problem-solving and communication skills
• Bachelor's degree in Computer Science or related field

Responsibilities:
• Develop and maintain Python applications
• Collaborate with data science team on ML projects
• Deploy applications to AWS cloud infrastructure
• Code review and mentoring junior developers
""",
            height=300,
            key="job_description"
        )

    with col2:
        st.markdown("**Search Options:**")
        num_results = st.selectbox("Max Results", [5, 10, 15, 20], index=2, key="jd_results")
        match_threshold = st.slider("Match Threshold %", 30, 90, 60, 5, key="jd_threshold")

        st.markdown("**Quick Templates:**")
        templates = {
                "Mobile Dev": """Mobile Application Developer
• 3+ years mobile development experience
• iOS (Swift) and Android (Kotlin/Java)
• React Native or Flutter preferred
• App Store/Play Store publishing
• UI/UX collaboration experience""",
            
            "ML Engineer": """Machine Learning Engineer
• 4+ years ML/AI development experience
• Python, TensorFlow, PyTorch
• Data preprocessing and feature engineering
• Model deployment and MLOps experience
• Statistical analysis and research skills""",
            
            "Full Stack": """Full Stack Developer
• 5+ years full-stack development
• Frontend: React, Vue.js, or Angular
• Backend: Node.js, Python, or Java
• Database design and optimization
• RESTful API development"""
        }

        for template_name, template_content in templates.items():
            if st.button(template_name, key=f"template_{template_name}"):
                st.session_state.jd_template = template_content
    
    # Use template if selected
    if 'jd_template' in st.session_state:
        job_description = st.text_area(
            "**Job Description:** (Template Applied)",
            value=st.session_state.jd_template,
            height=200,
            key="jd_with_template"
        )
        del st.session_state.jd_template
    
    # JD Analysis and Search
    if job_description and len(job_description.strip()) > 50:
        with st.expander("**Job Description Analysis**"):
            with st.spinner('Analyzing job description...'):
                jd_analysis = analyze_job_description(job_description)
                
            if jd_analysis:
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Required Skills:**")
                    for skill in jd_analysis.get('required_skills', []):
                        st.write(f"• {skill}")
                
                with col2:
                    st.markdown("**Key Requirements:**")
                    for req in jd_analysis.get('key_requirements', []):
                        st.write(f"• {req}")
                
                if jd_analysis.get('experience_level'):
                    st.markdown(f"**Experience Level:** {jd_analysis['experience_level']}")
                
                if jd_analysis.get('field'):
                    st.markdown(f"**Field:** {jd_analysis['field']}")

    # Perform semantic search
    if st.button("Find Matching Candidates", type="primary", key="jd_search_btn"):
        with st.spinner('Finding candidates that match the job description...'):
            search_results = db_manager.semantic_search_resumes(job_description, num_results)

            # Filter by threshold
            filtered_results = [
                result for result in search_results 
                if result['similarity_score'] * 100 >= match_threshold
            ]
        if filtered_results:
            st.markdown(f"### **Found {len(filtered_results)} candidates matching the job description**")
            st.markdown(f"*Showing candidates with {match_threshold}%+ similarity*")

            display_search_results(filtered_results, "Job Description Match")
        else:
            st.warning(f"**No candidates found with {match_threshold}%+ match.** Try lowering the threshold or refining the JD.")

def handle_chat_search():
    """Handle conversational chat-based candidate search using RAG with clean UI"""
    
    from chatbot_service import candidate_chatbot
    
    st.markdown("### **Find by Chat**")
    st.markdown("Chat with our AI assistant to find candidates using natural language")


    # Check if chatbot is available
    if not candidate_chatbot.is_available():
        st.error("**Chatbot service is not available.** Please check your LLM configuration.")
        return
    
    # Initialize chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Create a scrollable container for chat messages
    st.markdown("""
    <style>
    .stContainer > div:first-child {
        height: 400px;
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #e1e4e8;
        border-radius: 8px;
        background-color: #fafafa;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Create the chat message container
    with st.container(height=400):
        
        # Display chat history
        if st.session_state.chat_history:
            for i, message in enumerate(st.session_state.chat_history):
                # User message
                with st.chat_message("user"):
                    st.write(message["user"])
                
                # Assistant message
                with st.chat_message("assistant"):
                    st.write(message["assistant"])
    
    # Fixed chat input at bottom
    st.markdown("---")
    user_input = st.chat_input("Type your message here... (e.g., 'Find me Python developers with 3+ years experience')")
    
    # Clear chat button
    if st.button("Clear Chat History", key="clear_chat", help="Clear chat history"):
        st.session_state.chat_history = []
        candidate_chatbot.clear_history()
        st.rerun()

    # Handle example query from buttons
    if 'example_query' in st.session_state:
        user_input = st.session_state.example_query
        del st.session_state.example_query
    
    # Process user input
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            "user": user_input,
            "assistant": "Processing..."
        })

        # Show processing status in the chat area
        with st.container(height=400):
            # Display existing chat history
            for i, message in enumerate(st.session_state.chat_history[:-1]):  # All except the last processing message
                with st.chat_message("user"):
                    st.write(message["user"])
                with st.chat_message("assistant"):
                    st.write(message["assistant"])

            # Show the current user message
            with st.chat_message("user"):
                st.write(st.session_state.chat_history[-1]["user"])

            # Show processing spinner in chat area
            with st.chat_message("assistant"):
                with st.spinner("Searching candidates..."):
                    response = candidate_chatbot.chat(user_input)

        # Update the last message with the actual response
        st.session_state.chat_history[-1]["assistant"] = response

        st.rerun()
        
# Create three tabs for different search methods
tab1, tab2, tab3 = st.tabs(["Filter Method", "Job Description Search", "Find by Chat"])

with tab1:
    handle_filter_method()

with tab2:
    handle_job_description_search()

with tab3:
    handle_chat_search()

