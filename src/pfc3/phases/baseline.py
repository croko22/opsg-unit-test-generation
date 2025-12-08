import json
import time
from pathlib import Path
from typing import List, Dict
from ..core.config import cfg
from ..core.loader import loader
from ..core.runner import runner

class BaselineGenerator:
    """Phase 1: Generate baseline tests using EvoSuite."""
    
    def run(self, limit: int = None, time_budget: int = 60) -> Dict:
        """Execute Phase 1 pipeline."""
        
        csv_path = cfg.sf110_home / "classes.csv"
        if not csv_path.exists():
            csv_path = cfg.extended_dynamosa_home / "classes.csv"
            
        import csv
        with open(csv_path) as f:
            classes = list(csv.DictReader(f))
            
        if limit:
            classes = classes[:limit]
            
        results = []
        success_count = 0
        
        print(f"Phase 1: Processing {len(classes)} classes with budget {time_budget}s")
        
        for i, cls in enumerate(classes, 1):
            project_name = cls['project']
            class_name = cls['class']
            
            print(f"[{i}/{len(classes)}] {class_name}")
            
            # 1. Find Project & JAR
            project = loader.get_project(project_name)
            if not project or not project.jar_files:
                print(f"  ❌ Project/JAR not found: {project_name}")
                results.append({"project": project_name, "class": class_name, "success": False, "error": "no_jar"})
                continue
                
            target_jar = project.jar_files[0] # Primary JAR
            
            # 2. Run EvoSuite
            output_dir = cfg.base_dir / "generated_tests/baseline" / project_name / class_name.replace(".", "_")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            result = runner.run_evosuite(target_jar, class_name, output_dir, time_budget)
            
            # 3. Process Result
            if result['success']:
                # Count generated tests
                tests = list(output_dir.glob("**/*_ESTest.java"))
                if tests:
                    success_count += 1
                    print(f"  ✅ Generated {len(tests)} tests")
                    
                    # Parse coverage from stdout (simplified)
                    coverage = self._parse_coverage(result['stdout'])
                    
                    results.append({
                        "project": project_name,
                        "class": class_name,
                        "success": True,
                        "num_tests": len(tests),
                        "test_files": [str(t) for t in tests],
                        "output_dir": str(output_dir),
                        "time": result['time'],
                        "coverage": coverage
                    })
                else:
                    print("  ❌ EvoSuite ran but produced no tests")
                    results.append({"project": project_name, "class": class_name, "success": False, "error": "no_tests_generated"})
            else:
                print(f"  ❌ EvoSuite failed: {result.get('error')}")
                results.append({"project": project_name, "class": class_name, "success": False, "error": result.get('error')})
                
            # Incremental save
            self._save_results(results)
            
        return {
            "total": len(classes),
            "success": success_count,
            "results": results
        }
        
    def _parse_coverage(self, stdout: str) -> Dict[str, float]:
        """Extract coverage metrics from EvoSuite stdout."""
        coverage = {}
        for line in stdout.split('\n'):
            if "Coverage of criterion" in line and ":" in line:
                parts = line.split(":")
                if len(parts) >= 2:
                    crit = parts[0].split("criterion")[-1].strip()
                    try:
                        val = float(parts[1].strip().rstrip('%'))
                        coverage[crit] = val
                    except:
                        pass
        return coverage
        
    def _save_results(self, results: List[Dict]):
        output_file = cfg.base_dir / "generated_tests/baseline/T_base_results.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
