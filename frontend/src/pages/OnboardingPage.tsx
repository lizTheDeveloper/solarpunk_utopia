import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { WelcomeStep } from '../components/onboarding/WelcomeStep'
import { GiftEconomyStep } from '../components/onboarding/GiftEconomyStep'
import { CreateOfferStep } from '../components/onboarding/CreateOfferStep'
import { BrowseOffersStep } from '../components/onboarding/BrowseOffersStep'
import { AgentsHelpStep } from '../components/onboarding/AgentsHelpStep'
import { CompletionStep } from '../components/onboarding/CompletionStep'

/**
 * Onboarding flow for first-time users.
 * GAP-12: Onboarding Flow
 *
 * Shows a guided tour of the app:
 * 1. Welcome & introduction
 * 2. Gift economy explanation
 * 3. Create your first offer
 * 4. Browse community offers
 * 5. How agents help you
 * 6. Completion celebration
 */
export function OnboardingPage() {
  const [currentStep, setCurrentStep] = useState(0)
  const navigate = useNavigate()

  const handleSkip = () => {
    // Mark onboarding as complete
    localStorage.setItem('onboarding_completed', 'true')
    // Navigate to homepage (replace to prevent back button loop)
    navigate('/', { replace: true })
  }

  const stepTitles = [
    'Welcome',
    'Gift Economy',
    'Create Offer',
    'Browse Offers',
    'Smart Helpers',
    'Complete'
  ]

  const steps = [
    <WelcomeStep onNext={() => setCurrentStep(1)} />,
    <GiftEconomyStep
      onNext={() => setCurrentStep(2)}
      onBack={() => setCurrentStep(0)}
    />,
    <CreateOfferStep
      onNext={() => setCurrentStep(3)}
      onBack={() => setCurrentStep(1)}
    />,
    <BrowseOffersStep
      onNext={() => setCurrentStep(4)}
      onBack={() => setCurrentStep(2)}
    />,
    <AgentsHelpStep
      onNext={() => setCurrentStep(5)}
      onBack={() => setCurrentStep(3)}
    />,
    <CompletionStep
      onFinish={() => {
        // Mark onboarding as complete
        localStorage.setItem('onboarding_completed', 'true')
        // Navigate to homepage (replace to prevent back button loop)
        navigate('/', { replace: true })
      }}
    />
  ]

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-500 to-purple-600 p-4 sm:p-8">
      <div className="max-w-3xl w-full">
        {/* Progress indicator with step info and skip button */}
        <div className="flex flex-col gap-3 sm:gap-4 mb-6 sm:mb-8">
          {/* Step counter and skip button */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 text-white">
            <div className="text-xs sm:text-sm opacity-90">
              Step {currentStep + 1} of {steps.length}: {stepTitles[currentStep]}
            </div>
            <button
              onClick={handleSkip}
              className="bg-transparent border border-white/50 text-white px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm transition-all hover:bg-white/10 hover:border-white"
            >
              Skip to App
            </button>
          </div>

          {/* Progress dots */}
          <div className="flex justify-center gap-1.5 sm:gap-2">
            {steps.map((_, index) => (
              <div
                key={index}
                className={`w-6 sm:w-8 h-1.5 sm:h-2 rounded-sm transition-all duration-300 ${
                  index === currentStep
                    ? 'bg-white'
                    : 'bg-white/30'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Current step */}
        {steps[currentStep]}
      </div>
    </div>
  )
}
