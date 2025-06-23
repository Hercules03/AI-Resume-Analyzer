"""
Centralized LLM service for handling all LLM interactions.
"""
import json
import re
from typing import Type, Dict, Any, List
import streamlit as st
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
from config import LLM_CONFIG

try:
    from langchain_ollama import OllamaLLM
    from langchain.prompts import PromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class LLMService:
    """Centralized service for LLM operations."""
    
    def __init__(self, model_name: str = None, base_url: str = None):
        """Initialize the LLM service."""
        self.model_name = model_name or LLM_CONFIG['default_model']
        self.base_url = base_url or LLM_CONFIG['default_url']
        self.llm = None
        self.connection_tested = False
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the Ollama LLM connection."""
        if not LANGCHAIN_AVAILABLE:
            st.error("❌ LangChain not available. Please install: pip install langchain langchain-ollama")
            return False
        
        try:
            self.llm = OllamaLLM(
                model=self.model_name,
                base_url=self.base_url,
                temperature=LLM_CONFIG['temperature'],
                num_predict=LLM_CONFIG['num_predict'],
                top_k=LLM_CONFIG['top_k'],
                top_p=LLM_CONFIG['top_p']
            )
            
            # Don't test connection immediately - do it lazily when first used
            return True
                
        except Exception as e:
            st.error(f"❌ Failed to initialize LLM: {str(e)}")
            st.info("""
            **Troubleshooting:**
            1. Make sure Ollama is running: `ollama serve`
            2. Pull the model: `ollama pull gemma2:27b`
            3. Check if the model name is correct
            4. Verify Ollama is accessible at the configured URL
            """)
            return False
    
    def _test_connection(self):
        """Test LLM connection if not already tested."""
        if self.connection_tested or not self.llm:
            return self.llm is not None
        
        try:
            # Simple test with minimal prompt
            test_response = self.llm.invoke("Hi")
            if test_response:
                st.success(f"✅ LLM Connection established: {self.model_name}")
                self.connection_tested = True
                return True
            else:
                st.error("❌ LLM connection test failed - no response")
                return False
                
        except Exception as e:
            st.error(f"❌ LLM connection test failed: {str(e)}")
            st.info("""
            **Troubleshooting for Ollama:**
            1. Make sure Ollama is running: `ollama serve`
            2. Check available models: `ollama list`
            3. Pull the model if needed: `ollama pull gemma2:27b`
            4. Verify the model name matches what you have installed
            """)
            return False
    
    def extract_with_llm(
        self,
        model: Type[BaseModel],
        prompt_template: str,
        input_variables: List[str],
        input_data: Dict[str, Any],
        development_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Extract structured data using LLM with Pydantic model validation.
        
        Args:
            model: Pydantic model class for output validation
            prompt_template: Template string for the prompt
            input_variables: List of variable names expected in the template
            input_data: Dictionary containing values for the input variables
            development_mode: Whether to show detailed extraction process
            
        Returns:
            Dictionary containing the extracted and validated data
        """
        if not self.llm:
            if development_mode:
                st.error("❌ LLM not initialized")
            return {model.__name__.lower(): model().model_dump()}
        
        # Test connection if not already done
        if not self._test_connection():
            if development_mode:
                st.error("❌ LLM connection failed")
            return {model.__name__.lower(): model().model_dump()}
        
        try:
            # Create parser for the model
            parser = PydanticOutputParser(pydantic_object=model)
            
            # Create prompt template
            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=input_variables + ["format_instructions"],
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )
            
            # Format the prompt with input data
            formatted_prompt = prompt.format(**input_data)
            
            if development_mode:
                with st.expander(f"🔍 LLM Prompt for {model.__name__}"):
                    st.code(formatted_prompt)
            
            # Get response from LLM with timeout handling
            if development_mode:
                st.info(f"🤖 Requesting {model.__name__} from {self.model_name}...")
            
            response = self.llm.invoke(formatted_prompt)
            
            if development_mode:
                with st.expander(f"🔍 Raw LLM Response for {model.__name__}"):
                    st.code(response)
            
            # Try to parse with Pydantic parser first
            try:
                parsed_output = parser.parse(response)
                if development_mode:
                    st.success(f"✅ Successfully parsed {model.__name__} with Pydantic")
                return {model.__name__.lower(): parsed_output.model_dump()}
            except Exception as parse_error:
                if development_mode:
                    st.warning(f"⚠️ Pydantic parsing failed for {model.__name__}: {parse_error}")
                    st.info("🔧 Attempting manual JSON parsing...")
                
                # Fallback to manual JSON parsing
                cleaned_response = self._clean_json_response(response)
                json_output = json.loads(cleaned_response)
                
                # Validate with the model
                validated_output = model(**json_output)
                if development_mode:
                    st.success(f"✅ Successfully parsed {model.__name__} with manual JSON parsing")
                return {model.__name__.lower(): validated_output.model_dump()}
                
        except Exception as e:
            if development_mode:
                st.error(f"❌ LLM extraction failed for {model.__name__}: {str(e)}")
                st.exception(e)
            return {model.__name__.lower(): model().model_dump()}
    
    def extract_simple(
        self,
        prompt: str,
        development_mode: bool = False
    ) -> str:
        """
        Simple text extraction without structured parsing.
        
        Args:
            prompt: The prompt to send to the LLM
            development_mode: Whether to show detailed process
            
        Returns:
            Raw text response from LLM
        """
        if not self.llm:
            if development_mode:
                st.error("❌ LLM not initialized")
            return ""
        
        # Test connection if not already done
        if not self._test_connection():
            if development_mode:
                st.error("❌ LLM connection failed")
            return ""
        
        try:
            if development_mode:
                with st.expander("🔍 Simple LLM Prompt"):
                    st.code(prompt)
            
            response = self.llm.invoke(prompt)
            
            if development_mode:
                with st.expander("🔍 Simple LLM Response"):
                    st.code(response)
            
            return response
            
        except Exception as e:
            if development_mode:
                st.error(f"❌ Simple LLM extraction failed: {str(e)}")
            return ""
    
    def _clean_json_response(self, response: str) -> str:
        """Clean LLM response to extract valid JSON."""
        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        # Remove any text before the first { or [
        start_char = min(
            (response.find('{') if response.find('{') != -1 else len(response)),
            (response.find('[') if response.find('[') != -1 else len(response))
        )
        
        if start_char < len(response):
            response = response[start_char:]
        
        # Find the last } or ]
        last_brace = response.rfind('}')
        last_bracket = response.rfind(']')
        end_char = max(last_brace, last_bracket)
        
        if end_char != -1:
            response = response[:end_char + 1]
        
        return response.strip()
    
    def is_available(self) -> bool:
        """Check if LLM service is available."""
        return self.llm is not None and self._test_connection()
    
    def update_model(self, model_name: str):
        """Update the model being used."""
        self.model_name = model_name
        self.connection_tested = False  # Reset connection test
        self._initialize_llm()


# Global LLM service instance
llm_service = LLMService() 