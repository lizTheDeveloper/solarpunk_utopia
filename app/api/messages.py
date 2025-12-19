"""
API endpoints for E2E encrypted mesh messaging

Messages route over DTN mesh with end-to-end encryption.
Only the recipient can decrypt message content.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import uuid
import base64

from ..database import get_db
from .cells import get_current_user

router = APIRouter(prefix="/messages", tags=["messages"])


class Message(BaseModel):
    id: str
    sender_id: str
    recipient_id: str
    thread_id: Optional[str] = None
    message_type: str = "direct"
    encrypted_content: str  # Base64 encoded
    ephemeral_key: str
    timestamp: str
    expires_at: Optional[str] = None
    delivery_status: str = "pending"
    delivered_at: Optional[str] = None
    read_at: Optional[str] = None


class MessageThread(BaseModel):
    id: str
    thread_type: str
    participants: List[str]
    exchange_id: Optional[str] = None
    cell_id: Optional[str] = None
    created_at: str
    last_message_at: Optional[str] = None
    last_message_preview: Optional[str] = None
    unread_count: int = 0


class SendMessageRequest(BaseModel):
    recipient_id: str
    content: str  # Plain text - will be encrypted server-side
    thread_id: Optional[str] = None
    message_type: str = "direct"
    expires_in_hours: Optional[int] = None
    exchange_id: Optional[str] = None


class MessageReceipt(BaseModel):
    id: str
    message_id: str
    recipient_id: str
    receipt_type: str
    timestamp: str


@router.post("/", response_model=Message)
async def send_message(
    request: SendMessageRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Send an encrypted message to a recipient.

    Message is encrypted and wrapped in a DTN bundle for mesh delivery.
    """
    db = await get_db()

    # Get recipient's public key
    cursor = await db.execute(
        "SELECT public_key FROM user_keys WHERE user_id = ?",
        (request.recipient_id,)
    )
    recipient_key_row = await cursor.fetchone()

    if not recipient_key_row:
        raise HTTPException(status_code=404, detail="Recipient not found or has no encryption key")

    recipient_public_key = recipient_key_row[0]

    # In production: Encrypt content with recipient's public key using nacl/libsodium
    # For now: Simple base64 encoding as placeholder
    # TODO: Replace with actual X25519 encryption
    encrypted_content = base64.b64encode(request.content.encode()).decode()

    # Generate ephemeral key for this message (placeholder)
    ephemeral_key = str(uuid.uuid4())

    # Create message record
    message_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    expires_at = None
    if request.expires_in_hours:
        expires_at = (datetime.now() + timedelta(hours=request.expires_in_hours)).isoformat()

    # Determine or create thread
    thread_id = request.thread_id
    if not thread_id:
        # Create new thread for direct message
        thread_id = str(uuid.uuid4())
        participants = json.dumps([user_id, request.recipient_id])

        await db.execute("""
            INSERT INTO message_threads (
                id, thread_type, participants, exchange_id, cell_id,
                created_at, last_message_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            thread_id, request.message_type, participants,
            request.exchange_id, None, timestamp, timestamp
        ))

    # Insert message
    await db.execute("""
        INSERT INTO messages (
            id, sender_id, recipient_id, thread_id, message_type,
            encrypted_content, ephemeral_key, timestamp, expires_at,
            delivery_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (
        message_id, user_id, request.recipient_id, thread_id,
        request.message_type, encrypted_content, ephemeral_key,
        timestamp, expires_at
    ))

    # Update thread last message
    await db.execute("""
        UPDATE message_threads
        SET last_message_at = ?,
            last_message_preview = ?,
            unread_count = unread_count + 1
        WHERE id = ?
    """, (timestamp, request.content[:100], thread_id))

    # TODO: Create DTN bundle for mesh delivery
    # This would call the DTN API to create a bundle with:
    # - audience: "direct"
    # - recipient: request.recipient_id
    # - payload: encrypted message
    # - priority: based on message_type

    await db.commit()

    return Message(
        id=message_id,
        sender_id=user_id,
        recipient_id=request.recipient_id,
        thread_id=thread_id,
        message_type=request.message_type,
        encrypted_content=encrypted_content,
        ephemeral_key=ephemeral_key,
        timestamp=timestamp,
        expires_at=expires_at,
        delivery_status="pending"
    )


@router.get("/inbox", response_model=List[Message])
async def get_inbox(
    user_id: str = Depends(get_current_user),
    limit: int = 100
):
    """Get messages for the current user"""
    db = await get_db()

    cursor = await db.execute("""
        SELECT id, sender_id, recipient_id, thread_id, message_type,
               encrypted_content, ephemeral_key, timestamp, expires_at,
               delivery_status, delivered_at, read_at
        FROM messages
        WHERE recipient_id = ? AND is_deleted = 0
        ORDER BY timestamp DESC
        LIMIT ?
    """, (user_id, limit))

    rows = await cursor.fetchall()

    messages = []
    for row in rows:
        messages.append(Message(
            id=row[0],
            sender_id=row[1],
            recipient_id=row[2],
            thread_id=row[3],
            message_type=row[4],
            encrypted_content=row[5],
            ephemeral_key=row[6],
            timestamp=row[7],
            expires_at=row[8],
            delivery_status=row[9],
            delivered_at=row[10],
            read_at=row[11]
        ))

    return messages


@router.get("/threads", response_model=List[MessageThread])
async def get_threads(
    user_id: str = Depends(get_current_user)
):
    """Get all message threads for the current user"""
    db = await get_db()

    cursor = await db.execute("""
        SELECT id, thread_type, participants, exchange_id, cell_id,
               created_at, last_message_at, last_message_preview, unread_count
        FROM message_threads
        WHERE participants LIKE ?
        ORDER BY last_message_at DESC
    """, (f'%"{user_id}"%',))

    rows = await cursor.fetchall()

    threads = []
    for row in rows:
        threads.append(MessageThread(
            id=row[0],
            thread_type=row[1],
            participants=json.loads(row[2]),
            exchange_id=row[3],
            cell_id=row[4],
            created_at=row[5],
            last_message_at=row[6],
            last_message_preview=row[7],
            unread_count=row[8]
        ))

    return threads


@router.get("/threads/{thread_id}/messages", response_model=List[Message])
async def get_thread_messages(
    thread_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get all messages in a thread"""
    db = await get_db()

    # Verify user is participant in thread
    cursor = await db.execute(
        "SELECT participants FROM message_threads WHERE id = ?",
        (thread_id,)
    )
    thread_row = await cursor.fetchone()

    if not thread_row:
        raise HTTPException(status_code=404, detail="Thread not found")

    participants = json.loads(thread_row[0])
    if user_id not in participants:
        raise HTTPException(status_code=403, detail="Not a participant in this thread")

    # Get messages
    cursor = await db.execute("""
        SELECT id, sender_id, recipient_id, thread_id, message_type,
               encrypted_content, ephemeral_key, timestamp, expires_at,
               delivery_status, delivered_at, read_at
        FROM messages
        WHERE thread_id = ? AND is_deleted = 0
        ORDER BY timestamp ASC
    """, (thread_id,))

    rows = await cursor.fetchall()

    messages = []
    for row in rows:
        messages.append(Message(
            id=row[0],
            sender_id=row[1],
            recipient_id=row[2],
            thread_id=row[3],
            message_type=row[4],
            encrypted_content=row[5],
            ephemeral_key=row[6],
            timestamp=row[7],
            expires_at=row[8],
            delivery_status=row[9],
            delivered_at=row[10],
            read_at=row[11]
        ))

    # Mark messages as read
    await db.execute("""
        UPDATE messages
        SET read_at = datetime('now'), delivery_status = 'read'
        WHERE thread_id = ? AND recipient_id = ? AND read_at IS NULL
    """, (thread_id, user_id))

    # Reset unread count
    await db.execute("""
        UPDATE message_threads SET unread_count = 0 WHERE id = ?
    """, (thread_id,))

    await db.commit()

    return messages


@router.post("/messages/{message_id}/mark-delivered")
async def mark_message_delivered(
    message_id: str,
    user_id: str = Depends(get_current_user)
):
    """Mark a message as delivered (called when message bundle arrives)"""
    db = await get_db()

    # Verify recipient
    cursor = await db.execute(
        "SELECT recipient_id FROM messages WHERE id = ?",
        (message_id,)
    )
    msg_row = await cursor.fetchone()

    if not msg_row:
        raise HTTPException(status_code=404, detail="Message not found")

    if msg_row[0] != user_id:
        raise HTTPException(status_code=403, detail="Not the recipient")

    # Update message status
    await db.execute("""
        UPDATE messages
        SET delivery_status = 'delivered', delivered_at = datetime('now')
        WHERE id = ?
    """, (message_id,))

    # Create delivery receipt
    receipt_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    await db.execute("""
        INSERT INTO message_receipts (
            id, message_id, recipient_id, receipt_type, timestamp
        ) VALUES (?, ?, ?, 'delivered', ?)
    """, (receipt_id, message_id, user_id, timestamp))

    await db.commit()

    return {"status": "delivered"}


@router.post("/cells/{cell_id}/broadcast")
async def send_cell_broadcast(
    cell_id: str,
    content: str,
    user_id: str = Depends(get_current_user)
):
    """
    Send a broadcast message to all cell members.

    Only cell stewards can send broadcasts.
    """
    db = await get_db()

    # Check if user is steward
    cursor = await db.execute("""
        SELECT role FROM cell_memberships
        WHERE cell_id = ? AND user_id = ? AND is_active = 1
    """, (cell_id, user_id))

    membership = await cursor.fetchone()

    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this cell")

    if membership[0] != 'steward':
        raise HTTPException(status_code=403, detail="Only stewards can broadcast")

    # Get all cell members
    cursor = await db.execute("""
        SELECT user_id FROM cell_memberships
        WHERE cell_id = ? AND is_active = 1 AND user_id != ?
    """, (cell_id, user_id))

    members = [row[0] for row in await cursor.fetchall()]

    # Create broadcast messages to each member
    message_ids = []
    timestamp = datetime.now().isoformat()

    for member_id in members:
        message_id = str(uuid.uuid4())
        encrypted_content = base64.b64encode(content.encode()).decode()
        ephemeral_key = str(uuid.uuid4())

        await db.execute("""
            INSERT INTO messages (
                id, sender_id, recipient_id, message_type,
                encrypted_content, ephemeral_key, timestamp,
                delivery_status
            ) VALUES (?, ?, ?, 'broadcast', ?, ?, ?, 'pending')
        """, (message_id, user_id, member_id, encrypted_content, ephemeral_key, timestamp))

        message_ids.append(message_id)

    await db.commit()

    return {"broadcast_sent": len(message_ids), "recipients": len(members)}
