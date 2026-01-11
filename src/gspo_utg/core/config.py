import os
import yaml
from pathlib import Path

class Config:
    """Central configuration for PFC3 pipeline."""
    
    def __init__(self):
        self.base_dir = Path(os.getcwd())
        self.config_path = self.base_dir / "config.yml"
        self._load_config()
        
    def _load_config(self):
        """Load configuration from config.yml."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                self.data = yaml.safe_load(f)
        else:
            self.data = {}
            
    @property
    def sf110_home(self) -> Path:
        path = self.data.get("sf110_home", "data/SF110-binary")
        return self.base_dir / path

    @property
    def extended_dynamosa_home(self) -> Path:
        path = self.data.get("extended_dynamosa_home", "data/extended-dynamosa-repos-binary")
        return self.base_dir / path
        
    @property
    def evosuite_jar(self) -> Path:
        return self.base_dir / "lib/evosuite-1.2.0.jar"
        
    @property
    def junit_jar(self) -> Path:
        return self.base_dir / "lib/junit-4.11.jar"
        
    @property
    def hamcrest_jar(self) -> Path:
        return self.base_dir / "lib/hamcrest-core-1.3.jar"
        
    @property
    def jacoco_agent_jar(self) -> Path:
        return self.base_dir / "lib/jacocoagent.jar"
        
    @property
    def jacoco_cli_jar(self) -> Path:
        return self.base_dir / "lib/jacococli.jar"
        
    @property
    def pitest_jar(self) -> Path:
        return self.base_dir / "lib/pitest-command-line.jar"

# Global instance
cfg = Config()
