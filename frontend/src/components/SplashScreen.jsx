import { useState, useEffect } from 'react'
import AtomIcon from './AtomIcon'
import './SplashScreen.css'

function SplashScreen({ onComplete }) {
  const [displayedText, setDisplayedText] = useState('')
  const fullText = "The Reddot virus has just infected the state of California. This virus is 30% more contagious than previous strains, with symptoms appearing within 24-48 hours. Hospitals are preparing for increased capacity needs, and state officials are coordinating rapid response measures. Your input will help shape policy decisions that balance individual autonomy with collective safety."
  const [showButton, setShowButton] = useState(false)

  useEffect(() => {
    let currentIndex = 0
    const typingSpeed = 10 // milliseconds per character (much faster)

    const typeWriter = () => {
      if (currentIndex < fullText.length) {
        setDisplayedText(fullText.slice(0, currentIndex + 1))
        currentIndex++
        setTimeout(typeWriter, typingSpeed)
      } else {
        setShowButton(true)
      }
    }

    // Start typing after a short delay
    const timer = setTimeout(typeWriter, 500)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="splash-screen">
      <div className="splash-content">
        <AtomIcon />
        <h1 className="app-title">Coordinal</h1>
        
        <div className="typewriter-container">
          <p className="typewriter-text">{displayedText}</p>
          {displayedText.length < fullText.length && (
            <span className="cursor">|</span>
          )}
        </div>

        {showButton && (
          <button className="enter-button" onClick={onComplete}>
            Enter
          </button>
        )}
      </div>
    </div>
  )
}

export default SplashScreen
