# Tasks: GAP-59 Conscientization Prompts (Paulo Freire)

## Phase 1: Design Prompt Library (3-4 hours)

### Task 1.1: Create prompt taxonomy
**File**: `frontend/src/data/conscientization-prompts.ts` (new file)
**Estimated**: 2 hours

```typescript
export interface ConscientizationPrompt {
  id: string;
  trigger: 'first_offer' | 'first_need' | 'exchange_complete' | 'weekly' | 'milestone';
  question: string;
  options?: string[];
  followUp?: string;
  freireanPrinciple: 'problem-posing' | 'critical-reflection' | 'praxis' | 'dialogue';
  optional: boolean;
}

export const PROMPTS: ConscientizationPrompt[] = [
  {
    id: 'first-offer',
    trigger: 'first_offer',
    question: "Take a moment... Why are you offering this?",
    options: [
      "I have abundance and want to share",
      "I want to build connections",
      "I'm experimenting with non-market exchange",
      "Other"
    ],
    followUp: "What does it feel like to offer something without expecting payment?",
    freireanPrinciple: 'critical-reflection',
    optional: true
  },
  {
    id: 'exchange-complete',
    trigger: 'exchange_complete',
    question: "You just completed a gift exchange. How was it different from buying/selling?",
    followUp: "What surprised you? Did power dynamics show up? What did you learn?",
    freireanPrinciple: 'praxis',
    optional: true
  },
  {
    id: 'community-milestone',
    trigger: 'milestone',
    question: "Your commune has shared 100 gifts this month. What's happening here?",
    followUp: "What patterns are emerging? Who's participating, who isn't? Is this mutual aid, or replicating hierarchies?",
    freireanPrinciple: 'problem-posing',
    optional: true
  }
];
```

**Acceptance criteria**:
- 8-10 prompts covering key moments
- Questions open-ended, not didactic
- Optional for all prompts
- Follows Freirean principles

### Task 1.2: Design reflection storage (optional)
**File**: `app/models/reflection.py` (new file)
**Estimated**: 1 hour

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Reflection(BaseModel):
    id: str
    user_id: Optional[str]  # Optional for anonymous reflections
    prompt_id: str
    response: str
    context: dict  # What triggered the prompt
    created_at: datetime
    anonymous: bool = False
    shared_with_community: bool = False
```

**Acceptance criteria**:
- Anonymous reflections supported
- User can choose to share or keep private
- Minimal schema (don't over-engineer)

### Task 1.3: A/B test prompt phrasing
**Estimated**: 1 hour

Test variations:
- "Why are you giving?" vs "What motivated this offer?"
- "How did this feel?" vs "What did you notice?"
- Find least preachy, most invitational wording

**Acceptance criteria**:
- 3-5 users test each variation
- Select most engaging phrasing
- Document rationale

## Phase 2: Build Reflection Components (4-5 hours)

### Task 2.1: Create ReflectionPrompt modal
**File**: `frontend/src/components/ReflectionPrompt.tsx` (new file)
**Estimated**: 2 hours

```tsx
interface ReflectionPromptProps {
  prompt: ConscientizationPrompt;
  onSubmit: (response: string) => void;
  onSkip: () => void;
}

export function ReflectionPrompt({ prompt, onSubmit, onSkip }: ReflectionPromptProps) {
  const [response, setResponse] = useState('');

  return (
    <Modal open onClose={onSkip}>
      <ModalContent>
        <Typography variant="h6">{prompt.question}</Typography>

        {prompt.options && (
          <RadioGroup onChange={(e) => setResponse(e.target.value)}>
            {prompt.options.map(option => (
              <FormControlLabel key={option} value={option} label={option} />
            ))}
          </RadioGroup>
        )}

        {prompt.followUp && (
          <TextField
            multiline
            rows={4}
            placeholder={prompt.followUp}
            helperText="Optional - share what you're thinking, or just reflect privately"
          />
        )}

        <Stack direction="row" spacing={2}>
          <Button variant="outlined" onClick={onSkip}>
            Skip (that's okay!)
          </Button>
          <Button variant="contained" onClick={() => onSubmit(response)}>
            Save Reflection
          </Button>
        </Stack>
      </ModalContent>
    </Modal>
  );
}
```

**Acceptance criteria**:
- Non-intrusive modal design
- "Skip" button prominent
- Warm, invitational tone
- Mobile-friendly

### Task 2.2: Create hook for triggering prompts
**File**: `frontend/src/hooks/useConscientization.ts` (new file)
**Estimated**: 1.5 hours

```typescript
export function useConscientization() {
  const { user } = useAuth();
  const [currentPrompt, setCurrentPrompt] = useState<ConscientizationPrompt | null>(null);

  const checkForPrompt = useCallback((event: string, context: any) => {
    // Check if user has seen this prompt recently
    const lastSeen = localStorage.getItem(`prompt-${event}`);
    if (lastSeen && Date.now() - parseInt(lastSeen) < 7 * 24 * 60 * 60 * 1000) {
      return; // Don't show same prompt twice in a week
    }

    // Find matching prompt
    const prompt = PROMPTS.find(p => p.trigger === event);
    if (prompt) {
      setCurrentPrompt(prompt);
    }
  }, []);

  const dismissPrompt = useCallback(() => {
    if (currentPrompt) {
      localStorage.setItem(`prompt-${currentPrompt.trigger}`, Date.now().toString());
    }
    setCurrentPrompt(null);
  }, [currentPrompt]);

  return {
    currentPrompt,
    checkForPrompt,
    dismissPrompt
  };
}
```

**Acceptance criteria**:
- Rate-limits prompts (not annoying)
- Respects user dismissals
- Works across sessions
- Simple API

### Task 2.3: Integrate into key user flows
**Files**: Various page components
**Estimated**: 1.5 hours

```tsx
// In CreateOfferPage.tsx
function CreateOfferPage() {
  const { checkForPrompt } = useConscientization();
  const isFirstOffer = useQuery(['offers', 'count']).data === 0;

  const handleSubmit = async (data) => {
    await createOffer(data);

    if (isFirstOffer) {
      checkForPrompt('first_offer', { offer: data });
    }
  };
}

// In ExchangeCompletePage.tsx
function ExchangeCompletePage() {
  const { checkForPrompt } = useConscientization();

  useEffect(() => {
    checkForPrompt('exchange_complete', { exchange });
  }, []);
}
```

**Acceptance criteria**:
- Prompts appear at meaningful moments
- Don't interrupt critical flows
- Timing feels natural

## Phase 3: Collective Reflection Space (5-6 hours)

### Task 3.1: Create dialogue data model
**File**: `app/models/dialogue.py` (new file)
**Estimated**: 1 hour

```python
class Dialogue(BaseModel):
    id: str
    problem: str  # The tension/contradiction being explored
    voices: List[Voice]
    synthesis: Optional[str]  # Emergent understanding
    created_at: datetime
    commune_id: str

class Voice(BaseModel):
    author_id: Optional[str]  # Anonymous if None
    text: str
    created_at: datetime
```

**Acceptance criteria**:
- Problem-posing structure (not Q&A)
- Anonymous participation supported
- Synthesis emerges from community

### Task 3.2: Create CollectiveReflections page
**File**: `frontend/src/pages/CollectiveReflections.tsx` (new file)
**Estimated**: 3 hours

```tsx
export function CollectiveReflectionsPage() {
  const { data: dialogues } = useQuery(['dialogues']);

  return (
    <Page title="Collective Reflections">
      <Alert severity="info">
        "No one educates anyone else. We educate each other, mediated by the world." - Paulo Freire
      </Alert>

      {dialogues.map(dialogue => (
        <Card key={dialogue.id}>
          <CardHeader title={dialogue.problem} />
          <CardContent>
            {dialogue.voices.map(voice => (
              <Voice key={voice.id} anonymous={!voice.author_id}>
                {voice.text}
              </Voice>
            ))}
          </CardContent>
          <CardActions>
            <Button onClick={() => addVoice(dialogue.id)}>
              Add Your Voice
            </Button>
          </CardActions>
        </Card>
      ))}
    </Page>
  );
}
```

**Acceptance criteria**:
- Surfaces tensions, not just celebrations
- Anonymous participation easy
- Invitation not obligation
- Not a typical forum

### Task 3.3: Create dialogue seeding system
**File**: `app/services/dialogue_service.py` (new file)
**Estimated**: 2 hours

Auto-generate problem-posing dialogues from data:

```python
class DialogueSeeder:
    async def seed_from_patterns(self):
        # Detect imbalances
        if await self.detect_gift_imbalance():
            await self.create_dialogue(
                problem="Some people offer a lot, others rarely. Why?",
                context="Detected in gift data"
            )

        # Detect participation gaps
        if await self.detect_participation_gap():
            await self.create_dialogue(
                problem="Who's participating, who isn't? What does that tell us?",
                context="Participation patterns"
            )
```

**Acceptance criteria**:
- Automatically surfaces tensions
- Based on real data patterns
- Provocative not prescriptive

## Phase 4: Testing & Refinement (2-3 hours)

### Task 4.1: User testing with actual prompts
**Estimated**: 2 hours

Test with 5-10 real users:
- Do prompts feel preachy or invitational?
- Are they annoying or engaging?
- Do people skip or engage?
- What's the emotional response?

**Acceptance criteria**:
- > 60% find prompts "thought-provoking"
- < 20% find them "annoying"
- Skip rate < 80% (some engagement)

### Task 4.2: Adjust prompt frequency
**Estimated**: 1 hour

Find balance between:
- Too frequent: annoying
- Too rare: not impactful

Test different rates:
- Every action (too much!)
- Every 5th action
- Weekly summary
- Milestone-based

**Acceptance criteria**:
- User feedback positive
- Engagement sustained over time

## Phase 5: Documentation (1 hour)

### Task 5.1: Explain Freirean approach
**File**: `docs/CONSCIENTIZATION.md` (new)
**Estimated**: 45 minutes

Document:
- What is conscientization?
- Why prompts, not lectures?
- How to add new prompts
- Freirean principles

**Acceptance criteria**:
- Clear theoretical grounding
- Practical guidance
- Examples of good/bad prompts

### Task 5.2: Settings documentation
**Estimated**: 15 minutes

Document user controls:
- How to disable prompts
- How to export reflections
- Privacy controls

## Verification Checklist

- [ ] Prompts feel invitational, not preachy
- [ ] "Skip" button always visible
- [ ] Prompts appear at meaningful moments
- [ ] Rate-limiting prevents annoyance
- [ ] Collective reflection space exists
- [ ] Anonymous participation supported
- [ ] System surfaces tensions
- [ ] Freirean principles followed
- [ ] User testing positive
- [ ] Documentation complete

## Estimated Total Time

- Phase 1: 4 hours (prompt design)
- Phase 2: 5 hours (components)
- Phase 3: 6 hours (collective space)
- Phase 4: 3 hours (testing)
- Phase 5: 1 hour (docs)

**Total: 1-2 days (19 hours)**

## Dependencies

- User authentication (for non-anonymous reflections)
- Database for storing reflections (optional)
- Analytics to detect patterns for dialogue seeding

## Philosophical Guardrails

**NEVER**:
- Make prompts mandatory
- Judge responses as "right" or "wrong"
- Create social pressure to reflect
- Track who engages vs who doesn't

**ALWAYS**:
- Invite, don't command
- Question, don't lecture
- Surface contradictions, not consensus
- Celebrate diverse responses

## Success Metrics

- 30%+ engagement rate on prompts
- Users report feeling "more aware" of gift economy dynamics
- Community dialogues generate insights
- Tensions surfaced and discussed (not hidden)
- No reports of feeling guilt-tripped
