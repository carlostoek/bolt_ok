#!/bin/bash
# 🛡️ DIANA BOT PROTECTION TESTING SCRIPT
# Easy-to-use wrapper for running the complete protection test suite

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Banner
echo -e "${CYAN}"
echo "🛡️ ============================================================"
echo "🛡️ DIANA BOT TESTING PROTECTION NETWORK"
echo "🛡️ ============================================================"
echo -e "${NC}"

# Function to print usage
print_usage() {
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 [COMMAND] [OPTIONS]"
    echo ""
    echo -e "${YELLOW}Commands:${NC}"
    echo "  all         Run complete protection test suite (default)"
    echo "  quick       Run quick smoke test only"
    echo "  mvp         Run MVP baseline protection tests only"
    echo "  cinema      Run cinema architecture tests only" 
    echo "  journey     Run user journey & archetype tests only"
    echo "  performance Run performance & scalability tests only"
    echo "  coverage    Run all tests with coverage report"
    echo "  help        Show this help message"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  --fail-fast Stop on first critical failure"
    echo "  --verbose   Show detailed output"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0                    # Run all protection tests"
    echo "  $0 quick              # Quick environment check"
    echo "  $0 mvp --fail-fast    # MVP tests, stop on failure"
    echo "  $0 coverage           # Full tests with coverage"
}

# Function to check environment
check_environment() {
    echo -e "${BLUE}🔍 Checking test environment...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 not found!${NC}"
        exit 1
    fi
    
    # Check pytest
    if ! python3 -c "import pytest" 2>/dev/null; then
        echo -e "${RED}❌ pytest not installed!${NC}"
        echo "Install with: pip install pytest pytest-asyncio"
        exit 1
    fi
    
    # Check project structure
    if [[ ! -d "tests/protection" ]]; then
        echo -e "${RED}❌ Protection tests directory not found!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Environment check passed!${NC}"
}

# Function to run tests with proper logging
run_test_command() {
    local cmd="$1"
    local description="$2"
    
    echo -e "${BLUE}🔄 $description${NC}"
    echo "Command: $cmd"
    echo ""
    
    # Create logs directory
    mkdir -p logs
    
    # Run command with logging
    if eval "$cmd" 2>&1 | tee "logs/test_$(date +%Y%m%d_%H%M%S).log"; then
        echo -e "${GREEN}✅ $description completed successfully!${NC}"
        return 0
    else
        echo -e "${RED}❌ $description failed!${NC}"
        return 1
    fi
}

# Parse command line arguments
COMMAND="${1:-all}"
shift || true  # Remove first argument, ignore error if no arguments

# Parse options
FAIL_FAST=""
VERBOSE=""
COVERAGE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --fail-fast)
            FAIL_FAST="--fail-fast"
            shift
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Main execution
case $COMMAND in
    all)
        check_environment
        echo -e "${PURPLE}🛡️ Running COMPLETE protection test suite...${NC}"
        run_test_command "python3 scripts/run_protection_tests.py $FAIL_FAST $VERBOSE" "Complete Protection Test Suite"
        ;;
        
    quick)
        check_environment
        echo -e "${PURPLE}🚀 Running QUICK smoke test...${NC}"
        run_test_command "python3 scripts/run_protection_tests.py --quick $VERBOSE" "Quick Smoke Test"
        ;;
        
    mvp)
        check_environment
        echo -e "${PURPLE}🛡️ Running MVP baseline protection tests...${NC}"
        run_test_command "python3 scripts/run_protection_tests.py --suite MVP_Baseline_Protection $FAIL_FAST $VERBOSE" "MVP Baseline Protection Tests"
        ;;
        
    cinema)
        check_environment
        echo -e "${PURPLE}🎬 Running cinema architecture tests...${NC}"
        run_test_command "python3 scripts/run_protection_tests.py --suite Cinema_Architecture_Integration $FAIL_FAST $VERBOSE" "Cinema Architecture Integration Tests"
        ;;
        
    journey)
        check_environment
        echo -e "${PURPLE}🎭 Running user journey & archetype tests...${NC}"
        run_test_command "python3 scripts/run_protection_tests.py --suite User_Journey_Archetypes $FAIL_FAST $VERBOSE" "User Journey & Archetype Tests"
        ;;
        
    performance)
        check_environment
        echo -e "${PURPLE}⚡ Running performance & scalability tests...${NC}"
        run_test_command "python3 scripts/run_protection_tests.py --suite Performance_Scalability $FAIL_FAST $VERBOSE" "Performance & Scalability Tests"
        ;;
        
    coverage)
        check_environment
        echo -e "${PURPLE}📊 Running ALL tests with coverage report...${NC}"
        run_test_command "python3 scripts/run_protection_tests.py --coverage $FAIL_FAST $VERBOSE" "Complete Test Suite with Coverage"
        ;;
        
    help)
        print_usage
        exit 0
        ;;
        
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        print_usage
        exit 1
        ;;
esac

# Final status
if [[ $? -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}🎉 ============================================================${NC}"
    echo -e "${GREEN}🛡️ DIANA BOT PROTECTION TESTING COMPLETED SUCCESSFULLY!${NC}"
    echo -e "${GREEN}🛡️ All critical systems are protected and operational!${NC}"
    echo -e "${GREEN}🎉 ============================================================${NC}"
else
    echo ""
    echo -e "${RED}🚨 ============================================================${NC}"
    echo -e "${RED}🛡️ DIANA BOT PROTECTION TESTING FAILED!${NC}"
    echo -e "${RED}⚠️  Critical protection failures detected!${NC}"
    echo -e "${RED}🚨 ============================================================${NC}"
    exit 1
fi