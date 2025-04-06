#!/bin/bash

# Script to deploy CloudWatch dashboards for Experimentation Platform

# Exit on error
set -e

# Check for required AWS CLI
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is required but not installed. Please install it first."
    exit 1
fi

# Set AWS profile and region
AWS_PROFILE=${AWS_PROFILE:-experimentation-platform}
AWS_REGION=${AWS_REGION:-us-west-2}

echo "Using AWS Profile: $AWS_PROFILE"
echo "Using AWS Region: $AWS_REGION"

# Define dashboard names
SYSTEM_HEALTH_DASHBOARD="ExperimentationPlatform-SystemHealth"
API_PERFORMANCE_DASHBOARD="ExperimentationPlatform-APIPerformance"

# Path to dashboard definition files
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEM_HEALTH_DEFINITION="$SCRIPT_DIR/system-health-dashboard.json"
API_PERFORMANCE_DEFINITION="$SCRIPT_DIR/api-performance-dashboard.json"

# Deploy system health dashboard
echo "Deploying System Health Dashboard..."
aws cloudwatch put-dashboard \
    --dashboard-name "$SYSTEM_HEALTH_DASHBOARD" \
    --dashboard-body "$(cat $SYSTEM_HEALTH_DEFINITION)" \
    --profile "$AWS_PROFILE" \
    --region "$AWS_REGION"

echo "System Health Dashboard deployed successfully!"

# Deploy API performance dashboard
echo "Deploying API Performance Dashboard..."
aws cloudwatch put-dashboard \
    --dashboard-name "$API_PERFORMANCE_DASHBOARD" \
    --dashboard-body "$(cat $API_PERFORMANCE_DEFINITION)" \
    --profile "$AWS_PROFILE" \
    --region "$AWS_REGION"

echo "API Performance Dashboard deployed successfully!"

echo "All dashboards deployed successfully!"
