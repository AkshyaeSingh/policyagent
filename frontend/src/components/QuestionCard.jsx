import { useState, useRef, useEffect } from 'react'
import './QuestionCard.css'

function QuestionCard({ question, isActive, onAnswer, zIndex }) {
  // question is now an object with type, question text, options, etc.
  const questionType = question?.type || 'yes_no'
  const questionText = question?.question || question || ''
  
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [rotation, setRotation] = useState(0)
  const [startPos, setStartPos] = useState(null)
  const [sliderValue, setSliderValue] = useState(50)
  const [selectedOption, setSelectedOption] = useState(null)
  const [allocationValues, setAllocationValues] = useState({})
  const cardRef = useRef(null)

  useEffect(() => {
    if (isActive) {
      setPosition({ x: 0, y: 0 })
      setRotation(0)
      setSliderValue(50)
      setSelectedOption(null)
      // Initialize allocation values if needed
      if (questionType === 'allocation' && question.options) {
        const initial = {}
        question.options.forEach(opt => {
          initial[opt] = 0
        })
        setAllocationValues(initial)
      }
    }
  }, [isActive, questionType, question])

  // Swipe handlers for trade_off and yes_no types
  const handleTouchStart = (e) => {
    if (!isActive || (questionType !== 'trade_off' && questionType !== 'yes_no')) return
    const touch = e.touches[0]
    setStartPos({ x: touch.clientX, y: touch.clientY })
  }

  const handleTouchMove = (e) => {
    if (!isActive || !startPos || (questionType !== 'trade_off' && questionType !== 'yes_no')) return
    const touch = e.touches[0]
    const deltaX = touch.clientX - startPos.x
    const deltaY = touch.clientY - startPos.y

    setPosition({ x: deltaX, y: deltaY })
    setRotation(deltaX * 0.1)
  }

  const handleTouchEnd = () => {
    if (!isActive || !startPos || (questionType !== 'trade_off' && questionType !== 'yes_no')) return

    const threshold = 100
    if (Math.abs(position.x) > threshold) {
      if (position.x > 0) {
        if (questionType === 'trade_off') {
          onAnswer('option_b', { question, answer: 'option_b' })
        } else {
          onAnswer('agree', { question, answer: 'yes' })
        }
      } else {
        if (questionType === 'trade_off') {
          onAnswer('option_a', { question, answer: 'option_a' })
        } else {
          onAnswer('disagree', { question, answer: 'no' })
        }
      }
    } else {
      setPosition({ x: 0, y: 0 })
      setRotation(0)
    }
    setStartPos(null)
  }

  const handleMouseDown = (e) => {
    if (!isActive || (questionType !== 'trade_off' && questionType !== 'yes_no')) return
    setStartPos({ x: e.clientX, y: e.clientY })
  }

  const handleMouseMove = (e) => {
    if (!isActive || !startPos || (questionType !== 'trade_off' && questionType !== 'yes_no')) return
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
    onAnswer('slider_value', { question, answer: sliderValue, value: sliderValue })
  }

  const handleOptionSelect = (option) => {
    setSelectedOption(option)
    onAnswer('option_selected', { question, answer: option })
  }

  const handleAllocationChange = (option, value) => {
    const newValues = { ...allocationValues, [option]: parseInt(value) || 0 }
    setAllocationValues(newValues)
  }

  const handleAllocationSubmit = () => {
    const total = Object.values(allocationValues).reduce((sum, val) => sum + val, 0)
    const constraint = question.constraint || 100
    if (Math.abs(total - constraint) < 5) { // Allow small tolerance
      onAnswer('allocation', { question, answer: allocationValues })
    } else {
      alert(`Total must equal ${constraint}. Current: ${total}`)
    }
  }

  if (!isActive) return null

  const renderQuestionContent = () => {
    switch (questionType) {
      case 'trade_off':
        // Handle both object format (option_A: {caption: "..."}) and string format
        const optionA = question.option_A?.caption || question.option_A || "Option A"
        const optionB = question.option_B?.caption || question.option_B || "Option B"
        
        return (
          <div className="trade-off-question">
            <div className="question-text">{questionText}</div>
            <div className="trade-off-options">
              <div className="option option-a">
                <div className="option-label">Option A</div>
                <div className="option-text">{optionA}</div>
              </div>
              <div className="option-divider">VS</div>
              <div className="option option-b">
                <div className="option-label">Option B</div>
                <div className="option-text">{optionB}</div>
              </div>
            </div>
            <div className="swipe-hint">Swipe left for Option A, right for Option B</div>
          </div>
        )

      case 'slider':
        return (
          <div className="slider-question">
            <div className="question-text">{questionText}</div>
            <div className="slider-container">
              <input
                type="range"
                min={question.range?.[0] || 0}
                max={question.range?.[1] || 100}
                value={sliderValue}
                onChange={handleSliderChange}
                className="slider"
              />
              <div className="slider-labels">
                <span>{question.range?.[0] || 0}</span>
                <span className="slider-value">{sliderValue}{question.unit ? ` ${question.unit}` : ''}</span>
                <span>{question.range?.[1] || 100}</span>
              </div>
              <button onClick={handleSliderSubmit} className="slider-submit">
                Submit
              </button>
            </div>
          </div>
        )

      case 'numerical':
        return (
          <div className="numerical-question">
            <div className="question-text">{questionText}</div>
            <div className="options-grid">
              {question.options?.map((option, idx) => (
                <button
                  key={idx}
                  className={`option-button ${selectedOption === option ? 'selected' : ''}`}
                  onClick={() => handleOptionSelect(option)}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
        )

      case 'yes_no':
        return (
          <div className="yes-no-question">
            <div className="question-text">{questionText}</div>
            {question.context && <div className="question-context">{question.context}</div>}
            <div className="swipe-hint">Swipe left for No, right for Yes</div>
          </div>
        )

      case 'allocation':
        const total = Object.values(allocationValues).reduce((sum, val) => sum + val, 0)
        const constraint = question.constraint || 100
        return (
          <div className="allocation-question">
            <div className="question-text">{questionText}</div>
            <div className="allocation-container">
              {question.options?.map((option, idx) => (
                <div key={idx} className="allocation-item">
                  <label>{option}</label>
                  <input
                    type="range"
                    min="0"
                    max={constraint}
                    value={allocationValues[option] || 0}
                    onChange={(e) => handleAllocationChange(option, e.target.value)}
                    className="allocation-slider"
                  />
                  <span className="allocation-value">{allocationValues[option] || 0}</span>
                </div>
              ))}
              <div className="allocation-total">
                Total: {total} / {constraint}
              </div>
              <button
                onClick={handleAllocationSubmit}
                className="allocation-submit"
                disabled={Math.abs(total - constraint) > 5}
              >
                Submit
              </button>
            </div>
          </div>
        )

      default:
        return <div className="question-text">{questionText}</div>
    }
  }

  const canSwipe = questionType === 'trade_off' || questionType === 'yes_no'

  return (
    <div
      ref={cardRef}
      className={`question-card ${isActive ? 'active' : ''} ${questionType}`}
      style={{
        transform: canSwipe ? `translate(${position.x}px, ${position.y}px) rotate(${rotation}deg)` : 'none',
        zIndex,
        transition: startPos ? 'none' : 'transform 0.3s ease',
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
        {renderQuestionContent()}
      </div>

      {canSwipe && Math.abs(position.x) > 50 && (
        <div className={`swipe-indicator ${position.x > 0 ? 'swipe-right' : 'swipe-left'}`}>
          {position.x > 0 ? '✓' : '✗'}
        </div>
      )}
    </div>
  )
}

export default QuestionCard
