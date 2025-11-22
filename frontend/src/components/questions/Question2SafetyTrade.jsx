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
      style={{
        transform: `translate(${position.x}px, ${position.y}px) rotate(${rotation}deg)`,
        transition: startPos ? 'none' : 'transform 0.3s ease',
        opacity: hasSwiped ? 0 : 1,
      }}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div className="question-header">
        <h2 className="question-title">The Safety Investment Trade</h2>
        <p className="question-subtitle">
          Would you rather invest $10,000 in HEPA filters and UV systems to operate at 75% capacity, OR operate at 40% capacity with basic masks required?
        </p>
      </div>

      <div className="split-screen">
        <div className={`option-panel option-a ${selectedOption === 'option_a' ? 'selected' : ''}`}>
          <div className="option-label">Option A</div>
          <div className="option-title">High Investment, More Freedom</div>
          <div className="option-details">
            <p>• $10,000 investment</p>
            <p>• HEPA filters + UV systems</p>
            <p>• 75% capacity</p>
          </div>
        </div>

        <div className="divider">VS</div>

        <div className={`option-panel option-b ${selectedOption === 'option_b' ? 'selected' : ''}`}>
          <div className="option-label">Option B</div>
          <div className="option-title">Low Investment, Strict Limits</div>
          <div className="option-details">
            <p>• No investment</p>
            <p>• Basic masks required</p>
            <p>• 40% capacity</p>
          </div>
        </div>
      </div>

      <div className="swipe-hint">
        Swipe left for Option A, right for Option B
      </div>

      {Math.abs(position.x) > 50 && (
        <div className={`swipe-indicator ${position.x > 0 ? 'swipe-right' : 'swipe-left'}`}>
          {position.x > 0 ? '✓ Option B' : '✓ Option A'}
        </div>
      )}
    </div>
  )
}

export default Question2SafetyTrade
