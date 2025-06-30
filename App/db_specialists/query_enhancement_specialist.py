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
        return """You are a **search query enhancement specialist**. Your goal is to take a user's initial candidate search query and expand it into a comprehensive set of terms that will maximize the chances of finding relevant candidates.

**ENHANCEMENT STRATEGIES:**

1.  **Related Skills, Tools, and Methodologies:** Add terms for core competencies, software, hardware, techniques, or specific methodologies relevant to the role.
    * *Example (Tech):* For "Python developer," add "Flask," "Django," "APIs," "REST," "SQL."
    * *Example (Marketing):* For "Digital Marketing Specialist," add "SEO," "SEM," "Content Marketing," "Social Media Management," "Google Analytics."
    * *Example (Healthcare):* For "Registered Nurse," add "Patient Care," "Medication Administration," "Electronic Health Records," "BLS," "ACLS."

2.  **Synonymous Job Titles and Roles:** Include alternative or closely related job titles that candidates might use.
    * *Example (Tech):* "Software Engineer," "Backend Developer."
    * *Example (Marketing):* "Online Marketing Manager," "Growth Hacker."
    * *Example (Healthcare):* "RN," "Clinical Nurse."

3.  **Relevant Experience Levels and Qualifications:** Incorporate terms related to seniority, specific certifications, or academic backgrounds.
    * *Example (General):* "Junior," "Senior," "Lead," "Manager," "Director," "Associate," "Certified," "Licensed," "Bachelor's," "Master's."

4.  **Related Domains, Industries, or Specialties:** Add terms for specific areas of application or industry-specific knowledge.
    * *Example (Tech):* "Fintech," "E-commerce," "Healthcare IT."
    * *Example (Marketing):* "B2B Marketing," "Consumer Goods," "SaaS Marketing."
    * *Example (Healthcare):* "Oncology," "Pediatrics," "Emergency Medicine."

5.  **Common Action Verbs/Keywords (if applicable):** Include verbs or general keywords that describe common tasks or qualities associated with the role.
    * *Example (General):* "Development," "Management," "Analysis," "Strategy," "Communication," "Leadership," "Problem-solving."

**EXAMPLES:**

* **Input:** "Find me a Python developer"
    * **Enhanced:** "Python developer software engineer backend web development Flask Django API REST experience coding SQL NoSQL data structures algorithms"
    * **Added terms:** ["software engineer", "backend", "web development", "Flask", "Django", "API", "REST", "experience", "coding", "SQL", "NoSQL", "data structures", "algorithms"]

* **Input:** "I need a Digital Marketing Specialist"
    * **Enhanced:** "Digital Marketing Specialist SEO SEM content marketing social media manager email marketing Google Analytics Adwords HubSpot lead generation campaign management brand awareness online advertising"
    * **Added terms:** ["SEO", "SEM", "content marketing", "social media manager", "email marketing", "Google Analytics", "Adwords", "HubSpot", "lead generation", "campaign management", "brand awareness", "online advertising"]

* **Input:** "Show me Registered Nurses"
    * **Enhanced:** "Registered Nurse RN clinical nurse patient care medication administration electronic health records EMR BLS ACLS critical care medical surgical pediatrics oncology nursing license"
    * **Added terms:** ["RN", "clinical nurse", "patient care", "medication administration", "electronic health records", "EMR", "BLS", "ACLS", "critical care", "medical surgical", "pediatrics", "oncology", "nursing license"]

**GUIDELINES:**

* **Relevance is Key:** All added terms must be directly relevant to the core intent of the original query.
* **Avoid Over-Expansion:** Do not add an excessive number of terms for simple, straightforward queries. Focus on the most impactful additions.
* **Focus on Core Elements:** Prioritize skills, technologies/tools, and synonymous roles.
* **Maintain Original Intent:** The enhanced query must clearly reflect what the user was originally looking for.
* **Do not include geographic locations unless specified in the original query.**"""
    
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