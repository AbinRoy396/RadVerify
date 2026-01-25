"""
Input Handler Module
Validates and processes uploaded scan images and doctor's report text.
"""

from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from PIL import Image
import numpy as np


class InputHandler:
    """Handles validation and loading of input data."""
    
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.dcm'}
    MAX_IMAGE_SIZE_MB = 50
    MIN_IMAGE_SIZE = (100, 100)
    
    def __init__(self):
        """Initialize InputHandler."""
        self.errors = []
    
    def validate_image(self, image_file) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded image file.
        
        Args:
            image_file: Uploaded image file object
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if file exists
            if image_file is None:
                return False, "No image file provided"
            
            # Check file extension
            file_ext = Path(image_file.name).suffix.lower()
            if file_ext not in self.ALLOWED_IMAGE_EXTENSIONS:
                return False, f"Invalid file type. Allowed: {', '.join(self.ALLOWED_IMAGE_EXTENSIONS)}"
            
            # Check file size
            image_file.seek(0, 2)  # Seek to end
            file_size_mb = image_file.tell() / (1024 * 1024)
            image_file.seek(0)  # Reset to beginning
            
            if file_size_mb > self.MAX_IMAGE_SIZE_MB:
                return False, f"File too large. Maximum size: {self.MAX_IMAGE_SIZE_MB}MB"
            
            # Try to load image
            try:
                img = Image.open(image_file)
                img.verify()  # Verify it's a valid image
                image_file.seek(0)  # Reset after verify
                
                # Reload for size check
                img = Image.open(image_file)
                width, height = img.size
                
                if width < self.MIN_IMAGE_SIZE[0] or height < self.MIN_IMAGE_SIZE[1]:
                    return False, f"Image too small. Minimum size: {self.MIN_IMAGE_SIZE}"
                
                image_file.seek(0)  # Reset for future use
                
            except Exception as e:
                return False, f"Invalid or corrupted image file: {str(e)}"
            
            return True, None
            
        except Exception as e:
            return False, f"Error validating image: {str(e)}"
    
    def validate_report(self, report_text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate doctor's report text.
        
        Args:
            report_text: Text content of the report
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not report_text or not report_text.strip():
            return False, "Report text is empty"
        
        if len(report_text.strip()) < 50:
            return False, "Report text too short (minimum 50 characters)"
        
        if len(report_text) > 50000:
            return False, "Report text too long (maximum 50,000 characters)"
        
        return True, None
    
    def load_image(self, image_file) -> Tuple[Optional[np.ndarray], Optional[Dict[str, Any]]]:
        """
        Load image file into memory.
        
        Args:
            image_file: Image file object
            
        Returns:
            Tuple of (image_array, metadata)
        """
        try:
            # Validate first
            is_valid, error = self.validate_image(image_file)
            if not is_valid:
                raise ValueError(error)
            
            # Load image
            img = Image.open(image_file)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert to numpy array
            img_array = np.array(img)
            
            # Extract metadata
            metadata = {
                'filename': image_file.name,
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.size[0],
                'height': img.size[1],
                'channels': len(img.getbands())
            }
            
            return img_array, metadata
            
        except Exception as e:
            raise RuntimeError(f"Error loading image: {str(e)}")
    
    def process_inputs(self, image_file, report_text: str) -> Dict[str, Any]:
        """
        Process and validate all inputs.
        
        Args:
            image_file: Uploaded image file
            report_text: Doctor's report text
            
        Returns:
            Dictionary containing processed inputs and validation results
        """
        results = {
            'valid': True,
            'errors': [],
            'image_array': None,
            'image_metadata': None,
            'report_text': None
        }
        
        # Validate and load image
        is_valid, error = self.validate_image(image_file)
        if not is_valid:
            results['valid'] = False
            results['errors'].append(f"Image validation failed: {error}")
        else:
            try:
                img_array, metadata = self.load_image(image_file)
                results['image_array'] = img_array
                results['image_metadata'] = metadata
            except Exception as e:
                results['valid'] = False
                results['errors'].append(f"Image loading failed: {str(e)}")
        
        # Validate report
        is_valid, error = self.validate_report(report_text)
        if not is_valid:
            results['valid'] = False
            results['errors'].append(f"Report validation failed: {error}")
        else:
            results['report_text'] = report_text.strip()
        
        return results
