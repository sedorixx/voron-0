#!/usr/bin/env python3
"""
Command-line interface for structural optimization agent.

Usage:
    python -m structural_optimization.cli optimize <input_file> [options]
    python -m structural_optimization.cli validate <input_file>
"""

import argparse
import logging
import sys
from pathlib import Path

from .agent import StructuralOptimizationAgent
from .config import OptimizationConfig, MATERIALS
from .workflow_orchestrator import WorkflowOrchestrator


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def cmd_optimize(args):
    """Run optimization command."""
    logger = logging.getLogger(__name__)
    
    # Load configuration
    if args.config:
        config = OptimizationConfig.from_json(Path(args.config))
        logger.info(f"Loaded configuration from {args.config}")
    else:
        # Use predefined material config
        if args.material in MATERIALS:
            config = MATERIALS[args.material]
            logger.info(f"Using predefined material: {args.material}")
        else:
            logger.error(f"Unknown material: {args.material}")
            logger.info(f"Available materials: {', '.join(MATERIALS.keys())}")
            return 1
    
    # Override config with command-line arguments
    if args.mesh_size:
        config.mesh_size = args.mesh_size
    
    # Create agent and run optimization
    agent = StructuralOptimizationAgent(config)
    
    input_file = Path(args.input_file)
    output_dir = Path(args.output_dir) if args.output_dir else input_file.parent / "optimized"
    
    try:
        report = agent.optimize(
            input_file=input_file,
            output_dir=output_dir,
            max_iterations=args.max_iterations
        )
        
        logger.info("\n" + "="*60)
        logger.info("OPTIMIZATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Initial deflection: {report['initial_metrics']['max_deflection_mm']:.4f} mm")
        logger.info(f"Final deflection:   {report['final_metrics']['max_deflection_mm']:.4f} mm")
        logger.info(f"Improvement:        {report['improvements']['deflection_reduction_percent']:.1f}%")
        logger.info(f"Iterations:         {report['optimization_summary']['iterations']}")
        logger.info(f"Output files:       {output_dir}")
        logger.info("="*60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Optimization failed: {e}", exc_info=True)
        return 1


def cmd_validate(args):
    """Validate CAD file can be imported."""
    logger = logging.getLogger(__name__)
    
    from .cad_handler import CADHandler
    
    try:
        handler = CADHandler()
        input_file = Path(args.input_file)
        
        logger.info(f"Validating {input_file}...")
        geometry = handler.import_cad(input_file)
        
        logger.info("✓ File successfully imported")
        logger.info(f"  Type: {geometry.get('type')}")
        logger.info(f"  Volume: {geometry.get('volume', 0):.1f} mm³")
        
        return 0
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return 1


def cmd_materials(args):
    """List available materials."""
    print("\nAvailable materials:")
    print("="*60)
    
    for name, config in MATERIALS.items():
        print(f"\n{name}:")
        print(f"  Young's Modulus: {config.youngs_modulus} MPa")
        print(f"  Yield Strength:  {config.yield_strength} MPa")
        print(f"  Density:         {config.density} g/cm³")
    
    print("\n" + "="*60)
    return 0


def cmd_workflow(args):
    """Run complete workflow: FreeCAD → Gmsh → FEniCS/CalculiX → OpenMDAO → FreeCAD."""
    logger = logging.getLogger(__name__)
    
    # Load configuration
    if args.config:
        config = OptimizationConfig.from_json(Path(args.config))
        logger.info(f"Loaded configuration from {args.config}")
    else:
        # Use predefined material config
        if args.material in MATERIALS:
            config = MATERIALS[args.material]
            logger.info(f"Using predefined material: {args.material}")
        else:
            logger.error(f"Unknown material: {args.material}")
            logger.info(f"Available materials: {', '.join(MATERIALS.keys())}")
            return 1
    
    # Override config with command-line arguments
    if args.mesh_size:
        config.mesh_size = args.mesh_size
    
    # Create workflow orchestrator
    orchestrator = WorkflowOrchestrator(
        config=config,
        fem_solver=args.fem_solver
    )
    
    input_file = Path(args.input_file)
    output_dir = Path(args.output_dir) if args.output_dir else input_file.parent / "workflow_output"
    
    try:
        logger.info("\n" + "="*60)
        logger.info("STARTING WORKFLOW")
        logger.info("="*60)
        logger.info(f"Pipeline: FreeCAD → Gmsh → {args.fem_solver.upper()} → OpenMDAO → FreeCAD")
        logger.info(f"Input:    {input_file}")
        logger.info(f"Output:   {output_dir}")
        logger.info("="*60 + "\n")
        
        results = orchestrator.run_workflow(
            input_file=input_file,
            output_dir=output_dir,
            max_iterations=args.max_iterations,
            convergence_tolerance=args.convergence_tolerance
        )
        
        logger.info("\n" + "="*60)
        logger.info("WORKFLOW SUMMARY")
        logger.info("="*60)
        logger.info(f"Tools used:")
        for tool_type, tool_name in results['tools'].items():
            logger.info(f"  - {tool_type.upper()}: {tool_name}")
        logger.info(f"\nResults:")
        logger.info(f"  Initial deflection:  {results['initial_metrics']['max_deflection_mm']:.4f} mm")
        logger.info(f"  Final deflection:    {results['final_metrics']['max_deflection_mm']:.4f} mm")
        logger.info(f"  Improvement:         {results['improvements']['deflection_reduction_percent']:.1f}%")
        logger.info(f"  Iterations:          {results['workflow']['iterations']}")
        logger.info(f"  Total time:          {results['workflow']['elapsed_time_seconds']:.1f} seconds")
        logger.info(f"\nOutput files:")
        for file_type, file_path in results['output_files'].items():
            logger.info(f"  - {file_type}: {file_path}")
        logger.info("="*60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Structural Optimization Agent for 3D Printed Parts"
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Optimize command
    optimize_parser = subparsers.add_parser('optimize', help='Run structural optimization')
    optimize_parser.add_argument('input_file', help='Input CAD file (STEP format)')
    optimize_parser.add_argument(
        '--output-dir', '-o',
        help='Output directory (default: <input_dir>/optimized)'
    )
    optimize_parser.add_argument(
        '--config', '-c',
        help='Configuration JSON file'
    )
    optimize_parser.add_argument(
        '--material', '-m',
        default='PA-CF',
        help='Material preset (default: PA-CF)'
    )
    optimize_parser.add_argument(
        '--max-iterations', '-n',
        type=int,
        default=5,
        help='Maximum optimization iterations (default: 5)'
    )
    optimize_parser.add_argument(
        '--mesh-size',
        type=float,
        help='FEM mesh size in mm'
    )
    optimize_parser.set_defaults(func=cmd_optimize)
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate CAD file')
    validate_parser.add_argument('input_file', help='Input CAD file')
    validate_parser.set_defaults(func=cmd_validate)
    
    # Materials command
    materials_parser = subparsers.add_parser('materials', help='List available materials')
    materials_parser.set_defaults(func=cmd_materials)
    
    # Workflow command
    workflow_parser = subparsers.add_parser(
        'workflow',
        help='Run complete optimization workflow (FreeCAD → Gmsh → FEM → OpenMDAO)'
    )
    workflow_parser.add_argument('input_file', help='Input parametric CAD file (.FCStd or .step)')
    workflow_parser.add_argument(
        '--output-dir', '-o',
        help='Output directory (default: <input_dir>/workflow_output)'
    )
    workflow_parser.add_argument(
        '--config', '-c',
        help='Configuration JSON file'
    )
    workflow_parser.add_argument(
        '--material', '-m',
        default='PA-CF',
        help='Material preset (default: PA-CF)'
    )
    workflow_parser.add_argument(
        '--fem-solver',
        choices=['fenics', 'calculix'],
        default='fenics',
        help='FEM solver to use (default: fenics)'
    )
    workflow_parser.add_argument(
        '--max-iterations', '-n',
        type=int,
        default=10,
        help='Maximum workflow iterations (default: 10)'
    )
    workflow_parser.add_argument(
        '--convergence-tolerance',
        type=float,
        default=0.01,
        help='Convergence tolerance (default: 0.01 = 1%%)'
    )
    workflow_parser.add_argument(
        '--mesh-size',
        type=float,
        help='FEM mesh size in mm'
    )
    workflow_parser.set_defaults(func=cmd_workflow)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Run command
    if hasattr(args, 'func'):
        return args.func(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
