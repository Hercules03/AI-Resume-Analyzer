"""
Query enhancement specialist for improving search queries.
"""
from typing import Type, Optional, Dict, Any
from .base_specialist import BaseSpecialist
from .models import QueryEnhancement
from pydantic import BaseModel


class QueryEnhancementSpecialist(BaseSpecialist):
    """Specialist for enhancing search queries for better candidate matching."""
    
    def get_model(self) -> Optional[Type[BaseModel]]:
        """Get the Pydantic model for query enhancement."""
        return QueryEnhancement
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for query enhancement."""
        return """You are a search query enhancement specialist for candidate recruitment.
Your task is to expand user queries into comprehensive search terms that will find relevant candidates.

ENHANCEMENT STRATEGIES:

1. Add related technical skills and technologies
2. Include synonymous job titles and roles
3. Add relevant experience levels and qualifications
4. Include related domains and industries
5. Add common tools and frameworks

EXAMPLES:

Input: "Find me a Python developer"
Enhanced: "Python developer software engineer programming backend web development Flask Django API REST experience coding"
Added terms: ["software engineer", "programming", "backend", "web development", "Flask", "Django", "API", "REST", "experience", "coding"]

Input: "I need someone for machine learning"
Enhanced: "machine learning data scientist AI artificial intelligence Python TensorFlow PyTorch deep learning neural networks data analysis statistics ML engineer"
Added terms: ["data scientist", "AI", "artificial intelligence", "Python", "TensorFlow", "PyTorch", "deep learning", "neural networks", "data analysis", "statistics", "ML engineer"]

Input: "Show me frontend developers"
Enhanced: "frontend developer front-end UI UX JavaScript React Angular Vue HTML CSS TypeScript web developer interface design"
Added terms: ["front-end", "UI", "UX", "JavaScript", "React", "Angular", "Vue", "HTML", "CSS", "TypeScript", "web developer", "interface design"]

GUIDELINES:
- Keep enhancements relevant and specific
- Don't over-expand simple queries
- Focus on skills, technologies, and synonyms
- Maintain the core intent of the original query"""
    
    def get_user_prompt_template(self) -> str:
        """Get the user prompt template for query enhancement."""
        return """Enhance this candidate search query for better semantic matching:

Original Query: "{query}"

Provide your enhancement in the following JSON format:
{{
    "enhanced_query": "expanded query with related terms",
    "original_query": "{query}",
    "added_terms": ["term1", "term2", "term3"],
    "reasoning": "explanation of enhancements made"
}}

Make the enhanced query comprehensive but focused. Include related skills, technologies, job titles, and relevant terms that would help find matching candidates."""
    
    def process_output(self, output: str, **kwargs) -> str:
        """Process the query enhancement output."""
        try:
            import json
            # Try to parse JSON output
            result = json.loads(output.strip())
            
            enhanced_query = result.get('enhanced_query', '').strip()
            original_query = kwargs.get('query', '')
            
            # Validation: enhanced query should be longer and contain original terms
            if enhanced_query and len(enhanced_query) > len(original_query):
                return enhanced_query
            else:
                return original_query
                
        except (json.JSONDecodeError, ValueError):
            # Fallback: return original query
            return kwargs.get('query', '')
    
    def _get_fallback_output(self, **kwargs) -> str:
        """Get fallback output when query enhancement fails."""
        return kwargs.get('query', '') 