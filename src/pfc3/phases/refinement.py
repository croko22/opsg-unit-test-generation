import json
import shutil
from pathlib import Path
from typing import Dict, Optional
from ..core.config import cfg
from ..core.llm import get_adapter

class LLMRefiner:
    def __init__(self, adapter_name: str, model: str = None, **kwargs):
        self.adapter = get_adapter(adapter_name, model, **kwargs)
        
    def refine_test(self, test_code: str) -> Dict:
        prompt = self._build_prompt(test_code)
        result = self.adapter.generate(prompt)
        
        if result['success']:
            result['refined_code'] = self._clean_code(result['code'])
            
        return result
        
    def _build_prompt(self, test_code: str) -> str:
        return f"""Refine this Java test to be concise and readable. Remove redundancy.
ORIGINAL:
```java
{test_code}
```
OUTPUT ONLY JAVA CODE."""

    def _clean_code(self, code: str) -> str:
        """Extract Java code from LLM output."""
        # 1. Try to find markdown code blocks
        import re
        match = re.search(r'```java\s*(.*?)\s*```', code, re.DOTALL)
        if match:
            return match.group(1).strip()
            
        match = re.search(r'```\s*(.*?)\s*```', code, re.DOTALL)
        if match:
            return match.group(1).strip()
            
        # 2. Fallback: Heuristic extraction
        lines = code.split('\n')
        cleaned = []
        in_code = False
        
        # Find start (package or import)
        start_idx = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("package ") or stripped.startswith("import ") or stripped.startswith("public class "):
                start_idx = i
                in_code = True
                break
                
        if not in_code:
            return code # Return original if no structure found
            
        # Find end (last closing brace)
        # This is tricky without parsing, but we can assume the last '}' is the end
        # if we ignore trailing text.
        # For now, just take everything from start
        content = lines[start_idx:]
        
        # Remove trailing text that doesn't look like code
        # Simple heuristic: if a line after the last '}' contains text, remove it.
        # But finding the "last }" is hard if there are comments.
        
        return '\n'.join(content)

class RefinementPhase:
    def run(self, adapter: str = "openrouter", model: str = None) -> Dict:
        baseline_file = cfg.base_dir / "generated_tests/baseline/T_base_results.json"
        if not baseline_file.exists():
            print("❌ T_base not found")
            return {"success": False}
            
        with open(baseline_file) as f:
            baseline_results = json.load(f)
            
        successful = [r for r in baseline_results if r.get('success')]
        refiner = LLMRefiner(adapter, model)
        
        results = []
        
        for item in successful:
            project = item['project']
            cls = item['class']
            
            for test_file in item.get('test_files', []):
                path = Path(test_file)
                if not path.exists(): continue
                
                print(f"Refining {path.name}...")
                with open(path) as f:
                    code = f.read()
                    
                res = refiner.refine_test(code)
                
                if res['success']:
                    out_dir = cfg.base_dir / "generated_tests/refined" / project / cls.replace(".", "_")
                    out_dir.mkdir(parents=True, exist_ok=True)
                    out_path = out_dir / path.name
                    
                    with open(out_path, 'w') as f:
                        f.write(res['refined_code'])
                        
                    # Copy scaffolding
                    for scaff in path.parent.glob("*_scaffolding.java"):
                        shutil.copy2(scaff, out_dir)
                        
                    results.append({
                        "project": project,
                        "class": cls,
                        "original_file": str(path),
                        "refined_file": str(out_path),
                        "success": True
                    })
                else:
                    print(f"Failed: {res.get('error')}")
                    
        # Save results
        out_file = cfg.base_dir / "generated_tests/refined/T_refined_results.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        return {"success": True, "count": len(results)}
