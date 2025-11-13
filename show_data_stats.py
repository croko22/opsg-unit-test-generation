#!/usr/bin/env python3
"""
Display detailed statistics about the benchmark data.
"""

import csv
from pathlib import Path
from collections import defaultdict, Counter
import subprocess


def analyze_extended_dynamosa():
    """Analyze extended-dynamosa-repos-binary data."""
    print("=" * 80)
    print("Extended DynaMOSA Repos - Detailed Statistics")
    print("=" * 80)
    
    data_dir = Path("data/extended-dynamosa-repos-binary")
    classes_csv = data_dir / "classes.csv"
    
    projects = defaultdict(list)
    with open(classes_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            projects[row['project']].append(row['class'])
    
    print(f"\n📊 Overview:")
    print(f"   Total projects: {len(projects)}")
    print(f"   Total classes:  {sum(len(classes) for classes in projects.values())}")
    
    print(f"\n📁 Projects and class counts:")
    for project, classes in sorted(projects.items(), key=lambda x: len(x[1]), reverse=True):
        project_dir = data_dir / project
        jar_count = len(list(project_dir.glob("*.jar"))) if project_dir.exists() else 0
        print(f"   {project:25s} - {len(classes):3d} classes, {jar_count} JARs")
    
    # Package analysis
    print(f"\n📦 Top-level packages:")
    packages = Counter()
    for classes in projects.values():
        for cls in classes:
            top_package = cls.split('.')[0] if '.' in cls else 'default'
            packages[top_package] += 1
    
    for package, count in packages.most_common(10):
        print(f"   {package:30s} - {count} classes")


def analyze_sf110():
    """Analyze SF110-binary data."""
    print("\n" + "=" * 80)
    print("SF110 Benchmark - Detailed Statistics")
    print("=" * 80)
    
    data_dir = Path("data/SF110-binary")
    classes_csv = data_dir / "classes.csv"
    
    projects = defaultdict(list)
    with open(classes_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            projects[row['project']].append(row['class'])
    
    print(f"\n📊 Overview:")
    print(f"   Total projects: {len(projects)}")
    print(f"   Total classes:  {sum(len(classes) for classes in projects.values())}")
    
    # Directory count
    project_dirs = [d for d in data_dir.iterdir() if d.is_dir() and d.name[0].isdigit()]
    print(f"   Project dirs:   {len(project_dirs)}")
    
    print(f"\n📁 Sample projects (first 20):")
    for project, classes in sorted(projects.items())[:20]:
        print(f"   {project:40s} - {len(classes):3d} classes")
    
    print(f"\n   ... and {len(projects) - 20} more projects")
    
    # Class distribution
    class_counts = [len(classes) for classes in projects.values()]
    print(f"\n📊 Class distribution:")
    print(f"   Min classes per project:  {min(class_counts)}")
    print(f"   Max classes per project:  {max(class_counts)}")
    print(f"   Avg classes per project:  {sum(class_counts) / len(class_counts):.1f}")


def analyze_jar_sizes():
    """Analyze JAR file sizes."""
    print("\n" + "=" * 80)
    print("JAR File Size Analysis")
    print("=" * 80)
    
    all_jars = []
    
    for data_dir in ["data/extended-dynamosa-repos-binary", "data/SF110-binary"]:
        base_path = Path(data_dir)
        if base_path.exists():
            for jar_file in base_path.glob("**/*.jar"):
                size_mb = jar_file.stat().st_size / (1024 * 1024)
                all_jars.append((jar_file.relative_to(base_path), size_mb))
    
    print(f"\n📊 Overview:")
    print(f"   Total JAR files: {len(all_jars)}")
    
    if all_jars:
        sizes = [size for _, size in all_jars]
        total_size = sum(sizes)
        print(f"   Total size:      {total_size:.2f} MB")
        print(f"   Average size:    {total_size / len(all_jars):.2f} MB")
        print(f"   Smallest:        {min(sizes):.2f} MB")
        print(f"   Largest:         {max(sizes):.2f} MB")
        
        print(f"\n📦 Largest JARs:")
        for path, size in sorted(all_jars, key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {str(path):60s} - {size:6.2f} MB")


def sample_classes():
    """Show sample classes that can be tested."""
    print("\n" + "=" * 80)
    print("Sample Classes for Testing")
    print("=" * 80)
    
    data_dir = Path("data/extended-dynamosa-repos-binary")
    classes_csv = data_dir / "classes.csv"
    
    projects = defaultdict(list)
    with open(classes_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            projects[row['project']].append(row['class'])
    
    print("\nThese classes are good candidates for testing with EvoSuite:\n")
    
    # Show a few from different projects
    sample_projects = ['commons-lang', 'commons-cli', 'checkstyle', 'guava']
    
    for project in sample_projects:
        if project in projects:
            print(f"  {project}:")
            for cls in projects[project][:3]:
                print(f"    - {cls}")
            print()


def main():
    """Display all statistics."""
    print("\n📈 Benchmark Data Statistics\n")
    
    analyze_extended_dynamosa()
    analyze_sf110()
    analyze_jar_sizes()
    sample_classes()
    
    print("\n" + "=" * 80)
    print("💡 Next Steps:")
    print("=" * 80)
    print("""
  1. Run basic validation:
     python test_data.py
  
  2. Test EvoSuite pipeline (requires Java):
     python test_evosuite_pipeline.py
  
  3. Test with your existing code:
     python examples.py
  
  4. Start an experiment:
     python experiments/run_experiment.py
""")


if __name__ == "__main__":
    main()
