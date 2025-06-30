import streamlit as st
import sys
import os

# Add the App directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PAGE_CONFIG
from database import db_manager
from datetime import datetime

st.set_page_config(**PAGE_CONFIG)


st.title("Database Management")

st.header("Database Management")

tab1, tab2, tab3, tab4 = st.tabs(["View Records", "Create Records", "Update Records", "Delete Records"])

def handle_delete_records():
    """Handle deleting records with confirmation"""
    
    st.subheader("**Delete Records**")
    
    # Only resume record deletion
    st.markdown("### **Delete Resume Record**")
    
    # Get all resume IDs with preview
    resume_ids = db_manager.get_all_resume_ids()
    
    if not resume_ids:
        st.warning("No resume records found to delete.")
        return
    
    # Create a mapping of IDs to names for better UX
    id_name_mapping = {}
    for rid in resume_ids:
        record = db_manager.get_resume_by_id(rid)
        if record:
            name = record['metadata'].get('name', 'Unknown')
            email = record['metadata'].get('email', 'No email')
            id_name_mapping[rid] = f"{name} ({email}) - ID: {rid[:8]}..."
    
    selected_id = st.selectbox(
        "Select Resume Record to Delete",
        options=list(id_name_mapping.keys()),
        format_func=lambda x: id_name_mapping[x]
    )
    
    if selected_id:
        # Show record preview
        current_record = db_manager.get_resume_by_id(selected_id)
        if current_record:
            metadata = current_record['metadata']
            
            st.markdown("**Record Preview:**")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Name:** {metadata.get('name', 'Unknown')}")
                st.write(f"**Email:** {metadata.get('email', 'Unknown')}")
                st.write(f"**Field:** {metadata.get('reco_field', 'Unknown')}")
            with col2:
                st.write(f"**Level:** {metadata.get('cand_level', 'Unknown')}")
                st.write(f"**File:** {metadata.get('pdf_name', 'Unknown')}")
            
            # Confirmation
            col1, col2 = st.columns(2)
            with col1:
                confirm_delete = st.checkbox("I confirm I want to delete this record")
            
            with col2:
                if confirm_delete:
                    if db_manager.delete_resume_record(selected_id):
                        st.success("Resume record deleted successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to delete resume record.")

def handle_view_records():
    """Handle viewing and searching records with comprehensive metadata display"""

    st.subheader("View Database Records")
    
    # Get all resume IDs and records
    resume_ids = db_manager.get_all_resume_ids()
    
    if not resume_ids:
        st.warning("No resume records found in the database.")
        return
    
    # Display type selection
    view_type = st.radio(
        "Select View Type",
        ["Summary View", "Detailed Metadata View", "Vector Content View"],
        horizontal=True
    )
    
    # Search functionality
    search_term = st.text_input("Search records:", placeholder="Enter name, email, field, skills, or any metadata...")
    
    # Get all records with full metadata
    all_records = []
    for record_id in resume_ids:
        record = db_manager.get_resume_by_id(record_id)
        if record:
            # Flatten metadata for searching
            searchable_content = " ".join([
                str(record['metadata'].get(key, '')) for key in record['metadata'].keys()
            ]) + " " + str(record.get('document', ''))
            
            if not search_term or search_term.lower() in searchable_content.lower():
                all_records.append({
                    'id': record_id,
                    'metadata': record['metadata'],
                    'document': record.get('document', '')
                })
    
    if not all_records:
        st.warning("No records found matching your search criteria.")
        return
    
    st.info(f"Found **{len(all_records)}** records")
    
    if view_type == "Summary View":
        # Summary table view
        summary_data = []
        for record in all_records:
            metadata = record['metadata']
            summary_data.append({
                'ID': record['id'][:8] + '...',
                'Name': metadata.get('name', 'Unknown'),
                'Email': metadata.get('email', 'Unknown'),
                'Field': metadata.get('reco_field', 'Unknown'),
                'Level': metadata.get('cand_level', 'Unknown'),
                'Experience': metadata.get('years_of_experience', 'Unknown'),
                'Skills Count': len(eval(metadata.get('skills', '[]'))) if metadata.get('skills', '[]') != '[]' else 0,
                'City': metadata.get('city', 'Unknown'),
                'PDF File': metadata.get('pdf_name', 'Unknown'),
                'Timestamp': metadata.get('timestamp', 'Unknown')
            })
        
        if summary_data:
            import pandas as pd
            df_summary = pd.DataFrame(summary_data)
            st.dataframe(df_summary, use_container_width=True, height=400)
            
            # Export summary
            csv = df_summary.to_csv(index=False)
            st.download_button(
                label="📥 Download Summary as CSV",
                data=csv,
                file_name=f"resume_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    elif view_type == "Detailed Metadata View":
        # Detailed metadata view with organized sections
        for i, record in enumerate(all_records):
            metadata = record['metadata']
            
            with st.expander(f"**{metadata.get('name', 'Unknown')}** ({metadata.get('email', 'No email')}) - ID: {record['id'][:8]}...", expanded=i==0):
                
                # Organize metadata into logical sections
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("### 👤 **Personal Information**")
                    st.write(f"**Name:** {metadata.get('name', 'Not provided')}")
                    st.write(f"**Email:** {metadata.get('email', 'Not provided')}")
                    st.write(f"**Contact Info:** {metadata.get('contact_info', 'Not provided')}")
                    
                    st.markdown("### 🏢 **Professional Profile**")
                    st.write(f"**Field:** {metadata.get('reco_field', 'Not determined')}")
                    st.write(f"**Primary Field:** {metadata.get('primary_field', 'Not determined')}")
                    st.write(f"**Career Level:** {metadata.get('cand_level', 'Not determined')}")
                    st.write(f"**Years of Experience:** {metadata.get('years_of_experience', 'Not calculated')}")
                    st.write(f"**Field-Specific Experience:** {metadata.get('field_specific_experience', 'Not calculated')}")
                    st.write(f"**Career Transitions:** {metadata.get('career_transition_history', 'Not analyzed')}")
                
                with col2:
                    st.markdown("### 🌍 **Location & System Info**")
                    st.write(f"**City:** {metadata.get('city', 'Not provided')}")
                    st.write(f"**State:** {metadata.get('state', 'Not provided')}")
                    st.write(f"**Country:** {metadata.get('country', 'Not provided')}")
                    st.write(f"**Coordinates:** {metadata.get('latlong', 'Not provided')}")
                    st.write(f"**IP Address:** {metadata.get('ip_add', 'Not recorded')}")
                    st.write(f"**Host:** {metadata.get('host_name', 'Not recorded')}")
                    st.write(f"**OS:** {metadata.get('os_name_ver', 'Not recorded')}")
                    
                    st.markdown("### 📄 **Document Info**")
                    st.write(f"**PDF Name:** {metadata.get('pdf_name', 'Not provided')}")
                    st.write(f"**Pages:** {metadata.get('no_of_pages', 'Not counted')}")
                    st.write(f"**Timestamp:** {metadata.get('timestamp', 'Not recorded')}")
                    st.write(f"**Record Type:** {metadata.get('record_type', 'Not specified')}")
                
                with col3:
                    st.markdown("### 🔧 **Skills & Details**")
                    skills = metadata.get('skills', 'Not extracted')
                    if skills and skills != 'Not extracted' and skills != '[]':
                        try:
                            skills_list = eval(skills) if isinstance(skills, str) else skills
                            if isinstance(skills_list, list) and skills_list:
                                st.write(f"**Skills ({len(skills_list)}):** {', '.join(skills_list[:10])}")
                                if len(skills_list) > 10:
                                    st.write(f"... and {len(skills_list) - 10} more")
                            else:
                                st.write(f"**Skills:** {skills}")
                        except:
                            st.write(f"**Skills:** {skills}")
                    else:
                        st.write("**Skills:** Not extracted")
                    
                    st.markdown("### 📊 **Activity Info**")
                    st.write(f"**Activity:** {metadata.get('act_name', 'Not recorded')}")
                    st.write(f"**Activity Email:** {metadata.get('act_mail', 'Not recorded')}")
                    st.write(f"**Security Token:** {metadata.get('sec_token', 'Not generated')[:8]}...")
                
                # Additional detailed sections
                st.markdown("---")
                
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.markdown("### 💼 **Work Experience Summary**")
                    work_exp = metadata.get('work_experiences', 'Not extracted')
                    if work_exp and work_exp != 'Not extracted':
                        # Truncate if too long
                        if len(work_exp) > 500:
                            st.write(work_exp[:500] + "...")
                            with st.expander("View Full Work Experience"):
                                st.write(work_exp)
                        else:
                            st.write(work_exp)
                    else:
                        st.write("No work experience extracted")
                
                with detail_col2:
                    st.markdown("### 🎓 **Education Summary**")
                    education = metadata.get('educations', 'Not extracted')
                    if education and education != 'Not extracted':
                        st.write(education)
                    else:
                        st.write("No education information extracted")
                
                # Full resume data
                full_resume = metadata.get('full_resume_data', 'Not available')
                if full_resume and full_resume != 'Not available':
                    with st.expander("📋 View Full Resume Data Summary"):
                        st.write(full_resume)
    
    elif view_type == "Vector Content View":
        # Show the actual vector document content used for embeddings
        for i, record in enumerate(all_records):
            metadata = record['metadata']
            document = record['document']
            
            with st.expander(f"**Vector Content:** {metadata.get('name', 'Unknown')} - ID: {record['id'][:8]}...", expanded=i==0):
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("### 📊 **Record Metadata**")
                    st.json({
                        'Record ID': record['id'],
                        'Name': metadata.get('name'),
                        'Email': metadata.get('email'),
                        'Field': metadata.get('reco_field'),
                        'Level': metadata.get('cand_level'),
                        'Timestamp': metadata.get('timestamp')
                    })
                
                with col2:
                    st.markdown("### 🔍 **Vector Document Content**")
                    st.markdown("*This is the actual content used for semantic search embeddings:*")
                    
                    if document:
                        # Show structured document content
                        if len(document) > 1000:
                            st.text_area("Document Content", document, height=200)
                        else:
                            st.code(document, language="text")
                    else:
                        st.warning("No vector document content found")
                
                # Show extracted text if available
                extracted_text = metadata.get('extracted_text', '')
                if extracted_text:
                    with st.expander("🏷️ View Tagged Extracted Text"):
                        st.code(extracted_text, language="text")
    
    # Export options
    st.markdown("---")
    st.markdown("### 📥 **Export Options**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Export all metadata as JSON
        if st.button("📄 Export All Metadata (JSON)"):
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_records': len(all_records),
                'records': []
            }
            
            for record in all_records:
                export_data['records'].append({
                    'id': record['id'],
                    'metadata': record['metadata'],
                    'document_content': record['document']
                })
            
            import json
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
            st.download_button(
                label="Download Complete Metadata",
                data=json_str,
                file_name=f"complete_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        # Export vector content only
        if st.button("🔍 Export Vector Content"):
            vector_data = []
            for record in all_records:
                vector_data.append({
                    'id': record['id'][:8],
                    'name': record['metadata'].get('name'),
                    'email': record['metadata'].get('email'),
                    'vector_content': record['document']
                })
            
            import pandas as pd
            df_vector = pd.DataFrame(vector_data)
            csv_vector = df_vector.to_csv(index=False)
            st.download_button(
                label="Download Vector Content",
                data=csv_vector,
                file_name=f"vector_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col3:
        # Database stats
        if st.button("📊 Show Database Stats"):
            stats = db_manager.get_database_stats()
            st.json(stats)

def handle_create_records():
    """Handle creating new records"""

    st.subheader("Create New Resume Record")

    st.markdown("### **Create New Resume Record**")

    with st.form("create_resume_form"):
        st.markdown("**Basic Information**")
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Candidate Name*", placeholder="John Doe")
            email = st.text_input("Email*", placeholder="john.doe@email.com")
            city = st.text_input("City", placeholder="New York")
            state = st.text_input("State", placeholder="NY")

        with col2:
            reco_field = st.selectbox(
                "Field*",
                ["Data Science & Analytics", "Web Development", "Backend Development",
                 "Mobile Development", "DevOps & Cloud", "Machine Learning", "General"]
            )
            cand_level = st.selectbox(
                "Experience Level*",
                ["Entry Level", "Junior Level", "Mid Level", "Senior Level", "Expert Level", "Career Changer"]
            )
            pdf_name = st.text_input("Resume File Name", placeholder="resume.pdf")
        
        st.markdown("**Skills & Additional Info**")
        skills = st.text_area(
            "Skills (comma-separated)",
            placeholder="Python, JavaScript, React, Machine Learning, AWS",
            height=100
        )

        submitted = st.form_submit_button("Create Resume Record", type="primary")

        if submitted:
            if name and email and reco_field and cand_level:
                record_data = {
                    'name': name,
                    'email': email,
                    'city': city,
                    'state': state,
                    'country': 'Hong Kong',
                    'reco_field': reco_field,
                    'cand_level': cand_level,
                    'skills': skills,
                    'pdf_name': pdf_name or 'Manual Entry'
                }

                # Insert into database
                if db_manager.create_manual_resume_record(record_data):
                    st.success("Resume record created successfully!")
                    st.balloons()
                else:
                    st.error("Failed to create resume record.")
            else:
                st.error("Please fill in all required fields (marked with *)")

def handle_update_records():
    """Handle updating existing records"""

    st.subheader("Update Existing Records")

    # Record type selection
    record_type = st.selectbox(
        "Select Record Type to Update",
        ["Resume Record"],
        key="update_record_type"
    )

    if record_type == "Resume Record":
        st.markdown("### Update Resume Record")
        
        # Get all resume IDs
        resume_ids = db_manager.get_all_resume_ids()
        
        if not resume_ids:
            st.warning("No resume records found to update.")
            return
        
        # Record selection
        selected_id = st.selectbox("Select Resume ID to Update", resume_ids, key="update_resume_id")
        
        if selected_id:
            # Get current record data
            current_record = db_manager.get_resume_by_id(selected_id)

            if current_record:
                with st.form("update_resume_form"):
                    metadata = current_record['metadata']

                    col1, col2 = st.columns(2)

                    with col1:
                        name = st.text_input("Candidate Name*", placeholder="John Doe", value=metadata.get('name', ''))
                        email = st.text_input("Email*", placeholder="john.doe@email.com", value=metadata.get('email', ''))
                        city = st.text_input("City", placeholder="New York", value=metadata.get('city', ''))
                        state = st.text_input("State", placeholder="NY", value=metadata.get('state', ''))

                    with col2:
                        reco_field = st.selectbox(
                            "Field",
                            ["Data Science & Analytics", "Web Development", "Backend Development", 
                             "Mobile Development", "DevOps & Cloud", "Machine Learning", "General"],
                            index=0 if metadata.get('reco_field') not in ["Data Science & Analytics", "Web Development", "Backend Development", "Mobile Development", "DevOps & Cloud", "Machine Learning", "General"] 
                            else ["Data Science & Analytics", "Web Development", "Backend Development", "Mobile Development", "DevOps & Cloud", "Machine Learning", "General"].index(metadata.get('reco_field'))
                        )
                        cand_level = st.selectbox(
                            "Experience Level",
                            ["Entry Level", "Junior", "Mid Level", "Senior Level", "Lead/Expert"],
                            index=0 if metadata.get('cand_level') not in ["Entry Level", "Junior", "Mid Level", "Senior Level", "Lead/Expert"]
                            else ["Entry Level", "Junior", "Mid Level", "Senior Level", "Lead/Expert"].index(metadata.get('cand_level'))
                        )

                        pdf_name = st.text_input("Resume File Name", value=metadata.get('pdf_name', ''))
                    
                    skills = st.text_area(
                        "Skills", 
                        value=metadata.get('skills', ''),
                        height=100
                    )
                    
                    submitted = st.form_submit_button("Update Record", type="primary")
                    
                    if submitted:
                        updated_data = {
                            'name': name,
                            'email': email,
                            'city': city,
                            'state': state,
                            'reco_field': reco_field,
                            'cand_level': cand_level,
                            'skills': skills,
                            'pdf_name': pdf_name
                        }
                        
                        # Update database
                        if db_manager.update_resume_record(selected_id, updated_data):
                            st.success("Resume record updated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to update resume record.")


with tab1:
    handle_view_records()

with tab2:
    handle_create_records()

with tab3:
    handle_update_records()

with tab4:
    handle_delete_records()