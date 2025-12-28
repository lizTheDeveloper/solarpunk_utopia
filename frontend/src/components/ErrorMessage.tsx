import { AlertCircle } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  title?: string;
}

export function ErrorMessage({ message, title = 'Error' }: ErrorMessageProps) {
  return (
    <div
      className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3"
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <div>
        <h3 className="font-medium text-red-900">{title}</h3>
        <p className="text-red-700 text-sm mt-1">{message}</p>
      </div>
    </div>
  );
}
