"""
Autonomous Engineering Agent for Structural Optimization of 3D Printed Parts

This module provides tools for optimizing 3D printed components for maximum
structural stiffness with minimal deflection under defined load cases.
"""

__version__ = "1.0.0"
__author__ = "Voron Structural Optimization Team"

from .agent import StructuralOptimizationAgent
from .cad_handler import CADHandler
from .fem_analyzer import FEMAnalyzer
from .geometry_optimizer import GeometryOptimizer
from .export_handler import ExportHandler

__all__ = [
    "StructuralOptimizationAgent",
    "CADHandler",
    "FEMAnalyzer",
    "GeometryOptimizer",
    "ExportHandler",
]
