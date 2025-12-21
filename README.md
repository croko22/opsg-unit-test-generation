# Automated Test Generation Pipeline using LLMs and GSPO

## Overview
This repository contains the source code and experimental framework for the Master's Thesis focused on automated software test generation. The project implements a hybrid pipeline that combines genetic algorithms (EvoSuite) with Large Language Models (LLM) and Reinforcement Learning (GSPO) to generate high-quality, maintainable unit tests.

The system aims to optimize multiple objectives simultaneously, including code coverage, mutation score, and maintainability metrics (readability, complexity, and test smells).

## Requirements
- **Python**: 3.8 or higher
- **Java**: JDK 8 (required for EvoSuite)
- **Cuda**: GPU with CUDA support recommended for LLM inference components.

## Configuration
The system is configurable via `config.yml`. Key parameters include:
- **Paths**: Directories for SF110 benchmarks and tools.
- **LLM**: Model selection (e.g., CodeLlama) and LoRA parameters.
- **GSPO**: Hyperparameters for the Generative Self-Play Optimization algorithm.
- **Reward**: Weights for the multi-objective reward function.

## Usage
The pipeline is managed by `scripts/pipeline/run_pipeline.py` and can be executed entirely or in distinct phases.

### Full Pipeline Execution
To run the complete workflow from baseline generation to evaluation:
```bash
python3 scripts/pipeline/run_pipeline.py --full
```

### Phased Execution
The pipeline allows for granular execution of specific stages:

**Phase 1: Baseline Generation**
Generates initial test suites using EvoSuite.
```bash
python3 scripts/pipeline/run_pipeline.py --phase 1
```

**Phase 2: LLM Refinement**
Iteratively improves tests using the LLM and RL agent.
```bash
python3 scripts/pipeline/run_pipeline.py --phase 2
```

**Phase 3: Verification**
Validates compilation and execution of generated tests.
```bash
python3 scripts/pipeline/run_pipeline.py --phase 3
```

**Phase 4: Evaluation**
Calculates final metrics and generates reports.
```bash
python3 scripts/pipeline/run_pipeline.py --phase 4
```

### Testing
To test the pipeline on a limited subset of classes (fast run):
```bash
python3 scripts/pipeline/run_pipeline.py --limit 5
```

## Documentation
- **Scripts**: located in `scripts/`, containing logic for pipeline orchestration, metrics calculation, and plotting.
- **Data**: The `data/` directory should contain the SF110 benchmark subjects.
- **Output**: Results, including generated tests and metric reports, are stored in the `evaluation_results/` and `figures/` directories.
