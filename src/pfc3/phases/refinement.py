import json
import shutil
from pathlib import Path
from typing import Dict, Optional
from ..core.config import cfg
from ..core.llm import get_adapter
from ..utils.code_utils import clean_java_code
from ..utils.code_utils import clean_java_code
from ..utils.static_analysis import ContextExtractor, find_sut_file

class LLMRefiner:
    def __init__(self, adapter_name: str, model: str = None, **kwargs):
        self.adapter = get_adapter(adapter_name, model, **kwargs)
        
    def refine_test(self, test_code: str, sut_path: Path = None, class_name: str = None) -> Dict:
        context = ""
        if sut_path:
            extractor = ContextExtractor()
            context = extractor.extract_context(sut_path, class_name)
            
        prompt = self._build_prompt(test_code, context)
        result = self.adapter.generate(prompt)
        
        if result['success']:
            result['refined_code'] = clean_java_code(result['code'])
            
        return result
        
    def _build_prompt(self, test_code: str, context: str = "") -> str:
        return f"""Refine this Java test to be concise and readable. Remove redundancy.

CONTEXT (System Under Test):
{context}

ORIGINAL TEST:
```java
{test_code}
```
OUTPUT ONLY JAVA CODE."""



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
                    
                # Find SUT path (heuristic: assume src/main/java + package structure)
                # This is tricky without project structure knowledge. 
                # But we can try to find it in the project dir.
                # For now, let's skip strict SUT finding or implement a helper.
                # Actually, we can use the class name to find it.
                sut_path = find_sut_file(item['class'], project)
                
                res = refiner.refine_test(code, sut_path, cls) # Pass sut_path and class_name here
                
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


