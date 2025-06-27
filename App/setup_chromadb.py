"""
ChromaDB Setup and Testing Script for AI Resume Analyzer
Run this script to initialize and test the vector database setup.
"""

import sys
import os
import traceback
from pathlib import Path

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def test_chromadb_installation():
    """Test if ChromaDB and related dependencies are properly installed."""
    print("🔧 Testing ChromaDB installation...")
    
    try:
        import chromadb
        print("✅ ChromaDB installed successfully")
        
        import sentence_transformers
        print("✅ Sentence Transformers installed successfully")
        
        from chromadb.utils import embedding_functions
        print("✅ ChromaDB embedding functions available")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\n📦 Please install missing dependencies:")
        print("pip install chromadb sentence-transformers faiss-cpu")
        return False

def initialize_chromadb():
    """Initialize ChromaDB with test collections."""
    print("\n🔄 Initializing ChromaDB...")
    
    try:
        from database import VectorDatabaseManager
        
        # Create database manager instance
        db_manager = VectorDatabaseManager()
        
        print("✅ ChromaDB initialized successfully")
        
        # Test basic functionality
        print("\n🧪 Testing database operations...")
        
        # Test user data insertion
        test_user_data = {
            'sec_token': 'test_token_001',
            'ip_add': '127.0.0.1',
            'host_name': 'localhost',
            'dev_user': 'test_user',
            'os_name_ver': 'Windows 10',
            'latlong': '40.7128,-74.0060',
            'city': 'New York',
            'state': 'NY',
            'country': 'USA',
            'act_name': 'Test HR User',
            'act_mail': 'hr@test.com',
            'act_mob': '+1234567890',
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'timestamp': '2024-01-01T12:00:00',
            'no_of_pages': '2',
            'reco_field': 'Data Science & Analytics',
            'cand_level': 'Mid Level',
            'skills': "['Python', 'Machine Learning', 'SQL', 'TensorFlow']",
            'recommended_skills': 'Advanced Python, Deep Learning',
            'courses': 'AI_Recommended_Field: Data Science & Analytics',
            'pdf_name': 'john_doe_resume.pdf'
        }
        
        # Insert test data
        success = db_manager.insert_user_data(test_user_data)
        if success:
            print("✅ Test resume data inserted successfully")
        else:
            print("❌ Failed to insert test resume data")
            return False
        
        # Test feedback insertion
        test_feedback = {
            'feed_name': 'HR Manager',
            'feed_email': 'hr.manager@company.com',
            'feed_score': '5',
            'comments': 'Excellent vector database integration!',
            'timestamp': '2024-01-01T12:00:00'
        }
        
        success = db_manager.insert_feedback(test_feedback)
        if success:
            print("✅ Test feedback data inserted successfully")
        else:
            print("❌ Failed to insert test feedback data")
            return False
        
        # Test data retrieval
        user_count = db_manager.get_user_count()
        print(f"✅ Database contains {user_count} resume records")
        
        # Test semantic search
        search_results = db_manager.semantic_search_resumes("Python developer", n_results=3)
        print(f"✅ Semantic search returned {len(search_results)} results")
        
        # Test similar candidate search
        similar_candidates = db_manager.get_similar_candidates(['Python', 'Machine Learning'], 'Data Science & Analytics', 3)
        print(f"✅ Similar candidate search returned {len(similar_candidates)} candidates")
        
        # Get database statistics
        stats = db_manager.get_database_stats()
        print(f"✅ Database statistics: {stats}")
        
        print("\n🎉 ChromaDB setup completed successfully!")
        print("📊 Your vector database is ready for AI-powered resume analysis!")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB initialization failed: {e}")
        print("\n🔍 Full error details:")
        traceback.print_exc()
        return False

def test_embedding_functionality():
    """Test embedding generation and similarity search."""
    print("\n🧬 Testing embedding functionality...")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # Initialize the embedding model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Test sentences
        sentences = [
            "Python developer with machine learning experience",
            "Senior software engineer specializing in backend development",
            "Data scientist with expertise in deep learning and NLP"
        ]
        
        # Generate embeddings
        embeddings = model.encode(sentences)
        print(f"✅ Generated embeddings for {len(sentences)} sentences")
        print(f"✅ Embedding dimension: {embeddings.shape[1]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        return False

def cleanup_test_data():
    """Clean up test data from the database."""
    print("\n🧹 Cleaning up test data...")
    
    try:
        from database import VectorDatabaseManager
        
        db_manager = VectorDatabaseManager()
        
        # Note: ChromaDB doesn't have built-in delete by metadata
        # For production, you'd implement more sophisticated cleanup
        print("⚠️ Note: Test data will remain in the database")
        print("💡 Use the admin panel to reset the database if needed")
        
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 AI Resume Analyzer - ChromaDB Vector Database Setup")
    print("=" * 60)
    
    # Step 1: Test installation
    if not test_chromadb_installation():
        print("\n❌ Setup failed: Missing dependencies")
        return False
    
    # Step 2: Test embedding functionality
    if not test_embedding_functionality():
        print("\n❌ Setup failed: Embedding functionality test failed")
        return False
    
    # Step 3: Initialize ChromaDB
    if not initialize_chromadb():
        print("\n❌ Setup failed: ChromaDB initialization failed")
        return False
    
    # Step 4: Provide next steps
    print("\n🎯 Next Steps:")
    print("1. Run the main application: streamlit run main.py")
    print("2. Upload some resumes using 'Candidate Evaluation'")
    print("3. Try the new 'Vector Search' feature!")
    print("4. Access admin panel to view vector database statistics")
    
    print("\n💡 Tips:")
    print("- Vector database is stored in ./chroma_db/ directory")
    print("- Use development mode to see detailed extraction process")
    print("- Semantic search works best with natural language queries")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed!")
        sys.exit(1) 