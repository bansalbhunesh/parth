"use client";

import { useEffect } from "react";

// Route-level error boundary. The client <ErrorBoundary> only catches errors
// after it mounts; this catches errors thrown during the async Server Component
// render of a route (page.tsx / judge/page.tsx) — e.g. a degraded gateway
// returning a 200 with an unexpected shape — so a render failure shows a friendly
// recoverable card instead of a bare Next.js 500.
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Route render error:", error);
  }, [error]);

  return (
    <div className="error-boundary">
      <div className="error-boundary-icon">!</div>
      <div className="error-boundary-title">Something went wrong</div>
      <div className="error-boundary-msg">
        This page failed to render. The API may be unavailable or returned an
        unexpected response. The product normally falls back to bundled data —
        try again.
      </div>
      <button className="error-boundary-retry" onClick={() => reset()}>
        Try again
      </button>
    </div>
  );
}
