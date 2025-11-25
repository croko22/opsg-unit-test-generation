#!/usr/bin/env python3
"""
Quick test of a single class with EvoSuite.

Usage:
    python quick_test.py <project> <class_name> [time_budget]

Examples:
    python quick_test.py commons-lang org.apache.commons.lang3.ArrayUtils
    python quick_test.py commons-cli org.apache.commons.cli.Option 30
    python quick_test.py guava com.google.common.math.BigIntegerMath 60
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional


def find_class_jar(project: str, class_name: str) -> Optional[Path]:
    """Find JAR containing a class."""
    base_dir = Path("data/extended-dynamosa-repos-binary") / project
    
    if not base_dir.exists():
        return None
    
    for jar_file in base_dir.glob("*.jar"):
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


def run_evosuite(class_name: str, jar_file: Path, time_budget: int = 30):
    """Run EvoSuite test generation."""
    # Find EvoSuite JAR (prefer versioned)
    lib_dir = Path("lib")
    evosuite_jars = list(lib_dir.glob("evosuite-*.jar"))
    if evosuite_jars:
        evosuite_jar = sorted(evosuite_jars)[-1]  # Use latest version
    else:
        evosuite_jar = lib_dir / "evosuite.jar"
    
    output_dir = Path("generated_tests/evosuite")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🔧 Generating tests for: {class_name}")
    print(f"   Using: {evosuite_jar.name}")
    print(f"   Time budget: {time_budget}s")
    print(f"   Output dir: {output_dir}")
    print()
    
    cmd = [
        "java",
        "-jar", str(evosuite_jar),
        "-class", class_name,
        "-target", str(jar_file),
        "-Dtest_dir", str(output_dir),
        "-Dsearch_budget", str(time_budget),
        "-Dassertion_strategy", "all",
        "-Dminimize", "true",
        "-Dshow_progress", "false"
    ]
    
    try:
        result = subprocess.run(cmd, timeout=time_budget + 120)  # Add 2 minutes for post-processing
        
        # Check for generated files
        test_files = list(output_dir.glob(f"**/*{class_name.split('.')[-1]}*Test*.java"))
        
        if test_files:
            print("\n✅ Test generation completed!")
            print(f"\n📄 Generated files:")
            for test_file in test_files:
                size = test_file.stat().st_size
                print(f"   {test_file.name} ({size} bytes)")
            
            print(f"\n💡 Files saved to: {output_dir}/")
            print(f"\n📖 To view the test:")
            if test_files:
                print(f"   cat {test_files[0]}")
        else:
            print("\n⚠️  Test generation completed but no test files found")
            print(f"   Check {output_dir}/ for output")
        
        return 0
        
    except subprocess.TimeoutExpired:
        print("\n❌ Timeout! EvoSuite took too long")
        print("   Try reducing the time budget or choose a simpler class")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    
    project = sys.argv[1]
    class_name = sys.argv[2]
    time_budget = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    
    print("=" * 80)
    print("Quick EvoSuite Test")
    print("=" * 80)
    print()
    
    # Find JAR
    print(f"🔍 Looking for {class_name} in {project}...")
    jar_file = find_class_jar(project, class_name)
    
    if not jar_file:
        print(f"\n❌ Could not find {class_name} in {project}")
        print("\n💡 Available projects:")
        data_dir = Path("data/extended-dynamosa-repos-binary")
        for p in sorted(data_dir.iterdir()):
            if p.is_dir():
                print(f"   - {p.name}")
        return 1
    
    print(f"✓ Found in: {jar_file.name}")
    print()
    
    # Run EvoSuite
    return run_evosuite(class_name, jar_file, time_budget)


if __name__ == "__main__":
    sys.exit(main())
