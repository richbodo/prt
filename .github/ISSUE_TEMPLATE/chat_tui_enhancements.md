# Chat TUI Enhancements

## Summary
Enhance the chat screen user experience with progress indicators, LLM status checking, and improved feedback.

## Current Issues
1. **No progress indication** - Long LLM responses leave users wondering if the app crashed
2. **No LLM status checking** - Users don't know if Ollama is available before trying to chat
3. **Confusing status text** - "Enhanced with Ollama AI (if available)" is unclear

## Requested Enhancements

### 1. Progress Indicator
- **Behavior**: Mimic Claude Code's progress display
- **Visual**: Fun nonsense verbs with spinning ASCII symbol (e.g., spinning slash `/|\-`)
- **Examples**:
  - "🤔 Pondering your request..."
  - "🧠 Consulting the knowledge base..."
  - "💭 Formulating response..."
  - "🔍 Searching through contacts..."
- **Technical**: Show progress meter during LLM API calls

### 2. LLM Status Checking
- **Quick responsiveness check** before accepting user input
- **Status line display** showing LLM availability:
  - ✅ "LLM: Online" (green)
  - ❌ "LLM: Offline" (red) 
  - ⚠️ "LLM: Checking..." (yellow)
- **Remove confusing text**:
  - Remove: "Enhanced with Ollama AI (if available)"
  - Remove: "When Ollama is running, I provide..."
- **Replace with clear status**: Dynamic status line

### 3. User Experience Improvements
- **Input validation** - Don't accept queries if LLM is offline
- **Graceful degradation** - Clear messaging when falling back to local processing
- **Status updates** - Real-time LLM availability updates

## Acceptance Criteria
- [ ] Progress indicator shows during LLM processing with fun messages
- [ ] Spinning ASCII symbol animates during processing
- [ ] LLM status check happens before accepting input
- [ ] Status line shows current LLM availability
- [ ] Confusing "if available" text removed
- [ ] Clear feedback when LLM is offline vs online
- [ ] No user confusion about app responsiveness

## Technical Notes
- Progress indicator should be non-blocking
- Status checking should be lightweight (quick ping/health check)
- ASCII animation should be smooth and not distracting
- Consider using Textual's LoadingIndicator or custom spinner widget

## Priority
**Medium** - Improves user experience but doesn't break functionality

## Labels
- enhancement
- tui
- chat
- user-experience
