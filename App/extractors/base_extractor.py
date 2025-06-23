"""
Base extractor class for all specialized extractors.
"""
from abc import ABC, abstractmethod
from typing import Type, Dict, Any, List
from pydantic import BaseModel
from llm_service import llm_service


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
    
    def extract(self, extracted_text: str, development_mode: bool = False) -> Dict[str, Any]:
        """Extract information from the resume."""
        input_data = self.prepare_input_data(extracted_text)
        output = llm_service.extract_with_llm(
            self.get_model(),
            self.get_prompt_template(),
            self.get_input_variables(),
            input_data,
            development_mode
        )
        return self.process_output(output) 