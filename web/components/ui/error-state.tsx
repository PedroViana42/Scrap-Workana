"use client";

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="panel flex min-h-48 flex-col items-center justify-center gap-3 border-red-200 bg-red-50 p-8 text-center">
      <h2 className="text-base font-semibold text-red-900">{message}</h2>
      {onRetry ? (
        <button className="rounded-md border border-red-300 bg-white px-3 py-1.5 text-sm font-medium text-red-800" onClick={onRetry} type="button">
          Tentar novamente
        </button>
      ) : null}
    </div>
  );
}
