"""
Basic tests for structural optimization agent.
"""

import pytest
from pathlib import Path
import tempfile

from structural_optimization.config import (
    OptimizationConfig,
    BoundaryCondition,
    LoadCase,
    MATERIALS
)


class TestConfig:
    """Tests for configuration management."""
    
    def test_default_config(self):
        """Test default configuration creation."""
        config = OptimizationConfig()
        
        assert config.material_type == "PA-CF"
        assert config.youngs_modulus > 0
        assert config.mesh_size > 0
        assert config.safety_factor > 0
    
    def test_material_presets(self):
        """Test predefined materials."""
        assert "PA-CF" in MATERIALS
        assert "ABS" in MATERIALS
        assert "PLA" in MATERIALS
        
        pa_cf = MATERIALS["PA-CF"]
        assert pa_cf.youngs_modulus == 5500.0
        assert pa_cf.density == 1.15
    
    def test_config_to_dict(self):
        """Test configuration serialization."""
        config = OptimizationConfig()
        config_dict = config.to_dict()
        
        assert 'material' in config_dict
        assert 'printing' in config_dict
        assert 'constraints' in config_dict
        assert 'analysis' in config_dict
    
    def test_config_json_roundtrip(self):
        """Test saving and loading config from JSON."""
        config1 = OptimizationConfig(
            material_type="Test",
            mesh_size=3.0
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            config1.save_json(temp_path)
            config2 = OptimizationConfig.from_json(temp_path)
            
            assert config2.mesh_size == 3.0
        finally:
            temp_path.unlink()
    
    def test_boundary_condition(self):
        """Test boundary condition creation."""
        bc = BoundaryCondition(
            type='fixed',
            location=[0, 0, 0],
            constrained_dof=['x', 'y', 'z']
        )
        
        assert bc.type == 'fixed'
        assert len(bc.location) == 3
        assert len(bc.constrained_dof) == 3
    
    def test_load_case(self):
        """Test load case creation."""
        lc = LoadCase(
            type='force',
            location=[10, 20, 30],
            magnitude=50.0,
            direction=[0, 0, -1]
        )
        
        assert lc.type == 'force'
        assert lc.magnitude == 50.0
        assert len(lc.direction) == 3


class TestCADHandler:
    """Tests for CAD handling."""
    
    def test_cad_handler_init(self):
        """Test CAD handler initialization."""
        from structural_optimization.cad_handler import CADHandler
        
        handler = CADHandler()
        assert handler.current_geometry is None
    
    def test_extract_features(self):
        """Test feature extraction."""
        from structural_optimization.cad_handler import CADHandler
        
        handler = CADHandler()
        geometry = {'type': 'test', 'volume': 1000}
        
        features = handler.extract_features(geometry)
        
        assert 'walls' in features
        assert 'spans' in features
        assert 'holes' in features


class TestFEMAnalyzer:
    """Tests for FEM analysis."""
    
    def test_fem_analyzer_init(self):
        """Test FEM analyzer initialization."""
        from structural_optimization.fem_analyzer import FEMAnalyzer
        
        config = OptimizationConfig()
        analyzer = FEMAnalyzer(config)
        
        assert analyzer.config == config
    
    def test_mesh_generation(self):
        """Test mesh generation."""
        from structural_optimization.fem_analyzer import FEMAnalyzer
        
        config = OptimizationConfig(mesh_size=2.0)
        analyzer = FEMAnalyzer(config)
        
        geometry = {'type': 'test', 'volume': 1000}
        mesh = analyzer._generate_mesh(geometry)
        
        assert mesh['num_nodes'] > 0
        assert mesh['num_elements'] > 0
        assert mesh['element_type'] == 'tetrahedron'


class TestGeometryOptimizer:
    """Tests for geometry optimization."""
    
    def test_optimizer_init(self):
        """Test optimizer initialization."""
        from structural_optimization.geometry_optimizer import GeometryOptimizer
        
        config = OptimizationConfig()
        optimizer = GeometryOptimizer(config)
        
        assert optimizer.config == config
    
    def test_add_ribs(self):
        """Test rib addition strategy."""
        from structural_optimization.geometry_optimizer import GeometryOptimizer
        import numpy as np
        
        config = OptimizationConfig()
        optimizer = GeometryOptimizer(config)
        
        geometry = {'type': 'test', 'volume': 1000}
        fem_results = {
            'displacements': np.random.rand(100, 3),
            'max_deflection': 1.0
        }
        
        ribs = optimizer._add_reinforcing_ribs(geometry, fem_results)
        
        assert isinstance(ribs, list)
        for rib in ribs:
            assert rib['type'] == 'add_rib'
            assert 'thickness' in rib


class TestExportHandler:
    """Tests for export functionality."""
    
    def test_export_handler_init(self):
        """Test export handler initialization."""
        from structural_optimization.export_handler import ExportHandler
        
        handler = ExportHandler()
        assert handler is not None
    
    def test_export_step(self):
        """Test STEP file export."""
        from structural_optimization.export_handler import ExportHandler
        
        handler = ExportHandler()
        geometry = {'type': 'test', 'volume': 1000}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.step"
            handler.export_step(geometry, output_path)
            
            assert output_path.exists()
            assert output_path.stat().st_size > 0
    
    def test_export_stl(self):
        """Test STL file export."""
        from structural_optimization.export_handler import ExportHandler
        
        handler = ExportHandler()
        geometry = {'type': 'test', 'volume': 1000}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.stl"
            handler.export_stl(geometry, output_path)
            
            assert output_path.exists()


class TestIntegration:
    """Integration tests."""
    
    def test_agent_init(self):
        """Test agent initialization."""
        from structural_optimization import StructuralOptimizationAgent
        
        config = OptimizationConfig()
        agent = StructuralOptimizationAgent(config)
        
        assert agent.config == config
        assert agent.current_iteration == 0
        assert len(agent.iteration_history) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
