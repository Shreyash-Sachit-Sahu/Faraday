"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { ArrowChip, btnBase, btnStyles } from "@/components/Button";

/** Primary "start" CTA: routes signed-in users to /chat, everyone else to /register. */
export default function AuthCTA({
  children,
  variant = "solid",
  className = "",
  arrow = false,
}: {
  children: React.ReactNode;
  variant?: "solid" | "ghost";
  className?: string;
  arrow?: boolean;
}) {
  const router = useRouter();
  const { user } = useAuth();
  return (
    <button
      onClick={() => router.push(user ? "/chat" : "/register")}
      className={`${btnBase} ${btnStyles(variant)} ${className}`}
    >
      {children}
      {arrow && <ArrowChip />}
    </button>
  );
}
