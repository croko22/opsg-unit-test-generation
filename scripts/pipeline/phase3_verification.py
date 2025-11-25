#!/usr/bin/env python3
"""
PASO 3: Verificación y Filtrado

Verifica que los tests refinados:
1. Compilan (Verificación Estática)
2. Preservan el oráculo del test original (Verificación Dinámica)

Output: T_valid (tests refinados que pasan ambas verificaciones)
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple, Optional
import shutil


class TestVerifier:
    """Verifica tests refinados."""
    
    def __init__(self):
        self.junit_jar = Path("lib/junit-4.11.jar")
        self.evosuite_jar = Path("lib/evosuite-1.2.0.jar")
        self.java_version = self._check_java()
    
    def _check_java(self) -> str:
        """Verifica versión de Java."""
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True
        )
        return result.stderr.split('\n')[0]
    
    def compile_test(
        self,
        test_file: Path,
        sut_jar: Path,
        output_dir: Path
    ) -> dict:
        """
        3.a. VERIFICACIÓN ESTÁTICA: Compila el test.
        
        Returns:
            dict con 'success', 'error_message', etc.
        """
        
        # Classpath: SUT + JUnit + EvoSuite + test source
        classpath = f"{sut_jar}:{self.junit_jar}:{self.evosuite_jar}:{test_file.parent}"
        
        cmd = [
            "javac",
            "-cp", classpath,
            "-d", str(output_dir),
            str(test_file)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": "compilation_failed",
                    "message": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_test(
        self,
        test_class: str,
        sut_jar: Path,
        compiled_dir: Path
    ) -> dict:
        """
        Ejecuta un test y retorna el resultado.
        
        Returns:
            dict con 'passed', 'failed', 'errors'
        """
        
        classpath = f"{sut_jar}:{self.junit_jar}:{self.evosuite_jar}:{compiled_dir}"
        
        cmd = [
            "java",
            "-cp", classpath,
            "org.junit.runner.JUnitCore",
            test_class
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parsear output de JUnit
            output = result.stdout + result.stderr
            
            passed = result.returncode == 0
            
            return {
                "passed": passed,
                "returncode": result.returncode,
                "output": output
            }
            
        except subprocess.TimeoutExpired:
            return {"passed": False, "error": "timeout"}
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    def verify_oracle_preservation(
        self,
        original_result: dict,
        refined_result: dict
    ) -> Tuple[bool, str]:
        """
        3.b. VERIFICACIÓN DINÁMICA: Verifica preservación del oráculo.
        
        El test refinado debe comportarse igual que el original:
        - Si original pasaba → refinado debe pasar
        - Si original fallaba → refinado debe fallar (por la misma razón)
        
        Returns:
            (preservado: bool, reason: str)
        """
        
        # Caso 1: Original pasaba
        if original_result.get('passed'):
            if refined_result.get('passed'):
                return True, "Oracle preserved: both pass"
            else:
                return False, "Oracle violated: original passed but refined failed"
        
        # Caso 2: Original fallaba
        else:
            if refined_result.get('passed'):
                return False, "Oracle violated: original failed but refined passes (bug hidden)"
            else:
                # Ambos fallan - verificar que sea por la misma razón
                # Esto es una heurística simple - puedes mejorarla
                return True, "Oracle preserved: both fail"
    
    def find_jar(self, project: str) -> Optional[Path]:
        """Encuentra el JAR del SUT."""
        # Buscar en SF110
        base = Path("data/SF110-binary") / project
        if not base.exists():
            # Buscar en Extended DynaMOSA
            base = Path("data/extended-dynamosa-repos-binary") / project
        
        if not base.exists():
            return None
        
        jars = list(base.glob("*.jar"))
        return jars[0] if jars else None


def main():
    """
    FASE 3: Verificación y Filtrado (T_refined → T_valid)
    """
    
    print("="*80)
    print("FASE 3: VERIFICACIÓN Y FILTRADO (T_refined → T_valid)")
    print("="*80)
    print()
    
    # Cargar resultados de Fase 2
    refined_results_file = Path("generated_tests/refined/T_refined_results.json")
    
    if not refined_results_file.exists():
        print("❌ No se encuentra T_refined_results.json")
        print("   Ejecuta primero: python phase2_llm_refinement.py")
        return 1
    
    with open(refined_results_file) as f:
        refined_results = json.load(f)
    
    # Filtrar solo exitosos de Fase 2
    to_verify = [r for r in refined_results if r.get('success')]
    print(f"📊 Tests a verificar: {len(to_verify)}")
    print()
    
    verifier = TestVerifier()
    
    valid_results = []
    compiled_count = 0
    oracle_preserved_count = 0
    
    for i, refined in enumerate(to_verify, 1):
        project = refined['project']
        class_name = refined['class']
        
        print(f"\n[{i}/{len(to_verify)}] {class_name}")
        print("-" * 60)
        
        # Buscar JAR del SUT
        sut_jar = verifier.find_jar(project)
        if not sut_jar:
            print("❌ SUT JAR not found")
            valid_results.append({
                **refined,
                "verified": False,
                "error": "sut_jar_not_found"
            })
            continue
        
        # 3.a. VERIFICACIÓN ESTÁTICA: Compilar test refinado
        with tempfile.TemporaryDirectory() as tmpdir:
            compiled_dir = Path(tmpdir)
            
            refined_file = Path(refined['refined_file'])
            print(f"🔨 Compilando test refinado...")
            
            compile_result = verifier.compile_test(
                refined_file,
                sut_jar,
                compiled_dir
            )
            
            if not compile_result['success']:
                print(f"   ❌ No compila: {compile_result.get('error')}")
                # Mostrar primeras líneas del error
                error_msg = compile_result.get('message', '')
                if error_msg:
                    lines = error_msg.strip().split('\n')[:10]  # Primeras 10 líneas
                    for line in lines:
                        print(f"      {line}")
                    if len(error_msg.split('\n')) > 10:
                        print(f"      ... ({len(error_msg.split('\n')) - 10} líneas más)")
                valid_results.append({
                    **refined,
                    "verified": False,
                    "compilation": compile_result
                })
                continue
            
            print(f"   ✅ Compilación exitosa")
            compiled_count += 1
            
            # 3.b. VERIFICACIÓN DINÁMICA: Ejecutar y comparar oráculos
            print(f"🧪 Verificando preservación del oráculo...")
            
            # Ejecutar test ORIGINAL
            original_file = Path(refined['original_file'])
            test_class = class_name + "_ESTest"  # Convención de EvoSuite
            
            # Compilar original
            compile_orig = verifier.compile_test(
                original_file,
                sut_jar,
                compiled_dir
            )
            
            if not compile_orig['success']:
                print(f"   ⚠️  Test original no compila (raro)")
                continue
            
            # Ejecutar ambos
            original_run = verifier.run_test(test_class, sut_jar, compiled_dir)
            
            # Recompilar refinado (sobreescribir clases)
            verifier.compile_test(refined_file, sut_jar, compiled_dir)
            refined_run = verifier.run_test(test_class, sut_jar, compiled_dir)
            
            # Verificar oráculo
            preserved, reason = verifier.verify_oracle_preservation(
                original_run,
                refined_run
            )
            
            if preserved:
                print(f"   ✅ Oráculo preservado")
                oracle_preserved_count += 1
                
                valid_results.append({
                    **refined,
                    "verified": True,
                    "compilation": "success",
                    "oracle_preserved": True,
                    "oracle_reason": reason
                })
            else:
                print(f"   ❌ Oráculo violado: {reason}")
                valid_results.append({
                    **refined,
                    "verified": False,
                    "compilation": "success",
                    "oracle_preserved": False,
                    "oracle_reason": reason
                })
    
    # Guardar T_valid
    output_file = Path("generated_tests/validated/T_valid_results.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(valid_results, f, indent=2)
    
    # Copiar tests válidos a directorio separado
    valid_dir = Path("generated_tests/validated")
    for result in valid_results:
        if result.get('verified'):
            refined_path = Path(result['refined_file'])
            dest = valid_dir / refined_path.relative_to("generated_tests/refined")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(refined_path, dest)
    
    # Resumen
    print("\n" + "="*80)
    print("RESUMEN - FASE 3")
    print("="*80)
    print(f"Tests verificados: {len(to_verify)}")
    print(f"Compilaron exitosamente: {compiled_count} ({compiled_count/len(to_verify)*100:.1f}%)")
    print(f"Preservaron oráculo: {oracle_preserved_count} ({oracle_preserved_count/len(to_verify)*100:.1f}%)")
    print(f"\n📁 Tests válidos en: generated_tests/validated/")
    print(f"📄 Resultados en: {output_file}")
    print(f"\n✅ T_valid generado con {oracle_preserved_count} tests.")
    print("   Listo para FASE 4 (Evaluación).")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    main()
