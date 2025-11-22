import { useState } from 'react'
import './Question1Survival.css'

function Question1Survival({ onAnswer }) {
  const [capacity, setCapacity] = useState(60)
  const [subsidy, setSubsidy] = useState(0)
  const [showFollowUp, setShowFollowUp] = useState(false)

  // Inverse relationship: lower capacity = higher subsidy
  const handleCapacityChange = (value) => {
    const newCapacity = parseInt(value)
    setCapacity(newCapacity)
    // Calculate inverse subsidy: 0% capacity = $20k, 100% capacity = $0
    const newSubsidy = Math.round(20000 * (1 - newCapacity / 100))
    setSubsidy(newSubsidy)
  }

  const handleSubsidyChange = (value) => {
    const newSubsidy = parseInt(value)
    setSubsidy(newSubsidy)
    // Calculate inverse capacity
    const newCapacity = Math.round(100 * (1 - newSubsidy / 20000))
    setCapacity(newCapacity)
  }

  const handleSubmit = () => {
    onAnswer({
      capacity,
      subsidy,
      breakEven: 60
    }, null)
    setShowFollowUp(true)
  }

  const handleFollowUpSubmit = () => {
    onAnswer({
      capacity,
      subsidy,
      breakEven: 60
    }, {
      governmentCoverage50: true
    })
  }

  return (
    <div className="question-card survival-question">
      <div className="question-header">
        <h2 className="question-title">The Survival Slider</h2>
        <p className="question-subtitle">
          Your restaurant breaks even at 60% capacity. Slide to show the lowest capacity you could survive for 3 months if you received monthly subsidies.
        </p>
      </div>

      <div className="restaurant-visual">
        <div className="capacity-overlay" style={{ height: `${100 - capacity}%` }}></div>
        <div className="restaurant-label">Your Restaurant</div>
      </div>

      <div className="sliders-container">
        <div className="slider-group">
          <label className="slider-label">
            Capacity: <span className="slider-value">{capacity}%</span>
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={capacity}
            onChange={(e) => handleCapacityChange(e.target.value)}
            className="slider"
          />
          <div className="slider-range">
            <span>0%</span>
            <span>100%</span>
          </div>
        </div>

        <div className="slider-group">
          <label className="slider-label">
            Monthly Subsidy Needed: <span className="slider-value">${subsidy.toLocaleString()}</span>
          </label>
          <input
            type="range"
            min="0"
            max="20000"
            value={subsidy}
            onChange={(e) => handleSubsidyChange(e.target.value)}
            className="slider"
          />
          <div className="slider-range">
            <span>$0</span>
            <span>$20,000</span>
          </div>
        </div>
      </div>

      {!showFollowUp ? (
        <button className="submit-button" onClick={handleSubmit}>
          Continue
        </button>
      ) : (
        <div className="follow-up">
          <p>What if the government covered 50% of this subsidy?</p>
          <button className="submit-button" onClick={handleFollowUpSubmit}>
            Accept
          </button>
        </div>
      )}
    </div>
  )
}

export default Question1Survival
