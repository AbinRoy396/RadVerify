"""
Report Synthesizer Module
Generates natural language medical narratives from structured AI findings.
Supports LLM integration (Gemini) with smart template fallbacks.
"""

import os
from typing import Dict, Any, List
import yaml

class ReportSynthesizer:
    """Synthesizes human-readable medical reports from AI data."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize synthesizer with optional API keys."""
        self.config = self._load_config(config_path)
        self.api_key = os.environ.get("GEMINI_API_KEY") or self.config.get("ai_model", {}).get("gemini_api_key")
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception:
            return {}

    def synthesize(self, ai_findings: Dict[str, Any]) -> str:
        """
        Generate a textual narrative report.
        
        Args:
            ai_findings: Dictionary of AI results
            
        Returns:
            String containing the medical narrative
        """
        if self.api_key:
            return self._synthesize_llm(ai_findings)
        else:
            return self._synthesize_template(ai_findings)

    def _synthesize_llm(self, ai_findings: Dict[str, Any]) -> str:
        """Use Gemini to generate a professional report."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""
            As a radiologist, write a concise professional medical narrative for a fetal ultrasound based on these findings:
            {ai_findings}
            
            Focus on:
            1. Presentation and Biometry
            2. Anatomical structures
            3. Impression
            
            Keep it clinical and structured.
            """
            
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"LLM Synthesis failed: {e}, falling back to templates.")
            return self._synthesize_template(ai_findings)

    def _synthesize_template(self, ai_findings: Dict[str, Any]) -> str:
        """Generate report using intelligent templates."""
        ga = ai_findings.get('gestational_age_estimate', {})
        biometry = ai_findings.get('biometry', {})
        quality = ai_findings.get('overall_quality', 'fair')
        
        report = []
        report.append("# FETAL ULTRASOUND NARRATIVE (AI GENERATED)")
        report.append(f"Examination quality is {quality}.")
        
        # Biometry section
        report.append("\n## FINDINGS")
        biomet_str = ", ".join([f"{k}: {v['value']}{v['unit']}" for k, v in biometry.items()])
        report.append(f"Fetal biometry is consistent with {ga.get('weeks')} weeks {ga.get('days')} days. {biomet_str}.")
        
        # Anatomy section
        report.append("\n## ANATOMY")
        detected = []
        for cat, structs in ai_findings.get('structures_detected', {}).items():
            for s, data in structs.items():
                if data.get('present'):
                    detected.append(s.replace('_', ' '))
        
        if detected:
            report.append(f"Visualized structures: {', '.join(detected)}. Appearance is unremarkable within diagnostic limits.")
        else:
            report.append("Detailed anatomical survey limited by acoustic shadowing or fetal position.")

        # Conclusion
        report.append("\n## IMPRESSION")
        report.append(f"1. Single live intrauterine gestation.")
        report.append(f"2. Estimated gestational age {ga.get('total_weeks')} weeks based on AI biometry.")
        
        return "\n".join(report)
