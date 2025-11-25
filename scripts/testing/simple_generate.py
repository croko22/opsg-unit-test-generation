#!/usr/bin/env python3
"""
SIMPLE test generator - Just works, no bullshit.

Genera tests con EvoSuite para una lista de clases.
Guarda todo en generated_tests/baseline/ con un JSON simple.

Usage:
    python simple_generate.py
"""

import csv
import json
import subprocess
from pathlib import Path
from datetime import datetime


def find_jar(project: str) -> Path:
    """Encuentra el JAR de un proyecto."""
    base = Path("data/extended-dynamosa-repos-binary") / project
    jars = list(base.glob("*.jar"))
    return jars[0] if jars else None


def generate_test(project: str, class_name: str, time_budget: int = 60):
    """Genera UN test. Simple."""
    
    print(f"\n{'='*60}")
    print(f"{class_name}")
    print('='*60)
    
    # Buscar JAR
    jar = find_jar(project)
    if not jar:
        print("❌ No JAR")
        return {"success": False, "error": "no_jar"}
    
    # Output dir
    output = Path("generated_tests/baseline") / project / class_name.replace(".", "_")
    output.mkdir(parents=True, exist_ok=True)
    
    # EvoSuite
    evosuite = list(Path("lib").glob("evosuite-*.jar"))[-1]
    
    # Comando
    cmd = [
        "java", "-jar", str(evosuite),
        "-class", class_name,
        "-target", str(jar),
        "-Dtest_dir", str(output),
        "-Dsearch_budget", str(time_budget),
        "-Dminimize", "true"
    ]
    
    # Ejecutar
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=time_budget + 120
        )
        
        # Verificar
        tests = list(output.glob("**/*_ESTest.java"))
        
        if tests:
            print(f"✅ OK - {len(tests)} tests")
            return {
                "success": True,
                "num_tests": len(tests),
                "output_dir": str(output)
            }
        else:
            print("⚠️ Sin tests")
            return {"success": False, "error": "no_tests"}
            
    except subprocess.TimeoutExpired:
        print("⏱️ Timeout")
        return {"success": False, "error": "timeout"}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Genera baseline tests. Simple."""
    
    print("="*60)
    print("SIMPLE BASELINE GENERATOR")
    print("="*60)
    
    # Cargar clases
    csv_path = Path("data/extended-dynamosa-repos-binary/classes.csv")
    classes = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        classes = list(reader)
    
    # CAMBIAR ESTO para probar con pocas clases
    LIMIT = 5  # ← CAMBIA ESTO: None para todas, 5 para prueba
    if LIMIT:
        classes = classes[:LIMIT]
        print(f"⚠️ Solo procesando {LIMIT} clases (cambiar LIMIT en el código)")
    
    print(f"\n📊 Total: {len(classes)} clases\n")
    
    # Generar
    results = []
    ok = 0
    
    for i, cls in enumerate(classes, 1):
        print(f"[{i}/{len(classes)}]", end=" ")
        
        result = generate_test(cls['project'], cls['class'])
        result['project'] = cls['project']
        result['class'] = cls['class']
        results.append(result)
        
        if result['success']:
            ok += 1
    
    # Guardar
    output_file = Path("generated_tests/baseline") / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Resumen
    print("\n" + "="*60)
    print(f"LISTO: {ok}/{len(classes)} exitosos ({ok/len(classes)*100:.0f}%)")
    print(f"Resultados: {output_file}")
    print("="*60)


if __name__ == "__main__":
    main()
