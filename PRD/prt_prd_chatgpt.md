# Personal Relationship Tool (PRT) - Product Requirements Document (PRD)

**Author**: Rich Bodo  
**Date**: June 2025  
**Version**: Draft 0.1

---

## 1. Purpose

To create a client-side encrypted, private, relationship-first contact database that helps individuals maintain meaningful connections, improve mental well-being, and explore a more sovereign and healthy alternative to social networks. This MVP will be developed initially to serve the author and iteratively refined with input from the surrounding tech and decentralization communities.

---

## 2. Problem Statement

Traditional contact databases and social platforms fail to support mental health or genuine connection. They:

- Emphasize quantity over quality  
- Are hostile to privacy  
- Encourage shallow engagement (e.g. feeds, likes)  
- Don’t support relationship context (e.g. trust, recency, emotional depth)

What’s needed is a tool that:

- Centers relationships, not contacts  
- Supports recall and emotional insight  
- Respects privacy absolutely  
- Provides users with actionable support to maintain or rekindle meaningful connections

---

## 3. Goals

### Primary Goals

- Private contact database with strong encryption  
- Relationship-oriented graph structure with decorated links (e.g., trust, contact recency, emotional safety)  
- Fast, intuitive UX for mobile recall and visualization  
- MVP that works offline and serves the creator's personal needs

### Secondary Goals (Post-MVP)

- AI-assisted onboarding of meaningful contacts  
- Relationship maintenance prompts  
- Optional export of small directory views  
- Zero-knowledge architecture for optional decentralized insights

---

## 4. Features

### 4.1 Core Features (MVP)

- **Encrypted Local Database**: Client-side encryption, ideally with no centralized storage  
- **Visual Relationship Graph**: Nodes = People; Edges = Relationships with metadata  
- **Taggable Relationship Qualities**: Trust, frequency, importance, availability, etc.  
- **Mobile-Optimized UI**: Quick lookup of faces/names/groups  
- **Search by Relationship Tags**: Not just by name  
- **Manual Contact Entry**: To reinforce mindfulness and reduce bulk import overwhelm

### 4.2 Post-MVP Features

- **AI-assisted Contact Filtering**: Help user sort contacts to extract meaningful connections  
- **Relationship Maintenance AI**: Suggests outreach, drafts messages  
- **Privacy-Respectful Directory Export**: Password-protected visual directories  
- **Zero-Knowledge Suggestions**: Enable peer-to-peer insight without exposing network  
- **Gamified Engagement**: Promote reflection, emotional check-ins, and mindful sharing

---

## 5. Use Cases

- I want to talk through a personal issue and need to find who I trust most  
- I want to reconnect with someone I haven’t spoken to in months  
- I want to prepare for a social event by reviewing names and notes for a group  
- I want to share a group directory without compromising full database privacy

---

## 6. User Stories

| As a...                  | I want to...                                            | So that...                                        |
|--------------------------|----------------------------------------------------------|--------------------------------------------------|
| Forgetful human          | Quickly match faces to names                             | I don’t feel embarrassed in social settings      |
| Mentally overwhelmed     | Filter my network for meaningful connections             | I can feel supported when I need it most         |
| Privacy-conscious worker | Store relationship notes offline and encrypted           | My trust in the tool and community isn’t violated|
| Community builder        | Export a mini-directory for a trusted group              | We can connect efficiently without using big tech|

---

## 7. Technical Considerations

- Local-first architecture (e.g., SQLite + libsodium)
- Electron/Vite/Flutter for early cross-platform dev
- Optional CLI version for early contributors
- Potential integration with OSS password manager patterns
- Consider zero-knowledge proof architecture in future

---

## 8. Out-of-Scope (MVP)

- Feeds, notifications, algorithmic content
- Cloud sync (unless fully user-controlled)
- Broad social features
- Analytics or behavior tracking

---

## 9. Risks

- Privacy leakage if encryption is flawed
- UX friction from manual tagging could deter use
- Emotional risk from surfacing painful memories
- AI features may hallucinate or overreach

---

## 10. Roadmap

### Phase 0: Personal MVP
- Local encrypted DB with manual contact/relationship entry  
- Visual sociogram UI  
- Mobile-first interface for recall  

### Phase 1: Community Test
- Optional group directory export  
- Invite-only feedback loop  
- Onboarding UX testing  

### Phase 2: AI + ZK Exploration
- Guided onboarding via AI  
- AI-enhanced relationship prompts  
- Research on zero-knowledge peer matching  

---

