-- Migration 005: Add Performance Indexes for Large Contact Datasets
-- Purpose: Optimize query performance for databases with 1000+ contacts
-- Date: 2025-11-03

-- Index for contact name searches (very common in LLM queries)
CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(name);

-- Index for email searches and lookups
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);

-- Index for profile image queries (common pattern: "contacts with images")
CREATE INDEX IF NOT EXISTS idx_contacts_profile_image_not_null ON contacts(id) WHERE profile_image IS NOT NULL;

-- Index for created_at for temporal queries and sorting
CREATE INDEX IF NOT EXISTS idx_contacts_created_at ON contacts(created_at);

-- Index for contact metadata relationships (joins)
CREATE INDEX IF NOT EXISTS idx_contact_metadata_contact_id ON contact_metadata(contact_id);

-- Index for tag name searches
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);

-- Index for note title and content searches (if not using FTS)
CREATE INDEX IF NOT EXISTS idx_notes_title ON notes(title);

-- Composite index for contact name and email (common combined searches)
CREATE INDEX IF NOT EXISTS idx_contacts_name_email ON contacts(name, email);