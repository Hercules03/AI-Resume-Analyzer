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
            try:
                st.error("LangChain not available. Please install: pip install langchain langchain-ollama")
            except:
                print("LangChain not available. Please install: pip install langchain langchain-ollama")
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
            try:
                st.error(f"Failed to initialize LLM: {str(e)}")
            except:
                print(f"Failed to initialize LLM: {str(e)}")
            return False
    
    def _test_connection(self):
        """Test LLM connection if not already tested."""
        if self.connection_tested or not self.llm:
            return self.llm is not None
        
        try:
            # Simple test with minimal prompt
            test_response = self.llm.invoke("Hi")
            if test_response:
                self.connection_tested = True
                return True
            else:
                try:
                    st.error("LLM connection test failed - no response")
                except:
                    print("LLM connection test failed - no response")
                return False
                
        except Exception as e:
            try:
                st.error(f"LLM connection test failed: {str(e)}")
            except:
                print(f"LLM connection test failed: {str(e)}")
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
                try:
                    st.error("LLM not initialized")
                except:
                    print("LLM not initialized")
            return {model.__name__.lower(): model().model_dump()}
        
        # Test connection if not already done
        if not self._test_connection():
            if development_mode:
                try:
                    st.error("LLM connection failed")
                except:
                    print("LLM connection failed")
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
                try:
                    with st.expander(f"🔧 LLM Configuration for {model.__name__}"):
                        config_details = {
                            "Extractor": model.__name__,
                            "Model": self.model_name,
                            "Base URL": self.base_url,
                            "Temperature": self.llm.temperature,
                            "Max Tokens (num_predict)": self.llm.num_predict,
                            "Top K": self.llm.top_k,
                            "Top P": self.llm.top_p,
                            "Prompt Length": len(formatted_prompt),
                            "Input Variables": input_variables
                        }
                        st.json(config_details)
                    
                    with st.expander(f"📝 LLM Prompt for {model.__name__}"):
                        st.code(formatted_prompt)
                except:
                    print(f"Debug info for {model.__name__}: Model={self.model_name}, Prompt Length={len(formatted_prompt)}")
            
            
            response = self.llm.invoke(formatted_prompt)
            
            if development_mode:
                try:
                    with st.expander(f"📤 Raw LLM Response for {model.__name__}"):
                        response_info = {
                            "Response Length": len(response),
                            "Response Type": type(response).__name__,
                            "Has JSON Content": "{" in response and "}" in response
                        }
                        st.json(response_info)
                        st.code(response)
                except:
                    print(f"LLM Response for {model.__name__}: Length={len(response)}, Type={type(response).__name__}")
            
            # Try to parse with Pydantic parser first
            try:
                parsed_output = parser.parse(response)
                if development_mode:
                    try:
                        st.success(f"Successfully parsed {model.__name__} with Pydantic")
                    except:
                        print(f"Successfully parsed {model.__name__} with Pydantic")
                return {model.__name__.lower(): parsed_output.model_dump()}
            except Exception as parse_error:
                if development_mode:
                    try:
                        st.warning(f"Pydantic parsing failed for {model.__name__}: {parse_error}")
                    except:
                        print(f"Pydantic parsing failed for {model.__name__}: {parse_error}")
                
                # Fallback to manual JSON parsing
                cleaned_response = self._clean_json_response(response)
                json_output = json.loads(cleaned_response)
                
                # Validate with the model
                validated_output = model(**json_output)
                if development_mode:
                    try:
                        st.success(f"Successfully parsed {model.__name__} with manual JSON parsing")
                    except:
                        print(f"Successfully parsed {model.__name__} with manual JSON parsing")
                return {model.__name__.lower(): validated_output.model_dump()}
                
        except Exception as e:
            if development_mode:
                try:
                    st.error(f"LLM extraction failed for {model.__name__}: {str(e)}")
                    st.exception(e)
                except:
                    print(f"LLM extraction failed for {model.__name__}: {str(e)}")
            return {model.__name__.lower(): model().model_dump()}
    
    def stream_simple(
        self,
        prompt: str,
        development_mode: bool = False
    ):
        """
        Stream text response from LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            development_mode: Whether to show detailed process
            
        Yields:
            Text chunks as they are generated
        """
        if not self.llm:
            if development_mode:
                try:
                    st.error("LLM not initialized")
                except:
                    print("LLM not initialized")
            yield ""
            return
        
        # Test connection if not already done
        if not self._test_connection():
            if development_mode:
                try:
                    st.error("LLM connection failed")
                except:
                    print("LLM connection failed")
            yield ""
            return
        
        try:
            if development_mode:
                try:
                    with st.expander("🔧 Streaming LLM Configuration"):
                        stream_config = {
                            "Model": self.model_name,
                            "Base URL": self.base_url,
                            "Temperature": self.llm.temperature,
                            "Max Tokens": self.llm.num_predict,
                            "Top K": self.llm.top_k,
                            "Top P": self.llm.top_p,
                            "Prompt Length": len(prompt),
                            "Streaming": True
                        }
                        st.json(stream_config)
                    
                    with st.expander("📝 Streaming LLM Prompt"):
                        st.code(prompt)
                except:
                    print(f"Debug info: Model={self.model_name}, Prompt Length={len(prompt)}, Streaming=True")
            
            # Use stream method for streaming response
            for chunk in self.llm.stream(prompt):
                if chunk:
                    yield chunk
            
        except Exception as e:
            if development_mode:
                try:
                    st.error(f"Streaming LLM failed: {str(e)}")
                except:
                    print(f"Streaming LLM failed: {str(e)}")
            yield ""

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
                try:
                    st.error("LLM not initialized")
                except:
                    print("LLM not initialized")
            return ""
        
        # Test connection if not already done
        if not self._test_connection():
            if development_mode:
                try:
                    st.error("LLM connection failed")
                except:
                    print("LLM connection failed")
            return ""
        
        try:
            if development_mode:
                with st.expander("🔧 Simple LLM Configuration"):
                    simple_config = {
                        "Model": self.model_name,
                        "Base URL": self.base_url,
                        "Temperature": self.llm.temperature,
                        "Max Tokens": self.llm.num_predict,
                        "Top K": self.llm.top_k,
                        "Top P": self.llm.top_p,
                        "Prompt Length": len(prompt)
                    }
                    st.json(simple_config)
                
                with st.expander("📝 Simple LLM Prompt"):
                    st.code(prompt)
            
            response = self.llm.invoke(prompt)
            
            if development_mode:
                with st.expander("📤 Simple LLM Response"):
                    response_info = {
                        "Response Length": len(response),
                        "Response Type": type(response).__name__
                    }
                    st.json(response_info)
                    st.code(response)
            
            return response
            
        except Exception as e:
            if development_mode:
                try:
                    st.error(f"Simple LLM extraction failed: {str(e)}")
                except:
                    print(f"Simple LLM extraction failed: {str(e)}")
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