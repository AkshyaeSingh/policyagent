import { useState } from 'react'
import './InitialInput.css'

function InitialInput({ onSubmit }) {
  const [name, setName] = useState('')
  const [role, setRole] = useState('')
  const [description, setDescription] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim() || !role.trim() || !description.trim()) {
      alert('Please fill in all fields')
      return
    }

    setIsSubmitting(true)
    
    // Small delay for UX
    setTimeout(() => {
      onSubmit({
        name: name.trim(),
        role: role.trim(),
        description: description.trim()
      })
      setIsSubmitting(false)
    }, 300)
  }

  return (
    <div className="initial-input">
      <div className="initial-input-container">
        <div className="header">
          <h1>Policy Agent</h1>
          <p>Tell us about yourself</p>
        </div>

        <form onSubmit={handleSubmit} className="input-form">
          <div className="input-group">
            <label>Your Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Alice"
              required
            />
          </div>

          <div className="input-group">
            <label>Your Role</label>
            <input
              type="text"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="e.g., Noise-Sensitive neighbor"
              required
            />
          </div>

          <div className="input-group">
            <label>How does this issue affect you?</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your situation and concerns. For example: 'I live next to the proposed construction site and I'm concerned about noise levels, especially in the mornings when I work from home.'"
              rows="5"
              required
            />
          </div>

          <button 
            type="submit" 
            className="submit-btn"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Loading...' : 'Continue'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default InitialInput

