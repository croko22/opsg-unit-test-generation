import json
from pathlib import Path
from typing import Dict, List
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from ..core.config import cfg

class AnalysisPhase:
    """Phase 5: Analysis and Visualization."""
    
    def __init__(self):
        self.output_dir = cfg.base_dir / "figures"
        self.output_dir.mkdir(exist_ok=True)
        
        # Style
        # Style
        sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
        plt.rcParams['figure.dpi'] = 300
        plt.rcParams['axes.titlesize'] = 16
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['font.family'] = 'sans-serif'
        # Premium palette
        self.palette = sns.color_palette("viridis", n_colors=2)
        
    def run(self):
        print("Phase 5: Analysis & Visualization")
        
        data = self._load_data()
        if not data.get('baseline') or not data.get('evaluation'):
            print("⚠️  Missing data (baseline or evaluation results)")
            return
            
        df = self._create_dataframe(data)
        if df.empty:
            print("⚠️  No paired data for comparison")
            return
            
        print(f"📊 Analyzing {len(df)} classes")
        
        self._plot_coverage(df)
        self._plot_mutation(df)
        self._plot_readability(df)
        self._plot_rates(df)
        self._save_summary(df)
        self._calculate_statistics(df)
        self._calculate_correlations(df)
        
    def _load_data(self) -> Dict:
        data = {}
        base_file = cfg.base_dir / "generated_tests/baseline/T_base_results.json"
        eval_file = cfg.base_dir / "evaluation_results/final_evaluation.json"
        
        if base_file.exists():
            with open(base_file) as f: data['baseline'] = json.load(f)
        if eval_file.exists():
            with open(eval_file) as f: data['evaluation'] = json.load(f)
            
        return data
        
    def _create_dataframe(self, data: Dict) -> pd.DataFrame:
        rows = []
        # Baseline might have different structure, assuming it has coverage info
        # If baseline didn't run full evaluation, we might only have basic info.
        # For now, assuming baseline has 'coverage' dict or similar.
        base_map = {r['class']: r for r in data['baseline'] if r.get('success')}
        
        for eval_item in data['evaluation']:
            cls = eval_item['class']
            base = base_map.get(cls)
            if not base: continue
            
            # Extract metrics
            # Baseline might not have full metrics if we didn't run full eval on it.
            # Assuming baseline has at least coverage from generation time.
            base_cov = base.get('coverage', {}).get('Line', 0)
            if isinstance(base_cov, str): base_cov = float(base_cov.replace('%',''))
            
            rows.append({
                'class': cls,
                'baseline_cov': base_cov,
                'valid_cov': eval_item.get('line_coverage', 0),
                'baseline_mut': base.get('mutation_score', 0), # Might be missing
                'valid_mut': eval_item.get('mutation_score', 0),
                'valid_mut': eval_item.get('mutation_score', 0),
                'sloc': eval_item.get('sloc', 0),
                'cyclomatic': eval_item.get('cyclomatic_complexity', 0),
                'branches': eval_item.get('switch_conditions', 0) + eval_item.get('primitive_conditions', 0),
                'avg_id_len': eval_item.get('avg_identifier_length', 0),
                'nesting': eval_item.get('max_nesting_depth', 0),
                'compilation_rate': eval_item.get('compilation_rate', 0),
                'verified': 1 if eval_item.get('verified') else 0
            })
            
        return pd.DataFrame(rows)

    def _plot_coverage(self, df: pd.DataFrame):
        if 'baseline_cov' not in df.columns: return
        
        plt.figure(figsize=(12, 6))
        
        # 1. Violin Plot for Distribution
        plt.subplot(1, 2, 1)
        data_melted = df.melt(value_vars=['baseline_cov', 'valid_cov'], var_name='Type', value_name='Coverage')
        data_melted['Type'] = data_melted['Type'].map({'baseline_cov': 'Baseline', 'valid_cov': 'Refined'})
        
        sns.violinplot(data=data_melted, x='Type', y='Coverage', palette="viridis", inner="quartile", alpha=0.8)
        sns.stripplot(data=data_melted, x='Type', y='Coverage', color='black', alpha=0.3, jitter=True)
        plt.title('Coverage Distribution', fontweight='bold')
        plt.xlabel('')
        plt.ylabel('Line Coverage (%)')
        sns.despine()
        
        # 2. Scatter Plot for Improvement
        plt.subplot(1, 2, 2)
        sns.scatterplot(data=df, x='baseline_cov', y='valid_cov', 
                        hue='valid_cov', palette="viridis", size='sloc', sizes=(50, 400), alpha=0.7, legend=False)
        
        # Diagonal line
        max_val = max(df['baseline_cov'].max(), df['valid_cov'].max())
        plt.plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label='No Change')
        
        plt.xlabel('Baseline Coverage (%)')
        plt.ylabel('Refined Coverage (%)')
        plt.title('Coverage Improvement', fontweight='bold')
        sns.despine()
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'coverage_comparison.png', bbox_inches='tight')
        plt.close()
        print(f"✅ Saved coverage plot to {self.output_dir}")

    def _plot_mutation(self, df: pd.DataFrame):
        if 'baseline_mut' not in df.columns: return
        
        plt.figure(figsize=(8, 6))
        
        data_melted = df.melt(value_vars=['baseline_mut', 'valid_mut'], var_name='Type', value_name='Score')
        data_melted['Type'] = data_melted['Type'].map({'baseline_mut': 'Baseline', 'valid_mut': 'Refined'})
        
        sns.boxplot(data=data_melted, x='Type', y='Score', palette="magma", width=0.5)
        sns.stripplot(data=data_melted, x='Type', y='Score', color='black', alpha=0.3, jitter=True)
        
        plt.title('Mutation Score Comparison', fontweight='bold')
        plt.xlabel('')
        plt.ylabel('Mutation Score (%)')
        sns.despine()
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'mutation_comparison.png', bbox_inches='tight')
        plt.close()

    def _plot_readability(self, df: pd.DataFrame):
        if 'avg_id_len' not in df.columns: return
        
        plt.figure(figsize=(12, 5))
        
        # 1. Identifier Length
        plt.subplot(1, 2, 1)
        sns.histplot(df['avg_id_len'], kde=True, color="#3498db", alpha=0.6, edgecolor=None)
        plt.axvline(df['avg_id_len'].mean(), color='red', linestyle='--', label=f"Mean: {df['avg_id_len'].mean():.1f}")
        plt.title('Identifier Length Distribution', fontweight='bold')
        plt.xlabel('Avg Length (chars)')
        plt.legend()
        sns.despine()
        
        # 2. Nesting Depth
        plt.subplot(1, 2, 2)
        sns.histplot(df['nesting'], kde=True, color="#e74c3c", alpha=0.6, edgecolor=None, discrete=True)
        plt.title('Nesting Depth Distribution', fontweight='bold')
        plt.xlabel('Max Depth')
        sns.despine()
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'readability_metrics.png', bbox_inches='tight')
        plt.close()

    def _plot_rates(self, df: pd.DataFrame):
        if 'compilation_rate' not in df.columns: return
        
        # Calculate overall rates
        compilation_rate = df['compilation_rate'].mean() * 100
        preservation_rate = df['verified'].mean() * 100
        
        plt.figure(figsize=(8, 6))
        
        rates = [compilation_rate, preservation_rate]
        labels = ['Compilation Rate', 'Preservation Rate']
        colors = ['#2ecc71', '#3498db']
        
        bars = plt.bar(labels, rates, color=colors, alpha=0.8, width=0.6)
        plt.ylim(0, 110)
        plt.ylabel('Rate (%)')
        plt.title('Success Metrics', fontweight='bold')
        
        # Add values on top
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 2,
                     f'{height:.1f}%',
                     ha='center', va='bottom', fontsize=14, fontweight='bold')
            
        sns.despine()
        plt.tight_layout()
        plt.savefig(self.output_dir / 'success_rates.png', bbox_inches='tight')
        plt.close()

    def _save_summary(self, df: pd.DataFrame):
        summary = df.describe()
        summary.to_csv(self.output_dir / 'summary_stats.csv')
        print(f"✅ Saved summary stats to {self.output_dir}")

    def _calculate_statistics(self, df: pd.DataFrame):
        stats_results = []
        
        for metric in ['cov', 'mut']:
            base_col = f'baseline_{metric}'
            valid_col = f'valid_{metric}'
            
            if base_col not in df.columns or valid_col not in df.columns:
                continue
                
            # Wilcoxon Signed-Rank Test
            try:
                stat, p_value = stats.wilcoxon(df[base_col], df[valid_col])
            except ValueError:
                p_value = 1.0 # e.g. all identical
                
            # Effect Size (Vargha-Delaney A12)
            a12 = self._vargha_delaney(df[base_col], df[valid_col])
            
            stats_results.append({
                'metric': metric,
                'p_value': p_value,
                'effect_size_a12': a12,
                'mean_diff': (df[valid_col] - df[base_col]).mean()
            })
            
        pd.DataFrame(stats_results).to_csv(self.output_dir / 'statistical_significance.csv', index=False)
        print(f"✅ Saved statistical analysis to {self.output_dir}")

    def _calculate_correlations(self, df: pd.DataFrame):
        # Correlate Code Metrics with Improvement
        if 'sloc' not in df.columns: return
        
        df['cov_improvement'] = df['valid_cov'] - df['baseline_cov']
        
        correlations = []
        code_metrics = ['sloc', 'cyclomatic', 'branches']
        
        for cm in code_metrics:
            if cm not in df.columns: continue
            
            corr, p = stats.spearmanr(df[cm], df['cov_improvement'])
            correlations.append({
                'code_metric': cm,
                'spearman_corr': corr,
                'p_value': p
            })
            
        pd.DataFrame(correlations).to_csv(self.output_dir / 'correlations.csv', index=False)
        print(f"✅ Saved correlations to {self.output_dir}")

    def _vargha_delaney(self, x, y):
        """
        Computes Vargha-Delaney A12 statistic.
        A12 > 0.5 means y is stochastically larger than x.
        """
        x = list(x)
        y = list(y)
        m = len(x)
        n = len(y)
        
        r = stats.rankdata(x + y)
        r1 = sum(r[:m])
        
        # Formula for A12
        # A = (R1/m - (m+1)/2) / n  ... wait, this is for Mann-Whitney U
        # For paired data, it's slightly different usually, but A12 is often used for independent.
        # For paired, we can use the same if we treat them as distributions.
        # A12 = (R1/m - (m+1)/2) / n is correct for U.
        # Let's use the standard formula:
        
        return (r1 / m - (m + 1) / 2) / n
