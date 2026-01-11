import subprocess
import time
from pathlib import Path
from typing import List, Dict, Optional
from .config import cfg

class CommandRunner:
    """Standardized execution of Java commands."""
    
    def run_java(self, 
                 classpath: str, 
                 main_class: str, 
                 args: List[str] = None, 
                 timeout: int = 60) -> subprocess.CompletedProcess:
        """Run a Java class."""
        cmd = ["java", "-cp", classpath, main_class]
        if args:
            cmd.extend(args)
            
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
    def run_javac(self,
                  classpath: str,
                  source_files: List[Path],
                  output_dir: Path,
                  timeout: int = 60) -> subprocess.CompletedProcess:
        """Compile Java files."""
        cmd = [
            "javac",
            "-cp", classpath,
            "-d", str(output_dir)
        ] + [str(f) for f in source_files]
        
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
    def run_evosuite(self,
                     target_jar: Path,
                     class_name: str,
                     output_dir: Path,
                     time_budget: int = 60) -> Dict:
        """Run EvoSuite generation."""
        cmd = [
            "java", "-jar", str(cfg.evosuite_jar),
            "-class", class_name,
            "-target", str(target_jar),
            "-Dtest_dir", str(output_dir),
            "-Dsearch_budget", str(time_budget),
            "-Dminimize", "true",
            "-Dassertion_strategy", "all"
        ]
        
        start = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=time_budget + 120
            )
            elapsed = time.time() - start
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "time": elapsed
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "timeout", "time": time.time() - start}

    def run_with_jacoco(self,
                        classpath: str,
                        test_class: str,
                        exec_file: Path,
                        timeout: int = 60) -> subprocess.CompletedProcess:
        """Run JUnit tests with JaCoCo agent."""
        # includes=* ensures we capture everything, avoiding filtering issues
        agent_opts = f"-javaagent:{cfg.jacoco_agent_jar}=destfile={exec_file},append=false,includes=*"
        
        cmd = [
            "java",
            agent_opts,
            "-cp", classpath,
            "org.junit.runner.JUnitCore",
            test_class
        ]
        
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

    def generate_jacoco_report(self,
                             exec_file: Path,
                             class_files_dir: Path,
                             source_dir: Path,
                             report_dir: Path) -> subprocess.CompletedProcess:
        """Generate JaCoCo XML report."""
        cmd = [
            "java", "-jar", str(cfg.jacoco_cli_jar),
            "report", str(exec_file),
            "--classfiles", str(class_files_dir),
            "--sourcefiles", str(source_dir),
            "--xml", str(report_dir / "jacoco.xml")
        ]
        
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

    def run_pitest(self,
                   classpath: str,
                   target_classes: str,
                   test_classes: str,
                   source_dirs: str,
                   report_dir: Path,
                   timeout: int = 300) -> subprocess.CompletedProcess:
        """Run PIT mutation testing."""
        cmd = [
            "java", "-cp", f"{cfg.pitest_jar}:{classpath}",
            "org.pitest.mutationtest.commandline.MutationCoverageReport",
            "--reportDir", str(report_dir),
            "--targetClasses", target_classes,
            "--targetTests", test_classes,
            "--sourceDirs", source_dirs,
            "--outputFormats", "XML"
        ]
        
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

    def instrument_classes(self,
                           classes_dir: Path,
                           dest_dir: Path) -> subprocess.CompletedProcess:
        """Instrument classes for offline JaCoCo."""
        cmd = [
            "java", "-jar", str(cfg.jacoco_cli_jar),
            "instrument", str(classes_dir),
            "--dest", str(dest_dir)
        ]
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

    def run_with_jacoco_offline(self,
                                classpath: str,
                                test_class: str,
                                exec_file: Path,
                                timeout: int = 60) -> subprocess.CompletedProcess:
        """Run JUnit tests with Offline JaCoCo (agent in CP, sys prop set)."""
        # Note: Classpath must have instrumented classes FIRST.
        
        cmd = [
            "java",
            f"-Djacoco-agent.destfile={exec_file}",
            "-cp", classpath,
            "org.junit.runner.JUnitCore",
            test_class
        ]
        
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

    def run_cmd(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Run generic command."""
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

runner = CommandRunner()
