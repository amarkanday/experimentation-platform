#!/bin/bash

# Test script for CloudWatch dashboard deployment

# Test variables
TEST_DASHBOARD_NAME="ExperimentationPlatform-Test"
TEST_DASHBOARD_BODY='{
    "widgets": [
        {
            "type": "metric",
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    [ "AWS/EC2", "CPUUtilization", "InstanceId", "i-1234567890abcdef0" ]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "us-west-2",
                "period": 300
            }
        }
    ]
}'

# Function to test dashboard creation
test_create_dashboard() {
    echo "Testing dashboard creation..."
    aws cloudwatch put-dashboard \
        --dashboard-name "$TEST_DASHBOARD_NAME" \
        --dashboard-body "$TEST_DASHBOARD_BODY" \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION"

    if [ $? -eq 0 ]; then
        echo "✅ Dashboard creation test passed"
    else
        echo "❌ Dashboard creation test failed"
        exit 1
    fi
}

# Function to test dashboard retrieval
test_get_dashboard() {
    echo "Testing dashboard retrieval..."
    aws cloudwatch get-dashboard \
        --dashboard-name "$TEST_DASHBOARD_NAME" \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION"

    if [ $? -eq 0 ]; then
        echo "✅ Dashboard retrieval test passed"
    else
        echo "❌ Dashboard retrieval test failed"
        exit 1
    fi
}

# Function to test dashboard deletion
test_delete_dashboard() {
    echo "Testing dashboard deletion..."
    aws cloudwatch delete-dashboards \
        --dashboard-names "$TEST_DASHBOARD_NAME" \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION"

    if [ $? -eq 0 ]; then
        echo "✅ Dashboard deletion test passed"
    else
        echo "❌ Dashboard deletion test failed"
        exit 1
    fi
}

# Function to test invalid dashboard name
test_invalid_dashboard_name() {
    echo "Testing invalid dashboard name..."
    aws cloudwatch put-dashboard \
        --dashboard-name "" \
        --dashboard-body "$TEST_DASHBOARD_BODY" \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION"

    if [ $? -ne 0 ]; then
        echo "✅ Invalid dashboard name test passed"
    else
        echo "❌ Invalid dashboard name test failed"
        exit 1
    fi
}

# Function to test invalid dashboard body
test_invalid_dashboard_body() {
    echo "Testing invalid dashboard body..."
    aws cloudwatch put-dashboard \
        --dashboard-name "$TEST_DASHBOARD_NAME" \
        --dashboard-body "invalid json" \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION"

    if [ $? -ne 0 ]; then
        echo "✅ Invalid dashboard body test passed"
    else
        echo "❌ Invalid dashboard body test failed"
        exit 1
    fi
}

# Function to test missing AWS credentials
test_missing_credentials() {
    echo "Testing missing AWS credentials..."
    unset AWS_PROFILE
    aws cloudwatch put-dashboard \
        --dashboard-name "$TEST_DASHBOARD_NAME" \
        --dashboard-body "$TEST_DASHBOARD_BODY" \
        --region "$AWS_REGION"

    if [ $? -ne 0 ]; then
        echo "✅ Missing AWS credentials test passed"
    else
        echo "❌ Missing AWS credentials test failed"
        exit 1
    fi
}

# Main test execution
echo "Starting CloudWatch dashboard deployment tests..."

# Set test environment
export AWS_PROFILE="${AWS_PROFILE:-default}"
export AWS_REGION="${AWS_REGION:-us-west-2}"

# Run tests
test_create_dashboard
test_get_dashboard
test_delete_dashboard
test_invalid_dashboard_name
test_invalid_dashboard_body
test_missing_credentials

echo "All CloudWatch dashboard deployment tests completed successfully!"
