"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { GoogleLogin } from "@react-oauth/google";
import { useAuth } from "@/lib/auth";
import AuthShell from "@/components/AuthShell";

const inputCls =
  "field-input w-full rounded-xl border border-surface-2 bg-ink/50 px-4 py-3 text-text placeholder:text-muted outline-none";

export default function RegisterPage() {
  const router = useRouter();
  const { user, ready, register, loginWithGoogle } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (ready && user) router.replace("/chat");
  }, [ready, user, router]);

  const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const passwordValid = password.length >= 12;
  const nameValid = displayName.trim().length > 0;
  const formValid = emailValid && passwordValid && nameValid;

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formValid || submitting) return;
    setError(null);
    setSubmitting(true);
    try {
      await register(email, password, displayName);
      router.push("/chat");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  };

  const onGoogle = async (credential?: string) => {
    if (!credential) return;
    setError(null);
    try {
      await loginWithGoogle(credential);
      router.push("/chat");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Google sign-in failed.");
    }
  };

  return (
    <AuthShell>
      <h1 className="mt-6 font-display text-2xl tracking-tight">Create your account</h1>
      <p className="mt-1 text-sm text-muted">Start asking &mdash; it&rsquo;s free.</p>

      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <div>
          <label htmlFor="email" className="font-mono text-xs text-muted">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={`mt-1 ${inputCls}`}
            placeholder="you@university.edu"
          />
        </div>
        <div>
          <label htmlFor="displayName" className="font-mono text-xs text-muted">
            Display name
          </label>
          <input
            id="displayName"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className={`mt-1 ${inputCls}`}
            placeholder="Ada"
          />
        </div>
        <div>
          <label
            htmlFor="password"
            className="flex items-center justify-between font-mono text-xs text-muted"
          >
            <span>Password</span>
            <span
              className={
                password.length === 0
                  ? "text-muted"
                  : passwordValid
                    ? "text-field"
                    : "text-copper"
              }
            >
              12+ characters
            </span>
          </label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={`mt-1 ${inputCls}`}
            placeholder="a long passphrase"
          />
        </div>

        {error && (
          <p
            role="alert"
            className="rounded-lg border border-copper/40 bg-copper/10 px-3 py-2 text-sm text-copper"
          >
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={!formValid || submitting}
          className="glow-copper w-full rounded-full bg-copper px-6 py-3 text-sm font-medium text-ink transition-all duration-300 ease-fluid hover:brightness-110 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
        >
          {submitting ? "Creating…" : "Create account"}
        </button>
      </form>

      <div className="my-6 flex items-center gap-3 font-mono text-xs text-muted">
        <span className="h-px flex-1 bg-surface-2" /> or
        <span className="h-px flex-1 bg-surface-2" />
      </div>

      <div className="flex justify-center">
        <GoogleLogin
          onSuccess={(c) => onGoogle(c.credential)}
          onError={() => setError("Google sign-in was cancelled or failed.")}
          theme="filled_black"
          shape="pill"
        />
      </div>

      <p className="mt-6 text-center text-sm text-muted">
        Already have an account?{" "}
        <Link href="/login" className="text-field hover:underline">
          Sign in.
        </Link>
      </p>
    </AuthShell>
  );
}
