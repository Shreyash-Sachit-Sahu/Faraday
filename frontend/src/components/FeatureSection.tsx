import Reveal from "@/components/Reveal";

export default function FeatureSection({
  index,
  title,
  body,
  visual,
  reverse = false,
}: {
  index: string;
  title: string;
  body: string;
  visual: React.ReactNode;
  reverse?: boolean;
}) {
  return (
    <Reveal>
      <div className="grid items-center gap-10 md:grid-cols-2 md:gap-16">
        <div className={reverse ? "md:order-2" : ""}>
          <span className="inline-flex items-center gap-2 font-mono text-xs tracking-[0.18em] text-copper">
            <span className="h-1.5 w-1.5 rounded-full bg-copper" />
            {index}
          </span>
          <h3 className="mt-4 text-balance font-display text-3xl tracking-tight md:text-4xl">
            {title}
          </h3>
          <p className="mt-4 max-w-md text-pretty leading-relaxed text-muted">{body}</p>
        </div>
        {/* double-bezel: outer shell + inner core */}
        <div
          className={`rounded-[1.75rem] border border-text/8 bg-surface/30 p-2 transition-transform duration-500 ease-fluid hover:-translate-y-1 ${
            reverse ? "md:order-1" : ""
          }`}
        >
          <div className="card rounded-[1.25rem] p-6">{visual}</div>
        </div>
      </div>
    </Reveal>
  );
}
