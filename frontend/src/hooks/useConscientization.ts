/**
 * GAP-59: Conscientization Hook
 *
 * React hook to trigger reflection prompts at key moments
 */

import { useState, useCallback } from 'react';
import { ConscientizationPrompt, UserReflection } from '../types/conscientization';
import {
  getPromptForTrigger,
  shouldShowPrompt,
  recordPromptShown
} from '../services/conscientization';

export interface UseConscientizationReturn {
  activePrompt: ConscientizationPrompt | null;
  showPrompt: (trigger: string, context?: any) => void;
  dismissPrompt: () => void;
  submitReflection: (reflection: Partial<UserReflection>) => void;
}

export function useConscientization(userId: string): UseConscientizationReturn {
  const [activePrompt, setActivePrompt] = useState<ConscientizationPrompt | null>(null);

  const showPrompt = useCallback((trigger: string, context?: any) => {
    // Check if user should see this prompt
    if (!shouldShowPrompt(userId, trigger)) {
      return;
    }

    // Get the prompt
    const prompt = getPromptForTrigger(trigger, context);

    if (prompt) {
      setActivePrompt(prompt);
      recordPromptShown(userId, trigger);
    }
  }, [userId]);

  const dismissPrompt = useCallback(() => {
    setActivePrompt(null);
  }, []);

  const submitReflection = useCallback((reflection: Partial<UserReflection>) => {
    console.log('💭 Freire Reflection:', reflection);

    // Store reflection locally
    const reflections = JSON.parse(
      localStorage.getItem(`freire_reflections_${userId}`) || '[]'
    );

    reflections.push({
      ...reflection,
      id: `reflection:${Date.now()}`
    });

    localStorage.setItem(
      `freire_reflections_${userId}`,
      JSON.stringify(reflections)
    );

    // TODO: Send to API if user wants to share
    if (reflection.anonymous || !reflection.anonymous) {
      // In future: POST /api/reflections
      console.log('Would send reflection to API:', reflection);
    }

    setActivePrompt(null);
  }, [userId]);

  return {
    activePrompt,
    showPrompt,
    dismissPrompt,
    submitReflection
  };
}
