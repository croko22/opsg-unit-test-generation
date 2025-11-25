#!/usr/bin/env python3
"""
PASO 4: Evaluación - Responder las RQs

Compara T_base vs T_valid para responder:
- RQ1: ¿Mejora la eficacia (cobertura, mutación)?
- RQ2: ¿Mejora la legibilidad?
- RQ3: ¿Cuál es el overhead/costo?

Output: Métricas y gráficas para el paper
"""

import json
import subprocess
from pathlib import Path
from typing import Dict
import csv
import tempfile
import shutil
import re
import xml.etree.ElementTree as ET


class MetricsEvaluator:
    """Evalúa métricas para RQs."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.jacoco_agent = self.base_dir / "lib/jacocoagent.jar"
        self.jacoco_cli = self.base_dir / "lib/jacococli.jar"
        self.pitest_jar = self.base_dir / "lib/pitest-command-line.jar"
        self.junit_jar = self.base_dir / "lib/junit-4.11.jar"
        self.hamcrest_jar = self.base_dir / "lib/hamcrest-core-1.3.jar"
        self.evosuite_jar = self.base_dir / "lib/evosuite-1.2.0.jar"
    
    def find_sut_jar(self, project: str) -> Path:
        """
        Encuentra el JAR del SUT para un proyecto.
        
        Args:
            project: Nombre del proyecto (ej: "100_jgaap")
        
        Returns:
            Path al JAR o None si no se encuentra
        """
        # Buscar en SF110-binary
        project_path = self.base_dir / "data" / "SF110-binary" / project
        if project_path.exists():
            jar_files = list(project_path.glob("*.jar"))
            if jar_files:
                return jar_files[0]
        
        # Buscar en extended-dynamosa
        project_path = self.base_dir / "data" / "extended-dynamosa-repos-binary" / project
        if project_path.exists():
            jar_files = list(project_path.glob("*.jar"))
            if jar_files:
                return jar_files[0]
        
        return None
    
    def compile_test(self, test_file: Path, sut_jar: Path, output_dir: Path) -> bool:
        """
        Compila un archivo de test, incluyendo scaffolding si existe.
        
        Returns:
            True si compiló exitosamente
        """
        try:
            # Buscar scaffolding files en el mismo directorio
            test_dir = test_file.parent
            java_files = [test_file]
            
            # Agregar archivos *_scaffolding.java
            for scaff in test_dir.glob("*_scaffolding.java"):
                java_files.append(scaff)
            
            compile_cmd = [
                "javac",
                "-cp", f"{sut_jar}:{self.junit_jar}:{self.hamcrest_jar}:{self.evosuite_jar}",
                "-d", str(output_dir),
            ] + [str(f) for f in java_files]
            
            result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"      ⚠️  Errores de compilación:")
                for line in result.stderr.split('\n')[:5]:  # Primeras 5 líneas
                    if line.strip():
                        print(f"         {line}")
            
            return result.returncode == 0
        except Exception as e:
            print(f"      ⚠️  Excepción: {e}")
            return False

    
    def measure_coverage_jacoco(
        self,
        test_class: Path,
        sut_jar: Path,
        test_class_name: str
    ) -> Dict:
        """
        RQ1: Mide cobertura con JaCoCo.
        
        Args:
            test_class: Path al .class compilado del test
            sut_jar: Path al JAR del SUT
            test_class_name: Nombre completo de la clase (ej: "org.example.FooTest")
        
        Returns:
            dict con line_coverage, branch_coverage, etc.
        """
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            exec_file = tmpdir / "jacoco.exec"
            report_dir = tmpdir / "report"
            report_dir.mkdir()
            
            try:
                # 1. Ejecutar tests con JaCoCo agent
                test_dir = test_class.parent
                
                cmd = [
                    "java",
                    "-Djava.awt.headless=true",
                    f"-javaagent:{self.jacoco_agent}=destfile={exec_file}",
                    "-cp",
                    f"{test_dir}:{sut_jar}:{self.junit_jar}:{self.hamcrest_jar}:{self.evosuite_jar}",
                    "org.junit.runner.JUnitCore",
                    test_class_name
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                # Debug: print JUnit output
                if result.returncode != 0 or not exec_file.exists():
                    print(f"      ⚠️  JUnit stdout: {result.stdout[:200]}")
                    print(f"      ⚠️  JUnit stderr: {result.stderr[:200]}")
                
                # Si el test falló, aún podemos obtener cobertura
                if not exec_file.exists():
                    return {
                        "line_coverage": 0.0,
                        "branch_coverage": 0.0,
                        "method_coverage": 0.0,
                        "error": "No se generó archivo de ejecución"
                    }
                
                # 2. Generar reporte XML
                cmd = [
                    "java",
                    "-jar",
                    str(self.jacoco_cli),
                    "report",
                    str(exec_file),
                    "--classfiles",
                    str(sut_jar),
                    "--xml",
                    str(report_dir / "jacoco.xml")
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    return {
                        "line_coverage": 0.0,
                        "branch_coverage": 0.0,
                        "method_coverage": 0.0,
                        "error": f"Error generando reporte: {result.stderr}"
                    }
                
                # 3. Parsear XML
                xml_file = report_dir / "jacoco.xml"
                if not xml_file.exists():
                    return {
                        "line_coverage": 0.0,
                        "branch_coverage": 0.0,
                        "method_coverage": 0.0,
                        "error": "No se generó reporte XML"
                    }
                
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Extraer métricas
                line_covered = 0
                line_missed = 0
                branch_covered = 0
                branch_missed = 0
                method_covered = 0
                method_missed = 0
                
                for counter in root.findall(".//counter"):
                    counter_type = counter.get("type")
                    covered = int(counter.get("covered", 0))
                    missed = int(counter.get("missed", 0))
                    
                    if counter_type == "LINE":
                        line_covered += covered
                        line_missed += missed
                    elif counter_type == "BRANCH":
                        branch_covered += covered
                        branch_missed += missed
                    elif counter_type == "METHOD":
                        method_covered += covered
                        method_missed += missed
                
                # Calcular porcentajes
                line_total = line_covered + line_missed
                branch_total = branch_covered + branch_missed
                method_total = method_covered + method_missed
                
                return {
                    "line_coverage": (line_covered / line_total * 100) if line_total > 0 else 0.0,
                    "branch_coverage": (branch_covered / branch_total * 100) if branch_total > 0 else 0.0,
                    "method_coverage": (method_covered / method_total * 100) if method_total > 0 else 0.0,
                    "lines_covered": line_covered,
                    "lines_total": line_total,
                    "branches_covered": branch_covered,
                    "branches_total": branch_total,
                    "methods_covered": method_covered,
                    "methods_total": method_total
                }
                
            except subprocess.TimeoutExpired:
                return {
                    "line_coverage": 0.0,
                    "branch_coverage": 0.0,
                    "method_coverage": 0.0,
                    "error": "Timeout ejecutando tests"
                }
            except Exception as e:
                return {
                    "line_coverage": 0.0,
                    "branch_coverage": 0.0,
                    "method_coverage": 0.0,
                    "error": str(e)
                }
    
    def measure_mutation_score_pit(
        self,
        test_class: Path,
        sut_jar: Path,
        test_class_name: str,
        target_classes: str = None
    ) -> Dict:
        """
        RQ1: Mide mutation score con PIT.
        Esta es LA métrica clave.
        
        Args:
            test_class: Path al .class compilado del test
            sut_jar: Path al JAR del SUT
            test_class_name: Nombre completo de la clase test
            target_classes: Clases a mutar (glob pattern, ej: "org.example.*")
        
        Returns:
            dict con mutation_score, mutants_killed, total_mutants
        """
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            report_dir = tmpdir / "pit-reports"
            
            try:
                # Extraer el paquete de la clase de test para determinar target
                if target_classes is None:
                    # Inferir del nombre: org.example.FooTest -> org.example.*
                    parts = test_class_name.split('.')
                    if len(parts) > 1:
                        target_classes = '.'.join(parts[:-1]) + '.*'
                    else:
                        target_classes = '*'
                
                test_dir = test_class.parent
                
                # Comando PIT
                cmd = [
                    "java",
                    "-Djava.awt.headless=true",
                    "-cp",
                    f"{str(self.pitest_jar)}:{test_dir}:{sut_jar}:{self.junit_jar}:{self.hamcrest_jar}:{self.evosuite_jar}",
                    "org.pitest.mutationtest.commandline.MutationCoverageReport",
                    "--reportDir", str(report_dir),
                    "--targetClasses", target_classes,
                    "--targetTests", test_class_name,
                    "--sourceDirs", ".",  # PIT necesita esto aunque no genere reportes HTML
                    "--outputFormats", "XML,CSV",
                    "--timeoutConst", "4000",
                    "--threads", "1"
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutos max
                )
                
                # PIT puede retornar != 0 y aún generar reportes válidos
                # Buscar el XML de resultados
                xml_file = report_dir / "mutations.xml"
                
                if not xml_file.exists():
                    # Buscar en subdirectorios
                    xml_files = list(report_dir.rglob("mutations.xml"))
                    if xml_files:
                        xml_file = xml_files[0]
                    else:
                        return {
                            "mutation_score": 0.0,
                            "mutants_killed": 0,
                            "total_mutants": 0,
                            "line_coverage": 0.0,
                            "error": f"No se generó reporte XML. stderr: {result.stderr[:200]}"
                        }
                
                # Parsear XML de PIT
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Contar mutantes
                total_mutants = 0
                killed = 0
                survived = 0
                no_coverage = 0
                
                for mutation in root.findall(".//mutation"):
                    total_mutants += 1
                    status = mutation.get("status", "").upper()
                    
                    if status == "KILLED":
                        killed += 1
                    elif status == "SURVIVED":
                        survived += 1
                    elif status == "NO_COVERAGE":
                        no_coverage += 1
                
                # Mutation score = killed / (total - no_coverage)
                # Algunos contabilizan: killed / total
                # Usaremos la definición estándar
                testable_mutants = total_mutants - no_coverage
                mutation_score = (killed / testable_mutants * 100) if testable_mutants > 0 else 0.0
                
                # Line coverage de PIT (si está disponible)
                line_cov = 0.0
                for counter in root.findall(".//line-coverage"):
                    covered = int(counter.get("covered", 0))
                    total = int(counter.get("total", 0))
                    if total > 0:
                        line_cov = covered / total * 100
                        break
                
                return {
                    "mutation_score": round(mutation_score, 2),
                    "mutants_killed": killed,
                    "mutants_survived": survived,
                    "mutants_no_coverage": no_coverage,
                    "total_mutants": total_mutants,
                    "testable_mutants": testable_mutants,
                    "line_coverage": round(line_cov, 2)
                }
                
            except subprocess.TimeoutExpired:
                return {
                    "mutation_score": 0.0,
                    "mutants_killed": 0,
                    "total_mutants": 0,
                    "line_coverage": 0.0,
                    "error": "Timeout ejecutando PIT (>5 min)"
                }
            except Exception as e:
                return {
                    "mutation_score": 0.0,
                    "mutants_killed": 0,
                    "total_mutants": 0,
                    "line_coverage": 0.0,
                    "error": str(e)
                }

    
    def measure_readability(self, test_file: Path) -> Dict:
        """
        RQ2: Métricas de legibilidad del test.
        
        Returns:
            dict con cyclomatic_complexity, LOC, etc.
        """
        
        # Leer archivo
        with open(test_file) as f:
            code = f.read()
        
        # Métricas simples
        loc = len([l for l in code.split('\n') if l.strip() and not l.strip().startswith('//')])
        
        # TODO: Calcular complejidad ciclomática real
        # Puedes usar herramientas como JavaNCSS o PMD
        
        return {
            "lines_of_code": loc,
            "cyclomatic_complexity": 0,  # TODO
            "comment_ratio": 0.0,  # TODO
        }
    
    def compute_statistics(
        self,
        baseline_metrics: list,
        valid_metrics: list
    ) -> Dict:
        """
        Calcula estadísticas comparativas.
        
        Returns:
            dict con mejoras, p-values, etc.
        """
        
        import numpy as np
        from scipy import stats
        
        results = {}
        
        # Para cada métrica, calcular mejora y significancia
        metrics_to_compare = [
            'line_coverage',
            'branch_coverage',
            'mutation_score'
        ]
        
        for metric in metrics_to_compare:
            baseline_vals = [m.get(metric, 0) for m in baseline_metrics]
            valid_vals = [m.get(metric, 0) for m in valid_metrics]
            
            if not baseline_vals or not valid_vals:
                continue
            
            # Mejora promedio
            baseline_mean = np.mean(baseline_vals)
            valid_mean = np.mean(valid_vals)
            improvement = ((valid_mean - baseline_mean) / baseline_mean) * 100 if baseline_mean > 0 else 0
            
            # Test estadístico (requiere n >= 2)
            p_value = None
            stat = None
            
            if len(baseline_vals) >= 2 and len(valid_vals) >= 2:
                # Test estadístico (Wilcoxon signed-rank test)
                if len(baseline_vals) == len(valid_vals):
                    stat, p_value = stats.wilcoxon(baseline_vals, valid_vals)
                else:
                    # Mann-Whitney U test si tamaños diferentes
                    stat, p_value = stats.mannwhitneyu(baseline_vals, valid_vals)
            
            results[metric] = {
                "baseline_mean": baseline_mean,
                "valid_mean": valid_mean,
                "improvement_pct": improvement,
                "p_value": p_value if p_value is not None else "N/A (n < 2)",
                "significant": p_value < 0.05 if p_value is not None else False
            }
        
        return results


def main():
    """
    FASE 4: Evaluación Final
    """
    
    print("="*80)
    print("FASE 4: EVALUACIÓN - Responder RQs")
    print("="*80)
    print()
    
    # Cargar resultados de fases anteriores
    baseline_file = Path("generated_tests/baseline/T_base_results.json")
    valid_file = Path("generated_tests/validated/T_valid_results.json")
    
    if not baseline_file.exists() or not valid_file.exists():
        print("❌ Faltan archivos de resultados de fases anteriores")
        return 1
    
    with open(baseline_file) as f:
        baseline_results = json.load(f)
    
    with open(valid_file) as f:
        valid_results = json.load(f)
    
    # Filtrar exitosos
    baseline_success = [r for r in baseline_results if r.get('success')]
    valid_success = [r for r in valid_results if r.get('verified')]
    
    print(f"📊 Tests en T_base: {len(baseline_success)}")
    print(f"📊 Tests en T_valid: {len(valid_success)}")
    print()
    
    evaluator = MetricsEvaluator()
    
    # ========================================
    # RQ1: EFICACIA (Cobertura + Mutación)
    # ========================================
    print("="*80)
    print("RQ1: EFICACIA")
    print("="*80)
    print("\n¿Mejora T_valid la cobertura y detección de defectos vs T_base?\n")
    
    baseline_metrics = []
    valid_metrics = []
    
    print(f"📊 Midiendo métricas para {len(valid_success)} pares de tests...")
    print(f"   (Esto puede tardar varios minutos)\n")
    
    for i, valid in enumerate(valid_success, 1):
        project = valid['project']
        class_name = valid['class']
        
        print(f"[{i}/{len(valid_success)}] {class_name}")
        
        # Encontrar JAR del SUT
        sut_jar = evaluator.find_sut_jar(project)
        if not sut_jar:
            print(f"   ❌ No se encontró JAR del SUT para proyecto: {project}")
            continue
        
        print(f"   📦 SUT JAR: {sut_jar.name}")
        
        # Inferir nombre de clase de test
        test_class_name = class_name
        if not test_class_name.endswith("_ESTest"):
            test_class_name = f"{class_name}_ESTest"
        
        # Compilar ambos tests
        with tempfile.TemporaryDirectory() as tmpdir:
            compiled_dir = Path(tmpdir)
            
            # BASELINE
            baseline_file = Path(valid['original_file'])
            print(f"   📄 Baseline: {baseline_file}")
            if baseline_file.exists():
                print(f"      Existe: ✅")
                if evaluator.compile_test(baseline_file, sut_jar, compiled_dir):
                    print(f"      Compiló: ✅")
                    # Buscar el .class
                    test_class_file = compiled_dir / f"{test_class_name.replace('.', '/')}.class"
                    print(f"      Buscando: {test_class_file}")
                    print(f"      Existe .class: {test_class_file.exists()}")
                    
                    # Listar contenido del directorio compilado
                    print(f"      Contenido de {compiled_dir}:")
                    for item in compiled_dir.rglob("*.class"):
                        print(f"         {item.relative_to(compiled_dir)}")
                    
                    if test_class_file.exists():
                        print(f"   📊 Baseline - Midiendo cobertura...")
                        cov_baseline = evaluator.measure_coverage_jacoco(
                            test_class_file,
                            sut_jar,
                            test_class_name
                        )
                        
                        if 'error' not in cov_baseline:
                            print(f"      Líneas: {cov_baseline.get('line_coverage', 0):.1f}%")
                        else:
                            print(f"      ⚠️  Error: {cov_baseline['error'][:50]}")
                        
                        print(f"   🧬 Baseline - Midiendo mutación...")
                        mut_baseline = evaluator.measure_mutation_score_pit(
                            test_class_file,
                            sut_jar,
                            test_class_name
                        )
                        
                        if 'error' not in mut_baseline:
                            print(f"      Mutation: {mut_baseline.get('mutation_score', 0):.1f}%")
                        else:
                            print(f"      ⚠️  Error: {mut_baseline['error'][:50]}")
                        
                        baseline_metrics.append({
                            **cov_baseline,
                            **mut_baseline,
                            "class": class_name,
                            "project": project
                        })
            
            # REFINED/VALID
            refined_file = Path(valid['refined_file'])
            if refined_file.exists():
                # Limpiar directorio de compilación
                shutil.rmtree(compiled_dir)
                compiled_dir.mkdir()
                
                if evaluator.compile_test(refined_file, sut_jar, compiled_dir):
                    test_class_file = compiled_dir / f"{test_class_name.replace('.', '/')}.class"
                    if test_class_file.exists():
                        print(f"   📊 Refined - Midiendo cobertura...")
                        cov_valid = evaluator.measure_coverage_jacoco(
                            test_class_file,
                            sut_jar,
                            test_class_name
                        )
                        
                        if 'error' not in cov_valid:
                            print(f"      Líneas: {cov_valid.get('line_coverage', 0):.1f}%")
                        else:
                            print(f"      ⚠️  Error: {cov_valid['error'][:50]}")
                        
                        print(f"   🧬 Refined - Midiendo mutación...")
                        mut_valid = evaluator.measure_mutation_score_pit(
                            test_class_file,
                            sut_jar,
                            test_class_name
                        )
                        
                        if 'error' not in mut_valid:
                            print(f"      Mutation: {mut_valid.get('mutation_score', 0):.1f}%")
                        else:
                            print(f"      ⚠️  Error: {mut_valid['error'][:50]}")
                        
                        valid_metrics.append({
                            **cov_valid,
                            **mut_valid,
                            "class": class_name,
                            "project": project
                        })
        
        print()
    
    # Estadísticas RQ1
    print("\n" + "="*80)
    print("RESULTADOS RQ1")
    print("="*80)
    
    if baseline_metrics and valid_metrics:
        stats = evaluator.compute_statistics(baseline_metrics, valid_metrics)
        
        print("\n📊 COBERTURA DE LÍNEA:")
        if 'line_coverage' in stats:
            s = stats['line_coverage']
            print(f"   T_base:  {s['baseline_mean']:.2f}%")
            print(f"   T_valid: {s['valid_mean']:.2f}%")
            print(f"   Mejora:  {s['improvement_pct']:+.2f}%")
            if isinstance(s['p_value'], str):
                print(f"   p-value: {s['p_value']}")
            else:
                print(f"   p-value: {s['p_value']:.4f} {'✅ significativo' if s['significant'] else '❌ no significativo'}")
        
        print("\n📊 COBERTURA DE RAMAS:")
        if 'branch_coverage' in stats:
            s = stats['branch_coverage']
            print(f"   T_base:  {s['baseline_mean']:.2f}%")
            print(f"   T_valid: {s['valid_mean']:.2f}%")
            print(f"   Mejora:  {s['improvement_pct']:+.2f}%")
            if isinstance(s['p_value'], str):
                print(f"   p-value: {s['p_value']}")
            else:
                print(f"   p-value: {s['p_value']:.4f} {'✅ significativo' if s['significant'] else '❌ no significativo'}")
        
        print("\n🧬 MUTATION SCORE (MÉTRICA CLAVE):")
        if 'mutation_score' in stats:
            s = stats['mutation_score']
            print(f"   T_base:  {s['baseline_mean']:.2f}%")
            print(f"   T_valid: {s['valid_mean']:.2f}%")
            print(f"   Mejora:  {s['improvement_pct']:+.2f}%")
            if isinstance(s['p_value'], str):
                print(f"   p-value: {s['p_value']}")
            else:
                print(f"   p-value: {s['p_value']:.4f} {'✅ significativo' if s['significant'] else '❌ no significativo'}")
    else:
        print("❌ No se pudieron calcular métricas")
    
    print()
    
    # ========================================
    # RQ2: LEGIBILIDAD
    # ========================================
    print("="*80)
    print("RQ2: LEGIBILIDAD")
    print("="*80)
    print("\n¿Son más legibles los tests de T_valid?\n")
    
    readability_baseline = []
    readability_valid = []
    
    for valid in valid_success:
        # Baseline
        baseline_file = Path(valid['original_file'])
        if baseline_file.exists():
            metrics = evaluator.measure_readability(baseline_file)
            readability_baseline.append(metrics)
        
        # Valid
        valid_file = Path(valid['refined_file'])
        if valid_file.exists():
            metrics = evaluator.measure_readability(valid_file)
            readability_valid.append(metrics)
    
    if readability_baseline and readability_valid:
        avg_loc_baseline = sum(m['lines_of_code'] for m in readability_baseline) / len(readability_baseline)
        avg_loc_valid = sum(m['lines_of_code'] for m in readability_valid) / len(readability_valid)
        
        print(f"📏 LOC promedio:")
        print(f"   T_base:  {avg_loc_baseline:.1f} líneas")
        print(f"   T_valid: {avg_loc_valid:.1f} líneas")
        print(f"   Cambio:  {((avg_loc_valid - avg_loc_baseline) / avg_loc_baseline * 100):+.1f}%")
    
    print("\n⚠️  Métricas de complejidad - TODO: Opcional (PMD, Checkstyle, etc.)")
    print()
    
    # ========================================
    # RQ3: EFICIENCIA / OVERHEAD
    # ========================================
    print("="*80)
    print("RQ3: EFICIENCIA")
    print("="*80)
    print("\n¿Cuál es el costo de refinamiento con LLM?\n")
    
    # Calcular costos
    total_tokens = sum(r.get('tokens_used', 0) for r in valid_results if r.get('success'))
    
    # Tasa de descarte
    refined_count = len([r for r in valid_results if r.get('success', False)])
    verified_count = len(valid_success)
    discard_rate = ((refined_count - verified_count) / refined_count * 100) if refined_count > 0 else 0
    
    print(f"💰 Tokens usados: {total_tokens:,}")
    print(f"🗑️  Tasa de descarte: {discard_rate:.1f}%")
    print(f"   ({refined_count - verified_count}/{refined_count} tests descartados en verificación)")
    print()
    
    # ========================================
    # GUARDAR RESULTADOS
    # ========================================
    
    # Preparar datos para JSON
    evaluation_results = {
        "rq1_efficacy": {
            "description": "Métricas de cobertura y mutación",
            "statistics": stats if baseline_metrics and valid_metrics else {},
            "baseline_metrics": baseline_metrics,
            "valid_metrics": valid_metrics,
            "summary": {
                "n_tests_measured": len(baseline_metrics),
                "avg_line_coverage_baseline": sum(m.get('line_coverage', 0) for m in baseline_metrics) / len(baseline_metrics) if baseline_metrics else 0,
                "avg_line_coverage_valid": sum(m.get('line_coverage', 0) for m in valid_metrics) / len(valid_metrics) if valid_metrics else 0,
                "avg_mutation_score_baseline": sum(m.get('mutation_score', 0) for m in baseline_metrics) / len(baseline_metrics) if baseline_metrics else 0,
                "avg_mutation_score_valid": sum(m.get('mutation_score', 0) for m in valid_metrics) / len(valid_metrics) if valid_metrics else 0
            }
        },
        "rq2_readability": {
            "baseline_avg_loc": avg_loc_baseline if readability_baseline else 0,
            "valid_avg_loc": avg_loc_valid if readability_valid else 0,
            "change_pct": ((avg_loc_valid - avg_loc_baseline) / avg_loc_baseline * 100) if (readability_baseline and avg_loc_baseline > 0) else 0
        },
        "rq3_efficiency": {
            "total_tokens": total_tokens,
            "discard_rate_pct": discard_rate,
            "refined_count": refined_count,
            "verified_count": verified_count
        }
    }
    
    output_file = Path("evaluation_results/final_evaluation.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(evaluation_results, f, indent=2)
    
    # Generar tabla CSV para el paper
    csv_file = Path("evaluation_results/results_table.csv")
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Metric', 'T_base', 'T_valid', 'Improvement (%)', 'p-value', 'Significant'])
        
        if baseline_metrics and valid_metrics and stats:
            for metric in ['line_coverage', 'branch_coverage', 'mutation_score']:
                if metric in stats:
                    s = stats[metric]
                    p_val = s['p_value'] if isinstance(s['p_value'], str) else f"{s['p_value']:.4f}"
                    writer.writerow([
                        metric.replace('_', ' ').title(),
                        f"{s['baseline_mean']:.2f}",
                        f"{s['valid_mean']:.2f}",
                        f"{s['improvement_pct']:+.2f}",
                        p_val,
                        "Yes" if s['significant'] else "No"
                    ])
    
    # Guardar métricas detalladas por test
    detailed_csv = Path("evaluation_results/detailed_metrics.csv")
    with open(detailed_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Project', 'Class', 'Type',
            'Line Coverage (%)', 'Branch Coverage (%)', 'Method Coverage (%)',
            'Mutation Score (%)', 'Mutants Killed', 'Total Mutants'
        ])
        
        for m in baseline_metrics:
            writer.writerow([
                m.get('project', ''),
                m.get('class', ''),
                'Baseline',
                f"{m.get('line_coverage', 0):.2f}",
                f"{m.get('branch_coverage', 0):.2f}",
                f"{m.get('method_coverage', 0):.2f}",
                f"{m.get('mutation_score', 0):.2f}",
                m.get('mutants_killed', 0),
                m.get('total_mutants', 0)
            ])
        
        for m in valid_metrics:
            writer.writerow([
                m.get('project', ''),
                m.get('class', ''),
                'Refined',
                f"{m.get('line_coverage', 0):.2f}",
                f"{m.get('branch_coverage', 0):.2f}",
                f"{m.get('method_coverage', 0):.2f}",
                f"{m.get('mutation_score', 0):.2f}",
                m.get('mutants_killed', 0),
                m.get('total_mutants', 0)
            ])
    
    print("="*80)
    print("RESUMEN FINAL")
    print("="*80)
    print(f"\n📄 Resultados completos: {output_file}")
    print(f"📊 Tabla resumen: {csv_file}")
    print(f"📊 Métricas detalladas: {detailed_csv}")
    print("\n✅ FASE 4 COMPLETADA")
    print("   - JaCoCo implementado para cobertura")
    print("   - PIT implementado para mutation score")
    print("   - Análisis estadístico completo")
    print("\n💡 PRÓXIMOS PASOS OPCIONALES:")
    print("   1. Implementar métricas de complejidad adicionales (RQ2)")
    print("   2. Generar gráficas (matplotlib/seaborn) en Phase 5")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    main()
