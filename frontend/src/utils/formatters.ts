// Utility functions for formatting data
import { formatDistanceToNow, format, parseISO } from 'date-fns';

// Date formatting
export const formatDate = (date: string | Date): string => {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, 'MMM d, yyyy');
};

export const formatDateTime = (date: string | Date): string => {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, 'MMM d, yyyy h:mm a');
};

export const formatTimeAgo = (date: string | Date): string => {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return formatDistanceToNow(dateObj, { addSuffix: true });
};

// Quantity formatting
export const formatQuantity = (quantity: number, unit?: string): string => {
  const formattedQty = quantity % 1 === 0 ? quantity.toString() : quantity.toFixed(2);
  return unit ? `${formattedQty} ${unit}` : formattedQty;
};

// File size formatting
export const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Duration formatting
export const formatDuration = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds}s`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    return `${minutes}m`;
  } else if (seconds < 86400) {
    const hours = Math.floor(seconds / 3600);
    return `${hours}h`;
  } else {
    const days = Math.floor(seconds / 86400);
    return `${days}d`;
  }
};

// Percentage formatting
export const formatPercentage = (value: number, total: number): string => {
  if (total === 0) return '0%';
  const percentage = (value / total) * 100;
  return `${percentage.toFixed(1)}%`;
};

// Status formatting
export const formatStatus = (status: string): string => {
  return status
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

// Agent name formatting (remove underscores, capitalize)
export const formatAgentName = (agentType: string): string => {
  return agentType
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

// Location formatting
export const formatLocation = (location?: string): string => {
  if (!location) return 'No location specified';
  return location;
};

// Truncate text
export const truncate = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};

// Bundle ID formatting (show first 8 chars)
export const formatBundleId = (id: string): string => {
  return id.slice(0, 8);
};

// Confidence score formatting (0-1 to percentage)
export const formatConfidence = (confidence: number): string => {
  return `${(confidence * 100).toFixed(0)}%`;
};
