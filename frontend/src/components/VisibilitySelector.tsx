import React from 'react';

interface VisibilitySelectorProps {
  value?: string;
  onChange: (value: string) => void;
  helperText?: string;
}

const visibilityOptions = [
  {
    value: 'my_cell',
    label: 'My Cell Only',
    description: 'Only your immediate affinity group (5-50 people)',
  },
  {
    value: 'my_community',
    label: 'My Community',
    description: 'Everyone in your community',
  },
  {
    value: 'trusted_network',
    label: 'Trusted Network (Default)',
    description: 'Anyone you trust (trust score >= 0.5)',
  },
  {
    value: 'anyone_local',
    label: 'Anyone Local',
    description: 'Anyone within your local radius',
  },
  {
    value: 'network_wide',
    label: 'Network Wide',
    description: 'Anyone with minimal trust (>= 0.1)',
  },
];

export const VisibilitySelector: React.FC<VisibilitySelectorProps> = ({
  value = 'trusted_network',
  onChange,
  helperText,
}) => {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Who can see this?
      </label>
      <select
        value={value}
        onChange={(e: React.ChangeEvent<HTMLSelectElement>) => onChange(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
      >
        {visibilityOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label} - {option.description}
          </option>
        ))}
      </select>
      {helperText && (
        <p className="mt-1 text-sm text-gray-500">{helperText}</p>
      )}
      {!helperText && (
        <p className="mt-1 text-sm text-gray-500">
          This controls who can discover and see your listing. You're always in control.
        </p>
      )}
    </div>
  );
};
