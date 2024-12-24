set -e
echo "🚀 Running some setup commands..."

echo "Creating virtual environment..."
python3 -m venv zapenv

echo "Downloading dependencies..."
pip install -r requirements.txt

echo "Installing repomix..."
npm install -g repomix

echo "Setup complete!"
