#!/bin/bash
# Quick daily sync script - exports today's VNPay/VNPayQR orders and imports to B4B

set -e

# Default payment methods
PAYMENT_METHODS="${PAYMENT_METHODS:-VNPay VNPayQR}"

# Run the sync script
python3 sync-odoo-to-b4b.py \
    --payment-methods $PAYMENT_METHODS \
    "$@"
