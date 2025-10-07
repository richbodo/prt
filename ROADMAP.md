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

## The fun stuff - working on a paper with proof of principle
### Tasks
- [ ] Implement lightweight public key communications for test mode.
- [ ] **P2P Privacy-Preserving State Attestation**
- [ ] **P2P Cooperative signalling and connection**
- [ ] **P2P Community messaging**

## Flet for mobile apps
- [ ] **We will take the working TUI and duplicate it in flet** TBD
