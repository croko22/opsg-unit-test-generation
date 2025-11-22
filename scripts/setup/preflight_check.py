#!/usr/bin/env python3
"""
Pre-flight Check - Verifica que todo esté listo antes de ejecutar el pipeline.

Uso:
    python preflight_check.py
"""

import subprocess
import sys
from pathlib import Path
import json


class PreflightChecker:
    """Verifica todos los requisitos antes de ejecutar."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.checks_total = 0
    
    def check(self, name: str, test_func) -> bool:
        """Ejecuta un check y registra resultado."""
        self.checks_total += 1
        print(f"  [{self.checks_total}] {name}... ", end="", flush=True)
        
        try:
            result = test_func()
            if result:
                print("✅")
                self.checks_passed += 1
                return True
            else:
                print("❌")
                return False
        except Exception as e:
            print(f"❌ ({e})")
            return False
    
    def check_java_version(self) -> bool:
        """Verifica Java 8."""
        try:
            result = subprocess.run(
                ["java", "-version"],
                capture_output=True,
                text=True
            )
            version_info = result.stderr
            
            if "1.8" in version_info or "java version \"8" in version_info:
                return True
            else:
                self.errors.append("Java 8 requerido. Actual: " + version_info.split('\n')[0])
                return False
        except:
            self.errors.append("Java no encontrado")
            return False
    
    def check_javac(self) -> bool:
        """Verifica javac (compilador)."""
        try:
            subprocess.run(
                ["javac", "-version"],
                capture_output=True,
                check=True
            )
            return True
        except:
            self.errors.append("javac no encontrado (necesario para verificación)")
            return False
    
    def check_python_version(self) -> bool:
        """Verifica Python 3.8+."""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            return True
        else:
            self.errors.append(f"Python 3.8+ requerido. Actual: {version.major}.{version.minor}")
            return False
    
    def check_python_packages(self) -> bool:
        """Verifica paquetes Python."""
        required = ["numpy", "pandas", "matplotlib", "seaborn", "scipy"]
        missing = []
        
        for pkg in required:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
        
        if missing:
            self.errors.append(f"Paquetes Python faltantes: {', '.join(missing)}")
            self.errors.append("  Instala con: pip install " + " ".join(missing))
            return False
        
        return True
    
    def check_evosuite(self) -> bool:
        """Verifica EvoSuite 1.2.0."""
        evosuite = Path("lib/evosuite-1.2.0.jar")
        
        if not evosuite.exists():
            self.errors.append(f"EvoSuite no encontrado: {evosuite}")
            return False
        
        # Verificar que es ejecutable
        try:
            result = subprocess.run(
                ["java", "-jar", str(evosuite), "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "EvoSuite" in result.stdout or "EvoSuite" in result.stderr:
                return True
            else:
                self.warnings.append("EvoSuite JAR existe pero no responde correctamente")
                return True  # No fallar por esto
        except:
            self.warnings.append("No se pudo verificar versión de EvoSuite")
            return True  # El archivo existe, eso es lo importante
    
    def check_jacoco(self) -> bool:
        """Verifica JaCoCo."""
        agent = Path("lib/jacocoagent.jar")
        cli = Path("lib/jacococli.jar")
        
        if not agent.exists():
            self.warnings.append(f"JaCoCo agent no encontrado: {agent} (necesario para Fase 4)")
            return False
        
        if not cli.exists():
            self.warnings.append(f"JaCoCo CLI no encontrado: {cli} (necesario para Fase 4)")
            return False
        
        return True
    
    def check_pit(self) -> bool:
        """Verifica PIT."""
        pit = Path("lib/pitest-command-line.jar")
        
        if not pit.exists():
            self.warnings.append(f"PIT no encontrado: {pit} (necesario para mutation score en Fase 4)")
            self.warnings.append("  Ejecuta: python setup_methodology.py")
            return False
        
        return True
    
    def check_junit(self) -> bool:
        """Verifica JUnit."""
        junit = Path("lib/junit-4.11.jar")
        
        if not junit.exists():
            self.errors.append(f"JUnit no encontrado: {junit}")
            return False
        
        return True
    
    def check_data_sf110(self) -> bool:
        """Verifica benchmark SF110."""
        sf110_dir = Path("data/SF110-binary")
        
        if not sf110_dir.exists():
            self.errors.append(f"SF110 no encontrado: {sf110_dir}")
            return False
        
        # Contar proyectos
        projects = [d for d in sf110_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        if len(projects) < 100:
            self.warnings.append(f"SF110 parece incompleto: solo {len(projects)} proyectos")
        
        return True
    
    def check_data_extended(self) -> bool:
        """Verifica benchmark Extended DynaMOSA."""
        extended_dir = Path("data/extended-dynamosa-repos-binary")
        
        if not extended_dir.exists():
            self.errors.append(f"Extended DynaMOSA no encontrado: {extended_dir}")
            return False
        
        # Contar proyectos
        projects = [d for d in extended_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        if len(projects) < 20:
            self.warnings.append(f"Extended DynaMOSA parece incompleto: solo {len(projects)} proyectos")
        
        return True
    
    def check_scripts(self) -> bool:
        """Verifica que todos los scripts existan."""
        scripts = [
            "phase1_generate_baseline.py",
            "phase2_llm_refinement.py",
            "phase3_verification.py",
            "phase4_evaluation.py",
            "phase5_analysis.py",
            "run_pipeline.py"
        ]
        
        missing = []
        for script in scripts:
            if not Path(script).exists():
                missing.append(script)
        
        if missing:
            self.errors.append(f"Scripts faltantes: {', '.join(missing)}")
            return False
        
        return True
    
    def check_output_dirs(self) -> bool:
        """Verifica directorios de salida."""
        dirs = [
            "baseline_tests",
            "refined_tests",
            "valid_tests",
            "evaluation_results",
            "figures"
        ]
        
        for d in dirs:
            Path(d).mkdir(exist_ok=True)
        
        return True
    
    def check_disk_space(self) -> bool:
        """Verifica espacio en disco."""
        import shutil
        
        stat = shutil.disk_usage(".")
        free_gb = stat.free / (1024**3)
        
        if free_gb < 5:
            self.warnings.append(f"Poco espacio en disco: {free_gb:.1f} GB libres")
            return False
        
        return True


def main():
    print("="*80)
    print("PRE-FLIGHT CHECK - Verificación de Requisitos")
    print("="*80)
    print()
    
    checker = PreflightChecker()
    
    print("🔍 Verificando entorno...\n")
    
    # Java
    print("JAVA:")
    checker.check("Java 8", checker.check_java_version)
    checker.check("javac", checker.check_javac)
    print()
    
    # Python
    print("PYTHON:")
    checker.check("Python 3.8+", checker.check_python_version)
    checker.check("Paquetes Python", checker.check_python_packages)
    print()
    
    # Librerías
    print("LIBRERÍAS:")
    checker.check("EvoSuite 1.2.0", checker.check_evosuite)
    checker.check("JUnit", checker.check_junit)
    checker.check("JaCoCo", checker.check_jacoco)
    checker.check("PIT", checker.check_pit)
    print()
    
    # Datos
    print("BENCHMARKS:")
    checker.check("SF110", checker.check_data_sf110)
    checker.check("Extended DynaMOSA", checker.check_data_extended)
    print()
    
    # Scripts
    print("SCRIPTS:")
    checker.check("Fases 1-5 + Pipeline", checker.check_scripts)
    print()
    
    # Sistema
    print("SISTEMA:")
    checker.check("Directorios de salida", checker.check_output_dirs)
    checker.check("Espacio en disco", checker.check_disk_space)
    print()
    
    # Resumen
    print("="*80)
    print("RESUMEN")
    print("="*80)
    print(f"✅ Checks pasados: {checker.checks_passed}/{checker.checks_total}")
    
    if checker.errors:
        print(f"\n❌ ERRORES CRÍTICOS ({len(checker.errors)}):")
        for error in checker.errors:
            print(f"   • {error}")
    
    if checker.warnings:
        print(f"\n⚠️  ADVERTENCIAS ({len(checker.warnings)}):")
        for warning in checker.warnings:
            print(f"   • {warning}")
    
    print("\n" + "="*80)
    
    if checker.errors:
        print("❌ HAY ERRORES CRÍTICOS - Corrígelos antes de continuar")
        print("\nSugerencias:")
        print("  1. Instala Java 8: sudo pacman -S jdk8-openjdk")
        print("  2. Cambia a Java 8: sudo archlinux-java set java-8-openjdk")
        print("  3. Instala dependencias: pip install -r requirements.txt")
        print("  4. Ejecuta setup: python setup_methodology.py")
        print("="*80)
        return 1
    
    elif checker.warnings:
        print("⚠️  HAY ADVERTENCIAS - El pipeline puede ejecutarse pero algunas features no funcionarán")
        print("\nPuedes continuar con:")
        print("  python run_pipeline.py --limit 10")
        print("\nPara resolver advertencias:")
        print("  python setup_methodology.py")
        print("="*80)
        return 0
    
    else:
        print("✅ TODO LISTO - Puedes ejecutar el pipeline completo")
        print("\nPróximo paso:")
        print("  python run_pipeline.py --limit 10     # Test rápido")
        print("  python run_pipeline.py --full         # Ejecución completa")
        print("="*80)
        return 0


if __name__ == "__main__":
    sys.exit(main())
