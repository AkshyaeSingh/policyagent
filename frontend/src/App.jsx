import { useState } from 'react'
import SplashScreen from './components/SplashScreen'
import VoiceInput from './components/VoiceInput'
import QuestionFlow from './components/QuestionFlow'
import './App.css'

function App() {
  const [step, setStep] = useState('splash') // 'splash' | 'voice' | 'questions' | 'complete'
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
          <button onClick={() => {
            setStep('splash')
            setUserDescription('')
            setPreferences(null)
          }}>Start Over</button>
        </div>
      )}
    </div>
  )
}

export default App
