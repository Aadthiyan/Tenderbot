#!/bin/bash

# TenderBot Global - Tenant Factory Bootstrapper
# This script initializes a brand new, fully isolated TenderBot instance for a single company.

set -e

echo "============================================================"
echo "🚀 TENDERBOT AGENT FACTORY: NEW TENANT DEPLOYMENT"
echo "============================================================"

# 1. Prompt for Tenant Basics
read -p "Enter Target Company Name (e.g. 'Stark Industries'): " COMPANY_NAME
TENANT_ID=$(echo "$COMPANY_NAME" | tr '[:upper:]' '[:lower:]' | tr -d ' ' | tr -dc '[:alnum:]')

read -s -p "Enter Frontend Admin Password (to secure the dashboard): " APP_PASSWORD
echo ""

echo "------------------------------------------------------------"
echo "🔑 Enter External Credentials for $COMPANY_NAME:"
echo "------------------------------------------------------------"
read -p "TINYFISH_API_KEY (Leave blank to use global): " TF_KEY
read -p "COMPOSIO_API_KEY (Slack alerting): " COMPOSIO_KEY
read -p "SLACK_CHANNEL (e.g. #tender-bids): " SLACK_CHANNEL

# 2. Build the Isolated Environment File
ENV_FILE=".env.$TENANT_ID"
echo "Creating isolated environment at $ENV_FILE..."

# Copy base template
if [ -f ".env.example" ]; then
    cp .env.example "$ENV_FILE"
else
    touch "$ENV_FILE"
fi

# Append specific Tenant Configurations
echo "" >> "$ENV_FILE"
echo "# --- Isolated Tenant Configurations ($COMPANY_NAME) ---" >> "$ENV_FILE"
echo "TENANT_ID=$TENANT_ID" >> "$ENV_FILE"
echo "NEXT_PUBLIC_APP_PASSWORD=$APP_PASSWORD" >> "$ENV_FILE"
echo "MONGODB_DB_NAME=tenderbot_${TENANT_ID}" >> "$ENV_FILE"

if [ ! -z "$TF_KEY" ]; then
    sed -i "s/^TINYFISH_API_KEY=.*/TINYFISH_API_KEY=$TF_KEY/" "$ENV_FILE"
fi
if [ ! -z "$COMPOSIO_KEY" ]; then
    sed -i "s/^COMPOSIO_API_KEY=.*/COMPOSIO_API_KEY=$COMPOSIO_KEY/" "$ENV_FILE"
fi
if [ ! -z "$SLACK_CHANNEL" ]; then
    sed -i "s/^SLACK_CHANNEL=.*/SLACK_CHANNEL=$SLACK_CHANNEL/" "$ENV_FILE"
fi

# 3. Spin up Docker Stack
echo "------------------------------------------------------------"
echo "🐳 Deploying Docker Containers for $TENANT_ID..."
echo "------------------------------------------------------------"
# Use project name to isolate the docker stack networks explicitly per tenant
docker-compose --env-file "$ENV_FILE" -p "tenderbot_$TENANT_ID" up -d --build

echo "============================================================"
echo "✅ DEPLOYMENT SUCCESSFUL!"
echo "Isolated Dashboard: http://localhost:3000"
echo "Backend Endpoint: http://localhost:8000"
echo "Secured with Basic Auth (Password Set)"
echo "Database Isolated to: tenderbot_$TENANT_ID"
echo "============================================================"
