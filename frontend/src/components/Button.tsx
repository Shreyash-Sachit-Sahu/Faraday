import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

type ButtonProps = {
  href: string;
  variant?: "solid" | "ghost";
  children: React.ReactNode;
  className?: string;
  arrow?: boolean;
};

export const btnBase =
  "group inline-flex items-center gap-2 whitespace-nowrap rounded-full px-5 py-2.5 text-sm transition-all duration-300 ease-fluid active:scale-[0.97]";

export const btnStyles = (variant: "solid" | "ghost") =>
  variant === "solid"
    ? "glow-copper bg-copper text-ink font-medium hover:brightness-[1.07]"
    : "border border-text/10 text-text hover:border-text/25 hover:bg-surface/60";

/** Nested circular arrow — the "button-in-button" trailing icon. */
export function ArrowChip() {
  return (
    <span className="grid h-6 w-6 place-items-center rounded-full bg-ink/15 transition-transform duration-300 ease-fluid group-hover:translate-x-0.5 group-hover:-translate-y-0.5">
      <ArrowUpRight size={14} strokeWidth={2.25} />
    </span>
  );
}

export function Button({ href, variant = "solid", children, className = "", arrow = false }: ButtonProps) {
  return (
    <Link href={href} className={`${btnBase} ${btnStyles(variant)} ${className}`}>
      {children}
      {arrow && <ArrowChip />}
    </Link>
  );
}

/** Layered copper→field magnet glyph — the wordmark's field-of-force mark. */
export function FieldGlyph({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <span className={`relative inline-block ${className}`} aria-hidden="true">
      <span className="absolute inset-0 rounded-full bg-gradient-to-br from-copper via-volt to-field opacity-90" />
      <span className="absolute inset-[3px] rounded-full bg-ink" />
      <span className="absolute inset-[6px] rounded-full bg-gradient-to-br from-copper to-field" />
    </span>
  );
}

export function Wordmark({ size = "text-xl" }: { size?: string }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <FieldGlyph />
      <span className={`font-display ${size} tracking-tight text-text`}>Faraday</span>
    </span>
  );
}

/** A text link with a field-colored underline that draws on hover/focus. */
export function DrawLink({
  href,
  children,
  className = "",
}: {
  href: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Link
      href={href}
      className={`relative text-muted transition-colors hover:text-text after:absolute after:-bottom-1 after:left-0 after:h-px after:w-0 after:bg-field after:transition-[width] after:duration-300 hover:after:w-full ${className}`}
    >
      {children}
    </Link>
  );
}
