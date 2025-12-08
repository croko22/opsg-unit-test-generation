import javalang
from pathlib import Path
from pathlib import Path
from typing import List, Dict, Optional
from ..core.config import cfg

def find_sut_file(class_name: str, project_name: str) -> Optional[Path]:
    """Find the source file for the given class."""
    # Construct relative path from class name
    rel_path = class_name.replace(".", "/") + ".java"
    
    # Try common source roots
    roots = [
        cfg.sf110_home / project_name / "src" / "main" / "java",
        cfg.sf110_home / project_name / "src",
        cfg.sf110_home / project_name / "source",
    ]
    
    for root in roots:
        candidate = root / rel_path
        print(f"    🔎 Checking {candidate}...") 
        if candidate.exists():
            return candidate
            
    # If not found, try recursive search in project dir (limited depth)
    project_dir = cfg.sf110_home / project_name
    if project_dir.exists():
        print(f"    🔎 Recursive search in {project_dir} for {class_name.split('.')[-1]}.java...") 
        found = list(project_dir.rglob(f"{class_name.split('.')[-1]}.java"))
        if found:
            return found[0]
            
    print(f"    ⚠️  SUT source not found for {class_name}") 
    return None

class ContextExtractor:
    def extract_context(self, java_file: Path) -> str:
        """Extracts method signatures and fields from a Java file."""
        if not java_file.exists():
            return "Context not available (file not found)."
            
        try:
            with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            tree = javalang.parse.parse(content)
            
            context = []
            
            # Package
            if tree.package:
                context.append(f"package {tree.package.name};")
                
            # Imports (only java.util/io or relevant ones? let's keep all for now)
            # context.append("\nImports:")
            # for imp in tree.imports:
            #     context.append(f"import {imp.path};")
                
            # Classes
            for path, node in tree.filter(javalang.tree.ClassDeclaration):
                context.append(f"\nclass {node.name} {{")
                
                # Fields
                for field in node.fields:
                    type_name = field.type.name
                    for declarator in field.declarators:
                        context.append(f"    {type_name} {declarator.name};")
                        
                # Methods
                for method in node.methods:
                    # Skip private methods? Maybe keeps protected/public
                    if 'private' in method.modifiers:
                        continue
                        
                    return_type = method.return_type.name if method.return_type else "void"
                    params = []
                    for param in method.parameters:
                        params.append(f"{param.type.name} {param.name}")
                    
                    sig = f"    {return_type} {method.name}({', '.join(params)});"
                    context.append(sig)
                    
                context.append("}")
                
            return "\n".join(context)
            
        except Exception as e:
            return f"Error extracting context: {str(e)}"
