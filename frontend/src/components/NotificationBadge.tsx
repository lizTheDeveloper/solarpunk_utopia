import { Bell } from 'lucide-react';

interface NotificationBadgeProps {
  count: number;
  onClick: () => void;
  isOpen: boolean;
}

export function NotificationBadge({ count, onClick, isOpen }: NotificationBadgeProps) {
  return (
    <button
      onClick={onClick}
      className={`relative p-2 hover:bg-gray-100 rounded-full transition-colors ${
        isOpen ? 'bg-gray-100' : ''
      }`}
      aria-label={`${count} pending notifications`}
      aria-expanded={isOpen}
    >
      <Bell className="w-6 h-6 text-gray-600" />
      {count > 0 && (
        <span className="absolute top-0 right-0 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
          {count > 9 ? '9+' : count}
        </span>
      )}
    </button>
  );
}
