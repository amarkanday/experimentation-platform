# Frontend Development Guide

Frontend-specific guidance for the experimentation platform Next.js application.

## Quick Start

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
# Opens at http://localhost:3000

# Run tests
npm test

# Build for production
npm run build

# Run production build locally
npm start
```

## Directory Structure

```
frontend/
├── src/
│   ├── app/              # Next.js App Router
│   │   ├── layout.tsx    # Root layout
│   │   ├── page.tsx      # Home page
│   │   └── [routes]/     # Dynamic routes
│   ├── components/       # React components
│   │   ├── experiments/  # Experiment-related components
│   │   ├── feature-flags/# Feature flag components
│   │   ├── analytics/    # Analytics & metrics components
│   │   ├── ui/           # Shared UI components
│   │   └── common/       # Common components
│   ├── services/         # API service layer
│   │   ├── api.ts        # Base API client
│   │   ├── experiments.ts
│   │   ├── featureFlags.ts
│   │   └── analytics.ts
│   ├── hooks/            # Custom React hooks
│   ├── lib/              # Utilities and helpers
│   ├── types/            # TypeScript type definitions
│   └── styles/           # Global styles
├── public/               # Static assets
└── package.json
```

## TypeScript Patterns

### Type Definitions

```typescript
// Use interfaces for object shapes
interface Experiment {
  id: string;
  name: string;
  status: ExperimentStatus;
  startDate: Date;
  endDate?: Date;
  variants: Variant[];
}

// Use types for unions and primitives
type ExperimentStatus = 'DRAFT' | 'ACTIVE' | 'PAUSED' | 'COMPLETED';
type UserRole = 'ADMIN' | 'DEVELOPER' | 'ANALYST' | 'VIEWER';

// Component props
interface ExperimentCardProps {
  experiment: Experiment;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}
```

### Component Patterns

```typescript
// Client components (interactive)
'use client';

import { useState } from 'react';
import { Experiment } from '@/types';

export default function ExperimentCard({
  experiment,
  onEdit,
  onDelete
}: ExperimentCardProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleEdit = async () => {
    setIsLoading(true);
    try {
      await onEdit?.(experiment.id);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card">
      <h3>{experiment.name}</h3>
      <button onClick={handleEdit} disabled={isLoading}>
        Edit
      </button>
    </div>
  );
}

// Server components (default in App Router)
import { ExperimentService } from '@/services/experiments';

export default async function ExperimentsPage() {
  const experiments = await ExperimentService.list();

  return (
    <div>
      <h1>Experiments</h1>
      {experiments.map(exp => (
        <ExperimentCard key={exp.id} experiment={exp} />
      ))}
    </div>
  );
}
```

## API Service Layer

### Base API Client

```typescript
// src/services/api.ts
import axios, { AxiosInstance } from 'axios';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth interceptor
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Add error interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Redirect to login
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  get<T>(url: string) {
    return this.client.get<T>(url);
  }

  post<T>(url: string, data?: unknown) {
    return this.client.post<T>(url, data);
  }

  put<T>(url: string, data?: unknown) {
    return this.client.put<T>(url, data);
  }

  delete<T>(url: string) {
    return this.client.delete<T>(url);
  }
}

export const apiClient = new ApiClient();
```

### Resource-Specific Services

```typescript
// src/services/experiments.ts
import { apiClient } from './api';
import { Experiment, CreateExperimentRequest } from '@/types';

export class ExperimentService {
  static async list(): Promise<Experiment[]> {
    const response = await apiClient.get<Experiment[]>('/api/v1/experiments');
    return response.data;
  }

  static async get(id: string): Promise<Experiment> {
    const response = await apiClient.get<Experiment>(`/api/v1/experiments/${id}`);
    return response.data;
  }

  static async create(data: CreateExperimentRequest): Promise<Experiment> {
    const response = await apiClient.post<Experiment>('/api/v1/experiments', data);
    return response.data;
  }

  static async update(id: string, data: Partial<Experiment>): Promise<Experiment> {
    const response = await apiClient.put<Experiment>(`/api/v1/experiments/${id}`, data);
    return response.data;
  }

  static async delete(id: string): Promise<void> {
    await apiClient.delete(`/api/v1/experiments/${id}`);
  }
}
```

## Custom Hooks

### Data Fetching Hook

```typescript
// src/hooks/useExperiments.ts
'use client';

import { useState, useEffect } from 'react';
import { ExperimentService } from '@/services/experiments';
import { Experiment } from '@/types';

export function useExperiments() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchExperiments = async () => {
      try {
        setIsLoading(true);
        const data = await ExperimentService.list();
        setExperiments(data);
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchExperiments();
  }, []);

  const refresh = async () => {
    const data = await ExperimentService.list();
    setExperiments(data);
  };

  return { experiments, isLoading, error, refresh };
}
```

### Form Hook

```typescript
// src/hooks/useForm.ts
import { useState, ChangeEvent, FormEvent } from 'react';

export function useForm<T>(initialValues: T, onSubmit: (values: T) => Promise<void>) {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setValues(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await onSubmit(values);
    } catch (error) {
      console.error('Form submission error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    values,
    errors,
    isSubmitting,
    handleChange,
    handleSubmit,
    setValues,
    setErrors,
  };
}
```

## State Management

### React Context Pattern

```typescript
// src/contexts/AuthContext.tsx
'use client';

import { createContext, useContext, useState, ReactNode } from 'react';
import { User } from '@/types';

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const login = async (email: string, password: string) => {
    // Call login API
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    const data = await response.json();
    setUser(data.user);
    localStorage.setItem('auth_token', data.token);
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('auth_token');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        isAuthenticated: !!user
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

## Styling Guidelines

### Tailwind CSS (Recommended)

```typescript
// Use Tailwind utility classes
export default function Button({ children, variant = 'primary' }) {
  const baseClasses = 'px-4 py-2 rounded font-medium transition-colors';
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
    danger: 'bg-red-600 text-white hover:bg-red-700',
  };

  return (
    <button className={`${baseClasses} ${variantClasses[variant]}`}>
      {children}
    </button>
  );
}
```

### CSS Modules (Alternative)

```typescript
// Button.module.css
.button {
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.primary {
  background-color: #2563eb;
  color: white;
}

.primary:hover {
  background-color: #1d4ed8;
}

// Button.tsx
import styles from './Button.module.css';

export default function Button({ children, variant = 'primary' }) {
  return (
    <button className={`${styles.button} ${styles[variant]}`}>
      {children}
    </button>
  );
}
```

## Testing

### Component Testing

```typescript
// ExperimentCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import ExperimentCard from './ExperimentCard';

describe('ExperimentCard', () => {
  const mockExperiment = {
    id: '1',
    name: 'Test Experiment',
    status: 'ACTIVE',
    startDate: new Date('2024-01-01'),
  };

  it('renders experiment name', () => {
    render(<ExperimentCard experiment={mockExperiment} />);
    expect(screen.getByText('Test Experiment')).toBeInTheDocument();
  });

  it('calls onEdit when edit button clicked', () => {
    const onEdit = jest.fn();
    render(<ExperimentCard experiment={mockExperiment} onEdit={onEdit} />);

    fireEvent.click(screen.getByText('Edit'));
    expect(onEdit).toHaveBeenCalledWith('1');
  });
});
```

### Hook Testing

```typescript
// useExperiments.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useExperiments } from './useExperiments';
import { ExperimentService } from '@/services/experiments';

jest.mock('@/services/experiments');

describe('useExperiments', () => {
  it('fetches experiments on mount', async () => {
    const mockExperiments = [{ id: '1', name: 'Test' }];
    (ExperimentService.list as jest.Mock).mockResolvedValue(mockExperiments);

    const { result } = renderHook(() => useExperiments());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
      expect(result.current.experiments).toEqual(mockExperiments);
    });
  });
});
```

## Performance Optimization

### Code Splitting

```typescript
// Use dynamic imports for heavy components
import dynamic from 'next/dynamic';

const AnalyticsDashboard = dynamic(
  () => import('@/components/analytics/Dashboard'),
  { loading: () => <p>Loading...</p> }
);

export default function AnalyticsPage() {
  return <AnalyticsDashboard />;
}
```

### Memoization

```typescript
import { memo, useMemo, useCallback } from 'react';

// Memo for expensive components
const ExperimentCard = memo(({ experiment }: ExperimentCardProps) => {
  return <div>{experiment.name}</div>;
});

// useMemo for expensive calculations
function ExperimentList({ experiments }) {
  const activeExperiments = useMemo(() => {
    return experiments.filter(exp => exp.status === 'ACTIVE');
  }, [experiments]);

  return <div>{activeExperiments.map(...)}</div>;
}

// useCallback for stable function references
function ExperimentManager() {
  const handleEdit = useCallback((id: string) => {
    console.log('Editing', id);
  }, []);

  return <ExperimentCard onEdit={handleEdit} />;
}
```

## Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ANALYTICS_ID=UA-XXXXXXXXX-X

# Access in code
const apiUrl = process.env.NEXT_PUBLIC_API_URL;
```

**Important**: Only variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.

## Common Development Tasks

### Adding New Page

1. Create file in `src/app/[route]/page.tsx`
2. Define component and data fetching
3. Add navigation link in layout/header
4. Add types in `src/types/`
5. Create service methods if needed

### Adding New Component

1. Create component file in appropriate `src/components/` subdirectory
2. Define TypeScript interface for props
3. Implement component logic
4. Add unit tests
5. Update Storybook if using

### Integration with Backend

1. Define TypeScript types matching backend schemas
2. Create service method in `src/services/`
3. Create custom hook for data fetching
4. Use hook in component
5. Handle loading and error states

## Debugging Tips

- Use React DevTools browser extension
- Enable verbose Next.js logging: `DEBUG=* npm run dev`
- Check Network tab for API calls
- Use `console.log` strategically (remove before commit)
- Add error boundaries for graceful error handling

## Resources

- Next.js Docs: https://nextjs.org/docs
- React Docs: https://react.dev
- TypeScript Handbook: https://www.typescriptlang.org/docs/
- Tailwind CSS: https://tailwindcss.com/docs
