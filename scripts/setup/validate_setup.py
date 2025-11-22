#!/usr/bin/env python3
"""
Setup validation script for GSPO-UTG.

Checks that all dependencies and external tools are properly installed.
"""

import sys
import subprocess
from pathlib import Path
import importlib


class Colors:
    """ANSI color codes."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def check_python_version():
    """Check Python version."""
    print(f"\n{Colors.BLUE}Checking Python version...{Colors.RESET}")
    version = sys.version_info
    
    if version.major == 3 and version.minor >= 8:
        print(f"  {Colors.GREEN}✓{Colors.RESET} Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  {Colors.RED}✗{Colors.RESET} Python 3.8+ required (found {version.major}.{version.minor})")
        return False


def check_python_packages():
    """Check required Python packages."""
    print(f"\n{Colors.BLUE}Checking Python packages...{Colors.RESET}")
    
    required_packages = [
        ('torch', 'PyTorch'),
        ('transformers', 'Transformers'),
        ('peft', 'PEFT'),
        ('numpy', 'NumPy'),
        ('yaml', 'PyYAML'),
        ('javalang', 'javalang'),
    ]
    
    all_ok = True
    for module_name, display_name in required_packages:
        try:
            importlib.import_module(module_name)
            print(f"  {Colors.GREEN}✓{Colors.RESET} {display_name}")
        except ImportError:
            print(f"  {Colors.RED}✗{Colors.RESET} {display_name} (not installed)")
            all_ok = False
    
    return all_ok


def check_java():
    """Check Java installation."""
    print(f"\n{Colors.BLUE}Checking Java...{Colors.RESET}")
    
    try:
        result = subprocess.run(
            ['java', '-version'],
            capture_output=True,
            text=True
        )
        
        # Java outputs version to stderr
        version_line = result.stderr.split('\n')[0]
        print(f"  {Colors.GREEN}✓{Colors.RESET} {version_line}")
        return True
    except FileNotFoundError:
        print(f"  {Colors.RED}✗{Colors.RESET} Java not found in PATH")
        print(f"    Install Java 8+ from: https://www.oracle.com/java/technologies/downloads/")
        return False


def check_defects4j(config_path='config.yml'):
    """Check Defects4J installation."""
    print(f"\n{Colors.BLUE}Checking Defects4J...{Colors.RESET}")
    
    try:
        # Try to load config
        import yaml
        if Path(config_path).exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
            
            defects4j_home = Path(config['paths']['defects4j_home'])
            defects4j_cmd = defects4j_home / 'framework' / 'bin' / 'defects4j'
            
            if defects4j_cmd.exists():
                print(f"  {Colors.GREEN}✓{Colors.RESET} Defects4J found at {defects4j_home}")
                return True
            else:
                print(f"  {Colors.RED}✗{Colors.RESET} Defects4J not found at {defects4j_home}")
                print(f"    Clone from: https://github.com/rjust/defects4j.git")
                return False
        else:
            print(f"  {Colors.YELLOW}⚠{Colors.RESET} Config file not found (run will fail)")
            return False
    
    except Exception as e:
        print(f"  {Colors.YELLOW}⚠{Colors.RESET} Could not check Defects4J: {e}")
        return False


def check_evosuite(config_path='config.yml'):
    """Check EvoSuite JAR."""
    print(f"\n{Colors.BLUE}Checking EvoSuite...{Colors.RESET}")
    
    try:
        import yaml
        if Path(config_path).exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
            
            evosuite_jar = Path(config['paths']['evosuite_jar'])
            
            if evosuite_jar.exists():
                print(f"  {Colors.GREEN}✓{Colors.RESET} EvoSuite found at {evosuite_jar}")
                return True
            else:
                print(f"  {Colors.RED}✗{Colors.RESET} EvoSuite JAR not found at {evosuite_jar}")
                print(f"    Download from: https://github.com/EvoSuite/evosuite/releases")
                return False
        else:
            print(f"  {Colors.YELLOW}⚠{Colors.RESET} Config file not found")
            return False
    
    except Exception as e:
        print(f"  {Colors.YELLOW}⚠{Colors.RESET} Could not check EvoSuite: {e}")
        return False


def check_cuda():
    """Check CUDA availability."""
    print(f"\n{Colors.BLUE}Checking CUDA...{Colors.RESET}")
    
    try:
        import torch
        
        if torch.cuda.is_available():
            print(f"  {Colors.GREEN}✓{Colors.RESET} CUDA available")
            print(f"    GPU: {torch.cuda.get_device_name(0)}")
            print(f"    CUDA version: {torch.version.cuda}")
            return True
        else:
            print(f"  {Colors.YELLOW}⚠{Colors.RESET} CUDA not available (CPU mode will be used)")
            return False
    except ImportError:
        print(f"  {Colors.YELLOW}⚠{Colors.RESET} PyTorch not installed")
        return False


def check_directories():
    """Check project structure."""
    print(f"\n{Colors.BLUE}Checking project structure...{Colors.RESET}")
    
    required_dirs = [
        'src',
        'src/benchmark_handler',
        'src/evaluation',
        'src/gspo_optimizer',
        'src/llm_agent',
        'src/rl_env',
        'src/static_analyzer',
        'experiments',
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  {Colors.GREEN}✓{Colors.RESET} {dir_path}/")
        else:
            print(f"  {Colors.RED}✗{Colors.RESET} {dir_path}/ (missing)")
            all_ok = False
    
    return all_ok


def print_summary(results):
    """Print summary of checks."""
    print(f"\n{'=' * 80}")
    print(f"{Colors.BOLD}VALIDATION SUMMARY{Colors.RESET}")
    print(f"{'=' * 80}\n")
    
    total = len(results)
    passed = sum(results.values())
    
    for check, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {status} - {check}")
    
    print(f"\n{'=' * 80}")
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All checks passed! ({passed}/{total}){Colors.RESET}")
        print(f"\nYou're ready to run experiments!")
        print(f"\nNext steps:")
        print(f"  1. Review and update config.yml")
        print(f"  2. Run examples: python examples.py")
        print(f"  3. Start experiment: python experiments/run_experiment.py")
    elif passed >= total * 0.7:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ Some checks failed ({passed}/{total}){Colors.RESET}")
        print(f"\nMost components are ready, but some optional features may not work.")
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Setup incomplete ({passed}/{total}){Colors.RESET}")
        print(f"\nPlease install missing dependencies before running experiments.")
    
    print(f"{'=' * 80}\n")


def main():
    """Run all validation checks."""
    print(f"\n{'=' * 80}")
    print(f"{Colors.BOLD}GSPO-UTG Setup Validation{Colors.RESET}")
    print(f"{'=' * 80}")
    
    results = {
        'Python Version': check_python_version(),
        'Python Packages': check_python_packages(),
        'Java': check_java(),
        'Defects4J': check_defects4j(),
        'EvoSuite': check_evosuite(),
        'CUDA': check_cuda(),
        'Project Structure': check_directories(),
    }
    
    print_summary(results)
    
    # Return exit code
    return 0 if all(results.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
