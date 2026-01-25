"""
Main Pipeline Module
Orchestrates the complete verification workflow.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml

from modules.input_handler import InputHandler
from modules.image_enhancer import ImageEnhancer
from modules.image_processor import ImageProcessor
from modules.ai_analyzer import AIAnalyzer
from modules.report_generator import ReportGenerator
from modules.nlp_parser import NLPParser
from modules.verification_engine import VerificationEngine
from modules.comparison_report import ComparisonReport
from modules.result_generator import ResultGenerator


class RadVerifyPipeline:
    """Main pipeline for radiology report verification."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize pipeline with configuration.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize modules
        self.input_handler = InputHandler()
        
        enhancement_config = self.config.get('image_processing', {}).get('enhancement', {})
        self.image_enhancer = ImageEnhancer(
            method=enhancement_config.get('method', 'opencv'),
            scale_factor=enhancement_config.get('scale_factor', 2)
        )
        
        img_proc_config = self.config.get('image_processing', {})
        self.image_processor = ImageProcessor(
            target_size=tuple(img_proc_config.get('target_size', [512, 512])),
            normalize=img_proc_config.get('normalize', True)
        )
        
        ai_config = self.config.get('ai_model', {})
        self.ai_analyzer = AIAnalyzer(
            model_name=ai_config.get('model_name', 'efficientnet-b0'),
            confidence_threshold=ai_config.get('confidence_threshold', 0.8)
        )
        
        self.report_generator = ReportGenerator()
        self.nlp_parser = NLPParser()
        self.verification_engine = VerificationEngine(self.config)
        self.comparison_report = ComparisonReport()
        self.result_generator = ResultGenerator()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Config file not found: {config_path}, using defaults")
            return {}
    
    def process(self, image_file, doctor_report_text: str, 
                enhance_image: bool = True) -> Dict[str, Any]:
        """
        Complete verification pipeline.
        
        Args:
            image_file: Uploaded ultrasound image file
            doctor_report_text: Doctor's report text
            enhance_image: Whether to enhance the image
            
        Returns:
            Complete results package
        """
        results = {
            'success': False,
            'errors': [],
            'stage': 'initialization'
        }
        
        try:
            # Stage 1: Input validation and loading
            results['stage'] = 'input_validation'
            input_results = self.input_handler.process_inputs(image_file, doctor_report_text)
            
            if not input_results['valid']:
                results['errors'] = input_results['errors']
                return results
            
            image_array = input_results['image_array']
            report_text = input_results['report_text']
            
            # Stage 2: Image enhancement (optional)
            enhanced_image = None
            enhancement_metadata = None
            
            if enhance_image:
                results['stage'] = 'image_enhancement'
                enhancement_results = self.image_enhancer.process(image_array)
                enhanced_image = enhancement_results['enhanced']
                enhancement_metadata = enhancement_results['enhancement_metadata']
                comparison_metrics = enhancement_results['comparison_metrics']
                
                results['enhancement_metrics'] = comparison_metrics
            
            # Stage 3: Image preprocessing
            results['stage'] = 'image_preprocessing'
            # Use enhanced image if available, otherwise original
            image_to_process = enhanced_image if enhanced_image is not None else image_array
            processed_image, preprocessing_metadata = self.image_processor.preprocess(
                image_to_process,
                grayscale=False,
                denoise=True
            )
            
            # Stage 4: AI analysis
            results['stage'] = 'ai_analysis'
            ai_findings = self.ai_analyzer.analyze(processed_image)
            
            # Stage 5: AI report generation
            results['stage'] = 'ai_report_generation'
            ai_report_text = self.report_generator.generate_report(ai_findings, format='text')
            ai_report_structured = self.report_generator.generate_structured_data(ai_findings)
            
            # Stage 6: NLP parsing of doctor's report
            results['stage'] = 'nlp_parsing'
            doctor_findings = self.nlp_parser.parse_report(report_text)
            doctor_summary = self.nlp_parser.summarize_findings(doctor_findings)
            
            # Stage 7: Verification and comparison
            results['stage'] = 'verification'
            verification_results = self.verification_engine.verify(ai_findings, doctor_findings)
            
            # Stage 8: Comparison report generation
            results['stage'] = 'comparison_report_generation'
            comparison_report_text = self.comparison_report.generate_comparison_report(
                ai_findings,
                doctor_findings,
                verification_results,
                enhancement_metadata
            )
            
            comparison_report_json = self.comparison_report.generate_json_report(
                ai_findings,
                doctor_findings,
                verification_results
            )
            
            # Stage 9: Final results formatting
            results['stage'] = 'results_formatting'
            final_results = self.result_generator.format_results(
                ai_findings,
                doctor_findings,
                verification_results,
                comparison_report_text
            )
            
            # Compile complete results
            results.update({
                'success': True,
                'stage': 'completed',
                'original_image': image_array,
                'enhanced_image': enhanced_image,
                'enhancement_metadata': enhancement_metadata,
                'preprocessing_metadata': preprocessing_metadata,
                'ai_findings': ai_findings,
                'ai_report_text': ai_report_text,
                'ai_report_structured': ai_report_structured,
                'doctor_findings': doctor_findings,
                'doctor_summary': doctor_summary,
                'verification_results': verification_results,
                'comparison_report_text': comparison_report_text,
                'comparison_report_json': comparison_report_json,
                'final_results': final_results
            })
            
            return results
            
        except Exception as e:
            results['errors'].append(f"Error in stage '{results['stage']}': {str(e)}")
            results['success'] = False
            return results


# Convenience function for quick usage
def verify_report(image_file, doctor_report_text: str, 
                 config_path: str = "config/config.yaml",
                 enhance_image: bool = True) -> Dict[str, Any]:
    """
    Quick verification function.
    
    Args:
        image_file: Ultrasound image file
        doctor_report_text: Doctor's report text
        config_path: Path to config file
        enhance_image: Whether to enhance image
        
    Returns:
        Verification results
    """
    pipeline = RadVerifyPipeline(config_path)
    return pipeline.process(image_file, doctor_report_text, enhance_image)
