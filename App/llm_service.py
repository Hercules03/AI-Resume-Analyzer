"""
Centralized LLM service for handling all LLM interactions.
Supports both Ollama (local) and OpenAI API providers.
"""
import json
import re
import os
from typing import Type, Dict, Any, List
import streamlit as st
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
from config import LLM_CONFIG

# Try to import Ollama dependencies
try:
    from langchain_ollama import OllamaLLM
    from langchain.prompts import PromptTemplate
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Try to import OpenAI dependencies  
try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import PromptTemplate
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class LLMService:
    """Centralized service for LLM operations supporting both Ollama and OpenAI."""
    
    def __init__(self, provider: str = None, model_name: str = None, **kwargs):
        """
        Initialize the LLM service.
        
        Args:
            provider: 'ollama' or 'openai'
            model_name: Model name to use (optional, will use default from config)
            **kwargs: Additional provider-specific arguments
        """
        self.provider = provider or LLM_CONFIG['default_provider']
        self.llm = None
        self.connection_tested = False
        
        # Set model name based on provider
        if model_name:
            self.model_name = model_name
        else:
            self.model_name = LLM_CONFIG[self.provider]['default_model']
        
        # Store provider-specific config
        self.config = LLM_CONFIG[self.provider].copy()
        self.config.update(kwargs)
        
        # Initialize the appropriate LLM
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM connection based on provider."""
        if self.provider == 'ollama':
            return self._initialize_ollama()
        elif self.provider == 'openai':
            return self._initialize_openai()
        else:
            try:
                st.error(f"Unsupported provider: {self.provider}")
            except:
                print(f"Unsupported provider: {self.provider}")
            return False
    
    def _initialize_ollama(self):
        """Initialize Ollama LLM connection."""
        if not OLLAMA_AVAILABLE:
            try:
                st.error("Ollama not available. Please install: pip install langchain langchain-ollama")
            except:
                print("Ollama not available. Please install: pip install langchain langchain-ollama")
            return False
        
        try:
            self.llm = OllamaLLM(
                model=self.model_name,
                base_url=self.config['default_url'],
                temperature=self.config['temperature'],
                num_predict=self.config['num_predict'],
                num_ctx=self.config['num_ctx'],
                top_k=self.config['top_k'],
                top_p=self.config['top_p']
            )
            return True
                
        except Exception as e:
            try:
                st.error(f"Failed to initialize Ollama: {str(e)}")
            except:
                print(f"Failed to initialize Ollama: {str(e)}")
            return False
    
    def _initialize_openai(self):
        """Initialize OpenAI LLM connection."""
        if not OPENAI_AVAILABLE:
            try:
                st.error("OpenAI not available. Please install: pip install langchain-openai")
            except:
                print("OpenAI not available. Please install: pip install langchain-openai")
            return False
        
        try:
            # Get API key from config or environment variable
            api_key = self.config.get('api_key') or os.getenv('OPENAI_API_KEY')
            
            if not api_key:
                try:
                    st.error("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or configure it in config.py")
                except:
                    print("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or configure it in config.py")
                return False
            
            self.llm = ChatOpenAI(
                model=self.model_name,
                temperature=self.config['temperature'],
                max_tokens=self.config['max_tokens'],
                top_p=self.config['top_p'],
                api_key=api_key,
                timeout=self.config['timeout']
            )
            return True
                
        except Exception as e:
            try:
                st.error(f"Failed to initialize OpenAI: {str(e)}")
            except:
                print(f"Failed to initialize OpenAI: {str(e)}")
            return False
    
    def _test_connection(self):
        """Test LLM connection if not already tested."""
        if self.connection_tested or not self.llm:
            return self.llm is not None
        
        try:
            # Simple test with minimal prompt
            if self.provider == 'openai':
                # For OpenAI ChatModels, we need to use messages format
                from langchain.schema import HumanMessage
                test_response = self.llm.invoke([HumanMessage(content="Hi")])
                response_content = test_response.content if hasattr(test_response, 'content') else str(test_response)
            else:
                # For Ollama, use direct invoke
                test_response = self.llm.invoke("Hi")
                response_content = test_response
                
            if response_content:
                self.connection_tested = True
                return True
            else:
                try:
                    st.error(f"{self.provider.title()} connection test failed - no response")
                except:
                    print(f"{self.provider.title()} connection test failed - no response")
                return False
                
        except Exception as e:
            try:
                st.error(f"{self.provider.title()} connection test failed: {str(e)}")
            except:
                print(f"{self.provider.title()} connection test failed: {str(e)}")
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
                            "Provider": self.provider.title(),
                            "Model": self.model_name,
                            "Temperature": self.config['temperature'],
                            "Prompt Length": len(formatted_prompt),
                            "Input Variables": input_variables
                        }
                        
                        # Add provider-specific details
                        if self.provider == 'ollama':
                            config_details.update({
                                "Base URL": self.config['default_url'],
                                "Max Tokens (num_predict)": self.config['num_predict'],
                                "Top K": self.config['top_k'],
                                "Top P": self.config['top_p']
                            })
                        elif self.provider == 'openai':
                            config_details.update({
                                "Max Tokens": self.config['max_tokens'],
                                "Top P": self.config['top_p'],
                                "API Key": "***" if self.config.get('api_key') or os.getenv('OPENAI_API_KEY') else "Not Set"
                            })
                        
                        st.json(config_details)
                    
                    with st.expander(f"📝 LLM Prompt for {model.__name__}"):
                        st.code(formatted_prompt)
                except:
                    print(f"Debug info for {model.__name__}: Provider={self.provider}, Model={self.model_name}, Prompt Length={len(formatted_prompt)}")
            
            # Invoke LLM based on provider
            if self.provider == 'openai':
                # For OpenAI ChatModels, we need to use messages format
                from langchain.schema import HumanMessage
                llm_response = self.llm.invoke([HumanMessage(content=formatted_prompt)])
                response = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
            else:
                # For Ollama, use direct invoke
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
                            "Provider": self.provider.title(),
                            "Model": self.model_name,
                            "Temperature": self.config['temperature'],
                            "Prompt Length": len(prompt),
                            "Streaming": True
                        }
                        
                        # Add provider-specific details
                        if self.provider == 'ollama':
                            stream_config.update({
                                "Base URL": self.config['default_url'],
                                "Max Tokens": self.config['num_predict'],
                                "Top K": self.config['top_k'],
                                "Top P": self.config['top_p']
                            })
                        elif self.provider == 'openai':
                            stream_config.update({
                                "Max Tokens": self.config['max_tokens'],
                                "Top P": self.config['top_p']
                            })
                        
                        st.json(stream_config)
                    
                    with st.expander("📝 Streaming LLM Prompt"):
                        st.code(prompt)
                except:
                    print(f"Debug info: Provider={self.provider}, Model={self.model_name}, Prompt Length={len(prompt)}, Streaming=True")
            
            # Use stream method for streaming response
            if self.provider == 'openai':
                # For OpenAI ChatModels, use messages format for streaming
                from langchain.schema import HumanMessage
                for chunk in self.llm.stream([HumanMessage(content=prompt)]):
                    if hasattr(chunk, 'content') and chunk.content:
                        yield chunk.content
                    elif chunk:
                        yield str(chunk)
            else:
                # For Ollama, use direct streaming
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
                        "Provider": self.provider.title(),
                        "Model": self.model_name,
                        "Temperature": self.config['temperature'],
                        "Prompt Length": len(prompt)
                    }
                    
                    # Add provider-specific details
                    if self.provider == 'ollama':
                        simple_config.update({
                            "Base URL": self.config['default_url'],
                            "Max Tokens": self.config['num_predict'],
                            "Top K": self.config['top_k'],
                            "Top P": self.config['top_p']
                        })
                    elif self.provider == 'openai':
                        simple_config.update({
                            "Max Tokens": self.config['max_tokens'],
                            "Top P": self.config['top_p']
                        })
                    
                    st.json(simple_config)
                
                with st.expander("📝 Simple LLM Prompt"):
                    st.code(prompt)
            
            # Invoke LLM based on provider
            if self.provider == 'openai':
                # For OpenAI ChatModels, use messages format
                from langchain.schema import HumanMessage
                llm_response = self.llm.invoke([HumanMessage(content=prompt)])
                response = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
            else:
                # For Ollama, use direct invoke
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
    
    def update_provider(self, provider: str, model_name: str = None):
        """Update the provider and optionally the model."""
        self.provider = provider
        self.config = LLM_CONFIG[provider].copy()
        
        if model_name:
            self.model_name = model_name
        else:
            self.model_name = LLM_CONFIG[provider]['default_model']
        
        self.connection_tested = False  # Reset connection test
        self._initialize_llm()
    
    def get_available_models(self):
        """Get available models for the current provider."""
        if self.provider == 'ollama':
            # For Ollama, these are common models - you can extend this list
            return ['gemma3:27b', 'gemma3:12b', 'gemma3:4b', 'llama3.2:3b', 'llama3.2:1b', 'mistral:7b']
        elif self.provider == 'openai':
            # Common OpenAI models
            return ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo']
        return []


# Global LLM service instance
llm_service = LLMService() 