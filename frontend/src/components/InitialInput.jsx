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
          <p>Airborne Virus Crisis - Tell us about yourself</p>
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
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              required
            >
              <option value="">Select your role...</option>
              <option value="Business_Owner">Business Owner (restaurant/retail)</option>
              <option value="Healthcare_Worker">Healthcare Worker (immunocompromised)</option>
              <option value="Parent">Parent (school-age children)</option>
              <option value="Essential_Worker">Essential Worker (grocery/transit)</option>
              <option value="Remote_Worker">Remote Worker (tech)</option>
              <option value="Elderly_Resident">Elderly Resident (high-risk)</option>
              <option value="Small_Landlord">Small Landlord (property owner)</option>
              <option value="Young_Adult">Young Adult (social/nightlife)</option>
            </select>
          </div>

          <div className="input-group">
            <label>How does this crisis affect you?</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your situation and concerns in the context of an airborne virus crisis. For example: 'I own a restaurant and I'm worried about capacity restrictions affecting my revenue, but I also want to keep my customers safe.'"
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

