'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode, useState } from 'react';
import axios from 'axios';

export default function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        retry: (failureCount: number, error: unknown) => {
          // 1. Type-safe check: Is this an Axios error?
          if (axios.isAxiosError(error)) {
            // 2. Now we can safely access .response without 'any'
            if (error.response?.status === 429) {
              return false; // Don't retry if we are being rate-limited
            }
          }
          
          // Retry other errors up to 3 times
          return failureCount < 3;
        },
        staleTime: 5 * 60 * 1000,
      },
    },
  }));

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}