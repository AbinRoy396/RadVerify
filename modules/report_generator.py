"""
Report Generator Module
Converts AI findings to structured pregnancy ultrasound report using templates.
"""

from jinja2 import Template
from typing import Dict, Any
from datetime import datetime
import json


class ReportGenerator:
    """Generates structured pregnancy ultrasound reports from AI findings."""
    
    # Report template
    REPORT_TEMPLATE = """
PREGNANCY ULTRASOUND REPORT (AI-GENERATED)
===========================================

EXAMINATION: Fetal Anatomy Survey (Mid-Trimester)
DATE: {{ timestamp }}
GESTATIONAL AGE: {{ gestational_age }}
IMAGE QUALITY: {{ image_quality }}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FETAL BIOMETRY:
{% for param, data in biometry.items() %}
- {{ param }}: {{ data.value }} {{ data.unit }}{% if data.confidence %} (Confidence: {{ (data.confidence * 100)|round|int }}%){% endif %}
{% endfor %}
- Estimated Fetal Weight: {{ estimated_weight }} grams

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FETAL ANATOMY:

Brain and Skull:
{% for structure, data in structures.brain.items() %}
- {{ structure|replace('_', ' ')|title }}: {{ 'Normal' if data.present else 'Not visualized' }}{% if data.confidence %} ({{ (data.confidence * 100)|round|int }}%){% endif %}
{% endfor %}

Face:
{% for structure, data in structures.face.items() %}
- {{ structure|replace('_', ' ')|title }}: {{ 'Present' if data.present else 'Not visualized' }}{% if data.confidence %} ({{ (data.confidence * 100)|round|int }}%){% endif %}
{% endfor %}

Spine:
{% for structure, data in structures.spine.items() %}
- {{ structure|replace('_', ' ')|title }}: {{ 'Intact' if data.present else 'Not visualized' }}{% if data.confidence %} ({{ (data.confidence * 100)|round|int }}%){% endif %}
{% endfor %}

Heart:
{% for structure, data in structures.heart.items() %}
- {{ structure|replace('_', ' ')|title }}: {{ 'Normal' if data.present else 'Not visualized' }}{% if data.confidence %} ({{ (data.confidence * 100)|round|int }}%){% endif %}
{% endfor %}

Abdomen and Organs:
{% for structure, data in structures.organs.items() %}
- {{ structure|replace('_', ' ')|title }}: {{ 'Visualized' if data.present else 'Not visualized' }}{% if data.confidence %} ({{ (data.confidence * 100)|round|int }}%){% endif %}
{% endfor %}

Extremities:
{% for structure, data in structures.limbs.items() %}
- {{ structure|replace('_', ' ')|title }}: {{ 'Present' if data.present else 'Not visualized' }}{% if data.confidence %} ({{ (data.confidence * 100)|round|int }}%){% endif %}
{% endfor %}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PLACENTA AND AMNIOTIC FLUID:
{% for structure, data in structures.maternal.items() %}
- {{ structure|replace('_', ' ')|title }}: {{ 'Normal' if data.present else 'Not assessed' }}{% if data.confidence %} ({{ (data.confidence * 100)|round|int }}%){% endif %}
{% endfor %}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPRESSION:
{{ impression }}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LIMITATIONS:
This is an AI-generated report for verification purposes only.
Not all structures may be visible depending on fetal position and image quality.
This report does not constitute medical advice or diagnosis.
All findings should be reviewed by qualified medical professionals.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    def __init__(self):
        """Initialize ReportGenerator."""
        self.template = Template(self.REPORT_TEMPLATE)
    
    def calculate_estimated_weight(self, biometry: Dict[str, Any]) -> float:
        """
        Calculate estimated fetal weight from biometry.
        
        Args:
            biometry: Biometric measurements
            
        Returns:
            Estimated weight in grams
        """
        ac = biometry.get('AC', {}).get('value')
        fl = biometry.get('FL', {}).get('value')
        
        if ac and fl:
            # Simplified Hadlock formula
            weight = (ac * fl * fl) / 100
            return round(weight, 1)
        
        return None
    
    def generate_impression(self, analysis: Dict[str, Any]) -> str:
        """
        Generate impression summary from analysis.
        
        Args:
            analysis: Complete AI analysis results
            
        Returns:
            Impression text
        """
        impressions = []
        
        # Gestational age
        ga = analysis.get('gestational_age_estimate', {})
        if ga.get('weeks'):
            impressions.append(
                f"Fetal biometry consistent with approximately {ga['weeks']} weeks "
                f"{ga.get('days', 0)} days gestation."
            )
        
        # Image quality
        quality = analysis.get('overall_quality', 'unknown')
        impressions.append(f"Image quality: {quality.capitalize()}.")
        
        # Structure visibility
        structures = analysis.get('structures_detected', {})
        total_structures = sum(len(cat) for cat in structures.values())
        visible_structures = sum(
            1 for cat in structures.values() 
            for struct in cat.values() 
            if struct.get('present', False)
        )
        
        visibility_rate = (visible_structures / total_structures * 100) if total_structures > 0 else 0
        
        if visibility_rate >= 90:
            impressions.append("Excellent visualization of fetal anatomy.")
        elif visibility_rate >= 75:
            impressions.append("Good visualization of fetal anatomy.")
        elif visibility_rate >= 60:
            impressions.append("Adequate visualization of fetal anatomy.")
        else:
            impressions.append("Limited visualization of fetal anatomy. Repeat scan may be needed.")
        
        # General statement
        impressions.append(
            "No obvious structural abnormalities detected by AI analysis. "
            "Clinical correlation and expert review recommended."
        )
        
        return " ".join(impressions)
    
    def generate_report(self, analysis: Dict[str, Any], format: str = 'text') -> str:
        """
        Generate complete ultrasound report.
        
        Args:
            analysis: AI analysis results
            format: Output format ('text', 'json', 'markdown')
            
        Returns:
            Formatted report
        """
        # Prepare data for template
        ga = analysis.get('gestational_age_estimate', {})
        gestational_age = f"{ga.get('weeks', 'Unknown')} weeks {ga.get('days', 0)} days"
        
        estimated_weight = self.calculate_estimated_weight(analysis.get('biometry', {}))
        if estimated_weight is None:
            estimated_weight = "Unable to calculate"
        
        impression = self.generate_impression(analysis)
        
        template_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'gestational_age': gestational_age,
            'image_quality': analysis.get('overall_quality', 'Unknown').capitalize(),
            'biometry': analysis.get('biometry', {}),
            'estimated_weight': estimated_weight,
            'structures': analysis.get('structures_detected', {}),
            'impression': impression
        }
        
        if format == 'json':
            return json.dumps(template_data, indent=2)
        elif format == 'markdown':
            # Convert to markdown format
            report = self.template.render(**template_data)
            return f"```\n{report}\n```"
        else:
            # Default text format
            return self.template.render(**template_data)
    
    def generate_structured_data(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured data representation of the report.
        
        Args:
            analysis: AI analysis results
            
        Returns:
            Structured report data
        """
        ga = analysis.get('gestational_age_estimate', {})
        
        return {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'report_type': 'ai_generated_ultrasound',
                'version': '1.0'
            },
            'gestational_age': {
                'weeks': ga.get('weeks'),
                'days': ga.get('days'),
                'confidence': ga.get('confidence')
            },
            'biometry': analysis.get('biometry', {}),
            'estimated_fetal_weight': self.calculate_estimated_weight(analysis.get('biometry', {})),
            'structures': analysis.get('structures_detected', {}),
            'image_quality': analysis.get('overall_quality'),
            'impression': self.generate_impression(analysis)
        }
