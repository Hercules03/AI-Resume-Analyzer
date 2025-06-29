"""
Enhanced ProfileExtractor with sliding window approach and context detection
for handling complex PDF layouts and fragmented contact information.
"""
import re
from typing import Dict, Any, List, Tuple, Set, Optional, Type
from difflib import SequenceMatcher
from .base_extractor import BaseExtractor
from models import Profile


class ProfileExtractor(BaseExtractor):
    """Enhanced extractor with sliding window and context detection for profile information."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Sliding window configuration
        self.window_size = 150  # Smaller windows for contact info
        self.window_overlap = 40
        self.fuzzy_threshold = 0.75  # Slightly lower for names
        
        # Contact patterns and context detection
        self.contact_section_patterns = self._load_contact_section_patterns()
        self.contact_extraction_patterns = self._load_contact_extraction_patterns()
        self.name_patterns = self._load_name_patterns()
        
    def _load_contact_section_patterns(self) -> List[str]:
        """Load patterns that indicate contact/profile sections."""
        return [
            # Common contact section headers
            r'(?i)\bcontact\s+(?:info|information|details)?\b',
            r'(?i)\bpersonal\s+(?:info|information|details)\b',
            r'(?i)\bprofile\s+(?:info|information)?\b',
            r'(?i)\bget\s+in\s+touch\b',
            r'(?i)\breach\s+(?:me|out)\b',
            r'(?i)\bcontact\s+me\b',
            
            # Header at top of resume
            r'(?i)^[A-Z][a-z]+\s+[A-Z][a-z]+',  # Likely name at start
            
            # Fragmented patterns (for broken extraction)
            r'(?i)cont\s*act',
            r'(?i)per\s*son\s*al',
            r'(?i)prof\s*ile',
            r'(?i)info\s*rm\s*ation',
            
            # Email/phone indicators
            r'(?i)\b(?:email|e-mail|mail)\b',
            r'(?i)\b(?:phone|tel|mobile|cell)\b',
            r'(?i)\b(?:address|location)\b',
            r'(?i)\b(?:linkedin|github|portfolio)\b',
        ]
    
    def _load_contact_extraction_patterns(self) -> Dict[str, List[str]]:
        """Load regex patterns for extracting specific contact information."""
        return {
            'email': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                r'(?i)(?:email|e-mail|mail):\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
                r'(?i)([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            ],
            'phone': [
                r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
                r'(?:\+?[1-9]\d{0,3}[-.\s]?)?\(?[0-9]{2,4}\)?[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}',
                r'(?i)(?:phone|tel|mobile|cell):\s*([\+\-\.\s\(\)\d]+)',
                r'(?i)(?:ph|tel|mob|cell)\.?\s*([\+\-\.\s\(\)\d]+)',
            ],
            'linkedin': [
                r'(?i)(?:linkedin\.com/in/|linkedin\.com/pub/)([A-Za-z0-9\-]+)',
                r'(?i)(?:linkedin|linked-in):\s*((?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-]+)',
                r'(?i)((?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-]+)',
            ],
            'github': [
                r'(?i)(?:github\.com/)([A-Za-z0-9\-]+)',
                r'(?i)github:\s*((?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9\-]+)',
                r'(?i)((?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9\-]+)',
            ],
            'portfolio': [
                r'(?i)portfolio:\s*((?:https?://)?[A-Za-z0-9\-\.]+\.[A-Za-z]{2,})',
                r'(?i)website:\s*((?:https?://)?[A-Za-z0-9\-\.]+\.[A-Za-z]{2,})',
                r'(?i)((?:https?://)?[A-Za-z0-9\-\.]+\.(?:com|org|net|io|dev|me|portfolio))',
            ],
            'address': [
                r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)',
                r'(?i)(?:address|location):\s*([^,\n]+(?:,\s*[^,\n]+)*)',
                r'[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}',  # City, State ZIP
            ]
        }
    
    def _load_name_patterns(self) -> List[str]:
        """Load patterns for extracting names."""
        return [
            # Full name patterns
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]*\.?)*\s+[A-Z][a-z]+)',  # First Last or First M. Last
            r'(?i)(?:name|candidate):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]*\.?)*\s+[A-Z][a-z]+)',
            
            # Name in header (first line)
            r'^([A-Z][A-Z\s]+)$',  # ALL CAPS name
            r'^([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',  # Title case
            
            # Name near contact info
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)(?=.*(?:@|\+|\(?\d{3}\)?))' # Name before email/phone
        ]
    
    def extract(self, extracted_text: str, development_mode: bool = False) -> Dict[str, Any]:
        """Enhanced extraction with sliding window and context detection."""
        # Get standard extraction first
        standard_result = super().extract(extracted_text, development_mode)
        
        if development_mode:
            print(f"🔍 Standard profile extraction results:")
            self._print_profile_summary(standard_result)
        
        # Apply enhanced extraction techniques
        enhanced_result = self._enhanced_profile_extraction(
            extracted_text, standard_result, development_mode
        )
        
        # Validate and clean results
        validated_result = self._validate_profile_data(enhanced_result, extracted_text)
        
        if development_mode:
            print(f"✨ Enhanced profile extraction results:")
            self._print_profile_summary(validated_result)
            self._print_extraction_analysis(validated_result, extracted_text)
        
        return validated_result
    
    def _enhanced_profile_extraction(self, text: str, standard_result: Dict[str, Any], 
                                   development_mode: bool = False) -> Dict[str, Any]:
        """Apply sliding window and context detection for profile information."""
        
        # Start with standard results
        profile_data = standard_result.get('profile', {}).copy()
        
        # Step 1: Sliding window approach
        sliding_window_data = self._sliding_window_profile_extraction(text, development_mode)
        
        # Step 2: Context detection approach
        context_data = self._context_detection_profile_extraction(text, development_mode)
        
        # Step 3: Pattern-based extraction (emails, phones, URLs)
        pattern_data = self._pattern_based_extraction(text, development_mode)
        
        # Step 4: Merge results intelligently
        merged_data = self._merge_profile_results([profile_data, sliding_window_data, context_data, pattern_data])
        
        return {'profile': merged_data}
    
    def _sliding_window_profile_extraction(self, text: str, development_mode: bool = False) -> Dict[str, Any]:
        """Extract profile information using sliding window approach."""
        
        if development_mode:
            print("🔄 Applying sliding window profile extraction...")
        
        # Create sliding windows
        windows = self._create_sliding_windows(text)
        
        # Extract profile data from each window
        window_data = {}
        
        for i, window in enumerate(windows):
            window_results = self._extract_profile_from_window(window)
            
            # Merge window results
            for field, value in window_results.items():
                if value and (field not in window_data or not window_data[field]):
                    window_data[field] = value
        
        if development_mode:
            found_fields = len([v for v in window_data.values() if v])
            print(f"  📊 Sliding window found {found_fields} profile fields across {len(windows)} windows")
        
        return window_data
    
    def _context_detection_profile_extraction(self, text: str, development_mode: bool = False) -> Dict[str, Any]:
        """Extract profile information using context detection."""
        
        if development_mode:
            print("🎯 Applying context detection profile extraction...")
        
        context_data = {}
        
        # Step 1: Find contact sections
        contact_sections = self._identify_contact_sections(text)
        
        # Step 2: Extract from identified sections
        for section_text, confidence in contact_sections:
            section_data = self._extract_from_contact_section(section_text, confidence)
            
            # Merge section results (prioritize higher confidence)
            for field, value in section_data.items():
                if value and (field not in context_data or not context_data[field]):
                    context_data[field] = value
        
        # Step 3: Extract name from document header
        header_name = self._extract_name_from_header(text)
        if header_name and not context_data.get('name'):
            context_data['name'] = header_name
        
        if development_mode:
            found_fields = len([v for v in context_data.values() if v])
            print(f"  🎯 Context detection found {found_fields} profile fields from {len(contact_sections)} sections")
        
        return context_data
    
    def _pattern_based_extraction(self, text: str, development_mode: bool = False) -> Dict[str, Any]:
        """Extract profile information using regex patterns."""
        
        if development_mode:
            print("🔍 Applying pattern-based extraction...")
        
        pattern_data = {}
        
        # Extract using specific patterns
        for field_type, patterns in self.contact_extraction_patterns.items():
            values = []
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else match[1] if len(match) > 1 else ''
                    
                    if match and self._validate_field_value(field_type, match):
                        values.append(match.strip())
            
            # Take the best match
            if values:
                pattern_data[field_type] = self._select_best_match(field_type, values)
        
        # Extract names using name patterns
        name_values = []
        for pattern in self.name_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                if self._validate_name(match):
                    name_values.append(match.strip())
        
        if name_values:
            pattern_data['name'] = self._select_best_name(name_values)
        
        if development_mode:
            found_fields = len([v for v in pattern_data.values() if v])
            print(f"  🔍 Pattern-based extraction found {found_fields} profile fields")
        
        return pattern_data
    
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
                for i in range(min(20, text_length - end)):
                    if text[end + i].isspace():
                        window = text[start:end + i]
                        break
            
            windows.append(window)
            start += self.window_size - self.window_overlap
            
            if start >= text_length:
                break
        
        return windows
    
    def _extract_profile_from_window(self, window: str) -> Dict[str, Any]:
        """Extract profile information from a single window."""
        window_data = {}
        
        # Extract using patterns
        for field_type, patterns in self.contact_extraction_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, window, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else match[1] if len(match) > 1 else ''
                    
                    if match and self._validate_field_value(field_type, match):
                        window_data[field_type] = match.strip()
                        break
                if field_type in window_data:
                    break
        
        # Extract name from window
        for pattern in self.name_patterns:
            matches = re.findall(pattern, window, re.MULTILINE)
            for match in matches:
                if self._validate_name(match):
                    window_data['name'] = match.strip()
                    break
            if 'name' in window_data:
                break
        
        return window_data
    
    def _identify_contact_sections(self, text: str) -> List[Tuple[str, float]]:
        """Identify sections that likely contain contact information."""
        contact_sections = []
        
        for pattern in self.contact_section_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
            
            for match in matches:
                # Extract section after the header
                start_pos = max(0, match.start() - 50)  # Include some context before
                section_end = self._find_contact_section_end(text, match.end())
                section_text = text[start_pos:section_end].strip()
                
                if len(section_text) > 10:  # Minimum section length
                    confidence = self._calculate_contact_section_confidence(match.group(), section_text)
                    contact_sections.append((section_text, confidence))
        
        # Add document header as potential contact section
        header_section = text[:300]  # First 300 characters
        if header_section.strip():
            confidence = self._calculate_header_confidence(header_section)
            contact_sections.append((header_section, confidence))
        
        # Sort by confidence and remove duplicates
        contact_sections = self._deduplicate_sections(contact_sections)
        
        return contact_sections
    
    def _find_contact_section_end(self, text: str, start_pos: int) -> int:
        """Find the end of a contact section."""
        # Look for next section header or significant content break
        patterns = [
            r'\n\s*\n\s*[A-Z]',  # Double newline followed by capital letter
            r'\n\s*(?:EXPERIENCE|EDUCATION|WORK|EMPLOYMENT|SKILLS|SUMMARY)',
            r'\n\s*\d{4}\s*[-–—]',  # Date patterns
        ]
        
        min_end = len(text)
        for pattern in patterns:
            match = re.search(pattern, text[start_pos:], re.IGNORECASE)
            if match:
                min_end = min(min_end, start_pos + match.start())
        
        # Fallback: limit to reasonable section length
        max_section_length = 400
        return min(min_end, start_pos + max_section_length)
    
    def _calculate_contact_section_confidence(self, header: str, content: str) -> float:
        """Calculate confidence that this is a contact section."""
        confidence = 0.3  # Base confidence
        
        # Boost confidence based on header quality
        if re.search(r'(?i)\bcontact\b', header):
            confidence += 0.4
        if re.search(r'(?i)\bprofile\b', header):
            confidence += 0.2
        if re.search(r'(?i)\bpersonal\b', header):
            confidence += 0.2
        
        # Boost confidence based on content patterns
        contact_indicators = [
            r'@',  # Email
            r'\b\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4}\b',  # Phone pattern
            r'(?i)\blinkedin\b',
            r'(?i)\bgithub\b',
            r'(?i)\.com\b',
        ]
        
        for pattern in contact_indicators:
            matches = len(re.findall(pattern, content))
            confidence += min(matches * 0.15, 0.3)
        
        return min(confidence, 1.0)
    
    def _calculate_header_confidence(self, header_text: str) -> float:
        """Calculate confidence that document header contains contact info."""
        confidence = 0.6  # Base confidence for document header
        
        # Boost for contact indicators
        if '@' in header_text:
            confidence += 0.2
        if re.search(r'\b\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4}\b', header_text):
            confidence += 0.2
        if re.search(r'(?i)(?:linkedin|github)', header_text):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _extract_from_contact_section(self, section_text: str, confidence: float) -> Dict[str, Any]:
        """Extract contact information from an identified contact section."""
        section_data = {}
        
        # Apply different extraction strategies based on confidence
        if confidence > 0.7:
            # High confidence: aggressive extraction
            section_data = self._aggressive_contact_extraction(section_text)
        else:
            # Lower confidence: conservative extraction
            section_data = self._conservative_contact_extraction(section_text)
        
        return section_data
    
    def _extract_name_from_header(self, text: str) -> Optional[str]:
        """Extract name from document header."""
        # Look at first few lines
        lines = text.split('\n')[:5]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip lines with obvious non-name content
            if any(indicator in line.lower() for indicator in ['resume', 'cv', 'curriculum', '@', 'phone', 'email']):
                continue
            
            # Check if line looks like a name
            for pattern in self.name_patterns:
                match = re.match(pattern, line)
                if match:
                    potential_name = match.group(1) if match.groups() else match.group(0)
                    if self._validate_name(potential_name):
                        return potential_name.strip()
        
        return None
    
    def _aggressive_contact_extraction(self, text: str) -> Dict[str, Any]:
        """Aggressive extraction for high-confidence contact sections."""
        data = {}
        
        # Extract all patterns with lower validation threshold
        for field_type, patterns in self.contact_extraction_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else match[1] if len(match) > 1 else ''
                    
                    if match:  # Relaxed validation
                        data[field_type] = match.strip()
                        break
                if field_type in data:
                    break
        
        return data
    
    def _conservative_contact_extraction(self, text: str) -> Dict[str, Any]:
        """Conservative extraction for lower-confidence sections."""
        data = {}
        
        # Only extract well-formatted contact information
        strict_patterns = {
            'email': [r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'],
            'phone': [r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'],
            'linkedin': [r'(?i)((?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-]+)'],
            'github': [r'(?i)((?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9\-]+)'],
        }
        
        for field_type, patterns in strict_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if self._validate_field_value(field_type, match):
                        data[field_type] = match.strip()
                        break
                if field_type in data:
                    break
        
        return data
    
    def _validate_field_value(self, field_type: str, value: str) -> bool:
        """Validate extracted field values."""
        value = value.strip()
        
        if field_type == 'email':
            return bool(re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$', value))
        
        elif field_type == 'phone':
            # Remove formatting and check digit count
            digits = re.sub(r'[^\d]', '', value)
            return len(digits) >= 10 and len(digits) <= 15
        
        elif field_type in ['linkedin', 'github', 'portfolio']:
            return len(value) > 10 and ('.' in value or '/' in value)
        
        elif field_type == 'address':
            return len(value) > 10 and any(char.isdigit() for char in value)
        
        return len(value) > 2
    
    def _validate_name(self, name: str) -> bool:
        """Validate extracted name."""
        name = name.strip()
        
        # Basic checks
        if len(name) < 3 or len(name) > 50:
            return False
        
        # Should contain at least first and last name
        parts = name.split()
        if len(parts) < 2:
            return False
        
        # Check for reasonable name pattern
        if not re.match(r'^[A-Za-z\s\.\-\']+$', name):
            return False
        
        # Exclude common non-name phrases
        exclude_patterns = [
            r'(?i)\b(?:resume|cv|curriculum|vitae|contact|phone|email|address)\b',
            r'(?i)\b(?:page|of|and|or|the|by|for|with|at|in|on)\b',
            r'\d',  # Contains digits
        ]
        
        for pattern in exclude_patterns:
            if re.search(pattern, name):
                return False
        
        return True
    
    def _select_best_match(self, field_type: str, values: List[str]) -> str:
        """Select the best match from multiple values."""
        if not values:
            return ''
        
        if len(values) == 1:
            return values[0]
        
        # For emails, prefer shorter, cleaner ones
        if field_type == 'email':
            values.sort(key=lambda x: (len(x), x.count('.')))
            return values[0]
        
        # For URLs, prefer https and complete URLs
        if field_type in ['linkedin', 'github', 'portfolio']:
            https_values = [v for v in values if v.startswith('https://')]
            if https_values:
                return https_values[0]
            
            complete_values = [v for v in values if v.startswith('http')]
            if complete_values:
                return complete_values[0]
        
        # For phone, prefer formatted numbers
        if field_type == 'phone':
            formatted = [v for v in values if '(' in v or '-' in v]
            if formatted:
                return formatted[0]
        
        # Default: return first value
        return values[0]
    
    def _select_best_name(self, names: List[str]) -> str:
        """Select the best name from multiple candidates."""
        if not names:
            return ''
        
        if len(names) == 1:
            return names[0]
        
        # Prefer names that:
        # 1. Are title case (not all caps)
        # 2. Have reasonable length
        # 3. Don't contain unusual characters
        
        def name_score(name):
            score = 0
            
            # Prefer title case
            if name.istitle():
                score += 3
            elif name.isupper():
                score -= 1
            
            # Prefer reasonable length
            if 5 <= len(name) <= 25:
                score += 2
            
            # Prefer 2-3 parts
            parts = name.split()
            if 2 <= len(parts) <= 3:
                score += 2
            
            return score
        
        names.sort(key=name_score, reverse=True)
        return names[0]
    
    def _merge_profile_results(self, profile_lists: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple profile extraction results."""
        merged = {}
        
        # Define priority order for conflicting values
        priority_fields = ['email', 'phone', 'name', 'linkedin', 'github', 'portfolio', 'address']
        
        for profile_dict in profile_lists:
            for field, value in profile_dict.items():
                if value and value.strip():
                    if field not in merged or not merged[field]:
                        merged[field] = value
                    elif field in priority_fields:
                        # Keep the longer/more complete value
                        if len(str(value)) > len(str(merged[field])):
                            merged[field] = value
        
        return merged
    
    def _validate_profile_data(self, result: Dict[str, Any], original_text: str) -> Dict[str, Any]:
        """Validate extracted profile data against original text."""
        profile_data = result.get('profile', {})
        validated_data = {}
        
        for field, value in profile_data.items():
            if value and self._field_exists_in_text(field, value, original_text):
                validated_data[field] = value
        
        return {'profile': validated_data}
    
    def _field_exists_in_text(self, field: str, value: str, text: str) -> bool:
        """Check if field value exists in original text."""
        text_lower = text.lower()
        value_lower = str(value).lower()
        
        if field == 'email':
            # For emails, check exact match
            return value_lower in text_lower
        
        elif field == 'phone':
            # For phones, check digits match
            value_digits = re.sub(r'[^\d]', '', str(value))
            text_digits = re.findall(r'\d+', text)
            return any(value_digits in digits for digits in text_digits)
        
        elif field == 'name':
            # For names, check if all parts exist
            name_parts = value_lower.split()
            return all(part in text_lower for part in name_parts if len(part) > 2)
        
        elif field in ['linkedin', 'github', 'portfolio']:
            # For URLs, check domain or username
            if 'linkedin.com' in value_lower:
                return 'linkedin' in text_lower
            elif 'github.com' in value_lower:
                return 'github' in text_lower
            else:
                return value_lower in text_lower
        
        else:
            # Default: fuzzy match
            return value_lower in text_lower
    
    def _deduplicate_sections(self, sections: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        """Remove duplicate sections based on content similarity."""
        unique_sections = []
        
        for section_text, confidence in sections:
            is_duplicate = False
            
            for existing_text, existing_conf in unique_sections:
                similarity = SequenceMatcher(None, section_text, existing_text).ratio()
                if similarity > 0.6:  # 60% similarity threshold
                    is_duplicate = True
                    # Keep the one with higher confidence
                    if confidence > existing_conf:
                        unique_sections.remove((existing_text, existing_conf))
                        unique_sections.append((section_text, confidence))
                    break
            
            if not is_duplicate:
                unique_sections.append((section_text, confidence))
        
        # Sort by confidence descending
        return sorted(unique_sections, key=lambda x: x[1], reverse=True)
    
    def _print_profile_summary(self, result: Dict[str, Any]):
        """Print profile extraction summary."""
        profile_data = result.get('profile', {})
        
        found_fields = []
        for field, value in profile_data.items():
            if value:
                found_fields.append(f"{field}: {value}")
        
        if found_fields:
            print(f"  Found {len(found_fields)} profile fields:")
            for field in found_fields:
                print(f"    • {field}")
        else:
            print("  No profile fields found")
    
    def _print_extraction_analysis(self, result: Dict[str, Any], original_text: str):
        """Print detailed extraction analysis."""
        profile_data = result.get('profile', {})
        
        print(f"\n📊 **PROFILE EXTRACTION ANALYSIS**")
        print(f"Text length: {len(original_text)} characters")
        print(f"Profile fields extracted: {len([v for v in profile_data.values() if v])}")
        
        # Check what's missing
        expected_fields = ['name', 'email', 'phone', 'linkedin', 'github']
        missing_fields = [field for field in expected_fields if not profile_data.get(field)]
        
        if missing_fields:
            print(f"Missing fields: {', '.join(missing_fields)}")
        
        # Estimate completeness
        completeness = (len([v for v in profile_data.values() if v]) / len(expected_fields)) * 100
        print(f"Profile completeness: {completeness:.1f}%")

    # Keep original methods
    def get_model(self) -> Type[Profile]:
        """Get the Pydantic model for profile extraction."""
        return Profile
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for profile extraction."""
        return """
You are an assistant that extracts personal/profile information from resume text.
Focus on contact information, personal details, and online profiles.

Extract the following information if available:
- Full name
- Contact number/phone
- Email address
- Physical address details (address, city, state, country, postal code)
- Online profiles (LinkedIn, GitHub, portfolio)
- Personal information (nationality, date of birth)

Return your output as a JSON object with the schema provided below.
Use null for any field that cannot be found in the resume.

{format_instructions}

Resume Text:
{text}
"""
    
    def process_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Process the profile extraction output."""
        return output