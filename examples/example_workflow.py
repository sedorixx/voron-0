#!/usr/bin/env python3
"""
Example usage of the complete optimization workflow.

This demonstrates the workflow:
FreeCAD (Parametric) → Gmsh (Mesh) → FEniCS/CalculiX (FEM) → OpenMDAO (Optimization) → FreeCAD (new geometry)
"""

import sys
from pathlib import Path
import tempfile

# Add parent directory to path for importing
sys.path.insert(0, str(Path(__file__).parent.parent))

from structural_optimization.workflow_orchestrator import WorkflowOrchestrator
from structural_optimization.config import OptimizationConfig, LoadCase, BoundaryCondition


def example_workflow_basic():
    """
    Example 1: Basic workflow with default settings.
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Workflow with Default Settings")
    print("="*70)
    
    # Create configuration with PA-CF material
    config = OptimizationConfig(material_type="PA-CF")
    
    # Define boundary conditions - fixed at one end
    config.boundary_conditions = [
        BoundaryCondition(
            type='fixed',
            location=[0, 0, 0],
            constrained_dof=['x', 'y', 'z']
        )
    ]
    
    # Define load case - force at the other end
    config.load_cases = [
        LoadCase(
            type='force',
            location=[100, 50, 50],
            magnitude=50.0,  # 50 N
            direction=[0, 0, -1]  # Downward
        )
    ]
    
    # Create workflow orchestrator with FEniCS solver
    orchestrator = WorkflowOrchestrator(config, fem_solver='fenics')
    
    # Create temporary files for demonstration
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy parametric CAD file
        input_file = Path(tmpdir) / "test_bracket.step"
        input_file.write_text("ISO-10303-21;\nHEADER;\n/* Example parametric bracket */\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;")
        
        output_dir = Path(tmpdir) / "workflow_output"
        
        print(f"\nInput file:  {input_file}")
        print(f"Output dir:  {output_dir}")
        print("\nRunning workflow...")
        
        # Run the workflow
        results = orchestrator.run_workflow(
            input_file=input_file,
            output_dir=output_dir,
            max_iterations=3,  # Few iterations for demo
            convergence_tolerance=0.01
        )
        
        # Display results
        print("\n" + "-"*70)
        print("RESULTS:")
        print("-"*70)
        print(f"Workflow completed in {results['workflow']['iterations']} iterations")
        print(f"Tools used:")
        for tool_type, tool_name in results['tools'].items():
            print(f"  - {tool_type.upper()}: {tool_name}")
        print(f"\nInitial deflection: {results['initial_metrics']['max_deflection_mm']:.4f} mm")
        print(f"Final deflection:   {results['final_metrics']['max_deflection_mm']:.4f} mm")
        print(f"Improvement:        {results['improvements']['deflection_reduction_percent']:.1f}%")
        print(f"\nInitial parameters: {results['initial_parameters']}")
        print(f"Optimal parameters: {results['optimal_parameters']}")


def example_workflow_with_calculix():
    """
    Example 2: Workflow using CalculiX FEM solver.
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Workflow with CalculiX FEM Solver")
    print("="*70)
    
    # Create configuration with ABS material
    config = OptimizationConfig(material_type="ABS")
    
    # Define boundary conditions
    config.boundary_conditions = [
        BoundaryCondition(
            type='fixed',
            location=[0, 0, 0],
            constrained_dof=['x', 'y', 'z']
        )
    ]
    
    # Define load case
    config.load_cases = [
        LoadCase(
            type='force',
            location=[80, 40, 40],
            magnitude=30.0,
            direction=[0, 0, -1]
        )
    ]
    
    # Use CalculiX solver instead of FEniCS
    orchestrator = WorkflowOrchestrator(config, fem_solver='calculix')
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "test_part.step"
        input_file.write_text("ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;")
        
        output_dir = Path(tmpdir) / "calculix_output"
        
        print(f"\nUsing CalculiX FEM solver")
        print(f"Material: ABS")
        print("\nRunning workflow...")
        
        results = orchestrator.run_workflow(
            input_file=input_file,
            output_dir=output_dir,
            max_iterations=3,
            convergence_tolerance=0.01
        )
        
        print(f"\nWorkflow completed successfully!")
        print(f"FEM Solver: {results['tools']['fem_solver']}")
        print(f"Deflection reduced by {results['improvements']['deflection_reduction_percent']:.1f}%")


def example_workflow_custom_parameters():
    """
    Example 3: Workflow with custom convergence parameters.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Workflow with Custom Parameters")
    print("="*70)
    
    # Create configuration with custom settings
    config = OptimizationConfig(
        material_type="PA-CF",
        mesh_size=1.5,  # Finer mesh
        safety_factor=2.5,  # Higher safety factor
        prefer_no_supports=True
    )
    
    config.boundary_conditions = [
        BoundaryCondition(
            type='fixed',
            location=[0, 0, 0],
            constrained_dof=['x', 'y', 'z']
        )
    ]
    
    config.load_cases = [
        LoadCase(
            type='force',
            location=[100, 50, 50],
            magnitude=75.0,  # Higher load
            direction=[0, 0, -1]
        )
    ]
    
    orchestrator = WorkflowOrchestrator(config, fem_solver='fenics')
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "test_heavy_duty.step"
        input_file.write_text("ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;")
        
        output_dir = Path(tmpdir) / "custom_output"
        
        print(f"\nCustom settings:")
        print(f"  - Mesh size: {config.mesh_size} mm")
        print(f"  - Safety factor: {config.safety_factor}")
        print(f"  - Load: 75 N")
        print("\nRunning workflow...")
        
        results = orchestrator.run_workflow(
            input_file=input_file,
            output_dir=output_dir,
            max_iterations=5,  # More iterations
            convergence_tolerance=0.005  # Tighter convergence
        )
        
        print(f"\nOptimization converged: {results['workflow']['converged']}")
        print(f"Total iterations: {results['workflow']['iterations']}")
        print(f"Elapsed time: {results['workflow']['elapsed_time_seconds']:.1f} seconds")


def example_workflow_status():
    """
    Example 4: Checking workflow status during execution.
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Workflow Status Monitoring")
    print("="*70)
    
    config = OptimizationConfig(material_type="PA-CF")
    
    config.boundary_conditions = [
        BoundaryCondition(type='fixed', location=[0, 0, 0])
    ]
    
    config.load_cases = [
        LoadCase(type='force', location=[100, 50, 50], magnitude=50.0)
    ]
    
    orchestrator = WorkflowOrchestrator(config, fem_solver='fenics')
    
    # Check status before running
    status = orchestrator.get_workflow_status()
    print(f"\nInitial status: {status}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "test_part.step"
        input_file.write_text("ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;")
        
        output_dir = Path(tmpdir) / "status_output"
        
        results = orchestrator.run_workflow(
            input_file=input_file,
            output_dir=output_dir,
            max_iterations=3
        )
        
        # Check status after running
        status = orchestrator.get_workflow_status()
        print(f"\nFinal status: {status}")
        print(f"Best deflection achieved: {status['best_deflection']:.4f} mm")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("WORKFLOW INTEGRATION EXAMPLES")
    print("="*70)
    print("\nThese examples demonstrate the complete optimization workflow:")
    print("FreeCAD → Gmsh → FEniCS/CalculiX → OpenMDAO → FreeCAD")
    print("\nNote: These examples use placeholder implementations.")
    print("Install real tools (FreeCAD, Gmsh, FEniCS, etc.) for production use.")
    
    try:
        # Run examples
        example_workflow_basic()
        example_workflow_with_calculix()
        example_workflow_custom_parameters()
        example_workflow_status()
        
        print("\n" + "="*70)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
