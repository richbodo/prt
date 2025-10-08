# PRT Development Roadmap

This document outlines the development roadmap for the Personal Relationship Toolkit (PRT).  Not exactly doing these in order, but there is a [Project](https://github.com/users/richbodo/projects/2) that shows what is being worked on, more or less. 

## Database Encryption 
### Tasks
- [ ] **Implement database encryption** at rest - pulled sqlcipher - simplifying
- [ ] **Add key management**
- [ ] **Update CLI for encryption setup**
- [ ] **Document encryption security model**

## Enhanced Search & Filtering, Web Views
### Tasks
- [x] **Web Views** create a "directory" of any group of contacts - a static page to nav the group with contact details on mouseover or click. - basic version implemented
- [x] **Image support for contacts** upload images or find them online
- [x] **Extend database schema** with additional qualia
- [ ] **Implement textual TUI for advanced search** in progress
- [ ] **Implement advanced search** with multiple criteria - not spec'd

## AI Chat Integration for CLI
### Tasks
- [X] Hugging Face transformer can use gpt-oss-20b to chat generically in chat mode
- [ ] Duplicate CLI/TUI capabilities in chat mode - in progress

## AI Chat Dialogue Evals and functions
### Tasks - pre-CRT
- [ ] Find the string "test" in any user-editable table and return a paginated list.
- [ ] Find images online for all the missing images for my contacts in this directory view, and allow me to select from them and add them to my db as contact images.
- [ ] Find all the contacts I used to work with at Company X
### Tasks - post-CRT
- [ ] Discuss: Who you know, who have you supported, who has supported you, and tag and add notes with the AI
- [ ] Discuss: Who do you have things in common with?  Who might need your help today?  Who might you help today?
- [ ] Discuss: Specific needs you have - identify groups of contact relationships, start building communications plans.
- [ ] Discuss: In your day to day life, how can you take notes that we can discuss, so we can keep growing your relationship graph, and your knowledge of your relationships and your communities.  How can we make it trivial to find what you need and participate.


## Message Analysis - enables contact recency
### Tasks
- [ ] **Add messaging data to db** probably just use an IMAP db first.
- [ ] **Pull recent messages from some messaging tool (IMAP?  Chat?)**
- [ ] **Recency analysis for community messaging**
- [ ] **Add to enhanced search and filtering**

## The fun stuff - working on a CRT paper with proof of principle
### Tasks
- [ ] Implement CRT with lightweight public key communications for test mesh.
- [ ] **P2P Privacy-Preserving State Attestation**
- [ ] **P2P Cooperative signalling and connection**
- [ ] **P2P Community messaging**

## Flet for mobile apps
- [ ] **We will take the working TUI and duplicate it in flet** TBD

## Make it fun - can be done in parallel with any other initiative

I had a nice, wide-ranging, rambling [conversation with claude about this](https://claude.ai/share/c2c3ac4d-894e-47c9-b3f9-7f4c5e4f4a43), and claude came up with some suggestions to make the project more fun:

Some thoughts on making it more engaging:

1. Make the loneliness visible (then addressable)
Right now it tracks relationships, but does it surface gaps? Imagine a gentle dashboard that shows: "You haven't reached out to anyone in the 'close friend' tag in 3 weeks" or "5 people reached out to you that you never responded to." Not guilt-trippy, just... honest. Distributed devs respond to metrics. Make relationship health a metric they can improve.

2. The directory tool is your killer feature - lean into it
Those single-page HTML visualizations of relationship graphs? That's cool. That's the kind of thing devs show each other. Make it beautiful. Make it mesmerizing. Add force-directed graphs, time-based visualizations (who faded away? who emerged?), clusters that reveal patterns you didn't know existed. Make people go "whoa, I need to see my network like this."

3. Create a "share anonymized insights" feature
What if users could opt-in to share (fully anonymized) patterns? Like: "Average distributed dev has 47 contacts but actively communicates with 4." Or "Most common gap: people who message you that you don't respond to." This gives the isolated community a sense of "oh, we're all struggling with this together" without violating privacy.

4. Build in prompts for reconnection
The LLM chat integration is perfect for this. What if it could suggest: "You haven't talked to [contact] in 6 months. Here are three low-pressure ways to reach out based on your last conversation." Make the tool an active relationship coach, not just a database.

5. Make contribution ultra-low-friction  
Your isolated devs won't contribute big features. But they might add: a cool color scheme, a new graph layout, a helpful prompt template, a search filter. Make your issues tiny and well-specified. "Good first issues" that take 15 minutes. Make it feel like dropping by to help, not committing to a project.

6. The CRT integration is everything
You mention PRTs joining together via CRT to "discover relational needs." THIS is the secret sauce. If PRT helps me manage my relationships and CRT helps me find new relationships with people who have compatible needs... that's the full loop. Can you prototype even a minimal version of this? Even if it's just "PRTs in this mesh can see each other's anonymized 'looking for' tags"?

7. Add some joy
Relationship management sounds like a chore. But what if finding a long-lost friend felt like uncovering treasure? What if your network visualization played a little musical note when you strengthened a connection? Small dopamine hits. Devs are human too.

