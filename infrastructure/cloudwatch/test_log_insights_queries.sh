#!/bin/bash

# Test script for CloudWatch Log Insights queries

# Test variables
TEST_LOG_GROUP="ExperimentationPlatform-Test"
TEST_QUERY='fields @timestamp, @message
| filter @message like /error/
| sort @timestamp desc
| limit 20'

# Function to test query execution
test_query_execution() {
    echo "Testing query execution..."
    aws logs start-query \
        --log-group-name "$TEST_LOG_GROUP" \
        --start-time "$(date -v-1H +%s)" \
        --end-time "$(date +%s)" \
        --query-string "$TEST_QUERY" \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION"

    if [ $? -eq 0 ]; then
        echo "✅ Query execution test passed"
    else
        echo "❌ Query execution test failed"
        exit 1
    fi
}

# Function to test invalid query
test_invalid_query() {
    echo "Testing invalid query..."
    aws logs start-query \
        --log-group-name "$TEST_LOG_GROUP" \
        --start-time "$(date -v-1H +%s)" \
        --end-time "$(date +%s)" \
        --query-string "invalid query" \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION"

    if [ $? -ne 0 ]; then
        echo "✅ Invalid query test passed"
    else
        echo "❌ Invalid query test failed"
        exit 1
    fi
}

# Function to test query with invalid time range
test_invalid_time_range() {
    echo "Testing invalid time range..."
    aws logs start-query \
        --log-group-name "$TEST_LOG_GROUP" \
        --start-time "$(date +%s)" \
        --end-time "$(date -v-1H +%s)" \
        --query-string "$TEST_QUERY" \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION"

    if [ $? -ne 0 ]; then
        echo "✅ Invalid time range test passed"
    else
        echo "❌ Invalid time range test failed"
        exit 1
    fi
}

# Function to test query with non-existent log group
test_nonexistent_log_group() {
    echo "Testing non-existent log group..."
    aws logs start-query \
        --log-group-name "NonExistentLogGroup" \
        --start-time "$(date -v-1H +%s)" \
        --end-time "$(date +%s)" \
        --query-string "$TEST_QUERY" \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION"

    if [ $? -ne 0 ]; then
        echo "✅ Non-existent log group test passed"
    else
        echo "❌ Non-existent log group test failed"
        exit 1
    fi
}

# Function to test query with missing permissions
test_missing_permissions() {
    echo "Testing missing permissions..."
    aws logs start-query \
        --log-group-name "$TEST_LOG_GROUP" \
        --start-time "$(date -v-1H +%s)" \
        --end-time "$(date +%s)" \
        --query-string "$TEST_QUERY" \
        --profile "invalid-profile" \
        --region "$AWS_REGION"

    if [ $? -ne 0 ]; then
        echo "✅ Missing permissions test passed"
    else
        echo "❌ Missing permissions test failed"
        exit 1
    fi
}

# Function to test query results retrieval
test_query_results() {
    echo "Testing query results retrieval..."
    # First start a query
    query_id=$(aws logs start-query \
        --log-group-name "$TEST_LOG_GROUP" \
        --start-time "$(date -v-1H +%s)" \
        --end-time "$(date +%s)" \
        --query-string "$TEST_QUERY" \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION" \
        --query 'queryId' \
        --output text)

    if [ $? -eq 0 ]; then
        # Wait for query to complete
        sleep 5

        # Get results
        aws logs get-query-results \
            --query-id "$query_id" \
            --profile "$AWS_PROFILE" \
            --region "$AWS_REGION"

        if [ $? -eq 0 ]; then
            echo "✅ Query results retrieval test passed"
        else
            echo "❌ Query results retrieval test failed"
            exit 1
        fi
    else
        echo "❌ Query start failed"
        exit 1
    fi
}

# Main test execution
echo "Starting CloudWatch Log Insights query tests..."

# Set test environment
export AWS_PROFILE="${AWS_PROFILE:-default}"
export AWS_REGION="${AWS_REGION:-us-west-2}"

# Run tests
test_query_execution
test_invalid_query
test_invalid_time_range
test_nonexistent_log_group
test_missing_permissions
test_query_results

echo "All CloudWatch Log Insights query tests completed successfully!"
