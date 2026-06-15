"use client";

import { useEffect, useState } from "react";
import { Button, DrawLink, Wordmark } from "@/components/Button";
import { useAuth } from "@/lib/auth";

export default function SiteNav() {
  const [scrolled, setScrolled] = useState(false);
  const { user, ready, logout } = useAuth();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-colors duration-300 ${
        scrolled
          ? "border-b border-surface-2 bg-ink/70 backdrop-blur-md"
          : "border-b border-transparent"
      }`}
    >
      <nav className="mx-auto flex max-w-[1100px] items-center justify-between px-6 py-4">
        <a href="#top" aria-label="Faraday home">
          <Wordmark />
        </a>
        <div className="flex items-center gap-4 sm:gap-6">
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
                className="whitespace-nowrap rounded-full border border-surface-2 px-5 py-2 text-sm text-text transition hover:bg-surface"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Button href="/login" variant="ghost" className="px-5 py-2">
                Sign in
              </Button>
              <Button href="/register" variant="solid" className="px-5 py-2">
                Get started
              </Button>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
