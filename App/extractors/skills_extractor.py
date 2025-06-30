"""
Skills extractor for technical and soft skills.
"""
from typing import Type, Dict, Any
from .base_extractor import BaseExtractor
from models import Skills


class SkillsExtractor(BaseExtractor):
    """Extractor for skills."""
    
    def get_model(self) -> Type[Skills]:
        """Get the Pydantic model for skills extraction."""
        return Skills
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for skills extraction."""
        return """
You are an assistant that extracts and categorizes skills mentioned in resume text.
Focus on the Skills section and also extract skills mentioned throughout the resume.

Categorize skills into the following categories. If a skill doesn't perfectly fit, place it in the most relevant category or create a new, highly specific category if necessary (e.g., "Medical Procedures" or "Financial Regulations").

- **Technical Skills:** (Software proficiency, specific tools, programming languages, data analysis tools, design software, etc.)
- **Industry-Specific Skills:** (Skills unique to a particular industry such as medical procedures, financial modeling, legal research, marketing analytics platforms, specific manufacturing processes, etc.)
- **Business & Management Skills:** (Project management, strategic planning, financial analysis, budgeting, risk management, business development, operations management, quality assurance, supply chain management, etc.)
- **Creative & Design Skills:** (Graphic design, content creation, video editing, UI/UX design, artistic abilities, creative writing, photography, etc.)
- **Communication & Interpersonal Skills:** (Public speaking, negotiation, client relations, teamwork, presentation skills, written communication, active listening, conflict resolution, customer service, etc.)
- **Leadership & Mentorship:** (Team leadership, coaching, mentoring, delegation, decision-making, strategic leadership, change management, etc.)
- **Problem-Solving & Critical Thinking:** (Analytical thinking, root cause analysis, troubleshooting, research, data interpretation, innovative thinking, etc.)
- **Organizational & Administrative Skills:** (Time management, scheduling, record keeping, data entry, office management, event planning, meticulous attention to detail, etc.)
- **Methodologies & Frameworks:** (Agile, Scrum, Lean, Six Sigma, project management methodologies, research methodologies, specific business frameworks like SWOT analysis, etc.)
- **Languages:** (Fluency in spoken and written languages, e.g., English, Spanish, Japanese, with proficiency levels like "Fluent," "Proficient," "Basic conversational.")
- **Domain Knowledge:** (Specialized knowledge in a particular field or subject area, e.g., healthcare regulations, international trade, environmental policy, digital marketing, educational psychology, real estate law, etc.)

Resume Text:
```Resume Text
{text}
```

Return your output as a JSON object with the schema provided below.
Use empty arrays for categories where no skills are found.

{format_instructions}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the skills extraction output."""
        return output 