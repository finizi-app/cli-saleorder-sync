#!/bin/bash
# Shell wrapper for syncing VNPay orders from Odoo
# This script provides a convenient interface to the Python sync scripts

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
DATE=""
DRY_RUN=false
VERBOSE=false
EXTRACT_ONLY=false
IMPORT_ONLY=false
INPUT_FILE=""
OUTPUT_FILE=""
PAYMENT_METHODS="VNPay VNPayQR Thẻ ATM"

# Print banner
print_banner() {
    echo -e "${BLUE}"
    cat << "BANNER"
╔════════════════════════════════════════════════════════════╗
║  Odoo VNPay Order Sync - POS Invoice Generator            ║
║  Extract VNPay, VNPayQR, Thẻ ATM orders and issue invoices ║
╚════════════════════════════════════════════════════════════╝
BANNER
    echo -e "${NC}"
}

# Print usage
print_usage() {
    cat << USAGE
Usage: $0 [OPTIONS]

Options:
    -d, --date DATE          Date to sync (YYYY-MM-DD format, default: today)
    -i, --input FILE         Input file (for --import-only)
    -o, --output FILE        Output file path
    -p, --payment-methods    Payment methods (default: VNPay VNPayQR Thẻ ATM)
    --extract-only           Only extract, skip invoice generation
    --import-only            Only import from file, skip extraction
    --dry-run                Validate without actual import
    -v, --verbose            Enable verbose output
    -h, --help               Show this help message

Environment Variables:
    ODOO_URL                 Odoo server URL (default: http://localhost:8069)
    ODOO_DB                  Database name (default: prod)
    ODOO_USERNAME            Username (default: admin)
    ODOO_PASSWORD            Password (default: admin)

Examples:
    # Sync today's orders
    $0

    # Sync for specific date
    $0 --date 2026-03-31

    # Dry run
    $0 --dry-run --verbose

    # Extract only
    $0 --extract-only

    # Import from existing file
    $0 --import-only --input orders.json

USAGE
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--date)
            DATE="$2"
            shift 2
            ;;
        -i|--input)
            INPUT_FILE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -p|--payment-methods)
            PAYMENT_METHODS="$2"
            shift 2
            ;;
        --extract-only)
            EXTRACT_ONLY=true
            shift
            ;;
        --import-only)
            IMPORT_ONLY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Validate arguments
if [[ "$EXTRACT_ONLY" == true && "$IMPORT_ONLY" == true ]]; then
    echo -e "${RED}Error: Cannot specify both --extract-only and --import-only${NC}"
    exit 1
fi

if [[ "$IMPORT_ONLY" == true && -z "$INPUT_FILE" ]]; then
    echo -e "${RED}Error: --input required when using --import-only${NC}"
    exit 1
fi

# Print banner
print_banner

# Build Python command
PYTHON_CMD="python3"

# Build sync command
SYNC_CMD="$PYTHON_CMD $SCRIPT_DIR/sync_vnpay_orders.py"

# Add arguments
if [[ -n "$DATE" ]]; then
    SYNC_CMD="$SYNC_CMD --date $DATE"
fi

if [[ -n "$OUTPUT_FILE" ]]; then
    SYNC_CMD="$SYNC_CMD --output $OUTPUT_FILE"
elif [[ -z "$INPUT_FILE" ]]; then
    # Default output file for extraction
    OUTPUT_FILE="orders-extracted.json"
    SYNC_CMD="$SYNC_CMD --output $OUTPUT_FILE"
fi

if [[ -n "$PAYMENT_METHODS" ]]; then
    SYNC_CMD="$SYNC_CMD --payment-methods $PAYMENT_METHODS"
fi

if [[ "$EXTRACT_ONLY" == true ]]; then
    SYNC_CMD="$SYNC_CMD --extract-only"
fi

if [[ "$IMPORT_ONLY" == true ]]; then
    SYNC_CMD="$SYNC_CMD --input $INPUT_FILE"
fi

if [[ "$DRY_RUN" == true ]]; then
    SYNC_CMD="$SYNC_CMD --dry-run"
fi

if [[ "$VERBOSE" == true ]]; then
    SYNC_CMD="$SYNC_CMD --verbose"
fi

# Change to script directory
cd "$SCRIPT_DIR"

# Print command if verbose
if [[ "$VERBOSE" == true ]]; then
    echo -e "${YELLOW}Running:${NC} $SYNC_CMD"
    echo
fi

# Execute command
if eval "$SYNC_CMD"; then
    echo
    echo -e "${GREEN}✓ Sync completed successfully!${NC}"

    # Show output files
    if [[ -f "$OUTPUT_FILE" ]]; then
        echo -e "${BLUE}📄 Output:${NC} $OUTPUT_FILE"
    fi

    if [[ -f "invoices-${OUTPUT_FILE##orders-}" ]]; then
        echo -e "${BLUE}📄 Invoices:${NC} invoices-${OUTPUT_FILE##orders-}"
    fi

    exit 0
else
    echo
    echo -e "${RED}✗ Sync failed!${NC}"
    exit 1
fi
