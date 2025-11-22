import { useState } from 'react'
import Question1Survival from './questions/Question1Survival'
import Question2SafetyTrade from './questions/Question2SafetyTrade'
import Question3StaffDilemma from './questions/Question3StaffDilemma'
import './QuestionFlow.css'

function QuestionFlow({ userDescription, onComplete }) {
  const [currentQuestion, setCurrentQuestion] = useState(1)
  const [answers, setAnswers] = useState({})

  const handleAnswer = (questionNum, answer, followUpAnswer = null) => {
    setAnswers(prev => ({
      ...prev,
      [questionNum]: { answer, followUpAnswer }
    }))
    
    if (questionNum < 3) {
      setCurrentQuestion(questionNum + 1)
    } else {
      // All questions answered
      finalizeAnswers()
    }
  }

  const finalizeAnswers = async () => {
    try {
      // Format answers for backend
      const formattedAnswers = Object.entries(answers).map(([qNum, data]) => {
        const questionText = {
          1: "The Survival Slider - Capacity and subsidy preferences",
          2: "The Safety Investment Trade - Investment vs capacity trade-off",
          3: "The Staff Protection Dilemma - Staff accommodation choices"
        }[qNum] || `Question ${qNum}`
        
        return {
          question: questionText,
          answer: typeof data.answer === 'object' ? JSON.stringify(data.answer) : data.answer,
          followUpAnswer: data.followUpAnswer ? (typeof data.followUpAnswer === 'object' ? JSON.stringify(data.followUpAnswer) : data.followUpAnswer) : null
        }
      })

      const response = await fetch('/api/finalize-preferences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_name: 'Restaurant Owner',
          user_role: 'Business_Owner',
          user_description: userDescription,
          answers: formattedAnswers,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        onComplete(data)
      } else {
        onComplete({ answers })
      }
    } catch (error) {
      console.error('Error finalizing:', error)
      onComplete({ answers })
    }
  }

  return (
    <div className="question-flow">
      <div className="progress-bar-container">
        {[1, 2, 3, 4, 5, 6].map((block) => (
          <div
            key={block}
            className={`progress-block ${block <= currentQuestion * 2 ? 'filled' : ''}`}
          />
        ))}
      </div>

      <div className="question-container">
        {currentQuestion === 1 && (
          <Question1Survival
            onAnswer={(answer, followUp) => handleAnswer(1, answer, followUp)}
          />
        )}
        {currentQuestion === 2 && (
          <Question2SafetyTrade
            onAnswer={(answer, followUp) => handleAnswer(2, answer, followUp)}
          />
        )}
        {currentQuestion === 3 && (
          <Question3StaffDilemma
            onAnswer={(answer, followUp) => handleAnswer(3, answer, followUp)}
          />
        )}
      </div>
    </div>
  )
}

export default QuestionFlow

