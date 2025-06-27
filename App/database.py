"""
Vector Database operations for AI Resume Analyzer using ChromaDB
"""
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import pandas as pd
import streamlit as st
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import CHROMA_CONFIG


class VectorDatabaseManager:
    """ChromaDB-based vector database manager for LLM-enhanced resume analytics"""
    
    def __init__(self):
        self.client = None
        self.resume_collection = None
        self.feedback_collection = None
        self.embedding_function = None
        self._initialize_client()
        self._initialize_collections()
    
    def _initialize_client(self):
        """Initialize ChromaDB client with persistent storage"""
        try:
            # Initialize embedding function
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=CHROMA_CONFIG['embedding_model']
            )
            
            # Initialize ChromaDB client with persistent storage
            self.client = chromadb.PersistentClient(
                path=CHROMA_CONFIG['persist_directory'],
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
        except Exception as e:
            st.error(f"ChromaDB connection failed: {e}")
            raise
    
    def _initialize_collections(self):
        """Initialize or get existing collections"""
        try:
            # Resume data collection
            self.resume_collection = self.client.get_or_create_collection(
                name=CHROMA_CONFIG['collection_name_resumes'],
                embedding_function=self.embedding_function,
                metadata={"description": "Resume analysis data with vector embeddings"}
            )
            
            # Feedback collection
            self.feedback_collection = self.client.get_or_create_collection(
                name=CHROMA_CONFIG['collection_name_feedback'],
                embedding_function=self.embedding_function,
                metadata={"description": "User feedback data"}
            )
            
        except Exception as e:
            st.error(f"Collection initialization failed: {e}")
            raise
    
    def insert_user_data(self, data: Dict[str, Any]) -> bool:
        """Insert or update resume data with duplicate prevention and enhanced embeddings"""
        try:
            # Check for existing record based on email or name
            existing_record_id = self._find_existing_record(data.get('email', ''), data.get('name', ''))
            
            if existing_record_id:
                st.info(f"**Updating existing record** for {data.get('name', 'Unknown')} ({data.get('email', 'No email')})")
                return self._update_existing_record(existing_record_id, data)
            
            # Generate unique ID for new record
            record_id = str(uuid.uuid4())
            
            # Create enhanced document content with tagged metadata
            document_content = self._create_enhanced_document_content(data)
            
            # Prepare comprehensive metadata
            metadata = {
                'sec_token': str(data.get('sec_token', '')),
                'ip_add': str(data.get('ip_add', '')),
                'host_name': str(data.get('host_name', '')),
                'dev_user': str(data.get('dev_user', '')),
                'os_name_ver': str(data.get('os_name_ver', '')),
                'latlong': str(data.get('latlong', '')),
                'city': str(data.get('city', '')),
                'state': str(data.get('state', '')),
                'country': str(data.get('country', '')),
                'act_name': str(data.get('act_name', '')),
                'act_mail': str(data.get('act_mail', '')),
                'act_mob': str(data.get('act_mob', '')),
                'name': str(data.get('name', 'Unknown')),
                'email': str(data.get('email', '')),
                'timestamp': str(data.get('timestamp', datetime.now().isoformat())),
                'no_of_pages': str(data.get('no_of_pages', '1')),
                'reco_field': str(data.get('reco_field', 'General')),
                'cand_level': str(data.get('cand_level', 'Unknown')),
                'pdf_name': str(data.get('pdf_name', '')),
                'record_type': 'resume_analysis',
                # Enhanced metadata for robust searching
                'skills': str(data.get('skills', '')),
                'work_experiences': str(data.get('work_experiences', '')),
                'educations': str(data.get('educations', '')),
                'years_of_experience': str(data.get('years_of_experience', '')),
                'field_specific_experience': str(data.get('field_specific_experience', '')),
                'career_transition_history': str(data.get('career_transition_history', '')),
                'primary_field': str(data.get('primary_field', '')),
                'full_resume_data': str(data.get('full_resume_data', '')),
                'extracted_text': str(data.get('extracted_text', '')),
                'contact_info': str(data.get('contact_info', ''))
            }
            
            # Add to collection with enhanced embedding
            self.resume_collection.add(
                documents=[document_content],
                metadatas=[metadata],
                ids=[record_id]
            )
            
            st.success(f"**New record created** for {data.get('name', 'Unknown')}")
            return True
            
        except Exception as e:
            st.error(f"Resume data insertion failed: {e}")
            return False
    
    def insert_feedback(self, data: Dict[str, Any]) -> bool:
        """Insert feedback data into vector database"""
        try:
            # Generate unique ID
            record_id = str(uuid.uuid4())
            
            # Create document content for feedback
            document_content = f"Feedback from {data.get('feed_name', '')}: {data.get('comments', '')}"
            
            # Prepare metadata
            metadata = {
                'feed_name': str(data.get('feed_name', '')),
                'feed_email': str(data.get('feed_email', '')),
                'feed_score': str(data.get('feed_score', '0')),
                'comments': str(data.get('comments', '')),
                'timestamp': str(data.get('timestamp', datetime.now().isoformat())),
                'record_type': 'user_feedback'
            }
            
            # Add to feedback collection
            self.feedback_collection.add(
                documents=[document_content],
                metadatas=[metadata],
                ids=[record_id]
            )
            
            return True
            
        except Exception as e:
            st.error(f"Feedback insertion failed: {e}")
            return False
    
    def get_user_data(self) -> Optional[pd.DataFrame]:
        """Get all resume data as DataFrame for analytics compatibility"""
        try:
            # Get all documents from resume collection
            results = self.resume_collection.get()
            
            if not results['metadatas']:
                return pd.DataFrame()
            
            # Convert to DataFrame format compatible with existing analytics
            data_rows = []
            for metadata in results['metadatas']:
                row = {
                    'ID': metadata.get('sec_token', ''),
                    'sec_token': metadata.get('sec_token', ''),
                    'ip_add': metadata.get('ip_add', ''),
                    'host_name': metadata.get('host_name', ''),
                    'dev_user': metadata.get('dev_user', ''),
                    'os_name_ver': metadata.get('os_name_ver', ''),
                    'latlong': metadata.get('latlong', ''),
                    'city': metadata.get('city', ''),
                    'state': metadata.get('state', ''),
                    'country': metadata.get('country', ''),
                    'act_name': metadata.get('act_name', ''),
                    'act_mail': metadata.get('act_mail', ''),
                    'act_mob': metadata.get('act_mob', ''),
                    'Name': metadata.get('name', ''),
                    'Email_ID': metadata.get('email', ''),
                    'Timestamp': metadata.get('timestamp', ''),
                    'Page_no': metadata.get('no_of_pages', ''),
                    'Predicted_Field': metadata.get('reco_field', ''),
                    'User_level': metadata.get('cand_level', ''),
                    'Actual_skills': metadata.get('skills', ''),
                    'Field_Experience': metadata.get('field_specific_experience', ''),
                    'Career_Transitions': metadata.get('career_transition_history', ''),
                    'pdf_name': metadata.get('pdf_name', '')
                }
                data_rows.append(row)
            
            return pd.DataFrame(data_rows)
            
        except Exception as e:
            st.error(f"Failed to fetch user data: {e}")
            return pd.DataFrame()
    
    def get_feedback_data(self) -> Optional[pd.DataFrame]:
        """Get all feedback data as DataFrame"""
        try:
            # Get all documents from feedback collection
            results = self.feedback_collection.get()
            
            if not results['metadatas']:
                return pd.DataFrame()
            
            # Convert to DataFrame
            data_rows = []
            for metadata in results['metadatas']:
                row = {
                    'ID': len(data_rows) + 1,  # Auto-increment ID
                    'feed_name': metadata.get('feed_name', ''),
                    'feed_email': metadata.get('feed_email', ''),
                    'feed_score': metadata.get('feed_score', ''),
                    'comments': metadata.get('comments', ''),
                    'Timestamp': metadata.get('timestamp', '')
                }
                data_rows.append(row)
            
            return pd.DataFrame(data_rows)
            
        except Exception as e:
            st.error(f"❌ Failed to fetch feedback data: {e}")
            return pd.DataFrame()
    
    def get_analytics_data(self) -> Optional[pd.DataFrame]:
        """Get analytics data compatible with existing charts"""
        try:
            # Get resume data and format for analytics
            results = self.resume_collection.get()
            
            if not results['metadatas']:
                return pd.DataFrame()
            
            data_rows = []
            for i, metadata in enumerate(results['metadatas']):
                row = {
                    'ID': i + 1,
                    'ip_add': metadata.get('ip_add', ''),
                    'Predicted_Field': metadata.get('reco_field', ''),
                    'User_Level': metadata.get('cand_level', ''),
                    'Field_Experience': metadata.get('field_specific_experience', ''),
                    'city': metadata.get('city', ''),
                    'state': metadata.get('state', ''),
                    'country': metadata.get('country', '')
                }
                data_rows.append(row)
            
            return pd.DataFrame(data_rows)
            
        except Exception as e:
            st.error(f"❌ Failed to fetch analytics data: {e}")
            return pd.DataFrame()
    
    def get_user_count(self) -> int:
        """Get total number of resume records"""
        try:
            results = self.resume_collection.count()
            return results
        except Exception as e:
            st.error(f"❌ Failed to get user count: {e}")
            return 0
    
    def semantic_search_resumes(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search on resume data - NEW FEATURE for LLM integration"""
        try:
            results = self.resume_collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            search_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
                    }
                    search_results.append(result)
            
            return search_results
            
        except Exception as e:
            st.error(f"❌ Semantic search failed: {e}")
            return []
    
    def get_similar_candidates(self, skills: List[str], field: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Find similar candidates based on skills and field - NEW FEATURE for HR"""
        try:
            # Create search query from skills and field
            query = f"Skills: {', '.join(skills)}. Field: {field}"
            
            results = self.resume_collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances'],
                where={'reco_field': field}  # Filter by field
            )
            
            candidates = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    candidate = {
                        'name': results['metadatas'][0][i].get('name', 'Unknown'),
                        'email': results['metadatas'][0][i].get('email', ''),
                        'field': results['metadatas'][0][i].get('reco_field', ''),
                        'level': results['metadatas'][0][i].get('cand_level', ''),
                        'similarity': round((1 - results['distances'][0][i]) * 100, 2),
                        'pdf_name': results['metadatas'][0][i].get('pdf_name', '')
                    }
                    candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            st.error(f"❌ Similar candidates search failed: {e}")
            return []
    
    def _find_existing_record(self, email: str, name: str) -> Optional[str]:
        """Find existing record by email or name to prevent duplicates"""
        try:
            if not email and not name:
                return None
            
            # Search by email first (more reliable)
            if email:
                results = self.resume_collection.get(
                    where={"email": email},
                    include=['metadatas']
                )
                if results['ids']:
                    return results['ids'][0]
            
            # If no email match, search by name
            if name and name != 'Unknown':
                results = self.resume_collection.get(
                    where={"name": name},
                    include=['metadatas']
                )
                if results['ids']:
                    return results['ids'][0]
            
            return None
            
        except Exception as e:
            st.warning(f"⚠️ Duplicate check failed: {e}")
            return None
    
    def _update_existing_record(self, record_id: str, new_data: Dict[str, Any]) -> bool:
        """Update existing record with new data"""
        try:
            # Delete old record
            self.resume_collection.delete(ids=[record_id])
            
            # Create enhanced document content
            document_content = self._create_enhanced_document_content(new_data)
            
            # Prepare updated metadata
            metadata = {
                'sec_token': str(new_data.get('sec_token', '')),
                'ip_add': str(new_data.get('ip_add', '')),
                'host_name': str(new_data.get('host_name', '')),
                'dev_user': str(new_data.get('dev_user', '')),
                'os_name_ver': str(new_data.get('os_name_ver', '')),
                'latlong': str(new_data.get('latlong', '')),
                'city': str(new_data.get('city', '')),
                'state': str(new_data.get('state', '')),
                'country': str(new_data.get('country', '')),
                'act_name': str(new_data.get('act_name', '')),
                'act_mail': str(new_data.get('act_mail', '')),
                'act_mob': str(new_data.get('act_mob', '')),
                'name': str(new_data.get('name', 'Unknown')),
                'email': str(new_data.get('email', '')),
                'timestamp': str(new_data.get('timestamp', datetime.now().isoformat())),
                'no_of_pages': str(new_data.get('no_of_pages', '1')),
                'reco_field': str(new_data.get('reco_field', 'General')),
                'cand_level': str(new_data.get('cand_level', 'Unknown')),
                'pdf_name': str(new_data.get('pdf_name', '')),
                'record_type': 'resume_analysis',
                'skills': str(new_data.get('skills', '')),
                'work_experiences': str(new_data.get('work_experiences', '')),
                'educations': str(new_data.get('educations', '')),
                'years_of_experience': str(new_data.get('years_of_experience', '')),
                'field_specific_experience': str(new_data.get('field_specific_experience', '')),
                'career_transition_history': str(new_data.get('career_transition_history', '')),
                'primary_field': str(new_data.get('primary_field', '')),
                'full_resume_data': str(new_data.get('full_resume_data', '')),
                'extracted_text': str(new_data.get('extracted_text', '')),
                'contact_info': str(new_data.get('contact_info', '')),
                'updated_at': datetime.now().isoformat()
            }
            
            # Re-add with same ID
            self.resume_collection.add(
                documents=[document_content],
                metadatas=[metadata],
                ids=[record_id]
            )
            
            return True
            
        except Exception as e:
            st.error(f"❌ Record update failed: {e}")
            return False
    
    def _create_enhanced_document_content(self, data: Dict[str, Any]) -> str:
        """Create enhanced document content using tagged metadata approach"""
        
        # Use the tagged extracted text as the primary document content
        extracted_text = data.get('extracted_text', '')
        if extracted_text:
            # The tagged text already contains structured metadata
            base_content = extracted_text
        else:
            # Fallback to basic content creation
            base_content = self._create_basic_document_content(data)
        
        # Add contextual information for better embeddings
        context_parts = []
        
        # Field-specific experience context
        field_exp = data.get('field_specific_experience', '')
        if field_exp:
            context_parts.append(f"[CONTEXT:FIELD_EXPERIENCE] {field_exp}")
        
        # Career transition context
        transitions = data.get('career_transition_history', '')
        if transitions and transitions != 'No transitions detected':
            context_parts.append(f"[CONTEXT:CAREER_TRANSITIONS] {transitions}")
        
        # Combine base content with context
        if context_parts:
            return f"{base_content} || {' || '.join(context_parts)}"
        else:
            return base_content
    
    def _create_basic_document_content(self, data: Dict[str, Any]) -> str:
        """Create basic document content as fallback"""
        name = data.get('name', 'Unknown Candidate')
        field = data.get('reco_field', 'General')
        level = data.get('cand_level', 'Unknown Level')
        skills = str(data.get('skills', ''))
        
        # Start with basic information
        content_parts = [
            f"Candidate: {name}",
            f"Professional Field: {field}",
            f"Experience Level: {level}",
            f"Skills and Competencies: {skills}",
            f"Location: {data.get('city', '')}, {data.get('state', '')}, {data.get('country', '')}"
        ]
        
        # Add detailed information if available
        work_experiences = data.get('work_experiences', '')
        if work_experiences:
            content_parts.append(f"Work Experience Details: {work_experiences}")
        
        educations = data.get('educations', '')
        if educations:
            content_parts.append(f"Education Background: {educations}")
        
        years_exp = data.get('years_of_experience', '')
        if years_exp:
            content_parts.append(f"Years of Experience: {years_exp}")
        
        full_data = data.get('full_resume_data', '')
        if full_data:
            content_parts.append(f"Additional Resume Information: {full_data}")
        
        return "\n".join(content_parts)
    
    def reset_database(self) -> bool:
        """Reset all collections (useful for development)"""
        try:
            self.client.reset()
            self._initialize_collections()
            st.success("Vector database reset successfully")
            return True
        except Exception as e:
            st.error(f"Database reset failed: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics - NEW FEATURE"""
        try:
            stats = {
                'total_resumes': self.resume_collection.count(),
                'total_feedback': self.feedback_collection.count(),
                'collections': len(self.client.list_collections()),
                'embedding_model': CHROMA_CONFIG['embedding_model']
            }
            return stats
        except Exception as e:
            st.error(f"❌ Failed to get database stats: {e}")
            return {}
    
    # CRUD Operations for Database Management
    
    def get_resume_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific resume record by ID"""
        try:
            results = self.resume_collection.get(
                ids=[record_id],
                include=['documents', 'metadatas']
            )
            
            if results['metadatas'] and results['metadatas'][0]:
                return {
                    'id': record_id,
                    'document': results['documents'][0] if results['documents'] else '',
                    'metadata': results['metadatas'][0]
                }
            return None
            
        except Exception as e:
            st.error(f"❌ Failed to get resume record: {e}")
            return None
    
    def get_feedback_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific feedback record by ID"""
        try:
            results = self.feedback_collection.get(
                ids=[record_id],
                include=['documents', 'metadatas']
            )
            
            if results['metadatas'] and results['metadatas'][0]:
                return {
                    'id': record_id,
                    'document': results['documents'][0] if results['documents'] else '',
                    'metadata': results['metadatas'][0]
                }
            return None
            
        except Exception as e:
            st.error(f"❌ Failed to get feedback record: {e}")
            return None
    
    def get_all_resume_ids(self) -> List[str]:
        """Get all resume record IDs"""
        try:
            results = self.resume_collection.get()
            return results.get('ids', [])
        except Exception as e:
            st.error(f"❌ Failed to get resume IDs: {e}")
            return []
    
    def get_all_feedback_ids(self) -> List[str]:
        """Get all feedback record IDs"""
        try:
            results = self.feedback_collection.get()
            return results.get('ids', [])
        except Exception as e:
            st.error(f"❌ Failed to get feedback IDs: {e}")
            return []
    
    def update_resume_record(self, record_id: str, updated_data: Dict[str, Any]) -> bool:
        """Update a resume record"""
        try:
            # Get existing record
            existing = self.get_resume_by_id(record_id)
            if not existing:
                st.error("Record not found")
                return False
            
            # Update metadata
            updated_metadata = existing['metadata'].copy()
            updated_metadata.update({
                'name': str(updated_data.get('name', updated_metadata.get('name', ''))),
                'email': str(updated_data.get('email', updated_metadata.get('email', ''))),
                'reco_field': str(updated_data.get('reco_field', updated_metadata.get('reco_field', ''))),
                'cand_level': str(updated_data.get('cand_level', updated_metadata.get('cand_level', ''))),
                'city': str(updated_data.get('city', updated_metadata.get('city', ''))),
                'state': str(updated_data.get('state', updated_metadata.get('state', ''))),
                'skills': str(updated_data.get('skills', updated_metadata.get('skills', ''))),
                'pdf_name': str(updated_data.get('pdf_name', updated_metadata.get('pdf_name', '')))
            })
            
            # Create updated document content
            updated_document = self._create_document_content(updated_metadata)
            
            # Delete old record and add updated one
            self.resume_collection.delete(ids=[record_id])
            self.resume_collection.add(
                documents=[updated_document],
                metadatas=[updated_metadata],
                ids=[record_id]
            )
            
            return True
            
        except Exception as e:
            st.error(f"❌ Failed to update resume record: {e}")
            return False
    
    def update_feedback_record(self, record_id: str, updated_data: Dict[str, Any]) -> bool:
        """Update a feedback record"""
        try:
            # Get existing record
            existing = self.get_feedback_by_id(record_id)
            if not existing:
                st.error("Record not found")
                return False
            
            # Update metadata
            updated_metadata = existing['metadata'].copy()
            updated_metadata.update({
                'feed_name': str(updated_data.get('feed_name', updated_metadata.get('feed_name', ''))),
                'feed_email': str(updated_data.get('feed_email', updated_metadata.get('feed_email', ''))),
                'feed_score': str(updated_data.get('feed_score', updated_metadata.get('feed_score', ''))),
                'comments': str(updated_data.get('comments', updated_metadata.get('comments', '')))
            })
            
            # Create updated document content
            updated_document = f"Feedback from {updated_metadata.get('feed_name', '')}: {updated_metadata.get('comments', '')}"
            
            # Delete old record and add updated one
            self.feedback_collection.delete(ids=[record_id])
            self.feedback_collection.add(
                documents=[updated_document],
                metadatas=[updated_metadata],
                ids=[record_id]
            )
            
            return True
            
        except Exception as e:
            st.error(f"❌ Failed to update feedback record: {e}")
            return False
    
    def delete_resume_record(self, record_id: str) -> bool:
        """Delete a resume record"""
        try:
            self.resume_collection.delete(ids=[record_id])
            return True
        except Exception as e:
            st.error(f"❌ Failed to delete resume record: {e}")
            return False
    
    def delete_feedback_record(self, record_id: str) -> bool:
        """Delete a feedback record"""
        try:
            self.feedback_collection.delete(ids=[record_id])
            return True
        except Exception as e:
            st.error(f"❌ Failed to delete feedback record: {e}")
            return False
    
    def create_manual_resume_record(self, data: Dict[str, Any]) -> bool:
        """Create a new resume record manually"""
        try:
            # Generate unique ID
            record_id = str(uuid.uuid4())
            
            # Create document content
            document_content = self._create_document_content(data)
            
            # Prepare metadata
            metadata = {
                'sec_token': str(data.get('sec_token', str(uuid.uuid4()))),
                'name': str(data.get('name', '')),
                'email': str(data.get('email', '')),
                'reco_field': str(data.get('reco_field', 'General')),
                'cand_level': str(data.get('cand_level', 'Unknown')),
                'city': str(data.get('city', '')),
                'state': str(data.get('state', '')),
                'country': str(data.get('country', '')),
                'skills': str(data.get('skills', '')),
                'pdf_name': str(data.get('pdf_name', 'Manual Entry')),
                'timestamp': datetime.now().isoformat(),
                'record_type': 'resume_analysis',
                'ip_add': str(data.get('ip_add', 'Manual')),
                'host_name': str(data.get('host_name', 'Manual')),
                'dev_user': str(data.get('dev_user', 'Manual')),
                'os_name_ver': str(data.get('os_name_ver', 'Manual')),
                'latlong': str(data.get('latlong', '')),
                'act_name': str(data.get('act_name', 'MANUAL_ENTRY')),
                'act_mail': str(data.get('act_mail', 'manual@system.com')),
                'act_mob': str(data.get('act_mob', 'N/A')),
                'no_of_pages': str(data.get('no_of_pages', '1'))
            }
            
            # Add to collection
            self.resume_collection.add(
                documents=[document_content],
                metadatas=[metadata],
                ids=[record_id]
            )
            
            return True
            
        except Exception as e:
            st.error(f"❌ Failed to create resume record: {e}")
            return False
    
    def create_manual_feedback_record(self, data: Dict[str, Any]) -> bool:
        """Create a new feedback record manually"""
        try:
            # Generate unique ID
            record_id = str(uuid.uuid4())
            
            # Create document content
            document_content = f"Feedback from {data.get('feed_name', '')}: {data.get('comments', '')}"
            
            # Prepare metadata
            metadata = {
                'feed_name': str(data.get('feed_name', '')),
                'feed_email': str(data.get('feed_email', '')),
                'feed_score': str(data.get('feed_score', '5')),
                'comments': str(data.get('comments', '')),
                'timestamp': datetime.now().isoformat(),
                'record_type': 'user_feedback'
            }
            
            # Add to collection
            self.feedback_collection.add(
                documents=[document_content],
                metadatas=[metadata],
                ids=[record_id]
            )
            
            return True
            
        except Exception as e:
            st.error(f"❌ Failed to create feedback record: {e}")
            return False
    
    def close(self):
        """Close database connections (ChromaDB handles this automatically)"""
        try:
            # ChromaDB handles cleanup automatically
            pass
        except Exception as e:
            st.error(f"❌ Error during database cleanup: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Global vector database instance (renamed for clarity)
db_manager = VectorDatabaseManager() 