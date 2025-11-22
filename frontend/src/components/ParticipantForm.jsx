import { useState, useEffect } from 'react'
import './ParticipantForm.css'

function ParticipantForm({ onSubmit, currentName, currentRole }) {
  const [name, setName] = useState(currentName)
  const [role, setRole] = useState(currentRole)

  useEffect(() => {
    setName(currentName)
    setRole(currentRole)
  }, [currentName, currentRole])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (name.trim() && role.trim()) {
      onSubmit(name.trim(), role.trim())
    }
  }

  return (
    <div className="participant-form">
      <h2>Participant Information</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="name">Participant Name:</label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Alice, Bob, Developer"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="role">Role:</label>
          <input
            id="role"
            type="text"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            placeholder="e.g., neighbor, developer, Noise-Sensitive"
            required
          />
        </div>

        <button type="submit" className="submit-btn">
          {currentName ? 'Update Participant' : 'Start Session'}
        </button>
      </form>

      {currentName && (
        <div className="current-participant">
          <p>
            <strong>Current:</strong> {currentName} ({currentRole})
          </p>
        </div>
      )}
    </div>
  )
}

export default ParticipantForm

