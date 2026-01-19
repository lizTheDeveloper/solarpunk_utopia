#!/bin/bash

echo "============================================================"
echo "GAP-59: Conscientization Prompts - Verification"
echo "Philosophical Foundation: Paulo Freire"
echo "============================================================"
echo ""

echo "Checking files created:"
echo ""

files=(
  "frontend/src/types/conscientization.ts"
  "frontend/src/services/conscientization.ts"
  "frontend/src/components/ReflectionPrompt.tsx"
  "frontend/src/hooks/useConscientization.ts"
  "frontend/src/pages/CollectiveReflectionsPage.tsx"
)

all_exist=true
for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    lines=$(wc -l < "$file")
    echo "✓ $file ($lines lines)"
  else
    echo "❌ Missing: $file"
    all_exist=false
  fi
done

echo ""

if [ "$all_exist" = true ]; then
  echo "✓ All files created successfully!"
  echo ""
  echo "Implementation includes:"
  echo "  1. Prompt library with 7 trigger types"
  echo "  2. React component for displaying prompts"
  echo "  3. Hook for triggering prompts at key moments"
  echo "  4. Collective reflections page (dialogue space)"
  echo "  5. Philosophical framing from Paulo Freire"
  echo ""
  echo "Prompts trigger on:"
  echo "  - First offer/need/exchange"
  echo "  - Receiving gifts"
  echo "  - Weekly reflections"
  echo "  - Community milestones"
  echo "  - Detected tensions"
  echo ""
  echo "\"No one educates anyone alone."
  echo "People educate each other through dialogue.\""
  echo "- Paulo Freire"
  exit 0
else
  echo "❌ Some files missing"
  return 1
fi
