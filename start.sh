#!/bin/bash

# Referral Outreach App Startup Script

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Referral Outreach App...${NC}"

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}Error: app.py not found. Please run this script from the project directory.${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade dependencies
echo -e "${GREEN}Checking dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check for required files
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Please configure your API keys.${NC}"
fi

if [ ! -f "credentials.json" ]; then
    echo -e "${YELLOW}Warning: credentials.json not found. Gmail authentication may fail.${NC}"
    echo -e "${YELLOW}Please download OAuth credentials from Google Cloud Console.${NC}"
fi

# Create data directory if it doesn't exist
mkdir -p data

# Start the app
echo -e "${GREEN}Starting Streamlit app...${NC}"
echo -e "${GREEN}App will open in your browser at http://localhost:8501${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the app${NC}"
echo ""

streamlit run app.py
