from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from .config import cfg

@dataclass
class ProjectInfo:
    name: str
    path: Path
    jar_files: List[Path]
    dataset: str

class ProjectLoader:
    """Handles discovery of projects and JARs."""
    
    def __init__(self):
        self.sf110_path = cfg.sf110_home
        self.dynamosa_path = cfg.extended_dynamosa_home
        
    def get_project(self, project_name: str) -> Optional[ProjectInfo]:
        """Find a project in either dataset."""
        # Check SF110
        p = self.sf110_path / project_name
        if p.exists():
            return self._create_project_info(project_name, p, "sf110")
            
        # Check DynaMOSA
        p = self.dynamosa_path / project_name
        if p.exists():
            return self._create_project_info(project_name, p, "dynamosa")
            
        return None
        
    def _create_project_info(self, name: str, path: Path, dataset: str) -> ProjectInfo:
        jars = list(path.glob("*.jar"))
        lib_dir = path / "lib"
        if lib_dir.exists():
            jars.extend(lib_dir.glob("*.jar"))
            
        return ProjectInfo(
            name=name,
            path=path,
            jar_files=jars,
            dataset=dataset
        )
        
    def get_classpath(self, project: ProjectInfo) -> str:
        """Generate classpath for a project."""
        jars = [str(j) for j in project.jar_files]
        return ":".join(jars)

loader = ProjectLoader()
