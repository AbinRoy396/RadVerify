"""
Verification Engine Module
Core comparison logic between AI findings and doctor's report findings.
"""

from typing import Dict, Any, List, Tuple


class VerificationEngine:
    """Compares AI findings with doctor's report to identify matches and mismatches."""
    
    # Confidence thresholds
    CONFIDENCE_HIGH = 0.8
    CONFIDENCE_MEDIUM = 0.5
    CONFIDENCE_LOW = 0.3
    
    # Measurement tolerance (in mm)
    MEASUREMENT_TOLERANCE = {
        'BPD': 2.0,
        'HC': 5.0,
        'AC': 5.0,
        'FL': 2.0
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize VerificationEngine.
        
        Args:
            config: Configuration dictionary
        """
        if config:
            self.confidence_thresholds = config.get('verification', {}).get('confidence_thresholds', {})
            self.measurement_tolerance = config.get('verification', {}).get('measurement_tolerance', {})
        else:
            self.confidence_thresholds = {
                'high': self.CONFIDENCE_HIGH,
                'medium': self.CONFIDENCE_MEDIUM,
                'low': self.CONFIDENCE_LOW
            }
            self.measurement_tolerance = self.MEASUREMENT_TOLERANCE
    
    def compare_measurements(self, ai_measurements: Dict[str, Any], 
                           doctor_measurements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare biometric measurements between AI and doctor.
        
        Args:
            ai_measurements: AI-detected measurements
            doctor_measurements: Doctor's measurements
            
        Returns:
            Comparison results
        """
        comparisons = {}
        
        for param in ['BPD', 'HC', 'AC', 'FL']:
            ai_data = ai_measurements.get(param, {})
            doctor_data = doctor_measurements.get(param, {})
            
            ai_value = ai_data.get('value')
            doctor_value = doctor_data.get('value')
            doctor_mentioned = doctor_data.get('mentioned', False)
            
            tolerance = self.measurement_tolerance.get(param, 2.0)
            
            if ai_value and doctor_value:
                # Both have values - check if within tolerance
                difference = abs(ai_value - doctor_value)
                within_tolerance = difference <= tolerance
                
                comparisons[param] = {
                    'status': 'match' if within_tolerance else 'mismatch',
                    'ai_value': ai_value,
                    'doctor_value': doctor_value,
                    'difference': round(difference, 2),
                    'tolerance': tolerance,
                    'severity': 'low' if within_tolerance else 'high'
                }
            elif ai_value and not doctor_mentioned:
                # AI detected but doctor didn't mention
                comparisons[param] = {
                    'status': 'omission',
                    'ai_value': ai_value,
                    'doctor_value': None,
                    'severity': 'medium'
                }
            elif not ai_value and doctor_mentioned and doctor_value:
                # Doctor mentioned but AI didn't detect
                comparisons[param] = {
                    'status': 'overstatement',
                    'ai_value': None,
                    'doctor_value': doctor_value,
                    'severity': 'medium'
                }
            else:
                # Neither detected
                comparisons[param] = {
                    'status': 'not_assessed',
                    'ai_value': None,
                    'doctor_value': None,
                    'severity': 'low'
                }
        
        return comparisons
    
    def compare_structures(self, ai_structures: Dict[str, Any], 
                          doctor_structures: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare anatomical structure findings.
        
        Args:
            ai_structures: AI-detected structures
            doctor_structures: Doctor's structure mentions
            
        Returns:
            Comparison results
        """
        comparisons = {}
        
        # Iterate through AI findings
        for category, structures in ai_structures.items():
            category_comparisons = {}
            
            for structure_name, ai_data in structures.items():
                ai_present = ai_data.get('present', False)
                ai_confidence = ai_data.get('confidence', 0)
                
                # Check if doctor mentioned this structure
                doctor_category = doctor_structures.get(category, {})
                doctor_mentioned = False
                doctor_negated = False
                
                # Look for mentions in doctor's report
                for keyword, doctor_data in doctor_category.items():
                    if structure_name.replace('_', ' ') in keyword or keyword in structure_name.replace('_', ' '):
                        doctor_mentioned = True
                        doctor_negated = doctor_data.get('negated', False)
                        break
                
                # Determine status
                if ai_present and ai_confidence >= self.confidence_thresholds['high']:
                    if doctor_mentioned and not doctor_negated:
                        status = 'match'
                        severity = 'low'
                    elif doctor_mentioned and doctor_negated:
                        status = 'mismatch'
                        severity = 'high'
                    elif not doctor_mentioned:
                        status = 'omission'
                        severity = 'medium'
                    else:
                        status = 'uncertain'
                        severity = 'low'
                elif not ai_present or ai_confidence < self.confidence_thresholds['high']:
                    if doctor_mentioned and not doctor_negated:
                        status = 'overstatement'
                        severity = 'medium'
                    else:
                        status = 'match'
                        severity = 'low'
                else:
                    status = 'uncertain'
                    severity = 'low'
                
                category_comparisons[structure_name] = {
                    'status': status,
                    'ai_present': ai_present,
                    'ai_confidence': ai_confidence,
                    'doctor_mentioned': doctor_mentioned,
                    'doctor_negated': doctor_negated,
                    'severity': severity
                }
            
            comparisons[category] = category_comparisons
        
        return comparisons
    
    def calculate_agreement_rate(self, measurement_comparisons: Dict[str, Any],
                                structure_comparisons: Dict[str, Any]) -> float:
        """
        Calculate overall agreement rate between AI and doctor.
        
        Args:
            measurement_comparisons: Measurement comparison results
            structure_comparisons: Structure comparison results
            
        Returns:
            Agreement rate (0-1)
        """
        total_items = 0
        agreements = 0
        
        # Count measurement agreements
        for comparison in measurement_comparisons.values():
            if comparison['status'] != 'not_assessed':
                total_items += 1
                if comparison['status'] == 'match':
                    agreements += 1
        
        # Count structure agreements
        for category in structure_comparisons.values():
            for comparison in category.values():
                total_items += 1
                if comparison['status'] == 'match':
                    agreements += 1
        
        if total_items == 0:
            return 0.0
        
        return agreements / total_items
    
    def assess_risk_level(self, agreement_rate: float) -> str:
        """
        Assess risk level based on agreement rate.
        
        Args:
            agreement_rate: Overall agreement rate
            
        Returns:
            Risk level ('low', 'medium', 'high')
        """
        if agreement_rate >= 0.85:
            return 'low'
        elif agreement_rate >= 0.70:
            return 'medium'
        else:
            return 'high'
    
    def verify(self, ai_findings: Dict[str, Any], 
              doctor_findings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete verification pipeline.
        
        Args:
            ai_findings: AI analysis results
            doctor_findings: Parsed doctor's report
            
        Returns:
            Complete verification results
        """
        # Compare measurements
        measurement_comparisons = self.compare_measurements(
            ai_findings.get('biometry', {}),
            doctor_findings.get('measurements', {})
        )
        
        # Compare structures
        structure_comparisons = self.compare_structures(
            ai_findings.get('structures_detected', {}),
            doctor_findings.get('structures', {})
        )
        
        # Calculate agreement rate
        agreement_rate = self.calculate_agreement_rate(
            measurement_comparisons,
            structure_comparisons
        )
        
        # Assess risk level
        risk_level = self.assess_risk_level(agreement_rate)
        
        # Count discrepancies by type
        discrepancies = {
            'matches': 0,
            'omissions': 0,
            'mismatches': 0,
            'overstatements': 0
        }
        
        for comparison in measurement_comparisons.values():
            status = comparison['status']
            if status in discrepancies:
                discrepancies[status + 's'] = discrepancies.get(status + 's', 0) + 1
            elif status == 'match':
                discrepancies['matches'] += 1
        
        for category in structure_comparisons.values():
            for comparison in category.values():
                status = comparison['status']
                if status == 'match':
                    discrepancies['matches'] += 1
                elif status == 'omission':
                    discrepancies['omissions'] += 1
                elif status == 'mismatch':
                    discrepancies['mismatches'] += 1
                elif status == 'overstatement':
                    discrepancies['overstatements'] += 1
        
        return {
            'measurement_comparisons': measurement_comparisons,
            'structure_comparisons': structure_comparisons,
            'agreement_rate': round(agreement_rate, 3),
            'risk_level': risk_level,
            'discrepancy_counts': discrepancies
        }
