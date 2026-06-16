import Reveal from "@/components/Reveal";
import AuthCTA from "@/components/AuthCTA";

export default function ClosingCTA() {
  return (
    <Reveal>
      <section className="relative py-32 text-center">
        <svg
          viewBox="0 0 400 24"
          className="mx-auto mb-16 w-64 opacity-70"
          aria-hidden="true"
        >
          <defs>
            <linearGradient id="cta-field-line" x1="0" x2="1">
              <stop offset="0" stopColor="#e0915f" stopOpacity="0" />
              <stop offset="0.5" stopColor="#5bc8e8" />
              <stop offset="1" stopColor="#e0915f" stopOpacity="0" />
            </linearGradient>
          </defs>
          <path
            d="M0 12 C 100 2, 300 22, 400 12"
            stroke="url(#cta-field-line)"
            strokeWidth="1.5"
            fill="none"
          />
        </svg>
        <h2 className="font-display text-4xl tracking-tight md:text-5xl">Start asking.</h2>
        <p className="mx-auto mt-5 max-w-md text-muted">
          Make an account and put it to work on something you&rsquo;re stuck on.
        </p>
        <div className="mt-9 flex justify-center">
          <AuthCTA variant="solid">Get started</AuthCTA>
        </div>
      </section>
    </Reveal>
  );
}
