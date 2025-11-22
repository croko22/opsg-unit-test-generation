#!/usr/bin/env python3
"""
PIPELINE COMPLETO: Metodología de Tesis

Ejecuta las 5 fases en secuencia:
  1. Baseline con EvoSuite (T_base)
  2. Refinamiento con LLM (T_refined)
  3. Verificación (T_valid)
  4. Evaluación con métricas (RQ1, RQ2, RQ3)
  5. Análisis y visualización

Uso:
  python run_pipeline.py --limit 10        # Test rápido con 10 clases
  python run_pipeline.py --full            # Ejecución completa (SF110 + Extended DynaMOSA)
  python run_pipeline.py --phase 1         # Solo ejecutar Fase 1
  python run_pipeline.py --resume          # Continuar desde última fase exitosa
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List
import time


class PipelineRunner:
    """Orquestador del pipeline completo."""
    
    def __init__(self, args):
        self.args = args
        # Directorio base del proyecto (dos niveles arriba desde scripts/pipeline/)
        self.base_dir = Path(__file__).parent.parent.parent
        self.pipeline_dir = Path(__file__).parent
        
        self.phases = [
            {
                "id": 1,
                "name": "Baseline Generation",
                "script": self.pipeline_dir / "phase1_generate_baseline.py",
                "output_marker": self.base_dir / "baseline_tests/T_base_results.json"
            },
            {
                "id": 2,
                "name": "LLM Refinement",
                "script": self.pipeline_dir / "phase2_llm_refinement.py",
                "output_marker": self.base_dir / "refined_tests/T_refined_results.json"
            },
            {
                "id": 3,
                "name": "Verification",
                "script": self.pipeline_dir / "phase3_verification.py",
                "output_marker": self.base_dir / "valid_tests/T_valid_results.json"
            },
            {
                "id": 4,
                "name": "Evaluation",
                "script": self.pipeline_dir / "phase4_evaluation.py",
                "output_marker": self.base_dir / "evaluation_results/final_evaluation.json"
            },
            {
                "id": 5,
                "name": "Analysis & Visualization",
                "script": self.pipeline_dir / "phase5_analysis.py",
                "output_marker": self.base_dir / "figures/summary_table.csv"
            }
        ]
    
    def check_prerequisites(self) -> List[str]:
        """Verifica que todo esté listo."""
        
        errors = []
        
        # Java 8
        try:
            result = subprocess.run(
                ["java", "-version"],
                capture_output=True,
                text=True
            )
            version_info = result.stderr
            if "1.8" not in version_info:
                errors.append("❌ Java 8 no detectado (necesario para EvoSuite)")
        except:
            errors.append("❌ Java no encontrado")
        
        # EvoSuite
        evosuite_jar = self.base_dir / "lib/evosuite-1.2.0.jar"
        if not evosuite_jar.exists():
            errors.append(f"❌ EvoSuite no encontrado: {evosuite_jar}")
        
        # JaCoCo (para evaluación)
        jacoco_agent = self.base_dir / "lib/jacocoagent.jar"
        jacoco_cli = self.base_dir / "lib/jacococli.jar"
        if not jacoco_agent.exists() or not jacoco_cli.exists():
            errors.append("⚠️  JaCoCo no encontrado (necesario para Fase 4 RQ1)")
        
        # Datos
        sf110_dir = self.base_dir / "data/SF110-binary"
        extended_dir = self.base_dir / "data/extended-dynamosa-repos-binary"
        
        if not sf110_dir.exists():
            errors.append(f"❌ SF110 no encontrado: {sf110_dir}")
        
        if not extended_dir.exists():
            errors.append(f"❌ Extended DynaMOSA no encontrado: {extended_dir}")
        
        # Scripts de fases
        for phase in self.phases:
            script = Path(phase['script'])
            if not script.exists():
                errors.append(f"❌ Script faltante: {script}")
        
        return errors
    
    def get_last_completed_phase(self) -> int:
        """Determina la última fase completada exitosamente."""
        
        for i in range(len(self.phases) - 1, -1, -1):
            phase = self.phases[i]
            marker_file = Path(phase['output_marker'])
            
            if marker_file.exists():
                return phase['id']
        
        return 0  # Ninguna fase completada
    
    def run_phase(self, phase_id: int) -> bool:
        """
        Ejecuta una fase específica.
        
        Returns:
            True si exitoso, False si falla
        """
        
        phase = self.phases[phase_id - 1]
        
        print("\n" + "="*80)
        print(f"FASE {phase['id']}: {phase['name']}")
        print("="*80)
        print(f"Script: {phase['script']}")
        print()
        
        # Construir comando
        cmd = ["python3", str(phase['script'])]
        
        # Pasar LIMIT solo a Fase 1
        if phase['id'] == 1 and self.args.limit:
            # Modificar el script temporalmente para usar el LIMIT
            # O pasar como variable de entorno
            import os
            os.environ['LIMIT'] = str(self.args.limit)
        
        # Ejecutar desde el directorio base del proyecto
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.base_dir),  # Ejecutar desde la raíz del proyecto
                check=False  # No lanzar excepción si falla
            )
            
            elapsed = time.time() - start_time
            
            if result.returncode != 0:
                print(f"\n❌ Fase {phase['id']} FALLÓ (código: {result.returncode})")
                print(f"⏱️  Tiempo: {elapsed:.1f}s")
                return False
            
            # Verificar que se creó el output marker
            marker_file = Path(phase['output_marker'])
            if not marker_file.exists():
                print(f"\n⚠️  Fase {phase['id']} completó pero no generó: {marker_file}")
                return False
            
            print(f"\n✅ Fase {phase['id']} COMPLETADA")
            print(f"⏱️  Tiempo: {elapsed:.1f}s")
            print(f"📁 Output: {marker_file}")
            
            return True
        
        except Exception as e:
            print(f"\n❌ Error ejecutando Fase {phase['id']}: {e}")
            return False
    
    def run_full_pipeline(self):
        """Ejecuta el pipeline completo."""
        
        print("="*80)
        print("PIPELINE COMPLETO: Metodología de Tesis")
        print("="*80)
        
        if self.args.limit:
            print(f"⚙️  Modo: TEST ({self.args.limit} clases)")
        else:
            print("⚙️  Modo: COMPLETO (todos los benchmarks)")
        
        print()
        
        # Verificar requisitos
        print("🔍 Verificando prerequisitos...")
        errors = self.check_prerequisites()
        
        if errors:
            print("\n❌ PROBLEMAS DETECTADOS:")
            for error in errors:
                print(f"   {error}")
            print("\nCorrige los problemas antes de continuar.")
            return 1
        
        print("✅ Todos los prerequisitos OK\n")
        
        # Determinar desde dónde empezar
        if self.args.resume:
            last_completed = self.get_last_completed_phase()
            start_phase = last_completed + 1
            print(f"🔄 Resumiendo desde Fase {start_phase}")
        elif self.args.phase:
            start_phase = self.args.phase
            print(f"▶️  Ejecutando solo Fase {start_phase}")
        else:
            start_phase = 1
            print("▶️  Ejecutando pipeline completo")
        
        # Ejecutar fases
        total_start = time.time()
        
        for phase in self.phases:
            if phase['id'] < start_phase:
                print(f"⏭️  Saltando Fase {phase['id']} (ya completada)")
                continue
            
            if self.args.phase and phase['id'] != self.args.phase:
                continue
            
            success = self.run_phase(phase['id'])
            
            if not success:
                print("\n💥 Pipeline ABORTADO")
                return 1
            
            # Si solo se pidió una fase, salir
            if self.args.phase:
                break
        
        total_elapsed = time.time() - total_start
        
        # Resumen final
        print("\n" + "="*80)
        print("PIPELINE COMPLETADO")
        print("="*80)
        print(f"⏱️  Tiempo total: {total_elapsed/60:.1f} minutos")
        print("\n📁 Resultados:")
        for phase in self.phases:
            marker = Path(phase['output_marker'])
            status = "✅" if marker.exists() else "❌"
            print(f"   {status} Fase {phase['id']}: {marker}")
        
        print("\n🎉 ¡Metodología completada!")
        print("   Revisa la carpeta 'figures/' para gráficas y tablas")
        print("="*80)
        
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline completo de metodología de tesis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Test rápido con 10 clases
  python run_pipeline.py --limit 10
  
  # Ejecución completa
  python run_pipeline.py --full
  
  # Solo ejecutar Fase 1 (baseline)
  python run_pipeline.py --phase 1
  
  # Continuar desde última fase exitosa
  python run_pipeline.py --resume
        """
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Número de clases para test rápido (default: ejecutar todo)'
    )
    
    parser.add_argument(
        '--full',
        action='store_true',
        help='Ejecución completa de todos los benchmarks'
    )
    
    parser.add_argument(
        '--phase',
        type=int,
        choices=[1, 2, 3, 4, 5],
        help='Ejecutar solo una fase específica'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Continuar desde última fase completada'
    )
    
    args = parser.parse_args()
    
    # Validaciones
    if args.limit and args.full:
        print("❌ No puedes usar --limit y --full juntos")
        return 1
    
    runner = PipelineRunner(args)
    return runner.run_full_pipeline()


if __name__ == "__main__":
    sys.exit(main())
