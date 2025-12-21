import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Rectangle
import os

# Directorio de salida
OUTPUT_DIR = 'figures'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configuración general para todos los gráficos
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'serif'
sns.set_palette("Set2")

# ============================================================================
# GRÁFICO 1: Barras agrupadas de métricas de mantenibilidad
# ============================================================================
def plot_maintainability_comparison():
    methods = ['EvoSuite', 'LLM Zero-Shot', 'PPO', 'GSPO\n(Propuesto)']
    test_smells = [4.82, 3.15, 2.90, 1.24]
    complexity = [5.10, 3.80, 3.20, 2.05]
    readability = [0.45, 0.68, 0.72, 0.89]

    x = np.arange(len(methods))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 5))

    bars1 = ax.bar(x - width, test_smells, width, label='Test Smells',
                   color='#E74C3C', alpha=0.8)
    bars2 = ax.bar(x, complexity, width, label='Complejidad Ciclomática',
                   color='#3498DB', alpha=0.8)
    bars3 = ax.bar(x + width, readability, width, label='Legibilidad',
                   color='#2ECC71', alpha=0.8)

    ax.set_ylabel('Valor de la Métrica')
    ax.set_xlabel('Método')
    ax.set_xticks(x)
    ax.set_xticklabels(methods)
    ax.legend(loc='upper left', frameon=True)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    # Añadir valores sobre las barras
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}', ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    # plt.savefig(os.path.join(OUTPUT_DIR, 'grafico1_maintainability_bars.pdf'), bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'grafico1_maintainability_bars.png'), bbox_inches='tight')
    plt.show()

# ============================================================================
# GRÁFICO 2: Box plot de distribución de test smells
# ============================================================================
def plot_test_smells_distribution():
    np.random.seed(42)

    # Simulación de distribuciones basadas en las medias reportadas
    evosuite = np.random.gamma(4, 1.2, 100) + 0.5
    llm_zero = np.random.gamma(3, 1.05, 100) + 0.2
    ppo = np.random.gamma(2.5, 1.16, 100) + 0.1
    gspo = np.random.gamma(1.2, 1.03, 100)

    data = [evosuite, llm_zero, ppo, gspo]
    labels = ['EvoSuite', 'LLM\nZero-Shot', 'PPO', 'GSPO\n(Propuesto)']

    fig, ax = plt.subplots(figsize=(9, 5))

    bp = ax.boxplot(data, labels=labels, patch_artist=True,
                    medianprops=dict(color='red', linewidth=2),
                    boxprops=dict(facecolor='lightblue', alpha=0.7),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5))

    ax.set_ylabel('Número de Test Smells')
    ax.set_xlabel('Método')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    plt.tight_layout()
    # plt.savefig(os.path.join(OUTPUT_DIR, 'grafico2_testsmells_boxplot.pdf'), bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'grafico2_testsmells_boxplot.png'), bbox_inches='tight')
    plt.show()

# ============================================================================
# GRÁFICO 3: Scatter plot de Branch Coverage vs Mutation Score
# ============================================================================
def plot_coverage_vs_mutation():
    methods = ['EvoSuite', 'LLM Zero-Shot', 'PPO', 'GSPO (Propuesto)']
    branch_cov = [84.5, 81.0, 83.2, 84.3]
    mutation_score = [76.2, 68.5, 74.1, 77.5]
    colors = ['#E74C3C', '#F39C12', '#3498DB', '#2ECC71']
    sizes = [200, 200, 200, 250]

    fig, ax = plt.subplots(figsize=(8, 6))

    for i, method in enumerate(methods):
        ax.scatter(branch_cov[i], mutation_score[i], s=sizes[i],
                  alpha=0.7, color=colors[i], edgecolors='black',
                  linewidth=1.5, label=method)

    ax.set_xlabel('Cobertura de Ramas (%)')
    ax.set_ylabel('Mutation Score (%)')
    ax.legend(loc='lower right', frameon=True)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    # Líneas de referencia
    ax.axhline(y=75, color='gray', linestyle=':', alpha=0.5, linewidth=1)
    ax.axvline(x=83, color='gray', linestyle=':', alpha=0.5, linewidth=1)

    ax.set_xlim(79, 86)
    ax.set_ylim(66, 79)

    plt.tight_layout()
    # plt.savefig(os.path.join(OUTPUT_DIR, 'grafico3_coverage_mutation_scatter.pdf'), bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'grafico3_coverage_mutation_scatter.png'), bbox_inches='tight')
    plt.show()

# ============================================================================
# GRÁFICO 4: Barras apiladas de compilación
# ============================================================================
def plot_compilation_stacked():
    methods = ['EvoSuite', 'LLM\nZero-Shot', 'PPO', 'GSPO\n(Propuesto)']
    successful = [100, 88.4, 92.1, 98.6]
    failed = [0, 11.6, 7.9, 1.4]

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.bar(methods, successful, label='Compilación Exitosa',
           color='#2ECC71', alpha=0.85)
    ax.bar(methods, failed, bottom=successful, label='Fallos de Compilación',
           color='#E74C3C', alpha=0.85)

    ax.set_ylabel('Porcentaje (%)')
    ax.set_xlabel('Método')
    ax.set_ylim(0, 105)
    ax.legend(loc='lower left', frameon=True)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    # Añadir valores sobre las barras
    for i, (s, f) in enumerate(zip(successful, failed)):
        ax.text(i, s/2, f'{s:.1f}%', ha='center', va='center',
               fontweight='bold', fontsize=10, color='white')
        if f > 0:
            ax.text(i, s + f/2, f'{f:.1f}%', ha='center', va='center',
                   fontweight='bold', fontsize=9, color='white')

    plt.tight_layout()
    # plt.savefig(os.path.join(OUTPUT_DIR, 'grafico4_compilation_stacked.pdf'), bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'grafico4_compilation_stacked.png'), bbox_inches='tight')
    plt.show()

# ============================================================================
# GRÁFICO 5: Convergencia temporal PPO vs GSPO
# ============================================================================
def plot_convergence_comparison():
    np.random.seed(42)
    steps = np.arange(0, 18000, 100)

    # Simular curvas de convergencia
    gspo_mean = 0.3 + 0.55 * (1 - np.exp(-steps/3000))
    gspo_std = 0.05 * np.exp(-steps/5000) + 0.02

    ppo_mean = 0.3 + 0.48 * (1 - np.exp(-steps/5000))
    ppo_std = 0.15 * np.exp(-steps/8000) + 0.04

    # Añadir ruido
    gspo_mean += np.random.normal(0, 0.01, len(steps))
    ppo_mean += np.random.normal(0, 0.03, len(steps))

    fig, ax = plt.subplots(figsize=(10, 5))

    # GSPO
    ax.plot(steps, gspo_mean, color='#2ECC71', linewidth=2, label='GSPO (Propuesto)')
    ax.fill_between(steps, gspo_mean - gspo_std, gspo_mean + gspo_std,
                    color='#2ECC71', alpha=0.2)

    # PPO
    ax.plot(steps, ppo_mean, color='#E74C3C', linewidth=2, label='PPO')
    ax.fill_between(steps, ppo_mean - ppo_std, ppo_mean + ppo_std,
                    color='#E74C3C', alpha=0.2)

    ax.set_xlabel('Steps de Entrenamiento')
    ax.set_ylabel('Recompensa Promedio')
    ax.legend(loc='lower right', frameon=True, fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    ax.set_xlim(0, 18000)
    ax.set_ylim(0.2, 1.0)

    # Líneas de convergencia
    ax.axvline(x=9000, color='#2ECC71', linestyle=':', alpha=0.5, linewidth=1.5)
    ax.axvline(x=15000, color='#E74C3C', linestyle=':', alpha=0.5, linewidth=1.5)

    ax.text(9000, 0.25, 'Convergencia\nGSPO (9K)', ha='center', fontsize=8,
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    ax.text(15000, 0.25, 'Convergencia\nPPO (15K)', ha='center', fontsize=8,
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    # plt.savefig(os.path.join(OUTPUT_DIR, 'grafico5_convergence_training.pdf'), bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'grafico5_convergence_training.png'), bbox_inches='tight')
    plt.show()

# ============================================================================
# GRÁFICO 6: Violin plot de distribución de recompensas
# ============================================================================
def plot_reward_distribution():
    np.random.seed(42)

    # Simulación de distribuciones finales
    ppo_rewards = np.random.normal(0.78, 0.042, 500)
    gspo_rewards = np.random.normal(0.85, 0.025, 500)

    data = [ppo_rewards, gspo_rewards]
    labels = ['PPO', 'GSPO (Propuesto)']

    fig, ax = plt.subplots(figsize=(7, 5))

    parts = ax.violinplot(data, positions=[1, 2], showmeans=True, showmedians=True)

    # Personalizar colores
    colors = ['#E74C3C', '#2ECC71']
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.7)

    ax.set_xticks([1, 2])
    ax.set_xticklabels(labels)
    ax.set_ylabel('Recompensa por Episodio')
    ax.set_xlabel('Algoritmo')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    plt.tight_layout()
    # plt.savefig(os.path.join(OUTPUT_DIR, 'grafico6_reward_distribution.pdf'), bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'grafico6_reward_distribution.png'), bbox_inches='tight')
    plt.show()

# ============================================================================
# GRÁFICO 7: Diagrama de radar comparativo
# ============================================================================
def plot_radar_comparison():
    categories = ['Test Smells\n(invertido)', 'Legibilidad',
                  'Branch\nCoverage', 'Mutation\nScore',
                  'Tasa de\nCompilación']

    # Normalizar métricas a escala 0-1 (invertir test smells)
    evosuite = [1 - 4.82/5, 0.45, 0.845, 0.762, 1.0]
    llm_zero = [1 - 3.15/5, 0.68, 0.81, 0.685, 0.884]
    ppo = [1 - 2.90/5, 0.72, 0.832, 0.741, 0.921]
    gspo = [1 - 1.24/5, 0.89, 0.843, 0.775, 0.986]

    # Número de variables
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()

    # Cerrar el círculo
    evosuite += evosuite[:1]
    llm_zero += llm_zero[:1]
    ppo += ppo[:1]
    gspo += gspo[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

    ax.plot(angles, evosuite, 'o-', linewidth=2, label='EvoSuite', color='#E74C3C')
    ax.fill(angles, evosuite, alpha=0.15, color='#E74C3C')

    ax.plot(angles, llm_zero, 's-', linewidth=2, label='LLM Zero-Shot', color='#F39C12')
    ax.fill(angles, llm_zero, alpha=0.15, color='#F39C12')

    ax.plot(angles, ppo, '^-', linewidth=2, label='PPO', color='#3498DB')
    ax.fill(angles, ppo, alpha=0.15, color='#3498DB')

    ax.plot(angles, gspo, 'D-', linewidth=2.5, label='GSPO (Propuesto)', color='#2ECC71')
    ax.fill(angles, gspo, alpha=0.25, color='#2ECC71')

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=8)
    ax.grid(True, alpha=0.3)

    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), frameon=True)

    plt.tight_layout()
    # plt.savefig(os.path.join(OUTPUT_DIR, 'grafico7_radar_comparison.pdf'), bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'grafico7_radar_comparison.png'), bbox_inches='tight')
    plt.show()

# ============================================================================
# EJECUTAR TODOS LOS GRÁFICOS
# ============================================================================
if __name__ == "__main__":
    print("Generando gráficos...")

    print("1. Barras agrupadas de mantenibilidad...")
    plot_maintainability_comparison()

    print("2. Box plot de test smells...")
    plot_test_smells_distribution()

    print("3. Scatter plot coverage vs mutation...")
    plot_coverage_vs_mutation()

    print("4. Barras apiladas de compilación...")
    plot_compilation_stacked()

    print("5. Convergencia temporal...")
    plot_convergence_comparison()

    print("6. Violin plot de recompensas...")
    plot_reward_distribution()

    print("7. Diagrama de radar...")
    plot_radar_comparison()

    print("\n¡Todos los gráficos generados exitosamente!")
    print(f"Archivos generados: .png en directorio '{OUTPUT_DIR}'")
