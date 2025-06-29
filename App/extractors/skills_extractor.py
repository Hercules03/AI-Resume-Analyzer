"""
Enhanced SkillsExtractor with sliding window approach and skill context detection
for handling complex PDF layouts and fragmented text.
"""
import re
from typing import Dict, Any, List, Tuple, Set
from difflib import SequenceMatcher
from .base_extractor import BaseExtractor
from models import Skills


class SkillsExtractor(BaseExtractor):
    """Enhanced extractor with sliding window and context detection capabilities."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.skill_databases = self._load_skill_databases()
        
        # Sliding window configuration
        self.window_size = 200  # characters per window
        self.window_overlap = 50  # overlap between windows
        self.fuzzy_threshold = 0.8  # minimum similarity for fuzzy matching
        
        # Context detection patterns
        self.skills_section_patterns = self._load_skills_section_patterns()
        self.skill_list_patterns = self._load_skill_list_patterns()
    
    def _load_skills_section_patterns(self) -> List[str]:
        """Load patterns that indicate skills sections."""
        return [
            # Common section headers
            r'(?i)\b(?:technical\s+)?skills?\b',
            r'(?i)\b(?:core\s+)?competenc(?:ies|y)\b',
            r'(?i)\bproficienc(?:ies|y)\b',
            r'(?i)\bexpertise\b',
            r'(?i)\btechnolog(?:ies|y)\b',
            r'(?i)\btools?\s+(?:and\s+)?(?:technologies|software)\b',
            r'(?i)\bprogramming\s+languages?\b',
            r'(?i)\bsoftware\s+skills?\b',
            r'(?i)\btechnical\s+knowledge\b',
            r'(?i)\bkey\s+skills?\b',
            r'(?i)\brelevant\s+skills?\b',
            
            # Fragmented patterns (for broken extraction)
            r'(?i)sk\s*ill\s*s?',
            r'(?i)tech\s*nic\s*al',
            r'(?i)prog\s*ram\s*ming',
            r'(?i)soft\s*ware',
            r'(?i)comp\s*eten\s*c',
        ]
    
    def _load_skill_list_patterns(self) -> List[str]:
        """Load patterns that indicate skill lists."""
        return [
            # Bullet points and list indicators
            r'[•·▪▫‣⁃]\s*([^•·▪▫‣⁃\n]+)',
            r'[-*]\s+([^-*\n]+)',
            r'(?:^|\n)\s*[➤►▶]\s*([^\n]+)',
            
            # Numbered lists
            r'\d+\.\s*([^\d\n]+?)(?=\d+\.|$)',
            
            # Comma-separated lists (after skills indicators)
            r'(?i)(?:skills?|technologies|tools|languages):\s*([^:\n]+)',
            
            # Parenthetical skill lists
            r'\(([^)]+(?:,\s*[^)]+)*)\)',
            
            # Skills in job descriptions
            r'(?i)(?:using|with|including|such as|experience in)\s+([^.;:\n]+)',
            
            # Common separator patterns
            r'([A-Za-z][^,;|\n]+)(?:[,;|]\s*([A-Za-z][^,;|\n]+))*',
        ]
    
    def extract(self, extracted_text: str, development_mode: bool = False) -> Dict[str, Any]:
        """Enhanced extraction with sliding window and context detection."""
        # Get standard extraction first
        standard_result = super().extract(extracted_text, development_mode)
        
        # Check if standard extraction was successful
        standard_skills_count = self._count_total_skills(standard_result.get('skills', {}))
        
        if development_mode:
            print(f"🔍 Standard extraction found {standard_skills_count} skills")
        
        # Apply enhanced extraction techniques
        enhanced_result = self._enhanced_skills_extraction(
            extracted_text, standard_result, development_mode
        )
        
        # Validate and clean results
        validated_result = self._validate_skills_against_text(enhanced_result, extracted_text)
        cleaned_result = self._clean_and_categorize_skills(validated_result)
        
        if development_mode:
            enhanced_count = self._count_total_skills(cleaned_result.get('skills', {}))
            improvement = enhanced_count - standard_skills_count
            print(f"✨ Enhanced extraction found {enhanced_count} skills ({improvement:+d} improvement)")
            self._print_extraction_summary(cleaned_result, extracted_text)
        
        return cleaned_result
    
    def _enhanced_skills_extraction(self, text: str, standard_result: Dict[str, Any], 
                                  development_mode: bool = False) -> Dict[str, Any]:
        """Apply sliding window and context detection techniques."""
        
        # Start with standard results
        all_skills = standard_result.get('skills', {}).copy()
        
        # Step 1: Sliding window approach
        sliding_window_skills = self._sliding_window_extraction(text, development_mode)
        
        # Step 2: Context detection approach
        context_skills = self._context_detection_extraction(text, development_mode)
        
        # Step 3: Merge results intelligently
        merged_skills = self._merge_skill_results([all_skills, sliding_window_skills, context_skills])
        
        return {'skills': merged_skills}
    
    def _sliding_window_extraction(self, text: str, development_mode: bool = False) -> Dict[str, List[str]]:
        """Extract skills using sliding window approach for fragmented text."""
        
        if development_mode:
            print("🔄 Applying sliding window extraction...")
        
        # Prepare known skills database for fuzzy matching
        known_skills = self._build_comprehensive_skills_database()
        
        # Create sliding windows
        windows = self._create_sliding_windows(text)
        
        # Extract skills from each window
        window_skills = {}
        
        for i, window in enumerate(windows):
            window_results = self._extract_skills_from_window(window, known_skills)
            
            # Merge window results
            for category, skills in window_results.items():
                if category not in window_skills:
                    window_skills[category] = []
                window_skills[category].extend(skills)
        
        # Remove duplicates while preserving order
        deduplicated_skills = self._deduplicate_skills(window_skills)
        
        if development_mode:
            window_count = self._count_total_skills(deduplicated_skills)
            print(f"  📊 Sliding window found {window_count} skills across {len(windows)} windows")
        
        return deduplicated_skills
    
    def _context_detection_extraction(self, text: str, development_mode: bool = False) -> Dict[str, List[str]]:
        """Extract skills using context detection for scrambled sections."""
        
        if development_mode:
            print("🎯 Applying context detection extraction...")
        
        context_skills = {}
        
        # Step 1: Find skills sections
        skills_sections = self._identify_skills_sections(text)
        
        # Step 2: Extract from identified sections
        for section_text, confidence in skills_sections:
            section_skills = self._extract_from_skills_section(section_text, confidence)
            
            # Merge section results
            for category, skills in section_skills.items():
                if category not in context_skills:
                    context_skills[category] = []
                context_skills[category].extend(skills)
        
        # Step 3: Extract from skill list patterns
        pattern_skills = self._extract_from_skill_patterns(text)
        
        # Merge pattern results
        for category, skills in pattern_skills.items():
            if category not in context_skills:
                context_skills[category] = []
            context_skills[category].extend(skills)
        
        # Remove duplicates
        deduplicated_skills = self._deduplicate_skills(context_skills)
        
        if development_mode:
            context_count = self._count_total_skills(deduplicated_skills)
            print(f"  🎯 Context detection found {context_count} skills from {len(skills_sections)} sections")
        
        return deduplicated_skills
    
    def _create_sliding_windows(self, text: str) -> List[str]:
        """Create overlapping windows from text."""
        windows = []
        text_length = len(text)
        
        start = 0
        while start < text_length:
            end = min(start + self.window_size, text_length)
            window = text[start:end]
            
            # Extend window to complete words if possible
            if end < text_length:
                # Look for word boundary within next 20 characters
                for i in range(min(20, text_length - end)):
                    if text[end + i].isspace():
                        window = text[start:end + i]
                        break
            
            windows.append(window)
            
            # Move start position
            start += self.window_size - self.window_overlap
            
            # Prevent infinite loop
            if start >= text_length:
                break
        
        return windows
    
    def _extract_skills_from_window(self, window: str, known_skills: Set[str]) -> Dict[str, List[str]]:
        """Extract skills from a single window using fuzzy matching."""
        window_skills = {}
        window_lower = window.lower()
        
        # Direct matching with known skills
        for skill in known_skills:
            skill_lower = skill.lower()
            
            # Exact match
            if self._skill_exists_in_window(skill_lower, window_lower):
                category = self._categorize_skill(skill)
                if category not in window_skills:
                    window_skills[category] = []
                window_skills[category].append(skill)
                continue
            
            # Fuzzy matching for fragmented skills
            fuzzy_matches = self._find_fuzzy_matches(skill_lower, window_lower)
            for match in fuzzy_matches:
                category = self._categorize_skill(skill)
                if category not in window_skills:
                    window_skills[category] = []
                window_skills[category].append(skill)
                break  # Only add once per skill
        
        return window_skills
    
    def _skill_exists_in_window(self, skill: str, window: str) -> bool:
        """Check if skill exists in window with flexible matching."""
        # Handle multi-word skills
        if ' ' in skill:
            words = skill.split()
            # Check if all words appear in reasonable proximity
            pattern = r'\b' + r'\W{0,10}'.join(re.escape(word) for word in words) + r'\b'
            return bool(re.search(pattern, window, re.IGNORECASE))
        
        # Single word with boundary check
        pattern = r'\b' + re.escape(skill) + r'\b'
        return bool(re.search(pattern, window, re.IGNORECASE))
    
    def _find_fuzzy_matches(self, skill: str, window: str) -> List[str]:
        """Find fuzzy matches for fragmented skills."""
        matches = []
        
        # Split window into potential skill tokens
        tokens = re.findall(r'\b\w+\b', window)
        
        # Check similarity with each token
        for token in tokens:
            if len(token) >= 3 and len(skill) >= 3:  # Minimum length for fuzzy matching
                similarity = SequenceMatcher(None, skill, token.lower()).ratio()
                if similarity >= self.fuzzy_threshold:
                    matches.append(token)
        
        # Check for partial matches in longer strings
        for i in range(len(window) - len(skill) + 1):
            substring = window[i:i + len(skill)]
            similarity = SequenceMatcher(None, skill, substring).ratio()
            if similarity >= self.fuzzy_threshold:
                matches.append(substring)
        
        return matches
    
    def _identify_skills_sections(self, text: str) -> List[Tuple[str, float]]:
        """Identify sections that likely contain skills."""
        skills_sections = []
        
        for pattern in self.skills_section_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
            
            for match in matches:
                # Extract section after the header
                start_pos = match.end()
                
                # Find end of section (next header or significant gap)
                section_end = self._find_section_end(text, start_pos)
                section_text = text[start_pos:section_end].strip()
                
                if len(section_text) > 10:  # Minimum section length
                    confidence = self._calculate_section_confidence(match.group(), section_text)
                    skills_sections.append((section_text, confidence))
        
        # Sort by confidence and remove duplicates
        skills_sections = self._deduplicate_sections(skills_sections)
        
        return skills_sections
    
    def _find_section_end(self, text: str, start_pos: int) -> int:
        """Find the end of a skills section."""
        # Look for next section header or double newline
        patterns = [
            r'\n\s*\n\s*[A-Z]',  # Double newline followed by capital letter
            r'\n\s*(?:EXPERIENCE|EDUCATION|WORK|EMPLOYMENT|PROJECTS?)',  # Common section headers
            r'\n\s*\d{4}\s*[-–—]',  # Date patterns (likely start of experience)
        ]
        
        min_end = len(text)
        for pattern in patterns:
            match = re.search(pattern, text[start_pos:], re.IGNORECASE)
            if match:
                min_end = min(min_end, start_pos + match.start())
        
        # Fallback: limit to reasonable section length
        max_section_length = 1000
        return min(min_end, start_pos + max_section_length)
    
    def _calculate_section_confidence(self, header: str, content: str) -> float:
        """Calculate confidence that this is a skills section."""
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on header quality
        if re.search(r'(?i)\bskills?\b', header):
            confidence += 0.3
        if re.search(r'(?i)\btechnical\b', header):
            confidence += 0.2
        
        # Boost confidence based on content patterns
        skill_indicators = [
            r'[•·▪▫‣⁃-]',  # Bullet points
            r'(?i)\b(?:python|java|javascript|html|css|sql)\b',  # Common tech skills
            r'(?i)\b(?:microsoft|adobe|oracle|salesforce)\b',  # Common software
            r'[,;]\s*[A-Z]',  # Comma-separated lists
        ]
        
        for pattern in skill_indicators:
            matches = len(re.findall(pattern, content))
            confidence += min(matches * 0.1, 0.3)
        
        return min(confidence, 1.0)
    
    def _extract_from_skills_section(self, section_text: str, confidence: float) -> Dict[str, List[str]]:
        """Extract skills from an identified skills section."""
        section_skills = {}
        
        # Apply different extraction strategies based on confidence
        if confidence > 0.8:
            # High confidence: aggressive extraction
            section_skills = self._aggressive_skill_extraction(section_text)
        else:
            # Lower confidence: conservative extraction
            section_skills = self._conservative_skill_extraction(section_text)
        
        return section_skills
    
    def _extract_from_skill_patterns(self, text: str) -> Dict[str, List[str]]:
        """Extract skills using predefined patterns."""
        pattern_skills = {}
        
        for pattern in self.skill_list_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                if isinstance(match, tuple):
                    match = ' '.join(match)
                
                # Parse potential skills from match
                skills = self._parse_skills_from_text(match)
                
                for skill in skills:
                    category = self._categorize_skill(skill)
                    if category not in pattern_skills:
                        pattern_skills[category] = []
                    pattern_skills[category].append(skill)
        
        return pattern_skills
    
    def _aggressive_skill_extraction(self, text: str) -> Dict[str, List[str]]:
        """Aggressive skill extraction for high-confidence sections."""
        skills = {}
        known_skills = self._build_comprehensive_skills_database()
        
        # Extract any token that matches known skills
        tokens = re.findall(r'\b\w+(?:\s+\w+){0,2}\b', text)  # 1-3 word tokens
        
        for token in tokens:
            token_clean = token.strip().title()
            if token_clean.lower() in [s.lower() for s in known_skills]:
                category = self._categorize_skill(token_clean)
                if category not in skills:
                    skills[category] = []
                skills[category].append(token_clean)
        
        return skills
    
    def _conservative_skill_extraction(self, text: str) -> Dict[str, List[str]]:
        """Conservative skill extraction for lower-confidence sections."""
        skills = {}
        
        # Only extract well-formatted skills
        patterns = [
            r'\b(?:Python|Java|JavaScript|C\+\+|HTML|CSS|SQL|PHP|Ruby|Go|Swift|Kotlin)\b',  # Programming languages
            r'\b(?:Microsoft Office|Excel|PowerPoint|Word|Outlook|Photoshop|Illustrator)\b',  # Software
            r'\b(?:AWS|Azure|Google Cloud|Docker|Kubernetes|Jenkins|Git|GitHub)\b',  # Cloud/DevOps
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                category = self._categorize_skill(match)
                if category not in skills:
                    skills[category] = []
                skills[category].append(match.title())
        
        return skills
    
    def _parse_skills_from_text(self, text: str) -> List[str]:
        """Parse individual skills from text snippet."""
        # Remove common non-skill words
        text = re.sub(r'\b(?:and|or|with|using|including|such as|experience|in|of|the|a|an)\b', '', text, flags=re.IGNORECASE)
        
        # Split on common separators
        separators = r'[,;|•·▪▫‣⁃\n]'
        potential_skills = re.split(separators, text)
        
        skills = []
        for skill in potential_skills:
            skill = skill.strip()
            if len(skill) >= 2 and re.match(r'^[A-Za-z][A-Za-z0-9\s\+\#\.\-]*$', skill):
                skills.append(skill.title())
        
        return skills
    
    def _categorize_skill(self, skill: str) -> str:
        """Categorize a skill into appropriate category."""
        skill_lower = skill.lower()
        
        # Programming languages
        if skill_lower in ['python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'swift', 'kotlin', 'r', 'matlab']:
            return 'Programming Languages'
        
        # Databases
        if skill_lower in ['sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'sqlite']:
            return 'Databases'
        
        # Cloud platforms
        if any(cloud in skill_lower for cloud in ['aws', 'azure', 'google cloud', 'gcp']):
            return 'Cloud Platforms'
        
        # Default categorization
        if any(keyword in skill_lower for keyword in ['office', 'excel', 'word', 'powerpoint']):
            return 'Software & Applications'
        
        return 'Technical Skills'
    
    def _build_comprehensive_skills_database(self) -> Set[str]:
        """Build comprehensive database of known skills."""
        skills = set()
        
        # Add from existing databases
        for db in self.skill_databases.values():
            skills.update(db)
        
        # Add common skills
        common_skills = {
            # Programming
            'Python', 'Java', 'JavaScript', 'C++', 'C#', 'PHP', 'Ruby', 'Go', 'Swift', 'Kotlin',
            'R', 'MATLAB', 'Scala', 'Perl', 'Rust', 'TypeScript',
            
            # Web technologies
            'HTML', 'CSS', 'React', 'Angular', 'Vue.js', 'Node.js', 'Express.js', 'Django',
            'Flask', 'Spring', 'Bootstrap', 'jQuery',
            
            # Databases
            'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Oracle', 'SQLite', 'Redis', 'Elasticsearch',
            
            # Cloud & DevOps
            'AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes', 'Jenkins', 'Git', 'GitHub',
            'CI/CD', 'Terraform', 'Ansible',
            
            # Software
            'Microsoft Office', 'Excel', 'PowerPoint', 'Word', 'Outlook', 'Photoshop',
            'Illustrator', 'AutoCAD', 'SolidWorks', 'Tableau', 'Power BI',
            
            # Methodologies
            'Agile', 'Scrum', 'Kanban', 'DevOps', 'Machine Learning', 'Deep Learning',
            'Data Science', 'Big Data', 'AI', 'Analytics'
        }
        
        skills.update(common_skills)
        return skills
    
    def _merge_skill_results(self, skill_lists: List[Dict[str, List[str]]]) -> Dict[str, List[str]]:
        """Merge multiple skill extraction results."""
        merged = {}
        
        for skill_dict in skill_lists:
            for category, skills in skill_dict.items():
                if category not in merged:
                    merged[category] = []
                merged[category].extend(skills)
        
        return self._deduplicate_skills(merged)
    
    def _deduplicate_skills(self, skills_dict: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Remove duplicate skills while preserving order."""
        deduplicated = {}
        
        for category, skills in skills_dict.items():
            seen = set()
            unique_skills = []
            
            for skill in skills:
                skill_lower = skill.lower().strip()
                if skill_lower not in seen and len(skill.strip()) > 1:
                    seen.add(skill_lower)
                    unique_skills.append(skill.strip())
            
            if unique_skills:
                deduplicated[category] = unique_skills
        
        return deduplicated
    
    def _deduplicate_sections(self, sections: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        """Remove duplicate sections based on content similarity."""
        unique_sections = []
        
        for section_text, confidence in sections:
            is_duplicate = False
            
            for existing_text, existing_conf in unique_sections:
                similarity = SequenceMatcher(None, section_text, existing_text).ratio()
                if similarity > 0.7:  # 70% similarity threshold
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_sections.append((section_text, confidence))
        
        # Sort by confidence descending
        return sorted(unique_sections, key=lambda x: x[1], reverse=True)
    
    def _count_total_skills(self, skills_data: Dict[str, Any]) -> int:
        """Count total number of skills across all categories."""
        total = 0
        for category, skill_list in skills_data.items():
            if isinstance(skill_list, list):
                total += len(skill_list)
        return total
    
    def _print_extraction_summary(self, result: Dict[str, Any], original_text: str):
        """Print detailed extraction summary for development mode."""
        skills_data = result.get('skills', {})
        total_skills = self._count_total_skills(skills_data)
        
        print(f"\n📊 **ENHANCED EXTRACTION SUMMARY**")
        print(f"Total skills extracted: {total_skills}")
        print(f"Categories found: {len([k for k, v in skills_data.items() if v])}")
        
        print(f"\n📋 **SKILLS BY CATEGORY:**")
        for category, skill_list in skills_data.items():
            if skill_list:
                print(f"  {category}: {len(skill_list)} skills")
                for skill in skill_list[:3]:  # Show first 3 skills
                    print(f"    • {skill}")
                if len(skill_list) > 3:
                    print(f"    ... and {len(skill_list) - 3} more")

    # Keep all existing methods from the original SkillsExtractor
    def get_model(self):
        return Skills
    
    def get_prompt_template(self):
        """Get the prompt template for universal skills extraction."""
        return """
You are a comprehensive skills extractor that identifies ALL types of skills mentioned across ANY industry or field.

**EXTRACTION SOURCES - Look for skills in:**
1. **Skills section** - Any dedicated skills, competencies, or qualifications section
2. **Work experience descriptions** - Tools, techniques, skills, and competencies explicitly mentioned
3. **Project descriptions** - Methods, tools, technologies, and approaches used
4. **Education section** - Relevant coursework, certifications, techniques learned
5. **Certifications & Training** - Professional certifications and specialized training
6. **Achievements & Awards** - Skills demonstrated through accomplishments

**EXTRACTION RULES:**
✅ **DO EXTRACT when you see explicit mentions:**

**TECHNICAL SKILLS:**
- "Proficient in Python and JavaScript" → Extract: Python, JavaScript
- "Used Salesforce and HubSpot for CRM" → Extract: Salesforce, HubSpot
- "Experience with Adobe Creative Suite" → Extract: Adobe Creative Suite

**HEALTHCARE SKILLS:**
- "Performed phlebotomy and patient assessment" → Extract: Phlebotomy, Patient Assessment
- "Certified in CPR and First Aid" → Extract: CPR, First Aid
- "Used Epic EMR system" → Extract: Epic EMR

**BUSINESS & FINANCE:**
- "Conducted financial analysis using Excel" → Extract: Financial Analysis, Excel
- "Managed budgets and P&L statements" → Extract: Budget Management, P&L Analysis
- "Experience with QuickBooks and SAP" → Extract: QuickBooks, SAP

**MARKETING & SALES:**
- "Developed SEO strategies and Google Ads campaigns" → Extract: SEO, Google Ads
- "Used Hootsuite for social media management" → Extract: Hootsuite, Social Media Management
- "Conducted market research and competitor analysis" → Extract: Market Research, Competitor Analysis

**EDUCATION & TRAINING:**
- "Designed curriculum and lesson plans" → Extract: Curriculum Design, Lesson Planning
- "Used Blackboard and Canvas LMS" → Extract: Blackboard, Canvas LMS
- "Applied differentiated instruction techniques" → Extract: Differentiated Instruction

**OPERATIONS & LOGISTICS:**
- "Managed supply chain and inventory control" → Extract: Supply Chain Management, Inventory Control
- "Used Lean Six Sigma methodologies" → Extract: Lean Six Sigma
- "Operated forklifts and warehouse management systems" → Extract: Forklift Operation, Warehouse Management

**CREATIVE & DESIGN:**
- "Created graphics using Photoshop and Illustrator" → Extract: Photoshop, Illustrator
- "Developed brand identity and visual design" → Extract: Brand Identity, Visual Design
- "Used Figma for UI/UX design" → Extract: Figma, UI/UX Design

**SOFT SKILLS:**
- "Led cross-functional teams of 15+ members" → Extract: Team Leadership
- "Negotiated contracts worth $2M annually" → Extract: Contract Negotiation
- "Delivered presentations to C-level executives" → Extract: Executive Presentations

❌ **DO NOT EXTRACT when you see vague job titles or general descriptions:**
- "Software Engineer" → DO NOT assume programming languages
- "Marketing Manager" → DO NOT assume specific tools
- "Nurse" → DO NOT assume specific medical procedures
- "Managed projects" → DO NOT assume project management tools
- "Analyzed data" → DO NOT assume specific software

**SKILL CATEGORIES (Comprehensive):**

**Technical Skills:**
- Programming Languages (Python, Java, JavaScript, C#, R, etc.)
- Software & Applications (Microsoft Office, Adobe Suite, Salesforce, etc.)
- Databases (MySQL, Oracle, MongoDB, Access, etc.)
- Development Frameworks (React, Django, .NET, Spring, etc.)
- Cloud Platforms (AWS, Azure, Google Cloud, etc.)
- DevOps Tools (Docker, Kubernetes, Jenkins, Git, etc.)

**Industry-Specific Technical Skills:**
- Healthcare Software (Epic, Cerner, MEDITECH, AllScripts, etc.)
- Financial Software (Bloomberg Terminal, QuickBooks, SAP, Oracle Financials, etc.)
- Design Software (AutoCAD, SolidWorks, SketchUp, Revit, etc.)
- Marketing Tools (HubSpot, Marketo, Google Analytics, Hootsuite, etc.)
- Educational Technology (Canvas, Blackboard, Moodle, Smart Boards, etc.)

**Professional & Domain Skills:**
- Business Analysis (Requirements Gathering, Process Mapping, Stakeholder Management)
- Project Management (Agile, Scrum, Waterfall, Risk Management, etc.)
- Financial Skills (Financial Modeling, Budgeting, Forecasting, Auditing, etc.)
- Marketing Skills (SEO, SEM, Content Marketing, Brand Management, etc.)
- Sales Skills (Lead Generation, Account Management, Sales Presentations, etc.)
- HR Skills (Recruitment, Performance Management, Training & Development, etc.)

**Healthcare & Medical Skills:**
- Clinical Skills (Patient Assessment, Medication Administration, Wound Care, etc.)
- Medical Procedures (Phlebotomy, IV Insertion, Catheterization, etc.)
- Diagnostic Skills (X-ray Interpretation, Lab Analysis, EKG Reading, etc.)
- Specialized Medical (Surgery, Anesthesia, Physical Therapy, etc.)

**Certifications & Licenses:**
- Professional Certifications (PMP, CPA, CFA, CISSP, etc.)
- Medical Licenses (RN, MD, LPN, CNA, etc.)
- Technical Certifications (AWS Certified, Google Analytics, Salesforce Admin, etc.)
- Industry Certifications (Six Sigma, OSHA, Real Estate License, etc.)

**Soft Skills:**
- Leadership (Team Leadership, Change Management, Mentoring, etc.)
- Communication (Public Speaking, Technical Writing, Multilingual, etc.)
- Problem Solving (Critical Thinking, Root Cause Analysis, Troubleshooting, etc.)
- Interpersonal (Customer Service, Conflict Resolution, Relationship Building, etc.)

**Languages:**
- Human Languages (English, Spanish, Mandarin, etc.) with proficiency levels
- Programming Languages (when explicitly mentioned)

**Industry Knowledge:**
- Healthcare (Emergency Medicine, Pediatrics, Cardiology, etc.)
- Finance (Investment Banking, Risk Management, Insurance, etc.)
- Technology (Cybersecurity, Data Science, Machine Learning, etc.)
- Education (Special Education, STEM Education, Adult Learning, etc.)
- Manufacturing (Quality Control, Production Planning, Safety Management, etc.)

**VALIDATION PROCESS:**
For each skill, verify:
1. **Explicit mention**: Is the skill/tool/technique specifically named?
2. **Context clarity**: Can you identify where it was mentioned?
3. **Concrete skill**: Is it a specific skill rather than a job function?
4. **Industry relevance**: Does it make sense in the professional context?

**EXTRACTION PATTERNS TO RECOGNIZE:**
- "Certified in [skill/technology]"
- "Experience with [tool/software/method]"
- "Proficient in [language/software/technique]"
- "Used [tool] to [accomplish task]"
- "Managed [process/system/team]"
- "Developed [skill/capability/process]"
- "Applied [methodology/framework/approach]"
- "Operated [equipment/software/system]"
- "Licensed in [field/specialty]"
- "Trained in [method/procedure/technique]"

**INDUSTRY-SPECIFIC PATTERNS:**
- Healthcare: "Administered", "Diagnosed", "Treated", "Monitored"
- Finance: "Analyzed", "Forecasted", "Reconciled", "Audited"
- Education: "Taught", "Developed curriculum", "Assessed", "Facilitated"
- Sales: "Prospected", "Closed deals", "Generated leads", "Negotiated"
- Operations: "Optimized", "Streamlined", "Coordinated", "Scheduled"

**QUALITY ASSURANCE:**
- Prefer precision over recall (better to miss than hallucinate)
- Empty categories are acceptable if no relevant skills found
- Focus on HIGH CONFIDENCE extractions only
- Consider industry context when validating skills

**REMEMBER: Extract skills from ALL industries and fields, not just technology.**

{format_instructions}

Resume Text:
{text}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        return output
    
    def _load_skill_databases(self):
        # Keep the original skill databases
        return {
            'healthcare_software': {
                'epic', 'cerner', 'meditech', 'allscripts', 'athenahealth', 'nextgen',
                'emr', 'ehr', 'pacs', 'his', 'ris', 'cpoe'
            },
            'financial_software': {
                'bloomberg', 'reuters', 'factset', 'quickbooks', 'sap', 'oracle financials',
                'peoplesoft', 'hyperion', 'cognos', 'tableau', 'power bi'
            },
            'marketing_tools': {
                'hubspot', 'marketo', 'pardot', 'mailchimp', 'hootsuite', 'buffer',
                'google analytics', 'google ads', 'facebook ads', 'linkedin ads',
                'semrush', 'ahrefs', 'moz'
            },
            'design_software': {
                'autocad', 'solidworks', 'catia', 'fusion 360', 'revit', 'sketchup',
                'photoshop', 'illustrator', 'indesign', 'figma', 'sketch', 'adobe xd'
            },
            'medical_procedures': {
                'phlebotomy', 'iv insertion', 'catheterization', 'wound care',
                'medication administration', 'patient assessment', 'vital signs',
                'cpr', 'first aid', 'bls', 'acls', 'pals'
            },
            'business_skills': {
                'financial modeling', 'budget management', 'forecasting', 'auditing',
                'risk management', 'compliance', 'due diligence', 'valuation',
                'mergers and acquisitions', 'investment analysis'
            }
        }
    
    def _validate_skills_against_text(self, result: Dict[str, Any], original_text: str) -> Dict[str, Any]:
        """Enhanced validation with sliding window support."""
        skills_data = result.get('skills', {})
        validated_skills = {}
        text_lower = original_text.lower()
        
        for category, skill_list in skills_data.items():
            if isinstance(skill_list, list):
                validated_list = []
                seen_skills = set()
                
                for skill in skill_list:
                    if skill and (self._skill_exists_in_text(skill, text_lower, original_text) or 
                                self._skill_exists_fuzzy(skill, text_lower)):
                        skill_normalized = skill.lower().strip()
                        if skill_normalized not in seen_skills:
                            validated_list.append(skill)
                            seen_skills.add(skill_normalized)
                
                validated_skills[category] = validated_list
            else:
                validated_skills[category] = skill_list
        
        return {'skills': validated_skills}
    
    def _skill_exists_fuzzy(self, skill: str, text_lower: str) -> bool:
        """Check if skill exists using fuzzy matching for fragmented text."""
        skill_lower = skill.lower().strip()
        
        # Create sliding windows for fuzzy search
        windows = self._create_sliding_windows(text_lower)
        
        for window in windows:
            if self._skill_exists_in_window(skill_lower, window):
                return True
            
            # Fuzzy matching
            fuzzy_matches = self._find_fuzzy_matches(skill_lower, window)
            if fuzzy_matches:
                return True
        
        return False
    
    def _clean_and_categorize_skills(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Keep original cleaning method but integrate with new categories."""
        skills_data = result.get('skills', {})
        cleaned_skills = {}
        
        # Use enhanced categorization
        for category, skill_list in skills_data.items():
            if isinstance(skill_list, list):
                for skill in skill_list:
                    if skill:
                        best_category = self._categorize_skill(skill)
                        
                        if best_category not in cleaned_skills:
                            cleaned_skills[best_category] = []
                        
                        cleaned_skills[best_category].append(skill)
        
        # Remove empty categories and duplicates
        cleaned_skills = {k: list(dict.fromkeys(v)) for k, v in cleaned_skills.items() if v}
        
        return {'skills': cleaned_skills}