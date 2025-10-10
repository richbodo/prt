-- Full-Text Search Support using SQLite FTS5
-- This migration adds virtual tables for fast text search across contacts, notes, and tags
-- FTS5 provides advanced features like phrase search, ranking, and highlighting

-- Enable FTS5 extension (should be built into SQLite by default)
-- The FTS5 module is included by default in most SQLite distributions

-- Create FTS5 virtual table for contacts
-- This enables full-text search across contact names, emails, and phones
CREATE VIRTUAL TABLE IF NOT EXISTS contacts_fts USING fts5(
    contact_id UNINDEXED,  -- Store but don't index the ID
    name,
    email,
    phone,
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
INSERT INTO contacts_fts (contact_id, name, email, phone, notes)
SELECT
    c.id,
    COALESCE(c.name, ''),
    COALESCE(c.email, ''),
    COALESCE(c.phone, ''),
    COALESCE(GROUP_CONCAT(n.content, ' '), '')
FROM contacts c
LEFT JOIN contact_metadata cm ON c.id = cm.contact_id
LEFT JOIN metadata_notes mn ON cm.id = mn.metadata_id
LEFT JOIN notes n ON mn.note_id = n.id
GROUP BY c.id;

-- Populate notes_fts with existing data
INSERT INTO notes_fts (note_id, title, content, contact_names)
SELECT
    n.id,
    COALESCE(n.title, ''),
    COALESCE(n.content, ''),
    COALESCE(GROUP_CONCAT(c.name, ', '), '')
FROM notes n
LEFT JOIN metadata_notes mn ON n.id = mn.note_id
LEFT JOIN contact_metadata cm ON mn.metadata_id = cm.id
LEFT JOIN contacts c ON cm.contact_id = c.id
GROUP BY n.id;

-- Populate tags_fts with existing data
INSERT INTO tags_fts (tag_id, name, description, contact_count)
SELECT
    t.id,
    COALESCE(t.name, ''),
    COALESCE(t.description, ''),
    COUNT(DISTINCT cm.contact_id)
FROM tags t
LEFT JOIN metadata_tags mt ON t.id = mt.tag_id
LEFT JOIN contact_metadata cm ON mt.metadata_id = cm.id
GROUP BY t.id;

-- Create triggers to keep FTS tables in sync with main tables

-- Contacts triggers
CREATE TRIGGER IF NOT EXISTS contacts_fts_insert
AFTER INSERT ON contacts
BEGIN
    INSERT INTO contacts_fts (contact_id, name, email, phone, notes)
    VALUES (
        NEW.id,
        COALESCE(NEW.name, ''),
        COALESCE(NEW.email, ''),
        COALESCE(NEW.phone, ''),
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
        phone = COALESCE(NEW.phone, '')
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
CREATE TRIGGER IF NOT EXISTS metadata_notes_fts_update
AFTER INSERT ON metadata_notes
BEGIN
    UPDATE contacts_fts
    SET notes = (
        SELECT COALESCE(GROUP_CONCAT(n.content, ' '), '')
        FROM metadata_notes mn
        JOIN notes n ON mn.note_id = n.id
        WHERE mn.metadata_id = NEW.metadata_id
    )
    WHERE contact_id = (SELECT contact_id FROM contact_metadata WHERE id = NEW.metadata_id);

    UPDATE notes_fts
    SET contact_names = (
        SELECT COALESCE(GROUP_CONCAT(c.name, ', '), '')
        FROM metadata_notes mn
        JOIN contact_metadata cm ON mn.metadata_id = cm.id
        JOIN contacts c ON cm.contact_id = c.id
        WHERE mn.note_id = NEW.note_id
    )
    WHERE note_id = NEW.note_id;
END;

-- Contact-Tag association trigger to update tag counts in FTS
CREATE TRIGGER IF NOT EXISTS metadata_tags_fts_update
AFTER INSERT ON metadata_tags
BEGIN
    UPDATE tags_fts
    SET contact_count = (
        SELECT COUNT(DISTINCT cm.contact_id)
        FROM metadata_tags mt
        JOIN contact_metadata cm ON mt.metadata_id = cm.id
        WHERE mt.tag_id = NEW.tag_id
    )
    WHERE tag_id = NEW.tag_id;
END;

-- Create useful indexes for JOIN operations with FTS results
CREATE INDEX IF NOT EXISTS idx_contacts_fts_contact_id ON contacts(id);
CREATE INDEX IF NOT EXISTS idx_notes_fts_note_id ON notes(id);
CREATE INDEX IF NOT EXISTS idx_tags_fts_tag_id ON tags(id);