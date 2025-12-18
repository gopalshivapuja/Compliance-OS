/**
 * Utility Functions - Barrel Export
 *
 * Re-exports all utility functions from specialized modules.
 * This maintains backward compatibility while allowing tree-shaking.
 *
 * Usage:
 * import { formatDate, cn, debounce } from '@/lib/utils'
 *
 * Or import from specific modules:
 * import { formatDate } from '@/lib/utils/date'
 * import { cn } from '@/lib/utils/format'
 */

// Date utilities
export { formatDate, formatDateTime, daysUntilDue } from './date';

// File utilities
export { formatFileSize, getFileExtension, downloadBlob } from './file';

// String utilities
export { truncate, getInitials } from './string';

// Format utilities
export { cn, formatCurrency } from './format';

// DOM utilities
export { copyToClipboard } from './dom';

// Async utilities
export { debounce, sleep } from './async';

// Validation utilities
export { isEmpty } from './validation';

// Query string utilities
export { parseQueryParams, buildQueryString } from './query';
