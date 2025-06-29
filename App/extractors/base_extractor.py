"""
Base extractor class for all specialized extractors.
"""
from abc import ABC, abstractmethod
from typing import Type, Dict, Any, List
from pydantic import BaseModel
from llm_service import llm_service
from config import EXTRACTORS_CONFIG


class BaseExtractor(ABC):
    """
    Base class for all extractors.
    """
    
    @abstractmethod
    def get_model(self) -> Type[BaseModel]:
        """Get the Pydantic model for the extractor."""
        pass
    
    @abstractmethod
    def get_prompt_template(self) -> str:
        """Get the prompt template for the extractor."""
        pass
    
    def get_input_variables(self) -> List[str]:
        """Get the input variables for the prompt template."""
        return ["text"]
    
    @abstractmethod
    def process_output(self, output: Any) -> Dict[str, Any]:
        """Process the output from the LLM."""
        pass
    
    def prepare_input_data(self, extracted_text: str) -> Dict[str, Any]:
        """Prepare input data for the LLM."""
        return {"text": extracted_text}
    
    def get_extractor_name(self) -> str:
        """Get the extractor name for configuration lookup."""
        class_name = self.__class__.__name__
        # Convert CamelCase to snake_case (e.g., ProfileExtractor -> profile_extractor)
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', class_name)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        return name
    
    def get_extractor_config(self) -> Dict[str, Any]:
        """Get the configuration for this extractor."""
        extractor_name = self.get_extractor_name()
        return EXTRACTORS_CONFIG.get(extractor_name, EXTRACTORS_CONFIG.get('default', {
            'model': 'gemma3:12b',
            'url': 'http://localhost:11434',
            'temperature': 0.1,
            'num_predict': 1000,
            'timeout': 60
        }))
    
    def extract(self, extracted_text: str, development_mode: bool = False) -> Dict[str, Any]:
        """Extract information from the resume using extractor-specific configuration."""
        input_data = self.prepare_input_data(extracted_text)
        config = self.get_extractor_config()
        
        output = llm_service.extract_with_llm_config(
            self.get_model(),
            self.get_prompt_template(),
            self.get_input_variables(),
            input_data,
            config,
            development_mode
        )
        return self.process_output(output) 