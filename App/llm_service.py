"""
Enhanced LLM service with robust error handling and response processing.
"""
import json
import re
from typing import Type, Dict, Any, List, Optional
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
    """Enhanced centralized service for LLM operations with robust error handling."""
    
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
            st.error("LangChain not available. Please install: pip install langchain langchain-ollama")
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
            return True
                
        except Exception as e:
            st.error(f"Failed to initialize LLM: {str(e)}")
            return False
    
    def _test_connection(self):
        """Test LLM connection if not already tested."""
        if self.connection_tested or not self.llm:
            return self.llm is not None
        
        try:
            # Simple test with minimal prompt
            test_response = self.llm.invoke("Hi")
            if test_response and test_response.strip():
                self.connection_tested = True
                return True
            else:
                st.error("LLM connection test failed - no response")
                return False
                
        except Exception as e:
            st.error(f"LLM connection test failed: {str(e)}")
            return False
    
    def extract_with_llm_config(
        self,
        model: Type[BaseModel],
        prompt_template: str,
        input_variables: List[str],
        input_data: Dict[str, Any],
        config: Dict[str, Any],
        development_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Extract structured data using LLM with specific configuration.
        Enhanced with robust error handling and response validation.
        """
        model_key = model.__name__.lower()
        
        if not LANGCHAIN_AVAILABLE:
            if development_mode:
                st.error("LangChain not available")
            return {model_key: model().model_dump()}
        
        try:
            # Create temporary LLM instance with specific configuration
            temp_llm = OllamaLLM(
                model=config.get('model', self.model_name),
                base_url=config.get('url', self.base_url),
                temperature=config.get('temperature', 0.1),
                num_predict=config.get('num_predict', 1000),
                top_k=config.get('top_k', LLM_CONFIG.get('top_k', 10)),
                top_p=config.get('top_p', LLM_CONFIG.get('top_p', 0.9))
            )
            
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
                with st.expander(f"🔍 LLM Prompt for {model.__name__} (using {config.get('model', 'default')})"):
                    st.code(formatted_prompt)
                    st.json(config)
            
            # Get response from LLM
            response = temp_llm.invoke(formatted_prompt)
            
            if development_mode:
                with st.expander(f"📝 Raw LLM Response for {model.__name__}"):
                    st.code(f"Response length: {len(response) if response else 0} characters")
                    st.code(response if response else "EMPTY RESPONSE")
            
            # Enhanced response validation
            if not response or not response.strip():
                if development_mode:
                    st.error(f"❌ Empty response from LLM for {model.__name__}")
                return {model_key: model().model_dump()}
            
            # Try multiple parsing strategies
            parsed_data = self._parse_llm_response(response, model, parser, development_mode)
            
            if parsed_data:
                if development_mode:
                    st.success(f"✅ Successfully parsed {model.__name__}")
                return {model_key: parsed_data}
            else:
                if development_mode:
                    st.error(f"❌ All parsing strategies failed for {model.__name__}")
                return {model_key: model().model_dump()}
                
        except Exception as e:
            if development_mode:
                st.error(f"❌ LLM extraction with config failed for {model.__name__}: {str(e)}")
                st.exception(e)
            # Fallback to regular extraction with default config
            return self.extract_with_llm(model, prompt_template, input_variables, input_data, development_mode)
    
    def _parse_llm_response(
        self, 
        response: str, 
        model: Type[BaseModel], 
        parser: PydanticOutputParser, 
        development_mode: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Enhanced response parsing with multiple fallback strategies.
        """
        # Strategy 1: Try Pydantic parser first
        try:
            parsed_output = parser.parse(response)
            if development_mode:
                st.success(f"✅ Strategy 1: Pydantic parsing succeeded")
            return parsed_output.model_dump()
        except Exception as parse_error:
            if development_mode:
                st.warning(f"⚠️ Strategy 1: Pydantic parsing failed: {parse_error}")
        
        # Strategy 2: Clean and parse JSON manually
        try:
            cleaned_response = self._clean_json_response(response)
            if not cleaned_response or cleaned_response.strip() == "":
                if development_mode:
                    st.warning("⚠️ Strategy 2: JSON cleaning resulted in empty string")
                raise ValueError("Empty response after cleaning")
            
            if development_mode:
                with st.expander("🧹 Cleaned JSON Response"):
                    st.code(cleaned_response)
            
            json_output = json.loads(cleaned_response)
            validated_output = model(**json_output)
            
            if development_mode:
                st.success(f"✅ Strategy 2: Manual JSON parsing succeeded")
            return validated_output.model_dump()
            
        except json.JSONDecodeError as json_error:
            if development_mode:
                st.warning(f"⚠️ Strategy 2: JSON parsing failed: {json_error}")
        except Exception as validation_error:
            if development_mode:
                st.warning(f"⚠️ Strategy 2: Model validation failed: {validation_error}")
        
        # Strategy 3: Extract JSON from mixed content
        try:
            extracted_json = self._extract_json_from_text(response)
            if extracted_json:
                validated_output = model(**extracted_json)
                if development_mode:
                    st.success(f"✅ Strategy 3: JSON extraction from mixed content succeeded")
                return validated_output.model_dump()
            else:
                if development_mode:
                    st.warning("⚠️ Strategy 3: No valid JSON found in response")
        except Exception as extract_error:
            if development_mode:
                st.warning(f"⚠️ Strategy 3: JSON extraction failed: {extract_error}")
        
        # Strategy 4: Try to parse incomplete JSON
        try:
            repaired_json = self._repair_json_response(response)
            if repaired_json:
                validated_output = model(**repaired_json)
                if development_mode:
                    st.success(f"✅ Strategy 4: JSON repair succeeded")
                return validated_output.model_dump()
        except Exception as repair_error:
            if development_mode:
                st.warning(f"⚠️ Strategy 4: JSON repair failed: {repair_error}")
        
        # Strategy 5: Create structured response from unstructured text
        try:
            structured_data = self._extract_structured_data(response, model)
            if structured_data:
                validated_output = model(**structured_data)
                if development_mode:
                    st.success(f"✅ Strategy 5: Structured extraction succeeded")
                return validated_output.model_dump()
        except Exception as struct_error:
            if development_mode:
                st.warning(f"⚠️ Strategy 5: Structured extraction failed: {struct_error}")
        
        return None
    
    def _clean_json_response(self, response: str) -> str:
        """Enhanced JSON cleaning with better validation."""
        if not response or not response.strip():
            return ""
        
        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'```\s*', '', response)
        
        # Remove common LLM prefixes
        response = re.sub(r'^.*?(?=\{|\[)', '', response, flags=re.DOTALL)
        
        # Find JSON boundaries
        json_start = -1
        json_end = -1
        
        # Look for opening brace/bracket
        for i, char in enumerate(response):
            if char in ['{', '[']:
                json_start = i
                break
        
        if json_start == -1:
            return ""
        
        # Find matching closing brace/bracket
        if response[json_start] == '{':
            brace_count = 0
            for i in range(json_start, len(response)):
                if response[i] == '{':
                    brace_count += 1
                elif response[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i
                        break
        elif response[json_start] == '[':
            bracket_count = 0
            for i in range(json_start, len(response)):
                if response[i] == '[':
                    bracket_count += 1
                elif response[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        json_end = i
                        break
        
        if json_end == -1:
            return ""
        
        cleaned = response[json_start:json_end + 1].strip()
        return cleaned
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON objects from mixed content text."""
        if not text:
            return None
        
        # Look for JSON objects in the text
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                parsed = json.loads(match)
                if isinstance(parsed, dict) and parsed:
                    return parsed
            except:
                continue
        
        return None
    
    def _repair_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Attempt to repair malformed JSON responses."""
        if not response:
            return None
        
        # Common JSON repair strategies
        repair_strategies = [
            # Add missing closing braces
            lambda x: x + '}' if x.count('{') > x.count('}') else x,
            # Add missing quotes around keys
            lambda x: re.sub(r'(\w+):', r'"\1":', x),
            # Remove trailing commas
            lambda x: re.sub(r',\s*}', '}', x),
            lambda x: re.sub(r',\s*]', ']', x),
        ]
        
        current = response
        for strategy in repair_strategies:
            try:
                current = strategy(current)
                # Try to extract JSON from repaired text
                cleaned = self._clean_json_response(current)
                if cleaned:
                    parsed = json.loads(cleaned)
                    if isinstance(parsed, dict):
                        return parsed
            except:
                continue
        
        return None
    
    def _extract_structured_data(self, text: str, model: Type[BaseModel]) -> Optional[Dict[str, Any]]:
        """Extract structured data from unstructured text based on model fields."""
        if not text:
            return None
        
        # Get model field information
        try:
            model_fields = model.model_fields if hasattr(model, 'model_fields') else {}
            if not model_fields:
                return None
            
            extracted_data = {}
            text_lower = text.lower()
            
            # Simple field extraction based on common patterns
            for field_name, field_info in model_fields.items():
                field_value = None
                
                # Email extraction
                if 'email' in field_name.lower():
                    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
                    if email_match:
                        field_value = email_match.group()
                
                # Phone extraction
                elif 'phone' in field_name.lower() or 'contact' in field_name.lower():
                    phone_match = re.search(r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}', text)
                    if phone_match:
                        field_value = phone_match.group()
                
                # Name extraction (simple)
                elif 'name' in field_name.lower():
                    name_match = re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text)
                    if name_match:
                        field_value = name_match.group()
                
                # LinkedIn extraction
                elif 'linkedin' in field_name.lower():
                    linkedin_match = re.search(r'(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-]+', text, re.IGNORECASE)
                    if linkedin_match:
                        field_value = linkedin_match.group()
                
                # GitHub extraction
                elif 'github' in field_name.lower():
                    github_match = re.search(r'(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9\-]+', text, re.IGNORECASE)
                    if github_match:
                        field_value = github_match.group()
                
                extracted_data[field_name] = field_value
            
            # Only return if we found at least one valid field
            if any(v for v in extracted_data.values()):
                return extracted_data
                
        except Exception:
            pass
        
        return None
    
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
        Uses default configuration.
        """
        return self.extract_with_llm_config(
            model=model,
            prompt_template=prompt_template,
            input_variables=input_variables,
            input_data=input_data,
            config=LLM_CONFIG,
            development_mode=development_mode
        )
    
    def extract_simple(
        self,
        prompt: str,
        development_mode: bool = False
    ) -> str:
        """Simple text extraction without structured parsing."""
        if not self.llm:
            if development_mode:
                st.error("LLM not initialized")
            return ""
        
        if not self._test_connection():
            if development_mode:
                st.error("LLM connection failed")
            return ""
        
        try:
            if development_mode:
                with st.expander("Simple LLM Prompt"):
                    st.code(prompt)
            
            response = self.llm.invoke(prompt)
            
            if development_mode:
                with st.expander("Simple LLM Response"):
                    st.code(response if response else "EMPTY RESPONSE")
            
            return response or ""
            
        except Exception as e:
            if development_mode:
                st.error(f"Simple LLM extraction failed: {str(e)}")
            return ""
    
    def is_available(self) -> bool:
        """Check if LLM service is available."""
        return self.llm is not None and self._test_connection()
    
    def update_model(self, model_name: str):
        """Update the model being used."""
        self.model_name = model_name
        self.connection_tested = False
        self._initialize_llm()


# Global LLM service instance
llm_service = LLMService()