"""
RAG-powered Chatbot Service for Candidate Search using LangGraph and ChromaDB
"""
import streamlit as st
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
import json
import re
from database import db_manager
from config import LLM_CONFIG


class ChatState(TypedDict):
    """State for the chatbot conversation"""
    messages: Annotated[list, add_messages]
    context: str
    search_query: str
    search_results: List[Dict[str, Any]]
    user_intent: str


class CandidateSearchChatbot:
    """RAG-powered chatbot for candidate search using LangGraph"""
    
    def __init__(self):
        self.llm = None
        self.graph = None
        self.conversation_history = []
        self._initialize_llm()
        self._build_graph()
    
    def _initialize_llm(self):
        """Initialize the LLM for chatbot"""
        try:
            self.llm = ChatOllama(
                model=LLM_CONFIG['default_model'],
                base_url=LLM_CONFIG['default_url'],
                temperature=0.3,  # Slightly higher for more conversational responses
                num_predict=2048
            )
        except Exception as e:
            st.error(f"❌ Failed to initialize chatbot LLM: {e}")
    
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
        """Analyze user intent from their message"""
        
        last_message = state["messages"][-1].content if state["messages"] else ""
        
        intent_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an intent classifier for an HR candidate search system.
            Analyze the user's message and determine their intent:
            
            1. "search" - Finding candidates based on skills, experience, requirements
               Examples: "Find Python developers", "I need ML engineers", "Show me senior developers"
            
            2. "info" - Asking for specific information about candidates
               Examples: "What's John's email?", "Tell me about Sarah", "Contact details for Mike"
            
            3. "general" - General questions, greetings, help requests
               Examples: "Hello", "How does this work?", "What can you do?"
            
            Respond with only "search", "info", or "general".
            
            For "search" and "info" intents, also extract the search terms or candidate name."""),
            HumanMessage(content=last_message)
        ])
        
        try:
            response = self.llm.invoke(intent_prompt.format_messages())
            intent = response.content.strip().lower()
            
            # Extract search query for both search and info intents
            search_query = ""
            if intent in ["search", "info"]:
                search_query = last_message
            
            return {
                "user_intent": intent,
                "search_query": search_query
            }
        
        except Exception as e:
            st.error(f"Intent analysis failed: {e}")
            return {
                "user_intent": "general",
                "search_query": ""
            }
    
    def _route_based_on_intent(self, state: ChatState) -> str:
        """Route to appropriate node based on intent"""
        intent = state.get("user_intent", "general")
        return "search" if intent in ["search", "info"] else "general"
    
    def _search_candidates(self, state: ChatState) -> Dict[str, Any]:
        """Search for candidates using ChromaDB semantic search"""
        
        search_query = state.get("search_query", "")
        user_intent = state.get("user_intent", "search")
        
        if not search_query:
            return {"search_results": [], "context": "No search query provided."}
        
        try:
            # For info requests, search more broadly to find specific candidates
            if user_intent == "info":
                # Extract potential names from the query
                candidate_name = self._extract_candidate_name(search_query)
                if candidate_name:
                    search_results = db_manager.semantic_search_resumes(candidate_name, n_results=20)
                else:
                    search_results = db_manager.semantic_search_resumes(search_query, n_results=20)
            else:
                # Enhance the search query for better matching
                enhanced_query = self._enhance_search_query(search_query)
                search_results = db_manager.semantic_search_resumes(enhanced_query, n_results=10)
            
            # Create context from search results
            context = self._create_context_from_results(search_results, user_intent)
            
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
    
    def _extract_candidate_name(self, query: str) -> str:
        """Extract candidate name from info queries"""
        # Look for common patterns like "John's email", "contact for Sarah", "Tell me about Mike"
        patterns = [
            r"(?:email of|contact for|about|for)\s+([A-Za-z\s]+)",
            r"([A-Za-z]+(?:\s+[A-Za-z]+)*)'s?\s+(?:email|contact|info)",
            r"(?:who is|tell me about)\s+([A-Za-z\s]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up common words
                name = re.sub(r'\b(the|a|an|his|her|their)\b', '', name, flags=re.IGNORECASE).strip()
                if len(name) > 2:  # Ensure we have a meaningful name
                    return name
        
        return ""
    
    def _enhance_search_query(self, query: str) -> str:
        """Enhance search query for better semantic matching"""
        
        enhancement_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a search query enhancer for candidate recruitment.
            Take the user's natural language request and expand it into a comprehensive search query
            that will find relevant candidates. Include related skills, experience levels, and requirements.
            
            Example:
            Input: "Find me a Python developer"
            Output: "Python developer software engineer programming backend web development Flask Django API REST experience"
            
            Input: "I need someone for machine learning"
            Output: "machine learning data scientist AI artificial intelligence Python TensorFlow PyTorch deep learning neural networks data analysis statistics"
            
            Keep it concise but comprehensive."""),
            HumanMessage(content=f"Enhance this search query: {query}")
        ])
        
        try:
            response = self.llm.invoke(enhancement_prompt.format_messages())
            return response.content.strip()
        except:
            return query  # Fallback to original query
    
    def _create_context_from_results(self, search_results: List[Dict[str, Any]], intent: str = "search") -> str:
        """Create context string from search results for the LLM"""
        
        if not search_results:
            return "No candidates found matching the search criteria."
        
        context_parts = []
        
        # For info requests, provide more detailed information
        if intent == "info":
            for i, result in enumerate(search_results[:3], 1):  # Top 3 for info requests
                metadata = result.get('metadata', {})
                similarity = round(result.get('similarity_score', 0) * 100, 1)
                
                candidate_info = f"""
                Candidate {i}: {metadata.get('name', 'Unknown')}
                - Email: {metadata.get('email', 'Not provided')}
                - Field: {metadata.get('reco_field', 'General')}
                - Experience Level: {metadata.get('cand_level', 'Unknown')}
                - Resume Score: {metadata.get('resume_score', '0')}%
                - Location: {metadata.get('city', '')}, {metadata.get('state', '')}, {metadata.get('country', '')}
                - Skills: {metadata.get('skills', 'Not specified')}
                - Resume File: {metadata.get('pdf_name', 'Unknown')}
                - Match Score: {similarity}%
                - Full Profile Data Available: Yes
                """
                context_parts.append(candidate_info.strip())
        else:
            # For search requests, provide summary information
            for i, result in enumerate(search_results[:5], 1):  # Top 5 for searches
                metadata = result.get('metadata', {})
                similarity = round(result.get('similarity_score', 0) * 100, 1)
                
                candidate_info = f"""
                Candidate {i}: {metadata.get('name', 'Unknown')}
                - Email: {metadata.get('email', 'Not provided')}
                - Field: {metadata.get('reco_field', 'General')}
                - Experience Level: {metadata.get('cand_level', 'Unknown')}
                - Resume Score: {metadata.get('resume_score', '0')}%
                - Location: {metadata.get('city', '')}, {metadata.get('state', '')}
                - Key Skills: {str(metadata.get('skills', 'Not specified'))[:100]}...
                - Similarity Score: {similarity}%
                """
                context_parts.append(candidate_info.strip())
        
        return "\n\n".join(context_parts)
    
    def _generate_response(self, state: ChatState) -> Dict[str, Any]:
        """Generate final response using LLM with RAG context"""
        
        last_message = state["messages"][-1].content if state["messages"] else ""
        context = state.get("context", "")
        search_results = state.get("search_results", [])
        user_intent = state.get("user_intent", "general")
        
        # Create response prompt based on intent
        if user_intent == "search" and search_results:
            system_message = """You are an experienced HR assistant with direct access to the company's candidate database. 
            You have full access to all candidate information and can provide specific details when requested.
            
            Your role is to:
            1. Help find candidates based on skills, experience, and requirements
            2. Provide detailed candidate summaries with actionable insights
            3. Suggest the best matches and explain why they're good fits
            4. Give specific recommendations for next steps
            
            Be conversational, helpful, and provide all the information needed for HR decisions.
            Always include specific details like names, scores, and contact information when available."""
            
            user_message = f"""
            User request: {last_message}
            
            Search results from our candidate database:
            {context}
            
            Please provide a helpful summary of the candidates found, highlighting the best matches and their qualifications.
            Include specific names, scores, and key details that would help with the hiring decision.
            """
        
        elif user_intent == "info" and search_results:
            system_message = """You are an HR assistant with access to the complete candidate database.
            The user is asking for specific information about a candidate. Provide all available details 
            including contact information, skills, experience, and any other relevant data.
            
            Be direct and provide the specific information requested. If the user asks for an email 
            or contact details, provide them from the database. This is an internal HR system."""
            
            user_message = f"""
            User request: {last_message}
            
            Candidate information from database:
            {context}
            
            Please provide the specific information requested about the candidate(s). 
            If they're asking for contact details, provide the email address and any other relevant contact information.
            """
        
        else:
            system_message = """You are a helpful AI HR assistant for an internal candidate search system.
            You have access to the company's resume database and can help HR professionals find and evaluate candidates.
            
            Explain your capabilities:
            - Search for candidates by skills, experience, location, field
            - Provide detailed candidate information including contact details
            - Help with candidate evaluation and matching
            - Answer questions about specific candidates in the database
            
            Be friendly, professional, and helpful. Guide users on how to make the most of the system."""
            
            user_message = last_message
        
        response_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessage(content=user_message)
        ])
        
        try:
            # Prepare chat history (last 6 messages for context)
            chat_history = state.get("messages", [])[-6:]
            
            response = self.llm.invoke(response_prompt.format_messages(chat_history=chat_history))
            
            # Add the response to messages
            new_messages = [AIMessage(content=response.content)]
            
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
                "user_intent": ""
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
        return self.llm is not None and self.graph is not None


# Global chatbot instance
candidate_chatbot = CandidateSearchChatbot() 