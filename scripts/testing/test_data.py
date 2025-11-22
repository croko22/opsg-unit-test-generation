#!/usr/bin/env python3
"""
Test script to validate benchmark data structure and accessibility.
"""

import sys
from pathlib import Path
import csv
from collections import defaultdict


def test_extended_dynamosa():
    """Test extended-dynamosa-repos-binary data."""
    print("=" * 80)
    print("Testing Extended DynaMOSA Repos Binary")
    print("=" * 80)
    
    data_dir = Path("data/extended-dynamosa-repos-binary")
    
    # Check classes.csv
    classes_csv = data_dir / "classes.csv"
    if not classes_csv.exists():
        print(f"❌ classes.csv not found at {classes_csv}")
        return False
    
    # Parse CSV and count projects
    projects = defaultdict(list)
    with open(classes_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            projects[row['project']].append(row['class'])
    
    print(f"\n✓ Found {len(projects)} projects")
    print(f"✓ Total classes: {sum(len(classes) for classes in projects.values())}")
    
    # Check each project directory
    missing_dirs = []
    for project in projects.keys():
        project_dir = data_dir / project
        if not project_dir.exists():
            missing_dirs.append(project)
    
    if missing_dirs:
        print(f"\n⚠ Missing directories: {missing_dirs}")
    else:
        print("\n✓ All project directories exist")
    
    # Sample some projects
    print("\nProject summary:")
    for project, classes in sorted(projects.items())[:5]:
        project_dir = data_dir / project
        if project_dir.exists():
            jar_files = list(project_dir.glob("*.jar"))
            class_files = list(project_dir.glob("**/*.class"))
            print(f"  {project}: {len(classes)} classes, {len(jar_files)} JARs, {len(class_files)} .class files")
    
    return True


def test_sf110():
    """Test SF110-binary data."""
    print("\n" + "=" * 80)
    print("Testing SF110 Binary")
    print("=" * 80)
    
    data_dir = Path("data/SF110-binary")
    
    # Check classes.csv
    classes_csv = data_dir / "classes.csv"
    if not classes_csv.exists():
        print(f"❌ classes.csv not found at {classes_csv}")
        return False
    
    # Parse CSV
    projects = defaultdict(list)
    with open(classes_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            projects[row['project']].append(row['class'])
    
    print(f"\n✓ Found {len(projects)} projects in classes.csv")
    
    # Count project directories
    project_dirs = [d for d in data_dir.iterdir() if d.is_dir() and d.name[0].isdigit()]
    print(f"✓ Found {len(project_dirs)} project directories")
    
    # Sample some projects
    print("\nSample projects:")
    for project_dir in sorted(project_dirs)[:5]:
        jar_files = list(project_dir.glob("*.jar"))
        class_files = list(project_dir.glob("**/*.class"))
        print(f"  {project_dir.name}: {len(jar_files)} JARs, {len(class_files)} .class files")
    
    return True


def test_lib_jars():
    """Test that required JAR files exist."""
    print("\n" + "=" * 80)
    print("Testing Library JARs")
    print("=" * 80)
    
    lib_dir = Path("lib")
    required_jars = [
        "evosuite.jar",
        "jacocoagent.jar",
        "jacococli.jar",
        "junit-4.11.jar",
        "junit-4.4.jar"
    ]
    
    all_present = True
    for jar in required_jars:
        jar_path = lib_dir / jar
        if jar_path.exists():
            size_mb = jar_path.stat().st_size / (1024 * 1024)
            print(f"  ✓ {jar} ({size_mb:.2f} MB)")
        else:
            print(f"  ❌ {jar} NOT FOUND")
            all_present = False
    
    return all_present


def test_java_compilation():
    """Test if we can access Java classes from the data."""
    print("\n" + "=" * 80)
    print("Testing Java Class Access")
    print("=" * 80)
    
    import subprocess
    
    # Try to list classes in a JAR
    data_dir = Path("data/extended-dynamosa-repos-binary/commons-lang")
    jar_files = list(data_dir.glob("*.jar"))
    
    if jar_files:
        jar_file = jar_files[0]
        print(f"\nTesting JAR: {jar_file.name}")
        
        try:
            result = subprocess.run(
                ["jar", "tf", str(jar_file)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                class_count = len([l for l in result.stdout.split('\n') if l.endswith('.class')])
                print(f"  ✓ Successfully listed {class_count} class files")
                return True
            else:
                print(f"  ❌ Failed to list JAR contents")
                return False
        except subprocess.TimeoutExpired:
            print(f"  ⚠ Timeout while listing JAR")
            return False
        except FileNotFoundError:
            print(f"  ⚠ 'jar' command not found (Java not in PATH?)")
            return False
    else:
        print(f"  ⚠ No JAR files found in {data_dir}")
        return False


def main():
    """Run all tests."""
    print("🧪 Data Validation Test Suite")
    print("=" * 80)
    
    results = {
        "Extended DynaMOSA": test_extended_dynamosa(),
        "SF110": test_sf110(),
        "Library JARs": test_lib_jars(),
        "Java Access": test_java_compilation()
    }
    
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    all_passed = all(results.values())
    print("\n" + ("🎉 All tests passed!" if all_passed else "⚠ Some tests failed"))
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
