#!/bin/bash
# CI Test Runner - Fast tests for continuous integration
# Runs unit and integration tests with mocks for quick feedback

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Running CI-appropriate tests (unit + integration with mocks)${NC}"
echo "=================================================================="

# Check if we're in the project root
if [[ ! -f "pytest.ini" ]]; then
    echo -e "${RED}❌ Error: Must run from project root (pytest.ini not found)${NC}"
    exit 1
fi

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]] && [[ ! -f "prt_env/bin/python" ]]; then
    echo -e "${RED}❌ Error: Virtual environment not activated. Run 'source init.sh' first${NC}"
    exit 1
fi

# Use the virtual environment python if available
if [[ -f "prt_env/bin/python" ]]; then
    PYTHON_CMD="./prt_env/bin/python"
    PYTEST_CMD="./prt_env/bin/pytest"
else
    PYTHON_CMD="python"
    PYTEST_CMD="pytest"
fi

echo -e "${BLUE}📋 Test configuration:${NC}"
echo "   Python: $PYTHON_CMD"
echo "   Pytest: $PYTEST_CMD"
echo "   Markers: unit + integration (mocked)"
echo "   Timeout: 120 seconds"
echo "   Coverage: Enabled"
echo ""

# Run fast CI tests
echo -e "${YELLOW}🧪 Running unit and integration tests...${NC}"
$PYTEST_CMD \
    -m "unit or integration" \
    --timeout=120 \
    --tb=short \
    -v \
    tests/

EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}✅ All CI tests passed successfully!${NC}"
    echo -e "${GREEN}   Ready for deployment${NC}"
else
    echo ""
    echo -e "${RED}❌ Some CI tests failed (exit code: $EXIT_CODE)${NC}"
    echo -e "${RED}   Review failures before merging${NC}"
fi

exit $EXIT_CODE