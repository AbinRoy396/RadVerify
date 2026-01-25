"""
Image Processor Module
Prepares medical scans for AI analysis.
"""

import numpy as np
import cv2
from typing import Tuple, Dict, Any


class ImageProcessor:
    """Preprocesses images for AI model input."""
    
    def __init__(self, target_size: Tuple[int, int] = (512, 512), normalize: bool = True):
        """
        Initialize ImageProcessor.
        
        Args:
            target_size: Target image dimensions (width, height)
            normalize: Whether to normalize pixel values to [0, 1]
        """
        self.target_size = target_size
        self.normalize = normalize
    
    def resize_image(self, image: np.ndarray) -> np.ndarray:
        """
        Resize image to target size.
        
        Args:
            image: Input image
            
        Returns:
            Resized image
        """
        return cv2.resize(image, self.target_size, interpolation=cv2.INTER_AREA)
    
    def normalize_image(self, image: np.ndarray) -> np.ndarray:
        """
        Normalize pixel values to [0, 1] range.
        
        Args:
            image: Input image
            
        Returns:
            Normalized image
        """
        return image.astype(np.float32) / 255.0
    
    def apply_gaussian_blur(self, image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
        """
        Apply Gaussian blur for noise reduction.
        
        Args:
            image: Input image
            kernel_size: Size of Gaussian kernel
            
        Returns:
            Blurred image
        """
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    
    def convert_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """
        Convert image to grayscale.
        
        Args:
            image: Input RGB image
            
        Returns:
            Grayscale image
        """
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    def preprocess(self, image: np.ndarray, grayscale: bool = False, 
                   denoise: bool = False) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Complete preprocessing pipeline.
        
        Args:
            image: Input image
            grayscale: Convert to grayscale
            denoise: Apply denoising
            
        Returns:
            Tuple of (preprocessed_image, metadata)
        """
        original_shape = image.shape
        processed = image.copy()
        
        steps = []
        
        # Resize
        processed = self.resize_image(processed)
        steps.append('resize')
        
        # Denoise if requested
        if denoise:
            processed = self.apply_gaussian_blur(processed)
            steps.append('denoise')
        
        # Convert to grayscale if requested
        if grayscale:
            processed = self.convert_to_grayscale(processed)
            steps.append('grayscale')
        
        # Normalize
        if self.normalize:
            processed = self.normalize_image(processed)
            steps.append('normalize')
        
        metadata = {
            'original_shape': original_shape,
            'processed_shape': processed.shape,
            'target_size': self.target_size,
            'preprocessing_steps': steps,
            'normalized': self.normalize,
            'grayscale': grayscale
        }
        
        return processed, metadata
    
    def prepare_for_model(self, image: np.ndarray) -> np.ndarray:
        """
        Prepare image for model input (add batch dimension).
        
        Args:
            image: Preprocessed image
            
        Returns:
            Image with batch dimension
        """
        # Add batch dimension
        if len(image.shape) == 2:
            # Grayscale: (H, W) -> (1, H, W, 1)
            return np.expand_dims(np.expand_dims(image, axis=0), axis=-1)
        else:
            # RGB: (H, W, C) -> (1, H, W, C)
            return np.expand_dims(image, axis=0)
