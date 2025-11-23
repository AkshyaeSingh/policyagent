import { useState, useRef } from 'react'
import './Question2SafetyTrade.css'

function Question2SafetyTrade({ onAnswer }) {
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [rotation, setRotation] = useState(0)
  const [startPos, setStartPos] = useState(null)
  const [hasSwiped, setHasSwiped] = useState(false)
  const [selectedOption, setSelectedOption] = useState(null)
  const [showFollowUp, setShowFollowUp] = useState(false)
  const cardRef = useRef(null)

  const handleTouchStart = (e) => {
    const touch = e.touches[0]
    setStartPos({ x: touch.clientX, y: touch.clientY })
  }

  const handleTouchMove = (e) => {
    if (!startPos) return
    const touch = e.touches[0]
    const deltaX = touch.clientX - startPos.x
    const deltaY = touch.clientY - startPos.y

    setPosition({ x: deltaX, y: deltaY })
    setRotation(deltaX * 0.1)
  }

  const handleTouchEnd = () => {
    if (!startPos) return

    const threshold = 100
    if (Math.abs(position.x) > threshold) {
      const option = position.x > 0 ? 'option_b' : 'option_a'
      setSelectedOption(option)
      setHasSwiped(true)
      setTimeout(() => {
        setShowFollowUp(true)
      }, 500)
    } else {
      setPosition({ x: 0, y: 0 })
      setRotation(0)
    }
    setStartPos(null)
  }

  const handleMouseDown = (e) => {
    setStartPos({ x: e.clientX, y: e.clientY })
  }

  const handleMouseMove = (e) => {
    if (!startPos) return
    const deltaX = e.clientX - startPos.x
    const deltaY = e.clientY - startPos.y
    setPosition({ x: deltaX, y: deltaY })
    setRotation(deltaX * 0.1)
  }

  const handleMouseUp = () => {
    handleTouchEnd()
  }

  const handleFollowUpSubmit = (accept) => {
    onAnswer(selectedOption, { governmentCoverage50: accept })
  }

  if (showFollowUp) {
    return (
      <div className="question-card safety-trade-question">
        <div className="follow-up-content">
          <h2 className="question-title">Follow-up</h2>
          <p className="follow-up-text">
            What if the government covered 50% of the safety investment?
          </p>
          <div className="follow-up-buttons">
            <button
              className="follow-up-button accept"
              onClick={() => handleFollowUpSubmit(true)}
            >
              Accept
            </button>
            <button
              className="follow-up-button decline"
              onClick={() => handleFollowUpSubmit(false)}
            >
              Decline
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div
      ref={cardRef}
      className="question-card safety-trade-question"
    >
      <div className="question-header">
        <h2 className="question-title">The Safety Investment Trade</h2>
        <p className="question-subtitle">
          Would you rather: <strong>A</strong> - Invest $10,000 in HEPA filters and UV systems to operate at 75% capacity, <strong>B</strong> - Operate at 40% capacity with basic masks required?
        </p>
      </div>

      <div className="split-screen-horizontal">
        <div 
          className={`option-panel option-a ${selectedOption === 'option_a' ? 'selected' : ''}`}
          onClick={() => {
            setSelectedOption('option_a')
            setTimeout(() => setShowFollowUp(true), 500)
          }}
        >
          <div className="option-image-container">
            <img 
              src="/images/17.33.png" 
              alt="Option A" 
              className="option-image"
              onError={(e) => {
                e.target.style.display = 'none'
              }}
            />
            <div className="option-label-overlay">A</div>
          </div>
          <div className="option-content">
            <div className="option-title">High Investment, More Freedom</div>
            <div className="option-details">
              <p>• $10,000 investment</p>
              <p>• HEPA filters + UV systems</p>
              <p>• 75% capacity</p>
            </div>
          </div>
        </div>

        <div 
          className={`option-panel option-b ${selectedOption === 'option_b' ? 'selected' : ''}`}
          onClick={() => {
            setSelectedOption('option_b')
            setTimeout(() => setShowFollowUp(true), 500)
          }}
        >
          <div className="option-image-container">
            <img 
              src="/images/17.10.png" 
              alt="Option B" 
              className="option-image"
              onError={(e) => {
                e.target.style.display = 'none'
              }}
            />
            <div className="option-label-overlay">B</div>
          </div>
          <div className="option-content">
            <div className="option-title">Low Investment, Strict Limits</div>
            <div className="option-details">
              <p>• No investment</p>
              <p>• Basic masks required</p>
              <p>• 40% capacity</p>
            </div>
          </div>
        </div>
      </div>

      <div className="swipe-hint">
        Tap Option A or B to select
      </div>
    </div>
  )
}

export default Question2SafetyTrade
