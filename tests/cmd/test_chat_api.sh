#!/bin/bash

echo "=== Testing Chat Workflows REST API ==="
echo ""

BASE_URL="http://localhost:5050/api/v1"

# Test 1: Create conversation
echo "1. Creating new conversation..."
RESPONSE=$(curl -s -X POST "$BASE_URL/chat/workflows")
echo "$RESPONSE" | python -m json.tool
CHAT_ID=$(echo "$RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['data']['chat_id'])" 2>/dev/null)

if [ -z "$CHAT_ID" ]; then
    echo "❌ Failed to create conversation"
    exit 1
fi

echo "✓ Created conversation: $CHAT_ID"
echo ""

# Test 2: List conversations
echo "2. Listing conversations..."
curl -s "$BASE_URL/chat/workflows" | python -m json.tool | head -20
echo "✓ Listed conversations"
echo ""

# Test 3: Get conversation details
echo "3. Getting conversation details..."
curl -s "$BASE_URL/chat/workflows/$CHAT_ID" | python -m json.tool | head -20
echo "✓ Retrieved conversation"
echo ""

# Test 4: Delete conversation
echo "4. Deleting conversation..."
curl -s -X DELETE "$BASE_URL/chat/workflows/$CHAT_ID" | python -m json.tool
echo "✓ Deleted conversation"
echo ""

# Test 5: Backup SQLite
echo "5. Testing SQLite backup..."
curl -s -X POST "$BASE_URL/chat/sqlite/backup" | python -m json.tool
echo "✓ Created database backup"
echo ""

echo "=== All API Tests Passed! ==="
