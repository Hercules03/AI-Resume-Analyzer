"""
RAG-powered Chatbot Service for Candidate Search using LangGraph and Specialists
"""
import streamlit as st
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
import asyncio
import sys
import os

# Add the project root to the Python path to import the sfc_search function
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db_manager
from config import LLM_CONFIG, SPECIALISTS_CONFIG
from db_specialists import (
    IntentSpecialist,
    NameExtractionSpecialist, 
    QueryEnhancementSpecialist,
    SearchResponseSpecialist,
    InfoResponseSpecialist,
    GeneralResponseSpecialist,
    SFCLicenseCheckSpecialist,
    SFCWebAutomationService,
)


# Note: SFC search functionality is now handled by SFCWebAutomationService


class ChatState(TypedDict):
    """State for the chatbot conversation"""
    messages: Annotated[list, add_messages]
    context: str
    search_query: str
    search_results: List[Dict[str, Any]]
    user_intent: str
    intent_confidence: float
    sfc_candidate_name: str
    sfc_check_results: Dict[str, Any]


class CandidateSearchChatbot:
    """RAG-powered chatbot for candidate search using specialized LLM functions"""
    
    def __init__(self):
        self.graph = None
        self.conversation_history = []
        
        # Initialize existing specialists
        self.intent_specialist = IntentSpecialist(SPECIALISTS_CONFIG['intent_analysis'])
        self.name_extraction_specialist = NameExtractionSpecialist(SPECIALISTS_CONFIG['name_extraction'])
        self.query_enhancement_specialist = QueryEnhancementSpecialist(SPECIALISTS_CONFIG['query_enhancement'])
        
        # Initialize response specialists
        self.search_response_specialist = SearchResponseSpecialist(SPECIALISTS_CONFIG['search_response'])
        self.info_response_specialist = InfoResponseSpecialist(SPECIALISTS_CONFIG['info_response'])
        self.general_response_specialist = GeneralResponseSpecialist(SPECIALISTS_CONFIG['general_response'])
        
        # Initialize SFC license checking specialists
        self.sfc_license_check_specialist = SFCLicenseCheckSpecialist(SPECIALISTS_CONFIG['response_generation'])  # Reuse config
        self.sfc_web_automation_service = SFCWebAutomationService()
        
        self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph workflow for RAG-powered conversation with SFC checking"""
        
        # Define the workflow
        workflow = StateGraph(ChatState)
        
        # Add nodes
        workflow.add_node("analyze_intent", self._analyze_intent)
        workflow.add_node("search_candidates", self._search_candidates)
        workflow.add_node("check_sfc_license", self._check_sfc_license)
        workflow.add_node("generate_search_response", self._generate_search_response)
        workflow.add_node("generate_info_response", self._generate_info_response)
        workflow.add_node("generate_sfc_response", self._generate_sfc_response)
        workflow.add_node("generate_general_response", self._generate_general_response)
        
        # Define edges
        workflow.add_edge(START, "analyze_intent")
        workflow.add_conditional_edges(
            "analyze_intent",
            self._route_based_on_intent,
            {
                "search": "search_candidates",
                "info": "search_candidates",  # Also search for specific info requests
                "sfc_license": "check_sfc_license",  # Route to SFC license checking
                "general": "generate_general_response"
            }
        )
        workflow.add_conditional_edges(
            "search_candidates",
            self._route_to_response_specialist,
            {
                "search": "generate_search_response",
                "info": "generate_info_response"
            }
        )
        workflow.add_edge("check_sfc_license", "generate_sfc_response")  # SFC flow
        workflow.add_edge("generate_search_response", END)
        workflow.add_edge("generate_info_response", END)
        workflow.add_edge("generate_sfc_response", END)  # SFC end
        workflow.add_edge("generate_general_response", END)
        
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
        
        if intent == "sfc_license":
            return "sfc_license"
        elif intent in ["search", "info"]:
            return "search"
        else:
            return "general"
    
    def _route_to_response_specialist(self, state: ChatState) -> str:
        """Route to appropriate response specialist after search"""
        intent = state.get("user_intent", "search")
        return intent  # Returns "search" or "info"
    
    def _check_sfc_license(self, state: ChatState) -> Dict[str, Any]:
        """Check SFC license status for a candidate using SFCWebAutomationService"""
        
        last_message = state["messages"][-1].content if state["messages"] else ""
        
        try:
            # Step 1: Extract candidate name from the user message using NameExtractionSpecialist
            candidate_name = self.name_extraction_specialist.execute(query=last_message)

            
            if not candidate_name:
                return {
                    "sfc_candidate_name": "",
                    "sfc_check_results": {
                        "success": False,
                        "error": "Could not extract candidate name from your message",
                        "candidate_name": "",
                        "search_url": "https://apps.sfc.hk/publicregWeb/searchByName"
                    }
                }
            
            # Step 2: Use SFCWebAutomationService to perform the license check
            try:
                check_results = self.sfc_web_automation_service.check_sfc_license(candidate_name)
                
                # Display SFC search results
                if check_results.get("success", False):
                    sfo_status = check_results.get("sfo_license", "Unknown")
                    amlo_status = check_results.get("amlo_license", "Unknown")

                    
                    # Show raw output if available (for debugging)
                    if check_results.get("raw_output"):
                        with st.expander("🔧 Raw SFC Search Output (Debug)"):
                            st.code(check_results["raw_output"], language="text")
                else:
                    error_msg = check_results.get("error", "Unknown error")
                
                return {
                    "sfc_candidate_name": candidate_name,
                    "sfc_check_results": check_results
                }
                
            except Exception as e:
                st.error(f"🔍 **SFC Search Exception:** {str(e)}")
                return {
                    "sfc_candidate_name": candidate_name,
                    "sfc_check_results": {
                        "success": False,
                        "error": f"SFC license check failed: {str(e)}",
                        "candidate_name": candidate_name,
                        "search_url": "https://apps.sfc.hk/publicregWeb/searchByName"
                    }
                }
        
        except Exception as e:
            st.error(f"SFC license checking failed: {e}")
            return {
                "sfc_candidate_name": "",
                "sfc_check_results": {
                    "success": False,
                    "error": "Technical error during SFC license check",
                    "candidate_name": "",
                    "search_url": "https://apps.sfc.hk/publicregWeb/searchByName"
                }
            }
    
    def _generate_sfc_response(self, state: ChatState) -> Dict[str, Any]:
        """Generate response for SFC license queries using SFCLicenseCheckSpecialist"""
        
        candidate_name = state.get("sfc_candidate_name", "")
        check_results = state.get("sfc_check_results", {})
        
        try:
            # Display response generation step
            st.info("💬 **Response Generation:** Using SFCLicenseCheckSpecialist to generate user response...")
            
            # Step 3: Use SFCLicenseCheckSpecialist to generate the user response
            response = self.sfc_license_check_specialist.execute(
                check_results=check_results,
                candidate_name=candidate_name
            )
            
            
            # Add the response to messages
            new_messages = [AIMessage(content=response)]
            
            return {"messages": new_messages}
            
        except Exception as e:
            st.error(f"💬 **Response Generation Failed:** {e}")
            # Fallback response
            error_response = self.sfc_license_check_specialist._get_fallback_output(
                candidate_name=candidate_name
            )
            return {"messages": [AIMessage(content=error_response)]}
    
    def _search_candidates(self, state: ChatState) -> Dict[str, Any]:
        """Search for candidates using ChromaDB semantic search"""
        
        # Use the raw user message if no search_query is available
        search_query = state.get("search_query", "")
        if not search_query:
            search_query = state["messages"][-1].content if state["messages"] else ""
        
        user_intent = state.get("user_intent", "search")
        
        if not search_query:
            return {"search_results": [], "context": "No search query provided."}
        
        try:
            # Simple search logic
            if user_intent == "info":
                # Extract candidate name for specific info requests
                candidate_name = self.name_extraction_specialist.execute(query=search_query)
                
                if candidate_name:
                    # Search for specific candidate
                    search_results = db_manager.semantic_search_resumes(candidate_name, n_results=10)
                    # Simple name filtering
                    search_results = self._filter_by_name(search_results, candidate_name)
                else:
                    # General info search
                    search_results = db_manager.semantic_search_resumes(search_query, n_results=5)
            else:
                # Regular search
                enhanced_query = self.query_enhancement_specialist.execute(query=search_query)
                search_results = db_manager.semantic_search_resumes(enhanced_query, n_results=5)
            
            # Create simple context
            context = self._create_simple_context(search_results, user_intent)
            
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
    
    def _filter_by_name(self, search_results: List[Dict[str, Any]], target_name: str) -> List[Dict[str, Any]]:
        """Simple name filtering"""
        if not target_name or not search_results:
            return search_results
        
        target_lower = target_name.lower()
        filtered = []
        
        for result in search_results:
            metadata = result.get('metadata', {})
            candidate_name = metadata.get('name', '').lower()
            
            # Simple check: if target name parts are in candidate name
            if target_lower in candidate_name or any(part in candidate_name for part in target_lower.split()):
                filtered.append(result)
        
        return filtered if filtered else search_results[:3]  # Return top 3 if no matches
    
    def _get_candidate_info(self, metadata: Dict[str, Any]) -> str:
        """Get candidate information from metadata - SIMPLIFIED"""
        
        # Priority 1: Try raw resume text first (if we implement it)
        raw_text = metadata.get('raw_resume_text', '')
        if raw_text and raw_text != 'Not available':
            return f"Resume Content:\n{raw_text[:2000]}..."  # First 2000 chars
        
        # Priority 2: Try structured fields
        info_parts = []
        
        # Basic info
        info_parts.append(f"Name: {metadata.get('name', 'Unknown')}")
        info_parts.append(f"Email: {metadata.get('email', 'Not provided')}")
        info_parts.append(f"Field: {metadata.get('reco_field', 'General')}")
        info_parts.append(f"Level: {metadata.get('cand_level', 'Unknown')}")
        info_parts.append(f"Experience: {metadata.get('years_of_experience', 'Not specified')}")
        
        # Skills
        skills = metadata.get('skills', '')
        if skills:
            info_parts.append(f"Skills: {skills}")
        
        # Work experience
        work_exp = metadata.get('work_experiences', '')
        if work_exp:
            info_parts.append(f"Work Experience: {work_exp[:500]}...")
        
        # Education - SIMPLIFIED
        education = metadata.get('educations', '')
        if education:
            info_parts.append(f"Education: {education}")
        else:
            # Simple fallback
            info_parts.append("Education: Not detailed in database")
        
        return "\n".join(info_parts)
    
    def _create_simple_context(self, search_results: List[Dict[str, Any]], intent: str = "search") -> str:
        """Create simple context from search results - MUCH SIMPLIFIED"""
        
        if not search_results:
            return "No candidates found matching the search criteria."
        
        context_parts = []
        
        # Simple logic: show detailed info for info requests, summary for search
        if intent == "info":
            # Show detailed info for first few candidates
            for i, result in enumerate(search_results[:2], 1):
                metadata = result.get('metadata', {})
                                
                candidate_info = f"""
{self._get_candidate_info(metadata)}
                """.strip()
                context_parts.append(candidate_info)
        else:
            # Show summary for search results
            for i, result in enumerate(search_results[:3], 1):
                metadata = result.get('metadata', {})
                similarity = round(result.get('similarity_score', 0) * 100, 1)
                
                summary = f"""
Candidate {i}: {metadata.get('name', 'Unknown')} 
- Field: {metadata.get('reco_field', 'General')}
- Level: {metadata.get('cand_level', 'Unknown')}
- Experience: {metadata.get('years_of_experience', 'Not specified')}
                """.strip()
                context_parts.append(summary)
        
        return "\n\n".join(context_parts)
    
    def _generate_search_response(self, state: ChatState) -> Dict[str, Any]:
        """Generate response for search queries using the search response specialist"""
        
        last_message = state["messages"][-1].content if state["messages"] else ""
        context = state.get("context", "")
        search_results = state.get("search_results", [])
        
        try:
            # Use search response specialist
            response = self.search_response_specialist.execute(
                user_message=last_message,
                context=context,
                search_results=search_results
            )
            
            # Add the response to messages
            new_messages = [AIMessage(content=response)]
            
            return {"messages": new_messages}
        
        except Exception as e:
            st.error(f"Search response generation failed: {e}")
            error_response = "I apologize, but I'm having trouble processing your candidate search right now. Please try again."
            return {"messages": [AIMessage(content=error_response)]}
    
    def _generate_info_response(self, state: ChatState) -> Dict[str, Any]:
        """Generate response for info queries using the info response specialist"""
        
        last_message = state["messages"][-1].content if state["messages"] else ""
        context = state.get("context", "")
        
        try:
            # Use info response specialist
            response = self.info_response_specialist.execute(
                user_message=last_message,
                context=context
            )
            
            # Add the response to messages
            new_messages = [AIMessage(content=response)]
            
            return {"messages": new_messages}
        
        except Exception as e:
            st.error(f"Info response generation failed: {e}")
            error_response = "I'm unable to retrieve the specific candidate information you requested at the moment. Please try again."
            return {"messages": [AIMessage(content=error_response)]}
    
    def _generate_general_response(self, state: ChatState) -> Dict[str, Any]:
        """Generate response for general queries using the general response specialist"""
        
        last_message = state["messages"][-1].content if state["messages"] else ""
        
        try:
            # Use general response specialist
            response = self.general_response_specialist.execute(
                user_message=last_message
            )
            
            # Add the response to messages
            new_messages = [AIMessage(content=response)]
            
            return {"messages": new_messages}
        
        except Exception as e:
            st.error(f"General response generation failed: {e}")
            error_response = "Hello! I'm your AI HR assistant. I can help you find candidates and answer questions about the resume database. How can I assist you today?"
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

    def chat_stream(self, user_message: str):
        """Main chat interface with streaming"""
        
        if not self.graph:
            yield "Chatbot is not properly initialized. Please check your configuration."
            return
        
        response_chunks = []
        
        try:
            # Analyze intent first
            intent_result = self.intent_specialist.execute(message=user_message)
            user_intent = intent_result.get('intent', 'general')
            
            # Display intent information in Streamlit
            st.info(f"🔍 **Intent Analysis:** {user_intent} (confidence: {intent_result.get('confidence', 0):.1%})")
            
            # Handle SFC license intent using the proper workflow
            if user_intent == "sfc_license":
                # Use the LangGraph workflow for SFC license checking
                initial_state = {
                    "messages": [HumanMessage(content=user_message)],
                    "context": "",
                    "search_query": "",
                    "search_results": [],
                    "user_intent": "",
                    "intent_confidence": 0.0
                }
                
                final_state = self.graph.invoke(initial_state)
                ai_messages = [msg for msg in final_state["messages"] if isinstance(msg, AIMessage)]
                if ai_messages:
                    complete_response = ai_messages[-1].content
                    self.conversation_history.append({"user": user_message, "assistant": complete_response})
                    yield complete_response
                    return
                else:
                    yield "I'm sorry, I couldn't process your SFC license request properly."
                    return
            
            # Search candidates if needed for other intents
            search_results = []
            context = ""
            
            if user_intent in ["search", "info"]:
                # Search for candidates
                search_results = self._search_candidates_simple(user_message, user_intent)
                context = self._create_simple_context(search_results, user_intent)
            
            # Stream the appropriate response
            if user_intent == "search":
                for chunk in self.search_response_specialist.stream(
                    user_message=user_message,
                    context=context,
                    search_results=search_results
                ):
                    response_chunks.append(chunk)
                    yield chunk
            elif user_intent == "info":
                for chunk in self.info_response_specialist.stream(
                    user_message=user_message,
                    context=context
                ):
                    response_chunks.append(chunk)
                    yield chunk
            else:
                for chunk in self.general_response_specialist.stream(
                    user_message=user_message
                ):
                    response_chunks.append(chunk)
                    yield chunk
            
            # Store complete conversation history after streaming
            complete_response = "".join(response_chunks)
            self.conversation_history.append({"user": user_message, "assistant": complete_response})
            
        except Exception as e:
            st.error(f"Chat streaming failed: {e}")
            error_msg = "I encountered an error while processing your request. Please try again."
            self.conversation_history.append({"user": user_message, "assistant": error_msg})
            yield error_msg

    def _search_candidates_simple(self, user_message: str, user_intent: str):
        """Simplified candidate search for streaming"""
        try:
            if user_intent == "info":
                # Extract candidate name for specific info requests
                candidate_name = self.name_extraction_specialist.execute(query=user_message)
                
                if candidate_name:
                    # Search for specific candidate
                    search_results = db_manager.semantic_search_resumes(candidate_name, n_results=10)
                    # Simple name filtering
                    search_results = self._filter_by_name(search_results, candidate_name)
                else:
                    # General info search
                    search_results = db_manager.semantic_search_resumes(user_message, n_results=5)
            else:
                # Regular search
                enhanced_query = self.query_enhancement_specialist.execute(query=user_message)
                search_results = db_manager.semantic_search_resumes(enhanced_query, n_results=5)
            
            return search_results
        
        except Exception as e:
            st.error(f"Candidate search failed: {e}")
            return []
    
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
            self.search_response_specialist.is_available() and
            self.info_response_specialist.is_available() and
            self.general_response_specialist.is_available()
        )
    
    def get_specialists_status(self) -> Dict[str, bool]:
        """Get the status of all specialists"""
        return {
            'intent_specialist': self.intent_specialist.is_available(),
            'name_extraction_specialist': self.name_extraction_specialist.is_available(),
            'query_enhancement_specialist': self.query_enhancement_specialist.is_available(),
            'search_response_specialist': self.search_response_specialist.is_available(),
            'info_response_specialist': self.info_response_specialist.is_available(),
            'general_response_specialist': self.general_response_specialist.is_available()
        }


# Global chatbot instance
candidate_chatbot = CandidateSearchChatbot() 