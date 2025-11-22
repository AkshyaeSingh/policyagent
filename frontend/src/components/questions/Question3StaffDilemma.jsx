import { useState } from 'react'
import './Question3StaffDilemma.css'

function Question3StaffDilemma({ onAnswer }) {
  const [selectedOption, setSelectedOption] = useState(null)
  const [showFollowUp, setShowFollowUp] = useState(false)

  const handleOptionSelect = (option) => {
    setSelectedOption(option)
    setTimeout(() => {
      setShowFollowUp(true)
    }, 500)
  }

  const handleFollowUpSubmit = (answer) => {
    onAnswer(selectedOption, { threeStaffImmunocompromised: answer })
  }

  if (showFollowUp) {
    return (
      <div className="question-card staff-dilemma-question">
        <div className="follow-up-content">
          <h2 className="question-title">Follow-up</h2>
          <p className="follow-up-text">
            What if 3 of your 12 staff were immunocompromised?
          </p>
          <div className="follow-up-options">
            <button
              className="follow-up-option"
              onClick={() => handleFollowUpSubmit('same_accommodation')}
            >
              Apply same accommodation to all 3
            </button>
            <button
              className="follow-up-option"
              onClick={() => handleFollowUpSubmit('different_approach')}
            >
              Find a different approach
            </button>
            <button
              className="follow-up-option"
              onClick={() => handleFollowUpSubmit('reduce_capacity')}
            >
              Reduce overall capacity to 40%
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="question-card staff-dilemma-question">
      <div className="question-header">
        <h2 className="question-title">The Staff Protection Dilemma</h2>
        <p className="question-subtitle">
          A staff member is immunocompromised. Which accommodation would you choose?
        </p>
      </div>

      <div className="options-grid">
        <button
          className={`option-block option-a ${selectedOption === 'option_a' ? 'selected' : ''}`}
          onClick={() => handleOptionSelect('option_a')}
        >
          <div className="option-icon">🛡️</div>
          <div className="option-label">Option A</div>
          <div className="option-title">Install Protection</div>
          <div className="option-details">
            <p>$15,000 plexiglass barriers</p>
            <p>+ HEPA filters for their section</p>
          </div>
        </button>

        <button
          className={`option-block option-b ${selectedOption === 'option_b' ? 'selected' : ''}`}
          onClick={() => handleOptionSelect('option_b')}
        >
          <div className="option-icon">💰</div>
          <div className="option-label">Option B</div>
          <div className="option-title">Paid Leave</div>
          <div className="option-details">
            <p>70% salary to stay home</p>
            <p>Until case rates drop below 10/100k</p>
          </div>
        </button>

        <button
          className={`option-block option-c ${selectedOption === 'option_c' ? 'selected' : ''}`}
          onClick={() => handleOptionSelect('option_c')}
        >
          <div className="option-icon">📏</div>
          <div className="option-label">Option C</div>
          <div className="option-title">Reduce Capacity</div>
          <div className="option-details">
            <p>Reduce overall capacity to 40%</p>
            <p>So everyone has more space</p>
          </div>
        </button>
      </div>
    </div>
  )
}

export default Question3StaffDilemma

