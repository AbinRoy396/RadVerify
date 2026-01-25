"""
Comparison Report Module
Generates final comparison report comparing AI findings with doctor's report.
"""

from typing import Dict, Any, List
from datetime import datetime


class ComparisonReport:
    """Generates comprehensive comparison reports."""
    
    def __init__(self):
        """Initialize ComparisonReport."""
        pass
    
    def format_side_by_side_table(self, ai_findings: Dict[str, Any],
                                  doctor_findings: Dict[str, Any],
                                  comparisons: Dict[str, Any]) -> str:
        """
        Create side-by-side comparison table.
        
        Args:
            ai_findings: AI analysis results
            doctor_findings: Parsed doctor's report
            comparisons: Verification results
            
        Returns:
            Formatted table string
        """
        table = []
        table.append("┌─────────────────────────────────┬─────────────────────────────────┐")
        table.append("│      AI-GENERATED FINDINGS      │      DOCTOR'S REPORT FINDINGS   │")
        table.append("├─────────────────────────────────┼─────────────────────────────────┤")
        
        # Biometry section
        table.append("│ FETAL BIOMETRY:                 │ FETAL BIOMETRY:                 │")
        
        ai_biometry = ai_findings.get('biometry', {})
        doctor_measurements = doctor_findings.get('measurements', {})
        measurement_comparisons = comparisons.get('measurement_comparisons', {})
        
        for param in ['BPD', 'HC', 'AC', 'FL']:
            ai_data = ai_biometry.get(param, {})
            doctor_data = doctor_measurements.get(param, {})
            comparison = measurement_comparisons.get(param, {})
            
            ai_value = ai_data.get('value', 'Not measured')
            if isinstance(ai_value, (int, float)):
                ai_str = f"{ai_value} mm"
            else:
                ai_str = str(ai_value)
            
            doctor_value = doctor_data.get('value')
            if doctor_value:
                doctor_str = f"{doctor_value} mm"
            elif doctor_data.get('mentioned'):
                doctor_str = "Mentioned (no value)"
            else:
                doctor_str = "Not mentioned"
            
            # Add status indicator
            status = comparison.get('status', '')
            if status == 'match':
                indicator = '✓'
            elif status == 'mismatch':
                indicator = '✗'
            elif status == 'omission':
                indicator = '⚠'
            else:
                indicator = ' '
            
            ai_line = f"│ {indicator} {param}: {ai_str:<22} │"
            doctor_line = f" {param}: {doctor_str:<22} │"
            table.append(ai_line + doctor_line)
        
        table.append("└─────────────────────────────────┴─────────────────────────────────┘")
        
        return "\n".join(table)
    
    def format_mismatch_analysis(self, comparisons: Dict[str, Any]) -> str:
        """
        Format mismatch analysis section.
        
        Args:
            comparisons: Verification results
            
        Returns:
            Formatted mismatch analysis
        """
        sections = []
        
        measurement_comparisons = comparisons.get('measurement_comparisons', {})
        structure_comparisons = comparisons.get('structure_comparisons', {})
        
        # Agreements
        agreements = []
        for param, comp in measurement_comparisons.items():
            if comp['status'] == 'match':
                if comp.get('ai_value') and comp.get('doctor_value'):
                    diff = comp.get('difference', 0)
                    agreements.append(f"   • {param}: Both measured, difference {diff}mm (within tolerance)")
        
        for category, structures in structure_comparisons.items():
            for structure, comp in structures.items():
                if comp['status'] == 'match' and comp.get('ai_present'):
                    agreements.append(f"   • {structure.replace('_', ' ').title()}: Both report present")
        
        if agreements:
            sections.append("✅ AGREEMENTS (Items where AI and Doctor agree):")
            sections.extend(agreements[:10])  # Limit to 10 items
            if len(agreements) > 10:
                sections.append(f"   ... and {len(agreements) - 10} more")
        
        # Omissions
        omissions = []
        for param, comp in measurement_comparisons.items():
            if comp['status'] == 'omission':
                omissions.append(
                    f"   {len(omissions) + 1}. {param}: {comp['ai_value']} mm\n"
                    f"      - Severity: {comp['severity'].upper()}\n"
                    f"      - Recommendation: Verify if measurement was taken"
                )
        
        for category, structures in structure_comparisons.items():
            for structure, comp in structures.items():
                if comp['status'] == 'omission':
                    omissions.append(
                        f"   {len(omissions) + 1}. {structure.replace('_', ' ').title()}\n"
                        f"      - Severity: {comp['severity'].upper()}\n"
                        f"      - Recommendation: Confirm structure was assessed"
                    )
        
        if omissions:
            sections.append("\n⚠️ OMISSIONS (Items AI detected but Doctor didn't mention):")
            sections.extend(omissions[:5])  # Limit to 5 items
            if len(omissions) > 5:
                sections.append(f"   ... and {len(omissions) - 5} more")
        
        # Mismatches
        mismatches = []
        for param, comp in measurement_comparisons.items():
            if comp['status'] == 'mismatch':
                mismatches.append(
                    f"   {len(mismatches) + 1}. {param}: AI={comp['ai_value']}mm, Doctor={comp['doctor_value']}mm\n"
                    f"      - Difference: {comp.get('difference', 0)}mm (exceeds tolerance)\n"
                    f"      - Severity: {comp['severity'].upper()}"
                )
        
        for category, structures in structure_comparisons.items():
            for structure, comp in structures.items():
                if comp['status'] == 'mismatch':
                    mismatches.append(
                        f"   {len(mismatches) + 1}. {structure.replace('_', ' ').title()}\n"
                        f"      - AI: Present, Doctor: Negated\n"
                        f"      - Severity: {comp['severity'].upper()}"
                    )
        
        if mismatches:
            sections.append("\n❌ MISMATCHES (Contradictory findings):")
            sections.extend(mismatches)
        else:
            sections.append("\n❌ MISMATCHES (Contradictory findings):")
            sections.append("   [None detected]")
        
        # Overstatements
        overstatements = []
        for param, comp in measurement_comparisons.items():
            if comp['status'] == 'overstatement':
                overstatements.append(
                    f"   {len(overstatements) + 1}. {param}: Doctor mentioned but AI couldn't detect"
                )
        
        if overstatements:
            sections.append("\n⚠️ OVERSTATEMENTS (Items Doctor mentioned but AI couldn't detect):")
            sections.extend(overstatements)
        else:
            sections.append("\n⚠️ OVERSTATEMENTS (Items Doctor mentioned but AI couldn't detect):")
            sections.append("   [None detected]")
        
        return "\n".join(sections)
    
    def format_statistical_summary(self, comparisons: Dict[str, Any]) -> str:
        """
        Format statistical summary section.
        
        Args:
            comparisons: Verification results
            
        Returns:
            Formatted summary
        """
        agreement_rate = comparisons.get('agreement_rate', 0)
        risk_level = comparisons.get('risk_level', 'unknown')
        discrepancies = comparisons.get('discrepancy_counts', {})
        
        total_items = sum(discrepancies.values())
        
        summary = [
            f"Overall Agreement Rate: {agreement_rate * 100:.1f}%",
            f"Total Features Analyzed: {total_items}",
            f"  • Agreements: {discrepancies.get('matches', 0)}",
            f"  • Omissions: {discrepancies.get('omissions', 0)}",
            f"  • Mismatches: {discrepancies.get('mismatches', 0)}",
            f"  • Overstatements: {discrepancies.get('overstatements', 0)}",
            "",
            f"Risk Level: {risk_level.upper()}",
        ]
        
        # Add recommendation
        if risk_level == 'low':
            summary.append("Recommendation: Minor review suggested for documentation completeness")
        elif risk_level == 'medium':
            summary.append("Recommendation: Moderate review recommended to address discrepancies")
        else:
            summary.append("Recommendation: Comprehensive review required - significant discrepancies found")
        
        return "\n".join(summary)
    
    def generate_comparison_report(self, ai_findings: Dict[str, Any],
                                  doctor_findings: Dict[str, Any],
                                  comparisons: Dict[str, Any],
                                  enhanced_image_metadata: Dict[str, Any] = None) -> str:
        """
        Generate complete comparison report.
        
        Args:
            ai_findings: AI analysis results
            doctor_findings: Parsed doctor's report
            comparisons: Verification results
            enhanced_image_metadata: Image enhancement metadata
            
        Returns:
            Complete formatted report
        """
        report_lines = []
        
        # Header
        report_lines.append("RADIOLOGY REPORT VERIFICATION - COMPARISON ANALYSIS")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        # Scan information
        report_lines.append("SCAN INFORMATION:")
        report_lines.append("- Examination Type: Fetal Anatomy Survey (Mid-Trimester)")
        report_lines.append(f"- Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if enhanced_image_metadata:
            image_quality = "Enhanced"
        else:
            image_quality = "Original"
        report_lines.append(f"- Image Quality: {image_quality}")
        report_lines.append("")
        report_lines.append("━" * 60)
        report_lines.append("")
        
        # Section 1: Side-by-side comparison
        report_lines.append("SECTION 1: SIDE-BY-SIDE COMPARISON")
        report_lines.append("")
        report_lines.append(self.format_side_by_side_table(ai_findings, doctor_findings, comparisons))
        report_lines.append("")
        report_lines.append("━" * 60)
        report_lines.append("")
        
        # Section 2: Mismatch analysis
        report_lines.append("SECTION 2: MISMATCH ANALYSIS")
        report_lines.append("")
        report_lines.append(self.format_mismatch_analysis(comparisons))
        report_lines.append("")
        report_lines.append("━" * 60)
        report_lines.append("")
        
        # Section 3: Statistical summary
        report_lines.append("SECTION 3: STATISTICAL SUMMARY")
        report_lines.append("")
        report_lines.append(self.format_statistical_summary(comparisons))
        report_lines.append("")
        report_lines.append("━" * 60)
        report_lines.append("")
        
        # Disclaimer
        report_lines.append("DISCLAIMER:")
        report_lines.append("This comparison is generated by AI for verification purposes only.")
        report_lines.append("It does not constitute medical advice or diagnosis. All findings should")
        report_lines.append("be reviewed by qualified medical professionals. The AI system is designed")
        report_lines.append("to assist in quality assurance, not replace clinical judgment.")
        report_lines.append("")
        report_lines.append("━" * 60)
        
        return "\n".join(report_lines)
    
    def generate_json_report(self, ai_findings: Dict[str, Any],
                            doctor_findings: Dict[str, Any],
                            comparisons: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate JSON format comparison report.
        
        Args:
            ai_findings: AI analysis results
            doctor_findings: Parsed doctor's report
            comparisons: Verification results
            
        Returns:
            Structured JSON report
        """
        return {
            'metadata': {
                'report_type': 'comparison_analysis',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            },
            'ai_findings': ai_findings,
            'doctor_findings': doctor_findings,
            'verification_results': comparisons,
            'summary': {
                'agreement_rate': comparisons.get('agreement_rate'),
                'risk_level': comparisons.get('risk_level'),
                'discrepancy_counts': comparisons.get('discrepancy_counts')
            }
        }
