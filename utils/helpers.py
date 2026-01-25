"""
Helper utility functions for RadVerify
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dictionary containing configuration settings
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def save_json(data: Dict[str, Any], filepath: str) -> None:
    """
    Save data to JSON file.
    
    Args:
        data: Dictionary to save
        filepath: Output file path
    """
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def load_json(filepath: str) -> Dict[str, Any]:
    """
    Load data from JSON file.
    
    Args:
        filepath: Input file path
        
    Returns:
        Dictionary containing loaded data
    """
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    return data


def format_timestamp(dt: datetime = None) -> str:
    """
    Format timestamp for reports.
    
    Args:
        dt: Datetime object (uses current time if None)
        
    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def calculate_gestational_age(bpd: float, hc: float, ac: float, fl: float) -> Dict[str, Any]:
    """
    Calculate gestational age from biometric measurements.
    Uses Hadlock formula for estimation.
    
    Args:
        bpd: Biparietal diameter (mm)
        hc: Head circumference (mm)
        ac: Abdominal circumference (mm)
        fl: Femur length (mm)
        
    Returns:
        Dictionary with weeks, days, and confidence
    """
    # Simplified Hadlock formula (this is a placeholder - use actual medical formula)
    # In production, use validated medical algorithms
    
    # Average the estimates from different measurements
    estimates = []
    
    if bpd:
        # Rough estimation: BPD in mm / 2.4 ≈ weeks
        weeks_bpd = bpd / 2.4
        estimates.append(weeks_bpd)
    
    if fl:
        # Rough estimation: FL in mm / 1.6 ≈ weeks
        weeks_fl = fl / 1.6
        estimates.append(weeks_fl)
    
    if estimates:
        avg_weeks = sum(estimates) / len(estimates)
        weeks = int(avg_weeks)
        days = int((avg_weeks - weeks) * 7)
        
        return {
            "weeks": weeks,
            "days": days,
            "total_weeks": round(avg_weeks, 1),
            "confidence": "moderate" if len(estimates) >= 2 else "low"
        }
    
    return {
        "weeks": None,
        "days": None,
        "total_weeks": None,
        "confidence": "unknown"
    }


def calculate_estimated_fetal_weight(bpd: float, hc: float, ac: float, fl: float) -> float:
    """
    Calculate estimated fetal weight using Hadlock formula.
    
    Args:
        bpd: Biparietal diameter (mm)
        hc: Head circumference (mm)
        ac: Abdominal circumference (mm)
        fl: Femur length (mm)
        
    Returns:
        Estimated fetal weight in grams
    """
    # Simplified Hadlock formula (placeholder)
    # In production, use validated medical formula
    
    if ac and fl:
        # Very simplified estimation
        weight = (ac * fl * fl) / 100
        return round(weight, 1)
    
    return None
