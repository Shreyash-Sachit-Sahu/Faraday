"use client";

import { Button, DrawLink, Wordmark } from "@/components/Button";
import { useAuth } from "@/lib/auth";

export default function SiteNav() {
  const { user, ready, logout } = useAuth();

  return (
    <header className="fixed inset-x-0 top-3 z-50 px-4">
      <nav className="glass mx-auto flex w-[min(96%,1080px)] items-center justify-between rounded-full py-2.5 pl-5 pr-2.5">
        <a href="#top" aria-label="Faraday home">
          <Wordmark />
        </a>
        <div className="flex items-center gap-3 sm:gap-5">
          <DrawLink href="#features" className="hidden text-sm sm:inline">
            How it works
          </DrawLink>
          {ready && user ? (
            <>
              <span className="hidden font-mono text-xs text-muted sm:inline">
                {user.displayName}
              </span>
              <button
                onClick={() => logout()}
                className="rounded-full border border-text/10 px-4 py-2 text-sm text-text transition-all duration-300 ease-fluid hover:border-text/25 hover:bg-surface/60 active:scale-[0.97]"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Button href="/login" variant="ghost" className="hidden sm:inline-flex">
                Sign in
              </Button>
              <Button href="/register" variant="solid" arrow>
                Get started
              </Button>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
