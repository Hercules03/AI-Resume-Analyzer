# Career Transition Extractor

## Overview

The `CareerTransitionExtractor` is a robust, LLM-powered extractor that provides comprehensive career progression analysis, replacing the simple keyword-based approach previously used in the `_extract_career_transitions()` function.

## Key Improvements

### Before (Simple Function)
- **Basic keyword matching** for field detection
- **Limited field categories** (4 basic fields)
- **Simple transition detection** (field A → field B)
- **No context analysis** about why transitions occurred
- **No career progression insights**

### After (LLM-Based Extractor)
- **Intelligent field classification** using LLM understanding
- **15+ comprehensive field categories**
- **Detailed transition analysis** with context and rationale
- **Career coherence scoring** (1-10 scale)
- **Growth trajectory analysis**
- **Strengths and concerns assessment**
- **Transferable skills identification**

## Features

### 1. Advanced Field Classification
```
- Data Science & Analytics
- Software Engineering/Development  
- Product Management
- Business/Sales/Marketing
- Finance & Accounting
- Operations & Supply Chain
- Human Resources
- Design & Creative
- Healthcare & Medical
- Education & Training
- Legal & Compliance
- Consulting
- Management & Leadership
- Research & Development
- Other (with specification)
```

### 2. Transition Type Analysis
- **Vertical**: Promotion within same field
- **Horizontal**: Same level, different company/role in same field
- **Pivot**: Complete field change
- **Lateral**: Related field with skill overlap

### 3. Career Path Patterns
- **Linear**: Steady progression in one field
- **Zigzag**: Multiple field changes with some inconsistency
- **Specialized**: Deep expertise in one area
- **Diverse**: Intentional multi-field experience
- **Early Career**: Still exploring, limited experience

### 4. Comprehensive Analysis Output
```python
{
    "transitions": [
        {
            "from_field": "Business/Sales/Marketing",
            "to_field": "Data Science & Analytics", 
            "transition_point": "Tech Solutions Inc (2020)",
            "transition_type": "pivot",
            "skill_overlap": "Analytical thinking, customer behavior analysis",
            "rationale": "Career growth opportunity in emerging field"
        }
    ],
    "career_path_type": "diverse",
    "primary_career_field": "Data Science & Analytics",
    "career_coherence_score": 7,
    "growth_trajectory": "ascending",
    "field_expertise_areas": ["Marketing Analytics", "Data Science", "Machine Learning"],
    "transition_summary": "Strategic career progression from marketing to data science...",
    "strengths_from_transitions": [
        "Cross-functional perspective",
        "Adaptability and learning agility"
    ],
    "potential_concerns": [
        "May need time to deepen technical expertise"
    ]
}
```

## Usage

### Basic Usage
```python
from extractors import CareerTransitionExtractor
from models import Resume

# Initialize extractor
career_extractor = CareerTransitionExtractor()

# Analyze career transitions
result = career_extractor.extract_from_work_experiences(
    work_experiences_data, 
    development_mode=False
)

analysis = result.get('careerprogressionanalysis', {})
```

### Integration with Resume Processing
```python
def get_enhanced_career_data(resume: Resume) -> dict:
    """Get comprehensive career analysis for a resume."""
    
    # Convert Resume work_experiences to extractor format
    work_exp_data = []
    for exp in resume.work_experiences:
        exp_dict = {
            'job_title': exp.job_title,
            'company': exp.company,
            'duration': exp.duration,
            'responsibilities': exp.responsibilities or [],
            'technologies': exp.technologies or []
        }
        work_exp_data.append(exp_dict)
    
    # Analyze with LLM
    career_extractor = CareerTransitionExtractor()
    result = career_extractor.extract_from_work_experiences(work_exp_data)
    
    return result.get('careerprogressionanalysis', {})
```

### Database Integration (Backward Compatible)
```python
def format_for_database(analysis: dict) -> str:
    """Format analysis for existing database field."""
    
    if not analysis.get('transitions'):
        return analysis.get('transition_summary', 'No transitions detected')
    
    transitions_text = []
    for transition in analysis['transitions']:
        transition_str = f"{transition['from_field']} → {transition['to_field']}"
        if transition.get('transition_type'):
            transition_str += f" ({transition['transition_type']})"
        transitions_text.append(transition_str)
    
    result = "; ".join(transitions_text)
    
    # Add metadata
    if analysis.get('career_path_type'):
        result += f" | Path: {analysis['career_path_type']}"
    
    if analysis.get('career_coherence_score'):
        result += f" | Coherence: {analysis['career_coherence_score']}/10"
    
    return result
```

## Implementation in evaluation.py

The extractor has been integrated into `evaluation.py` with fallback support:

```python
def _extract_career_transitions(work_experiences):
    """Enhanced career transition analysis with LLM fallback."""
    try:
        # Use LLM-based analysis
        from extractors import CareerTransitionExtractor
        career_extractor = CareerTransitionExtractor()
        result = career_extractor.extract_from_work_experiences(work_exp_data)
        # ... process and format result
        
    except Exception as e:
        # Fallback to original keyword-based approach
        return _extract_career_transitions_fallback(work_experiences)
```

## Benefits for HR Analysis

### Enhanced Insights
1. **Career Coherence Scoring**: Understand how focused a candidate's career path is
2. **Transition Rationale**: Understand why candidates changed fields
3. **Transferable Skills**: Identify what skills enabled transitions
4. **Growth Trajectory**: Assess career progression patterns
5. **Strengths & Concerns**: Balanced view of career transitions

### HR Decision Support
- **Hiring Decisions**: Better understand candidate fit and potential
- **Interview Preparation**: Targeted questions about career transitions
- **Role Suitability**: Match candidates based on career progression patterns
- **Development Planning**: Understand candidate's growth trajectory

## Error Handling & Fallback

The system includes robust error handling:

1. **LLM Unavailable**: Falls back to keyword-based analysis
2. **Insufficient Data**: Provides appropriate default responses
3. **Processing Errors**: Graceful degradation with fallback methods
4. **Backward Compatibility**: Works with existing database schema

## Performance Considerations

- **Efficient Processing**: Only analyzes when multiple work experiences exist
- **Caching Potential**: Results can be cached for repeated analysis
- **Development Mode**: Includes detailed logging for debugging
- **Resource Management**: Handles LLM service availability gracefully

## Future Enhancements

Potential improvements:
1. **Industry-Specific Analysis**: Tailored analysis for different industries
2. **Timeline Analysis**: Consider timing and duration of transitions
3. **Skills Gap Analysis**: Identify missing skills for transitions
4. **Recommendation Engine**: Suggest career paths based on current trajectory
5. **Comparative Analysis**: Benchmark against similar career paths

## Testing

Run the example to test the extractor:

```bash
cd App
python example_career_transition_usage.py
```

This will demonstrate the extractor capabilities with sample data and show the detailed analysis output. 