#!/usr/bin/env python3
"""
PIPELINE COMPLETO: Metodología de Tesis (Modularized)
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path so we can import pfc3
# This assumes run_pipeline.py is in scripts/pipeline/
# and src is in ../../src
base_dir = Path(__file__).parent.parent.parent
sys.path.append(str(base_dir / "src"))

from pfc3.phases.baseline import BaselineGenerator
from pfc3.phases.refinement import RefinementPhase
from pfc3.phases.verification import VerificationPhase
from pfc3.phases.evaluation import EvaluationPhase
from pfc3.phases.evaluation import EvaluationPhase
# from pfc3.phases.analysis import AnalysisPhase


def main():
    parser = argparse.ArgumentParser(description="PFC3 Pipeline")
    parser.add_argument('--limit', type=int, help='Limit number of classes')
    parser.add_argument('--phase', type=int, choices=[1, 2, 3, 4, 5], help='Run specific phase')
    parser.add_argument('--start-phase', type=int, choices=[1, 2, 3, 4, 5], help='Start from specific phase')
    parser.add_argument('--full', action='store_true', help='Run full pipeline')
    
    args = parser.parse_args()
    
    def should_run(p):
        if args.phase:
            return args.phase == p
        if args.start_phase:
            return args.start_phase <= p
        return True

    # Phase 1: Baseline
    if should_run(1):
        print("\n=== PHASE 1: BASELINE ===")
        gen = BaselineGenerator()
        gen.run(limit=args.limit)
        
    # Phase 2: Refinement
    if should_run(2):
        print("\n=== PHASE 2: REFINEMENT ===")
        ref = RefinementPhase()
        ref.run()
        
    # Phase 3: Verification
    if should_run(3):
        print("\n=== PHASE 3: VERIFICATION ===")
        ver = VerificationPhase()
        ver.run()
        
    # Phase 4: Evaluation
    if should_run(4):
        print("\n=== PHASE 4: EVALUATION ===")
        eval = EvaluationPhase()
        eval.run()

    # Phase 5: Analysis
    if should_run(5):
        print("\n=== PHASE 5: ANALYSIS ===")
        from pfc3.phases.analysis import AnalysisPhase
        analysis = AnalysisPhase()
        analysis.run()


if __name__ == "__main__":
    main()
