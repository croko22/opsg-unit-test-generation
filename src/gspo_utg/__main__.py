#!/usr/bin/env python3
"""
CLI entry point for GSPO-UTG (Unit Test Generation and Refinement).

Usage:
    python -m gspo_utg pipeline --phase 1 --limit 10
    python -m gspo_utg evaluate --results-dir evaluation_results/
"""

import argparse
import sys
from pathlib import Path

from gspo_utg.phases.baseline import BaselineGenerator
from gspo_utg.phases.refinement import RefinementPhase
from gspo_utg.phases.verification import VerificationPhase
from gspo_utg.phases.evaluation import EvaluationPhase
from gspo_utg.phases.analysis import AnalysisPhase
from gspo_utg.utils.logger import logger


def run_pipeline(args):
    """Execute the complete test generation pipeline."""
    
    def should_run(phase_num):
        if args.phase:
            return args.phase == phase_num
        if args.start_phase:
            return args.start_phase <= phase_num
        return True

    # Phase 1: Baseline Generation
    if should_run(1):
        logger.info("\n=== PHASE 1: BASELINE GENERATION ===")
        gen = BaselineGenerator()
        gen.run(limit=args.limit)
        
    # Phase 2: Test Refinement
    if should_run(2):
        logger.info("\n=== PHASE 2: TEST REFINEMENT ===")
        refiner = RefinementPhase()
        refiner.run(limit=args.limit)
        
    # Phase 3: Test Verification
    if should_run(3):
        logger.info("\n=== PHASE 3: TEST VERIFICATION ===")
        verifier = VerificationPhase()
        verifier.run(limit=args.limit)
        
    # Phase 4: Test Evaluation
    if should_run(4):
        logger.info("\n=== PHASE 4: TEST EVALUATION ===")
        evaluator = EvaluationPhase()
        evaluator.run(limit=args.limit)
        
    # Phase 5: Results Analysis
    if should_run(5):
        logger.info("\n=== PHASE 5: RESULTS ANALYSIS ===")
        analyzer = AnalysisPhase()
        analyzer.run()
        
    logger.info("\n=== PIPELINE COMPLETED ===")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='gspo_utg',
        description='GSPO-based Unit Test Generation and Refinement',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline with limit
  python -m gspo_utg pipeline --full --limit 10
  
  # Run specific phase
  python -m gspo_utg pipeline --phase 2 --limit 5
  
  # Run from specific phase onwards
  python -m gspo_utg pipeline --start-phase 3
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Pipeline command
    pipeline_parser = subparsers.add_parser('pipeline', help='Run the test generation pipeline')
    pipeline_parser.add_argument(
        '--limit', 
        type=int, 
        help='Limit number of classes to process'
    )
    pipeline_parser.add_argument(
        '--phase', 
        type=int, 
        choices=[1, 2, 3, 4, 5], 
        help='Run specific phase only'
    )
    pipeline_parser.add_argument(
        '--start-phase', 
        type=int, 
        choices=[1, 2, 3, 4, 5], 
        help='Start from specific phase and run all subsequent phases'
    )
    pipeline_parser.add_argument(
        '--full', 
        action='store_true', 
        help='Run full pipeline (all phases)'
    )
    
    # Version command
    parser.add_argument('--version', action='version', version='%(prog)s 0.1.0')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'pipeline':
        run_pipeline(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
