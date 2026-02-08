"""
Example usage of the Structural Optimization Agent.

This script demonstrates how to use the agent programmatically
to optimize a 3D printed part.
"""

from pathlib import Path
from structural_optimization import StructuralOptimizationAgent
from structural_optimization.config import OptimizationConfig, LoadCase, BoundaryCondition


def example_basic_optimization():
    """
    Example 1: Basic optimization with default PA-CF material.
    """
    print("Example 1: Basic Optimization")
    print("-" * 60)
    
    # Create default configuration for PA-CF
    config = OptimizationConfig(material_type="PA-CF")
    
    # Define boundary conditions (fixed support)
    config.boundary_conditions = [
        BoundaryCondition(
            type='fixed',
            location=[0, 0, 0],
            constrained_dof=['x', 'y', 'z']
        )
    ]
    
    # Define load case (50N downward force)
    config.load_cases = [
        LoadCase(
            type='force',
            location=[100, 50, 50],
            magnitude=50.0,  # N
            direction=[0, 0, -1]  # downward
        )
    ]
    
    # Create agent
    agent = StructuralOptimizationAgent(config)
    
    # Note: This would need an actual STEP file to work
    # report = agent.optimize(
    #     input_file=Path("input_part.step"),
    #     output_dir=Path("./optimized"),
    #     max_iterations=5
    # )
    
    print("Configuration created successfully!")
    print(f"Material: {config.material_type}")
    print(f"Young's Modulus: {config.youngs_modulus} MPa")
    print(f"Mesh size: {config.mesh_size} mm")
    print()


def example_custom_material():
    """
    Example 2: Optimization with custom material properties.
    """
    print("Example 2: Custom Material")
    print("-" * 60)
    
    # Create custom material configuration
    config = OptimizationConfig(
        material_type="Custom-GF30",
        youngs_modulus=6500.0,  # MPa
        poisson_ratio=0.35,
        yield_strength=100.0,  # MPa
        density=1.22  # g/cm³
    )
    
    # Customize printing parameters
    config.layer_height = 0.16  # mm (finer layers)
    config.wall_line_count = 6  # More walls for strength
    config.infill_percentage = 50.0  # Higher infill
    
    # Set optimization targets
    config.target_deflection = 0.5  # mm (maximum acceptable)
    config.target_first_frequency = 100.0  # Hz (minimum)
    
    print("Custom material configured!")
    print(f"Material: {config.material_type}")
    print(f"Target deflection: {config.target_deflection} mm")
    print(f"Target frequency: {config.target_first_frequency} Hz")
    print()


def example_from_json():
    """
    Example 3: Load configuration from JSON file.
    """
    print("Example 3: Configuration from JSON")
    print("-" * 60)
    
    # Path to example config
    config_path = Path(__file__).parent / "example_config.json"
    
    if config_path.exists():
        config = OptimizationConfig.from_json(config_path)
        print("Configuration loaded from JSON!")
        print(f"Material: {config.material_type}")
        print(f"Boundary conditions: {len(config.boundary_conditions)}")
        print(f"Load cases: {len(config.load_cases)}")
    else:
        print(f"Config file not found: {config_path}")
    print()


def example_multi_load_case():
    """
    Example 4: Optimization with multiple load cases.
    """
    print("Example 4: Multiple Load Cases")
    print("-" * 60)
    
    config = OptimizationConfig(material_type="PA-CF")
    
    # Multiple supports
    config.boundary_conditions = [
        BoundaryCondition(type='fixed', location=[0, 0, 0]),
        BoundaryCondition(type='fixed', location=[100, 0, 0])
    ]
    
    # Multiple load scenarios
    config.load_cases = [
        LoadCase(
            type='force',
            location=[50, 50, 100],
            magnitude=30.0,
            direction=[0, 0, -1]
        ),
        LoadCase(
            type='moment',
            location=[50, 50, 50],
            magnitude=5000.0,  # Nmm
            direction=[1, 0, 0]
        ),
        LoadCase(
            type='pressure',
            location=[25, 50, 75],
            magnitude=0.5  # MPa
        )
    ]
    
    print("Multi-load case configuration created!")
    print(f"Number of supports: {len(config.boundary_conditions)}")
    print(f"Number of load cases: {len(config.load_cases)}")
    print()


def example_printability_focus():
    """
    Example 5: Optimization focused on printability.
    """
    print("Example 5: Printability-Focused Optimization")
    print("-" * 60)
    
    config = OptimizationConfig(material_type="PA-CF")
    
    # Strict printability constraints
    config.prefer_no_supports = True
    config.max_overhang_angle = 40.0  # degrees (stricter)
    config.min_wall_thickness = 2.0  # mm (thicker for reliability)
    config.max_unsupported_length = 25.0  # mm (shorter spans)
    
    # Preserve all interfaces
    config.preserve_interfaces = True
    
    print("Printability-focused configuration created!")
    print(f"Max overhang: {config.max_overhang_angle}°")
    print(f"Min wall thickness: {config.min_wall_thickness} mm")
    print(f"No supports: {config.prefer_no_supports}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("STRUCTURAL OPTIMIZATION AGENT - EXAMPLES")
    print("=" * 60)
    print()
    
    example_basic_optimization()
    example_custom_material()
    example_from_json()
    example_multi_load_case()
    example_printability_focus()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)
