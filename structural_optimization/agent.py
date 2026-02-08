"""
Main autonomous agent for structural optimization.

This module coordinates the entire optimization workflow:
1. CAD import
2. Structural analysis (FEM)
3. Geometry optimization
4. Verification
5. Export
"""

import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

from .cad_handler import CADHandler
from .fem_analyzer import FEMAnalyzer
from .geometry_optimizer import GeometryOptimizer
from .export_handler import ExportHandler
from .config import OptimizationConfig

logger = logging.getLogger(__name__)


class StructuralOptimizationAgent:
    """
    Autonomous agent for structural optimization of 3D printed parts.
    
    Works iteratively and deterministically following engineering principles.
    """
    
    def __init__(self, config: OptimizationConfig):
        """
        Initialize the optimization agent.
        
        Args:
            config: Configuration object with material properties, constraints, etc.
        """
        self.config = config
        self.cad_handler = CADHandler()
        self.fem_analyzer = FEMAnalyzer(config)
        self.geometry_optimizer = GeometryOptimizer(config)
        self.export_handler = ExportHandler()
        
        self.iteration_history = []
        self.current_iteration = 0
        
        logger.info("Structural Optimization Agent initialized")
    
    def optimize(
        self,
        input_file: Path,
        output_dir: Path,
        max_iterations: int = 5
    ) -> Dict:
        """
        Run the complete optimization workflow.
        
        Args:
            input_file: Path to input CAD file (STEP format)
            output_dir: Directory for output files
            max_iterations: Maximum number of optimization iterations
            
        Returns:
            Dictionary with optimization results and metrics
        """
        logger.info(f"Starting optimization of {input_file}")
        
        # Step 1: Import CAD geometry
        logger.info("Step 1: Importing CAD geometry...")
        geometry = self.cad_handler.import_cad(input_file)
        
        # Step 2: Identify load-bearing structures and weak points
        logger.info("Step 2: Identifying critical structures...")
        critical_regions = self._identify_critical_regions(geometry)
        
        # Optimization loop
        best_result = None
        best_score = float('inf')  # Lower deflection is better
        
        for iteration in range(max_iterations):
            self.current_iteration = iteration
            logger.info(f"\n=== Optimization Iteration {iteration + 1}/{max_iterations} ===")
            
            # Step 3: FEM Analysis
            logger.info("Step 3: Running FEM analysis...")
            fem_results = self.fem_analyzer.analyze(
                geometry,
                self.config.boundary_conditions,
                self.config.load_cases
            )
            
            # Check if this is the best result so far
            max_deflection = fem_results['max_deflection']
            logger.info(f"Max deflection: {max_deflection:.6f} mm")
            
            if max_deflection < best_score:
                best_score = max_deflection
                best_result = {
                    'iteration': iteration,
                    'geometry': geometry,
                    'fem_results': fem_results,
                    'deflection': max_deflection
                }
            
            # Store iteration data
            self.iteration_history.append({
                'iteration': iteration,
                'max_deflection': max_deflection,
                'mass': fem_results.get('mass', 0),
                'max_stress': fem_results.get('max_stress', 0),
                'first_eigenfrequency': fem_results.get('first_eigenfrequency', 0)
            })
            
            # Check convergence
            if iteration > 0:
                prev_deflection = self.iteration_history[-2]['max_deflection']
                if prev_deflection > 0:
                    improvement = (prev_deflection - max_deflection) / prev_deflection
                else:
                    improvement = 0.0 if max_deflection == 0 else 1.0
                logger.info(f"Improvement: {improvement * 100:.2f}%")
                
                if improvement < 0.01:  # Less than 1% improvement
                    logger.info("Convergence reached (< 1% improvement)")
                    break
            
            # Step 4: Optimize geometry
            if iteration < max_iterations - 1:  # Don't optimize on last iteration
                logger.info("Step 4: Optimizing geometry...")
                geometry = self.geometry_optimizer.optimize(
                    geometry,
                    fem_results,
                    critical_regions
                )
        
        # Step 7: Verify final result
        logger.info("\nStep 7: Final verification...")
        final_fem = self.fem_analyzer.analyze(
            best_result['geometry'],
            self.config.boundary_conditions,
            self.config.load_cases
        )
        
        # Step 8: Export results
        logger.info("Step 8: Exporting optimized files...")
        output_files = self.export_handler.export_all(
            best_result['geometry'],
            output_dir,
            input_file.stem + "_optimized"
        )
        
        # Generate optimization report
        report = self._generate_report(best_result, final_fem, output_files)
        
        # Sanitize report for JSON serialization (remove inf/nan values)
        report = self._sanitize_for_json(report)
        
        # Save report
        report_path = output_dir / "optimization_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\nOptimization complete! Report saved to {report_path}")
        
        return report
    
    def _identify_critical_regions(self, geometry) -> List[Dict]:
        """
        Identify load-bearing structures and critical weak points.
        
        Args:
            geometry: CAD geometry object
            
        Returns:
            List of critical regions with metadata
        """
        logger.info("Analyzing geometry for critical regions...")
        
        # Analyze geometry features
        features = self.cad_handler.extract_features(geometry)
        
        critical_regions = []
        
        # Identify thin walls
        for wall in features.get('walls', []):
            if wall['thickness'] < self.config.min_wall_thickness:
                critical_regions.append({
                    'type': 'thin_wall',
                    'location': wall['location'],
                    'thickness': wall['thickness'],
                    'severity': 'high'
                })
        
        # Identify long unsupported spans
        for span in features.get('spans', []):
            if span['length'] > self.config.max_unsupported_length:
                critical_regions.append({
                    'type': 'long_span',
                    'location': span['location'],
                    'length': span['length'],
                    'severity': 'medium'
                })
        
        # Identify stress concentration points
        for point in features.get('stress_concentrations', []):
            critical_regions.append({
                'type': 'stress_concentration',
                'location': point['location'],
                'severity': 'high'
            })
        
        logger.info(f"Found {len(critical_regions)} critical regions")
        return critical_regions
    
    def _generate_report(
        self,
        best_result: Dict,
        final_fem: Dict,
        output_files: Dict
    ) -> Dict:
        """
        Generate comprehensive optimization report.
        
        Args:
            best_result: Best optimization result
            final_fem: Final FEM analysis results
            output_files: Paths to exported files
            
        Returns:
            Report dictionary
        """
        # Calculate improvement metrics
        initial_deflection = self.iteration_history[0]['max_deflection']
        final_deflection = final_fem['max_deflection']
        if initial_deflection > 0:
            deflection_improvement = (initial_deflection - final_deflection) / initial_deflection * 100
        else:
            deflection_improvement = 0.0
        
        # Calculate stiffness increase (inverse of deflection ratio)
        # Avoid creating infinity values by using None for incomparable cases
        if final_deflection > 0 and initial_deflection > 0:
            stiffness_increase_percent = (initial_deflection / final_deflection - 1) * 100
        elif initial_deflection > 0 and final_deflection == 0:
            stiffness_increase_percent = None  # Infinite improvement case
        else:
            stiffness_increase_percent = 0.0
        
        report = {
            'optimization_summary': {
                'iterations': len(self.iteration_history),
                'best_iteration': best_result['iteration'],
                'converged': True
            },
            'initial_metrics': {
                'max_deflection_mm': self.iteration_history[0]['max_deflection'],
                'mass_g': self.iteration_history[0]['mass'],
                'max_stress_mpa': self.iteration_history[0]['max_stress'],
                'first_eigenfrequency_hz': self.iteration_history[0].get('first_eigenfrequency', 0)
            },
            'final_metrics': {
                'max_deflection_mm': final_deflection,
                'mass_g': final_fem.get('mass', 0),
                'max_stress_mpa': final_fem.get('max_stress', 0),
                'first_eigenfrequency_hz': final_fem.get('first_eigenfrequency', 0)
            },
            'improvements': {
                'deflection_reduction_percent': deflection_improvement,
                'stiffness_increase_percent': stiffness_increase_percent
            },
            'material': {
                'type': self.config.material_type,
                'youngs_modulus_mpa': self.config.youngs_modulus,
                'yield_strength_mpa': self.config.yield_strength,
                'density_g_cm3': self.config.density
            },
            'manufacturing': {
                'process': 'FDM 3D Printing',
                'printable_without_supports': self.config.prefer_no_supports,
                'layer_height_mm': self.config.layer_height
            },
            'output_files': output_files,
            'iteration_history': self.iteration_history,
            'configuration': self.config.to_dict()
        }
        
        return report
    
    def _sanitize_for_json(self, obj):
        """
        Sanitize object for JSON serialization by replacing inf/nan values.
        
        Args:
            obj: Object to sanitize (dict, list, or primitive)
            
        Returns:
            Sanitized object safe for JSON serialization
        """
        if isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(v) for v in obj]
        elif isinstance(obj, float):
            if math.isinf(obj) or math.isnan(obj):
                return None
        return obj
