-- Migration 017: Add private key storage to user_keys table
--
-- Adds private_key column for E2E encryption
-- Private keys are stored encrypted in production via secure key storage

PRAGMA foreign_keys = ON;

-- Add private_key column to user_keys table
-- Column stores Base64-encoded X25519 private key (32 bytes)
ALTER TABLE user_keys ADD COLUMN private_key TEXT;

-- Add index for faster lookups (though private key should only be accessed by owner)
CREATE INDEX IF NOT EXISTS idx_user_keys_private ON user_keys(user_id) WHERE private_key IS NOT NULL;
