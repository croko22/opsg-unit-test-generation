import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Tuple
from ..core.config import cfg
from ..core.loader import loader
from ..core.runner import runner

class VerificationPhase:
    """Phase 3: Verify refined tests."""
    
    def run(self) -> Dict:
        refined_file = cfg.base_dir / "generated_tests/refined/T_refined_results.json"
        if not refined_file.exists():
            print("❌ T_refined not found")
            return {"success": False}
            
        with open(refined_file) as f:
            refined_results = json.load(f)
            
        to_verify = [r for r in refined_results if r.get('success')]
        valid_results = []
        
        print(f"Phase 3: Verifying {len(to_verify)} tests")
        
        for i, refined in enumerate(to_verify, 1):
            project_name = refined['project']
            class_name = refined['class']
            
            print(f"[{i}/{len(to_verify)}] {class_name}")
            
            project = loader.get_project(project_name)
            if not project or not project.jar_files:
                print("  ❌ SUT JAR not found")
                continue
                
            sut_jar = project.jar_files[0]
            refined_path = Path(refined['refined_file'])
            original_path = Path(refined['original_file'])
            
            # Verify
            is_valid, reason = self._verify_test(
                refined_path, original_path, sut_jar, class_name
            )
            
            if is_valid:
                print("  ✅ Valid")
                valid_results.append({
                    **refined,
                    "verified": True,
                    "oracle_preserved": True
                })
            else:
                print(f"  ❌ Invalid: {reason}")
                valid_results.append({
                    **refined,
                    "verified": False,
                    "error": reason
                })
                
        # Save results
        out_file = cfg.base_dir / "generated_tests/validated/T_valid_results.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, 'w') as f:
            json.dump(valid_results, f, indent=2)
            
        # Copy valid tests
        valid_dir = cfg.base_dir / "generated_tests/validated"
        for res in valid_results:
            if res.get('verified'):
                src = Path(res['refined_file'])
                dest = valid_dir / src.relative_to(cfg.base_dir / "generated_tests/refined")
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                
        return {"success": True, "count": len(valid_results)}
        
    def _verify_test(self, refined_path: Path, original_path: Path, sut_jar: Path, class_name: str) -> Tuple[bool, str]:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            
            # 1. Compile Refined
            cp = f"{sut_jar}:{cfg.junit_jar}:{cfg.evosuite_jar}:{refined_path.parent}"
            
            # Find scaffolding
            scaffolding = list(refined_path.parent.glob("*_scaffolding.java"))
            files_to_compile = [refined_path] + scaffolding
            
            res = runner.run_javac(cp, files_to_compile, out_dir)
            if res.returncode != 0:
                print(f"  ❌ Compilation Error:\n{res.stderr}")
                return False, "Compilation failed"
                
            # 2. Run Original (Baseline)
            # We need to compile original first
            # Original scaffolding should be in the same dir as original file or we need to find it
            orig_scaffolding = list(original_path.parent.glob("*_scaffolding.java"))
            runner.run_javac(cp, [original_path] + orig_scaffolding, out_dir)
            if res.returncode != 0:
                return False, "Original compilation failed"
                
            test_class = class_name + "_ESTest"
            cp_run = f"{cp}:{out_dir}"
            
            orig_res = runner.run_java(cp_run, "org.junit.runner.JUnitCore", [test_class])
            orig_passed = "OK (" in orig_res.stdout
            
            # 3. Run Refined
            # Recompile refined to overwrite original .class
            runner.run_javac(cp, files_to_compile, out_dir)
            ref_res = runner.run_java(cp_run, "org.junit.runner.JUnitCore", [test_class])
            ref_passed = "OK (" in ref_res.stdout
            
            # 4. Oracle Check
            if orig_passed and ref_passed:
                return True, "Preserved (Pass)"
            elif not orig_passed and not ref_passed:
                return True, "Preserved (Fail)"
            elif orig_passed and not ref_passed:
                return False, "Regression"
            else:
                return False, "Fix (Unexpected)"
