import React from 'react'
import ReactDOM from 'react-dom/client'
import NegotiationVisualization from './components/NegotiationVisualization'
import './index.css'

// For testing/demo purposes, you can pass preferences directly
// In production, this would come from the preference collection flow
const demoPreferences = {
  participant_name: 'Healthcare_Worker_Test',
  role: 'neighbor',
  preferences: {
    min_mask_compliance_rate: 85.0,
    min_air_changes_per_hour: 8.0,
    max_acceptable_case_rate: 15.0,
    priority_medical_access: true,
  }
}

// Get preferences from URL params or use demo
const urlParams = new URLSearchParams(window.location.search)
const preferencesParam = urlParams.get('preferences')

let preferences = demoPreferences

if (preferencesParam) {
  try {
    preferences = JSON.parse(decodeURIComponent(preferencesParam))
  } catch (e) {
    console.error('Failed to parse preferences from URL:', e)
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <NegotiationVisualization preferences={preferences} />
  </React.StrictMode>,
)

