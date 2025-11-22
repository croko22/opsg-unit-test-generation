#!/usr/bin/env python3
"""
Muestra un resumen visual del estado del proyecto.
"""

from pathlib import Path
import subprocess


def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║              METODOLOGÍA DE TESIS - Test Generation + LLM                ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)


def check_file_exists(path: Path) -> str:
    return "✅" if path.exists() else "❌"


def get_file_count(pattern: str) -> int:
    try:
        return len(list(Path(".").glob(pattern)))
    except:
        return 0


def main():
    print_banner()
    
    print("📊 ESTADO DEL PROYECTO\n")
    
    # Scripts principales
    print("🔧 Scripts Principales:")
    scripts = [
        ("quick_test.py", "Test rápido de 1 clase"),
        ("simple_generate.py", "Generación baseline simple"),
        ("run_pipeline.py", "Pipeline completo (maestro)"),
        ("preflight_check.py", "Verificación de requisitos")
    ]
    
    for script, desc in scripts:
        status = check_file_exists(Path(script))
        print(f"  {status} {script:25s} - {desc}")
    
    print()
    
    # Fases
    print("📋 Fases de Metodología:")
    phases = [
        ("phase1_generate_baseline.py", "Fase 1: Baseline (EvoSuite)"),
        ("phase2_llm_refinement.py", "Fase 2: LLM Refinement"),
        ("phase3_verification.py", "Fase 3: Verificación"),
        ("phase4_evaluation.py", "Fase 4: Evaluación (RQs)"),
        ("phase5_analysis.py", "Fase 5: Análisis + Gráficas")
    ]
    
    for script, desc in phases:
        status = check_file_exists(Path(script))
        print(f"  {status} {script:35s} - {desc}")
    
    print()
    
    # Documentación
    print("📚 Documentación:")
    docs = [
        ("START_HERE.md", "Guía rápida (LEE PRIMERO)"),
        ("IMPLEMENTATION_SUMMARY.md", "Resumen ejecutivo"),
        ("METHODOLOGY.md", "Metodología completa"),
        ("INDEX.md", "Índice de todos los archivos"),
        ("CHECKLIST.md", "Checklist ejecutivo")
    ]
    
    for doc, desc in docs:
        status = check_file_exists(Path(doc))
        print(f"  {status} {doc:30s} - {desc}")
    
    print()
    
    # Librerías
    print("📦 Librerías Java:")
    libs = [
        ("lib/evosuite-1.2.0.jar", "⚠️  CRÍTICO"),
        ("lib/junit-4.11.jar", "⚠️  CRÍTICO"),
        ("lib/jacocoagent.jar", "Para Fase 4"),
        ("lib/jacococli.jar", "Para Fase 4"),
        ("lib/pitest-command-line.jar", "Para Fase 4 (mutation)"),
    ]
    
    for lib, note in libs:
        status = check_file_exists(Path(lib))
        print(f"  {status} {Path(lib).name:30s} {note}")
    
    print()
    
    # Datos
    print("💾 Benchmarks:")
    data_dirs = [
        ("data/SF110-binary", "SF110 (110 proyectos)"),
        ("data/extended-dynamosa-repos-binary", "Extended DynaMOSA (21 proyectos)")
    ]
    
    for data_dir, desc in data_dirs:
        path = Path(data_dir)
        status = check_file_exists(path)
        
        if path.exists():
            projects = len([d for d in path.iterdir() if d.is_dir() and not d.name.startswith('.')])
            print(f"  {status} {desc:40s} ({projects} dirs)")
        else:
            print(f"  {status} {desc}")
    
    print()
    
    # Outputs
    print("📁 Directorios de Output:")
    output_dirs = [
        "baseline_tests",
        "refined_tests",
        "valid_tests",
        "evaluation_results",
        "figures"
    ]
    
    for output_dir in output_dirs:
        path = Path(output_dir)
        status = check_file_exists(path)
        
        if path.exists():
            files = len(list(path.rglob("*")))
            print(f"  {status} {output_dir:25s} ({files} archivos)")
        else:
            print(f"  {status} {output_dir:25s} (vacío)")
    
    print()
    
    # Java version
    print("🔍 Entorno:")
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True
        )
        version_line = result.stderr.split('\n')[0]
        
        if "1.8" in version_line:
            print(f"  ✅ Java: {version_line}")
        else:
            print(f"  ⚠️  Java: {version_line} (se necesita Java 8)")
    except:
        print("  ❌ Java: No encontrado")
    
    # Python version
    import sys
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"  ✅ Python: {python_version}")
    
    print()
    print("═" * 79)
    print()
    
    # TODOs
    print("⚠️  PENDIENTE DE IMPLEMENTAR:")
    print("  1. Fase 2: Conectar LLM real (phase2_llm_refinement.py)")
    print("  2. Fase 4: Implementar PIT mutation testing (phase4_evaluation.py)")
    print("  3. Fase 4: Implementar JaCoCo coverage (phase4_evaluation.py)")
    print("  4. Fase 4: Implementar JavaNCSS complexity (phase4_evaluation.py)")
    
    print()
    print("🚀 PRÓXIMO PASO:")
    print("  python preflight_check.py     # Verificar requisitos completos")
    print("  python quick_test.py          # Test rápido")
    print("  python run_pipeline.py --limit 10  # Pipeline con 10 clases")
    
    print()
    print("📖 DOCUMENTACIÓN:")
    print("  cat START_HERE.md             # Guía rápida")
    print("  cat CHECKLIST.md              # Lista de tareas")
    
    print()
    print("═" * 79)


if __name__ == "__main__":
    main()
