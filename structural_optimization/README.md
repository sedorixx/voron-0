# Structural Optimization Agent - Quick Start

This is an autonomous engineering agent for structural optimization of 3D printed parts, specifically designed for the Voron 0 printer but applicable to any FDM 3D printing project.

## What It Does

The agent automatically optimizes 3D printed parts to:
- **Maximize structural stiffness**
- **Minimize deflection under load**
- **Maintain printability** (no supports preferred)
- **Preserve mounting interfaces**

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install minimal dependencies
pip install numpy scipy
```

## Quick Start

### 1. List Available Materials

```bash
python -m structural_optimization.cli materials
```

Output shows materials with their properties (PA-CF, ABS, PLA, PETG, PC).

### 2. Validate a CAD File

```bash
python -m structural_optimization.cli validate part.step
```

### 3. Run Optimization

```bash
# Basic optimization
python -m structural_optimization.cli optimize part.step

# With specific output directory
python -m structural_optimization.cli optimize part.step -o ./optimized

# With different material
python -m structural_optimization.cli optimize part.step -m ABS

# With custom configuration
python -m structural_optimization.cli optimize part.step -c config.json

# More iterations for better results
python -m structural_optimization.cli optimize part.step -n 10

# Verbose mode
python -m structural_optimization.cli optimize part.step -v
```

## Configuration

### Material Options

Pre-configured materials:
- **PA-CF**: Carbon fiber reinforced nylon (default) - Best for strength
- **ABS**: Standard thermoplastic
- **PLA**: Bio-based, easy to print
- **PETG**: Impact resistant
- **PC**: High temperature capable

### Custom Configuration File

Create a `config.json`:

```json
{
  "material": {
    "type": "PA-CF",
    "youngs_modulus_mpa": 5500,
    "yield_strength_mpa": 85,
    "density_g_cm3": 1.15
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

## Output Files

The optimization produces:
- `*_optimized.step` - Optimized CAD geometry
- `*_optimized.stl` - 3D printable file
- `*_optimized_metadata.json` - Geometry data
- `optimization_report.json` - Full analysis report

### Example Report

```json
{
  "improvements": {
    "deflection_reduction_percent": 40.3,
    "stiffness_increase_percent": 67.6
  },
  "initial_metrics": {
    "max_deflection_mm": 0.523,
    "mass_g": 45.2
  },
  "final_metrics": {
    "max_deflection_mm": 0.312,
    "mass_g": 48.7
  }
}
```

## Programmatic Usage

```python
from pathlib import Path
from structural_optimization import StructuralOptimizationAgent
from structural_optimization.config import OptimizationConfig, LoadCase, BoundaryCondition

# Configure
config = OptimizationConfig(material_type="PA-CF")

# Define loads and constraints
config.boundary_conditions = [
    BoundaryCondition(type='fixed', location=[0, 0, 0])
]
config.load_cases = [
    LoadCase(type='force', location=[100, 50, 50], magnitude=50.0)
]

# Optimize
agent = StructuralOptimizationAgent(config)
report = agent.optimize(
    input_file=Path("part.step"),
    output_dir=Path("./optimized"),
    max_iterations=5
)

print(f"Deflection reduced by {report['improvements']['deflection_reduction_percent']:.1f}%")
```

## Optimization Strategies

The agent applies multiple strategies:

1. **Reinforcing Ribs**: Added to high-deflection regions
2. **Stabilizing Webs**: Connect parallel surfaces
3. **Closed Sections**: Convert open to closed cross-sections for torsional rigidity
4. **Stress Relief Fillets**: Reduce stress concentrations
5. **Span Reduction**: Shorten unsupported lengths

## Examples

See `examples/example_usage.py` for complete examples:

```bash
python examples/example_usage.py
```

## Running Tests

```bash
pytest tests/test_optimization.py -v
```

All 16 tests should pass.

## Architecture

### Modules

- `agent.py` - Main optimization coordinator
- `cad_handler.py` - CAD import and geometry manipulation
- `fem_analyzer.py` - Finite element analysis
- `geometry_optimizer.py` - Optimization strategies
- `export_handler.py` - Export to STEP/STL/etc
- `config.py` - Configuration management
- `cli.py` - Command-line interface

### Workflow

```
Input CAD → Feature Analysis → FEM → Optimization → Verification → Export
```

## Production Use

This implementation provides a complete framework with placeholder functions for:

- **CAD Processing**: Ready for pythonOCC/CADQuery integration
- **FEM Solving**: Ready for FEniCS/PyFEM integration
- **Meshing**: Ready for gmsh/netgen integration

The architecture, API, and workflow logic are production-ready. To use with real CAD files, integrate appropriate CAD kernels and FEM solvers.

## Documentation

Full documentation: [STRUCTURAL_OPTIMIZATION.md](STRUCTURAL_OPTIMIZATION.md)

## Support

- See examples: `examples/`
- Run tests: `pytest tests/`
- Check help: `python -m structural_optimization.cli --help`
