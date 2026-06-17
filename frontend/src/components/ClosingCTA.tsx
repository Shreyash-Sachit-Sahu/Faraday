import Reveal from "@/components/Reveal";
import AuthCTA from "@/components/AuthCTA";

export default function ClosingCTA() {
  return (
    <Reveal>
      <section className="px-6 py-32">
        <div className="card relative mx-auto max-w-3xl overflow-hidden rounded-[2.25rem] px-6 py-20 text-center">
          <div className="panel-glow" />
          <div className="relative">
            <svg
              viewBox="0 0 400 24"
              className="mx-auto mb-12 w-56 opacity-70"
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
            <h2 className="text-balance font-display text-4xl tracking-tight md:text-6xl">
              Start asking.
            </h2>
            <p className="mx-auto mt-5 max-w-md text-pretty text-muted">
              Make an account and put it to work on something you&rsquo;re stuck on.
            </p>
            <div className="mt-9 flex justify-center">
              <AuthCTA variant="solid" arrow>
                Get started
              </AuthCTA>
            </div>
          </div>
        </div>
      </section>
    </Reveal>
  );
}
