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
                    if st.button("DELETE RECORD", type="secondary", use_container_width=True):
                        if db_manager.delete_resume_record(selected_id):
                            st.success("Resume record deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to delete resume record.")

def handle_view_records():
    """Handle viewing and searching records"""

    st.subheader("View Database Records")

    # Get resume data
    df = db_manager.get_user_data()

    if df is not None and not df.empty:
        # Search functionality
        search_term = st.text_input("Search records:", placeholder="Enter name, email, field, or skills...")

        # Filter records based on search
        if search_term:
            mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
            df_filtered = df[mask]
        else:
            df_filtered = df

        # Display records with better formatting
        if not df_filtered.empty:
            # Select columns to display
            display_columns = ['Name', 'Email_ID', 'Predicted_Field', 'User_level', 'Timestamp', 'pdf_name']
            available_columns = [col for col in display_columns if col in df_filtered.columns]

            st.dataframe(
                df_filtered[available_columns],
                use_container_width=True,
                height=400
            )

            # Export option
            csv = df_filtered.to_csv(index=False)
            st.download_button(
                label="Download Filtered Data as CSV",
                data=csv,
                file_name=f"resume_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No resume records found in the database.")
    else:
        st.warning("No resume records found in the database.")

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
                ["Entry Level", "Junior", "Mid Level", "Senior Level", "Lead/Expert"]
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
                        # Define the full field list
                        field_options = [
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
                            'General'
                        ]
                        
                        reco_field = st.selectbox(
                            "Field",
                            field_options,
                            index=0 if metadata.get('reco_field') not in field_options
                            else field_options.index(metadata.get('reco_field'))
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