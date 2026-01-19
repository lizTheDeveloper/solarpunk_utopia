/**
 * Test GAP-59: Conscientization Prompts
 *
 * Simple Node.js test to verify the prompt library structure
 */

import { CONSCIENTIZATION_PROMPTS, getPromptForTrigger, shouldShowPrompt, recordPromptShown } from './frontend/src/services/conscientization';

console.log("=" + "=".repeat(60));
console.log("GAP-59: Conscientization Prompts - Tests");
console.log("Philosophical Foundation: Paulo Freire");
console.log('"No one educates anyone alone. People educate each other through dialogue."');
console.log("=" + "=".repeat(60));
console.log();

// Test 1: All prompts exist
console.log("Test 1: Verify all prompt triggers exist");
const expectedTriggers = [
  'first_offer',
  'first_need',
  'first_exchange',
  'receiving_gift',
  'weekly_reflection',
  'milestone_reached',
  'tension_detected'
];

let allExist = true;
for (const trigger of expectedTriggers) {
  if (!CONSCIENTIZATION_PROMPTS[trigger]) {
    console.error(`❌ Missing prompt: ${trigger}`);
    allExist = false;
  } else {
    console.log(`✓ ${trigger}: "${CONSCIENTIZATION_PROMPTS[trigger].question.substring(0, 50)}..."`);
  }
}

if (allExist) {
  console.log("\n✓ All 7 prompts exist\n");
} else {
  console.error("\n❌ Some prompts missing\n");
  process.exit(1);
}

// Test 2: Prompt structure
console.log("Test 2: Verify prompt structure");
const firstOfferPrompt = CONSCIENTIZATION_PROMPTS.first_offer;

if (!firstOfferPrompt.question) {
  console.error("❌ Prompt missing question");
  process.exit(1);
}

if (!firstOfferPrompt.philosophy) {
  console.error("❌ Prompt missing philosophy explanation");
  process.exit(1);
}

if (!firstOfferPrompt.options || firstOfferPrompt.options.length < 3) {
  console.error("❌ Prompt missing sufficient options");
  process.exit(1);
}

console.log(`✓ Question: ${firstOfferPrompt.question}`);
console.log(`✓ Options: ${firstOfferPrompt.options.length} choices`);
console.log(`✓ Philosophy: ${firstOfferPrompt.philosophy.substring(0, 80)}...`);
if (firstOfferPrompt.followUp) {
  console.log(`✓ Follow-up: ${firstOfferPrompt.followUp.substring(0, 60)}...`);
}
console.log();

// Test 3: Context customization
console.log("Test 3: Verify context customization");
const weeklyPrompt = getPromptForTrigger('weekly_reflection', {
  gave: '5 gifts',
  received: '3 gifts'
});

if (!weeklyPrompt) {
  console.error("❌ Failed to get weekly_reflection prompt");
  process.exit(1);
}

if (!weeklyPrompt.question.includes('5 gifts')) {
  console.error("❌ Context not applied to question");
  process.exit(1);
}

console.log(`✓ Customized question: ${weeklyPrompt.question}`);
console.log();

// Test 4: Problem-posing prompts
console.log("Test 4: Verify sub-questions (problem-posing)");
const exchangePrompt = CONSCIENTIZATION_PROMPTS.first_exchange;

if (!exchangePrompt.subQuestions || exchangePrompt.subQuestions.length === 0) {
  console.error("❌ Exchange prompt missing sub-questions");
  process.exit(1);
}

console.log(`✓ Exchange prompt has ${exchangePrompt.subQuestions.length} sub-questions:`);
exchangePrompt.subQuestions.forEach((q, i) => {
  console.log(`  ${i + 1}. ${q}`);
});
console.log();

// Test 5: Philosophy alignment
console.log("Test 5: Verify Freire's pedagogical principles");
const principles = {
  'Problem-posing': false,
  'Dialogue': false,
  'Critical consciousness': false,
  'Reflection': false
};

Object.values(CONSCIENTIZATION_PROMPTS).forEach(prompt => {
  const text = (prompt.question + ' ' + prompt.philosophy + ' ' + (prompt.followUp || '')).toLowerCase();

  if (text.includes('why') || text.includes('what does') || prompt.subQuestions) {
    principles['Problem-posing'] = true;
  }
  if (text.includes('dialogue') || text.includes('together') || text.includes('community')) {
    principles['Dialogue'] = true;
  }
  if (text.includes('conscious') || text.includes('aware') || text.includes('notice')) {
    principles['Critical consciousness'] = true;
  }
  if (text.includes('reflect') || text.includes('think') || text.includes('moment')) {
    principles['Reflection'] = true;
  }
});

let allPrinciplesPresent = true;
Object.entries(principles).forEach(([principle, present]) => {
  if (present) {
    console.log(`✓ ${principle}: Present in prompts`);
  } else {
    console.error(`❌ ${principle}: Missing from prompts`);
    allPrinciplesPresent = false;
  }
});

if (!allPrinciplesPresent) {
  console.error("\n❌ Some Freire principles missing");
  process.exit(1);
}

console.log();
console.log("=" + "=".repeat(60));
console.log("✓ All tests passed!");
console.log();
console.log("The Conscientization system implements:");
console.log("  1. Critical reflection prompts at key moments");
console.log("  2. Problem-posing questions (not lectures)");
console.log("  3. Dialogue space for collective learning");
console.log("  4. Optional participation (no coercion)");
console.log("  5. Philosophical framing from Paulo Freire");
console.log();
console.log("This invites users to think about WHY they participate,");
console.log("not just transact mechanically. Conscientization in action.");
console.log("=" + "=".repeat(60));
