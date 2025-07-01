"""
Base analyzer class for all LLM-powered analyzers.
"""
from abc import ABC, abstractmethod
from typing import Type, Dict, Any, List
from pydantic import BaseModel
from llm_service import llm_service


class BaseAnalyzer(ABC):
    """
    Base class for all LLM-powered analyzers.
    Unlike extractors that work with raw text, analyzers work with structured resume data.
    """
    
    @abstractmethod
    def get_model(self) -> Type[BaseModel]:
        """Get the Pydantic model for the analyzer output."""
        pass
    
    @abstractmethod
    def get_prompt_template(self) -> str:
        """Get the prompt template for the analyzer."""
        pass
    
    def get_input_variables(self) -> List[str]:
        """Get the input variables for the prompt template."""
        return ["resume_data"]
    
    @abstractmethod
    def process_output(self, output: Any) -> Dict[str, Any]:
        """Process the output from the LLM."""
        pass
    
    @abstractmethod
    def prepare_input_data(self, resume, **kwargs) -> Dict[str, Any]:
        """Prepare input data from structured resume object."""
        pass
    
    def analyze(self, resume, development_mode: bool = False, **kwargs) -> Dict[str, Any]:
        """Analyze structured resume data using LLM."""
        input_data = self.prepare_input_data(resume, **kwargs)
        output = llm_service.extract_with_llm(
            self.get_model(),
            self.get_prompt_template(),
            self.get_input_variables(),
            input_data,
            development_mode
        )
        return self.process_output(output)