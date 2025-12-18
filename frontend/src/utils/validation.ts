// Form validation helpers

export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

// Validate required field
export const validateRequired = (value: any, fieldName: string): ValidationResult => {
  if (value === null || value === undefined || value === '') {
    return {
      valid: false,
      errors: [`${fieldName} is required`],
    };
  }
  return { valid: true, errors: [] };
};

// Validate number (positive)
export const validatePositiveNumber = (value: any, fieldName: string): ValidationResult => {
  const num = Number(value);
  if (isNaN(num) || num <= 0) {
    return {
      valid: false,
      errors: [`${fieldName} must be a positive number`],
    };
  }
  return { valid: true, errors: [] };
};

// Validate number (non-negative)
export const validateNonNegativeNumber = (value: any, fieldName: string): ValidationResult => {
  const num = Number(value);
  if (isNaN(num) || num < 0) {
    return {
      valid: false,
      errors: [`${fieldName} must be a non-negative number`],
    };
  }
  return { valid: true, errors: [] };
};

// Validate date (not in the past)
export const validateFutureDate = (value: string, fieldName: string): ValidationResult => {
  const date = new Date(value);
  const now = new Date();
  if (date < now) {
    return {
      valid: false,
      errors: [`${fieldName} must be in the future`],
    };
  }
  return { valid: true, errors: [] };
};

// Validate date range
export const validateDateRange = (
  from: string,
  until: string,
  fromFieldName: string,
  untilFieldName: string
): ValidationResult => {
  const fromDate = new Date(from);
  const untilDate = new Date(until);

  if (untilDate <= fromDate) {
    return {
      valid: false,
      errors: [`${untilFieldName} must be after ${fromFieldName}`],
    };
  }
  return { valid: true, errors: [] };
};

// Validate string length
export const validateLength = (
  value: string,
  min: number,
  max: number,
  fieldName: string
): ValidationResult => {
  if (value.length < min || value.length > max) {
    return {
      valid: false,
      errors: [`${fieldName} must be between ${min} and ${max} characters`],
    };
  }
  return { valid: true, errors: [] };
};

// Validate offer/need form
export const validateIntentForm = (data: {
  resourceSpecificationId?: string;
  quantity?: number;
  unit?: string;
  location?: string;
}): ValidationResult => {
  const errors: string[] = [];

  if (!data.resourceSpecificationId) {
    errors.push('Resource is required');
  }

  if (!data.quantity || data.quantity <= 0) {
    errors.push('Quantity must be greater than 0');
  }

  if (!data.unit) {
    errors.push('Unit is required');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
};

// Validate file upload
export const validateFileUpload = (file: File, maxSizeMB: number = 50): ValidationResult => {
  const errors: string[] = [];

  if (!file) {
    errors.push('File is required');
  } else {
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      errors.push(`File size must be less than ${maxSizeMB}MB`);
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  };
};

// Validate search query
export const validateSearchQuery = (query: string): ValidationResult => {
  if (!query || query.trim().length < 2) {
    return {
      valid: false,
      errors: ['Search query must be at least 2 characters'],
    };
  }
  return { valid: true, errors: [] };
};

// Combine multiple validation results
export const combineValidationResults = (...results: ValidationResult[]): ValidationResult => {
  const allErrors = results.flatMap((r) => r.errors);
  return {
    valid: allErrors.length === 0,
    errors: allErrors,
  };
};
