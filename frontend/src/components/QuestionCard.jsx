import { useState, useRef, useEffect } from 'react'
import './QuestionCard.css'

function QuestionCard({ question, isActive, onAnswer, zIndex }) {
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [rotation, setRotation] = useState(0)
  const [startPos, setStartPos] = useState(null)
  const [sliderValue, setSliderValue] = useState(50)
  const [showSlider, setShowSlider] = useState(false)
  const cardRef = useRef(null)

  useEffect(() => {
    if (isActive) {
      setPosition({ x: 0, y: 0 })
      setRotation(0)
      setSliderValue(50)
      setShowSlider(false)
    }
  }, [isActive])

  const handleTouchStart = (e) => {
    if (!isActive) return
    const touch = e.touches[0]
    setStartPos({ x: touch.clientX, y: touch.clientY })
  }

  const handleTouchMove = (e) => {
    if (!isActive || !startPos) return
    const touch = e.touches[0]
    const deltaX = touch.clientX - startPos.x
    const deltaY = touch.clientY - startPos.y

    setPosition({ x: deltaX, y: deltaY })
    setRotation(deltaX * 0.1)
  }

  const handleTouchEnd = () => {
    if (!isActive || !startPos) return

    const threshold = 100
    if (Math.abs(position.x) > threshold) {
      // Swipe detected
      if (position.x > 0) {
        onAnswer('agree')
      } else {
        onAnswer('disagree')
      }
    } else {
      // Return to center
      setPosition({ x: 0, y: 0 })
      setRotation(0)
    }
    setStartPos(null)
  }

  const handleMouseDown = (e) => {
    if (!isActive) return
    setStartPos({ x: e.clientX, y: e.clientY })
  }

  const handleMouseMove = (e) => {
    if (!isActive || !startPos) return
    const deltaX = e.clientX - startPos.x
    const deltaY = e.clientY - startPos.y

    setPosition({ x: deltaX, y: deltaY })
    setRotation(deltaX * 0.1)
  }

  const handleMouseUp = () => {
    handleTouchEnd()
  }

  const handleSliderChange = (e) => {
    setSliderValue(parseInt(e.target.value))
  }

  const handleSliderSubmit = () => {
    // Convert slider value (0-100) to answer
    let answer
    if (sliderValue < 30) {
      answer = 'strongly_disagree'
    } else if (sliderValue < 50) {
      answer = 'disagree'
    } else if (sliderValue < 70) {
      answer = 'neutral'
    } else if (sliderValue < 90) {
      answer = 'agree'
    } else {
      answer = 'strongly_agree'
    }
    onAnswer(answer, sliderValue)
  }

  const handleButtonClick = (answer) => {
    onAnswer(answer)
  }

  if (!isActive) return null

  const opacity = isActive ? 1 : 0.5
  const scale = isActive ? 1 : 0.95

  return (
    <div
      ref={cardRef}
      className={`question-card ${isActive ? 'active' : ''}`}
      style={{
        transform: `translate(${position.x}px, ${position.y}px) rotate(${rotation}deg) scale(${scale})`,
        opacity,
        zIndex,
        transition: startPos ? 'none' : 'transform 0.3s ease, opacity 0.3s ease',
      }}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div className="card-content">
        <div className="question-text">{question}</div>

        {showSlider ? (
          <div className="slider-container">
            <input
              type="range"
              min="0"
              max="100"
              value={sliderValue}
              onChange={handleSliderChange}
              className="slider"
            />
            <div className="slider-labels">
              <span>Disagree</span>
              <span>Agree</span>
            </div>
            <button onClick={handleSliderSubmit} className="slider-submit">
              Submit
            </button>
          </div>
        ) : (
          <div className="button-options">
            <button
              className="btn-disagree"
              onClick={() => handleButtonClick('disagree')}
            >
              👈 Disagree
            </button>
            <button
              className="btn-slider"
              onClick={() => setShowSlider(true)}
            >
              📊 Rank
            </button>
            <button
              className="btn-agree"
              onClick={() => handleButtonClick('agree')}
            >
              Agree 👉
            </button>
          </div>
        )}
      </div>

      {Math.abs(position.x) > 50 && (
        <div className={`swipe-indicator ${position.x > 0 ? 'swipe-right' : 'swipe-left'}`}>
          {position.x > 0 ? '✓ Agree' : '✗ Disagree'}
        </div>
      )}
    </div>
  )
}

export default QuestionCard

