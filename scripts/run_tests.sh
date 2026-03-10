#!/bin/bash
# WebPDTool Test Runner
# Provides convenient shortcuts for running different test suites

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Change to project root
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)
print_info "Project root: $PROJECT_ROOT"

# Check if uv is available
if command -v uv &> /dev/null; then
    PYTHON_CMD="uv run python"
    PYTEST_CMD="uv run pytest"
    print_info "Using uv for Python execution"
else
    PYTHON_CMD="python3"
    PYTEST_CMD="pytest"
    print_warning "uv not found, using system python3"
fi

# Default options
PYTEST_OPTS="-v"
COVERAGE_OPTS=""
MARKERS=""

# Parse arguments
TEST_TARGET=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            echo "WebPDTool Test Runner"
            echo ""
            echo "Usage: $0 [OPTIONS] [TARGET]"
            echo ""
            echo "Options:"
            echo "  -c, --coverage          Generate coverage report"
            echo "  -f, --fast              Run only fast tests"
            echo "  -s, --slow              Include slow tests"
            echo "  -u, --unit              Run only unit tests"
            echo "  -i, --integration       Run only integration tests"
            echo "  -n, --no-hardware       Skip hardware tests (default)"
            echo "  -w, --with-hardware     Include hardware tests"
            echo "  -x, --stop-on-fail      Stop on first failure"
            echo "  -v, --verbose           Verbose output"
            echo "  -h, --help              Show this help"
            echo ""
            echo "Targets:"
            echo "  measurements            Run measurement validation tests"
            echo "  instruments             Run instrument driver tests"
            echo "  34970a                  Run 34970A instrument tests"
            echo "  model2306               Run MODEL2306 instrument tests"
            echo "  it6723c                 Run IT6723C instrument tests"
            echo "  2260b                   Run 2260B instrument tests"
            echo "  cmw100                  Run CMW100 instrument tests"
            echo "  mt8872a                 Run MT8872A instrument tests"
            echo "  all                     Run all tests (default)"
            echo ""
            echo "Examples:"
            echo "  $0                      Run all tests (fast, simulation only)"
            echo "  $0 -c measurements      Run measurements with coverage"
            echo "  $0 -f instruments       Run instrument tests (fast only)"
            echo "  $0 -u                   Run only unit tests"
            echo "  $0 -c -x -i             Run integration tests with coverage, stop on fail"
            exit 0
            ;;
        -c|--coverage)
            COVERAGE_OPTS="--cov=app --cov-report=html --cov-report=term"
            shift
            ;;
        -f|--fast)
            MARKERS="$MARKERS and fast"
            shift
            ;;
        -s|--slow)
            # Include slow tests (default is to skip them)
            shift
            ;;
        -u|--unit)
            if [ -z "$MARKERS" ]; then
                MARKERS="-m unit"
            else
                MARKERS="$MARKERS and unit"
            fi
            shift
            ;;
        -i|--integration)
            if [ -z "$MARKERS" ]; then
                MARKERS="-m integration"
            else
                MARKERS="$MARKERS and integration"
            fi
            shift
            ;;
        -n|--no-hardware)
            # Default behavior, skip hardware tests
            MARKERS="$MARKERS and not hardware"
            shift
            ;;
        -w|--with-hardware)
            # Include hardware tests
            HARDWARE_OPTS="--run-hardware"
            shift
            ;;
        -x|--stop-on-fail)
            PYTEST_OPTS="$PYTEST_OPTS -x"
            shift
            ;;
        -v|--verbose)
            PYTEST_OPTS="$PYTEST_OPTS -vv"
            shift
            ;;
        measurements)
            TEST_TARGET="tests/test_measurements_refactoring.py"
            shift
            ;;
        instruments)
            TEST_TARGET="tests/test_instruments_pytest_style.py"
            shift
            ;;
        34970a)
            MARKERS="-m instrument_34970a"
            shift
            ;;
        model2306)
            MARKERS="-m instrument_model2306"
            shift
            ;;
        it6723c)
            MARKERS="-m instrument_it6723c"
            shift
            ;;
        2260b)
            MARKERS="-m instrument_2260b"
            shift
            ;;
        cmw100)
            MARKERS="-m instrument_cmw100"
            shift
            ;;
        mt8872a)
            MARKERS="-m instrument_mt8872a"
            shift
            ;;
        all)
            TEST_TARGET=""
            shift
            ;;
        *)
            if [[ -f "$1" ]] || [[ -d "$1" ]]; then
                TEST_TARGET="$1"
            else
                print_error "Unknown option or target: $1"
                echo "Use -h or --help for usage information"
                exit 1
            fi
            shift
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="$PYTEST_CMD $PYTEST_OPTS"

# Add coverage if requested
if [ -n "$COVERAGE_OPTS" ]; then
    print_info "Coverage report will be generated"
    PYTEST_CMD="$PYTEST_CMD $COVERAGE_OPTS"
fi

# Add markers
if [ -n "$MARKERS" ]; then
    print_info "Filtering tests: $MARKERS"
    PYTEST_CMD="$PYTEST_CMD $MARKERS"
fi

# Add hardware options
if [ -n "$HARDWARE_OPTS" ]; then
    print_warning "Hardware tests will be included"
    PYTEST_CMD="$PYTEST_CMD $HARDWARE_OPTS"
else
    # Default: skip hardware tests
    PYTEST_CMD="$PYTEST_CMD -m not hardware"
fi

# Add target
if [ -n "$TEST_TARGET" ]; then
    PYTEST_CMD="$PYTEST_CMD $TEST_TARGET"
fi

# Print what we're running
echo ""
print_info "Running: $PYTEST_CMD"
echo ""

# Run tests
if eval $PYTEST_CMD; then
    echo ""
    print_success "All tests passed!"
    if [ -n "$COVERAGE_OPTS" ]; then
        print_info "Coverage report: htmlcov/index.html"
    fi
    exit 0
else
    echo ""
    print_error "Some tests failed"
    exit 1
fi
