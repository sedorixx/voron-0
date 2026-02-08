"""
Tests for workflow integration components.
"""

import pytest
import tempfile
from pathlib import Path

from structural_optimization.workflow_integration import (
    FreeCADInterface,
    GmshInterface,
    FEMSolverInterface,
    OpenMDAOInterface
)
from structural_optimization.workflow_orchestrator import WorkflowOrchestrator
from structural_optimization.config import OptimizationConfig


class TestFreeCADInterface:
    """Test FreeCAD interface."""
    
    def test_freecad_init(self):
        """Test FreeCAD interface initialization."""
        interface = FreeCADInterface()
        assert interface is not None
        assert hasattr(interface, 'freecad_available')
    
    def test_load_parametric_model(self):
        """Test loading parametric model."""
        interface = FreeCADInterface()
        with tempfile.NamedTemporaryFile(suffix='.step', delete=False) as f:
            test_file = Path(f.name)
        
        try:
            model = interface.load_parametric_model(test_file)
            assert 'parameters' in model
            assert 'geometry' in model
            assert 'metadata' in model
            assert model['metadata']['parametric'] is True
        finally:
            test_file.unlink()
    
    def test_update_geometry(self):
        """Test updating geometry with new parameters."""
        interface = FreeCADInterface()
        model = {
            'parameters': {'thickness': 2.0, 'width': 50.0},
            'geometry': {'vertices': []},
            'metadata': {}
        }
        
        new_params = {'thickness': 3.0}
        updated_model = interface.update_geometry(model, new_params)
        
        assert updated_model['parameters']['thickness'] == 3.0
        assert updated_model['parameters']['width'] == 50.0
    
    def test_export_step(self):
        """Test STEP export."""
        interface = FreeCADInterface()
        model = {
            'parameters': {},
            'geometry': {},
            'metadata': {}
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / 'test.step'
            result = interface.export_step(model, output_file)
            assert result == output_file
            assert output_file.exists()


class TestGmshInterface:
    """Test Gmsh interface."""
    
    def test_gmsh_init(self):
        """Test Gmsh interface initialization."""
        interface = GmshInterface(mesh_size=2.0)
        assert interface is not None
        assert interface.mesh_size == 2.0
        assert hasattr(interface, 'gmsh_available')
    
    def test_generate_mesh(self):
        """Test mesh generation."""
        interface = GmshInterface(mesh_size=1.5)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy geometry file
            geom_file = Path(tmpdir) / 'test.step'
            geom_file.write_text('test')
            
            mesh_file = Path(tmpdir) / 'test.msh'
            mesh_data = interface.generate_mesh(geom_file, mesh_file)
            
            assert 'nodes' in mesh_data
            assert 'n_nodes' in mesh_data
            assert 'n_elements' in mesh_data
            assert mesh_data['mesh_size'] == 1.5
            assert mesh_file.exists()


class TestFEMSolverInterface:
    """Test FEM solver interface."""
    
    def test_fem_solver_init_fenics(self):
        """Test FEM solver initialization with FEniCS."""
        interface = FEMSolverInterface(solver_type='fenics')
        assert interface is not None
        assert interface.solver_type == 'fenics'
        assert hasattr(interface, 'solver_available')
    
    def test_fem_solver_init_calculix(self):
        """Test FEM solver initialization with CalculiX."""
        interface = FEMSolverInterface(solver_type='calculix')
        assert interface is not None
        assert interface.solver_type == 'calculix'
    
    def test_run_analysis(self):
        """Test running FEM analysis."""
        interface = FEMSolverInterface(solver_type='fenics')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            mesh_file = Path(tmpdir) / 'test.msh'
            mesh_file.write_text('test mesh')
            
            material_props = {
                'youngs_modulus': 5500.0,
                'poisson_ratio': 0.35,
                'density': 1.15
            }
            
            results = interface.run_analysis(
                mesh_file=mesh_file,
                material_properties=material_props,
                boundary_conditions=[],
                load_cases=[]
            )
            
            assert 'displacements' in results
            assert 'stresses' in results
            assert 'max_displacement' in results
            assert 'converged' in results
            assert results['solver'] == 'fenics'


class TestOpenMDAOInterface:
    """Test OpenMDAO interface."""
    
    def test_openmDAO_init(self):
        """Test OpenMDAO interface initialization."""
        interface = OpenMDAOInterface()
        assert interface is not None
        assert hasattr(interface, 'openmDAO_available')
    
    def test_setup_optimization(self):
        """Test optimization setup."""
        interface = OpenMDAOInterface()
        
        design_vars = {
            'thickness': (2.0, 1.0, 5.0),
            'width': (50.0, 30.0, 100.0)
        }
        
        objective = 'deflection'
        constraints = {
            'stress': ('upper', 85.0)
        }
        
        problem = interface.setup_optimization(design_vars, objective, constraints)
        
        assert problem is not None
        assert 'design_variables' in problem or hasattr(problem, 'model')
    
    def test_run_optimization(self):
        """Test running optimization."""
        interface = OpenMDAOInterface()
        
        design_vars = {
            'thickness': (2.0, 1.0, 5.0)
        }
        
        problem = interface.setup_optimization(
            design_vars,
            'objective',
            {}
        )
        
        def eval_func(params):
            return {
                'objective': params['thickness'] ** 2
            }
        
        results = interface.run_optimization(problem, eval_func, max_iterations=5)
        
        assert 'optimal_variables' in results
        assert 'optimal_objective' in results
        assert 'iterations' in results
        assert 'converged' in results


class TestWorkflowOrchestrator:
    """Test workflow orchestrator."""
    
    def test_orchestrator_init(self):
        """Test workflow orchestrator initialization."""
        config = OptimizationConfig(material_type='PA-CF')
        orchestrator = WorkflowOrchestrator(config, fem_solver='fenics')
        
        assert orchestrator is not None
        assert orchestrator.config == config
        assert orchestrator.freecad is not None
        assert orchestrator.gmsh is not None
        assert orchestrator.fem_solver is not None
        assert orchestrator.openmDAO is not None
    
    def test_get_workflow_status(self):
        """Test getting workflow status."""
        config = OptimizationConfig(material_type='PA-CF')
        orchestrator = WorkflowOrchestrator(config)
        
        status = orchestrator.get_workflow_status()
        
        assert status is not None
        assert 'status' in status
        assert status['status'] == 'not_started'
        assert status['iterations'] == 0
    
    def test_define_design_variables(self):
        """Test design variable definition."""
        config = OptimizationConfig(material_type='PA-CF')
        orchestrator = WorkflowOrchestrator(config)
        
        parameters = {
            'thickness': 2.0,
            'width': 50.0,
            'height': 30.0
        }
        
        design_vars = orchestrator._define_design_variables(parameters)
        
        assert 'thickness' in design_vars
        assert len(design_vars['thickness']) == 3  # (initial, lower, upper)
        assert design_vars['thickness'][0] == 2.0


class TestWorkflowIntegration:
    """Test end-to-end workflow integration."""
    
    def test_workflow_execution_placeholder(self):
        """Test workflow execution with placeholder implementations."""
        config = OptimizationConfig(material_type='PA-CF')
        orchestrator = WorkflowOrchestrator(config, fem_solver='fenics')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy input file
            input_file = Path(tmpdir) / 'test_part.step'
            input_file.write_text('ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;')
            
            output_dir = Path(tmpdir) / 'output'
            
            # Run workflow with minimal iterations
            results = orchestrator.run_workflow(
                input_file=input_file,
                output_dir=output_dir,
                max_iterations=2,
                convergence_tolerance=0.01
            )
            
            # Verify results structure
            assert 'workflow' in results
            assert 'initial_parameters' in results
            assert 'optimal_parameters' in results
            assert 'initial_metrics' in results
            assert 'final_metrics' in results
            assert 'improvements' in results
            assert 'output_files' in results
            assert 'tools' in results
            
            # Verify tools used
            assert results['tools']['cad'] == 'FreeCAD'
            assert results['tools']['meshing'] == 'Gmsh'
            assert results['tools']['fem_solver'] == 'FENICS'
            assert results['tools']['optimization'] == 'OpenMDAO'
            
            # Verify output files created
            assert output_dir.exists()
            assert (output_dir / 'workflow_report.json').exists()
