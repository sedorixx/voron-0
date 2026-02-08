# Quick Start Guide - Workflow Integration

## What is this?

An automated optimization workflow for 3D printed parts that chains together professional CAD and FEM tools:

```
FreeCAD → Gmsh → FEniCS/CalculiX → OpenMDAO → FreeCAD (optimized)
```

## 5-Minute Quick Start

### 1. Install

```bash
# Minimal installation (for testing)
pip install numpy scipy pytest

# Full installation (for production)
pip install numpy scipy gmsh fenics openmdao
# Plus: Install FreeCAD from freecadweb.org
```

### 2. Run Your First Optimization

```bash
# Test with placeholder implementations (no external tools needed)
python -m structural_optimization.cli workflow examples/test.step

# With custom settings
python -m structural_optimization.cli workflow part.step \
    --material PA-CF \
    --fem-solver fenics \
    --max-iterations 10 \
    --output-dir ./optimized
```

### 3. Check the Results

The workflow creates:
- `optimized_geometry.step` - Your optimized CAD file
- `optimized_geometry.stl` - Ready for 3D printing
- `workflow_report.json` - Detailed optimization report

## What Does It Do?

### The Problem
You have a 3D printed part that deflects too much under load. You want to strengthen it without adding unnecessary material.

### The Solution
The workflow automatically:

1. **Loads your parametric CAD model** (FreeCAD)
   - Extracts design parameters (thickness, width, rib spacing, etc.)

2. **Generates a finite element mesh** (Gmsh)
   - Converts your geometry into thousands of small elements for analysis

3. **Runs structural analysis** (FEniCS or CalculiX)
   - Calculates how your part deflects and stresses under load
   - Identifies weak points

4. **Optimizes the design** (OpenMDAO)
   - Adjusts parameters to minimize deflection
   - Respects constraints (max stress, printability, etc.)

5. **Updates the geometry** (FreeCAD)
   - Creates new geometry with optimized parameters

6. **Repeats until optimized**
   - Continues until improvement is below threshold

### Example Result

```
Before:  Max deflection = 0.523 mm
After:   Max deflection = 0.312 mm
Result:  40% improvement in stiffness!
```

## Common Use Cases

### Case 1: Strengthen a Bracket
```bash
python -m structural_optimization.cli workflow bracket.step \
    --material PA-CF \
    --output-dir ./optimized_bracket
```

### Case 2: Reduce Deflection in a Frame
```bash
python -m structural_optimization.cli workflow frame.step \
    --material ABS \
    --max-iterations 15 \
    --convergence-tolerance 0.005
```

### Case 3: High-Load Application
```bash
python -m structural_optimization.cli workflow part.step \
    --material PA-CF \
    --fem-solver calculix \
    --mesh-size 1.5
```

## Command Reference

### Basic Syntax
```bash
python -m structural_optimization.cli workflow INPUT_FILE [OPTIONS]
```

### Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output-dir` | Where to save results | `./workflow_output` |
| `-m, --material` | Material preset | `PA-CF` |
| `--fem-solver` | FEM solver to use | `fenics` |
| `-n, --max-iterations` | Max optimization loops | `10` |
| `--convergence-tolerance` | When to stop optimizing | `0.01` (1%) |
| `--mesh-size` | FEM mesh element size (mm) | `2.0` |
| `-v, --verbose` | Show detailed logs | Off |

### Material Options

Choose from pre-configured materials:

- **PA-CF** - Carbon Fiber Nylon (strongest, recommended)
- **ABS** - Standard thermoplastic
- **PLA** - Easy to print
- **PETG** - Impact resistant
- **PC** - High temperature

### FEM Solver Options

- **fenics** - Fast, Python-based (default)
- **calculix** - Industrial-strength, more accurate

## Python API

For more control, use the Python API directly:

```python
from pathlib import Path
from structural_optimization.workflow_orchestrator import WorkflowOrchestrator
from structural_optimization.config import OptimizationConfig, LoadCase, BoundaryCondition

# Create configuration
config = OptimizationConfig(material_type="PA-CF")

# Define where part is fixed
config.boundary_conditions = [
    BoundaryCondition(
        type='fixed',
        location=[0, 0, 0],  # Fixed at origin
        constrained_dof=['x', 'y', 'z']  # Cannot move in any direction
    )
]

# Define applied loads
config.load_cases = [
    LoadCase(
        type='force',
        location=[100, 50, 50],  # Where force is applied
        magnitude=50.0,          # 50 Newtons
        direction=[0, 0, -1]     # Downward
    )
]

# Run workflow
orchestrator = WorkflowOrchestrator(config, fem_solver='fenics')
results = orchestrator.run_workflow(
    input_file=Path("bracket.step"),
    output_dir=Path("./output"),
    max_iterations=10
)

# Check results
print(f"Deflection reduced by {results['improvements']['deflection_reduction_percent']:.1f}%")
print(f"Optimal parameters: {results['optimal_parameters']}")
```

## Understanding the Output

### workflow_report.json

```json
{
  "workflow": {
    "iterations": 5,
    "converged": true,
    "elapsed_time_seconds": 45.2
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
    "deflection_reduction_percent": 40.3
  },
  "tools": {
    "cad": "FreeCAD",
    "meshing": "Gmsh",
    "fem_solver": "FENICS",
    "optimization": "OpenMDAO"
  }
}
```

### What to Look For

- **deflection_reduction_percent**: Higher is better (goal: >20%)
- **iterations**: Fewer means faster convergence
- **converged**: Should be `true` for good results
- **max_stress_mpa**: Should be below material yield strength

## Troubleshooting

### "No improvement found"
- Try more iterations: `--max-iterations 20`
- Use finer mesh: `--mesh-size 1.5`
- Check if design space allows improvement

### "Workflow takes too long"
- Use coarser mesh: `--mesh-size 3.0`
- Reduce iterations: `--max-iterations 5`
- Switch to faster solver: `--fem-solver fenics`

### "Tools not found" warnings
These are OK! The workflow uses placeholder implementations for testing. To use real tools, install:
- FreeCAD from https://www.freecadweb.org/
- Gmsh: `pip install gmsh`
- FEniCS: `pip install fenics`
- OpenMDAO: `pip install openmdao`

## Examples

Run the provided examples:

```bash
# See all 4 examples in action
python examples/example_workflow.py

# Or run existing optimization examples
python examples/example_usage.py
```

## Testing

Verify everything works:

```bash
# Run all tests (should see 32 passed)
pytest tests/ -v

# Run just workflow tests
pytest tests/test_workflow.py -v
```

## Next Steps

1. **Try with your own part**: Export a STEP file from your CAD software
2. **Experiment with materials**: Try different options to see which works best
3. **Adjust convergence**: Balance speed vs. optimization quality
4. **Read full docs**: See WORKFLOW_INTEGRATION.md for complete details

## Getting Help

- **Documentation**: See WORKFLOW_INTEGRATION.md
- **Diagrams**: See WORKFLOW_DIAGRAM.md
- **General info**: See STRUCTURAL_OPTIMIZATION.md
- **Examples**: Check examples/ directory

## Summary

This workflow automates structural optimization using professional tools:
- ✅ No manual analysis needed
- ✅ Engineering-based optimization
- ✅ Works with placeholder implementations (no external tools required for testing)
- ✅ Production-ready when real tools are installed
- ✅ Comprehensive reporting
- ✅ Fully tested and documented

**Start optimizing in 5 minutes:**
```bash
pip install numpy scipy
python -m structural_optimization.cli workflow your_part.step
```

Happy optimizing! 🚀
