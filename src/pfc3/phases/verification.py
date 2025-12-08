import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Tuple, List
from ..core.config import cfg
from ..core.loader import loader
from ..core.runner import runner
from ..core.llm import get_adapter
from ..utils.code_utils import clean_java_code
from ..utils.static_analysis import ContextExtractor, find_sut_file

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
                
                # Attempt Repair
                print("  🔧 Attempting repair...")
                if self._repair_test(refined_path, res.stderr, cp, scaffolding):
                    print("  ✅ Repair successful (compiled)")
                    # Re-compile to ensure we have the .class files in out_dir for the next steps
                    res = runner.run_javac(cp, files_to_compile, out_dir)
                    if res.returncode != 0:
                         return False, "Compilation failed after repair"
                else:
                    return False, "Compilation failed (Repair failed)"
                
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

    def _repair_test(self, file_path: Path, error_log: str, classpath: str, scaffolding: List[Path], max_attempts: int = 3) -> bool:
        """Iteratively try to repair the test file using LLM."""
        adapter = get_adapter("openrouter") # Default or config
        
        # Try to find SUT context
        context = ""
        try:
            parts = file_path.parts
            refined_idx = parts.index("refined")
            project_name = parts[refined_idx + 1]
            
            # Infer class name from file content (package + class)
            # Or just search for the test class name minus _ESTest
            test_class_name = file_path.stem.replace("_ESTest", "")
            
            # We need full package.
            # Let's read the file to find package
            with open(file_path, 'r') as f:
                content = f.read()
                
            import re
            pkg_match = re.search(r'package\s+([\w\.]+);', content)
            if pkg_match:
                full_class_name = f"{pkg_match.group(1)}.{test_class_name}"
                sut_path = find_sut_file(full_class_name, project_name)
                
                if sut_path:
                    extractor = ContextExtractor()
                    context = extractor.extract_context(sut_path)
                    print(f"    ℹ️  Injected context from {sut_path.name}")
        except Exception as e:
            print(f"    ⚠️  Failed to extract context: {e}")

        with open(file_path, 'r') as f:
            code = f.read()
            
        for attempt in range(1, max_attempts + 1):
            print(f"    Attempt {attempt}/{max_attempts}...")
            
            prompt = f"""Fix the following Java compilation errors in the test file.

CONTEXT (System Under Test):
{context}

CODE:
```java
{code}
```

ERRORS:
{error_log}

INSTRUCTIONS:
1. Fix missing imports (e.g. @RunWith, @Test).
2. Fix missing symbols (e.g. class names, methods).
3. Do not remove the test logic, just fix the syntax/imports.
4. Output the FULL corrected Java file.

OUTPUT ONLY JAVA CODE."""

            result = adapter.generate(prompt)
            if not result['success']:
                print(f"    LLM Error: {result.get('error')}")
                continue
                
            repaired_code = clean_java_code(result['code'])
            
            # Save to file
            with open(file_path, 'w') as f:
                f.write(repaired_code)
                
            # Verify compilation
            with tempfile.TemporaryDirectory() as tmpdir:
                out_dir = Path(tmpdir)
                files_to_compile = [file_path] + scaffolding
                res = runner.run_javac(classpath, files_to_compile, out_dir)
                
                if res.returncode == 0:
                    return True
                else:
                    # Update error log for next iteration
                    error_log = res.stderr
                    # Update code for next iteration (optional, but maybe better to keep original context? 
                    # No, we should iterate on the new code if it's closer, but risky. 
                    # Let's keep using the *new* code as base for next fix)
                    code = repaired_code
            
        return False
