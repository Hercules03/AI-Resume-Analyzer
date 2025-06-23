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
            
            st.success("✅ ChromaDB Vector Database Connected")
            
        except Exception as e:
            st.error(f"❌ ChromaDB connection failed: {e}")
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
            
            st.info(f"📊 Collections ready: {len(self.client.list_collections())} active")
            
        except Exception as e:
            st.error(f"❌ Collection initialization failed: {e}")
            raise
    
    def insert_user_data(self, data: Dict[str, Any]) -> bool:
        """Insert resume data into vector database with semantic embeddings"""
        try:
            # Generate unique ID
            record_id = str(uuid.uuid4())
            
            # Create document content for embedding (combining key resume information)
            document_content = self._create_document_content(data)
            
            # Prepare metadata (non-embedded structured data)
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
                'resume_score': str(data.get('resume_score', '0')),
                'timestamp': str(data.get('timestamp', datetime.now().isoformat())),
                'no_of_pages': str(data.get('no_of_pages', '1')),
                'reco_field': str(data.get('reco_field', 'General')),
                'cand_level': str(data.get('cand_level', 'Unknown')),
                'pdf_name': str(data.get('pdf_name', '')),
                'record_type': 'resume_analysis'
            }
            
            # Add to collection with embedding
            self.resume_collection.add(
                documents=[document_content],
                metadatas=[metadata],
                ids=[record_id]
            )
            
            return True
            
        except Exception as e:
            st.error(f"❌ Resume data insertion failed: {e}")
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
            st.error(f"❌ Feedback insertion failed: {e}")
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
                    'resume_score': metadata.get('resume_score', ''),
                    'Timestamp': metadata.get('timestamp', ''),
                    'Page_no': metadata.get('no_of_pages', ''),
                    'Predicted_Field': metadata.get('reco_field', ''),
                    'User_level': metadata.get('cand_level', ''),
                    'Actual_skills': metadata.get('skills', ''),
                    'Recommended_skills': metadata.get('recommended_skills', ''),
                    'Recommended_courses': metadata.get('courses', ''),
                    'pdf_name': metadata.get('pdf_name', '')
                }
                data_rows.append(row)
            
            return pd.DataFrame(data_rows)
            
        except Exception as e:
            st.error(f"❌ Failed to fetch user data: {e}")
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
                    'resume_score': metadata.get('resume_score', ''),
                    'Predicted_Field': metadata.get('reco_field', ''),
                    'User_Level': metadata.get('cand_level', ''),
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
                        'score': results['metadatas'][0][i].get('resume_score', ''),
                        'similarity': round((1 - results['distances'][0][i]) * 100, 2),
                        'pdf_name': results['metadatas'][0][i].get('pdf_name', '')
                    }
                    candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            st.error(f"❌ Similar candidates search failed: {e}")
            return []
    
    def _create_document_content(self, data: Dict[str, Any]) -> str:
        """Create rich document content for semantic embedding"""
        name = data.get('name', 'Unknown Candidate')
        field = data.get('reco_field', 'General')
        level = data.get('cand_level', 'Unknown Level')
        skills = str(data.get('skills', ''))
        score = data.get('resume_score', '0')
        
        # Create a rich text representation for better embeddings
        content = f"""
        Candidate: {name}
        Professional Field: {field}
        Experience Level: {level}
        Resume Completeness Score: {score}%
        Skills and Competencies: {skills}
        Location: {data.get('city', '')}, {data.get('state', '')}, {data.get('country', '')}
        """
        
        return content.strip()
    
    def reset_database(self) -> bool:
        """Reset all collections (useful for development)"""
        try:
            self.client.reset()
            self._initialize_collections()
            st.success("✅ Vector database reset successfully")
            return True
        except Exception as e:
            st.error(f"❌ Database reset failed: {e}")
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