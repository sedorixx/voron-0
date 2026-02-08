# Structural Optimization Agent for 3D Printed Parts

Ein autonomer Engineering-Agent zur strukturellen Optimierung von 3D-Druck-Bauteilen mit dem Ziel, maximale Steifigkeit bei minimaler Durchbiegung zu erreichen.

## Überblick

Dieser Agent implementiert einen iterativen, deterministischen Optimierungsprozess für 3D-Druckteile:

1. **CAD-Import**: Unterstützt STEP, STL und native CAD-Formate
2. **Strukturanalyse**: FEM-Analyse (statisch + modal)
3. **Geometrieoptimierung**: Rippen, Stege, geschlossene Querschnitte
4. **Verifizierung**: Erneute Simulation zur Validierung
5. **Export**: Optimierte CAD- und STL-Dateien

## Features

### Optimierungsstrategien

- **Rippen und Stege**: Verstärkung in hochbelasteten Bereichen
- **Geschlossene Querschnitte**: Erhöhte Torsionssteifigkeit
- **Wandverlagerung**: Effizienter als Materialverdickung
- **Spannweiten-Reduktion**: Verkürzung freier Längen
- **Verrundungen**: Reduzierung von Spannungsspitzen
- **Topologieoptimierung**: Optional verfügbar

### Material-Unterstützung

Vorkonfigurierte Materialien:
- **PA-CF**: Carbon Fiber verstärktes Nylon (Standard)
- **ABS**: Standard-Thermoplast
- **PLA**: Bio-basierter Kunststoff
- **PETG**: Schlagzähes Material
- **PC**: Hochtemperatur-fähig

### FDM-Druckbarkeit

- Bevorzugt supportfreies Drucken
- Überhangwinkel-Prüfung
- Minimale Wandstärken
- Schicht-orientierte Optimierung

## Installation

```bash
# Repository klonen
git clone https://github.com/sedorixx/voron-0.git
cd voron-0

# Abhängigkeiten installieren
pip install -r requirements.txt
```

## Verwendung

### Kommandozeilen-Interface

#### Optimierung durchführen

```bash
# Einfache Optimierung mit PA-CF Material
python -m structural_optimization.cli optimize part.step

# Mit spezifischer Ausgabeverzeichnis
python -m structural_optimization.cli optimize part.step -o ./optimized_output

# Mit anderem Material
python -m structural_optimization.cli optimize part.step -m ABS

# Mit benutzerdefinierter Konfiguration
python -m structural_optimization.cli optimize part.step -c config.json

# Mehr Iterationen
python -m structural_optimization.cli optimize part.step -n 10

# Verbose-Modus für detaillierte Logs
python -m structural_optimization.cli optimize part.step -v
```

#### CAD-Datei validieren

```bash
python -m structural_optimization.cli validate part.step
```

#### Verfügbare Materialien auflisten

```bash
python -m structural_optimization.cli materials
```

### Programmatische Verwendung

```python
from pathlib import Path
from structural_optimization import StructuralOptimizationAgent
from structural_optimization.config import OptimizationConfig, LoadCase, BoundaryCondition

# Konfiguration erstellen
config = OptimizationConfig(
    material_type="PA-CF",
    mesh_size=2.0,
    prefer_no_supports=True
)

# Randbedingungen definieren
config.boundary_conditions = [
    BoundaryCondition(
        type='fixed',
        location=[0, 0, 0],
        constrained_dof=['x', 'y', 'z']
    )
]

# Lastfälle definieren
config.load_cases = [
    LoadCase(
        type='force',
        location=[100, 100, 100],
        magnitude=50.0,  # N
        direction=[0, 0, -1]
    )
]

# Agent initialisieren und optimieren
agent = StructuralOptimizationAgent(config)
report = agent.optimize(
    input_file=Path("part.step"),
    output_dir=Path("./optimized"),
    max_iterations=5
)

# Ergebnisse ausgeben
print(f"Durchbiegung reduziert um {report['improvements']['deflection_reduction_percent']:.1f}%")
print(f"Ausgabedateien: {report['output_files']}")
```

### Konfigurationsdatei

Beispiel `config.json`:

```json
{
  "material": {
    "type": "PA-CF",
    "youngs_modulus_mpa": 5500,
    "poisson_ratio": 0.35,
    "yield_strength_mpa": 85,
    "density_g_cm3": 1.15
  },
  "printing": {
    "layer_height_mm": 0.2,
    "nozzle_diameter_mm": 0.4,
    "wall_line_count": 4,
    "infill_percentage": 40
  },
  "constraints": {
    "min_wall_thickness_mm": 1.6,
    "max_unsupported_length_mm": 30,
    "prefer_no_supports": true,
    "preserve_interfaces": true,
    "max_overhang_angle_deg": 45
  },
  "analysis": {
    "mesh_size_mm": 2.0,
    "safety_factor": 2.0
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

## Ausgabe

Der Optimierungsprozess erstellt folgende Dateien:

- `*_optimized.step`: Optimierte CAD-Geometrie (STEP-Format)
- `*_optimized.stl`: Druckbereite STL-Datei
- `*_optimized_metadata.json`: Geometrie-Metadaten
- `optimization_report.json`: Vollständiger Optimierungsbericht

### Optimierungsbericht

Der Bericht enthält:

```json
{
  "optimization_summary": {
    "iterations": 5,
    "best_iteration": 3,
    "converged": true
  },
  "initial_metrics": {
    "max_deflection_mm": 0.523,
    "mass_g": 45.2,
    "max_stress_mpa": 28.5
  },
  "final_metrics": {
    "max_deflection_mm": 0.312,
    "mass_g": 48.7,
    "max_stress_mpa": 22.1
  },
  "improvements": {
    "deflection_reduction_percent": 40.3,
    "stiffness_increase_percent": 67.6
  }
}
```

## Architektur

### Module

- **agent.py**: Hauptkoordinator des Optimierungsprozesses
- **cad_handler.py**: CAD-Import und Geometrie-Manipulation
- **fem_analyzer.py**: Finite-Elemente-Analyse
- **geometry_optimizer.py**: Geometrieoptimierung mit verschiedenen Strategien
- **export_handler.py**: Export in verschiedene Formate
- **config.py**: Konfigurationsmanagement
- **cli.py**: Kommandozeilen-Interface

### Workflow

```
Input CAD File
     ↓
CAD Import
     ↓
Feature Extraction
     ↓
╔═══════════════════╗
║ Optimization Loop ║
║                   ║
║ FEM Analysis  →   ║
║ Geometry Opt  →   ║
║ Convergence Check ║
╚═══════════════════╝
     ↓
Final Verification
     ↓
Export (STEP + STL)
```

## Anforderungen

- Python 3.8+
- NumPy, SciPy (für numerische Berechnungen)
- Optional: pythonOCC, CADQuery (für echte CAD-Verarbeitung)
- Optional: FEniCS, PyFEM (für echte FEM-Analyse)

## Entwicklungsstatus

**Aktueller Stand**: Vollständige Framework-Implementierung mit Platzhaltern für:
- CAD-Kernelfunktionen (bereit für pythonOCC/CADQuery Integration)
- FEM-Solver (bereit für FEniCS/PyFEM Integration)
- Mesh-Generierung (bereit für gmsh/netgen Integration)

**Produktionsbereit**: Architektur, API, Workflow-Logik

**Benötigt für Produktion**: Integration echter CAD-Kernel und FEM-Solver

## Erweiterung

### Eigene Optimierungsstrategie hinzufügen

```python
from structural_optimization.geometry_optimizer import GeometryOptimizer

class MyOptimizer(GeometryOptimizer):
    def optimize(self, geometry, fem_results, critical_regions):
        # Eigene Logik hier
        modifications = []
        # ...
        return self.cad_handler.apply_modifications(geometry, modifications)
```

### Neues Material definieren

```python
from structural_optimization.config import OptimizationConfig

my_material = OptimizationConfig(
    material_type="My-Material",
    youngs_modulus=6000.0,  # MPa
    poisson_ratio=0.33,
    yield_strength=95.0,    # MPa
    density=1.18            # g/cm³
)
```

## Lizenz

Siehe LICENSE Datei im Repository.

## Beitragen

Beiträge sind willkommen! Bitte erstellen Sie einen Pull Request oder öffnen Sie ein Issue.

## Kontakt

Für Fragen und Support: Siehe Repository Issues auf GitHub
