import { useState } from 'react'
import Question1Survival from './questions/Question1Survival'
import Question2SafetyTrade from './questions/Question2SafetyTrade'
import Question3StaffDilemma from './questions/Question3StaffDilemma'
import './DemoQuestions.css'

function DemoQuestions({ userInfo, onComplete }) {
  const [currentQuestion, setCurrentQuestion] = useState(1)
  const [answers, setAnswers] = useState({})

  const handleAnswer = (questionNum, answer) => {
    setAnswers(prev => ({
      ...prev,
      [questionNum]: answer
    }))

    if (questionNum < 3) {
      setCurrentQuestion(questionNum + 1)
    } else {
      // All questions answered
      finalizeAnswers({ ...answers, [questionNum]: answer })
    }
  }

  const finalizeAnswers = async (finalAnswers) => {
    try {
      const response = await fetch('/api/finalize-preferences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_name: userInfo.name,
          user_role: userInfo.role,
          user_description: userInfo.description,
          answers: Object.values(finalAnswers).map((ans, idx) => ({
            question: `Question ${idx + 1}`,
            answer: ans,
            timestamp: new Date().toISOString(),
          })),
        }),
      })

      if (response.ok) {
        const data = await response.json()
        onComplete(data)
      } else {
        onComplete({
          participant_name: userInfo.name,
          role: userInfo.role,
          preferences: {},
        })
      }
    } catch (error) {
      console.error('Error finalizing:', error)
      onComplete({
        participant_name: userInfo.name,
        role: userInfo.role,
        preferences: {},
      })
    }
  }

  return (
    <div className="demo-questions">
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
            onAnswer={(answer) => handleAnswer(1, answer)}
          />
        )}
        {currentQuestion === 2 && (
          <Question2SafetyTrade
            onAnswer={(answer) => handleAnswer(2, answer)}
          />
        )}
        {currentQuestion === 3 && (
          <Question3StaffDilemma
            onAnswer={(answer) => handleAnswer(3, answer)}
          />
        )}
      </div>
    </div>
  )
}

export default DemoQuestions

