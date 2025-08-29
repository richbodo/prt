-- Full-Text Search Support using SQLite FTS5
-- This migration adds virtual tables for fast text search across contacts, notes, and tags
-- FTS5 provides advanced features like phrase search, ranking, and highlighting

-- Enable FTS5 extension (should be built into SQLite by default)
-- The FTS5 module is included by default in most SQLite distributions

-- Create FTS5 virtual table for contacts
-- This enables full-text search across contact names, emails, phones, and addresses
CREATE VIRTUAL TABLE IF NOT EXISTS contacts_fts USING fts5(
    contact_id UNINDEXED,  -- Store but don't index the ID
    name,
    email,
    phone,
    address,
    notes,
    tokenize='porter unicode61'  -- Use Porter stemming and Unicode support
);

-- Create FTS5 virtual table for notes
-- This enables full-text search across note titles and content
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    note_id UNINDEXED,
    title,
    content,
    contact_names,  -- Denormalized for better search
    tokenize='porter unicode61'
);

-- Create FTS5 virtual table for tags
-- This enables full-text search across tag names and descriptions
CREATE VIRTUAL TABLE IF NOT EXISTS tags_fts USING fts5(
    tag_id UNINDEXED,
    name,
    description,
    contact_count UNINDEXED,  -- Store but don't index
    tokenize='porter unicode61'
);

-- Populate contacts_fts with existing data
INSERT INTO contacts_fts (contact_id, name, email, phone, address, notes)
SELECT 
    c.id,
    COALESCE(c.name, ''),
    COALESCE(c.email, ''),
    COALESCE(c.phone, ''),
    COALESCE(c.address, ''),
    COALESCE(GROUP_CONCAT(n.content, ' '), '')
FROM contacts c
LEFT JOIN contact_notes cn ON c.id = cn.contact_id
LEFT JOIN notes n ON cn.note_id = n.id
GROUP BY c.id;

-- Populate notes_fts with existing data
INSERT INTO notes_fts (note_id, title, content, contact_names)
SELECT 
    n.id,
    COALESCE(n.title, ''),
    COALESCE(n.content, ''),
    COALESCE(GROUP_CONCAT(c.name, ', '), '')
FROM notes n
LEFT JOIN contact_notes cn ON n.id = cn.note_id
LEFT JOIN contacts c ON cn.contact_id = c.id
GROUP BY n.id;

-- Populate tags_fts with existing data
INSERT INTO tags_fts (tag_id, name, description, contact_count)
SELECT 
    t.id,
    COALESCE(t.name, ''),
    COALESCE(t.description, ''),
    COUNT(DISTINCT ct.contact_id)
FROM tags t
LEFT JOIN contact_tags ct ON t.id = ct.tag_id
GROUP BY t.id;

-- Create triggers to keep FTS tables in sync with main tables

-- Contacts triggers
CREATE TRIGGER IF NOT EXISTS contacts_fts_insert 
AFTER INSERT ON contacts
BEGIN
    INSERT INTO contacts_fts (contact_id, name, email, phone, address, notes)
    VALUES (
        NEW.id,
        COALESCE(NEW.name, ''),
        COALESCE(NEW.email, ''),
        COALESCE(NEW.phone, ''),
        COALESCE(NEW.address, ''),
        ''
    );
END;

CREATE TRIGGER IF NOT EXISTS contacts_fts_update
AFTER UPDATE ON contacts
BEGIN
    UPDATE contacts_fts 
    SET 
        name = COALESCE(NEW.name, ''),
        email = COALESCE(NEW.email, ''),
        phone = COALESCE(NEW.phone, ''),
        address = COALESCE(NEW.address, '')
    WHERE contact_id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS contacts_fts_delete
AFTER DELETE ON contacts
BEGIN
    DELETE FROM contacts_fts WHERE contact_id = OLD.id;
END;

-- Notes triggers
CREATE TRIGGER IF NOT EXISTS notes_fts_insert
AFTER INSERT ON notes
BEGIN
    INSERT INTO notes_fts (note_id, title, content, contact_names)
    VALUES (
        NEW.id,
        COALESCE(NEW.title, ''),
        COALESCE(NEW.content, ''),
        ''
    );
END;

CREATE TRIGGER IF NOT EXISTS notes_fts_update
AFTER UPDATE ON notes
BEGIN
    UPDATE notes_fts
    SET 
        title = COALESCE(NEW.title, ''),
        content = COALESCE(NEW.content, '')
    WHERE note_id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS notes_fts_delete
AFTER DELETE ON notes
BEGIN
    DELETE FROM notes_fts WHERE note_id = OLD.id;
END;

-- Tags triggers
CREATE TRIGGER IF NOT EXISTS tags_fts_insert
AFTER INSERT ON tags
BEGIN
    INSERT INTO tags_fts (tag_id, name, description, contact_count)
    VALUES (
        NEW.id,
        COALESCE(NEW.name, ''),
        COALESCE(NEW.description, ''),
        0
    );
END;

CREATE TRIGGER IF NOT EXISTS tags_fts_update
AFTER UPDATE ON tags
BEGIN
    UPDATE tags_fts
    SET 
        name = COALESCE(NEW.name, ''),
        description = COALESCE(NEW.description, '')
    WHERE tag_id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS tags_fts_delete
AFTER DELETE ON tags
BEGIN
    DELETE FROM tags_fts WHERE tag_id = OLD.id;
END;

-- Contact-Note association trigger to update contact notes in FTS
CREATE TRIGGER IF NOT EXISTS contact_notes_fts_update
AFTER INSERT ON contact_notes
BEGIN
    UPDATE contacts_fts
    SET notes = (
        SELECT COALESCE(GROUP_CONCAT(n.content, ' '), '')
        FROM contact_notes cn
        JOIN notes n ON cn.note_id = n.id
        WHERE cn.contact_id = NEW.contact_id
    )
    WHERE contact_id = NEW.contact_id;
    
    UPDATE notes_fts
    SET contact_names = (
        SELECT COALESCE(GROUP_CONCAT(c.name, ', '), '')
        FROM contact_notes cn
        JOIN contacts c ON cn.contact_id = c.id
        WHERE cn.note_id = NEW.note_id
    )
    WHERE note_id = NEW.note_id;
END;

-- Contact-Tag association trigger to update tag counts in FTS
CREATE TRIGGER IF NOT EXISTS contact_tags_fts_update
AFTER INSERT ON contact_tags
BEGIN
    UPDATE tags_fts
    SET contact_count = (
        SELECT COUNT(DISTINCT contact_id)
        FROM contact_tags
        WHERE tag_id = NEW.tag_id
    )
    WHERE tag_id = NEW.tag_id;
END;

-- Create useful indexes for JOIN operations with FTS results
CREATE INDEX IF NOT EXISTS idx_contacts_fts_contact_id ON contacts(id);
CREATE INDEX IF NOT EXISTS idx_notes_fts_note_id ON notes(id);
CREATE INDEX IF NOT EXISTS idx_tags_fts_tag_id ON tags(id);

-- Add schema version tracking for this migration
INSERT OR IGNORE INTO schema_versions (version, description, applied_at)
VALUES (5, 'Add FTS5 full-text search support', datetime('now'));