#!/usr/bin/env python3
"""
PASO 1: Generación de Línea Base con EvoSuite

Genera T_base usando EvoSuite sobre SF110.
Este es tu CONTROL para los experimentos.

Output:
  - generated_tests/baseline/ con todos los tests
  - baseline_metrics.json con cobertura y mutación inicial
"""

import csv
import json
import subprocess
from pathlib import Path
from datetime import datetime
import time


def find_jar(project: str, dataset: str = "SF110-binary") -> Path:
    """Encuentra el JAR de un proyecto."""
    base = Path(f"data/{dataset}") / project
    jars = list(base.glob("*.jar"))
    return jars[0] if jars else None


def run_evosuite(project: str, class_name: str, jar: Path, time_budget: int = 60) -> dict:
    """Genera test con EvoSuite."""
    
    output = Path("generated_tests/baseline") / project / class_name.replace(".", "_")
    output.mkdir(parents=True, exist_ok=True)
    
    evosuite = list(Path("lib").glob("evosuite-*.jar"))[-1]
    
    cmd = [
        "java", "-jar", str(evosuite),
        "-class", class_name,
        "-target", str(jar),
        "-Dtest_dir", str(output),
        "-Dsearch_budget", str(time_budget),
        "-Dminimize", "true",
        "-Dassertion_strategy", "all"
    ]
    
    try:
        start = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=time_budget + 120
        )
        elapsed = time.time() - start
        
        # Buscar tests generados
        tests = list(output.glob("**/*_ESTest.java"))
        
        if not tests:
            return {"success": False, "error": "no_tests"}
        
        # Parsear cobertura del output de EvoSuite
        coverage = {}
        for line in result.stdout.split('\n'):
            if "Coverage of criterion" in line and ":" in line:
                parts = line.split(":")
                if len(parts) >= 2:
                    criterion = parts[0].split("criterion")[-1].strip()
                    cov_str = parts[1].strip().rstrip('%')
                    try:
                        coverage[criterion] = float(cov_str)
                    except:
                        pass
        
        return {
            "success": True,
            "num_tests": len(tests),
            "test_files": [str(f) for f in tests],
            "output_dir": str(output),
            "time_seconds": elapsed,
            "coverage": coverage
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def measure_mutation_score(project: str, class_name: str, jar: Path) -> dict:
    """
    Mide mutation score con PIT.
    NOTA: Necesitas tener PIT configurado.
    """
    # TODO: Implementar cuando tengas PIT
    # Por ahora retorna placeholder
    return {"mutation_score": None, "mutants_killed": 0, "total_mutants": 0}


def main():
    """
    FASE 1: Genera T_base para SF110
    """
    
    print("="*80)
    print("FASE 1: GENERACIÓN DE LÍNEA BASE (T_base)")
    print("="*80)
    print("\nGenerando tests con EvoSuite sobre SF110...")
    print("Esto será tu CONTROL para comparar con LLM refinement.\n")
    
    # Cargar clases de SF110
    csv_path = Path("data/SF110-binary/classes.csv")
    if not csv_path.exists():
        print("❌ No se encuentra SF110/classes.csv")
        print("Intentando con Extended DynaMOSA...")
        csv_path = Path("data/extended-dynamosa-repos-binary/classes.csv")
    
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        classes = list(reader)
    
    # CONFIGURACIÓN
    LIMIT = 10  # Para prueba, None para todos
    TIME_BUDGET = 60  # segundos por clase
    
    if LIMIT:
        classes = classes[:LIMIT]
        print(f"⚠️  MODO PRUEBA: Solo {LIMIT} clases")
    
    print(f"📊 Total a procesar: {len(classes)} clases")
    print(f"⏱️  Budget: {TIME_BUDGET}s por clase\n")
    
    # Generar T_base
    results = []
    success_count = 0
    
    for i, cls in enumerate(classes, 1):
        project = cls['project']
        class_name = cls['class']
        
        print(f"\n[{i}/{len(classes)}] {class_name}")
        print("-" * 60)
        
        # Buscar JAR
        jar = find_jar(project)
        if not jar:
            print("❌ No JAR")
            results.append({
                "project": project,
                "class": class_name,
                "success": False,
                "error": "no_jar"
            })
            continue
        
        # Generar test con EvoSuite
        result = run_evosuite(project, class_name, jar, TIME_BUDGET)
        result['project'] = project
        result['class'] = class_name
        
        if result['success']:
            success_count += 1
            print(f"✅ {result['num_tests']} tests generados")
            print(f"⏱️  {result['time_seconds']:.1f}s")
            
            # Mostrar cobertura
            if result.get('coverage'):
                for crit, cov in result['coverage'].items():
                    print(f"   {crit}: {cov:.1f}%")
            
            # TODO: Medir mutation score (cuando tengas PIT)
            # mutation = measure_mutation_score(project, class_name, jar)
            # result['mutation'] = mutation
        else:
            print(f"❌ {result.get('error', 'unknown')}")
        
        results.append(result)
        
        # Guardar incrementalmente
        output_file = Path("generated_tests/baseline/T_base_results.json")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
    
    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN - FASE 1")
    print("="*80)
    print(f"Total procesados: {len(classes)}")
    print(f"Exitosos: {success_count} ({success_count/len(classes)*100:.1f}%)")
    print(f"\n📁 Tests guardados en: generated_tests/baseline/")
    print(f"📄 Métricas en: generated_tests/baseline/T_base_results.json")
    print("\n✅ T_base generado. Listo para FASE 2 (LLM Refinement).")
    print("="*80)


if __name__ == "__main__":
    main()
