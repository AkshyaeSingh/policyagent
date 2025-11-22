import { useState } from 'react'
import ChatInterface from './components/ChatInterface'
import ParticipantForm from './components/ParticipantForm'
import PreferencesOutput from './components/PreferencesOutput'
import './App.css'

function App() {
  const [participantName, setParticipantName] = useState('')
  const [role, setRole] = useState('')
  const [conversationHistory, setConversationHistory] = useState([])
  const [extractedPreferences, setExtractedPreferences] = useState(null)
  const [formattedOutput, setFormattedOutput] = useState('')

  const handleParticipantSubmit = (name, participantRole) => {
    setParticipantName(name)
    setRole(participantRole)
    setConversationHistory([])
    setExtractedPreferences(null)
    setFormattedOutput('')
  }

  const handleConversationUpdate = (history) => {
    setConversationHistory(history)
  }

  const handleExtractPreferences = async () => {
    if (!participantName || !role || conversationHistory.length === 0) {
      alert('Please start a conversation first and set participant name and role')
      return
    }

    try {
      const response = await fetch('/api/extract-preferences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          conversation_history: conversationHistory,
          participant_name: participantName,
          role: role,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to extract preferences')
      }

      const data = await response.json()
      setExtractedPreferences(data)

      // Also format the output
      const formatResponse = await fetch('/api/format-output', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (formatResponse.ok) {
        const formatData = await formatResponse.json()
        setFormattedOutput(formatData.formatted_output)
      }
    } catch (error) {
      console.error('Error extracting preferences:', error)
      alert('Error extracting preferences: ' + error.message)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Policy Agent - User Interaction</h1>
        <p>Engage with the agent to express your preferences and concerns</p>
      </header>

      <div className="app-content">
        <div className="left-panel">
          <ParticipantForm
            onSubmit={handleParticipantSubmit}
            currentName={participantName}
            currentRole={role}
          />

          {participantName && role && (
            <ChatInterface
              participantName={participantName}
              role={role}
              onConversationUpdate={handleConversationUpdate}
              onExtractPreferences={handleExtractPreferences}
            />
          )}
        </div>

        <div className="right-panel">
          <PreferencesOutput
            preferences={extractedPreferences}
            formattedOutput={formattedOutput}
          />
        </div>
      </div>
    </div>
  )
}

export default App

