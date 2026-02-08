"""
Workflow orchestrator for the complete optimization pipeline.

Implements: FreeCAD → Gmsh → FEniCS/CalculiX → OpenMDAO → FreeCAD
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import time

from .workflow_integration import (
    FreeCADInterface,
    GmshInterface,
    FEMSolverInterface,
    OpenMDAOInterface
)
from .config import OptimizationConfig

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """
    Orchestrates the complete optimization workflow.
    
    Workflow steps:
    1. FreeCAD: Load parametric geometry
    2. Gmsh: Generate finite element mesh
    3. FEniCS/CalculiX: Run structural analysis
    4. OpenMDAO: Optimize design parameters
    5. FreeCAD: Update geometry with optimized parameters
    6. Repeat until convergence
    """
    
    def __init__(self, config: OptimizationConfig, fem_solver: str = 'fenics'):
        """
        Initialize workflow orchestrator.
        
        Args:
            config: Optimization configuration
            fem_solver: FEM solver to use ('fenics' or 'calculix')
        """
        self.config = config
        
        # Initialize interfaces
        self.freecad = FreeCADInterface()
        self.gmsh = GmshInterface(mesh_size=config.mesh_size)
        self.fem_solver = FEMSolverInterface(solver_type=fem_solver)
        self.openmDAO = OpenMDAOInterface()
        
        # Workflow state
        self.iteration_history = []
        self.current_iteration = 0
        
        logger.info(f"Workflow orchestrator initialized with {fem_solver} solver")
    
    def run_workflow(self, input_file: Path, output_dir: Path,
                    max_iterations: int = 10,
                    convergence_tolerance: float = 0.01) -> Dict[str, Any]:
        """
        Run the complete optimization workflow.
        
        Args:
            input_file: Input parametric CAD file (.FCStd or .step)
            output_dir: Output directory for results
            max_iterations: Maximum optimization iterations
            convergence_tolerance: Relative improvement threshold for convergence
            
        Returns:
            Dictionary with workflow results and optimized geometry
        """
        logger.info(f"Starting optimization workflow with {max_iterations} max iterations")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        start_time = time.time()
        
        # Step 1: Load parametric model from FreeCAD
        logger.info("=" * 60)
        logger.info("STEP 1: Loading parametric model from FreeCAD")
        logger.info("=" * 60)
        model = self.freecad.load_parametric_model(input_file)
        initial_parameters = model['parameters'].copy()
        logger.info(f"Loaded model with parameters: {list(initial_parameters.keys())}")
        
        # Define design variables for optimization
        design_variables = self._define_design_variables(initial_parameters)
        
        # Setup optimization problem
        logger.info("=" * 60)
        logger.info("Setting up OpenMDAO optimization problem")
        logger.info("=" * 60)
        
        objective = 'max_deflection'
        constraints = {
            'max_stress': ('upper', self.config.yield_strength / self.config.safety_factor),
            'mass': ('upper', initial_parameters.get('max_mass', float('inf')))
        }
        
        opt_problem = self.openmDAO.setup_optimization(
            design_variables=design_variables,
            objective=objective,
            constraints=constraints
        )
        
        # Optimization loop
        best_deflection = float('inf')
        best_parameters = initial_parameters.copy()
        
        for iteration in range(max_iterations):
            self.current_iteration = iteration
            logger.info("")
            logger.info("=" * 60)
            logger.info(f"ITERATION {iteration + 1}/{max_iterations}")
            logger.info("=" * 60)
            
            # Step 2: Export to STEP and generate mesh with Gmsh
            logger.info("STEP 2: Generating mesh with Gmsh")
            step_file = output_dir / f"iteration_{iteration}_geometry.step"
            mesh_file = output_dir / f"iteration_{iteration}_mesh.msh"
            
            self.freecad.export_step(model, step_file)
            mesh_data = self.gmsh.generate_mesh(step_file, mesh_file, self.config.mesh_size)
            logger.info(f"Generated mesh with {mesh_data['n_nodes']} nodes, {mesh_data['n_elements']} elements")
            
            # Step 3: Run FEM analysis with FEniCS or CalculiX
            logger.info(f"STEP 3: Running FEM analysis with {self.fem_solver.solver_type}")
            
            material_props = {
                'youngs_modulus': self.config.youngs_modulus,
                'poisson_ratio': self.config.poisson_ratio,
                'density': self.config.density
            }
            
            fem_results = self.fem_solver.run_analysis(
                mesh_file=mesh_file,
                material_properties=material_props,
                boundary_conditions=self.config.boundary_conditions,
                load_cases=self.config.load_cases
            )
            
            max_deflection = fem_results['max_displacement']
            max_stress = fem_results.get('max_stress', 0.0)
            
            logger.info(f"Analysis results:")
            logger.info(f"  - Max deflection: {max_deflection:.4f} mm")
            logger.info(f"  - Max stress: {max_stress:.2f} MPa")
            logger.info(f"  - Safety factor: {self.config.yield_strength / max_stress:.2f}")
            
            # Record iteration
            iteration_data = {
                'iteration': iteration + 1,
                'parameters': model['parameters'].copy(),
                'max_deflection': max_deflection,
                'max_stress': max_stress,
                'converged': fem_results['converged']
            }
            self.iteration_history.append(iteration_data)
            
            # Check for improvement
            if max_deflection < best_deflection:
                improvement = (best_deflection - max_deflection) / best_deflection if best_deflection < float('inf') else 1.0
                logger.info(f"✓ Improvement: {improvement * 100:.2f}% reduction in deflection")
                
                best_deflection = max_deflection
                best_parameters = model['parameters'].copy()
                
                # Check convergence
                if iteration > 0 and improvement < convergence_tolerance:
                    logger.info(f"✓ Converged! Improvement below threshold ({convergence_tolerance * 100}%)")
                    break
            else:
                logger.info("No improvement in this iteration")
            
            # Step 4: Optimize parameters with OpenMDAO
            if iteration < max_iterations - 1:
                logger.info("STEP 4: Optimizing design parameters with OpenMDAO")
                
                # Create evaluation function for OpenMDAO
                def evaluate_design(params: Dict[str, float]) -> Dict[str, float]:
                    """Evaluate design for given parameters."""
                    # Update model
                    temp_model = self.freecad.update_geometry(model, params)
                    
                    # Export and mesh
                    temp_step = output_dir / f"temp_iteration_{iteration}_eval.step"
                    temp_mesh = output_dir / f"temp_iteration_{iteration}_eval.msh"
                    self.freecad.export_step(temp_model, temp_step)
                    self.gmsh.generate_mesh(temp_step, temp_mesh, self.config.mesh_size)
                    
                    # Run FEM
                    temp_results = self.fem_solver.run_analysis(
                        temp_mesh, material_props,
                        self.config.boundary_conditions,
                        self.config.load_cases
                    )
                    
                    return {
                        'objective': temp_results['max_displacement'],
                        'max_stress': temp_results.get('max_stress', 0.0)
                    }
                
                # Run optimization
                opt_results = self.openmDAO.run_optimization(
                    problem=opt_problem,
                    evaluation_function=evaluate_design,
                    max_iterations=5  # Inner optimization iterations
                )
                
                logger.info(f"OpenMDAO optimization completed in {opt_results['iterations']} iterations")
                logger.info(f"Optimal parameters: {opt_results['optimal_variables']}")
                
                # Step 5: Update geometry in FreeCAD
                logger.info("STEP 5: Updating geometry with optimized parameters")
                model = self.freecad.update_geometry(model, opt_results['optimal_variables'])
        
        # Final export
        logger.info("")
        logger.info("=" * 60)
        logger.info("WORKFLOW COMPLETE - Exporting final results")
        logger.info("=" * 60)
        
        final_step_file = output_dir / "optimized_geometry.step"
        final_stl_file = output_dir / "optimized_geometry.stl"
        
        self.freecad.export_step(model, final_step_file)
        
        # Generate final mesh for verification
        final_mesh_file = output_dir / "optimized_mesh.msh"
        final_mesh_data = self.gmsh.generate_mesh(final_step_file, final_mesh_file)
        
        # Run final FEM analysis
        final_fem_results = self.fem_solver.run_analysis(
            final_mesh_file,
            material_props,
            self.config.boundary_conditions,
            self.config.load_cases
        )
        
        elapsed_time = time.time() - start_time
        
        # Compile results
        results = {
            'workflow': {
                'iterations': len(self.iteration_history),
                'converged': len(self.iteration_history) < max_iterations,
                'elapsed_time_seconds': elapsed_time
            },
            'initial_parameters': initial_parameters,
            'optimal_parameters': best_parameters,
            'initial_metrics': {
                'max_deflection_mm': self.iteration_history[0]['max_deflection'],
                'max_stress_mpa': self.iteration_history[0]['max_stress']
            },
            'final_metrics': {
                'max_deflection_mm': final_fem_results['max_displacement'],
                'max_stress_mpa': final_fem_results.get('max_stress', 0.0)
            },
            'improvements': {
                'deflection_reduction_percent': (
                    (self.iteration_history[0]['max_deflection'] - final_fem_results['max_displacement']) /
                    self.iteration_history[0]['max_deflection'] * 100
                ),
                'iterations': len(self.iteration_history)
            },
            'output_files': {
                'geometry_step': str(final_step_file),
                'geometry_stl': str(final_stl_file),
                'mesh': str(final_mesh_file)
            },
            'iteration_history': self.iteration_history,
            'tools': {
                'cad': 'FreeCAD',
                'meshing': 'Gmsh',
                'fem_solver': self.fem_solver.solver_type.upper(),
                'optimization': 'OpenMDAO'
            }
        }
        
        # Save results
        report_file = output_dir / "workflow_report.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {report_file}")
        logger.info(f"Deflection reduced by {results['improvements']['deflection_reduction_percent']:.1f}%")
        logger.info(f"Total time: {elapsed_time:.1f} seconds")
        
        return results
    
    def _define_design_variables(self, parameters: Dict[str, float]) -> Dict[str, Tuple[float, float, float]]:
        """
        Define design variables for optimization from model parameters.
        
        Args:
            parameters: Dictionary of model parameters
            
        Returns:
            Dictionary of {name: (initial, lower_bound, upper_bound)}
        """
        design_vars = {}
        
        # Define bounds for common parameters
        param_bounds = {
            'thickness': (0.5, 5.0),
            'width': (0.5, 2.0),  # Relative bounds
            'height': (0.5, 2.0),
            'rib_spacing': (0.5, 2.0),
            'fillet_radius': (1.0, 10.0)
        }
        
        for name, value in parameters.items():
            if name in param_bounds:
                if 'width' in name or 'height' in name or 'spacing' in name:
                    # Relative bounds
                    lower = value * param_bounds[name][0]
                    upper = value * param_bounds[name][1]
                else:
                    # Absolute bounds
                    lower, upper = param_bounds[name]
                
                design_vars[name] = (value, lower, upper)
                logger.debug(f"Design variable '{name}': initial={value}, bounds=[{lower}, {upper}]")
        
        return design_vars
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """
        Get current workflow status.
        
        Returns:
            Dictionary with workflow status information
        """
        if not self.iteration_history:
            return {
                'status': 'not_started',
                'iterations': 0
            }
        
        return {
            'status': 'running' if self.current_iteration < len(self.iteration_history) else 'completed',
            'current_iteration': self.current_iteration,
            'total_iterations': len(self.iteration_history),
            'best_deflection': min(it['max_deflection'] for it in self.iteration_history),
            'latest_deflection': self.iteration_history[-1]['max_deflection']
        }
