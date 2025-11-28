#!/bin/bash
set -e

echo "================================================"
echo "Bill Extraction Datathon - Setup Script"
echo "================================================"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}[1/8] Checking Python...${NC}"
python3 --version
echo -e "${GREEN}✓ Python found${NC}"

echo -e "${YELLOW}[2/8] Creating virtual environment...${NC}"
python3 -m venv venv
echo -e "${GREEN}✓ Virtual environment created${NC}"

echo -e "${YELLOW}[3/8] Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

echo -e "${YELLOW}[4/8] Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"

echo -e "${YELLOW}[5/8] Installing dependencies...${NC}"
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo -e "${YELLOW}[6/8] Creating directories...${NC}"
mkdir -p src tests docs logs
echo -e "${GREEN}✓ Directories created${NC}"

echo -e "${YELLOW}[7/8] Setting up .env...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠ Created .env - add your GOOGLE_API_KEY${NC}"
else
    echo -e "${GREEN}✓ .env exists${NC}"
fi

echo -e "${GREEN}✓ Setup complete!${NC}"
echo ""
echo "Next: source venv/bin/activate && python app.py"
