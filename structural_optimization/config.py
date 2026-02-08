"""
Configuration management for structural optimization.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
from pathlib import Path


@dataclass
class BoundaryCondition:
    """Represents a boundary condition (support, constraint)."""
    type: str  # 'fixed', 'pinned', 'roller', 'symmetric'
    location: List[float]  # [x, y, z] coordinates
    constrained_dof: List[str] = field(default_factory=lambda: ['x', 'y', 'z'])  # degrees of freedom


@dataclass
class LoadCase:
    """Represents a load case (force, moment, pressure)."""
    type: str  # 'force', 'moment', 'pressure', 'thermal'
    location: List[float]  # [x, y, z] coordinates or surface ID
    magnitude: float  # in N, Nm, Pa, or °C
    direction: List[float] = field(default_factory=lambda: [0, 0, -1])  # normalized vector


@dataclass
class OptimizationConfig:
    """Configuration for structural optimization process."""
    
    # Material properties (PA-CF - Carbon Fiber Reinforced Nylon)
    material_type: str = "PA-CF"
    youngs_modulus: float = 5500.0  # MPa (typical for PA-CF)
    poisson_ratio: float = 0.35
    yield_strength: float = 85.0  # MPa
    density: float = 1.15  # g/cm³
    
    # Temperature properties
    temp_min: float = -20.0  # °C
    temp_max: float = 80.0  # °C
    thermal_expansion: float = 5e-5  # 1/°C
    
    # FDM printing parameters
    layer_height: float = 0.2  # mm
    nozzle_diameter: float = 0.4  # mm
    wall_line_count: int = 4
    infill_percentage: float = 40.0
    print_orientation: str = "auto"  # or 'xy', 'xz', 'yz'
    
    # Geometric constraints
    min_wall_thickness: float = 1.6  # mm (4 * 0.4mm nozzle)
    max_unsupported_length: float = 30.0  # mm
    min_rib_thickness: float = 1.2  # mm
    min_hole_diameter: float = 2.0  # mm
    
    # Optimization parameters
    prefer_no_supports: bool = True
    preserve_interfaces: bool = True  # Don't modify mounting interfaces
    max_overhang_angle: float = 45.0  # degrees
    
    # Analysis parameters
    mesh_size: float = 2.0  # mm
    safety_factor: float = 2.0
    
    # Boundary conditions and load cases
    boundary_conditions: List[BoundaryCondition] = field(default_factory=list)
    load_cases: List[LoadCase] = field(default_factory=list)
    
    # Optimization targets
    target_deflection: Optional[float] = None  # mm (if None, minimize)
    target_first_frequency: Optional[float] = None  # Hz (if None, maximize)
    target_mass_reduction: Optional[float] = None  # percentage
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return {
            'material': {
                'type': self.material_type,
                'youngs_modulus_mpa': self.youngs_modulus,
                'poisson_ratio': self.poisson_ratio,
                'yield_strength_mpa': self.yield_strength,
                'density_g_cm3': self.density,
                'temp_range_c': [self.temp_min, self.temp_max],
                'thermal_expansion_per_c': self.thermal_expansion
            },
            'printing': {
                'layer_height_mm': self.layer_height,
                'nozzle_diameter_mm': self.nozzle_diameter,
                'wall_line_count': self.wall_line_count,
                'infill_percentage': self.infill_percentage,
                'print_orientation': self.print_orientation
            },
            'constraints': {
                'min_wall_thickness_mm': self.min_wall_thickness,
                'max_unsupported_length_mm': self.max_unsupported_length,
                'min_rib_thickness_mm': self.min_rib_thickness,
                'prefer_no_supports': self.prefer_no_supports,
                'preserve_interfaces': self.preserve_interfaces,
                'max_overhang_angle_deg': self.max_overhang_angle
            },
            'analysis': {
                'mesh_size_mm': self.mesh_size,
                'safety_factor': self.safety_factor
            },
            'targets': {
                'deflection_mm': self.target_deflection,
                'first_frequency_hz': self.target_first_frequency,
                'mass_reduction_percent': self.target_mass_reduction
            }
        }
    
    @classmethod
    def from_json(cls, json_path: Path) -> 'OptimizationConfig':
        """Load configuration from JSON file."""
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        config = cls()
        
        # Load material properties
        if 'material' in data:
            mat = data['material']
            config.material_type = mat.get('type', config.material_type)
            config.youngs_modulus = mat.get('youngs_modulus_mpa', config.youngs_modulus)
            config.poisson_ratio = mat.get('poisson_ratio', config.poisson_ratio)
            config.yield_strength = mat.get('yield_strength_mpa', config.yield_strength)
            config.density = mat.get('density_g_cm3', config.density)
        
        # Load analysis parameters
        if 'analysis' in data:
            anal = data['analysis']
            config.mesh_size = anal.get('mesh_size_mm', config.mesh_size)
            config.safety_factor = anal.get('safety_factor', config.safety_factor)
        
        # Load boundary conditions
        if 'boundary_conditions' in data:
            config.boundary_conditions = [
                BoundaryCondition(**bc) for bc in data['boundary_conditions']
            ]
        
        # Load load cases
        if 'load_cases' in data:
            config.load_cases = [
                LoadCase(**lc) for lc in data['load_cases']
            ]
        
        return config
    
    def save_json(self, json_path: Path):
        """Save configuration to JSON file."""
        with open(json_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


# Predefined material configurations
MATERIALS = {
    'PA-CF': OptimizationConfig(
        material_type='PA-CF',
        youngs_modulus=5500.0,
        poisson_ratio=0.35,
        yield_strength=85.0,
        density=1.15
    ),
    'ABS': OptimizationConfig(
        material_type='ABS',
        youngs_modulus=2300.0,
        poisson_ratio=0.35,
        yield_strength=40.0,
        density=1.05
    ),
    'PLA': OptimizationConfig(
        material_type='PLA',
        youngs_modulus=3500.0,
        poisson_ratio=0.36,
        yield_strength=50.0,
        density=1.24
    ),
    'PETG': OptimizationConfig(
        material_type='PETG',
        youngs_modulus=2100.0,
        poisson_ratio=0.38,
        yield_strength=50.0,
        density=1.27
    ),
    'PC': OptimizationConfig(
        material_type='PC',
        youngs_modulus=2400.0,
        poisson_ratio=0.37,
        yield_strength=60.0,
        density=1.20
    )
}
