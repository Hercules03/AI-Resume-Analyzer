"""
Base specialist class for all chatbot LLM specialists.
"""
from abc import ABC, abstractmethod
from typing import Type, Dict, Any, List, Optional
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
import streamlit as st


class BaseSpecialist(ABC):
    """
    Base class for all LLM specialists in the chatbot system.
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """Initialize the specialist with LLM configuration."""
        self.llm_config = llm_config
        self.llm = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM instance."""
        try:
            self.llm = ChatOllama(
                model=self.llm_config['model'],
                base_url=self.llm_config.get('url', self.llm_config.get('base_url')),
                temperature=self.llm_config.get('temperature', 0.1),
                num_predict=self.llm_config.get('num_predict', 1024)
            )
        except Exception as e:
            st.error(f"❌ Failed to initialize {self.__class__.__name__}: {e}")
    
    @abstractmethod
    def get_model(self) -> Optional[Type[BaseModel]]:
        """Get the Pydantic model for the specialist (None if not using structured output)."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for the specialist."""
        pass
    
    @abstractmethod
    def get_user_prompt_template(self) -> str:
        """Get the user prompt template for the specialist."""
        pass
    
    @abstractmethod
    def process_output(self, output: Any, **kwargs) -> Any:
        """Process the output from the LLM."""
        pass
    
    def prepare_input_data(self, **kwargs) -> Dict[str, Any]:
        """Prepare input data for the LLM."""
        return kwargs
    
    def execute(self, **kwargs) -> Any:
        """Execute the specialist function."""
        if not self.llm:
            raise Exception(f"{self.__class__.__name__} LLM not initialized")
        
        try:
            # Prepare input data
            input_data = self.prepare_input_data(**kwargs)
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=self.get_user_prompt_template().format(**input_data))
            ])
            
            # Execute LLM
            response = self.llm.invoke(prompt.format_messages())
            
            # Process and return output
            return self.process_output(response.content, **kwargs)
            
        except Exception as e:
            st.error(f"{self.__class__.__name__} execution failed: {e}")
            return self._get_fallback_output(**kwargs)

    def stream(self, **kwargs):
        """Execute the specialist function with streaming."""
        if not self.llm:
            raise Exception(f"{self.__class__.__name__} LLM not initialized")
        
        try:
            # Prepare input data
            input_data = self.prepare_input_data(**kwargs)
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=self.get_user_prompt_template().format(**input_data))
            ])
            
            # Stream response
            for chunk in self.llm.stream(prompt.format_messages()):
                if chunk.content:
                    yield chunk.content
            
        except Exception as e:
            st.error(f"{self.__class__.__name__} streaming failed: {e}")
            yield self._get_fallback_output(**kwargs)
    
    @abstractmethod
    def _get_fallback_output(self, **kwargs) -> Any:
        """Get fallback output when LLM execution fails."""
        pass
    
    def is_available(self) -> bool:
        """Check if the specialist is available."""
        return self.llm is not None 