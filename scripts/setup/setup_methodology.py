#!/usr/bin/env python3
"""
Setup para la metodología completa.

Instala todas las dependencias Python necesarias y verifica herramientas.
"""

import subprocess
import sys
from pathlib import Path


def install_python_packages():
    """Instala paquetes Python necesarios."""
    
    print("📦 Instalando paquetes Python...")
    
    packages = [
        "numpy",
        "pandas",
        "matplotlib",
        "seaborn",
        "scipy",
        "tqdm"
    ]
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + packages,
            check=True
        )
        print("✅ Paquetes Python instalados")
    except Exception as e:
        print(f"❌ Error instalando paquetes: {e}")
        return False
    
    return True


def download_pit():
    """Descarga PIT mutation testing tool."""
    
    print("\n🧬 Descargando PIT (mutation testing)...")
    
    pit_jar = Path("lib/pitest-command-line.jar")
    
    if pit_jar.exists():
        print("✅ PIT ya existe")
        return True
    
    try:
        # URL de PIT
        url = "https://github.com/hcoles/pitest/releases/download/pitest-parent-1.15.0/pitest-command-line-1.15.0.jar"
        
        subprocess.run(
            ["wget", "-O", str(pit_jar), url],
            check=True
        )
        
        print("✅ PIT descargado")
        return True
    
    except Exception as e:
        print(f"❌ Error descargando PIT: {e}")
        print("   Descarga manual desde: https://pitest.org/")
        return False


def download_javancss():
    """Descarga JavaNCSS para métricas de complejidad."""
    
    print("\n📊 Descargando JavaNCSS (complexity metrics)...")
    
    javancss_jar = Path("lib/javancss.jar")
    
    if javancss_jar.exists():
        print("✅ JavaNCSS ya existe")
        return True
    
    try:
        # URL directa (puede cambiar)
        url = "https://github.com/jenkinsci/javancss-plugin/raw/master/javancss-33.54.jar"
        
        subprocess.run(
            ["wget", "-O", str(javancss_jar), url],
            check=True
        )
        
        print("✅ JavaNCSS descargado")
        return True
    
    except Exception as e:
        print(f"❌ Error descargando JavaNCSS: {e}")
        print("   Descarga manual desde: https://github.com/jenkinsci/javancss-plugin")
        return False


def verify_tools():
    """Verifica que todas las herramientas estén disponibles."""
    
    print("\n🔍 Verificando herramientas...")
    
    tools = {
        "Java 8": ["java", "-version"],
        "Python 3": ["python3", "--version"],
        "wget": ["wget", "--version"]
    }
    
    all_ok = True
    
    for name, cmd in tools.items():
        try:
            subprocess.run(
                cmd,
                capture_output=True,
                check=True
            )
            print(f"✅ {name}")
        except:
            print(f"❌ {name} no encontrado")
            all_ok = False
    
    return all_ok


def check_data():
    """Verifica que los datos estén presentes."""
    
    print("\n📂 Verificando datos...")
    
    data_paths = {
        "SF110": Path("data/SF110-binary"),
        "Extended DynaMOSA": Path("data/extended-dynamosa-repos-binary"),
        "EvoSuite 1.2.0": Path("lib/evosuite-1.2.0.jar"),
        "JaCoCo Agent": Path("lib/jacocoagent.jar"),
        "JaCoCo CLI": Path("lib/jacococli.jar"),
        "JUnit": Path("lib/junit-4.11.jar")
    }
    
    all_ok = True
    
    for name, path in data_paths.items():
        if path.exists():
            print(f"✅ {name}")
        else:
            print(f"❌ {name} no encontrado: {path}")
            all_ok = False
    
    return all_ok


def create_output_dirs():
    """Crea directorios de salida."""
    
    print("\n📁 Creando directorios de salida...")
    
    dirs = [
        "baseline_tests",
        "refined_tests",
        "valid_tests",
        "evaluation_results",
        "figures"
    ]
    
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
    
    print("✅ Directorios creados")


def main():
    print("="*80)
    print("SETUP: Metodología de Tesis")
    print("="*80)
    print()
    
    # Verificar herramientas básicas
    if not verify_tools():
        print("\n❌ Faltan herramientas básicas. Instala primero:")
        print("   - Java 8: sudo pacman -S jdk8-openjdk")
        print("   - wget: sudo pacman -S wget")
        return 1
    
    # Verificar datos
    if not check_data():
        print("\n⚠️  Faltan datos o librerías")
        print("   Asegúrate de tener los benchmarks y EvoSuite")
    
    # Instalar Python packages
    if not install_python_packages():
        return 1
    
    # Descargar herramientas opcionales
    print("\n⚠️  Herramientas opcionales:")
    download_pit()
    print("   (JavaNCSS omitido - opcional para métricas de complejidad)")
    
    # Crear directorios
    create_output_dirs()
    
    print("\n" + "="*80)
    print("SETUP COMPLETADO")
    print("="*80)
    print("\n✅ Listo para ejecutar la metodología")
    print("\nPróximo paso:")
    print("  python run_pipeline.py --limit 10  # Test rápido")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
