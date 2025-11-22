import { useState } from 'react'
import InitialInput from './components/InitialInput'
import SwipeableQuestions from './components/SwipeableQuestions'
import './App.css'

function App() {
  const [step, setStep] = useState('initial') // 'initial' | 'questions' | 'complete'
  const [userInfo, setUserInfo] = useState(null)
  const [preferences, setPreferences] = useState(null)

  const handleInitialSubmit = (info) => {
    setUserInfo(info)
    setStep('questions')
  }

  const handleQuestionsComplete = (finalPreferences) => {
    setPreferences(finalPreferences)
    setStep('complete')
  }

  return (
    <div className="app">
      {step === 'initial' && (
        <InitialInput onSubmit={handleInitialSubmit} />
      )}
      {step === 'questions' && (
        <SwipeableQuestions
          userInfo={userInfo}
          onComplete={handleQuestionsComplete}
        />
      )}
      {step === 'complete' && (
        <div className="complete-screen">
          <h1>✓ Preferences Captured!</h1>
          <p>Your preferences have been extracted and are ready for analysis.</p>
          <button onClick={() => {
            setStep('initial')
            setUserInfo(null)
            setPreferences(null)
          }}>Start Over</button>
        </div>
      )}
    </div>
  )
}

export default App
