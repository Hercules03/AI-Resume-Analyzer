"""
<<<<<<< HEAD
Enhanced LLM service with robust error handling and response processing.
Replace your current llm_service.py with this file.
=======
Centralized LLM service for handling all LLM interactions.
>>>>>>> parent of 1f716e87 (.)
"""
import json
import re
from typing import Type, Dict, Any, List
import streamlit as st
from pydantic import BaseModel, ValidationError
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
            st.error("LangChain not available. Please install: pip install langchain langchain-ollama")
            return False
        
        try:
            self.llm = OllamaLLM(
                model=self.model_name,
                base_url=self.base_url,
                temperature=LLM_CONFIG['temperature'],
                num_predict=LLM_CONFIG['num_predict'],
                top_k=LLM_CONFIG.get('top_k', 10),
                top_p=LLM_CONFIG.get('top_p', 0.9)
            )
            
            # Don't test connection immediately - do it lazily when first used
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
            if test_response:
                self.connection_tested = True
                return True
            else:
                st.error("LLM connection test failed - no response")
                return False
                
        except Exception as e:
            st.error(f"LLM connection test failed: {str(e)}")
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
                st.error("LLM not initialized")
            return {model.__name__.lower(): model().model_dump()}
        
        # Test connection if not already done
        if not self._test_connection():
            if development_mode:
                st.error("LLM connection failed")
            return {model.__name__.lower(): model().model_dump()}
        
        try:
<<<<<<< HEAD
            # Create temporary LLM instance with enhanced configuration
            temp_config = {
                'model': config.get('model', self.model_name),
                'base_url': config.get('url', self.base_url),
                'temperature': 0.0,  # Force deterministic for JSON
                'num_predict': config.get('num_predict', 2048),
                'top_k': 1,  # Most deterministic
                'top_p': 0.1,
                'repeat_penalty': 1.1,
            }
            
            temp_llm = OllamaLLM(**temp_config)
            
=======
>>>>>>> parent of 1f716e87 (.)
            # Create parser for the model
            parser = PydanticOutputParser(pydantic_object=model)
            
            # Build enhanced prompt template without brace conflicts
            json_instructions = """
CRITICAL: You MUST respond with ONLY a valid JSON object. No other text, explanations, or markdown.

JSON Requirements:
1. Start your response with an opening brace and end with a closing brace
2. Use double quotes for all strings
3. Use null for missing values (not "null", "N/A", or empty strings)  
4. Ensure all brackets and braces are properly closed
5. Do not include any text before or after the JSON object
6. Do not use markdown code blocks (no backticks)

IMPORTANT: Respond with ONLY the JSON object. No additional text.
"""
            
            # Combine original template with instructions
            enhanced_prompt_template = prompt_template + "\n" + json_instructions + "\n{format_instructions}"
            
            # Create prompt template with format_instructions
            prompt = PromptTemplate(
                template=enhanced_prompt_template,
                input_variables=input_variables,
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )
            
            # Format the prompt with input data
            formatted_prompt = prompt.format(**input_data)
            
            if development_mode:
<<<<<<< HEAD
                with st.expander(f"🔍 Enhanced Prompt for {model.__name__} (using {config.get('model', 'default')})"):
                    st.code(formatted_prompt)
                    st.json(temp_config)
            
            # Get response from LLM with retry
            response = self._get_response_with_retry(temp_llm, formatted_prompt, development_mode)
=======
                with st.expander(f"LLM Prompt for {model.__name__}"):
                    st.code(formatted_prompt)
            
            
            response = self.llm.invoke(formatted_prompt)
>>>>>>> parent of 1f716e87 (.)
            
            if development_mode:
                with st.expander(f"Raw LLM Response for {model.__name__}"):
                    st.code(response)
            
            # Try to parse with Pydantic parser first
            try:
                parsed_output = parser.parse(response)
                if development_mode:
<<<<<<< HEAD
                    st.error(f"❌ Empty response from LLM for {model.__name__}")
                return {model_key: model().model_dump()}
            
            # Try multiple parsing strategies
            parsed_data = self._parse_llm_response_enhanced(response, model, parser, development_mode)
            
            if parsed_data:
=======
                    st.success(f"Successfully parsed {model.__name__} with Pydantic")
                return {model.__name__.lower(): parsed_output.model_dump()}
            except Exception as parse_error:
>>>>>>> parent of 1f716e87 (.)
                if development_mode:
                    st.warning(f"Pydantic parsing failed for {model.__name__}: {parse_error}")
                
                # Fallback to manual JSON parsing
                cleaned_response = self._clean_json_response(response)
                json_output = json.loads(cleaned_response)
                
                # Validate with the model
                validated_output = model(**json_output)
                if development_mode:
                    st.success(f"Successfully parsed {model.__name__} with manual JSON parsing")
                return {model.__name__.lower(): validated_output.model_dump()}
                
        except Exception as e:
            if development_mode:
                st.error(f"LLM extraction failed for {model.__name__}: {str(e)}")
                st.exception(e)
<<<<<<< HEAD
            # Return empty model as fallback
            return {model_key: model().model_dump()}
    
    def _get_response_with_retry(self, llm, prompt: str, development_mode: bool = False, max_retries: int = 3) -> str:
        """Get LLM response with retry logic."""
        
        for attempt in range(max_retries):
            try:
                response = llm.invoke(prompt)
                
                if response and response.strip():
                    return response
                
                if development_mode:
                    st.warning(f"⚠️ Attempt {attempt + 1}: Empty response, retrying...")
                
            except Exception as e:
                if development_mode:
                    st.warning(f"⚠️ Attempt {attempt + 1} failed: {e}")
                
                if attempt == max_retries - 1:
                    raise e
        
        return ""
    
    def _parse_llm_response_enhanced(
        self, 
        response: str, 
        model: Type[BaseModel], 
        parser: PydanticOutputParser, 
        development_mode: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Enhanced response parsing with multiple fallback strategies."""
        
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
        
        # Fix common JSON issues
        cleaned = self._fix_json_issues(cleaned)
        
        return cleaned
    
    def _fix_json_issues(self, json_str: str) -> str:
        """Fix common JSON formatting issues."""
        
        # Fix unquoted null values
        json_str = re.sub(r':\s*"null"', ': null', json_str, flags=re.IGNORECASE)
        json_str = re.sub(r':\s*"None"', ': null', json_str, flags=re.IGNORECASE)
        json_str = re.sub(r':\s*"N/A"', ': null', json_str, flags=re.IGNORECASE)
        json_str = re.sub(r':\s*""', ': null', json_str)
        
        # Fix trailing commas
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # Fix multiple commas
        json_str = re.sub(r',\s*,', ',', json_str)
        
        return json_str
    
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
=======
            return {model.__name__.lower(): model().model_dump()}
>>>>>>> parent of 1f716e87 (.)
    
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
                st.error("LLM not initialized")
            return ""
        
        # Test connection if not already done
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
                    st.code(response)
            
            return response
            
        except Exception as e:
            if development_mode:
                st.error(f"Simple LLM extraction failed: {str(e)}")
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