"""
RAG-powered Chatbot Service for Candidate Search using LangGraph and Specialists
"""
import streamlit as st
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

from database import db_manager
from config import LLM_CONFIG, SPECIALISTS_CONFIG
from db_specialists import (
    IntentSpecialist,
    NameExtractionSpecialist, 
    QueryEnhancementSpecialist,
    ResponseGenerationSpecialist
)


class ChatState(TypedDict):
    """State for the chatbot conversation"""
    messages: Annotated[list, add_messages]
    context: str
    search_query: str
    search_results: List[Dict[str, Any]]
    user_intent: str
    intent_confidence: float


class CandidateSearchChatbot:
    """RAG-powered chatbot for candidate search using specialized LLM functions"""
    
    def __init__(self):
        self.graph = None
        self.conversation_history = []
        
        # Initialize specialists
        self.intent_specialist = IntentSpecialist(SPECIALISTS_CONFIG['intent_analysis'])
        self.name_extraction_specialist = NameExtractionSpecialist(SPECIALISTS_CONFIG['name_extraction'])
        self.query_enhancement_specialist = QueryEnhancementSpecialist(SPECIALISTS_CONFIG['query_enhancement'])
        self.response_generation_specialist = ResponseGenerationSpecialist(SPECIALISTS_CONFIG['response_generation'])
        
        self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph workflow for RAG-powered conversation"""
        
        # Define the workflow
        workflow = StateGraph(ChatState)
        
        # Add nodes
        workflow.add_node("analyze_intent", self._analyze_intent)
        workflow.add_node("search_candidates", self._search_candidates)
        workflow.add_node("generate_response", self._generate_response)
        
        # Define edges
        workflow.add_edge(START, "analyze_intent")
        workflow.add_conditional_edges(
            "analyze_intent",
            self._route_based_on_intent,
            {
                "search": "search_candidates",
                "info": "search_candidates",  # Also search for specific info requests
                "general": "generate_response"
            }
        )
        workflow.add_edge("search_candidates", "generate_response")
        workflow.add_edge("generate_response", END)
        
        # Compile the graph
        self.graph = workflow.compile()
    
    def _analyze_intent(self, state: ChatState) -> Dict[str, Any]:
        """Analyze user intent using the intent specialist"""
        
        last_message = state["messages"][-1].content if state["messages"] else ""
        
        try:
            # Use intent specialist
            result = self.intent_specialist.execute(message=last_message)
            
            return {
                "user_intent": result['intent'],
                "intent_confidence": result['confidence'],
                "search_query": result['search_query']
            }
        
        except Exception as e:
            st.error(f"Intent analysis failed: {e}")
            return {
                "user_intent": "general",
                "intent_confidence": 0.5,
                "search_query": ""
            }
    
    def _route_based_on_intent(self, state: ChatState) -> str:
        """Route to appropriate node based on intent"""
        intent = state.get("user_intent", "general")
        return "search" if intent in ["search", "info"] else "general"
    
    def _filter_results_by_name(self, search_results: List[Dict[str, Any]], target_name: str) -> List[Dict[str, Any]]:
        """Filter search results to only include candidates with matching names"""
        
        if not target_name or not search_results:
            return search_results
        
        target_name_lower = target_name.lower().strip()
        target_parts = target_name_lower.split()
        
        filtered_results = []
        
        for result in search_results:
            metadata = result.get('metadata', {})
            candidate_name = metadata.get('name', '').lower().strip()
            
            if not candidate_name:
                continue
            
            candidate_parts = candidate_name.split()
            
            # Check for exact match
            if candidate_name == target_name_lower:
                filtered_results.append(result)
                continue
            
            # Check if all target name parts are in candidate name
            if all(part in candidate_parts for part in target_parts):
                filtered_results.append(result)
                continue
            
            # Check for partial matches (useful for different name formats)
            matches = sum(1 for part in target_parts if any(part in candidate_part for candidate_part in candidate_parts))
            if matches >= len(target_parts) * 0.7:  # 70% match threshold
                filtered_results.append(result)
        
        return filtered_results
    
    def _search_candidates(self, state: ChatState) -> Dict[str, Any]:
        """Search for candidates using ChromaDB semantic search"""
        
        search_query = state.get("search_query", "")
        user_intent = state.get("user_intent", "search")
        
        if not search_query:
            return {"search_results": [], "context": "No search query provided."}
        
        try:
            # For info requests, search more specifically for named candidates
            if user_intent == "info":
                # Extract potential names from the query using name extraction specialist
                candidate_name = self.name_extraction_specialist.execute(query=search_query)
                
                if candidate_name:
                    # Search specifically for this candidate
                    search_results = db_manager.semantic_search_resumes(candidate_name, n_results=50)
                    
                    # Filter results to only include candidates with matching names
                    filtered_results = self._filter_results_by_name(search_results, candidate_name)
                    
                    # If we found specific matches, use only those
                    if filtered_results:
                        search_results = filtered_results
                    else:
                        # If no exact matches, try a broader search but still limit results
                        search_results = search_results[:5]
                else:
                    # No specific name found, do a general search
                    search_results = db_manager.semantic_search_resumes(search_query, n_results=10)
            else:
                # Enhance the search query for better matching using query enhancement specialist
                enhanced_query = self.query_enhancement_specialist.execute(query=search_query)
                search_results = db_manager.semantic_search_resumes(enhanced_query, n_results=10)
            
            # Create context from search results
            context = self._create_context_from_results(search_results, user_intent, candidate_name if user_intent == "info" else None)
            
            return {
                "search_results": search_results,
                "context": context
            }
        
        except Exception as e:
            st.error(f"Candidate search failed: {e}")
            return {
                "search_results": [],
                "context": "Search failed due to technical error."
            }
        
    def _is_target_candidate(self, candidate_name: str, target_name: str) -> bool:
        """Check if the candidate name matches the target name"""
        
        if not candidate_name or not target_name:
            return False
        
        candidate_lower = candidate_name.lower().strip()
        target_lower = target_name.lower().strip()
        
        # Exact match
        if candidate_lower == target_lower:
            return True
        
        # Check if all target name parts are in candidate name
        target_parts = target_lower.split()
        candidate_parts = candidate_lower.split()
        
        # All target parts should be present in candidate name
        return all(any(target_part in candidate_part for candidate_part in candidate_parts) 
                for target_part in target_parts)
    
    def _extract_education_info(self, metadata: Dict[str, Any]) -> str:
        """Extract education information from metadata, checking multiple sources"""
        
        # First, check the educations field
        educations = metadata.get('educations', '')
        if educations and educations not in ['', 'Not extracted', 'No education details available']:
            return educations
        
        # If educations field is empty or not useful, check extracted_text for education tags
        extracted_text = metadata.get('extracted_text', '')
        if extracted_text and 'EDUCATION' in extracted_text.upper():
            # Look for education sections in the tagged extracted text
            education_sections = []
            sections = extracted_text.split('||')
            
            for section in sections:
                if 'EDUCATION' in section.upper():
                    # Clean up the section and extract meaningful information
                    clean_section = section.strip()
                    # Remove section tags and format nicely
                    if '[SECTION:EDUCATION' in clean_section:
                        clean_section = clean_section.split(']', 1)[-1].strip()
                    
                    # Replace tag markers with readable text
                    clean_section = clean_section.replace('[DEGREE]', 'Degree:')
                    clean_section = clean_section.replace('[FIELD_OF_STUDY]', 'Field:')
                    clean_section = clean_section.replace('[INSTITUTION]', 'Institution:')
                    clean_section = clean_section.replace('[GRADUATION]', 'Graduated:')
                    clean_section = clean_section.replace('[GPA]', 'GPA:')
                    clean_section = clean_section.replace('|', ',')
                    
                    if clean_section:
                        education_sections.append(clean_section)
            
            if education_sections:
                return '\n'.join(f"• {section}" for section in education_sections)
        
        # Check full_resume_data for education information
        full_resume = metadata.get('full_resume_data', '')
        if full_resume and ('education' in full_resume.lower() or 'degree' in full_resume.lower()):
            # Extract lines that might contain education information
            lines = full_resume.split(';')
            education_lines = [line.strip() for line in lines 
                             if any(edu_word in line.lower() for edu_word in ['education', 'degree', 'university', 'college', 'bachelor', 'master', 'phd'])]
            if education_lines:
                return '; '.join(education_lines)
        
        return 'No detailed education information available in database'
    
    def _create_context_from_results(self, search_results: List[Dict[str, Any]], intent: str = "search", specific_candidate: str = None) -> str:
        """Create context string from search results for the LLM with detailed CV content"""
        
        if not search_results:
            if specific_candidate:
                return f"No information found for candidate '{specific_candidate}' in the database."
            return "No candidates found matching the search criteria."
        
        context_parts = []
        
        # For info requests about a specific candidate, only show that candidate
        if intent == "info" and specific_candidate:
            # Only show the specific candidate's information
            candidate_shown = False
            
            for result in search_results:
                metadata = result.get('metadata', {})
                candidate_name = metadata.get('name', '').strip()
                
                # Check if this is the candidate we're looking for
                if self._is_target_candidate(candidate_name, specific_candidate):
                    similarity = round(result.get('similarity_score', 0) * 100, 1)
                    
                    candidate_info = f"""
                    CANDIDATE: {candidate_name}
                    
                    CONTACT INFORMATION:
                    - Email: {metadata.get('email', 'Not provided')}
                    - Phone: {metadata.get('phone', 'Not provided')}
                    - LinkedIn: {metadata.get('linkedin', 'Not provided')}
                    
                    PROFESSIONAL DETAILS:
                    - Field: {metadata.get('reco_field', 'General')}
                    - Experience Level: {metadata.get('cand_level', 'Unknown')}
                    - Years of Experience: {metadata.get('years_of_experience', 'Not specified')}
                    - Location: {metadata.get('city', '')}, {metadata.get('state', '')}, {metadata.get('country', '')}
                    - Resume File: {metadata.get('pdf_name', 'Unknown')}
                    - Database Match Score: {similarity}%
                    
                    SKILLS & EXPERTISE:
                    {metadata.get('skills', 'Not specified')}
                    
                    DETAILED WORK EXPERIENCE:
                    {metadata.get('work_experiences', 'No work experience details available')}
                    
                    EDUCATION BACKGROUND:
                    {self._extract_education_info(metadata)}
                    
                    ADDITIONAL PROFILE DATA:
                    {metadata.get('full_resume_data', 'No additional data available')}
                    """
                    context_parts.append(candidate_info.strip())
                    candidate_shown = True
                    break  # Only show the first match for the specific candidate
            
            if not candidate_shown:
                return f"Could not find specific information for candidate '{specific_candidate}' in the database. The search returned {len(search_results)} results, but none matched the requested candidate name exactly."
                
        elif intent == "info":
            # General info request without specific candidate - show top 3
            for i, result in enumerate(search_results[:3], 1):
                metadata = result.get('metadata', {})
                similarity = round(result.get('similarity_score', 0) * 100, 1)
                
                candidate_info = f"""
                Candidate {i}: {metadata.get('name', 'Unknown')}
                - Email: {metadata.get('email', 'Not provided')}
                - Field: {metadata.get('reco_field', 'General')}
                - Experience Level: {metadata.get('cand_level', 'Unknown')}
                - Location: {metadata.get('city', '')}, {metadata.get('state', '')}, {metadata.get('country', '')}
                - Skills: {metadata.get('skills', 'Not specified')}
                - Years of Experience: {metadata.get('years_of_experience', 'Not specified')}
                - Resume File: {metadata.get('pdf_name', 'Unknown')}
                - Match Score: {similarity}%
                
                DETAILED WORK EXPERIENCE:
                {metadata.get('work_experiences', 'No work experience details available')}
                
                EDUCATION BACKGROUND:
                {self._extract_education_info(metadata)}
                """
                context_parts.append(candidate_info.strip())
        else:
            # For search requests, provide summary information with key details
            for i, result in enumerate(search_results[:5], 1):
                metadata = result.get('metadata', {})
                similarity = round(result.get('similarity_score', 0) * 100, 1)
                
                # Extract first job for quick reference
                work_exp = metadata.get('work_experiences', '')
                first_job = "No work experience"
                if work_exp and work_exp != '':
                    first_job = work_exp.split(';')[0] if ';' in work_exp else work_exp[:150] + "..."
                
                candidate_info = f"""
                Candidate {i}: {metadata.get('name', 'Unknown')}
                - Email: {metadata.get('email', 'Not provided')}
                - Field: {metadata.get('reco_field', 'General')}
                - Experience Level: {metadata.get('cand_level', 'Unknown')}
                - Location: {metadata.get('city', '')}, {metadata.get('state', '')}
                - Years of Experience: {metadata.get('years_of_experience', 'Not specified')}
                - Recent/First Job: {first_job}
                - Key Skills: {str(metadata.get('skills', 'Not specified'))[:100]}...
                - Similarity Score: {similarity}%
                """
                context_parts.append(candidate_info.strip())
        
        return "\n\n".join(context_parts)
    
    def _generate_response(self, state: ChatState) -> Dict[str, Any]:
        """Generate final response using the response generation specialist"""
        
        last_message = state["messages"][-1].content if state["messages"] else ""
        context = state.get("context", "")
        search_results = state.get("search_results", [])
        user_intent = state.get("user_intent", "general")
        
        try:
            # Use response generation specialist
            response = self.response_generation_specialist.execute(
                user_message=last_message,
                intent=user_intent,
                context=context,
                search_results=search_results
            )
            
            # Add the response to messages
            new_messages = [AIMessage(content=response)]
            
            return {"messages": new_messages}
        
        except Exception as e:
            st.error(f"Response generation failed: {e}")
            error_response = "I apologize, but I'm having trouble processing your request right now. Please try again."
            return {"messages": [AIMessage(content=error_response)]}
    
    def chat(self, user_message: str) -> str:
        """Main chat interface"""
        
        if not self.graph:
            return "Chatbot is not properly initialized. Please check your configuration."
        
        try:
            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=user_message)],
                "context": "",
                "search_query": "",
                "search_results": [],
                "user_intent": "",
                "intent_confidence": 0.0
            }
            
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            
            # Extract the response
            ai_messages = [msg for msg in final_state["messages"] if isinstance(msg, AIMessage)]
            if ai_messages:
                response = ai_messages[-1].content
                
                # Store conversation history
                self.conversation_history.append({"user": user_message, "assistant": response})
                
                return response
            else:
                return "I'm sorry, I couldn't generate a proper response. Please try again."
        
        except Exception as e:
            st.error(f"Chat processing failed: {e}")
            return "I encountered an error while processing your request. Please try again."
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def is_available(self) -> bool:
        """Check if chatbot is available"""
        return (
            self.graph is not None and
            self.intent_specialist.is_available() and
            self.name_extraction_specialist.is_available() and
            self.query_enhancement_specialist.is_available() and
            self.response_generation_specialist.is_available()
        )
    
    def get_specialists_status(self) -> Dict[str, bool]:
        """Get the status of all specialists"""
        return {
            'intent_specialist': self.intent_specialist.is_available(),
            'name_extraction_specialist': self.name_extraction_specialist.is_available(),
            'query_enhancement_specialist': self.query_enhancement_specialist.is_available(),
            'response_generation_specialist': self.response_generation_specialist.is_available()
        }


# Global chatbot instance
candidate_chatbot = CandidateSearchChatbot() 