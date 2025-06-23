"""
Utility functions for AI Resume Analyzer
Common helper functions used across the application
"""
import base64
import secrets
import socket
import platform
import getpass
import geocoder
from geopy.geocoders import Nominatim
import time
import datetime
import pandas as pd
import streamlit as st
from typing import Dict, Any, Optional


def generate_security_token() -> str:
    """Generate a secure token for user sessions"""
    return secrets.token_urlsafe(12)


def get_system_info() -> Dict[str, str]:
    """Get system information for logging"""
    try:
        host_name = socket.gethostname()
        ip_add = socket.gethostbyname(host_name)
        dev_user = getpass.getuser()
        os_name_ver = f"{platform.system()} {platform.release()}"
        
        return {
            'host_name': host_name,
            'ip_add': ip_add,
            'dev_user': dev_user,
            'os_name_ver': os_name_ver
        }
    except Exception as e:
        st.warning(f"Could not get system info: {e}")
        return {
            'host_name': 'unknown',
            'ip_add': 'unknown',
            'dev_user': 'unknown',
            'os_name_ver': 'unknown'
        }


def get_location_info() -> Dict[str, str]:
    """Get location information using geocoding"""
    try:
        g = geocoder.ip('me')
        latlong = g.latlng
        
        if latlong:
            geolocator = Nominatim(user_agent="ai-resume-analyzer")
            location = geolocator.reverse(latlong, language='en')
            
            if location and location.raw.get('address'):
                address = location.raw['address']
                return {
                    'latlong': str(latlong),
                    'city': address.get('city', ''),
                    'state': address.get('state', ''),
                    'country': address.get('country', '')
                }
        
        return {
            'latlong': '',
            'city': '',
            'state': '',
            'country': ''
        }
        
    except Exception as e:
        st.warning(f"Could not get location info: {e}")
        return {
            'latlong': '',
            'city': '',
            'state': '',
            'country': ''
        }


def get_current_timestamp() -> str:
    """Get current timestamp in standard format"""
    ts = time.time()
    cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    return f"{cur_date}_{cur_time}"


def get_csv_download_link(df: pd.DataFrame, filename: str, text: str) -> str:
    """Generate a download link for CSV data"""
    try:
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
        return href
    except Exception as e:
        st.error(f"Error generating CSV download link: {e}")
        return ""


def show_pdf(file_path: str) -> str:
    """Generate PDF display HTML for Streamlit"""
    try:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        pdf_display = f'''
        <iframe src="data:application/pdf;base64,{base64_pdf}" 
                width="700" height="1000" type="application/pdf">
        </iframe>
        '''
        return pdf_display
    except Exception as e:
        st.error(f"Error displaying PDF: {e}")
        return "<p>Error displaying PDF file</p>"


def prepare_user_data(resume_data: Dict[str, Any], llm_metadata: Optional[Dict[str, Any]], 
                     pdf_name: str, resume_score: int) -> Dict[str, Any]:
    """Prepare user data for database insertion"""
    
    # Get system and location info
    system_info = get_system_info()
    location_info = get_location_info()
    
    # Extract basic data
    cand_level = llm_metadata.get('career_level', 'Unknown') if llm_metadata else 'Unknown'
    reco_field = llm_metadata.get('primary_field', 'General') if llm_metadata else 'General'
    
    # Enhanced skills data
    enhanced_skills = str(resume_data.get('skills', []))
    if llm_metadata:
        try:
            llm_skills = llm_metadata.get('skills', {})
            all_llm_skills = []
            for skill_category, skills_list in llm_skills.items():
                if isinstance(skills_list, list):
                    all_llm_skills.extend(skills_list)
            
            if all_llm_skills:
                enhanced_skills = str(list(set(resume_data.get('skills', []) + all_llm_skills)))
        except Exception:
            pass
    
    # Enhanced recommendations
    enhanced_recommendations = str([])
    if llm_metadata:
        try:
            llm_analysis = {
                'extraction_method': 'AI_Analysis',
                'total_experience_years': llm_metadata.get('total_experience_years'),
                'career_level': llm_metadata.get('career_level'),
                'primary_field_llm': llm_metadata.get('primary_field'),
                'personal_info_completeness': len([v for v in llm_metadata.get('personal_information', {}).values() if v]),
                'work_experience_count': len(llm_metadata.get('work_experience', [])),
                'education_count': len(llm_metadata.get('education', [])),
                'certifications_count': len(llm_metadata.get('certifications', [])),
                'projects_count': len(llm_metadata.get('projects', []))
            }
            enhanced_recommendations = str(llm_analysis)
        except Exception:
            pass
    
    # Course data
    enhanced_course_data = str('')
    if llm_metadata:
        llm_primary_field = llm_metadata.get('primary_field', '')
        if llm_primary_field:
            enhanced_course_data = f"AI_Recommended_Field: {llm_primary_field}"
    
    return {
        'sec_token': generate_security_token(),
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
        'name': resume_data.get('name', 'Unknown'),
        'email': resume_data.get('email', 'unknown@email.com'),
        'resume_score': str(resume_score),
        'timestamp': get_current_timestamp(),
        'no_of_pages': str(resume_data.get('no_of_pages', 1)),
        'reco_field': reco_field,
        'cand_level': cand_level,
        'skills': enhanced_skills,
        'recommended_skills': enhanced_recommendations,
        'courses': enhanced_course_data,
        'pdf_name': pdf_name
    }


def prepare_feedback_data(feed_name: str, feed_email: str, feed_score: int, 
                         comments: str) -> Dict[str, Any]:
    """Prepare feedback data for database insertion"""
    return {
        'feed_name': feed_name,
        'feed_email': feed_email,
        'feed_score': str(feed_score),
        'comments': comments,
        'timestamp': get_current_timestamp()
    }


def validate_file_upload(uploaded_file) -> bool:
    """Validate uploaded file"""
    if uploaded_file is None:
        return False
    
    # Check file extension
    if not uploaded_file.name.lower().endswith('.pdf'):
        st.error("❌ Please upload a PDF file only")
        return False
    
    # Check file size (10MB limit)
    if uploaded_file.size > 10 * 1024 * 1024:
        st.error("❌ File size too large. Please upload files smaller than 10MB")
        return False
    
    return True


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters that might cause issues
    import re
    text = re.sub(r'[^\w\s@.-]', ' ', text)
    
    return text.strip()


def safe_get_nested_value(data: Dict[str, Any], keys: list, default=None):
    """Safely get nested dictionary values"""
    try:
        for key in keys:
            data = data[key]
        return data
    except (KeyError, TypeError):
        return default


def calculate_completeness_score(resume_data: Dict[str, Any], 
                               llm_metadata: Optional[Dict[str, Any]] = None) -> int:
    """Calculate resume completeness score"""
    score = 0
    
    # Basic information (30 points)
    if resume_data.get('name'):
        score += 10
    if resume_data.get('email'):
        score += 10
    if resume_data.get('mobile_number'):
        score += 10
    
    # Skills (20 points)
    skills = resume_data.get('skills', [])
    if isinstance(skills, list) and len(skills) > 0:
        score += 20
    
    # LLM-enhanced scoring
    if llm_metadata:
        # Work experience (25 points)
        work_exp = llm_metadata.get('work_experience', [])
        if work_exp:
            score += 25
        
        # Education (15 points)
        education = llm_metadata.get('education', [])
        if education:
            score += 15
        
        # Projects/Certifications (10 points)
        projects = llm_metadata.get('projects', [])
        certs = llm_metadata.get('certifications', [])
        if projects or certs:
            score += 10
    else:
        # Basic scoring without LLM
        score += 35  # Give some points for basic extraction
    
    return min(score, 100)  # Cap at 100 