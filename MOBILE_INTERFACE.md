# Mobile Tinder-Style Interface

## Overview

The frontend has been completely redesigned as a mobile-first, Tinder-style interface for capturing user preferences through swipeable question cards.

## User Flow

### 1. Initial Input Screen
- User enters their name (e.g., "Alice")
- User enters their role (e.g., "Noise-Sensitive neighbor")
- User describes how the issue affects them
- Submit to continue

### 2. Swipeable Questions
- Questions are generated based on user's initial input
- One question card at a time (Tinder-style)
- User can:
  - **Swipe Left** 👈 = Disagree
  - **Swipe Right** 👉 = Agree
  - **Tap "Rank"** 📊 = Use slider to rank (0-100)
- Progress bar shows completion
- Questions are contextual and relevant to their role

### 3. Live Preference Extraction
- As user answers questions, preferences are extracted in the **backend** (not shown to user)
- Preferences are logged to backend console in real-time
- Final preferences are formatted and ready for agent-agent analysis

## Features

### Mobile-First Design
- Optimized for mobile phones
- Touch gestures for swiping
- Responsive layout
- Full-screen experience

### Question Generation
- AI-generated questions based on user context
- Questions focus on policy trade-offs
- Examples:
  - "You'd accept a 10-story building on your block if it meant 20% lower rents"
  - "You care about the noise of the construction site"
  - "You care specifically about noise during the morning"

### Answer Methods
1. **Swipe Left** - Disagree
2. **Swipe Right** - Agree
3. **Slider** - Rank from 0-100 (Disagree to Agree)

### Backend Processing
- Preferences extracted incrementally as questions are answered
- Logged to backend console (not shown to user)
- Final output formatted as:
```
PARTICIPANTS:

Alice (Noise-Sensitive neighbor):
  - noise_level_below_db: 60.0
  - no_construction_before: 8am
  - compensation_minimum: 3000.0
```

## API Endpoints

### `/api/generate-questions`
- Generates contextual questions based on user input
- Input: `user_name`, `user_role`, `user_description`
- Output: Array of question strings

### `/api/update-preferences`
- Updates preferences incrementally as questions are answered
- Input: User info + array of answers
- Output: Current preferences object
- **Logs to backend console** (not shown to user)

### `/api/finalize-preferences`
- Finalizes preferences after all questions answered
- Input: User info + all answers
- Output: Final formatted preferences
- **Prints final output to backend console**

## Running the Application

1. **Start Backend:**
```bash
cd user-agent-api
source venv/bin/activate
python main.py
```

2. **Start Frontend:**
```bash
cd frontend
npm install  # if not done already
npm run dev
```

3. **Open on Mobile:**
- Open `http://localhost:5173` on your phone
- Or use browser dev tools mobile emulation

## Viewing Preferences

Preferences are extracted and logged in the **backend console** (terminal where you ran `python main.py`). They are NOT shown to the user in the frontend - this keeps the interface clean and focused.

The final output will appear in the backend console when all questions are answered, formatted exactly as your coworker needs for agent-agent analysis.

