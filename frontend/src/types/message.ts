export interface Message {
  id: string;
  sender_id: string;
  recipient_id: string;
  thread_id?: string;
  message_type: 'direct' | 'exchange' | 'broadcast' | 'alert';
  encrypted_content: string;
  ephemeral_key: string;
  timestamp: string;
  expires_at?: string;
  delivery_status: 'pending' | 'delivered' | 'read';
  delivered_at?: string;
  read_at?: string;
}

export interface MessageThread {
  id: string;
  thread_type: string;
  participants: string[];
  exchange_id?: string;
  cell_id?: string;
  created_at: string;
  last_message_at?: string;
  last_message_preview?: string;
  unread_count: number;
}

export interface SendMessageRequest {
  recipient_id: string;
  content: string;
  thread_id?: string;
  message_type?: 'direct' | 'exchange' | 'broadcast' | 'alert';
  expires_in_hours?: number;
  exchange_id?: string;
}
