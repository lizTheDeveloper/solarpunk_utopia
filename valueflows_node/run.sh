#!/bin/bash
# ValueFlows Node - Quick Start Script

echo "🌱 ValueFlows Node - Quick Start"
echo "================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Initialize database
echo "Initializing database..."
python -c "from app.database import initialize_database; initialize_database()"

# Start backend
echo ""
echo "✓ Setup complete!"
echo ""
echo "Starting FastAPI backend on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""
echo "To start frontend:"
echo "  cd frontend"
echo "  npm install"
echo "  npm run dev"
echo ""

python app/main.py
