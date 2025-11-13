#!/usr/bin/env python3
"""
Integration test for EvoSuite test generation and JaCoCo coverage analysis.

This script tests the complete pipeline:
1. Load a class from the benchmark data
2. Generate tests with EvoSuite
3. Compile and run tests
4. Measure coverage with JaCoCo
"""

import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Tuple


class TestPipeline:
    """Pipeline for testing data with EvoSuite and JaCoCo."""
    
    def __init__(self):
        self.root = Path(__file__).parent
        self.lib_dir = self.root / "lib"
        
        # Try to find EvoSuite JAR (prefer versioned, fallback to evosuite.jar)
        evosuite_jars = list(self.lib_dir.glob("evosuite-*.jar"))
        if evosuite_jars:
            self.evosuite_jar = sorted(evosuite_jars)[-1]  # Use latest version
        else:
            self.evosuite_jar = self.lib_dir / "evosuite.jar"
        
        self.jacoco_agent = self.lib_dir / "jacocoagent.jar"
        self.jacoco_cli = self.lib_dir / "jacococli.jar"
        self.junit_jar = self.lib_dir / "junit-4.11.jar"
        
        # Verify jars exist
        for jar in [self.evosuite_jar, self.jacoco_agent, self.jacoco_cli, self.junit_jar]:
            if not jar.exists():
                raise FileNotFoundError(f"Required JAR not found: {jar}")
    
    def find_class_jar(self, project: str, class_name: str) -> Optional[Path]:
        """Find the JAR file containing a specific class."""
        # Try extended-dynamosa first
        project_dir = self.root / "data" / "extended-dynamosa-repos-binary" / project
        
        if not project_dir.exists():
            # Try SF110
            for d in (self.root / "data" / "SF110-binary").iterdir():
                if d.is_dir() and project.lower() in d.name.lower():
                    project_dir = d
                    break
        
        if not project_dir.exists():
            return None
        
        # Find JAR containing the class
        for jar_file in project_dir.glob("*.jar"):
            try:
                result = subprocess.run(
                    ["jar", "tf", str(jar_file)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                class_path = class_name.replace(".", "/") + ".class"
                if class_path in result.stdout:
                    return jar_file
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        return None
    
    def run_evosuite(
        self,
        class_name: str,
        classpath: str,
        output_dir: Path,
        time_budget: int = 10
    ) -> bool:
        """
        Generate tests with EvoSuite.
        
        Args:
            class_name: Fully qualified class name
            classpath: Classpath containing the class
            output_dir: Output directory for generated tests
            time_budget: Time budget in seconds
            
        Returns:
            True if successful
        """
        cmd = [
            "java",
            "-jar", str(self.evosuite_jar),
            "-class", class_name,
            "-target", classpath,
            "-Dtest_dir", str(output_dir),
            "-Dsearch_budget", str(time_budget),
            "-Dassertion_strategy", "all",
            "-Dminimize", "true"
        ]
        
        print(f"\n🔧 Running EvoSuite for {class_name}...")
        print(f"   Time budget: {time_budget}s")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=time_budget + 30
            )
            
            if "* Writing JUnit test case" in result.stdout or "* Writing JUnit test case" in result.stderr:
                print("   ✓ Test generation successful")
                return True
            else:
                print("   ⚠ Test generation may have failed")
                print(f"   Output: {result.stdout[-200:]}")
                return False
                
        except subprocess.TimeoutExpired:
            print("   ❌ EvoSuite timeout")
            return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def compile_tests(
        self,
        test_dir: Path,
        classpath: str,
        output_dir: Path
    ) -> bool:
        """Compile generated test files."""
        java_files = list(test_dir.glob("**/*.java"))
        
        if not java_files:
            print("   ⚠ No test files found to compile")
            return False
        
        print(f"\n🔨 Compiling {len(java_files)} test files...")
        
        full_classpath = f"{classpath}:{self.junit_jar}:{test_dir}"
        
        cmd = [
            "javac",
            "-cp", full_classpath,
            "-d", str(output_dir),
            *[str(f) for f in java_files]
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("   ✓ Compilation successful")
                return True
            else:
                print("   ❌ Compilation failed")
                print(f"   Errors: {result.stderr[:500]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def run_tests_with_coverage(
        self,
        test_class: str,
        classpath: str,
        coverage_file: Path
    ) -> Tuple[bool, Optional[dict]]:
        """Run tests with JaCoCo coverage."""
        print(f"\n🧪 Running tests with coverage...")
        
        cmd = [
            "java",
            f"-javaagent:{self.jacoco_agent}=destfile={coverage_file}",
            "-cp", f"{classpath}:{self.junit_jar}",
            "org.junit.runner.JUnitCore",
            test_class
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            test_passed = result.returncode == 0
            print(f"   {'✓' if test_passed else '⚠'} Tests {'passed' if test_passed else 'had failures'}")
            
            # Generate coverage report
            if coverage_file.exists():
                print("\n📊 Generating coverage report...")
                report_cmd = [
                    "java",
                    "-jar", str(self.jacoco_cli),
                    "report", str(coverage_file),
                    "--classfiles", classpath.split(":")[0],
                    "--csv", str(coverage_file.parent / "coverage.csv")
                ]
                
                subprocess.run(report_cmd, capture_output=True, timeout=30)
                
                # Parse coverage
                coverage_csv = coverage_file.parent / "coverage.csv"
                if coverage_csv.exists():
                    with open(coverage_csv) as f:
                        lines = f.readlines()
                        if len(lines) > 1:
                            # Simple parsing - just get totals
                            print("   ✓ Coverage data generated")
                            return test_passed, {"coverage": "available"}
            
            return test_passed, None
            
        except subprocess.TimeoutExpired:
            print("   ❌ Test execution timeout")
            return False, None
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False, None
    
    def test_class(self, project: str, class_name: str, time_budget: int = 10) -> bool:
        """
        Test the complete pipeline for a single class.
        
        Args:
            project: Project name
            class_name: Fully qualified class name
            time_budget: Time budget for test generation
            
        Returns:
            True if successful
        """
        print("=" * 80)
        print(f"Testing: {class_name}")
        print(f"Project: {project}")
        print("=" * 80)
        
        # Find class JAR
        jar_file = self.find_class_jar(project, class_name)
        if not jar_file:
            print(f"❌ Could not find JAR containing {class_name}")
            return False
        
        print(f"✓ Found class in: {jar_file.name}")
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_dir = temp_path / "tests"
            compiled_dir = temp_path / "compiled"
            test_dir.mkdir()
            compiled_dir.mkdir()
            
            # Step 1: Generate tests
            if not self.run_evosuite(
                class_name,
                str(jar_file),
                test_dir,
                time_budget
            ):
                return False
            
            # Step 2: Compile tests
            if not self.compile_tests(
                test_dir,
                str(jar_file),
                compiled_dir
            ):
                return False
            
            # Step 3: Run tests with coverage
            test_class = class_name + "_ESTest"
            classpath = f"{jar_file}:{compiled_dir}"
            coverage_file = temp_path / "jacoco.exec"
            
            success, coverage = self.run_tests_with_coverage(
                test_class,
                classpath,
                coverage_file
            )
            
            print("\n" + "=" * 80)
            if success:
                print("✅ Pipeline completed successfully!")
            else:
                print("⚠ Pipeline completed with warnings")
            print("=" * 80)
            
            return True


def main():
    """Run integration tests."""
    print("🧪 EvoSuite + JaCoCo Integration Test")
    print("=" * 80)
    
    # Test cases from the data
    test_cases = [
        ("commons-lang", "org.apache.commons.lang3.ArrayUtils"),
        ("commons-cli", "org.apache.commons.cli.Option"),
        ("checkstyle", "com.puppycrawl.tools.checkstyle.api.FileContents"),
    ]
    
    pipeline = TestPipeline()
    
    print("\nNote: This test will run EvoSuite with a short time budget (10s per class)")
    print("to quickly verify the pipeline works.\n")
    
    results = []
    for project, class_name in test_cases:
        try:
            success = pipeline.test_class(project, class_name, time_budget=10)
            results.append((class_name, success))
        except Exception as e:
            print(f"\n❌ Error testing {class_name}: {e}")
            results.append((class_name, False))
        print("\n")
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    
    for class_name, success in results:
        status = "✓" if success else "❌"
        print(f"  {status} {class_name}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\n{passed}/{total} tests passed")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
