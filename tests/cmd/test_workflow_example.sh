#!/bin/bash

echo "=== Chat Workflows - Complete Example ==="
echo ""

BASE_URL="http://localhost:5050/api/v1"

# Create test data file
cat > /tmp/test_sales.csv << 'EOFCSV'
customer_id,amount,status,date
CUST001,1500,active,2026-01-15
CUST002,500,inactive,2026-01-16
CUST003,2000,active,2026-01-17
CUST004,800,active,2026-01-18
CUST005,300,inactive,2026-01-19
EOFCSV

echo "✓ Created test data file: /tmp/test_sales.csv"
echo ""

# Step 1: Create conversation
echo "Step 1: Creating conversation..."
RESPONSE=$(curl -s -X POST "$BASE_URL/chat/workflows")
CHAT_ID=$(echo "$RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['data']['chat_id'])" 2>/dev/null)
PARTICIPANT=$(echo "$RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['data']['participant_name'])" 2>/dev/null)

echo "  ✓ Chat ID: $CHAT_ID"
echo "  ✓ Participant: $PARTICIPANT"
echo ""

# Step 2: Upload file
echo "Step 2: Uploading sales data..."
curl -s -X POST -F "file=@/tmp/test_sales.csv" \
  "$BASE_URL/chat/workflows/$CHAT_ID/upload" | python -c "import sys, json; d=json.load(sys.stdin); print(f\"  ✓ Uploaded: {d['data']['filename']}\")"
echo ""

# Step 3: Execute workflow
echo "Step 3: Executing workflow (CSV → Excel → Filter → Normalize)..."
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {
        "operation": "csv/convert-to-excel",
        "arguments": {
          "sheet_name": "Sales"
        }
      },
      {
        "operation": "excel/search",
        "arguments": {
          "conditions": [
            {"column": "status", "operator": "equals", "value": "active"},
            {"column": "amount", "operator": "greater_than", "value": 1000}
          ],
          "logic": "AND",
          "output_format": "excel"
        }
      },
      {
        "operation": "normalization/apply",
        "arguments": {
          "normalizations": [
            {"column": "customer_id", "type": "uppercase"}
          ]
        }
      }
    ]
  }' \
  "$BASE_URL/chat/workflows/$CHAT_ID/execute" > /tmp/workflow_result.json

if [ $? -eq 0 ]; then
  echo "  ✓ Workflow executed successfully!"
  echo ""
  echo "Results:"
  cat /tmp/workflow_result.json | python -m json.tool | head -30
  echo ""
fi

# Step 4: Get conversation details
echo "Step 4: Retrieving conversation details..."
CONV_DETAILS=$(curl -s "$BASE_URL/chat/workflows/$CHAT_ID")
echo "$CONV_DETAILS" | python -c "import sys, json; d=json.load(sys.stdin)['data']; print(f\"  ✓ Status: {d['status']}\"); print(f\"  ✓ Steps executed: {len(d['workflow_steps'])}\"); print(f\"  ✓ Output files: {len(d['output_files'])}\")"
echo ""

# Step 5: Dump conversation
echo "Step 5: Creating conversation backup..."
DUMP_RESPONSE=$(curl -s -X POST "$BASE_URL/chat/workflows/$CHAT_ID/dump")
DUMP_FILE=$(echo "$DUMP_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['data']['dump_file'])" 2>/dev/null)
echo "  ✓ Backup created: $DUMP_FILE"
echo ""

# Step 6: List all conversations
echo "Step 6: Listing all conversations..."
curl -s "$BASE_URL/chat/workflows" | python -c "import sys, json; d=json.load(sys.stdin)['data']; print(f\"  ✓ Total conversations: {d['count']}\")"
echo ""

echo "=== Workflow Example Complete! ==="
echo ""
echo "Summary:"
echo "  • Created conversation with auto-generated name: $PARTICIPANT"
echo "  • Uploaded CSV file"
echo "  • Executed 3-step workflow: CSV→Excel, Filter, Normalize"
echo "  • Retrieved conversation details"
echo "  • Created backup archive"
echo "  • Verified conversation list"
echo ""
echo "Next steps:"
echo "  • Access output files in: ./automation/workflows/2026/02/$CHAT_ID/outputs/"
echo "  • Download backup from: $BASE_URL/chat/downloads/$DUMP_FILE"
echo "  • Delete conversation: curl -X DELETE $BASE_URL/chat/workflows/$CHAT_ID"
