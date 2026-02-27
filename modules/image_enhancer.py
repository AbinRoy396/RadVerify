"""
Image Enhancement Module
Enhances ultrasound scan quality using clarity filters + optional super-resolution.
"""

import numpy as np
from PIL import Image
import cv2
from typing import Dict, Any, Tuple, Optional
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


class ImageEnhancer:
    """Enhances medical images using clarity filters and super-resolution."""
    
    def __init__(
        self,
        method: str = "opencv",
        scale_factor: int = 2,
        model_path: Optional[str] = None,
        model_name: Optional[str] = None,
        tile: int = 0,
        tile_pad: int = 10,
        pre_pad: int = 0,
        use_half: Optional[bool] = None,
    ):
        """
        Initialize ImageEnhancer.
        
        Args:
            method: Enhancement method ('opencv', 'realesrgan', 'edsr')
            scale_factor: Upscaling factor (2 or 4)
            model_path: Optional path to SR model weights
            model_name: Optional SR model name (e.g., RealESRGAN_x2plus)
            tile: Tile size for SR (0 disables tiling)
            tile_pad: Padding for tiles
            pre_pad: Pre-padding for SR
            use_half: Force fp16 (True/False). None = auto
        """
        self.method = method
        self.scale_factor = scale_factor
        self.model_path = model_path
        self.model_name = model_name
        self.tile = tile
        self.tile_pad = tile_pad
        self.pre_pad = pre_pad
        self.use_half = use_half
        self.model = None
        self.realesrganer = None
        
        # Initialize enhancement method
        if method == "realesrgan":
            self._init_realesrgan()
        elif method == "edsr":
            self._init_edsr()
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
            import torch
            from basicsr.archs.rrdbnet_arch import RRDBNet
            from realesrgan import RealESRGANer
            
            # Initialize model (this is a placeholder - actual model loading would be here)
            # In production, download and load pre-trained weights
            if not self.model_path:
                print("Real-ESRGAN weights not provided, falling back to OpenCV")
                return self._init_opencv()
            model_name = self.model_name or ("RealESRGAN_x2plus" if self.scale_factor == 2 else "RealESRGAN_x4plus")
            if "x2" in model_name:
                scale = 2
            else:
                scale = 4

            model = RRDBNet(
                num_in_ch=3,
                num_out_ch=3,
                num_feat=64,
                num_block=23,
                num_grow_ch=32,
                scale=scale
            )

            gpu_id = 0 if torch.cuda.is_available() else None
            use_half = self.use_half if self.use_half is not None else torch.cuda.is_available()
            self.realesrganer = RealESRGANer(
                scale=scale,
                model_path=self.model_path,
                model=model,
                tile=self.tile,
                tile_pad=self.tile_pad,
                pre_pad=self.pre_pad,
                half=use_half,
                gpu_id=gpu_id
            )
            self.method = "realesrgan"
            print(f"Using Real-ESRGAN {model_name} from {self.model_path}")
            
        except ImportError:
            print("Real-ESRGAN not available, falling back to OpenCV")
            self._init_opencv()
        except Exception:
            print("Real-ESRGAN initialization failed, falling back to OpenCV")
            self._init_opencv()

    def _init_edsr(self):
        """Initialize OpenCV DNN Super-Resolution (EDSR) if available."""
        try:
            if not self.model_path:
                print("EDSR weights not provided, falling back to OpenCV")
                return self._init_opencv()
            if not hasattr(cv2, "dnn_superres"):
                print("OpenCV dnn_superres not available, falling back to OpenCV")
                return self._init_opencv()
            sr = cv2.dnn_superres.DnnSuperResImpl_create()
            sr.readModel(self.model_path)
            sr.setModel("edsr", int(self.scale_factor))
            self.model = sr
            self.method = "edsr"
            print(f"Using EDSR super-resolution from {self.model_path}")
        except Exception:
            print("EDSR initialization failed, falling back to OpenCV")
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
        if self.method == "realesrgan":
            return self._enhance_realesrgan(image)
        if self.method == "edsr":
            return self._enhance_edsr(image)
        return self._enhance_opencv(image)

    def _to_uint8(self, image: np.ndarray) -> np.ndarray:
        if image.dtype == np.uint8:
            return image
        img = np.clip(image, 0, 1)
        return (img * 255).astype(np.uint8)

    def _apply_denoise(self, image: np.ndarray) -> np.ndarray:
        return cv2.fastNlMeansDenoisingColored(
            image,
            None,
            h=10,
            hColor=10,
            templateWindowSize=7,
            searchWindowSize=21
        )

    def _apply_clahe(self, image: np.ndarray) -> np.ndarray:
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        merged = cv2.merge([l, a, b])
        return cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)

    def _apply_unsharp_mask(self, image: np.ndarray) -> np.ndarray:
        blur = cv2.GaussianBlur(image, (0, 0), sigmaX=1.0)
        return cv2.addWeighted(image, 1.2, blur, -0.2, 0)

    def _clarity_pipeline(self, image: np.ndarray) -> np.ndarray:
        img = self._to_uint8(image)
        img = self._apply_denoise(img)
        img = self._apply_clahe(img)
        img = self._apply_unsharp_mask(img)
        return img
    
    def _enhance_opencv(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Enhance image using OpenCV (basic method).
        
        Args:
            image: Input image
            
        Returns:
            Tuple of (enhanced_image, metadata)
        """
        original_shape = image.shape
        
        # Clarity pipeline first (denoise + CLAHE + light unsharp mask)
        enhanced = self._clarity_pipeline(image)

        # Calculate new dimensions for super-resolution (bicubic)
        new_width = int(image.shape[1] * self.scale_factor)
        new_height = int(image.shape[0] * self.scale_factor)
        
        # Upscale using bicubic interpolation
        enhanced = cv2.resize(
            enhanced,
            (new_width, new_height),
            interpolation=cv2.INTER_CUBIC
        )
        
        metadata = {
            'method': 'opencv',
            'scale_factor': self.scale_factor,
            'original_size': original_shape[:2],
            'enhanced_size': enhanced.shape[:2],
            'techniques': [
                'denoising',
                'clahe',
                'unsharp_mask',
                'bicubic_upscaling'
            ]
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
        if self.realesrganer is None:
            print("Real-ESRGAN not initialized, using OpenCV fallback")
            return self._enhance_opencv(image)

        original_shape = image.shape
        clarified = self._clarity_pipeline(image)
        bgr = cv2.cvtColor(clarified, cv2.COLOR_RGB2BGR)
        try:
            output, _ = self.realesrganer.enhance(bgr, outscale=self.scale_factor)
            enhanced = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
        except Exception:
            print("Real-ESRGAN enhancement failed, using OpenCV fallback")
            return self._enhance_opencv(image)

        metadata = {
            'method': 'realesrgan',
            'scale_factor': self.scale_factor,
            'original_size': original_shape[:2],
            'enhanced_size': enhanced.shape[:2],
            'techniques': ['denoising', 'clahe', 'unsharp_mask', 'realesrgan_superres']
        }
        return enhanced, metadata

    def _enhance_edsr(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Enhance image using OpenCV DNN Super-Resolution (EDSR).
        """
        if self.model is None:
            return self._enhance_opencv(image)
        original_shape = image.shape
        clarified = self._clarity_pipeline(image)
        try:
            enhanced = self.model.upsample(clarified)
        except Exception:
            return self._enhance_opencv(image)

        metadata = {
            'method': 'edsr',
            'scale_factor': self.scale_factor,
            'original_size': original_shape[:2],
            'enhanced_size': enhanced.shape[:2],
            'techniques': ['denoising', 'clahe', 'unsharp_mask', 'edsr_superres']
        }
        return enhanced, metadata
    
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
        
        if original_sharpness > 0:
            sharpness_improvement = ((enhanced_sharpness - original_sharpness) / original_sharpness) * 100
        else:
            sharpness_improvement = 0.0

        return {
            'psnr': round(psnr, 2),
            'original_sharpness': round(original_sharpness, 2),
            'enhanced_sharpness': round(enhanced_sharpness, 2),
            'sharpness_improvement': round(sharpness_improvement, 2)
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
