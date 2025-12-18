#!/bin/bash

# Setup local Cognito in LocalStack for development
# Run this after starting LocalStack: docker-compose up -d localstack

echo "Setting up local Cognito User Pool in LocalStack..."

export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_REGION=us-west-2

# Wait for LocalStack to be ready
echo "Waiting for LocalStack to be ready..."
timeout=30
counter=0
while [ $counter -lt $timeout ]; do
    if curl -s http://localhost:4566/_localstack/health | grep -q '"cognito-idp": "available"'; then
        echo "✅ LocalStack is ready"
        break
    fi
    echo "Waiting... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    echo "❌ LocalStack did not become ready in time"
    exit 1
fi

# Create User Pool
echo "Creating Cognito User Pool..."
USER_POOL_RESPONSE=$(aws cognito-idp create-user-pool \
    --endpoint-url http://localhost:4566 \
    --pool-name local-experimentation-pool \
    --policies '{"PasswordPolicy":{"MinimumLength":8,"RequireUppercase":false,"RequireLowercase":false,"RequireNumbers":false,"RequireSymbols":false}}' \
    --auto-verified-attributes email \
    --username-attributes email \
    --region us-west-2)

USER_POOL_ID=$(echo $USER_POOL_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['UserPool']['Id'])")
echo "✅ User Pool created: $USER_POOL_ID"

# Create User Pool Client
echo "Creating Cognito User Pool Client..."
CLIENT_RESPONSE=$(aws cognito-idp create-user-pool-client \
    --endpoint-url http://localhost:4566 \
    --user-pool-id $USER_POOL_ID \
    --client-name local-experimentation-client \
    --generate-secret \
    --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH ALLOW_USER_SRP_AUTH \
    --region us-west-2)

CLIENT_ID=$(echo $CLIENT_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['UserPoolClient']['ClientId'])")
echo "✅ Client created: $CLIENT_ID"

# Create admin group
echo "Creating admin group..."
aws cognito-idp create-group \
    --endpoint-url http://localhost:4566 \
    --user-pool-id $USER_POOL_ID \
    --group-name Admins \
    --description "Administrator group" \
    --region us-west-2

echo "✅ Admin group created"

# Create test admin user
echo "Creating test admin user..."
aws cognito-idp admin-create-user \
    --endpoint-url http://localhost:4566 \
    --user-pool-id $USER_POOL_ID \
    --username admin@example.com \
    --user-attributes Name=email,Value=admin@example.com Name=email_verified,Value=true \
    --temporary-password TempPassword123! \
    --message-action SUPPRESS \
    --region us-west-2

# Set permanent password
aws cognito-idp admin-set-user-password \
    --endpoint-url http://localhost:4566 \
    --user-pool-id $USER_POOL_ID \
    --username admin@example.com \
    --password admin123 \
    --permanent \
    --region us-west-2

# Add user to admin group
aws cognito-idp admin-add-user-to-group \
    --endpoint-url http://localhost:4566 \
    --user-pool-id $USER_POOL_ID \
    --username admin@example.com \
    --group-name Admins \
    --region us-west-2

echo "✅ Admin user created: admin@example.com / admin123"

# Update .env file
echo ""
echo "================================================"
echo "Add these to your backend/.env file:"
echo "================================================"
echo "AWS_REGION=us-west-2"
echo "AWS_ENDPOINT_URL=http://localhost:4566"
echo "AWS_ACCESS_KEY_ID=test"
echo "AWS_SECRET_ACCESS_KEY=test"
echo "COGNITO_USER_POOL_ID=$USER_POOL_ID"
echo "COGNITO_CLIENT_ID=$CLIENT_ID"
echo "================================================"
echo ""
echo "✅ LocalStack Cognito setup complete!"
echo ""
echo "Test credentials:"
echo "  Email: admin@example.com"
echo "  Password: admin123"
