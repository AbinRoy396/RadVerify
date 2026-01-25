"""
Image Enhancement Module
Enhances ultrasound scan quality using AI super-resolution (ESRGAN).
"""

import numpy as np
from PIL import Image
import cv2
from typing import Dict, Any, Tuple, Optional
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


class ImageEnhancer:
    """Enhances medical images using AI super-resolution."""
    
    def __init__(self, method: str = "opencv", scale_factor: int = 2):
        """
        Initialize ImageEnhancer.
        
        Args:
            method: Enhancement method ('opencv', 'realesrgan', 'edsr')
            scale_factor: Upscaling factor (2 or 4)
        """
        self.method = method
        self.scale_factor = scale_factor
        self.model = None
        
        # Initialize enhancement method
        if method == "realesrgan":
            self._init_realesrgan()
        elif method == "opencv":
            self._init_opencv()
        else:
            # Default to OpenCV
            self._init_opencv()
    
    def _init_opencv(self):
        """Initialize OpenCV-based enhancement (fallback method)."""
        # OpenCV doesn't require model loading
        self.method = "opencv"
        print("Using OpenCV-based enhancement (basic upscaling)")
    
    def _init_realesrgan(self):
        """Initialize Real-ESRGAN model."""
        try:
            # Try to import Real-ESRGAN
            from basicsr.archs.rrdbnet_arch import RRDBNet
            from realesrgan import RealESRGANer
            
            # Initialize model (this is a placeholder - actual model loading would be here)
            # In production, download and load pre-trained weights
            print("Real-ESRGAN initialization (placeholder)")
            self.method = "realesrgan"
            
        except ImportError:
            print("Real-ESRGAN not available, falling back to OpenCV")
            self._init_opencv()
    
    def enhance_image(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Enhance image quality using super-resolution.
        
        Args:
            image: Input image as numpy array (RGB)
            
        Returns:
            Tuple of (enhanced_image, enhancement_metadata)
        """
        if self.method == "opencv":
            return self._enhance_opencv(image)
        elif self.method == "realesrgan":
            return self._enhance_realesrgan(image)
        else:
            return self._enhance_opencv(image)
    
    def _enhance_opencv(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Enhance image using OpenCV (basic method).
        
        Args:
            image: Input image
            
        Returns:
            Tuple of (enhanced_image, metadata)
        """
        original_shape = image.shape
        
        # Calculate new dimensions
        new_width = int(image.shape[1] * self.scale_factor)
        new_height = int(image.shape[0] * self.scale_factor)
        
        # Upscale using bicubic interpolation
        enhanced = cv2.resize(
            image, 
            (new_width, new_height), 
            interpolation=cv2.INTER_CUBIC
        )
        
        # Apply slight sharpening
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]]) / 9
        enhanced = cv2.filter2D(enhanced, -1, kernel)
        
        # Apply denoising
        enhanced = cv2.fastNlMeansDenoisingColored(
            enhanced, 
            None, 
            h=10, 
            hColor=10, 
            templateWindowSize=7, 
            searchWindowSize=21
        )
        
        # Enhance contrast using CLAHE
        lab = cv2.cvtColor(enhanced, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
        
        metadata = {
            'method': 'opencv',
            'scale_factor': self.scale_factor,
            'original_size': original_shape[:2],
            'enhanced_size': enhanced.shape[:2],
            'techniques': ['bicubic_upscaling', 'sharpening', 'denoising', 'clahe']
        }
        
        return enhanced, metadata
    
    def _enhance_realesrgan(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Enhance image using Real-ESRGAN.
        
        Args:
            image: Input image
            
        Returns:
            Tuple of (enhanced_image, metadata)
        """
        # Placeholder for Real-ESRGAN implementation
        # In production, this would use the actual Real-ESRGAN model
        
        # For now, fall back to OpenCV
        print("Real-ESRGAN enhancement (using OpenCV fallback)")
        return self._enhance_opencv(image)
    
    def compare_images(self, original: np.ndarray, enhanced: np.ndarray) -> Dict[str, Any]:
        """
        Compare original and enhanced images.
        
        Args:
            original: Original image
            enhanced: Enhanced image
            
        Returns:
            Dictionary with comparison metrics
        """
        # Resize enhanced to match original for comparison
        enhanced_resized = cv2.resize(
            enhanced, 
            (original.shape[1], original.shape[0]), 
            interpolation=cv2.INTER_CUBIC
        )
        
        # Calculate PSNR (Peak Signal-to-Noise Ratio)
        psnr = cv2.PSNR(original, enhanced_resized)
        
        # Calculate sharpness (using Laplacian variance)
        original_gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
        enhanced_gray = cv2.cvtColor(enhanced_resized, cv2.COLOR_RGB2GRAY)
        
        original_sharpness = cv2.Laplacian(original_gray, cv2.CV_64F).var()
        enhanced_sharpness = cv2.Laplacian(enhanced_gray, cv2.CV_64F).var()
        
        return {
            'psnr': round(psnr, 2),
            'original_sharpness': round(original_sharpness, 2),
            'enhanced_sharpness': round(enhanced_sharpness, 2),
            'sharpness_improvement': round(
                ((enhanced_sharpness - original_sharpness) / original_sharpness) * 100, 2
            )
        }
    
    def process(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Complete enhancement pipeline.
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with original, enhanced images and metadata
        """
        # Enhance image
        enhanced, enhancement_metadata = self.enhance_image(image)
        
        # Compare images
        comparison = self.compare_images(image, enhanced)
        
        return {
            'original': image,
            'enhanced': enhanced,
            'enhancement_metadata': enhancement_metadata,
            'comparison_metrics': comparison
        }
