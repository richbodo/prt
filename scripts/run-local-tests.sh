#!/bin/bash
# Local Test Runner - Full test suite including LLM contract tests
# Detects Ollama availability for comprehensive testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Running full local test suite${NC}"
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

# Check Ollama availability
OLLAMA_AVAILABLE=false
if command -v ollama &> /dev/null; then
    if ollama list &> /dev/null; then
        # Check if any models are available
        MODEL_COUNT=$(ollama list | grep -c ":" || true)
        if [[ $MODEL_COUNT -gt 0 ]]; then
            OLLAMA_AVAILABLE=true
        fi
    fi
fi

echo -e "${BLUE}📋 Test configuration:${NC}"
echo "   Python: $PYTHON_CMD"
echo "   Pytest: $PYTEST_CMD"
echo "   Ollama available: $OLLAMA_AVAILABLE"

if [[ "$OLLAMA_AVAILABLE" == "true" ]]; then
    echo "   Test scope: Full suite (including LLM contract tests)"
    echo "   Timeout: 600 seconds (contract tests)"
    PYTEST_ARGS="--timeout=600"
else
    echo "   Test scope: Unit + Integration (Ollama not available)"
    echo "   Timeout: 120 seconds"
    echo -e "${YELLOW}   ⚠️  Skipping LLM contract tests (install Ollama for full coverage)${NC}"
    PYTEST_ARGS="-m 'unit or integration' --timeout=120"
fi

echo ""

# Run the test suite
if [[ "$OLLAMA_AVAILABLE" == "true" ]]; then
    echo -e "${YELLOW}🔬 Running full test suite with LLM contract tests...${NC}"
else
    echo -e "${YELLOW}🧪 Running unit and integration tests...${NC}"
fi

$PYTEST_CMD \
    $PYTEST_ARGS \
    --tb=short \
    -v \
    tests/

EXIT_CODE=$?

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
    if [[ "$OLLAMA_AVAILABLE" == "true" ]]; then
        echo -e "${GREEN}✅ All tests passed (including LLM contract tests)!${NC}"
        echo -e "${GREEN}   Full validation complete${NC}"
    else
        echo -e "${GREEN}✅ All available tests passed!${NC}"
        echo -e "${YELLOW}   Install Ollama for complete test coverage${NC}"
    fi
else
    echo -e "${RED}❌ Some tests failed (exit code: $EXIT_CODE)${NC}"
    if [[ "$OLLAMA_AVAILABLE" == "true" ]]; then
        echo -e "${RED}   Review LLM contract test failures${NC}"
    else
        echo -e "${RED}   Review unit/integration test failures${NC}"
    fi
fi

# Show Ollama setup instructions if not available
if [[ "$OLLAMA_AVAILABLE" == "false" ]]; then
    echo ""
    echo -e "${BLUE}💡 To run LLM contract tests:${NC}"
    echo "   1. Install Ollama: https://ollama.com/"
    echo "   2. Pull required model: ollama pull gpt-oss:20b"
    echo "   3. Re-run this script"
fi

exit $EXIT_CODE