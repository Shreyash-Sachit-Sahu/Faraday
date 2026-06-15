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
          <p className="font-mono text-xs tracking-[0.18em] text-copper">{index}</p>
          <h3 className="mt-3 font-display text-3xl tracking-tight md:text-4xl">{title}</h3>
          <p className="mt-4 max-w-md leading-relaxed text-muted">{body}</p>
        </div>
        <div
          className={`rounded-2xl border border-surface-2 bg-surface p-6 ${
            reverse ? "md:order-1" : ""
          }`}
        >
          {visual}
        </div>
      </div>
    </Reveal>
  );
}
