"""
NLP Parser Module
Extracts structured meaning from doctor's radiology report text.
"""

import re
from typing import Dict, Any, List, Tuple
import warnings

warnings.filterwarnings('ignore')

# Try to import spaCy, fall back to basic NLP if not available
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("spaCy not available, using basic NLP")


class NLPParser:
    """Parses doctor's reports to extract structured findings."""
    
    # Negation keywords
    NEGATION_KEYWORDS = [
        'no', 'not', 'absent', 'negative', 'without', 'unremarkable',
        'no evidence of', 'fails to demonstrate', 'does not show'
    ]
    
    # Uncertainty keywords
    UNCERTAINTY_KEYWORDS = [
        'possible', 'probable', 'likely', 'suggests', 'may indicate',
        'appears', 'seems', 'questionable', 'uncertain'
    ]
    
    # Structure keywords mapping
    STRUCTURE_KEYWORDS = {
        'brain': ['brain', 'skull', 'cranium', 'ventricle', 'cerebellum', 'cavum septum pellucidum'],
        'heart': ['heart', 'cardiac', 'four-chamber', 'atrium', 'ventricle'],
        'spine': ['spine', 'spinal', 'vertebra', 'vertebrae'],
        'face': ['face', 'facial', 'profile', 'nasal bone', 'lip', 'lips'],
        'organs': ['stomach', 'kidney', 'kidneys', 'bladder', 'liver'],
        'limbs': ['arm', 'arms', 'leg', 'legs', 'hand', 'hands', 'foot', 'feet', 'limb', 'limbs'],
        'placenta': ['placenta', 'placental'],
        'amniotic_fluid': ['amniotic fluid', 'liquor', 'fluid volume'],
        'umbilical_cord': ['umbilical cord', 'cord']
    }
    
    # Biometry keywords
    BIOMETRY_KEYWORDS = {
        'BPD': ['bpd', 'biparietal diameter'],
        'HC': ['hc', 'head circumference'],
        'AC': ['ac', 'abdominal circumference'],
        'FL': ['fl', 'femur length', 'femoral length']
    }
    
    def __init__(self):
        """Initialize NLPParser."""
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except:
                print("spaCy model not loaded, using basic parsing")
    
    def extract_sentences(self, text: str) -> List[str]:
        """
        Extract sentences from text.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        if self.nlp:
            doc = self.nlp(text)
            return [sent.text.strip() for sent in doc.sents]
        else:
            # Basic sentence splitting
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]
    
    def detect_negation(self, sentence: str) -> bool:
        """
        Detect if sentence contains negation.
        
        Args:
            sentence: Input sentence
            
        Returns:
            True if negation detected
        """
        sentence_lower = sentence.lower()
        return any(keyword in sentence_lower for keyword in self.NEGATION_KEYWORDS)
    
    def detect_uncertainty(self, sentence: str) -> str:
        """
        Detect uncertainty level in sentence.
        
        Args:
            sentence: Input sentence
            
        Returns:
            Uncertainty level ('definite', 'possible', 'unlikely')
        """
        sentence_lower = sentence.lower()
        
        if any(keyword in sentence_lower for keyword in self.UNCERTAINTY_KEYWORDS):
            return 'possible'
        elif self.detect_negation(sentence):
            return 'unlikely'
        else:
            return 'definite'
    
    def extract_measurements(self, text: str) -> Dict[str, Any]:
        """
        Extract biometric measurements from text.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary of measurements
        """
        measurements = {}
        text_lower = text.lower()
        
        for param, keywords in self.BIOMETRY_KEYWORDS.items():
            for keyword in keywords:
                # Look for pattern like "BPD: 47.2 mm" or "biparietal diameter 47.2mm"
                pattern = rf'{keyword}[:\s]+(\d+\.?\d*)\s*mm'
                match = re.search(pattern, text_lower)
                
                if match:
                    value = float(match.group(1))
                    measurements[param] = {
                        'value': value,
                        'unit': 'mm',
                        'mentioned': True
                    }
                    break
            
            if param not in measurements:
                measurements[param] = {
                    'value': None,
                    'unit': 'mm',
                    'mentioned': False
                }
        
        return measurements
    
    def extract_structure_mentions(self, text: str) -> Dict[str, Any]:
        """
        Extract mentions of anatomical structures.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary of structure mentions
        """
        structure_mentions = {}
        sentences = self.extract_sentences(text)
        text_lower = text.lower()
        
        for category, keywords in self.STRUCTURE_KEYWORDS.items():
            category_findings = {}
            
            for keyword in keywords:
                if keyword in text_lower:
                    # Find sentences containing this keyword
                    relevant_sentences = [
                        sent for sent in sentences 
                        if keyword in sent.lower()
                    ]
                    
                    if relevant_sentences:
                        # Check for negation
                        negated = any(
                            self.detect_negation(sent) 
                            for sent in relevant_sentences
                        )
                        
                        # Check uncertainty
                        uncertainty = 'definite'
                        for sent in relevant_sentences:
                            sent_uncertainty = self.detect_uncertainty(sent)
                            if sent_uncertainty != 'definite':
                                uncertainty = sent_uncertainty
                                break
                        
                        category_findings[keyword] = {
                            'mentioned': True,
                            'negated': negated,
                            'uncertainty_level': uncertainty,
                            'relevant_sentences': relevant_sentences
                        }
            
            if category_findings:
                structure_mentions[category] = category_findings
        
        return structure_mentions
    
    def parse_report(self, report_text: str) -> Dict[str, Any]:
        """
        Complete parsing pipeline for doctor's report.
        
        Args:
            report_text: Doctor's report text
            
        Returns:
            Structured findings from the report
        """
        # Extract measurements
        measurements = self.extract_measurements(report_text)
        
        # Extract structure mentions
        structures = self.extract_structure_mentions(report_text)
        
        # Extract sentences for reference
        sentences = self.extract_sentences(report_text)
        
        return {
            'measurements': measurements,
            'structures': structures,
            'total_sentences': len(sentences),
            'raw_text': report_text
        }
    
    def summarize_findings(self, parsed_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize key findings from parsed report.
        
        Args:
            parsed_report: Parsed report data
            
        Returns:
            Summary of findings
        """
        measurements = parsed_report.get('measurements', {})
        structures = parsed_report.get('structures', {})
        
        # Count mentioned measurements
        mentioned_measurements = sum(
            1 for m in measurements.values() 
            if m.get('mentioned', False)
        )
        
        # Count mentioned structures
        mentioned_structures = sum(
            len(category) for category in structures.values()
        )
        
        # Count negated findings
        negated_findings = sum(
            1 for category in structures.values()
            for finding in category.values()
            if finding.get('negated', False)
        )
        
        return {
            'total_measurements_mentioned': mentioned_measurements,
            'total_structures_mentioned': mentioned_structures,
            'negated_findings_count': negated_findings,
            'has_measurements': mentioned_measurements > 0,
            'has_structure_descriptions': mentioned_structures > 0
        }
