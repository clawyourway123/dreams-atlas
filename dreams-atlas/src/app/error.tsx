'use client';

import { useEffect } from 'react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('App error:', error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center bg-navy-950">
      <div className="mx-auto max-w-md text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-red-500/10">
          <svg className="h-8 w-8 text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-white">Something went wrong</h2>
        <p className="mt-2 text-sm text-navy-400">
          An unexpected error occurred while rendering this page.
        </p>
        <button
          onClick={reset}
          className="mt-6 rounded-card border border-teal-400/20 bg-teal-500/10 px-6 py-2.5 text-sm font-medium text-teal-400 transition-colors hover:bg-teal-500/20"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
