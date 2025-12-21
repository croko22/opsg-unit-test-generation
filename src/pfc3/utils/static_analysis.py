import javalang
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from ..core.config import cfg

def find_sut_file(class_name: str, project_name: str) -> Optional[Path]:
    """Find the source file or JAR for the given class."""
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
        # print(f"    🔎 Checking {candidate}...") 
        if candidate.exists():
            return candidate
            
    # If not found, try recursive search in project dir (limited depth)
    project_dir = cfg.sf110_home / project_name
    if project_dir.exists():
        # print(f"    🔎 Recursive search in {project_dir} for {class_name.split('.')[-1]}.java...") 
        found = list(project_dir.rglob(f"{class_name.split('.')[-1]}.java"))
        if found:
            return found[0]
            
    # If source not found, try to find the project JAR
    # Convention: 1_tullibee -> tullibee.jar
    if '_' in project_name:
        jar_name = project_name.split('_', 1)[1] + ".jar"
        jar_path = project_dir / jar_name
        if jar_path.exists():
            print(f"    📦 Found JAR: {jar_path.name} (Source missing)")
            return jar_path

    print(f"    ⚠️  SUT source/JAR not found for {class_name}") 
    return None

class ContextExtractor:
    def extract_context(self, file_path: Path, class_name: str = None) -> str:
        """Extracts method signatures and fields from a Java file or JAR."""
        if not file_path.exists():
            return "Context not available (file not found)."
            
        if file_path.suffix == '.jar':
            if not class_name:
                return "Context not available (class name required for JAR extraction)."
            return self._extract_from_jar(file_path, class_name)
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            tree = javalang.parse.parse(content)
            
            context = []
            
            # Package
            if tree.package:
                context.append(f"package {tree.package.name};")
                
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

    def _extract_from_jar(self, jar_path: Path, class_name: str) -> str:
        """Extracts class signature using javap."""
        try:
            # -public shows public classes and members
            cmd = ["javap", "-cp", str(jar_path), "-public", class_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return f"Error running javap: {result.stderr}"
                
            return result.stdout
        except Exception as e:
            return f"Error extracting from JAR: {str(e)}"
