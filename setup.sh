#!/bin/bash

# Portfolio Rebalancer - Setup & Launch Script
# Run this to install dependencies and start the app

set -e  # Exit on error

echo "🚀 Portfolio Rebalancer Setup"
echo "=========================================="

# Check Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8 or later."
    exit 1
fi

echo "✅ Python3 found: $(python3 --version)"

# Navigate to project directory
cd "$(dirname "$0")"

echo ""
echo "📦 Installing dependencies..."

# Create virtual environment if needed (optional)
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created"
else
    source venv/bin/activate
    echo "✅ Using existing virtual environment"
fi

# Install requirements
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

echo ""
echo "🎯 Project Structure:"
ls -1 *.py *.md *.csv 2>/dev/null | sed 's/^/   /'

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting Streamlit app..."
echo "   → Opening http://localhost:8501"
echo ""
echo "💡 Tip: Use sample_source.csv and sample_target.csv for first run"
echo ""

streamlit run streamlit_app.py
