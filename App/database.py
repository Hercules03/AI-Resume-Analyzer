"""
Database operations for AI Resume Analyzer
"""
import pymysql
import pandas as pd
import streamlit as st
from typing import Optional, Dict, Any, List
from config import DB_CONFIG


class DatabaseManager:
    """Centralized database operations manager"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Establish database connection"""
        try:
            self.connection = pymysql.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor()
            
            # Create database if it doesn't exist
            self.cursor.execute("CREATE DATABASE IF NOT EXISTS cv")
            self.cursor.execute("USE cv")
            
        except Exception as e:
            st.error(f"Database connection failed: {e}")
            raise
    
    def _create_tables(self):
        """Create required database tables"""
        try:
            # User data table
            user_data_sql = """
            CREATE TABLE IF NOT EXISTS user_data (
                ID INT NOT NULL AUTO_INCREMENT,
                sec_token VARCHAR(20) NOT NULL,
                ip_add VARCHAR(50) NULL,
                host_name VARCHAR(50) NULL,
                dev_user VARCHAR(50) NULL,
                os_name_ver VARCHAR(50) NULL,
                latlong VARCHAR(50) NULL,
                city VARCHAR(50) NULL,
                state VARCHAR(50) NULL,
                country VARCHAR(50) NULL,
                act_name VARCHAR(50) NOT NULL,
                act_mail VARCHAR(50) NOT NULL,
                act_mob VARCHAR(20) NOT NULL,
                Name VARCHAR(500) NOT NULL,
                Email_ID VARCHAR(500) NOT NULL,
                resume_score VARCHAR(8) NOT NULL,
                Timestamp VARCHAR(50) NOT NULL,
                Page_no VARCHAR(5) NOT NULL,
                Predicted_Field BLOB NOT NULL,
                User_level BLOB NOT NULL,
                Actual_skills BLOB NOT NULL,
                Recommended_skills BLOB NOT NULL,
                Recommended_courses BLOB NOT NULL,
                pdf_name VARCHAR(50) NOT NULL,
                PRIMARY KEY (ID)
            )
            """
            self.cursor.execute(user_data_sql)
            
            # Feedback table
            feedback_sql = """
            CREATE TABLE IF NOT EXISTS user_feedback (
                ID INT NOT NULL AUTO_INCREMENT,
                feed_name VARCHAR(50) NOT NULL,
                feed_email VARCHAR(50) NOT NULL,
                feed_score VARCHAR(5) NOT NULL,
                comments VARCHAR(100) NULL,
                Timestamp VARCHAR(50) NOT NULL,
                PRIMARY KEY (ID)
            )
            """
            self.cursor.execute(feedback_sql)
            
            self.connection.commit()
            
        except Exception as e:
            st.error(f"Table creation failed: {e}")
            raise
    
    def insert_user_data(self, data: Dict[str, Any]) -> bool:
        """Insert user data into database"""
        try:
            insert_sql = """
            INSERT INTO user_data VALUES (
                0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
            )
            """
            
            values = (
                data.get('sec_token'),
                data.get('ip_add'),
                data.get('host_name'),
                data.get('dev_user'),
                data.get('os_name_ver'),
                data.get('latlong'),
                data.get('city'),
                data.get('state'),
                data.get('country'),
                data.get('act_name'),
                data.get('act_mail'),
                data.get('act_mob'),
                data.get('name'),
                data.get('email'),
                data.get('resume_score'),
                data.get('timestamp'),
                data.get('no_of_pages'),
                data.get('reco_field'),
                data.get('cand_level'),
                data.get('skills'),
                data.get('recommended_skills'),
                data.get('courses'),
                data.get('pdf_name')
            )
            
            self.cursor.execute(insert_sql, values)
            self.connection.commit()
            return True
            
        except Exception as e:
            st.error(f"User data insertion failed: {e}")
            return False
    
    def insert_feedback(self, data: Dict[str, Any]) -> bool:
        """Insert feedback data into database"""
        try:
            insert_sql = """
            INSERT INTO user_feedback VALUES (0,%s,%s,%s,%s,%s)
            """
            
            values = (
                data.get('feed_name'),
                data.get('feed_email'),
                data.get('feed_score'),
                data.get('comments'),
                data.get('timestamp')
            )
            
            self.cursor.execute(insert_sql, values)
            self.connection.commit()
            return True
            
        except Exception as e:
            st.error(f"Feedback insertion failed: {e}")
            return False
    
    def get_user_data(self) -> Optional[pd.DataFrame]:
        """Get all user data"""
        try:
            query = """
            SELECT ID, sec_token, ip_add, act_name, act_mail, act_mob, 
                   CONVERT(Predicted_Field USING utf8), Timestamp, Name, Email_ID, 
                   resume_score, Page_no, pdf_name, CONVERT(User_level USING utf8), 
                   CONVERT(Actual_skills USING utf8), CONVERT(Recommended_skills USING utf8), 
                   CONVERT(Recommended_courses USING utf8), city, state, country, 
                   latlong, os_name_ver, host_name, dev_user 
            FROM user_data
            """
            
            return pd.read_sql(query, self.connection)
            
        except Exception as e:
            st.error(f"Failed to fetch user data: {e}")
            return None
    
    def get_feedback_data(self) -> Optional[pd.DataFrame]:
        """Get all feedback data"""
        try:
            query = "SELECT * FROM user_feedback"
            return pd.read_sql(query, self.connection)
            
        except Exception as e:
            st.error(f"Failed to fetch feedback data: {e}")
            return None
    
    def get_analytics_data(self) -> Optional[pd.DataFrame]:
        """Get data for analytics"""
        try:
            query = """
            SELECT ID, ip_add, resume_score, CONVERT(Predicted_Field USING utf8) as Predicted_Field, 
                   CONVERT(User_level USING utf8) as User_Level, city, state, country 
            FROM user_data
            """
            
            return pd.read_sql(query, self.connection)
            
        except Exception as e:
            st.error(f"Failed to fetch analytics data: {e}")
            return None
    
    def get_user_count(self) -> int:
        """Get total number of users"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM user_data")
            count = self.cursor.fetchone()[0]
            return count
            
        except Exception as e:
            st.error(f"Failed to get user count: {e}")
            return 0
    
    def close(self):
        """Close database connection"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
        except Exception as e:
            st.error(f"Error closing database connection: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Global database instance
db_manager = DatabaseManager() 