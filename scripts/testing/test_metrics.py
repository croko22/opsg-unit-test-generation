#!/usr/bin/env python3
"""
Script de prueba para verificar que JaCoCo y PIT funcionan correctamente.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.pipeline.phase4_evaluation import MetricsEvaluator
import tempfile


def test_jacoco_pit():
    """
    Test básico de JaCoCo y PIT con un test de ejemplo.
    """
    print("="*80)
    print("TEST: JaCoCo y PIT")
    print("="*80)
    print()
    
    evaluator = MetricsEvaluator()
    
    # Verificar que los JARs existan
    print("🔍 Verificando JARs necesarios...")
    jars = {
        "JaCoCo Agent": evaluator.jacoco_agent,
        "JaCoCo CLI": evaluator.jacoco_cli,
        "PIT": evaluator.pitest_jar,
        "JUnit": evaluator.junit_jar
    }
    
    missing = []
    for name, jar_path in jars.items():
        if jar_path.exists():
            print(f"   ✅ {name}: {jar_path.name}")
        else:
            print(f"   ❌ {name}: NO ENCONTRADO")
            missing.append(name)
    
    if missing:
        print(f"\n❌ Faltan JARs: {', '.join(missing)}")
        return False
    
    print("\n✅ Todos los JARs están disponibles")
    print()
    
    # Buscar un test de ejemplo en generated_tests/baseline
    baseline_dir = evaluator.base_dir / "generated_tests/baseline"
    if not baseline_dir.exists():
        print("⚠️  No hay tests en generated_tests/baseline/ todavía")
        print("   Ejecuta primero: python scripts/pipeline/phase1_generate_baseline.py")
        return False
    
    # Buscar primer test .java
    test_files = list(baseline_dir.rglob("*_ESTest.java"))
    if not test_files:
        print("⚠️  No se encontraron archivos *_ESTest.java")
        return False
    
    test_file = test_files[0]
    print(f"📄 Test de ejemplo: {test_file.name}")
    
    # Extraer info del path: generated_tests/baseline/PROJECT/CLASS/FILE.java
    parts = test_file.relative_to(baseline_dir).parts
    if len(parts) >= 2:
        project = parts[0]
        class_name = test_file.stem  # Quitar .java
        
        print(f"   Proyecto: {project}")
        print(f"   Clase: {class_name}")
        print()
        
        # Buscar SUT JAR
        sut_jar = evaluator.find_sut_jar(project)
        if not sut_jar:
            print(f"❌ No se encontró JAR para proyecto {project}")
            return False
        
        print(f"📦 SUT JAR: {sut_jar.name}")
        print()
        
        # Compilar test
        with tempfile.TemporaryDirectory() as tmpdir:
            compiled_dir = Path(tmpdir)
            
            print("🔨 Compilando test...")
            if not evaluator.compile_test(test_file, sut_jar, compiled_dir):
                print("❌ Error compilando test")
                return False
            
            print("✅ Test compilado")
            print()
            
            # Buscar .class
            test_class_file = compiled_dir / f"{class_name.replace('.', '/')}.class"
            if not test_class_file.exists():
                # Intentar buscar recursivamente
                class_files = list(compiled_dir.rglob(f"{class_name}.class"))
                if class_files:
                    test_class_file = class_files[0]
                else:
                    print(f"❌ No se encontró {class_name}.class")
                    return False
            
            print(f"📊 Probando JaCoCo...")
            cov = evaluator.measure_coverage_jacoco(
                test_class_file,
                sut_jar,
                class_name
            )
            
            if 'error' in cov:
                print(f"   ⚠️  Error: {cov['error']}")
            else:
                print(f"   ✅ Cobertura de línea: {cov['line_coverage']:.2f}%")
                print(f"   ✅ Cobertura de rama: {cov['branch_coverage']:.2f}%")
            print()
            
            print(f"🧬 Probando PIT (esto puede tardar un minuto)...")
            mut = evaluator.measure_mutation_score_pit(
                test_class_file,
                sut_jar,
                class_name
            )
            
            if 'error' in mut:
                print(f"   ⚠️  Error: {mut['error']}")
            else:
                print(f"   ✅ Mutation Score: {mut['mutation_score']:.2f}%")
                print(f"   ✅ Mutantes matados: {mut['mutants_killed']}/{mut['total_mutants']}")
            print()
            
            print("="*80)
            print("✅ TEST COMPLETADO")
            print("="*80)
            return True
    
    return False


if __name__ == "__main__":
    success = test_jacoco_pit()
    sys.exit(0 if success else 1)
