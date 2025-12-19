#!/bin/bash

echo "=== SQL Injection Audit ==="
echo ""

echo "1. Searching for f-string SQL queries..."
grep -r "f\".*SELECT" app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ --include="*.py" 2>/dev/null || echo "None found"
grep -r "f\".*INSERT" app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ --include="*.py" 2>/dev/null || echo "None found"
grep -r "f\".*UPDATE" app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ --include="*.py" 2>/dev/null || echo "None found"
grep -r "f\".*DELETE" app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ --include="*.py" 2>/dev/null || echo "None found"
echo ""

echo "2. Searching for .format() SQL queries..."
grep -r "\.format(" app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ --include="*.py" 2>/dev/null | grep -i "select\|insert\|update\|delete" || echo "None found"
echo ""

echo "3. Searching for % string formatting in SQL..."
grep -r "% " app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ --include="*.py" 2>/dev/null | grep -i "select\|insert\|update\|delete" || echo "None found"
echo ""

echo "4. Searching for string concatenation in SQL..."
grep -r "+.*SELECT\|SELECT.*+" app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ --include="*.py" 2>/dev/null || echo "None found"
echo ""

echo "5. Listing all .execute() calls for manual review..."
grep -r "\.execute(" app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ --include="*.py" -A 2 -B 2 2>/dev/null | head -100
echo "   (showing first 100 lines, may be more...)"
echo ""

echo "Audit complete. Review findings above."
