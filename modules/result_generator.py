"""
Result Generator Module
Formats verification results with human-readable explanations.
"""

from typing import Dict, Any


class ResultGenerator:
    """Generates final results and explanations."""
    
    def __init__(self):
        """Initialize ResultGenerator."""
        pass
    
    def generate_summary(self, comparisons: Dict[str, Any]) -> str:
        """
        Generate executive summary of verification results.
        
        Args:
            comparisons: Verification results
            
        Returns:
            Summary text
        """
        agreement_rate = comparisons.get('agreement_rate', 0) * 100
        risk_level = comparisons.get('risk_level', 'unknown')
        discrepancies = comparisons.get('discrepancy_counts', {})
        
        summary = f"""
VERIFICATION SUMMARY
====================

Agreement Rate: {agreement_rate:.1f}%
Risk Level: {risk_level.upper()}

Findings:
- Matches: {discrepancies.get('matches', 0)}
- Omissions: {discrepancies.get('omissions', 0)}
- Mismatches: {discrepancies.get('mismatches', 0)}
- Overstatements: {discrepancies.get('overstatements', 0)}

Recommendation: {'Minor review suggested' if risk_level == 'low' else 'Comprehensive review recommended' if risk_level == 'high' else 'Moderate review recommended'}
"""
        return summary.strip()
    
    def generate_detailed_explanations(self, comparisons: Dict[str, Any]) -> str:
        """
        Generate detailed explanations for discrepancies.
        
        Args:
            comparisons: Verification results
            
        Returns:
            Detailed explanations
        """
        explanations = []
        explanations.append("DETAILED EXPLANATIONS")
        explanations.append("=" * 60)
        explanations.append("")
        
        measurement_comparisons = comparisons.get('measurement_comparisons', {})
        
        # Explain measurement discrepancies
        for param, comp in measurement_comparisons.items():
            if comp['status'] in ['omission', 'mismatch', 'overstatement']:
                explanations.append(f"{param} {comp['status'].title()}:")
                
                if comp['status'] == 'omission':
                    explanations.append(
                        f"   The AI detected and measured {param} at {comp['ai_value']} mm, "
                        f"which is within normal range for mid-trimester gestation. This "
                        f"measurement was not mentioned in the doctor's report. This could be:"
                    )
                    explanations.append("   - An oversight in documentation")
                    explanations.append("   - Measurement was taken but not recorded")
                    explanations.append("   - Different reporting protocol")
                    explanations.append("")
                    explanations.append("   Recommendation: Verify measurement was performed and consider")
                    explanations.append("   adding to final report if confirmed.")
                
                elif comp['status'] == 'mismatch':
                    explanations.append(
                        f"   The AI measured {param} at {comp['ai_value']} mm, while the "
                        f"doctor's report indicates {comp['doctor_value']} mm. The difference "
                        f"of {comp.get('difference', 0)} mm exceeds the acceptable tolerance "
                        f"of {comp.get('tolerance', 0)} mm."
                    )
                    explanations.append("")
                    explanations.append("   Recommendation: Re-measure and verify the correct value.")
                
                explanations.append("")
                explanations.append("-" * 60)
                explanations.append("")
        
        if not any(comp['status'] in ['omission', 'mismatch', 'overstatement'] 
                  for comp in measurement_comparisons.values()):
            explanations.append("No significant measurement discrepancies found.")
            explanations.append("")
        
        return "\n".join(explanations)
    
    def format_results(self, ai_findings: Dict[str, Any],
                      doctor_findings: Dict[str, Any],
                      comparisons: Dict[str, Any],
                      comparison_report: str) -> Dict[str, Any]:
        """
        Format complete results package.
        
        Args:
            ai_findings: AI analysis results
            doctor_findings: Parsed doctor's report
            comparisons: Verification results
            comparison_report: Formatted comparison report
            
        Returns:
            Complete results package
        """
        return {
            'summary': self.generate_summary(comparisons),
            'detailed_explanations': self.generate_detailed_explanations(comparisons),
            'comparison_report': comparison_report,
            'verification_data': comparisons,
            'ai_findings': ai_findings,
            'doctor_findings': doctor_findings
        }
