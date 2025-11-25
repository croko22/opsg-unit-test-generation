#!/usr/bin/env python3
"""
PASO 5: Análisis y Visualización

Genera las figuras y tablas para tu paper:
- Gráficas de mejora (box plots, scatter, etc.)
- Tablas comparativas
- Test estadísticos
- Análisis de casos de éxito/fracaso

Output: Figuras para tu tesis/paper
"""

import json
from pathlib import Path
from typing import Dict, List
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from scipy import stats


class ResultsAnalyzer:
    """Analiza resultados y genera visualizaciones."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        
        # Configurar estilo para papers
        sns.set_style("whitegrid")
        sns.set_palette("colorblind")
        plt.rcParams['figure.dpi'] = 300
        plt.rcParams['font.size'] = 10
    
    def load_data(self) -> Dict:
        """Carga todos los resultados de las fases anteriores."""
        
        data = {}
        
        # T_base
        baseline_file = Path("generated_tests/baseline/T_base_results.json")
        if baseline_file.exists():
            with open(baseline_file) as f:
                data['baseline'] = json.load(f)
        
        # T_valid
        valid_file = Path("generated_tests/validated/T_valid_results.json")
        if valid_file.exists():
            with open(valid_file) as f:
                data['valid'] = json.load(f)
        
        # Evaluation
        eval_file = Path("evaluation_results/final_evaluation.json")
        if eval_file.exists():
            with open(eval_file) as f:
                data['evaluation'] = json.load(f)
        
        return data
    
    def create_comparison_dataframe(self, data: Dict) -> pd.DataFrame:
        """
        Crea DataFrame con métricas pareadas baseline vs valid.
        
        Returns:
            DataFrame con columnas: class, baseline_cov, valid_cov, baseline_mut, valid_mut, etc.
        """
        
        rows = []
        
        baseline_dict = {r['class']: r for r in data['baseline'] if r.get('success')}
        
        for valid in data['valid']:
            if not valid.get('verified'):
                continue
            
            class_name = valid['class']
            baseline = baseline_dict.get(class_name)
            
            if not baseline:
                continue
            
            row = {
                'class': class_name,
                'baseline_coverage': baseline.get('coverage', 0),
                'valid_coverage': valid.get('coverage', 0),
                'baseline_mutation': baseline.get('mutation_score', 0),
                'valid_mutation': valid.get('mutation_score', 0),
                'baseline_loc': baseline.get('loc', 0),
                'valid_loc': valid.get('loc', 0),
                'baseline_time': baseline.get('generation_time', 0),
                'refinement_time': valid.get('refinement_time', 0),
                'tokens_used': valid.get('tokens_used', 0)
            }
            
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def plot_coverage_comparison(self, df: pd.DataFrame):
        """RQ1: Gráfica de comparación de cobertura."""
        
        if df.empty or 'baseline_coverage' not in df.columns:
            print("⚠️  Sin datos de cobertura")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Box plot comparativo
        data_to_plot = [
            df['baseline_coverage'].dropna(),
            df['valid_coverage'].dropna()
        ]
        
        ax1.boxplot(data_to_plot, labels=['T_base', 'T_valid'])
        ax1.set_ylabel('Line Coverage (%)')
        ax1.set_title('Coverage Distribution')
        ax1.grid(True, alpha=0.3)
        
        # Scatter plot (mejora individual)
        ax2.scatter(df['baseline_coverage'], df['valid_coverage'], alpha=0.6)
        
        # Línea y=x (sin cambio)
        max_val = max(df['baseline_coverage'].max(), df['valid_coverage'].max())
        ax2.plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label='No change')
        
        ax2.set_xlabel('T_base Coverage (%)')
        ax2.set_ylabel('T_valid Coverage (%)')
        ax2.set_title('Coverage Improvement per Class')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'rq1_coverage_comparison.png')
        plt.close()
        
        print(f"✅ Guardado: {self.output_dir / 'rq1_coverage_comparison.png'}")
    
    def plot_mutation_comparison(self, df: pd.DataFrame):
        """RQ1: Gráfica de comparación de mutation score."""
        
        if df.empty or 'baseline_mutation' not in df.columns:
            print("⚠️  Sin datos de mutación")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Box plot
        data_to_plot = [
            df['baseline_mutation'].dropna(),
            df['valid_mutation'].dropna()
        ]
        
        ax1.boxplot(data_to_plot, labels=['T_base', 'T_valid'])
        ax1.set_ylabel('Mutation Score (%)')
        ax1.set_title('Mutation Score Distribution')
        ax1.grid(True, alpha=0.3)
        
        # Scatter plot
        ax2.scatter(df['baseline_mutation'], df['valid_mutation'], alpha=0.6)
        
        max_val = max(df['baseline_mutation'].max(), df['valid_mutation'].max())
        ax2.plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label='No change')
        
        ax2.set_xlabel('T_base Mutation Score (%)')
        ax2.set_ylabel('T_valid Mutation Score (%)')
        ax2.set_title('Mutation Score Improvement per Class')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'rq1_mutation_comparison.png')
        plt.close()
        
        print(f"✅ Guardado: {self.output_dir / 'rq1_mutation_comparison.png'}")
    
    def plot_readability_comparison(self, df: pd.DataFrame):
        """RQ2: Gráfica de comparación de legibilidad."""
        
        if df.empty or 'baseline_loc' not in df.columns:
            print("⚠️  Sin datos de legibilidad")
            return
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # LOC comparison
        x = np.arange(len(df))
        width = 0.35
        
        ax.bar(x - width/2, df['baseline_loc'], width, label='T_base', alpha=0.8)
        ax.bar(x + width/2, df['valid_loc'], width, label='T_valid', alpha=0.8)
        
        ax.set_xlabel('Class')
        ax.set_ylabel('Lines of Code')
        ax.set_title('RQ2: Test Size Comparison')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        # Rotar labels si son muchos
        if len(df) > 10:
            plt.xticks([])
        else:
            ax.set_xticks(x)
            ax.set_xticklabels(df['class'], rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'rq2_readability_comparison.png')
        plt.close()
        
        print(f"✅ Guardado: {self.output_dir / 'rq2_readability_comparison.png'}")
    
    def plot_efficiency_analysis(self, df: pd.DataFrame):
        """RQ3: Análisis de eficiencia/overhead."""
        
        if df.empty:
            print("⚠️  Sin datos de eficiencia")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Tiempo de refinamiento
        if 'refinement_time' in df.columns:
            ax1.hist(df['refinement_time'].dropna(), bins=20, alpha=0.7, edgecolor='black')
            ax1.set_xlabel('Refinement Time (s)')
            ax1.set_ylabel('Frequency')
            ax1.set_title('RQ3: LLM Refinement Time Distribution')
            ax1.grid(True, alpha=0.3)
        
        # Tokens usados
        if 'tokens_used' in df.columns:
            ax2.scatter(df['baseline_loc'], df['tokens_used'], alpha=0.6)
            ax2.set_xlabel('Test Size (LOC)')
            ax2.set_ylabel('Tokens Used')
            ax2.set_title('RQ3: Token Usage vs Test Size')
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'rq3_efficiency_analysis.png')
        plt.close()
        
        print(f"✅ Guardado: {self.output_dir / 'rq3_efficiency_analysis.png'}")
    
    def generate_summary_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Genera tabla resumen para el paper."""
        
        if df.empty:
            return pd.DataFrame()
        
        summary = {
            'Metric': [],
            'T_base Mean': [],
            'T_valid Mean': [],
            'Improvement (%)': [],
            'p-value': [],
            'Effect Size': []
        }
        
        metrics = [
            ('coverage', 'Line Coverage'),
            ('mutation', 'Mutation Score'),
            ('loc', 'Lines of Code')
        ]
        
        for metric_key, metric_name in metrics:
            baseline_col = f'baseline_{metric_key}'
            valid_col = f'valid_{metric_key}'
            
            if baseline_col not in df.columns or valid_col not in df.columns:
                continue
            
            baseline_vals = df[baseline_col].dropna()
            valid_vals = df[valid_col].dropna()
            
            if len(baseline_vals) == 0 or len(valid_vals) == 0:
                continue
            
            # Estadísticas
            baseline_mean = baseline_vals.mean()
            valid_mean = valid_vals.mean()
            improvement = ((valid_mean - baseline_mean) / baseline_mean * 100) if baseline_mean > 0 else 0
            
            # Test estadístico
            if len(baseline_vals) == len(valid_vals):
                _, p_value = stats.wilcoxon(baseline_vals, valid_vals)
            else:
                _, p_value = stats.mannwhitneyu(baseline_vals, valid_vals)
            
            # Effect size (Cohen's d)
            effect_size = (valid_mean - baseline_mean) / np.sqrt((baseline_vals.std()**2 + valid_vals.std()**2) / 2)
            
            summary['Metric'].append(metric_name)
            summary['T_base Mean'].append(f"{baseline_mean:.2f}")
            summary['T_valid Mean'].append(f"{valid_mean:.2f}")
            summary['Improvement (%)'].append(f"{improvement:+.2f}")
            summary['p-value'].append(f"{p_value:.4f}")
            summary['Effect Size'].append(f"{effect_size:.2f}")
        
        return pd.DataFrame(summary)
    
    def analyze_success_failure_cases(self, df: pd.DataFrame):
        """Análisis de casos de éxito y fracaso."""
        
        if df.empty:
            return
        
        print("\n" + "="*80)
        print("ANÁLISIS DE CASOS")
        print("="*80)
        
        # Mejoras significativas
        df['cov_improvement'] = df['valid_coverage'] - df['baseline_coverage']
        df['mut_improvement'] = df['valid_mutation'] - df['baseline_mutation']
        
        # Top mejoras
        top_improvements = df.nlargest(5, 'mut_improvement')
        
        print("\n🏆 TOP 5 MEJORAS (Mutation Score):")
        for _, row in top_improvements.iterrows():
            print(f"  {row['class']}: {row['baseline_mutation']:.1f}% → {row['valid_mutation']:.1f}% "
                  f"(+{row['mut_improvement']:.1f}%)")
        
        # Casos sin mejora o empeorados
        no_improvement = df[df['mut_improvement'] <= 0]
        if not no_improvement.empty:
            print(f"\n⚠️  CASOS SIN MEJORA: {len(no_improvement)}")
            for _, row in no_improvement.head(5).iterrows():
                print(f"  {row['class']}: {row['baseline_mutation']:.1f}% → {row['valid_mutation']:.1f}%")


def main():
    """
    FASE 5: Análisis y Visualización Final
    """
    
    print("="*80)
    print("FASE 5: ANÁLISIS Y VISUALIZACIÓN")
    print("="*80)
    print()
    
    analyzer = ResultsAnalyzer(Path("figures"))
    
    # Cargar datos
    print("📂 Cargando resultados...")
    data = analyzer.load_data()
    
    if not data.get('baseline') or not data.get('valid'):
        print("❌ Faltan datos de fases anteriores")
        return 1
    
    # Crear DataFrame
    df = analyzer.create_comparison_dataframe(data)
    
    if df.empty:
        print("⚠️  No hay datos pareados para comparar")
        print("   Esto es normal si:")
        print("   - El LLM no está conectado (Fase 2)")
        print("   - Los tests no compilaron (Fase 3)")
        print("   - Estás probando el pipeline por primera vez")
        print("\n✅ Fase 5 completada (sin datos para analizar)")
        return 0  # No es un error, solo no hay datos
    
    print(f"✅ {len(df)} clases con datos completos\n")
    
    # Generar gráficas
    print("📊 Generando visualizaciones...\n")
    
    analyzer.plot_coverage_comparison(df)
    analyzer.plot_mutation_comparison(df)
    analyzer.plot_readability_comparison(df)
    analyzer.plot_efficiency_analysis(df)
    
    # Generar tabla resumen
    print("\n📋 Generando tabla resumen...\n")
    summary_table = analyzer.generate_summary_table(df)
    
    if not summary_table.empty:
        print(summary_table.to_string(index=False))
        
        # Guardar tabla
        summary_table.to_csv(analyzer.output_dir / 'summary_table.csv', index=False)
        summary_table.to_latex(analyzer.output_dir / 'summary_table.tex', index=False)
        print(f"\n✅ Tabla guardada en: {analyzer.output_dir / 'summary_table.csv'}")
        print(f"✅ LaTeX guardado en: {analyzer.output_dir / 'summary_table.tex'}")
    
    # Análisis cualitativo
    analyzer.analyze_success_failure_cases(df)
    
    # Guardar DataFrame completo
    df.to_csv(analyzer.output_dir / 'complete_results.csv', index=False)
    
    print("\n" + "="*80)
    print("COMPLETADO")
    print("="*80)
    print(f"\n📁 Todos los resultados en: {analyzer.output_dir}/")
    print("   - Gráficas PNG (alta resolución)")
    print("   - Tabla CSV")
    print("   - Tabla LaTeX")
    print("\n✅ Listo para tu tesis/paper!")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
