#!/bin/bash

# Test script using curl commands
echo "🚀 Testing FastAPI Presentation Generator"
echo "=========================================="

BASE_URL="http://localhost:8001"

# Test 1: Root endpoint
echo ""
echo "🧪 Test 1: Root endpoint"
echo "------------------------"
curl -X GET "$BASE_URL/" \
  -H "accept: application/json" \
  | jq '.' 2>/dev/null || echo "Response received (jq not available for formatting)"

# Test 2: Health check
echo ""
echo "🧪 Test 2: Health check"
echo "-----------------------"
curl -X GET "$BASE_URL/health" \
  -H "accept: application/json" \
  | jq '.' 2>/dev/null || echo "Response received"

# Test 3: Generate presentation
echo ""
echo "🧪 Test 3: Generate presentation"
echo "-------------------------------"
curl -X POST "$BASE_URL/generate-presentation" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Machine Learning Fundamentals",
    "access_token": "demo_token_12345"
  }' \
  | jq '.' 2>/dev/null || echo "Response received"

# Test 4: Invalid request (missing fields)
echo ""
echo "🧪 Test 4: Invalid request"
echo "--------------------------"
curl -X POST "$BASE_URL/generate-presentation" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "invalid_field": "test"
  }' \
  | jq '.' 2>/dev/null || echo "Response received"

echo ""
echo "=========================================="
echo "✅ All tests completed!"
echo ""
echo "💡 To view API docs, visit: $BASE_URL/docs"
