"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

/** Primary "start" CTA: routes signed-in users to /chat, everyone else to /register. */
export default function AuthCTA({
  children,
  variant = "solid",
  className = "",
}: {
  children: React.ReactNode;
  variant?: "solid" | "ghost";
  className?: string;
}) {
  const router = useRouter();
  const { user } = useAuth();
  const base =
    "inline-flex items-center justify-center whitespace-nowrap rounded-full px-6 py-3 text-sm transition";
  const styles =
    variant === "solid"
      ? "bg-copper text-ink font-medium hover:brightness-110"
      : "border border-surface-2 text-text hover:bg-surface";
  return (
    <button
      onClick={() => router.push(user ? "/chat" : "/register")}
      className={`${base} ${styles} ${className}`}
    >
      {children}
    </button>
  );
}
