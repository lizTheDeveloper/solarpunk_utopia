-- Migration 004: Add E2E encrypted messaging
--
-- Messaging routes over DTN mesh with end-to-end encryption.
-- Only the recipient can decrypt message content.

PRAGMA foreign_keys = ON;

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    sender_id TEXT NOT NULL,
    recipient_id TEXT NOT NULL,
    thread_id TEXT,  -- Groups messages into conversations or exchanges
    message_type TEXT DEFAULT 'direct',  -- 'direct', 'exchange', 'broadcast', 'alert'
    encrypted_content BLOB NOT NULL,
    ephemeral_key TEXT NOT NULL,  -- Public key for this message's encryption
    timestamp TEXT NOT NULL,
    expires_at TEXT,
    bundle_id TEXT,  -- DTN bundle ID for this message
    delivery_status TEXT DEFAULT 'pending',  -- 'pending', 'sent', 'delivered', 'read'
    delivered_at TEXT,
    read_at TEXT,
    is_deleted INTEGER DEFAULT 0,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient_id);
CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(delivery_status);
CREATE INDEX IF NOT EXISTS idx_messages_bundle ON messages(bundle_id);

-- Create message_threads table for conversation metadata
CREATE TABLE IF NOT EXISTS message_threads (
    id TEXT PRIMARY KEY,
    thread_type TEXT NOT NULL,  -- 'direct', 'exchange', 'cell'
    participants TEXT NOT NULL,  -- JSON array of user IDs
    exchange_id TEXT,  -- If attached to an exchange
    cell_id TEXT,  -- If attached to a cell
    created_at TEXT NOT NULL,
    last_message_at TEXT,
    last_message_preview TEXT,
    unread_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_threads_type ON message_threads(thread_type);
CREATE INDEX IF NOT EXISTS idx_threads_exchange ON message_threads(exchange_id);
CREATE INDEX IF NOT EXISTS idx_threads_cell ON message_threads(cell_id);
CREATE INDEX IF NOT EXISTS idx_threads_last_message ON message_threads(last_message_at);

-- Create message_receipts table for delivery confirmations
CREATE TABLE IF NOT EXISTS message_receipts (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL,
    recipient_id TEXT NOT NULL,
    receipt_type TEXT NOT NULL,  -- 'delivered', 'read'
    timestamp TEXT NOT NULL,
    bundle_id TEXT,  -- DTN bundle ID for the receipt
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_receipts_message ON message_receipts(message_id);
CREATE INDEX IF NOT EXISTS idx_receipts_type ON message_receipts(receipt_type);

-- Create user_keys table for E2E encryption key management
CREATE TABLE IF NOT EXISTS user_keys (
    user_id TEXT PRIMARY KEY,
    public_key TEXT NOT NULL,
    public_key_signature TEXT NOT NULL,  -- Self-signed proof of ownership
    key_created_at TEXT NOT NULL,
    key_expires_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_keys_expires ON user_keys(key_expires_at);
