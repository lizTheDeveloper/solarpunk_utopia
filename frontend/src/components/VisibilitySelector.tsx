import React from 'react';
import { FormControl, FormLabel, Select, FormHelperText } from '@chakra-ui/react';

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
    <FormControl>
      <FormLabel>Who can see this?</FormLabel>
      <Select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Choose visibility level"
      >
        {visibilityOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label} - {option.description}
          </option>
        ))}
      </Select>
      {helperText && <FormHelperText>{helperText}</FormHelperText>}
      {!helperText && (
        <FormHelperText>
          This controls who can discover and see your listing. You're always in control.
        </FormHelperText>
      )}
    </FormControl>
  );
};
