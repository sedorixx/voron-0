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


class TestEdgeCases:
    """Tests for edge cases and bug fixes."""
    
    def test_config_validation_negative_youngs_modulus(self):
        """Test that negative Young's modulus is rejected."""
        with pytest.raises(ValueError, match="Young's modulus must be positive"):
            OptimizationConfig(youngs_modulus=-1000.0)
    
    def test_config_validation_zero_youngs_modulus(self):
        """Test that zero Young's modulus is rejected."""
        with pytest.raises(ValueError, match="Young's modulus must be positive"):
            OptimizationConfig(youngs_modulus=0.0)
    
    def test_config_validation_negative_density(self):
        """Test that negative density is rejected."""
        with pytest.raises(ValueError, match="Density must be positive"):
            OptimizationConfig(density=-1.5)
    
    def test_config_validation_negative_mesh_size(self):
        """Test that negative mesh size is rejected."""
        with pytest.raises(ValueError, match="Mesh size must be positive"):
            OptimizationConfig(mesh_size=-2.0)
    
    def test_config_validation_negative_safety_factor(self):
        """Test that negative safety factor is rejected."""
        with pytest.raises(ValueError, match="Safety factor must be positive"):
            OptimizationConfig(safety_factor=-1.0)
    
    def test_config_validation_invalid_poisson_ratio(self):
        """Test that invalid Poisson ratio is rejected."""
        with pytest.raises(ValueError, match="Poisson ratio must be in range"):
            OptimizationConfig(poisson_ratio=0.6)
        with pytest.raises(ValueError, match="Poisson ratio must be in range"):
            OptimizationConfig(poisson_ratio=-0.1)
    
    def test_boundary_condition_invalid_location(self):
        """Test that invalid boundary condition location is rejected."""
        with pytest.raises(TypeError, match="location must be a list"):
            BoundaryCondition(type='fixed', location="not a list")
        
        with pytest.raises(TypeError, match="location must be a list"):
            BoundaryCondition(type='fixed', location=[0, 0])  # Too short
        
        with pytest.raises(TypeError, match="location coordinates must be numeric"):
            BoundaryCondition(type='fixed', location=["a", "b", "c"])
    
    def test_load_case_invalid_magnitude(self):
        """Test that invalid load magnitude is rejected."""
        with pytest.raises(TypeError, match="magnitude must be numeric"):
            LoadCase(type='force', location=[0, 0, 0], magnitude="fifty")
    
    def test_load_case_invalid_direction(self):
        """Test that invalid load direction is rejected."""
        with pytest.raises(TypeError, match="direction must be a list"):
            LoadCase(type='force', location=[0, 0, 0], magnitude=50.0, direction="down")
    
    def test_export_handler_path_traversal(self):
        """Test that path traversal is prevented in export handler."""
        from structural_optimization.export_handler import ExportHandler
        
        handler = ExportHandler()
        geometry = {'type': 'test', 'volume': 1000}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "safe_dir"
            output_dir.mkdir()
            
            # Try to escape with path traversal
            malicious_name = "../../../malicious"
            output_files = handler.export_all(geometry, output_dir, malicious_name)
            
            # Verify files are created in safe directory, not escaped
            for file_path in output_files.values():
                assert Path(file_path).parent == output_dir
                assert "../" not in file_path
    
    def test_agent_division_by_zero_handling(self):
        """Test that division by zero is handled in agent report generation."""
        from structural_optimization import StructuralOptimizationAgent
        import numpy as np
        
        config = OptimizationConfig()
        agent = StructuralOptimizationAgent(config)
        
        # Simulate scenario with zero deflection
        agent.iteration_history = [
            {'max_deflection': 0.0, 'mass': 100, 'max_stress': 10, 'first_eigenfrequency': 50}
        ]
        
        best_result = {
            'iteration': 0,
            'geometry': {'type': 'test', 'volume': 1000},
            'fem_results': {'max_deflection': 0.0, 'mass': 100, 'max_stress': 10},
            'deflection': 0.0
        }
        
        final_fem = {
            'max_deflection': 0.0,
            'mass': 100,
            'max_stress': 10,
            'first_eigenfrequency': 50
        }
        
        output_files = {}
        
        # Should not raise division by zero error
        report = agent._generate_report(best_result, final_fem, output_files)
        
        assert report is not None
        assert report['improvements']['deflection_reduction_percent'] == 0.0
    
    def test_agent_json_sanitization(self):
        """Test that inf/nan values are sanitized before JSON export."""
        from structural_optimization import StructuralOptimizationAgent
        import math
        
        config = OptimizationConfig()
        agent = StructuralOptimizationAgent(config)
        
        # Test sanitization function
        test_data = {
            'value1': float('inf'),
            'value2': float('-inf'),
            'value3': float('nan'),
            'value4': 42.0,
            'nested': {
                'inf_value': float('inf'),
                'normal': 10
            },
            'list': [1, 2, float('nan'), 4]
        }
        
        sanitized = agent._sanitize_for_json(test_data)
        
        assert sanitized['value1'] is None
        assert sanitized['value2'] is None
        assert sanitized['value3'] is None
        assert sanitized['value4'] == 42.0
        assert sanitized['nested']['inf_value'] is None
        assert sanitized['nested']['normal'] == 10
        assert sanitized['list'][2] is None
    
    def test_fem_analyzer_zero_youngs_modulus(self):
        """Test that FEM analyzer rejects zero Young's modulus."""
        from structural_optimization.fem_analyzer import FEMAnalyzer
        
        # Create config with zero modulus (should be caught by config validation)
        # But test FEM analyzer's own validation too
        config = OptimizationConfig()
        analyzer = FEMAnalyzer(config)
        
        geometry = {'type': 'test', 'volume': 1000}
        mesh = analyzer._generate_mesh(geometry)
        
        # Manually set invalid E to test FEM validation
        mesh['material'] = {'E': 0.0, 'nu': 0.35, 'rho': 1.15, 'yield_strength': 85}
        mesh['boundary_conditions'] = []
        mesh['loads'] = [{'type': 'force', 'magnitude': 50.0}]
        
        with pytest.raises(ValueError, match="Young's modulus must be positive"):
            analyzer._solve_static(mesh)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
