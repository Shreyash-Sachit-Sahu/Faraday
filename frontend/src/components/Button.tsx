import Link from "next/link";

type ButtonProps = {
  href: string;
  variant?: "solid" | "ghost";
  children: React.ReactNode;
  className?: string;
};

const base =
  "inline-flex items-center justify-center whitespace-nowrap rounded-full px-6 py-3 text-sm transition";

export function Button({ href, variant = "solid", children, className = "" }: ButtonProps) {
  const styles =
    variant === "solid"
      ? "bg-copper text-ink font-medium hover:brightness-110"
      : "border border-surface-2 text-text hover:bg-surface";
  return (
    <Link href={href} className={`${base} ${styles} ${className}`}>
      {children}
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
