import { useState } from 'react'
import './PreferencesOutput.css'

function PreferencesOutput({ preferences, formattedOutput }) {
  const [viewMode, setViewMode] = useState('formatted') // 'formatted' or 'json'

  if (!preferences && !formattedOutput) {
    return (
      <div className="preferences-output">
        <h2>Extracted Preferences</h2>
        <div className="empty-state">
          <p>No preferences extracted yet.</p>
          <p className="hint">Have a conversation with the agent, then click "Extract Preferences" to see the structured output.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="preferences-output">
      <div className="output-header">
        <h2>Extracted Preferences</h2>
        <div className="view-toggle">
          <button
            className={viewMode === 'formatted' ? 'active' : ''}
            onClick={() => setViewMode('formatted')}
          >
            Formatted
          </button>
          <button
            className={viewMode === 'json' ? 'active' : ''}
            onClick={() => setViewMode('json')}
          >
            JSON
          </button>
        </div>
      </div>

      <div className="output-content">
        {viewMode === 'formatted' ? (
          <pre className="formatted-output">{formattedOutput}</pre>
        ) : (
          <pre className="json-output">
            {JSON.stringify(preferences, null, 2)}
          </pre>
        )}
      </div>

      <div className="output-actions">
        <button
          onClick={() => {
            const textToCopy = viewMode === 'formatted' ? formattedOutput : JSON.stringify(preferences, null, 2)
            navigator.clipboard.writeText(textToCopy)
            alert('Copied to clipboard!')
          }}
          className="copy-btn"
        >
          Copy to Clipboard
        </button>
      </div>
    </div>
  )
}

export default PreferencesOutput

