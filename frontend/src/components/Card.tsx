import { ReactNode } from 'react';
import { clsx } from 'clsx';

interface CardProps {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export function Card({ children, className, onClick, hoverable = false }: CardProps) {
  return (
    <div
      className={clsx(
        'bg-white rounded-lg shadow-md p-6 border border-gray-200',
        hoverable && 'hover:shadow-lg transition-shadow cursor-pointer',
        onClick && 'cursor-pointer',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
}
