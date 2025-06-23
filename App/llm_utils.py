"""
Utility functions for LLM operations and metadata handling
"""
import json
from typing import Dict, Any
from datetime import datetime
import requests
import streamlit as st


def get_available_ollama_models(base_url: str) -> list:
    """Get list of available models from Ollama server"""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            available_models = []
            for model in models_data.get('models', []):
                model_name = model.get('name', '')
                if model_name:
                    # Remove :latest suffix if present for cleaner display
                    if model_name.endswith(':latest'):
                        model_name = model_name[:-7]
                    available_models.append(model_name)
            return sorted(available_models) if available_models else []
    except Exception as e:
        st.warning(f"Could not fetch Ollama models: {e}")
        return []


def format_metadata_for_display(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Format metadata for better display in Streamlit"""
    if not metadata:
        return {}
    
    formatted = {}
    
    # Personal Information
    personal = metadata.get('personal_information', {})
    if personal:
        formatted['Personal Information'] = {
            k.replace('_', ' ').title(): v 
            for k, v in personal.items() 
            if v is not None and v != ""
        }
    
    # Work Experience
    work_exp = metadata.get('work_experience', [])
    if work_exp:
        formatted['Work Experience'] = []
        for i, job in enumerate(work_exp, 1):
            job_formatted = {
                f"Position {i}": {
                    k.replace('_', ' ').title(): v 
                    for k, v in job.items() 
                    if v is not None and v != "" and v != []
                }
            }
            formatted['Work Experience'].append(job_formatted)
    
    # Education
    education = metadata.get('education', [])
    if education:
        formatted['Education'] = []
        for i, edu in enumerate(education, 1):
            edu_formatted = {
                f"Education {i}": {
                    k.replace('_', ' ').title(): v 
                    for k, v in edu.items() 
                    if v is not None and v != "" and v != []
                }
            }
            formatted['Education'].append(edu_formatted)
    
    # Skills
    skills = metadata.get('skills', {})
    if skills:
        formatted['Skills'] = {
            k.replace('_', ' ').title(): v 
            for k, v in skills.items() 
            if v and len(v) > 0
        }
    
    # Certifications
    certs = metadata.get('certifications', [])
    if certs:
        formatted['Certifications'] = []
        for i, cert in enumerate(certs, 1):
            cert_formatted = {
                f"Certification {i}": {
                    k.replace('_', ' ').title(): v 
                    for k, v in cert.items() 
                    if v is not None and v != ""
                }
            }
            formatted['Certifications'].append(cert_formatted)
    
    # Projects
    projects = metadata.get('projects', [])
    if projects:
        formatted['Projects'] = []
        for i, project in enumerate(projects, 1):
            project_formatted = {
                f"Project {i}": {
                    k.replace('_', ' ').title(): v 
                    for k, v in project.items() 
                    if v is not None and v != "" and v != []
                }
            }
            formatted['Projects'].append(project_formatted)
    
    # Additional Information
    additional = metadata.get('additional_information', {})
    if additional:
        formatted['Additional Information'] = {
            k.replace('_', ' ').title(): v 
            for k, v in additional.items() 
            if v and len(v) > 0
        }
    
    # Analysis Summary
    analysis = {
        'Extraction Timestamp': metadata.get('extraction_timestamp'),
        'Total Experience Years': metadata.get('total_experience_years'),
        'Career Level': metadata.get('career_level'),
        'Primary Field': metadata.get('primary_field')
    }
    
    formatted['Analysis Summary'] = {
        k: v for k, v in analysis.items() 
        if v is not None
    }
    
    return formatted


def export_metadata_to_json(metadata: Dict[str, Any], filename: str = None) -> str:
    """Export metadata to JSON string"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resume_metadata_{timestamp}.json"
    
    try:
        json_str = json.dumps(metadata, indent=2, ensure_ascii=False)
        return json_str
    except Exception as e:
        return f"Error exporting to JSON: {str(e)}"


def display_clean_hr_summary(llm_metadata: Dict[str, Any], resume_data: Dict[str, Any]):
    """Display a clean, focused HR summary with only critical information"""
    if not llm_metadata:
        st.warning("No AI analysis available")
        return
    
    st.markdown("## 🎯 **AI Candidate Summary**")
    
    # Critical HR Metrics - Clean and Simple
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        exp_years = llm_metadata.get('total_experience_years', 0) or 0
        st.metric("Experience", f"{exp_years} years")
    
    with col2:
        career_level = llm_metadata.get('career_level', 'Unknown')
        st.metric("Level", career_level)
    
    with col3:
        primary_field = llm_metadata.get('primary_field', 'Unknown')
        st.metric("Field", primary_field)
    
    with col4:
        work_count = len(llm_metadata.get('work_experience', []))
        st.metric("Positions", f"{work_count}")
    
    st.markdown("---")
    
    # Personal Info - Essential Only
    personal = llm_metadata.get('personal_information', {})
    if personal:
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            if personal.get('full_name'):
                st.markdown(f"**👤 Name:** {personal['full_name']}")
            if personal.get('email'):
                st.markdown(f"**📧 Email:** {personal['email']}")
            if personal.get('phone'):
                st.markdown(f"**📱 Phone:** {personal['phone']}")
        
        with col_info2:
            if personal.get('linkedin'):
                linkedin_url = personal['linkedin']
                if not linkedin_url.startswith('http'):
                    linkedin_url = f"https://{linkedin_url}"
                st.markdown(f"**🔗 LinkedIn:** <a href='{linkedin_url}' target='_blank'>View Profile</a>", unsafe_allow_html=True)
            if personal.get('github'):
                github_url = personal['github']
                if not github_url.startswith('http'):
                    github_url = f"https://{github_url}"
                st.markdown(f"**💻 GitHub:** <a href='{github_url}' target='_blank'>View Profile</a>", unsafe_allow_html=True)
            location = f"{personal.get('city', '')}, {personal.get('country', '')}" if personal.get('city') or personal.get('country') else None
            if location and location != ", ":
                st.markdown(f"**📍 Location:** {location}")
    
    # Top Skills - Key Technologies Only
    skills = llm_metadata.get('skills', {})
    if skills:
        st.markdown("### 🛠️ **Key Skills**")
        
        # Get programming languages and frameworks (most relevant for HR)
        key_categories = ['programming_languages', 'frameworks_libraries', 'tools_platforms']
        
        for category in key_categories:
            if category in skills and skills[category]:
                category_display = category.replace('_', ' ').title()
                skills_text = ", ".join(skills[category][:5])  # Show only top 5
                if len(skills[category]) > 5:
                    skills_text += f" (+{len(skills[category]) - 5} more)"
                st.markdown(f"**{category_display}:** {skills_text}")
    
    # Recent Work Experience - Top 2 Only
    work_exp = llm_metadata.get('work_experience', [])
    if work_exp:
        st.markdown("### 💼 **Recent Experience**")
        
        for i, job in enumerate(work_exp[:2]):  # Show only top 2 recent positions
            with st.expander(f"📍 {job.get('job_title', 'Position')} at {job.get('company', 'Company')}", expanded=(i == 0)):
                col_job1, col_job2 = st.columns([2, 1])
                
                with col_job1:
                    if job.get('duration'):
                        st.markdown(f"**Duration:** {job['duration']}")
                    if job.get('responsibilities'):
                        st.markdown(f"**Key Responsibility:** {job['responsibilities'][0]}")  # Show only first responsibility
                
                with col_job2:
                    if job.get('technologies'):
                        tech_list = ", ".join(job['technologies'][:3])  # Show only top 3 technologies
                        st.markdown(f"**Tech Stack:** {tech_list}")
    
    # Education - Summary Only
    education = llm_metadata.get('education', [])
    if education:
        st.markdown("### 🎓 **Education**")
        for i, edu in enumerate(education[:2]):  # Show only top 2 education entries
            degree_info = f"{edu.get('degree', 'Degree')} in {edu.get('field_of_study', 'Field')}"
            if edu.get('institution'):
                degree_info += f" from {edu['institution']}"
            if edu.get('graduation_date'):
                degree_info += f" ({edu['graduation_date']})"
            st.markdown(f"• {degree_info}")
    
    # Certifications - Count Only
    certifications = llm_metadata.get('certifications', [])
    projects = llm_metadata.get('projects', [])
    
    if certifications or projects:
        col_cert, col_proj = st.columns(2)
        
        with col_cert:
            if certifications:
                st.markdown(f"### 🏆 **Certifications ({len(certifications)})**")
                for cert in certifications[:3]:  # Show only top 3
                    st.markdown(f"• {cert.get('name', 'Certification')}")
        
        with col_proj:
            if projects:
                st.markdown(f"### 🚀 **Projects ({len(projects)})**")
                for proj in projects[:3]:  # Show only top 3
                    st.markdown(f"• {proj.get('name', 'Project')}")
    
    # Final Quick Assessment
    st.markdown("---")
    st.markdown("### ⚡ **Quick Assessment**")
    
    assessment_col1, assessment_col2 = st.columns(2)
    
    with assessment_col1:
        # Experience assessment
        exp_years = llm_metadata.get('total_experience_years', 0) or 0
        if exp_years >= 5:
            st.success(f"✅ **Experienced** - {exp_years} years in field")
        elif exp_years >= 2:
            st.info(f"🔵 **Mid-level** - {exp_years} years experience")
        else:
            st.warning(f"🟡 **Junior** - {exp_years} years experience")
    
    with assessment_col2:
        # Profile completeness
        personal_completeness = len([v for v in personal.values() if v]) if personal else 0
        total_sections = len([x for x in [work_exp, education, skills, certifications] if x])
        
        if total_sections >= 3 and personal_completeness >= 3:
            st.success("✅ **Complete Profile**")
        elif total_sections >= 2:
            st.info("🔵 **Good Profile**")
        else:
            st.warning("🟡 **Basic Profile**")
    
    st.success("🎯 **AI Analysis Complete** - Ready for HR review")


def validate_ollama_connection(base_url: str, model_name: str) -> bool:
    """Validate Ollama connection and model availability"""
    try:
        # Check if Ollama is running
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code != 200:
            return False
        
        # Check if the specific model is available
        models_data = response.json()
        available_models = [model.get('name', '') for model in models_data.get('models', [])]
        
        # Check both with and without :latest suffix
        model_variants = [model_name, f"{model_name}:latest"]
        return any(variant in available_models for variant in model_variants)
        
    except Exception:
        return False


def create_model_selection_ui(base_url: str) -> str:
    """Create Streamlit UI for model selection"""
    available_models = get_available_ollama_models(base_url)
    
    if available_models:
        st.success(f"✅ Found {len(available_models)} available models")
        
        # Recommended models for resume analysis
        recommended_models = ["gemma2:27b", "gemma2:9b", "llama3.1:8b", "mistral:7b", "qwen2.5:14b"]
        recommended_available = [model for model in recommended_models if model in available_models]
        
        if recommended_available:
            st.info(f"🎯 Recommended models: {', '.join(recommended_available)}")
        
        selected_model = st.selectbox(
            "Model Selection",
            available_models,
            index=0,
            help=f"Select from {len(available_models)} available Ollama models"
        )
        
        # Show model info
        if selected_model in recommended_available:
            st.success(f"🌟 '{selected_model}' is optimized for resume analysis")
        else:
            st.warning(f"⚠️ '{selected_model}' may work but isn't specifically tested for resume analysis")
        
        return selected_model
        
    else:
        # Fallback to static list if Ollama is not available
        st.error("❌ Could not connect to Ollama server")
        st.info("💡 Make sure Ollama is running: `ollama serve`")
        
        selected_model = st.selectbox(
            "Model Selection (Fallback)",
            ["gemma2:27b", "gemma2:9b", "llama3.1:8b", "mistral:7b", "qwen2.5:14b"],
            index=0,
            help="Fallback list - install models with 'ollama pull <model_name>'"
        )
        
        st.markdown("""
        **To install recommended models:**
        ```bash
        ollama pull gemma2:27b    # Best for detailed analysis
        ollama pull gemma2:9b     # Good balance of speed/quality
        ollama pull llama3.1:8b   # Fast and reliable
        ```
        """)
        
        return selected_model 