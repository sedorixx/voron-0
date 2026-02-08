# Workflow Integration Documentation

## Overview

This document describes the complete optimization workflow integration that chains together FreeCAD, Gmsh, FEniCS/CalculiX, and OpenMDAO for automated structural optimization.

## Workflow Pipeline

```
FreeCAD (Parametric Geometry)
    ↓
Gmsh (Mesh Generation)
    ↓
FEniCS or CalculiX (FEM Analysis)
    ↓
OpenMDAO (Optimization)
    ↓
FreeCAD (Updated Geometry)
    ↓
Repeat until convergence
```

## Architecture

### Core Components

The workflow integration consists of four main interface classes and one orchestrator:

#### 1. FreeCADInterface
- **Purpose**: Load and manipulate parametric CAD models
- **Functions**:
  - `load_parametric_model()`: Load FreeCAD or STEP files with parameters
  - `update_geometry()`: Update model with new parameter values
  - `export_step()`: Export geometry to STEP format
- **Supported Formats**: `.FCStd` (FreeCAD native), `.step`, `.stp`

#### 2. GmshInterface
- **Purpose**: Generate finite element meshes from CAD geometry
- **Functions**:
  - `generate_mesh()`: Create 3D tetrahedral mesh
  - Configurable mesh size
- **Output Formats**: `.msh` (Gmsh native)

#### 3. FEMSolverInterface
- **Purpose**: Run structural FEM analysis
- **Supported Solvers**:
  - FEniCS: Python-based FEM solver
  - CalculiX: Industrial-strength CCX solver
- **Functions**:
  - `run_analysis()`: Perform static structural analysis
  - Returns displacements, stresses, and reaction forces

#### 4. OpenMDAOInterface
- **Purpose**: Optimization of design parameters
- **Functions**:
  - `setup_optimization()`: Define design variables, objectives, constraints
  - `run_optimization()`: Execute optimization loop
- **Algorithm**: SLSQP (Sequential Least Squares Programming)

#### 5. WorkflowOrchestrator
- **Purpose**: Coordinate the complete workflow
- **Functions**:
  - `run_workflow()`: Execute complete optimization pipeline
  - `get_workflow_status()`: Monitor progress
  - Handles convergence checking
  - Manages iteration history

## Installation

### Requirements

```bash
# Core requirements (minimal)
pip install numpy scipy

# For production use (optional)
pip install gmsh fenics-dolfinx openmdao

# FreeCAD installation
# Linux: sudo apt install freecad
# macOS: brew install freecad
# Windows: Download from freecadweb.org
```

## Usage

### Command Line Interface

#### Basic Workflow Execution

```bash
# Run workflow with default settings
python -m structural_optimization.cli workflow input_part.step

# Specify output directory
python -m structural_optimization.cli workflow input_part.step -o ./output

# Choose FEM solver
python -m structural_optimization.cli workflow input_part.step --fem-solver calculix

# Set material
python -m structural_optimization.cli workflow input_part.step -m PA-CF

# Custom iterations and convergence
python -m structural_optimization.cli workflow input_part.step -n 15 --convergence-tolerance 0.005
```

#### Full Command Options

```bash
python -m structural_optimization.cli workflow [OPTIONS] input_file

Options:
  --output-dir, -o         Output directory
  --config, -c             Configuration JSON file
  --material, -m           Material preset (PA-CF, ABS, PLA, PETG, PC)
  --fem-solver             FEM solver (fenics or calculix)
  --max-iterations, -n     Maximum workflow iterations (default: 10)
  --convergence-tolerance  Convergence threshold (default: 0.01)
  --mesh-size              Mesh element size in mm
  --verbose, -v            Verbose logging
```

### Programmatic API

#### Example 1: Basic Workflow

```python
from pathlib import Path
from structural_optimization.workflow_orchestrator import WorkflowOrchestrator
from structural_optimization.config import OptimizationConfig, LoadCase, BoundaryCondition

# Configure optimization
config = OptimizationConfig(material_type="PA-CF")

# Define boundary conditions
config.boundary_conditions = [
    BoundaryCondition(
        type='fixed',
        location=[0, 0, 0],
        constrained_dof=['x', 'y', 'z']
    )
]

# Define load cases
config.load_cases = [
    LoadCase(
        type='force',
        location=[100, 50, 50],
        magnitude=50.0,  # Newtons
        direction=[0, 0, -1]  # Downward
    )
]

# Create orchestrator
orchestrator = WorkflowOrchestrator(
    config=config,
    fem_solver='fenics'  # or 'calculix'
)

# Run workflow
results = orchestrator.run_workflow(
    input_file=Path("bracket.FCStd"),
    output_dir=Path("./optimized"),
    max_iterations=10,
    convergence_tolerance=0.01
)

# Access results
print(f"Deflection reduced by {results['improvements']['deflection_reduction_percent']:.1f}%")
print(f"Optimal parameters: {results['optimal_parameters']}")
```

#### Example 2: Custom Configuration

```python
from structural_optimization.workflow_orchestrator import WorkflowOrchestrator
from structural_optimization.config import OptimizationConfig

# Load custom configuration
config = OptimizationConfig.from_json(Path("my_config.json"))

# Or create programmatically
config = OptimizationConfig(
    material_type="PA-CF",
    youngs_modulus=5500.0,  # MPa
    poisson_ratio=0.35,
    yield_strength=85.0,    # MPa
    density=1.15,           # g/cm³
    mesh_size=1.5,          # mm
    safety_factor=2.0,
    prefer_no_supports=True
)

orchestrator = WorkflowOrchestrator(config, fem_solver='fenics')
results = orchestrator.run_workflow(...)
```

#### Example 3: Monitoring Progress

```python
orchestrator = WorkflowOrchestrator(config, fem_solver='fenics')

# Check status before starting
status = orchestrator.get_workflow_status()
print(f"Status: {status['status']}")  # 'not_started'

# Run workflow
results = orchestrator.run_workflow(...)

# Check final status
status = orchestrator.get_workflow_status()
print(f"Iterations: {status['total_iterations']}")
print(f"Best deflection: {status['best_deflection']:.4f} mm")
```

## Configuration

### Configuration File Format

Create a JSON configuration file:

```json
{
  "material": {
    "type": "PA-CF",
    "youngs_modulus_mpa": 5500,
    "poisson_ratio": 0.35,
    "yield_strength_mpa": 85,
    "density_g_cm3": 1.15
  },
  "analysis": {
    "mesh_size_mm": 2.0,
    "safety_factor": 2.0
  },
  "constraints": {
    "min_wall_thickness_mm": 1.6,
    "prefer_no_supports": true,
    "max_overhang_angle_deg": 45
  },
  "boundary_conditions": [
    {
      "type": "fixed",
      "location": [0, 0, 0],
      "constrained_dof": ["x", "y", "z"]
    }
  ],
  "load_cases": [
    {
      "type": "force",
      "location": [100, 50, 50],
      "magnitude": 50.0,
      "direction": [0, 0, -1]
    }
  ]
}
```

Use with:
```bash
python -m structural_optimization.cli workflow part.step -c config.json
```

## Output

### Generated Files

The workflow produces the following files in the output directory:

1. **optimized_geometry.step** - Final optimized CAD geometry
2. **optimized_geometry.stl** - 3D printable mesh (if applicable)
3. **optimized_mesh.msh** - Final FEM mesh
4. **workflow_report.json** - Complete optimization report
5. **iteration_X_geometry.step** - Intermediate geometries
6. **iteration_X_mesh.msh** - Intermediate meshes

### Workflow Report

The `workflow_report.json` contains:

```json
{
  "workflow": {
    "iterations": 5,
    "converged": true,
    "elapsed_time_seconds": 123.4
  },
  "initial_parameters": {
    "thickness": 2.0,
    "width": 50.0,
    ...
  },
  "optimal_parameters": {
    "thickness": 2.8,
    "width": 52.3,
    ...
  },
  "initial_metrics": {
    "max_deflection_mm": 0.523,
    "max_stress_mpa": 28.5
  },
  "final_metrics": {
    "max_deflection_mm": 0.312,
    "max_stress_mpa": 22.1
  },
  "improvements": {
    "deflection_reduction_percent": 40.3,
    "iterations": 5
  },
  "tools": {
    "cad": "FreeCAD",
    "meshing": "Gmsh",
    "fem_solver": "FENICS",
    "optimization": "OpenMDAO"
  },
  "iteration_history": [...]
}
```

## Integration with Real Tools

### Using Real FreeCAD

Install FreeCAD and its Python bindings:

```bash
# Linux
sudo apt install freecad python3-freecad

# macOS
brew install freecad

# Then in your Python environment
import FreeCAD
import Part
```

The workflow will automatically detect and use the real FreeCAD when available.

### Using Real Gmsh

```bash
pip install gmsh
```

Or install Gmsh standalone from http://gmsh.info/

### Using Real FEniCS

```bash
# FEniCS (legacy)
pip install fenics

# Or FEniCSx (modern)
pip install fenics-dolfinx
```

### Using Real CalculiX

Download CalculiX from http://www.calculix.de/ and ensure `ccx` is in your PATH.

### Using Real OpenMDAO

```bash
pip install openmdao
```

## Workflow Behavior

### Iteration Process

1. **Initialize**: Load parametric model, extract design parameters
2. **Loop** (until convergence or max iterations):
   - Export current geometry to STEP
   - Generate FEM mesh with Gmsh
   - Run FEM analysis (FEniCS or CalculiX)
   - Evaluate objective (deflection)
   - Optimize parameters with OpenMDAO
   - Update geometry with new parameters
3. **Finalize**: Export optimized geometry, generate report

### Convergence Criteria

The workflow stops when:
- Improvement < convergence_tolerance (default 1%)
- Maximum iterations reached
- Design constraints violated

### Design Variables

The workflow automatically extracts design variables from parametric models:
- Thickness dimensions
- Width/height dimensions
- Rib spacing
- Fillet radii
- Other constrained parameters

Bounds are automatically set based on reasonable engineering limits.

## Troubleshooting

### Common Issues

**Issue**: "FreeCAD not found"
- **Solution**: Install FreeCAD or use STEP files. The workflow will use placeholder implementations.

**Issue**: "Gmsh not found"
- **Solution**: `pip install gmsh` or install Gmsh standalone

**Issue**: "Workflow not converging"
- **Solution**: Increase `max_iterations`, adjust `convergence_tolerance`, or check if design space allows improvement

**Issue**: "FEM analysis fails"
- **Solution**: Check mesh quality (reduce `mesh_size`), verify boundary conditions, check material properties

### Debug Mode

Enable verbose logging:
```bash
python -m structural_optimization.cli workflow part.step -v
```

Or in Python:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

### Mesh Size
- Smaller mesh (1.0-1.5 mm): Better accuracy, slower
- Larger mesh (3.0-5.0 mm): Faster, less accurate
- Default (2.0 mm): Good balance

### Iterations
- Fewer iterations (5-7): Faster, may not fully converge
- More iterations (15-20): Better optimization, slower
- Default (10): Good balance

### Parallel Processing
The workflow runs iterations sequentially. For batch optimization of multiple parts, run workflows in parallel manually.

## Examples

See `examples/example_workflow.py` for complete working examples:

```bash
python examples/example_workflow.py
```

## Testing

Run workflow integration tests:

```bash
pytest tests/test_workflow.py -v
```

All tests use placeholder implementations and don't require real tools to be installed.

## References

- **FreeCAD**: https://www.freecadweb.org/
- **Gmsh**: http://gmsh.info/
- **FEniCS**: https://fenicsproject.org/
- **CalculiX**: http://www.calculix.de/
- **OpenMDAO**: https://openmdao.org/

## License

See LICENSE file in the repository.
