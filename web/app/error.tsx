"use client";

import { ErrorState } from "@/components/ui/error-state";

export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <ErrorState message="Nao foi possivel carregar o Radar agora." onRetry={reset} />;
}
