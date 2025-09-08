---
title: "Data Formats Reference"
description: "Reference for data formats, schemas, and file structures used by Westfall Personal Assistant"
category: "reference"
priority: 3
tags: ["data", "formats", "schemas", "import", "export"]
last_updated: "2025-09-08"
---

# Data Formats Reference

This document describes all data formats, schemas, and file structures used by Westfall Personal Assistant for import, export, and storage.

## Export Formats

### Complete Data Export

**Format**: JSON  
**Extension**: `.wfa`  
**Encryption**: Yes (with master password)

```json
{
  "metadata": {
    "version": "1.0.0",
    "exported_at": "2025-09-08T10:30:00Z",
    "application_version": "1.2.3",
    "data_version": 2,
    "encrypted": true
  },
  "features": {
    "passwords": { /* encrypted password data */ },
    "notes": { /* encrypted notes data */ },
    "email": { /* email configuration */ },
    "calendar": { /* calendar events */ },
    "finance": { /* financial data */ }
  },
  "settings": { /* application settings */ },
  "plugins": { /* plugin data */ }
}
```

### Selective Export

**Format**: JSON  
**Extension**: `.json`  
**Encryption**: Optional

```json
{
  "metadata": {
    "feature": "passwords",
    "exported_at": "2025-09-08T10:30:00Z",
    "count": 150
  },
  "data": [
    {
      "id": "uuid-1234",
      "site": "example.com",
      "username": "user@example.com",
      "password": "encrypted_password",
      "notes": "Login for work account",
      "created_at": "2025-01-15T09:00:00Z",
      "updated_at": "2025-08-20T14:30:00Z",
      "tags": ["work", "important"]
    }
  ]
}
```

## Import Formats

### Password Manager Import

#### LastPass CSV Format
```csv
url,username,password,extra,name,grouping,fav
https://example.com,user@example.com,password123,Notes here,Example Site,Work,0
```

#### 1Password 1PIF Format
```json
{
  "uuid": "12345",
  "updatedAt": 1609459200,
  "securityLevel": "SL5",
  "contentsHash": "hash",
  "title": "Example Site",
  "location": "https://example.com",
  "secureContents": {
    "fields": [
      {
        "designation": "username",
        "name": "username",
        "type": "T",
        "value": "user@example.com"
      }
    ]
  }
}
```

#### Bitwarden JSON Format
```json
{
  "folders": [],
  "items": [
    {
      "id": "uuid",
      "organizationId": null,
      "folderId": null,
      "type": 1,
      "name": "Example Site",
      "notes": "Notes here",
      "favorite": false,
      "login": {
        "username": "user@example.com",
        "password": "password123",
        "totp": null,
        "uris": [
          {
            "match": null,
            "uri": "https://example.com"
          }
        ]
      }
    }
  ]
}
```

### Notes Import

#### Markdown Format
```markdown
---
title: "Note Title"
tags: ["tag1", "tag2"]
category: "work"
created: "2025-09-08T10:00:00Z"
---

# Note Content

This is the note content in **Markdown** format.

- List item 1
- List item 2

[Link to somewhere](https://example.com)
```

#### Evernote ENEX Format
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">
<en-export export-date="20250908T100000Z" application="Evernote">
  <note>
    <title>Note Title</title>
    <content><![CDATA[<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>Note content here</en-note>]]></content>
    <created>20250908T100000Z</created>
    <updated>20250908T100000Z</updated>
    <tag>work</tag>
    <tag>important</tag>
  </note>
</en-export>
```

### Contact Import

#### vCard Format (.vcf)
```
BEGIN:VCARD
VERSION:3.0
FN:John Doe
N:Doe;John;;;
ORG:Example Company
TITLE:Software Engineer
EMAIL;TYPE=WORK:john.doe@example.com
TEL;TYPE=WORK:+1-555-555-5555
ADR;TYPE=WORK:;;123 Main St;Anytown;ST;12345;USA
URL:https://johndoe.example.com
NOTE:Important contact for project collaboration
END:VCARD
```

#### CSV Format
```csv
Name,Email,Phone,Company,Title,Notes
John Doe,john.doe@example.com,555-555-5555,Example Company,Software Engineer,Important contact
```

### Calendar Import

#### iCalendar Format (.ics)
```ical
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Westfall Personal Assistant//EN
BEGIN:VEVENT
UID:20250908T100000Z-12345@westfall.com
DTSTAMP:20250908T100000Z
DTSTART:20250915T140000Z
DTEND:20250915T150000Z
SUMMARY:Team Meeting
DESCRIPTION:Weekly team sync meeting
LOCATION:Conference Room A
STATUS:CONFIRMED
CATEGORIES:WORK,MEETING
BEGIN:VALARM
TRIGGER:-PT15M
ACTION:DISPLAY
DESCRIPTION:Reminder: Team Meeting in 15 minutes
END:VALARM
END:VEVENT
END:VCALENDAR
```

### Financial Data Import

#### CSV Format
```csv
Date,Description,Amount,Category,Account,Type
2025-09-08,Coffee Shop,-4.50,Food & Dining,Checking,Expense
2025-09-08,Salary Deposit,3000.00,Income,Checking,Income
2025-09-07,Gas Station,-45.00,Transportation,Credit Card,Expense
```

#### OFX/QIF Format
```
!Type:Bank
D09/08/2025
T-4.50
PCoffee Shop
LFood & Dining
^
D09/08/2025
T3000.00
PSalary Deposit
LIncome
^
```

## Database Schema

### Core Tables

#### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    settings TEXT -- JSON blob
);
```

#### Features Table
```sql
CREATE TABLE features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    feature_name TEXT NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    config TEXT, -- JSON blob
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Password Manager Schema

#### Passwords Table
```sql
CREATE TABLE passwords (
    id TEXT PRIMARY KEY, -- UUID
    user_id INTEGER REFERENCES users(id),
    site_name TEXT NOT NULL,
    site_url TEXT,
    username TEXT,
    password_encrypted BLOB,
    notes_encrypted BLOB,
    folder TEXT,
    tags TEXT, -- JSON array
    favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    INDEX idx_passwords_user_id (user_id),
    INDEX idx_passwords_site_name (site_name)
);
```

### Notes Schema

#### Notes Table
```sql
CREATE TABLE notes (
    id TEXT PRIMARY KEY, -- UUID
    user_id INTEGER REFERENCES users(id),
    title TEXT NOT NULL,
    content_encrypted BLOB,
    category TEXT,
    tags TEXT, -- JSON array
    format TEXT DEFAULT 'markdown', -- markdown, html, text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP,
    INDEX idx_notes_user_id (user_id),
    INDEX idx_notes_category (category),
    INDEX idx_notes_title (title)
);
```

### Calendar Schema

#### Events Table
```sql
CREATE TABLE calendar_events (
    id TEXT PRIMARY KEY, -- UUID
    user_id INTEGER REFERENCES users(id),
    title TEXT NOT NULL,
    description TEXT,
    location TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    all_day BOOLEAN DEFAULT FALSE,
    recurrence_rule TEXT, -- RRULE format
    reminder_minutes INTEGER DEFAULT 15,
    category TEXT,
    status TEXT DEFAULT 'confirmed', -- confirmed, tentative, cancelled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_events_user_id (user_id),
    INDEX idx_events_start_time (start_time)
);
```

### Finance Schema

#### Accounts Table
```sql
CREATE TABLE finance_accounts (
    id TEXT PRIMARY KEY, -- UUID
    user_id INTEGER REFERENCES users(id),
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- checking, savings, credit, investment
    balance DECIMAL(15,2) DEFAULT 0.00,
    currency TEXT DEFAULT 'USD',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Transactions Table
```sql
CREATE TABLE finance_transactions (
    id TEXT PRIMARY KEY, -- UUID
    user_id INTEGER REFERENCES users(id),
    account_id TEXT REFERENCES finance_accounts(id),
    amount DECIMAL(15,2) NOT NULL,
    description TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    transaction_date DATE NOT NULL,
    type TEXT NOT NULL, -- income, expense, transfer
    tags TEXT, -- JSON array
    receipt_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_transactions_user_id (user_id),
    INDEX idx_transactions_account_id (account_id),
    INDEX idx_transactions_date (transaction_date),
    INDEX idx_transactions_category (category)
);
```

## Plugin Data Formats

### Plugin Manifest
```json
{
  "manifest_version": 2,
  "name": "Plugin Name",
  "version": "1.0.0",
  "description": "Plugin description",
  "author": "Author Name",
  "homepage_url": "https://example.com",
  "permissions": [
    "read_notes",
    "write_notes",
    "network_access"
  ],
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"]
    }
  ],
  "background": {
    "scripts": ["background.js"],
    "persistent": false
  },
  "options_page": "options.html",
  "icons": {
    "16": "icon16.png",
    "48": "icon48.png",
    "128": "icon128.png"
  }
}
```

### Plugin Data Storage
```json
{
  "plugin_id": "example-plugin",
  "version": "1.0.0",
  "data": {
    "settings": {
      "api_key": "encrypted_value",
      "enabled": true
    },
    "cache": {
      "last_sync": "2025-09-08T10:00:00Z",
      "data": {}
    },
    "user_data": {}
  },
  "permissions": ["read_notes", "network_access"],
  "last_updated": "2025-09-08T10:00:00Z"
}
```

## Backup Formats

### Full Backup Format
```json
{
  "backup_metadata": {
    "version": "1.0.0",
    "created_at": "2025-09-08T10:00:00Z",
    "application_version": "1.2.3",
    "backup_type": "full",
    "encrypted": true,
    "compression": "gzip"
  },
  "database_dump": "base64_encoded_encrypted_data",
  "file_attachments": {
    "file1.pdf": "base64_encoded_file_data",
    "image1.png": "base64_encoded_file_data"
  },
  "settings": {
    "user_preferences": {},
    "feature_configs": {}
  }
}
```

### Incremental Backup Format
```json
{
  "backup_metadata": {
    "version": "1.0.0",
    "created_at": "2025-09-08T10:00:00Z",
    "backup_type": "incremental",
    "since": "2025-09-07T10:00:00Z",
    "encrypted": true
  },
  "changed_records": {
    "passwords": [
      {
        "id": "uuid-1234",
        "operation": "update",
        "data": "encrypted_data"
      }
    ],
    "notes": [
      {
        "id": "uuid-5678",
        "operation": "create",
        "data": "encrypted_data"
      }
    ]
  },
  "deleted_records": {
    "passwords": ["uuid-9999"],
    "notes": []
  }
}
```

## Encryption Formats

### Encrypted Data Structure
```json
{
  "algorithm": "AES-256-GCM",
  "key_derivation": {
    "method": "PBKDF2",
    "iterations": 100000,
    "salt": "base64_encoded_salt"
  },
  "encrypted_data": "base64_encoded_encrypted_data",
  "auth_tag": "base64_encoded_auth_tag",
  "nonce": "base64_encoded_nonce"
}
```

### Key Storage Format
```json
{
  "key_id": "uuid",
  "algorithm": "RSA-2048",
  "purpose": "data_encryption",
  "created_at": "2025-09-08T10:00:00Z",
  "expires_at": null,
  "public_key": "base64_encoded_public_key",
  "private_key_encrypted": "base64_encoded_encrypted_private_key"
}
```

## API Data Formats

### REST API Response Format
```json
{
  "success": true,
  "data": {
    "id": "12345",
    "type": "password",
    "attributes": {
      "site_name": "example.com",
      "username": "user@example.com",
      "created_at": "2025-09-08T10:00:00Z"
    }
  },
  "meta": {
    "version": "1.0",
    "timestamp": "2025-09-08T10:00:00Z"
  }
}
```

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "password",
      "reason": "Password too short"
    }
  },
  "meta": {
    "timestamp": "2025-09-08T10:00:00Z",
    "request_id": "req-12345"
  }
}
```

## Migration Formats

### Database Migration Script
```sql
-- Migration: 001_add_tags_to_passwords
-- Up
ALTER TABLE passwords ADD COLUMN tags TEXT;
CREATE INDEX idx_passwords_tags ON passwords(tags);

-- Down
DROP INDEX idx_passwords_tags;
ALTER TABLE passwords DROP COLUMN tags;
```

### Data Migration Format
```json
{
  "migration_id": "001_add_tags_to_passwords",
  "version_from": "1.0.0",
  "version_to": "1.1.0",
  "operations": [
    {
      "type": "add_column",
      "table": "passwords",
      "column": "tags",
      "data_type": "TEXT"
    },
    {
      "type": "create_index",
      "table": "passwords",
      "columns": ["tags"],
      "name": "idx_passwords_tags"
    }
  ],
  "rollback": [
    {
      "type": "drop_index",
      "name": "idx_passwords_tags"
    },
    {
      "type": "drop_column",
      "table": "passwords",
      "column": "tags"
    }
  ]
}
```

---

*Last updated: September 8, 2025*