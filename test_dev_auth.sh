#!/bin/bash

echo "================================"
echo "Development Auth Bypass Test"
echo "================================"
echo ""

# Check if backend is running
echo "1. Checking if backend is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "❌ Backend is NOT running"
    echo ""
    echo "Start the backend with:"
    echo "  cd /Users/ashishmarkanday/github/experimentation-platform"
    echo "  source venv/bin/activate"
    echo "  uvicorn backend.app.main:app --reload"
    echo ""
    exit 1
fi

echo ""
echo "2. Testing audit logs endpoint with dev token..."
echo ""

# Test with dev token
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  -H "Authorization: Bearer dev-token-admin" \
  http://localhost:8000/api/v1/audit-logs/)

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE:/d')

echo "HTTP Status: $HTTP_CODE"
echo ""
echo "Response:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

echo ""
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ SUCCESS! Development authentication bypass is working!"
    echo ""
    echo "You can now use 'dev-token-admin' for all API requests in development mode."
else
    echo "❌ Test failed with HTTP $HTTP_CODE"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Ensure ENVIRONMENT=development in backend/.env"
    echo "  2. Restart the backend server"
    echo "  3. Check backend logs for errors"
fi

echo ""
echo "================================"
