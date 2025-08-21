#!/bin/bash
# Docker Cross-Platform Testing Report Generator
# Generates detailed reports from Docker testing runs

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Report file paths
REPORTS_DIR="$PROJECT_ROOT/docker/reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$REPORTS_DIR/docker_test_report_$TIMESTAMP.md"

# Create reports directory
mkdir -p "$REPORTS_DIR"

print_usage() {
    echo -e "${BLUE}🐳 Docker Testing Report Generator${NC}"
    echo -e "${BLUE}==================================${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --full                    Generate full test report"
    echo "  --summary                 Generate summary report only"
    echo "  --platform [linux|windows|all]  Test specific platform"
    echo "  --output FILE             Custom output file"
    echo "  --json                    Output in JSON format"
    echo ""
    echo "Examples:"
    echo "  $0 --full                 # Full cross-platform report"
    echo "  $0 --platform linux      # Linux-only report"
    echo "  $0 --json --output test.json  # JSON output"
}

# Function to get system information
get_system_info() {
    echo "## System Information" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "| Component | Version |" >> "$REPORT_FILE"
    echo "|-----------|---------|" >> "$REPORT_FILE"
    echo "| Docker | $(docker --version | cut -d' ' -f3 | cut -d',' -f1) |" >> "$REPORT_FILE"
    echo "| Docker Compose | $(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1) |" >> "$REPORT_FILE"
    echo "| Host OS | $(uname -s) $(uname -r) |" >> "$REPORT_FILE"
    echo "| Host Arch | $(uname -m) |" >> "$REPORT_FILE"
    echo "| Date | $(date) |" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

# Function to test Linux platform
test_linux_platform() {
    echo -e "${GREEN}🐧 Testing Linux Platform${NC}"

    echo "## Linux Platform Test Results" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    local start_time=$(date +%s)
    local temp_log="/tmp/catzilla_linux_test.log"
    local exit_code=0

    cd "$PROJECT_ROOT"

    # Run Linux tests and capture output
    if docker-compose -f docker/docker-compose.yml run --rm catzilla-linux > "$temp_log" 2>&1; then
        echo "✅ **PASSED** - Linux tests completed successfully" >> "$REPORT_FILE"
        exit_code=0
    else
        echo "❌ **FAILED** - Linux tests failed" >> "$REPORT_FILE"
        exit_code=1
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo "" >> "$REPORT_FILE"
    echo "**Test Duration:** ${duration}s" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "### Test Output" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    cat "$temp_log" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    # Cleanup
    rm -f "$temp_log"

    return $exit_code
}

# Function to test Windows platform
test_windows_platform() {
    echo -e "${GREEN}🪟 Testing Windows Platform${NC}"

    echo "## Windows Platform Test Results" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    local start_time=$(date +%s)
    local temp_log="/tmp/catzilla_windows_test.log"
    local exit_code=0

    cd "$PROJECT_ROOT"

    # Run Windows tests and capture output
    if docker-compose -f docker/docker-compose.yml run --rm catzilla-windows > "$temp_log" 2>&1; then
        echo "✅ **PASSED** - Windows tests completed successfully" >> "$REPORT_FILE"
        exit_code=0
    else
        echo "❌ **FAILED** - Windows tests failed" >> "$REPORT_FILE"
        exit_code=1
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo "" >> "$REPORT_FILE"
    echo "**Test Duration:** ${duration}s" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "### Test Output" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    cat "$temp_log" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    # Cleanup
    rm -f "$temp_log"

    return $exit_code
}

# Function to get Docker image information
get_docker_images_info() {
    echo "## Docker Images Information" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    echo "| Image | Size | Created |" >> "$REPORT_FILE"
    echo "|-------|------|---------|" >> "$REPORT_FILE"

    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}" | grep catzilla | while read line; do
        echo "| $line |" | sed 's/\t/ | /g' >> "$REPORT_FILE"
    done

    echo "" >> "$REPORT_FILE"
}

# Function to generate performance metrics
get_performance_metrics() {
    echo "## Performance Metrics" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    # Get container resource usage
    echo "### Resource Usage" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "| Container | CPU % | Memory Usage | Memory % |" >> "$REPORT_FILE"
    echo "|-----------|-------|--------------|----------|" >> "$REPORT_FILE"

    # This would need to be run during active testing
    echo "| catzilla-linux | N/A | N/A | N/A |" >> "$REPORT_FILE"
    echo "| catzilla-windows | N/A | N/A | N/A |" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "*Note: Resource usage metrics require active containers*" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

# Function to generate summary
generate_summary() {
    local linux_result=$1
    local windows_result=$2

    echo "# Catzilla Docker Cross-Platform Test Report" > "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "**Generated:** $(date)" >> "$REPORT_FILE"
    echo "**Test Type:** Cross-Platform Docker Testing" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    echo "## Test Summary" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "| Platform | Result | Duration |" >> "$REPORT_FILE"
    echo "|----------|--------|----------|" >> "$REPORT_FILE"

    if [ "$linux_result" -eq 0 ]; then
        echo "| Linux (Ubuntu 22.04) | ✅ PASSED | ${LINUX_DURATION:-N/A}s |" >> "$REPORT_FILE"
    else
        echo "| Linux (Ubuntu 22.04) | ❌ FAILED | ${LINUX_DURATION:-N/A}s |" >> "$REPORT_FILE"
    fi

    if [ "$windows_result" -eq 0 ]; then
        echo "| Windows (Server 2022) | ✅ PASSED | ${WINDOWS_DURATION:-N/A}s |" >> "$REPORT_FILE"
    else
        echo "| Windows (Server 2022) | ❌ FAILED | ${WINDOWS_DURATION:-N/A}s |" >> "$REPORT_FILE"
    fi

    echo "" >> "$REPORT_FILE"

    local total_tests=0
    local passed_tests=0

    if [ "$PLATFORM" = "all" ] || [ "$PLATFORM" = "linux" ]; then
        total_tests=$((total_tests + 1))
        if [ "$linux_result" -eq 0 ]; then
            passed_tests=$((passed_tests + 1))
        fi
    fi

    if [ "$PLATFORM" = "all" ] || [ "$PLATFORM" = "windows" ]; then
        total_tests=$((total_tests + 1))
        if [ "$windows_result" -eq 0 ]; then
            passed_tests=$((passed_tests + 1))
        fi
    fi

    echo "**Overall Result:** $passed_tests/$total_tests platforms passed" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

# Default values
FULL_REPORT=false
SUMMARY_ONLY=false
PLATFORM="all"
OUTPUT_FORMAT="markdown"
JSON_OUTPUT=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            FULL_REPORT=true
            shift
            ;;
        --summary)
            SUMMARY_ONLY=true
            shift
            ;;
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --output)
            REPORT_FILE="$2"
            shift 2
            ;;
        --json)
            JSON_OUTPUT=true
            OUTPUT_FORMAT="json"
            REPORT_FILE="${REPORT_FILE%.md}.json"
            shift
            ;;
        --help|-h)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Main execution
echo -e "${BLUE}🐳 Generating Docker Cross-Platform Test Report${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

cd "$PROJECT_ROOT"

# Initialize results
linux_result=0
windows_result=0

# Generate report header
if [ "$JSON_OUTPUT" = false ]; then
    echo -e "${YELLOW}📝 Creating report: $REPORT_FILE${NC}"
    generate_summary 0 0  # Initial summary
    get_system_info
    get_docker_images_info
fi

# Run tests based on platform
case "$PLATFORM" in
    "linux")
        test_linux_platform
        linux_result=$?
        ;;
    "windows")
        test_windows_platform
        windows_result=$?
        ;;
    "all")
        test_linux_platform
        linux_result=$?
        test_windows_platform
        windows_result=$?
        ;;
    *)
        echo -e "${RED}❌ Unknown platform: $PLATFORM${NC}"
        exit 1
        ;;
esac

# Generate final summary
if [ "$JSON_OUTPUT" = false ]; then
    if [ "$FULL_REPORT" = true ]; then
        get_performance_metrics
    fi

    # Update summary at the top
    generate_summary $linux_result $windows_result
    get_system_info
    get_docker_images_info

    echo -e "${GREEN}✅ Report generated: $REPORT_FILE${NC}"
else
    # Generate JSON report
    cat > "$REPORT_FILE" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "test_type": "cross_platform_docker",
  "platform": "$PLATFORM",
  "results": {
    "linux": {
      "result": $([ $linux_result -eq 0 ] && echo "\"passed\"" || echo "\"failed\""),
      "exit_code": $linux_result
    },
    "windows": {
      "result": $([ $windows_result -eq 0 ] && echo "\"passed\"" || echo "\"failed\""),
      "exit_code": $windows_result
    }
  },
  "summary": {
    "total_platforms": $([ "$PLATFORM" = "all" ] && echo "2" || echo "1"),
    "passed_platforms": $(([ $linux_result -eq 0 ] && [ "$PLATFORM" != "windows" ] && echo -n "1" || echo -n "0") + ([ $windows_result -eq 0 ] && [ "$PLATFORM" != "linux" ] && echo " + 1" || echo "")),
    "overall_result": $([ $((linux_result + windows_result)) -eq 0 ] && echo "\"passed\"" || echo "\"failed\"")
  }
}
EOF
    echo -e "${GREEN}✅ JSON report generated: $REPORT_FILE${NC}"
fi

# Display final status
echo ""
if [ $((linux_result + windows_result)) -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
