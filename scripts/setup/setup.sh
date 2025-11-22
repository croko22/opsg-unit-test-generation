#!/bin/bash

# Quick setup script for GSPO Unit Test Generation

echo "========================================="
echo "GSPO-UTG Setup Script"
echo "========================================="

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "Python 3 not found!"; exit 1; }

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "========================================="
echo "Python dependencies installed!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Install Defects4J:"
echo "   git clone https://github.com/rjust/defects4j.git /path/to/defects4j"
echo "   cd /path/to/defects4j && ./init.sh"
echo ""
echo "2. Download EvoSuite:"
echo "   wget https://github.com/EvoSuite/evosuite/releases/download/v1.2.0/evosuite-master-1.2.0.jar"
echo ""
echo "3. Configure config.yml with your paths"
echo ""
echo "4. Run experiment:"
echo "   source venv/bin/activate"
echo "   python experiments/run_experiment.py --config config.yml"
echo ""
echo "========================================="
