import { useState, useEffect, useRef } from 'react'
import QuestionCard from './QuestionCard'
import './SwipeableQuestions.css'

function SwipeableQuestions({ userInfo, onComplete }) {
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [answers, setAnswers] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isGeneratingNext, setIsGeneratingNext] = useState(false)
  const [preferences, setPreferences] = useState({})
  const [policyDimensions, setPolicyDimensions] = useState({})
  const [questionCount, setQuestionCount] = useState(0)
  const MAX_QUESTIONS = 12

  useEffect(() => {
    generateNextQuestion()
  }, [])

  // Preferences are now updated directly in handleAnswer
  // This useEffect is kept for any edge cases but main flow is in handleAnswer

  const generateNextQuestion = async () => {
    setIsGeneratingNext(true)
    try {
      const response = await fetch('/api/generate-next-question', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_name: userInfo.name,
          user_role: userInfo.role,
          user_description: userInfo.description,
          previous_answers: answers,
          current_preferences: preferences,
          question_count: questionCount,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to generate question')
      }

      const data = await response.json()
      
      if (data.question) {
        // Ensure question is an object with type
        const questionObj = typeof data.question === 'string' 
          ? { type: 'yes_no', question: data.question }
          : data.question
        setCurrentQuestion(questionObj)
        setIsLoading(false)
        setIsGeneratingNext(false)
      } else if (data.complete) {
        // AI determined we have enough information
        finalizePreferences(answers)
      } else {
        throw new Error('No question generated')
      }
    } catch (error) {
      console.error('Error generating question:', error)
      // Fallback question
      setCurrentQuestion({ type: 'yes_no', question: "Should masks be required in indoor public spaces?" })
      setIsLoading(false)
      setIsGeneratingNext(false)
    }
  }

  const updatePreferences = async (answersToUse = null) => {
    const answersForUpdate = answersToUse || answers
    try {
      const response = await fetch('/api/update-preferences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_name: userInfo.name,
          user_role: userInfo.role,
          user_description: userInfo.description,
          answers: answersForUpdate,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        const updatedPrefs = data.preferences || {}
        setPreferences(updatedPrefs)
        return updatedPrefs
      }
      return preferences
    } catch (error) {
      console.error('Error updating preferences:', error)
      return preferences
    }
  }

  const handleAnswer = async (answerType, answerData = {}) => {
    const newAnswer = {
      question: currentQuestion,
      answer: answerData.answer || answerType,
      answer_type: answerType,
      slider_value: answerData.value,
      timestamp: new Date().toISOString(),
    }
    const newAnswers = [...answers, newAnswer]
    const newCount = questionCount + 1
    
    setAnswers(newAnswers)
    setQuestionCount(newCount)
    setCurrentQuestion(null)
    setIsGeneratingNext(true)

    // Check if we've reached max questions
    if (newCount >= MAX_QUESTIONS) {
      finalizePreferences(newAnswers)
      return
    }

    // Update preferences first, then generate next question
    const updatedPrefs = await updatePreferences(newAnswers)
    
    try {
      const response = await fetch('/api/generate-next-question', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_name: userInfo.name,
          user_role: userInfo.role,
          user_description: userInfo.description,
          previous_answers: newAnswers,
          current_preferences: updatedPrefs,
          policy_dimensions: policyDimensions,
          question_count: newCount,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to generate question')
      }

      const data = await response.json()
      
      if (data.complete) {
        // AI determined we have enough information
        finalizePreferences(newAnswers)
      } else if (data.question) {
        // Ensure question is an object with type
        const questionObj = typeof data.question === 'string' 
          ? { type: 'yes_no', question: data.question }
          : data.question
        setCurrentQuestion(questionObj)
        setIsGeneratingNext(false)
      } else {
        throw new Error('No question generated')
      }
    } catch (error) {
      console.error('Error generating next question:', error)
      // Fallback question
      setCurrentQuestion({ type: 'yes_no', question: "Should masks be required in indoor public spaces?" })
      setIsGeneratingNext(false)
    }
  }

  const finalizePreferences = async (finalAnswers) => {
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
          answers: finalAnswers,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to finalize preferences')
      }

      const data = await response.json()
      onComplete(data)
    } catch (error) {
      console.error('Error finalizing preferences:', error)
      // Still complete with what we have
      onComplete({
        participant_name: userInfo.name,
        role: userInfo.role,
        preferences: preferences,
      })
    }
  }

  if (isLoading && !currentQuestion) {
    return (
      <div className="swipeable-questions loading">
        <div className="loading-spinner"></div>
        <p>Generating your first question...</p>
      </div>
    )
  }

  if (!currentQuestion && !isGeneratingNext) {
    return (
      <div className="swipeable-questions error">
        <p>No question available. Please try again.</p>
      </div>
    )
  }

  const progress = ((questionCount + 1) / MAX_QUESTIONS) * 100

  return (
    <div className="swipeable-questions">
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${progress}%` }}></div>
      </div>

      <div className="question-counter">
        Question {questionCount + 1}
      </div>

      <div className="cards-container">
        {isGeneratingNext ? (
          <div className="generating-next">
            <div className="loading-spinner"></div>
            <p>Understanding your preferences...</p>
          </div>
        ) : currentQuestion && (
          <QuestionCard
            key={questionCount}
            question={currentQuestion}
            isActive={true}
            onAnswer={handleAnswer}
            zIndex={10}
          />
        )}
      </div>

      <div className="swipe-hints">
        <div className="hint-left">
          <span className="hint-icon">👈</span>
          <span>Disagree</span>
        </div>
        <div className="hint-right">
          <span>Agree</span>
          <span className="hint-icon">👉</span>
        </div>
      </div>
    </div>
  )
}

export default SwipeableQuestions

