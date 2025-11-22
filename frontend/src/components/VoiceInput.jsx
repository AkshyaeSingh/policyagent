import { useState, useEffect } from 'react'
import AtomIcon from './AtomIcon'
import './VoiceInput.css'

function VoiceInput({ onComplete }) {
  const [isRecording, setIsRecording] = useState(false)
  const [transcription, setTranscription] = useState('')
  const [recognition, setRecognition] = useState(null)
  const [hasRecorded, setHasRecorded] = useState(false)

  useEffect(() => {
    // Initialize Web Speech API
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      const recognitionInstance = new SpeechRecognition()
      recognitionInstance.continuous = false
      recognitionInstance.interimResults = true
      recognitionInstance.lang = 'en-US'

      recognitionInstance.onresult = (event) => {
        let interimTranscript = ''
        let finalTranscript = ''

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' '
          } else {
            interimTranscript += transcript
          }
        }

        const newText = finalTranscript || interimTranscript
        setTranscription(newText)
        if (finalTranscript) {
          setHasRecorded(true)
        }
      }

      recognitionInstance.onerror = (event) => {
        console.error('Speech recognition error:', event.error)
        setIsRecording(false)
        if (event.error === 'no-speech') {
          alert('No speech detected. Please try again.')
        }
      }

      recognitionInstance.onend = () => {
        setIsRecording(false)
      }

      setRecognition(recognitionInstance)
    } else {
      // Fallback for browsers without speech recognition
      console.warn('Speech recognition not supported. Using text input fallback.')
    }
  }, [])

  const handleMicClick = () => {
    if (!recognition) return

    if (isRecording) {
      recognition.stop()
      setIsRecording(false)
      if (transcription) {
        setHasRecorded(true)
      }
    } else {
      setTranscription('')
      setHasRecorded(false)
      recognition.start()
      setIsRecording(true)
    }
  }

  const handleContinue = () => {
    if (transcription.trim()) {
      onComplete(transcription)
    }
  }

  return (
    <div className="voice-input">
      <div className="voice-content">
        <AtomIcon />
        <h2 className="voice-title">Describe yourself</h2>
        
        <div className="mic-container">
          <button
            className={`mic-button ${isRecording ? 'recording' : ''}`}
            onClick={handleMicClick}
          >
            <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="23" />
              <line x1="8" y1="23" x2="16" y2="23" />
            </svg>
          </button>
          {isRecording && (
            <div className="recording-indicator">
              <span>Listening...</span>
            </div>
          )}
        </div>

        {hasRecorded && transcription && (
          <div className="transcription-container">
            <h3>Your description:</h3>
            <p className="transcription-text">{transcription}</p>
            <button className="continue-button" onClick={handleContinue}>
              Continue
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default VoiceInput
