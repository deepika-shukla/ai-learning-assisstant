# 🚀 Future Enhancements

A collection of ideas for future improvements to the AI Learning Assistant.

---

## 📊 Priority: High

### 1. Smart Resource Recommendations
**Status:** 🟡 Planned  
**Complexity:** Medium

When user asks "which video is best?", AI should:
- Store fetched resources in state (remember what was shown)
- Fetch metadata: views, likes, duration, channel info
- Recommend based on popularity & relevance
- Compare multiple resources intelligently

```python
# Example implementation
state["last_resources"] = {
    "videos": [...with views, duration...],
    "fetched_at": timestamp
}
```

---

### 2. Voice Input/Output
**Status:** 🔴 Not Started  
**Complexity:** High

- Add speech-to-text for voice commands
- Text-to-speech for AI responses
- Libraries: `speech_recognition`, `pyttsx3` or OpenAI Whisper

---

### 3. Progress Persistence Across Sessions
**Status:** 🟡 Partial (SQLite exists)  
**Complexity:** Low

- Save completed days permanently
- Resume learning from where user left off
- Track historical learning data

---

## 📊 Priority: Medium

### 4. Multi-Language Support
**Status:** 🔴 Not Started  
**Complexity:** Medium

- Detect user's language automatically
- Generate curriculum in user's language
- Support: Hindi, Spanish, French, etc.

---

### 5. PDF/Document Export
**Status:** 🔴 Not Started  
**Complexity:** Low

- Export curriculum as PDF
- Export progress reports
- Libraries: `reportlab`, `fpdf`

---

### 6. Spaced Repetition System
**Status:** 🔴 Not Started  
**Complexity:** High

- Track what user has learned
- Schedule review sessions
- Implement SM-2 algorithm for optimal retention

---

### 7. Collaborative Learning
**Status:** 🔴 Not Started  
**Complexity:** High

- Multiple users learning same topic
- Share progress with study buddies
- Group quizzes and challenges

---

### 8. Integration with Note-Taking Apps
**Status:** 🔴 Not Started  
**Complexity:** Medium

- Export to Notion
- Sync with Obsidian
- Save to Google Docs

---

## 📊 Priority: Low (Nice to Have)

### 9. Gamification
**Status:** 🔴 Not Started  
**Complexity:** Medium

- Badges for completing days
- Streaks for consistent learning
- Leaderboards (if multi-user)
- XP points system

---

### 10. Code Execution Sandbox
**Status:** 🔴 Not Started  
**Complexity:** High

- Let users run code directly in the app
- Verify quiz answers with actual code execution
- Libraries: `docker`, `subprocess` with sandbox

---

### 11. Calendar Integration
**Status:** 🔴 Not Started  
**Complexity:** Medium

- Add learning tasks to Google Calendar
- Set reminders for daily learning
- Sync with Apple Calendar

---

### 12. Mobile App
**Status:** 🔴 Not Started  
**Complexity:** Very High

- React Native or Flutter app
- Same backend, mobile frontend
- Push notifications for reminders

---

### 13. AI Tutor Chat History
**Status:** 🔴 Not Started  
**Complexity:** Low

- Save all conversations
- Search past Q&A
- Export chat history

---

### 14. Custom Learning Paths
**Status:** 🔴 Not Started  
**Complexity:** Medium

- Pre-built paths: "Become a Python Developer"
- Combine multiple topics
- Certification-style completion

---

### 15. Video Summarization
**Status:** 🔴 Not Started  
**Complexity:** High

- Fetch YouTube transcript
- Summarize with LLM
- Extract key points from videos

---

## 🐛 Known Issues to Fix

1. **Quiz grading edge cases** - Multiple answers not always parsed correctly
2. **Session timeout** - Long idle sessions lose state
3. **API rate limits** - YouTube/GitHub may hit limits

---

## 📝 Notes

- Keep features modular (separate services)
- Write tests before implementing
- Document all new APIs
- Update README after each feature

---

## ✅ Completed Features

- [x] Multi-agent LangGraph workflow
- [x] 12 specialized agents
- [x] YouTube, Wikipedia, GitHub integration
- [x] Web search (DuckDuckGo)
- [x] Thinking indicators
- [x] Duration extraction from natural language
- [x] Two-tier routing (keyword + LLM)
- [x] CLI with Rich formatting
- [x] Streamlit GUI
- [x] FastAPI REST API
- [x] JWT Authentication
- [x] SQLite persistence
- [x] Docker support
- [x] CI/CD pipeline

---

*Last updated: January 2026*
