/**
 * GAP-59: Conscientization Prompt Library
 *
 * Paulo Freire's pedagogy: critical consciousness through reflection and action
 */

import { ConscientizationPrompt } from '../types/conscientization';

export const CONSCIENTIZATION_PROMPTS: Record<string, ConscientizationPrompt> = {
  first_offer: {
    id: 'first_offer',
    trigger: 'first_offer',
    question: "Take a moment... Why are you offering this?",
    options: [
      "I have abundance and want to share",
      "I want to build connections",
      "I'm experimenting with non-market exchange",
      "I'm trying to live my values",
      "Other"
    ],
    followUp: "What does it feel like to offer something without expecting payment?",
    philosophy: "Freire believed liberation requires understanding WHY we act, not just acting mechanically. This prompt invites you to examine your motivations."
  },

  first_need: {
    id: 'first_need',
    trigger: 'first_need',
    question: "You're asking for help. How does that feel?",
    options: [
      "Natural - we all need things",
      "Vulnerable - asking is hard",
      "Hopeful - curious if it works",
      "Guilty - I should provide for myself",
      "Other"
    ],
    followUp: "What would it mean if asking for help was seen as strength, not weakness?",
    philosophy: "Capitalism teaches us to be ashamed of needing others. Gift economy is about interdependence, not independence."
  },

  first_exchange: {
    id: 'first_exchange',
    trigger: 'first_exchange',
    question: "You just completed a gift exchange. How was it different from buying/selling?",
    subQuestions: [
      "What surprised you?",
      "Did power dynamics show up?",
      "What did you learn?",
      "How did it feel compared to a transaction?"
    ],
    philosophy: "Freire's 'praxis' - reflection AND action. You acted (exchanged). Now reflect on what happened."
  },

  receiving_gift: {
    id: 'receiving_gift',
    trigger: 'receiving_gift',
    question: "What does it mean to receive without paying?",
    options: [
      "Gratitude - someone shared with me",
      "Debt - I owe them now",
      "Connection - we're in relationship",
      "Discomfort - I'm not used to this",
      "Other"
    ],
    followUp: "Capitalist culture says receiving without paying = debt. Gift culture says it creates relationship. Which feels true for you?",
    philosophy: "Freire warned about 'internalized oppression' - we can carry capitalist ideas even when trying to reject capitalism."
  },

  weekly_reflection: {
    id: 'weekly_reflection',
    trigger: 'weekly_reflection',
    question: "This week you gave [X] and received [Y]. What do you notice?",
    subQuestions: [
      "Are you in balance, or does that not matter to you?",
      "What relationships formed or deepened?",
      "What would a capitalist say about this week?",
      "What tensions or contradictions came up?"
    ],
    philosophy: "Regular reflection prevents the gift economy from becoming just another unconscious habit. Stay awake to what you're creating."
  },

  milestone_reached: {
    id: 'milestone_reached',
    trigger: 'milestone_reached',
    question: "Your commune has shared [N] gifts this month. What's happening here?",
    subQuestions: [
      "What patterns are emerging?",
      "Who's participating? Who isn't?",
      "Is this mutual aid, or replicating hierarchies?",
      "What would make this more liberatory?"
    ],
    philosophy: "Collective reflection space. Freire's 'conscientization' happens in dialogue, not isolation."
  },

  tension_detected: {
    id: 'tension_detected',
    trigger: 'tension_detected',
    question: "There's a tension in the community: [PROBLEM]. Let's think together.",
    subQuestions: [
      "What's the root cause?",
      "Who's affected? Who's not?",
      "What would addressing this require?",
      "What are we learning?"
    ],
    philosophy: "Freire: 'Problem-posing education.' Don't hide tensions - use them as opportunities for collective learning."
  }
};

/**
 * Get appropriate prompt based on user action
 */
export function getPromptForTrigger(trigger: string, context?: any): ConscientizationPrompt | null {
  const prompt = CONSCIENTIZATION_PROMPTS[trigger];

  if (!prompt) return null;

  // Customize question with context if provided
  if (context) {
    const customizedPrompt = { ...prompt };

    if (trigger === 'weekly_reflection' && context.gave && context.received) {
      customizedPrompt.question = `This week you gave ${context.gave} and received ${context.received}. What do you notice?`;
    }

    if (trigger === 'milestone_reached' && context.count) {
      customizedPrompt.question = `Your commune has shared ${context.count} gifts this month. What's happening here?`;
    }

    if (trigger === 'tension_detected' && context.problem) {
      customizedPrompt.question = `There's a tension in the community: ${context.problem}. Let's think together.`;
    }

    return customizedPrompt;
  }

  return prompt;
}

/**
 * Check if user should see a prompt based on their activity
 */
export function shouldShowPrompt(userId: string, trigger: string): boolean {
  // Check localStorage for when user last saw this prompt type
  const lastShown = localStorage.getItem(`freire_prompt_${trigger}_${userId}`);

  if (!lastShown) {
    return true;  // Never shown
  }

  const lastShownDate = new Date(lastShown);
  const now = new Date();

  // Different prompts have different frequencies
  switch (trigger) {
    case 'first_offer':
    case 'first_need':
    case 'first_exchange':
      // Only show once (first time)
      return false;

    case 'receiving_gift':
      // Show every 5th time
      const count = parseInt(localStorage.getItem(`freire_count_${trigger}_${userId}`) || '0');
      return count % 5 === 0;

    case 'weekly_reflection':
      // Show weekly
      const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      return lastShownDate < weekAgo;

    case 'milestone_reached':
    case 'tension_detected':
      // Show each time (these are rare events)
      return true;

    default:
      return false;
  }
}

/**
 * Mark prompt as shown
 */
export function recordPromptShown(userId: string, trigger: string): void {
  localStorage.setItem(`freire_prompt_${trigger}_${userId}`, new Date().toISOString());

  // Increment count for frequency-based prompts
  const countKey = `freire_count_${trigger}_${userId}`;
  const count = parseInt(localStorage.getItem(countKey) || '0');
  localStorage.setItem(countKey, (count + 1).toString());
}
