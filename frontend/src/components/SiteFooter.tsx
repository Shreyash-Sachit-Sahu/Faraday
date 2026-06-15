import { Wordmark } from "@/components/Button";

export default function SiteFooter() {
  return (
    <footer className="border-t border-surface-2">
      <div className="mx-auto flex max-w-[1100px] flex-col items-start gap-5 px-6 py-12 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-2">
          <Wordmark size="text-lg" />
          <p className="text-sm text-muted">A computer-science tutor.</p>
        </div>
        <p className="font-mono text-xs text-muted">
          Faraday · {new Date().getFullYear()}
        </p>
      </div>
    </footer>
  );
}
