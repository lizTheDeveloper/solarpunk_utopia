/**
 * GAP-59: Conscientization Prompts (Paulo Freire)
 *
 * "The oppressed must not, in seeking to regain their humanity, become in turn
 * oppressors of the oppressors, but rather restorers of the humanity of both."
 * - Paulo Freire
 *
 * Types for critical reflection prompts that invite users to think about WHY
 * they're participating in the gift economy, not just transact mechanically.
 */

export interface ConscientizationPrompt {
  id: string;
  trigger: PromptTrigger;
  question: string;
  options?: string[];
  followUp?: string;
  subQuestions?: string[];
  philosophy: string;  // Brief explanation of why this matters
}

export type PromptTrigger =
  | 'first_offer'
  | 'first_need'
  | 'first_exchange'
  | 'receiving_gift'
  | 'weekly_reflection'
  | 'milestone_reached'
  | 'tension_detected';

export interface UserReflection {
  id: string;
  user_id: string;
  prompt_id: string;
  response: string | string[];  // Can be selected options or free text
  free_text?: string;
  created_at: string;
  anonymous?: boolean;  // Can be shared anonymously
}

export interface DialogueProblem {
  id: string;
  problem: string;  // The contradiction or tension
  voices: DialogueVoice[];
  synthesis?: string;  // Emergent collective understanding
  created_at: string;
}

export interface DialogueVoice {
  id: string;
  author: string | 'anonymous';
  text: string;
  created_at: string;
}
