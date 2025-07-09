import streamlit as st
from streamlit_tags import st_tags
import sys
import os
import pandas as pd
import re

# Add the App directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_service import llm_service
from config import PAGE_CONFIG, SPECIALISTS_CONFIG
from database import db_manager
from analyzers import JobDescriptionAnalyzer
from db_specialists import FilterMatchingSpecialist

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

# Job description analysis will be handled by the JD analyzer

def create_pdf_download_button(pdf_name, button_label="Download Resume", key_suffix="", help_text="Click to download the resume PDF"):
    """Create a download button for PDF files with error handling."""
    if not pdf_name:
        return False
    
    pdf_path = f"./Uploaded_Resumes/{pdf_name}"
    
    if os.path.exists(pdf_path):
        try:
            with open(pdf_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
            
            return st.download_button(
                label=button_label,
                data=pdf_bytes,
                file_name=pdf_name,
                mime="application/pdf",
                help=help_text,
                key=f"download_{key_suffix}_{hash(pdf_name)}" if key_suffix else f"download_{hash(pdf_name)}"
            )
        except Exception as e:
            st.caption(f"Resume file: {pdf_name} (Error loading file)")
            return False
    else:
        st.caption(f"Resume file: {pdf_name} (File not found)")
        return False

def parse_work_experience(work_exp_text):
    """Parse work experience text and organize it by individual jobs."""
    if not work_exp_text:
        return []
    
    # Split by "Job X:" pattern to separate individual jobs
    job_pattern = r'Job \d+:'
    jobs = re.split(job_pattern, work_exp_text)
    
    # Remove empty first element if it exists
    if jobs and not jobs[0].strip():
        jobs = jobs[1:]
    
    organized_jobs = []
    job_counter = 1
    
    for job in jobs:
        if job.strip():
            # Clean up the job text
            job_text = job.strip()
            
            # Extract and format job details
            # Pattern: Title at Company (Date). Responsibilities: Description
            job_info_match = re.match(r'^(.*?)\s+at\s+(.*?)\s+\((.*?)\)\.\s*Responsibilities:\s*(.*)', job_text)
            
            if job_info_match:
                title, company, dates, responsibilities = job_info_match.groups()
                
                # Clean up responsibilities (remove trailing semicolon and extra whitespace)
                clean_responsibilities = responsibilities.strip().rstrip(';').strip()
                
                formatted_job = f"""**Position {job_counter}: {title.strip()}**  
**Company:** {company.strip()}  
**Duration:** {dates.strip()}  
**Responsibilities:** {clean_responsibilities}"""
            else:
                # Fallback formatting if pattern doesn't match
                formatted_job = f"**Position {job_counter}:**\n{job_text}"
            
            organized_jobs.append(formatted_job)
            job_counter += 1
    
    return organized_jobs

def display_search_results(search_results, search_type):
    """Display search results with streamlined UX - click candidate to see everything"""
    
    if search_results:
        
        # Display candidates in a simplified, action-oriented way
        for i, result in enumerate(search_results, 1):
            metadata = result['metadata']
            # Ensure similarity score is properly converted to percentage
            similarity_score = result.get('similarity_score', 0)
            if similarity_score > 1:  # Already in percentage format
                similarity = round(similarity_score, 1)
            else:  # Convert from decimal to percentage
                similarity = round(similarity_score * 100, 1)
            
            # Color-coded match indicators
            if similarity >= 80:
                match_text = "Excellent"
                match_color = "#28a745"
            elif similarity >= 70:
                match_text = "Very Good"
                match_color = "#ffc107"
            elif similarity >= 60:
                match_text = "Good" 
                match_color = "#fd7e14"
            else:
                match_text = "Fair"
                match_color = "#dc3545"
            
            # Streamlined candidate card - everything visible when clicked
            with st.expander(f"**{metadata.get('name', 'Unknown')}**", expanded=False):
                
                # === CANDIDATE SUMMARY (Top Section) ===
                st.markdown('<div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">', unsafe_allow_html=True)
                
                summary_col1, summary_col2, summary_col3 = st.columns([3, 3, 2])
                
                with summary_col1:
                    st.markdown("**Contact Info**")
                    st.markdown(f"**Email:** {metadata.get('email', 'Not provided')}")
                
                with summary_col2:
                    st.markdown("**Professional Profile**")
                    st.markdown(f"**Field:** {metadata.get('reco_field', 'General')}")
                    st.markdown(f"**Level:** {metadata.get('cand_level', 'Unknown')}")
                    
                    location = f"{metadata.get('city', 'Unknown')}, {metadata.get('state', 'Unknown')}"
                    if location == "Unknown, Unknown":
                        location = "Location not specified"
                    st.markdown(f"**Location:** {location}")
                
                with summary_col3:
                    st.markdown("**Match Analysis**")
                    st.markdown(f'<div style="background-color: {match_color}20; padding: 10px; border-radius: 5px; text-align: center; border-left: 4px solid {match_color};"><strong>{similarity}%</strong><br><span style="color: {match_color};">{match_text} Match</span></div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # === EXPERIENCE & SKILLS ===
                exp_col1, exp_col2 = st.columns(2)
                
                with exp_col1:
                    st.markdown("**Experience Summary**")
                    if metadata.get('years_of_experience'):
                        st.markdown(f"• **Total Experience:** {metadata['years_of_experience']}")
                    
                    if metadata.get('field_specific_experience'):
                        st.markdown(f"• **Relevant Experience:** {metadata['field_specific_experience']}")
                    
                    # Show organized work experience preview if available
                    if metadata.get('work_experiences'):
                        jobs = parse_work_experience(metadata['work_experiences'])
                        if jobs:
                            # Extract title and company from first job for preview
                            first_job = jobs[0]
                            # Try to extract just the position title and company
                            title_match = re.search(r'\*\*Position \d+: (.*?)\*\*', first_job)
                            company_match = re.search(r'\*\*Company:\*\* (.*?)(?=\*\*Duration:|\n|$)', first_job)
                            
                            if title_match and company_match:
                                title = title_match.group(1).strip()
                                company = company_match.group(1).strip()
                                st.markdown(f"• **Latest Role:** {title} at {company}")
                            else:
                                # Fallback to first 100 characters
                                preview = first_job[:100] + "..." if len(first_job) > 100 else first_job
                                st.markdown(f"• **Latest Role:** {preview}")
                                
                            if len(jobs) > 1:
                                st.markdown(f"• **Total Positions:** {len(jobs)} roles")
                    
                    if metadata.get('pdf_name'):
                        st.markdown("• **Resume File:**")
                        create_pdf_download_button(
                            metadata['pdf_name'],
                            button_label=f"Download {metadata['pdf_name']}",
                            key_suffix=f"exp_{metadata.get('name', 'unknown')}",
                            help_text="Click to download the resume PDF"
                        )
                
                with exp_col2:
                    if metadata.get('skills'):
                        st.markdown("**Key Skills**")
                        skills_text = str(metadata['skills'])
                        # Clean up skills display
                        if skills_text.startswith('[') and skills_text.endswith(']'):
                            skills_text = skills_text.strip('[]').replace("'", "").replace('"', '')
                        
                        # Display skills as tags
                        skills_list = [s.strip() for s in skills_text.split(',')[:8]]  # Show top 8 skills
                        skills_html = " ".join([f'<span style="background-color: #e3f2fd; padding: 4px 8px; border-radius: 12px; font-size: 12px; margin: 2px; display: inline-block;">{skill}</span>' for skill in skills_list if skill])
                        st.markdown(skills_html, unsafe_allow_html=True)
                
                
                # === STRUCTURED METADATA DISPLAY ===
                st.markdown("---")
                
                # Work Experience Details (Organized by Job)
                if metadata.get('work_experiences'):
                    st.markdown("### Work Experience")
                    work_exp = metadata.get('work_experiences', '')
                    if work_exp and work_exp != 'Not specified':
                        # Parse and organize work experience by individual jobs
                        jobs = parse_work_experience(work_exp)
                        for job in jobs:
                            if job.strip():
                                st.markdown(job)
                
                # Education Details (Show raw metadata)
                if metadata.get('educations'):
                    st.markdown("### Education")
                    education = metadata.get('educations', '')
                    if education and education != 'Not specified':
                        # Display raw education data as stored in metadata
                        st.markdown(education)
                
                # Additional Metadata in organized columns
                meta_col1, meta_col2 = st.columns(2)
                
                with meta_col1:
                    st.markdown("### Career Analysis")
                    
                    # Career level and field analysis
                    if metadata.get('cand_level'):
                        st.markdown(f"**Level:** {metadata['cand_level']}")
                    
                    if metadata.get('primary_field'):
                        st.markdown(f"**Primary Field:** {metadata['primary_field']}")
                    
                    if metadata.get('career_transition_history'):
                        st.markdown(f"**Career Transitions:** {metadata['career_transition_history']}")
                
                with meta_col2:
                    st.markdown("### Match Metrics")
                    
                    # Similarity and relevance scores
                    st.markdown(f"**Similarity Score:** {similarity}% ({match_text})")
                    
                    if metadata.get('reco_field'):
                        st.markdown(f"**Field Match:** {metadata['reco_field']}")
                    
                    # File information (display only - download available in Resume File section)
                    if metadata.get('pdf_name'):
                        st.markdown(f"**Source File:** {metadata['pdf_name']}")
                    
                    if metadata.get('timestamp'):
                        st.markdown(f"**Processed:** {metadata['timestamp']}")
                
                # Contact Information Section
                contact_info = []
                
                # Add email (already shown in summary, but include for completeness)
                if metadata.get('email'):
                    contact_info.append(f"{metadata['email']}")
                
                # Parse contact_info field which contains: email|phone|linkedin|github
                if metadata.get('contact_info'):
                    contact_parts = metadata['contact_info'].split('|')
                    
                    # Extract phone number (usually second element)
                    if len(contact_parts) > 1 and contact_parts[1].strip():
                        phone = contact_parts[1].strip()
                        if phone and phone != metadata.get('email', ''):  # Make sure it's not duplicate email
                            contact_info.append(f"{phone}")
                    
                    # Extract LinkedIn (usually third element)
                    if len(contact_parts) > 2 and contact_parts[2].strip():
                        linkedin = contact_parts[2].strip()
                        if linkedin and linkedin not in ['', 'None', 'Not available']:
                            contact_info.append(f"LinkedIn: {linkedin}")
                    
                    # Extract GitHub (usually fourth element)
                    if len(contact_parts) > 3 and contact_parts[3].strip():
                        github = contact_parts[3].strip()
                        if github and github not in ['', 'None', 'Not available']:
                            contact_info.append(f"GitHub: {github}")
                
                if contact_info:
                    st.markdown("### Contact Information")
                    for contact in contact_info:
                        if contact.strip():
                            st.markdown(contact)
                
                # System Metadata (if available)
                sys_meta = []
                for key in ['os_name_ver', 'dev_user', 'ip_add', 'act_name']:
                    if metadata.get(key):
                        sys_meta.append(f"**{key.replace('_', ' ').title()}:** {metadata[key]}")
                
                if sys_meta and len(sys_meta) > 0:
                    with st.expander("System Metadata", expanded=False):
                        for meta in sys_meta:
                            st.markdown(meta)
        
        # Export functionality
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            # Create downloadable CSV
            export_data = []
            for result in search_results:
                metadata = result['metadata']
                # Ensure similarity score is properly formatted for export
                similarity_score = result.get('similarity_score', 0)
                if similarity_score > 1:  # Already in percentage format
                    similarity_percent = round(similarity_score, 1)
                else:  # Convert from decimal to percentage
                    similarity_percent = round(similarity_score * 100, 1)
                
                export_data.append({
                    'Name': metadata.get('name', 'Unknown'),
                    'Email': metadata.get('email', 'Not provided'),
                    'Field': metadata.get('reco_field', 'General'),
                    'Level': metadata.get('cand_level', 'Unknown'),
                    'Match Score (%)': similarity_percent,
                    'Location': f"{metadata.get('city', 'Unknown')}, {metadata.get('state', 'Unknown')}",
                    'Years Experience': metadata.get('years_of_experience', 'Not specified'),
                    'Skills': str(metadata.get('skills', '')).replace('[', '').replace(']', '').replace("'", ""),
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


def apply_candidate_filters(field_filter, level_filter, city_filter, state_filter, required_skills, num_results):
    """Apply filters to candidate database and return matching candidates using LLM-based semantic matching"""
    
    try:
        # Initialize filter matching specialist
        filter_specialist = FilterMatchingSpecialist(SPECIALISTS_CONFIG['filter_matching'])
        
        # Check if LLM specialist is available, fallback to simple matching if not
        use_llm_filtering = filter_specialist.is_available()
        
        # Get all user data
        user_data = db_manager.get_user_data()
        if user_data is None or user_data.empty:
            return []
        
        # Apply filters using proper column names
        filtered_data = user_data.copy()
        
        # Field filter - use LLM-based semantic matching with fallback
        if field_filter != 'All Fields':
            # Get unique field values from database
            available_fields = filtered_data['Predicted_Field'].dropna().unique().tolist()
            
            if available_fields:
                if use_llm_filtering:
                    try:
                        # Use LLM to find semantic matches
                        field_match_result = filter_specialist.execute(
                            filter_type="field/domain",
                            filter_criteria=field_filter,
                            available_values=available_fields
                        )
                        
                        matched_fields = field_match_result.get('matched_values', [])
                        
                        if matched_fields:
                            # Filter by matched fields
                            filtered_data = filtered_data[filtered_data['Predicted_Field'].isin(matched_fields)]
                        else:
                            # No semantic matches found, return empty results
                            filtered_data = filtered_data.iloc[0:0]  # Empty DataFrame with same structure
                    except Exception as e:
                        st.warning(f"LLM field filtering failed, using fallback: {str(e)}")
                        use_llm_filtering = False
                
                if not use_llm_filtering:
                    # Fallback: simple case-insensitive partial matching
                    field_matches = filtered_data[
                        filtered_data['Predicted_Field'].str.contains(field_filter, case=False, na=False)
                    ]
                    if field_matches.empty:
                        # Try reverse partial matching
                        field_matches = filtered_data[
                            filtered_data['Predicted_Field'].apply(
                                lambda x: str(x).lower() in field_filter.lower() if pd.notna(x) else False
                            )
                        ]
                    filtered_data = field_matches
        
        # Level filter - use LLM-based semantic matching with fallback 
        if level_filter != 'All Levels' and not filtered_data.empty:
            # Get unique level values from remaining data
            available_levels = filtered_data['User_level'].dropna().unique().tolist()
            
            if available_levels:
                if use_llm_filtering:
                    try:
                        # Use LLM to find semantic matches
                        level_match_result = filter_specialist.execute(
                            filter_type="experience level",
                            filter_criteria=level_filter,
                            available_values=available_levels
                        )
                        
                        matched_levels = level_match_result.get('matched_values', [])
                        
                        if matched_levels:
                            # Filter by matched levels
                            filtered_data = filtered_data[filtered_data['User_level'].isin(matched_levels)]
                        else:
                            # No semantic matches found, return empty results
                            filtered_data = filtered_data.iloc[0:0]
                    except Exception as e:
                        st.warning(f"LLM level filtering failed, using fallback: {str(e)}")
                        use_llm_filtering = False
                
                if not use_llm_filtering:
                    # Fallback: predefined level variations
                    level_variations = {
                        'Senior': ['Senior', 'Senior Level', 'Senior Developer', 'Senior Engineer', 'Lead', 'Principal'],
                        'Senior Level': ['Senior', 'Senior Level', 'Senior Developer', 'Senior Engineer', 'Lead', 'Principal'],
                        'Entry Level': ['Entry Level', 'Entry', 'Junior', 'Graduate', 'Intern', 'Trainee'],
                        'Mid Level': ['Mid Level', 'Mid', 'Intermediate', 'Associate', 'Regular'],
                        'Junior': ['Junior', 'Junior Level', 'Entry Level', 'Entry', 'Graduate'],
                        'Lead/Expert': ['Lead/Expert', 'Lead', 'Expert', 'Lead Level', 'Principal', 'Architect', 'Director']
                    }
                    
                    possible_levels = level_variations.get(level_filter, [level_filter])
                    level_match = filtered_data[
                        filtered_data['User_level'].str.lower().isin([level.lower() for level in possible_levels])
                    ]
                    filtered_data = level_match
        

        
        # Location filters - keep simple exact/case-insensitive matching (location names are usually straightforward)
        if city_filter != 'All Cities' and not filtered_data.empty:
            # Try exact match first, then case-insensitive
            city_exact = filtered_data[filtered_data['city'] == city_filter]
            if city_exact.empty:
                city_match = filtered_data[filtered_data['city'].str.lower() == city_filter.lower()]
                filtered_data = city_match
            else:
                filtered_data = city_exact

        if state_filter != 'All States' and not filtered_data.empty:
            # Try exact match first, then case-insensitive
            state_exact = filtered_data[filtered_data['state'] == state_filter]
            if state_exact.empty:
                state_match = filtered_data[filtered_data['state'].str.lower() == state_filter.lower()]
                filtered_data = state_match
            else:
                filtered_data = state_exact
        
        # Skills filter - use LLM-based semantic matching with fallback
        if required_skills and not filtered_data.empty:
            if use_llm_filtering:
                try:
                    # Get all unique skills from the remaining candidates
                    all_candidate_skills = []
                    for _, row in filtered_data.iterrows():
                        skills_text = str(row.get('Actual_skills', ''))
                        if skills_text and skills_text != 'nan':
                            # Parse skills from the text (they might be comma-separated or in other formats)
                            candidate_skills = [s.strip() for s in skills_text.replace('[', '').replace(']', '').replace("'", "").replace('"', '').split(',')]
                            all_candidate_skills.extend(candidate_skills)
                    
                    # Get unique skills
                    unique_skills = list(set([skill.strip() for skill in all_candidate_skills if skill.strip()]))
                    
                    if unique_skills:
                        # Track candidates that match each required skill
                        skill_matched_candidates = []
                        
                        for required_skill in required_skills:
                            # Use LLM to find semantic matches for this skill
                            skill_match_result = filter_specialist.execute(
                                filter_type="skill/technology",
                                filter_criteria=required_skill,
                                available_values=unique_skills
                            )
                            
                            matched_skills = skill_match_result.get('matched_values', [])
                            
                            if matched_skills:
                                # Find candidates who have any of these matched skills
                                skill_candidates = []
                                for _, row in filtered_data.iterrows():
                                    candidate_skills_text = str(row.get('Actual_skills', ''))
                                    if candidate_skills_text and candidate_skills_text != 'nan':
                                        # Check if any matched skill is in this candidate's skills
                                        for matched_skill in matched_skills:
                                            if matched_skill.lower() in candidate_skills_text.lower():
                                                skill_candidates.append(row.name)  # Add row index
                                                break
                                
                                skill_matched_candidates.append(set(skill_candidates))
                            else:
                                # No matches for this skill - set to empty to filter out all candidates
                                skill_matched_candidates.append(set())
                        
                        # Require ALL skills to match (AND condition) - find intersection of all skill matches
                        if skill_matched_candidates:
                            final_candidates = skill_matched_candidates[0]
                            for skill_set in skill_matched_candidates[1:]:
                                final_candidates = final_candidates.intersection(skill_set)
                            
                            # Filter to only these candidates
                            if final_candidates:
                                filtered_data = filtered_data.loc[list(final_candidates)]
                            else:
                                # No candidates match all required skills
                                filtered_data = filtered_data.iloc[0:0]
                        else:
                            # No skill matches at all
                            filtered_data = filtered_data.iloc[0:0]
                    else:
                        # No skills data available, can't filter
                        pass
                except Exception as e:
                    st.warning(f"LLM skills filtering failed, using fallback: {str(e)}")
                    use_llm_filtering = False
            
            if not use_llm_filtering:
                # Fallback: simple case-insensitive partial matching
                skills_conditions = []
                for skill in required_skills:
                    skills_conditions.append(
                        filtered_data['Actual_skills'].str.contains(skill, case=False, na=False)
                    )
                
                if skills_conditions:
                    # Require ALL skills to match (AND condition)
                    combined_condition = skills_conditions[0]
                    for condition in skills_conditions[1:]:
                        combined_condition = combined_condition & condition
                    filtered_data = filtered_data[combined_condition]
        
        # Limit results
        filtered_data = filtered_data.head(num_results)
        
        # Convert to list of dictionaries for display using proper column names
        results = []
        for _, row in filtered_data.iterrows():
            results.append({
                'name': row['Name'],
                'email': row['Email_ID'],  
                'field': row['Predicted_Field'],
                'level': row['User_level'],
                'skills': row['Actual_skills'],
                'city': row['city'],
                'state': row['state'],
                'file': row['pdf_name']
            })
        
        return results
        
    except Exception as e:
        st.error(f"Filter application failed: {e}")
        st.error(f"Available columns: {list(user_data.columns) if user_data is not None else 'None'}")
        
        # Show detailed error information
        import traceback
        st.error(f"Detailed error: {traceback.format_exc()}")
        return []

def convert_filter_results_to_search_format(filter_results):
    """Convert filter results to the same format used by semantic search results for consistent display"""
    
    if not filter_results:
        return []
    
    # Get full user data for additional metadata
    try:
        user_data = db_manager.get_user_data()
        if user_data is None or user_data.empty:
            return []
        
        search_format_results = []
        
        for candidate in filter_results:
            # Find the full record in user_data
            matching_record = user_data[user_data['Name'] == candidate['name']]
            
            if not matching_record.empty:
                row = matching_record.iloc[0]
                
                # Create metadata in the same format as semantic search results
                metadata = {
                    'name': row.get('Name', 'Unknown'),
                    'email': row.get('Email_ID', ''),
                    'reco_field': row.get('Predicted_Field', 'General'),
                    'cand_level': row.get('User_level', 'Unknown'),
                    'skills': row.get('Actual_skills', ''),
                    'city': row.get('city', ''),
                    'state': row.get('state', ''),
                    'pdf_name': row.get('pdf_name', ''),
                    'timestamp': row.get('Timestamp', ''),
                    'years_of_experience': row.get('years_of_experience', 'Not specified'),
                    'field_specific_experience': row.get('field_specific_experience', 'Not specified'),
                    'career_transition_history': row.get('career_transition_history', 'Not specified'),
                    'primary_field': row.get('primary_field', 'General'),
                    'work_experiences': row.get('work_experiences', 'Not specified'),
                    'educations': row.get('educations', 'Not specified'),
                    'contact_info': row.get('contact_info', ''),
                    'full_resume_data': row.get('full_resume_data', ''),
                    'extracted_text': row.get('extracted_text', ''),
                    'raw_resume_text': row.get('raw_resume_text', 'Not available'),
                    # System metadata
                    'sec_token': row.get('sec_token', ''),
                    'ip_add': row.get('ip_add', ''),
                    'host_name': row.get('host_name', ''),
                    'dev_user': row.get('dev_user', ''),
                    'os_name_ver': row.get('os_name_ver', ''),
                    'latlong': row.get('latlong', ''),
                    'country': row.get('country', ''),
                    'act_name': row.get('act_name', ''),
                    'act_mail': row.get('act_mail', ''),
                    'act_mob': row.get('act_mob', ''),
                    'no_of_pages': row.get('no_of_pages', '1'),
                    'record_type': row.get('record_type', 'resume_analysis')
                }
                
                # Create result in search format with 100% similarity (perfect filter match)
                result = {
                    'metadata': metadata,
                    'similarity_score': 100.0  # Perfect match for filter results
                }
                
                search_format_results.append(result)
        
        return search_format_results
        
    except Exception as e:
        st.error(f"Failed to convert filter results: {e}")
        return []

def handle_filter_method():
    """Handle filter-based candidate search"""
    
    st.markdown('''<h5 style='text-align: left; color: #021659;'>Filter Method</h5>''', unsafe_allow_html=True)
    st.markdown("**Search candidates based on specific criteria**")

    # Filter Options
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Field & Experience**")

        # Use standardized field categories (not dynamic from database to avoid overly specific values)
        field_options = ['All Fields', 
             # Technology & Engineering
             'Data Science & Analytics', 'Web Development', 'Backend Development', 
             'Mobile Development', 'DevOps & Cloud', 'Machine Learning', 'Software Engineering',
             'Cybersecurity', 'AI/Artificial Intelligence', 'Blockchain', 'Game Development',
             # Business & Management  
             'Business Analysis', 'Project Management', 'Product Management', 'Operations Management',
             'Human Resources', 'Finance & Accounting', 'Marketing & Advertising', 'Sales',
             'Customer Service', 'Business Development', 'Consulting',
             # Healthcare & Science
             'Healthcare & Medical', 'Nursing', 'Pharmacy', 'Medical Research', 'Biotechnology',
             'Chemistry', 'Biology', 'Environmental Science', 'Laboratory Science',
             # Creative & Media
             'Graphic Design', 'UI/UX Design', 'Content Writing', 'Digital Marketing', 
             'Photography', 'Video Production', 'Animation', 'Architecture', 'Interior Design',
             # Education & Training
             'Education & Teaching', 'Training & Development', 'Academic Research', 'Curriculum Development',
             # Legal & Government
             'Legal & Law', 'Government & Public Service', 'Policy Analysis', 'Compliance',
             # Other Fields
             'Manufacturing', 'Supply Chain & Logistics', 'Real Estate', 'Retail', 'Hospitality & Tourism',
             'Construction', 'Agriculture', 'Transportation', 'Energy & Utilities', 'Non-Profit',
             'General']

        field_filter = st.selectbox(
            "Field",
            field_options,
            key="filter_field"
        )

        # Use standardized level categories (not dynamic from database to avoid overly specific values)
        level_options = ['All Levels', 'Entry Level', 'Junior', 'Mid Level', 'Senior Level', 'Lead/Expert']

        level_filter = st.selectbox(
            "Experience Level",
            level_options,
            key="filter_level"
        )
        
    with col2:
        st.markdown("**Location**")

        # Get unique locations from database for filter options using proper column names
        try:
            user_data = db_manager.get_user_data()
            if user_data is not None and not user_data.empty:
                cities = ['All Cities'] + sorted([city for city in user_data['city'].dropna().unique() if city])
                states = ['All States'] + sorted([state for state in user_data['state'].dropna().unique() if state])
            else:
                cities = ['All Cities']
                states = ['All States']
        except Exception as e:
            st.warning(f"Could not load location data: {e}")
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
            suggestions=[
                # Programming & Technology
                'Python', 'JavaScript', 'Java', 'C#', 'C++', 'PHP', 'Ruby', 'Go', 'Rust', 'Swift', 'Kotlin',
                'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'Spring', 'ASP.NET', 'Laravel',
                'Machine Learning', 'Data Science', 'AI', 'Deep Learning', 'TensorFlow', 'PyTorch', 'SQL', 'NoSQL',
                'AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes', 'DevOps', 'CI/CD', 'Git', 'Linux',
                # Business & Finance
                'Project Management', 'Agile', 'Scrum', 'Business Analysis', 'Financial Analysis', 'Accounting',
                'Excel', 'PowerBI', 'Tableau', 'Salesforce', 'CRM', 'ERP', 'SAP', 'QuickBooks',
                # Design & Creative
                'Photoshop', 'Illustrator', 'Figma', 'Sketch', 'InDesign', 'UI/UX Design', 'Graphic Design',
                'Video Editing', 'After Effects', 'AutoCAD', 'Blender', '3D Modeling',
                # Marketing & Sales
                'Digital Marketing', 'SEO', 'SEM', 'Google Analytics', 'Facebook Ads', 'Content Marketing',
                'Social Media', 'Email Marketing', 'Lead Generation', 'CRM', 'HubSpot',
                # Healthcare & Science
                'Medical Terminology', 'Patient Care', 'Clinical Research', 'Laboratory Skills', 'Nursing',
                'Healthcare Management', 'Medical Coding', 'Pharmacy', 'Radiology', 'Surgery',
                # General Professional
                'Communication', 'Leadership', 'Team Management', 'Problem Solving', 'Critical Thinking',
                'Customer Service', 'Negotiation', 'Public Speaking', 'Writing', 'Research'
            ],
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
            # Convert filter results to search format for consistent rich display
            search_format_results = convert_filter_results_to_search_format(filtered_candidates)
            
            if search_format_results:
                st.markdown(f"### **Found {len(search_format_results)} candidates matching your filters**")
                st.markdown(f"*Showing candidates that match your selected criteria*")
                
                display_search_results(search_format_results, "Filter Match")
            else:
                st.warning("**No candidates found matching your filters.** Try broadening your criteria.")
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
        match_threshold = st.slider("Match Threshold %", 10, 90, 60, 5, key="jd_threshold")

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
    
    # Initialize session state for JD search results
    if "jd_search_results" not in st.session_state:
        st.session_state.jd_search_results = None
    if "jd_all_similarities" not in st.session_state:
        st.session_state.jd_all_similarities = []
    if "jd_match_threshold" not in st.session_state:
        st.session_state.jd_match_threshold = match_threshold

    # Search button - always visible
    if st.button("Find Matching Candidates", type="primary", key="jd_search_btn"):
        # Check if job description is provided and valid
        if not job_description or len(job_description.strip()) < 50:
            st.error("**Please provide a job description** (at least 50 characters) to search for matching candidates.")
        else:
            # Auto-analyze and search when job description is provided
            with st.spinner('Analyzing job description and finding matching candidates...'):
                # Background JD analysis (no UI display)
                jd_analyzer = JobDescriptionAnalyzer()
                jd_analysis = jd_analyzer.analyze_with_fallback(job_description, development_mode=False)
                
                # Perform semantic search
                search_results = db_manager.semantic_search_resumes(job_description, num_results)
                
                # Store JD analysis in session state for potential future use
                st.session_state.jd_analysis = jd_analysis

                # Store results in session state
                st.session_state.jd_search_results = search_results
                st.session_state.jd_match_threshold = match_threshold
                
                # Enhanced filtering logic with better threshold handling
                all_similarities = []
                for result in search_results:
                    similarity_score = result.get('similarity_score', 0)
                    similarity_percent = similarity_score * 100 if similarity_score <= 1 else similarity_score
                    all_similarities.append(similarity_percent)
                
                st.session_state.jd_all_similarities = all_similarities

    # Display results if available (from current search or session state)
    if st.session_state.jd_search_results is not None:
        search_results = st.session_state.jd_search_results
        all_similarities = st.session_state.jd_all_similarities
        stored_threshold = st.session_state.jd_match_threshold
        
        # Filter results based on current threshold (allow dynamic threshold changes)
        filtered_results = []
        for result in search_results:
            similarity_score = result.get('similarity_score', 0)
            similarity_percent = similarity_score * 100 if similarity_score <= 1 else similarity_score
            if similarity_percent >= match_threshold:
                filtered_results.append(result)
        
        # Show search results info
        if search_results:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Candidates", len(search_results))
            with col2:
                best_match = max(all_similarities) if all_similarities else 0
                st.metric("Best Match", f"{best_match:.1f}%")
            with col3:
                avg_match = sum(all_similarities) / len(all_similarities) if all_similarities else 0
                st.metric("Average Match", f"{avg_match:.1f}%")
        
        if filtered_results:
            st.markdown(f"### **Found {len(filtered_results)} candidates matching the job description**")
            st.markdown(f"*Showing candidates with {match_threshold}%+ similarity*")

            display_search_results(filtered_results, "Job Description Match")
        else:
            # Enhanced feedback when no results found
            if search_results:
                best_score = max(all_similarities) if all_similarities else 0
                
                st.warning(f"**No candidates found with {match_threshold}%+ match.**")
                
                if best_score > 0:
                    suggested_threshold = max(10, int(best_score * 0.8))  # 80% of best score, minimum 10%
                    st.info(f"**Best available match: {best_score:.1f}%** - Try lowering threshold to {suggested_threshold}% to see results.")
                    
                    # Show all results if threshold is very low
                    if match_threshold <= 20:
                        st.markdown("### **All Available Candidates (Low Similarity)**")
                        st.markdown("*These candidates may not be ideal matches, but are the closest available:*")
                        display_search_results(search_results, "All Available Candidates")
                else:
                    st.error("**No meaningful matches found.** The job description may be very different from available candidates.")
            else:
                st.error("**Search failed or no candidates in database.** Please check that resumes have been processed.")
        
        # Add a clear button to reset search results
        if st.button("Clear Search Results", key="clear_jd_results"):
            st.session_state.jd_search_results = None
            st.session_state.jd_all_similarities = []
            st.rerun()

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
    if "processing_message" not in st.session_state:
        st.session_state.processing_message = False

    # Create a single chat container for all interactions
    chat_container = st.container(height=400)
    
    # Display all chat messages in the container (only when not processing)
    if not st.session_state.processing_message:
        with chat_container:
            if st.session_state.chat_history:
                for message in st.session_state.chat_history:
                    # User message
                    with st.chat_message("user"):
                        st.write(message["user"])
                    
                    # Assistant message (only if response exists)
                    if message["assistant"] is not None:
                        with st.chat_message("assistant"):
                            # Check if message contains screenshot information
                            assistant_content = message["assistant"]
                            if "[SCREENSHOT_PATH:" in assistant_content:
                                # Extract screenshot path and text content
                                import re
                                screenshot_match = re.search(r'\[SCREENSHOT_PATH:([^\]]+)\]', assistant_content)
                                if screenshot_match:
                                    screenshot_path = screenshot_match.group(1).strip()
                                    # Remove screenshot tag from text
                                    text_content = re.sub(r'\[SCREENSHOT_PATH:[^\]]+\]', '', assistant_content).strip()
                                    
                                    # Display text content
                                    st.write(text_content)
                                    
                                    # Display screenshot if file exists
                                    import os
                                    if os.path.exists(screenshot_path):
                                        st.image(screenshot_path, 
                                                caption="Official SFC License Search Results", 
                                                width=400)
                                    else:
                                        st.warning(f"📸 **Screenshot not found:** {screenshot_path}")
                                else:
                                    st.write(assistant_content)
                            else:
                                st.write(assistant_content)
    
    # Fixed chat input at bottom
    st.markdown("---")
    user_input = st.chat_input("Type your message here... (e.g., 'Find me Python developers with 3+ years experience')")
    
    # Clear chat button
    if st.button("Clear Chat History", key="clear_chat", help="Clear chat history"):
        st.session_state.chat_history = []
        st.session_state.processing_message = False
        candidate_chatbot.clear_history()
        st.rerun()

    # Handle example query from buttons
    if 'example_query' in st.session_state:
        user_input = st.session_state.example_query
        del st.session_state.example_query
    
    # Handle processing of pending messages
    if st.session_state.processing_message and st.session_state.chat_history:
        # Get the last message that needs processing
        last_message = st.session_state.chat_history[-1]
        if last_message["assistant"] is None:
            # Show message in chat immediately
            with chat_container:
                # Show existing messages
                for message in st.session_state.chat_history[:-1]:  # All but the last one
                    with st.chat_message("user"):
                        st.write(message["user"])
                    if message["assistant"] is not None:
                        with st.chat_message("assistant"):
                            st.write(message["assistant"])
                
                # Show current user message
                with st.chat_message("user"):
                    st.write(last_message["user"])
                
                # Stream the assistant response
                with st.chat_message("assistant"):
                    try:
                        # Use streaming chat and display with write_stream
                        response_generator = candidate_chatbot.chat_stream(last_message["user"])
                        response = st.write_stream(response_generator)
                        
                        # Check if response contains screenshot information
                        if "[SCREENSHOT_PATH:" in response:
                            import re
                            screenshot_match = re.search(r'\[SCREENSHOT_PATH:([^\]]+)\]', response)
                            if screenshot_match:
                                screenshot_path = screenshot_match.group(1).strip()
                                
                                # Display screenshot if file exists
                                import os
                                if os.path.exists(screenshot_path):
                                    st.image(screenshot_path, 
                                            caption="Official SFC License Search Results", 
                                            width=400)
                                else:
                                    st.warning(f"📸 **Screenshot not found:** {screenshot_path}")
                        
                        # Store the complete response
                        st.session_state.chat_history[-1]["assistant"] = response
                        
                    except Exception as e:
                        error_response = "I encountered an error while processing your request. Please try again."
                        st.write(error_response)
                        st.session_state.chat_history[-1]["assistant"] = error_response
            
            st.session_state.processing_message = False
            st.rerun()

    # Process user input
    if user_input:
        # Add user message to history immediately
        st.session_state.chat_history.append({
            "user": user_input,
            "assistant": None  # Placeholder for assistant response
        })
        
        # Set processing flag
        st.session_state.processing_message = True
        
        # Rerun to show user message and start processing
        st.rerun()
        
# Create three tabs for different search methods
tab1, tab2, tab3 = st.tabs(["Filter Method", "Job Description Search", "Find by Chat"])

with tab1:
    handle_filter_method()

with tab2:
    handle_job_description_search()

with tab3:
    handle_chat_search()

