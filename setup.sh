#!/bin/bash
# Setup script for Scalestack third-party modules repository

echo "🚀 Setting up Scalestack Third-Party Modules Repository"
echo "========================================================"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install Poetry first:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

echo "✅ Poetry is installed"

# Configure Poetry for Scalestack artifacts
echo "📦 Configuring Scalestack artifact repository..."
poetry source add --priority=supplemental scalestack https://artifacts.scalestack.me/api/packages/scalestack/pypi/simple/ 2>/dev/null || true

# Set environment variables for Scalestack authentication
echo ""
echo "🔐 Setting Scalestack authentication..."
export POETRY_HTTP_BASIC_SCALESTACK_USERNAME="buplex"
export POETRY_HTTP_BASIC_SCALESTACK_PASSWORD="jrh-bxq0aur6HDB8vjn"
echo "✅ Authentication configured"
echo ""

# Install dependencies
echo "📚 Installing dependencies..."
poetry install --no-root

# Check if AWS CDK is installed
if ! command -v cdk &> /dev/null; then
    echo ""
    echo "⚠️  AWS CDK is not installed. Installing globally..."
    npm install -g aws-cdk
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Create your team directory: mkdir modules_yourteam/"
echo "2. Add your first module: mkdir modules_yourteam/my_module/"
echo "3. Write your module code in: modules_yourteam/my_module/index.py"
echo "4. Create a PR to deploy to staging!"
echo ""
echo "📚 See DeveloperGuide.md for detailed instructions"