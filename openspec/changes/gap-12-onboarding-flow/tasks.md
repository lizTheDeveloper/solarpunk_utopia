# Tasks: GAP-12 Onboarding Flow

## Implementation (1-2 days)

### Task 1: Create OnboardingPage structure
**File**: `frontend/src/pages/OnboardingPage.tsx`
**Estimated**: 2 hours

```typescript
const steps = [
  'welcome',
  'how-it-works',
  'create-offer',
  'browse-community',
  'agents-intro',
  'complete'
];

const OnboardingPage = () => {
  const [currentStep, setCurrentStep] = useState(0);

  const handleComplete = () => {
    localStorage.setItem('onboarding_complete', 'true');
    navigate('/');
  };

  return (
    <div className="onboarding">
      {currentStep === 0 && <WelcomeStep onNext={() => setCurrentStep(1)} />}
      {/* ... other steps */}
    </div>
  );
};
```

### Task 2: Create step components
**Files**: `frontend/src/components/onboarding/*.tsx`
**Estimated**: 4 hours

- WelcomeStep.tsx
- HowItWorksStep.tsx
- CreateOfferStep.tsx
- BrowseCommunityStep.tsx
- AgentsIntroStep.tsx
- CompleteStep.tsx

### Task 3: Add routing logic
**File**: `frontend/src/App.tsx`
**Estimated**: 1 hour

```typescript
const onboardingComplete = localStorage.getItem('onboarding_complete');

// In routes
{!onboardingComplete && <Route path="*" element={<OnboardingPage />} />}
```

### Task 4: Design and styling
**Estimated**: 3 hours

Make it beautiful, mobile-friendly, engaging.

### Task 5: Testing
**Estimated**: 1 hour

Test full flow, test skip, test never repeat.

**Total: 11 hours (~1.5 days)**
