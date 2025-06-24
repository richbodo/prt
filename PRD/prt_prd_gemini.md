# Product Requirements Document: Personal Relationship Tool (PRT)

**Version:** 0.1
**Status:** Draft
**Author:** rsb
**Last Updated:** June 25, 2024

---

## 1. Introduction & Vision

### 1.1. Summary
The Personal Relationship Tool (PRT) is a client-side encrypted, privacy-first application designed to help individuals map, understand, and maintain their most important personal relationships. Unlike traditional social networks that focus on broad, public sharing and algorithmic feeds, PRT is a private utility focused on mental well-being. It serves as a "Relationship Maintenance System," enabling users to catalog their connections not by job titles, but by the qualitative nature of the relationship (e.g., trust, support type, recency of contact).

### 1.2. Vision
To initiate a cascade of positive mental health effects by providing a tool that encourages and facilitates the strengthening of meaningful human connections. We believe that by giving individuals a secure and private space to reflect on and manage their relationships, we can combat the feelings of isolation often exacerbated by modern social media and empower them to build healthier support networks.

---

## 2. The Problem

Individuals have hundreds, if not thousands, of "contacts" across various platforms (Google Contacts, LinkedIn, Facebook), yet often feel they have no one to turn to in moments of need. The core problems PRT aims to solve are:

1.  **Cognitive Overload & Poor Recall:** It is difficult to remember the names, faces, and contexts of a large number of acquaintances, leading to social anxiety and missed opportunities for connection.
2.  **Lack of Meaningful Categorization:** Existing contact managers are built for professional networking or mass communication. They provide no way to find a person based on the *quality* of the relationship (e.g., "Who can I have a deep, personal conversation with right now?").
3.  **Severe Privacy Concerns:** Users are unwilling to log sensitive, personal data about their relationships—the very data that makes them meaningful—into centralized, corporate-owned platforms where it can be analyzed, monetized, or exposed.
4.  **Detrimental UX Patterns:** Mainstream social platforms utilize mentally harmful mechanics like infinite feeds and constant notifications, which distract users and sell their attention, rather than helping them build genuine connections.

---

## 3. Target Audience & User Personas

### Primary Persona: The Privacy-Conscious Connector

* **Who they are:** A tech-savvy individual, likely working remotely in fields like software development or decentralized technology. They are part of multiple communities but may feel disconnected.
* **Needs & Goals:**
    * Wants to improve their memory of names and faces within their social/professional groups.
    * Needs a secure, private place for personal notes about their relationships.
    * Wants to proactively maintain important but distant friendships.
    * Seeks to find the "right person" to talk to based on their current emotional or practical needs.
* **Pain Points:**
    * Feels overwhelmed by the sheer volume of contacts in their phone and on social media.
    * Viscerally distrusts platforms like Facebook and Google with their personal relationship data.
    * Finds current tools useless for answering the question: "Who can I talk to about this problem?"

---

## 4. User Stories & Use Cases

* **As a user feeling isolated, I want to** search for relationships based on qualities like "will pick up the phone right away" or "gives good advice," **so that I can** find the right person to connect with in a moment of need.
* **As a user with a poor memory, I want to** quickly see a visual map of my relationship groups with names and faces, **so that I can** recall who people are and how I know them, especially on my mobile device.
* **As a user who values my privacy, I want to** store my personal notes and relationship data with client-side encryption, **so that I can** be certain no corporation or third party can access my most sensitive information.
* **As a user trying to be a better friend, I want to** see a "maintenance" view of people I haven't contacted in a while, **so that I can** proactively nurture my important relationships.
* **As a community organizer, I want to** export a password-protected, visual directory of a specific group, **so that I can** help members of a close-knit community get to know one another without exposing their data publicly.

---

## 5. Product Requirements & Features

### Phase 1: Minimum Viable Product (MVP) - "The Personal Vault"
The goal of the MVP is to build a tool that is immediately useful for a single user (the author), proving the core concepts of privacy and relationship-focused organization.

| Feature ID | Feature Name | Description |
| :--- | :--- | :--- |
| MVP-101 | **Secure Contact Database** | Create a local-first, client-side encrypted database to store contact information (name, image, contact details). Based on proven password-database patterns. |
| MVP-102 | **Relationship Qualia** | A user cannot store a contact without defining the relationship. Key fields must include: strength, recency of contact, and user-defined tags (e.g., `work-friend`, `mentor`, `can-call-anytime`). |
| MVP-103 | **Private Notes** | For each contact, provide an encrypted free-form text field for private notes, thoughts, and memories associated with that person and relationship. |
| MVP-104 | **Qualia-Based Search** | The primary search functionality. Allow users to search and filter their contacts based on relationship tags and qualities, not just by name. |
| MVP-105 | **Visual Group Navigation** | Provide a simple, fast-loading visual interface (especially on mobile) to navigate groups of contacts (e.g., by shared tags). |
| MVP-106 | **Relationship Maintenance View** | A simple list or view that sorts contacts by "last contacted" date, allowing the user to see who they might want to reach out to. |
| MVP-107 | **Basic Data Export** | Ability to export a selection of contacts and their basic information (no notes or sensitive qualia) to a simple, shareable format (e.g., a password-protected static HTML page). |
| MVP-108 | **CLI First-Version** | The initial implementation can be a command-line interface (CLI) application to accelerate development and cater to the initial tech-savvy audience. |

---

### Phase 2: Adoption & Intelligence
The goal of Phase 2 is to lower the barrier to entry and add intelligent features that enhance the core experience, making the tool valuable to a wider audience.

| Feature ID | Feature Name | Description |
| :--- | :--- | :--- |
| P2-201 | **AI-Enhanced Onboarding** | An intelligent import wizard. It connects to external sources (e.g., Google Contacts) and uses AI-driven prompts to help the user identify and import only their "Meaningful Personal Contacts," avoiding the depressing task of sifting through thousands of irrelevant entries. |
| P2-202 | **AI-Enhanced Maintenance** | Proactive, privacy-preserving suggestions. The system might suggest reconnecting with a contact based on past interaction frequency and the user's own goals. For example: *"You haven't spoken to Alice in 3 months. It might be a good time to reconnect."* This remains a private, on-device suggestion. |
| P2-203 | **GUI Application** | Develop a full-featured graphical user interface for desktop and mobile web, moving beyond the initial CLI. |

---

### Future Vision (Phase 3+)
This phase explores the powerful community and data-sharing aspects mentioned in the notes, with an unwavering commitment to privacy.

| Feature ID | Feature Name | Description |
| :--- | :--- | :--- |
| P3-301 | **Zero-Knowledge Community Insights** | Explore using zero-knowledge proofs to allow users to anonymously share aggregated data about their support network's health. This could allow a community to see, for example, "15% of our members feel they don't have someone to talk to this week" without revealing any individual's identity or connections. |
| P3-302 | **ZK-Powered Introductions** | A decentralized system where users' local AIs can "conspire" to suggest beneficial introductions or re-introductions between people, without ever revealing the full social graph to any central party. |

---

## 6. Non-Functional Requirements

| ID | Requirement | Description |
| :--- | :--- | :--- |
| NFR-1 | **Privacy** | All user-generated data (contacts, notes, relationship qualia) must be client-side encrypted with a user-controlled key. The service/server should be unable to decrypt user data. |
| NFR-2 | **Performance** | The application must be extremely fast, especially for search and visual navigation on mobile devices, to serve as a quick memory aid. |
| NFR-3 | **Offline-First** | The application must be fully functional offline. Data is stored locally on the user's device. |
| NFR-4 | **Data Sovereignty** | Users must have the ability to export their entire database in a non-proprietary format at any time. |

---

## 7. Out of Scope for Foreseeable Future

To maintain focus on mental health and privacy, the following features are explicitly **out of scope**:

* **Public Feeds or Timelines:** The tool is for private reflection, not public performance.
* **Real-time, Unsolicited Notifications:** The user initiates all interactions. No push notifications demanding attention.
* **Advertising or Data Monetization:** The business model will never involve selling user data or attention.
* **Centralized, Unencrypted Cloud Storage:** The core data will remain on the client.

---

## 8. Success Metrics

* **MVP Success:**
    * **Personal Utility:** The author uses the tool daily/weekly to solve the stated problems.
    * **Stability:** The data remains secure and uncorrupted.
* **Post-MVP Success:**
    * **Adoption:** Number of active users within the target community.
    * **Engagement:** Users are actively adding contacts and using the maintenance/search features.
    * **Qualitative Feedback:** User testimonials indicate the tool has had a positive impact on their sense of connection and mental well-being.

