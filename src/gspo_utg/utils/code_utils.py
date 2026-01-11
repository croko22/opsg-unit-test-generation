import re

def clean_java_code(code: str) -> str:
    """Extract Java code from LLM output."""
    # 1. Try to find markdown code blocks
    match = re.search(r'```java\s*(.*?)\s*```', code, re.DOTALL)
    if match:
        return match.group(1).strip()
        
    match = re.search(r'```\s*(.*?)\s*```', code, re.DOTALL)
    if match:
        return match.group(1).strip()
        
    # 2. Fallback: Heuristic extraction
    lines = code.split('\n')
    in_code = False
    
    # Find start (package or import)
    start_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("package ") or stripped.startswith("import ") or stripped.startswith("public class ") or stripped.startswith("@RunWith"):
            start_idx = i
            in_code = True
            break
            
    if not in_code:
        return code # Return original if no structure found
        
    content = lines[start_idx:]
    return '\n'.join(content)
