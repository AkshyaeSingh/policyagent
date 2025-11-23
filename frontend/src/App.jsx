import { useState } from 'react'
import SplashScreen from './components/SplashScreen'
import VoiceInput from './components/VoiceInput'
import QuestionFlow from './components/QuestionFlow'
import NegotiationVisualization from './components/NegotiationVisualization'
import './App.css'

function App() {
  const [step, setStep] = useState('splash') // 'splash' | 'voice' | 'questions' | 'complete' | 'negotiation'
  const [userDescription, setUserDescription] = useState('')
  const [preferences, setPreferences] = useState(null)

  const handleSplashComplete = () => {
    setStep('voice')
  }

  const handleVoiceComplete = (description) => {
    setUserDescription(description)
    setStep('questions')
  }

  const handleQuestionsComplete = (finalPreferences) => {
    setPreferences(finalPreferences)
    setStep('complete')
  }

  return (
    <div className="app">
      {step === 'splash' && (
        <SplashScreen onComplete={handleSplashComplete} />
      )}
      {step === 'voice' && (
        <VoiceInput onComplete={handleVoiceComplete} />
      )}
      {step === 'questions' && (
        <QuestionFlow
          userDescription={userDescription}
          onComplete={handleQuestionsComplete}
        />
      )}
      {step === 'complete' && (
        <div className="complete-screen">
          <h1>✓ Preferences Captured!</h1>
          <p>Your preferences have been extracted and are ready for analysis.</p>
          <div className="complete-actions">
            <button 
              className="primary-button"
              onClick={() => {
                // Convert preferences to the format expected by the backend
                // The API returns { participants: [{ participant_name, role, preferences }] }
                let negotiationPrefs;
                if (preferences?.participants && preferences.participants.length > 0) {
                  // Extract first participant from API response
                  const participant = preferences.participants[0];
                  negotiationPrefs = {
                    participant_name: participant.participant_name || 'User',
                    role: participant.role || 'neighbor',
                    preferences: participant.preferences || {}
                  };
                } else if (preferences?.participant_name) {
                  // Already in correct format
                  negotiationPrefs = preferences;
                } else {
                  // Fallback format
                  negotiationPrefs = {
                    participant_name: preferences?.participant_name || 'User',
                    role: preferences?.role || 'neighbor',
                    preferences: preferences?.preferences || preferences || {}
                  };
                }
                setPreferences(negotiationPrefs)
                setStep('negotiation')
              }}
            >
              Start Negotiation
            </button>
            <button 
              className="secondary-button"
              onClick={() => {
                setStep('splash')
                setUserDescription('')
                setPreferences(null)
              }}
            >
              Start Over
            </button>
          </div>
        </div>
      )}
      {step === 'negotiation' && preferences && (
        <div className="negotiation-redirect">
          <h1>Starting Negotiation...</h1>
          <p>Opening negotiation visualization in a new window...</p>
          <button 
            onClick={() => {
              // Encode preferences and open in new window
              const prefsJson = encodeURIComponent(JSON.stringify(preferences))
              window.open(`http://localhost:5174/negotiation.html?preferences=${prefsJson}`, '_blank')
            }}
          >
            Open Negotiation View
          </button>
        </div>
      )}
    </div>
  )
}

export default App
