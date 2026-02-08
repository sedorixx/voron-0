# Workflow Architecture Diagram

## Complete Optimization Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Parametric Optimization Workflow                     │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   FreeCAD    │  Step 1: Load Parametric Model
│ (Parametric) │  - Extract design parameters
│              │  - Load geometry
└──────┬───────┘
       │
       ▼
┌──────────────┐
│     Gmsh     │  Step 2: Generate Mesh
│   (Meshing)  │  - Convert CAD to FEM mesh
│              │  - Configurable element size
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   FEniCS     │  Step 3: FEM Analysis
│      or      │  - Structural analysis
│  CalculiX    │  - Calculate deflections & stresses
│    (FEM)     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   OpenMDAO   │  Step 4: Optimization
│(Optimization)│  - Update design parameters
│              │  - Minimize deflection
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   FreeCAD    │  Step 5: Update Geometry
│  (Updated)   │  - Apply optimized parameters
│              │  - Generate new model
└──────┬───────┘
       │
       │ Converged? ──No──> Loop back to Step 2
       │
       ▼ Yes
┌──────────────┐
│   Export     │  Final Step: Export Results
│  Results     │  - STEP file (CAD)
│              │  - STL file (3D printing)
│              │  - JSON report
└──────────────┘
```

## Interface Components

### 1. FreeCADInterface
```
┌─────────────────────────────┐
│      FreeCADInterface       │
├─────────────────────────────┤
│ • load_parametric_model()   │
│ • update_geometry()         │
│ • export_step()             │
└─────────────────────────────┘
         │
         ├─► Supports: .FCStd, .step, .stp
         └─► Auto-detects installed FreeCAD
```

### 2. GmshInterface
```
┌─────────────────────────────┐
│       GmshInterface         │
├─────────────────────────────┤
│ • generate_mesh()           │
│ • Configurable mesh size    │
│ • Tetrahedral elements      │
└─────────────────────────────┘
         │
         ├─► Output: .msh format
         └─► Auto-detects Gmsh library
```

### 3. FEMSolverInterface
```
┌─────────────────────────────┐
│     FEMSolverInterface      │
├─────────────────────────────┤
│ • run_analysis()            │
│ • Static structural         │
│ • Supports FEniCS/CalculiX  │
└─────────────────────────────┘
         │
         ├─► Returns: displacements, stresses
         └─► Material properties configurable
```

### 4. OpenMDAOInterface
```
┌─────────────────────────────┐
│     OpenMDAOInterface       │
├─────────────────────────────┤
│ • setup_optimization()      │
│ • run_optimization()        │
│ • SLSQP algorithm           │
└─────────────────────────────┘
         │
         ├─► Design variables: thickness, width, etc.
         └─► Constraints: stress, mass limits
```

### 5. WorkflowOrchestrator
```
┌─────────────────────────────────────────┐
│        WorkflowOrchestrator             │
├─────────────────────────────────────────┤
│ • run_workflow()                        │
│ • get_workflow_status()                 │
│ • Convergence checking                  │
│ • Iteration management                  │
│ • Progress reporting                    │
└─────────────────────────────────────────┘
         │
         ├─► Coordinates all interfaces
         ├─► Manages optimization loop
         └─► Generates comprehensive reports
```

## Data Flow

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ Parametric  │       │    Mesh     │       │    FEM      │
│   Model     │  ───► │    Data     │  ───► │  Results    │
│             │       │             │       │             │
│ parameters: │       │ nodes: 500  │       │ deflection: │
│  thickness  │       │ elements:   │       │  0.523 mm   │
│  width      │       │  800        │       │ stress:     │
│  height     │       │             │       │  28.5 MPa   │
└─────────────┘       └─────────────┘       └─────────────┘
                                                    │
                                                    ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  Updated    │       │  Optimal    │       │ Objective   │
│  Geometry   │  ◄─── │ Parameters  │  ◄─── │ Function    │
│             │       │             │       │             │
│ thickness:  │       │ thickness:  │       │ minimize:   │
│  2.8 mm     │       │  2.8        │       │  deflection │
│ width:      │       │ width: 52.3 │       │ subject to: │
│  52.3 mm    │       │ ...         │       │  constraints│
└─────────────┘       └─────────────┘       └─────────────┘
```

## Convergence Loop

```
Iteration 1:  deflection = 0.523 mm  ─┐
                                       │
Iteration 2:  deflection = 0.412 mm  ─┤  Improvement > 1%
                                       │  Continue...
Iteration 3:  deflection = 0.368 mm  ─┤
                                       │
Iteration 4:  deflection = 0.346 mm  ─┤
                                       │
Iteration 5:  deflection = 0.343 mm  ─┘  Improvement < 1%
                                          CONVERGED ✓
```

## Configuration Options

```
┌───────────────────────────────────────────┐
│         Configuration Options              │
├───────────────────────────────────────────┤
│ Material Presets:                         │
│   • PA-CF (Carbon Fiber Nylon)            │
│   • ABS                                   │
│   • PLA                                   │
│   • PETG                                  │
│   • PC (Polycarbonate)                    │
│                                           │
│ FEM Solvers:                              │
│   • FEniCS (Python-based)                 │
│   • CalculiX (Industrial)                 │
│                                           │
│ Optimization:                             │
│   • Max iterations: 10 (default)          │
│   • Convergence: 1% (default)             │
│   • Mesh size: 2.0mm (default)            │
│   • Safety factor: 2.0 (default)          │
└───────────────────────────────────────────┘
```

## CLI Usage

```bash
# Basic workflow
python -m structural_optimization.cli workflow part.step

# With options
python -m structural_optimization.cli workflow part.step \
    --output-dir ./optimized \
    --material PA-CF \
    --fem-solver fenics \
    --max-iterations 15 \
    --convergence-tolerance 0.005 \
    --mesh-size 1.5

# Check status
python -m structural_optimization.cli materials
```

## Output Files

```
output_directory/
├── optimized_geometry.step       # Final CAD geometry
├── optimized_geometry.stl        # 3D printable file
├── optimized_mesh.msh            # Final FEM mesh
├── workflow_report.json          # Complete report
├── iteration_0_geometry.step     # Intermediate files
├── iteration_0_mesh.msh
├── iteration_1_geometry.step
├── iteration_1_mesh.msh
└── ...
```

## Testing

```
┌─────────────────────────────────────────┐
│          Test Coverage                   │
├─────────────────────────────────────────┤
│ Unit Tests:                             │
│  ✓ FreeCAD Interface (4 tests)          │
│  ✓ Gmsh Interface (2 tests)             │
│  ✓ FEM Solver Interface (3 tests)       │
│  ✓ OpenMDAO Interface (3 tests)         │
│  ✓ Workflow Orchestrator (3 tests)      │
│  ✓ Integration Tests (1 test)           │
│                                         │
│ Total: 32 tests, all passing ✓          │
└─────────────────────────────────────────┘
```
