/** The four small capability visuals — copper/field palette only, calm and concrete. */

export function ShowsWorkVisual() {
  return (
    <div className="space-y-4">
      <p className="text-sm leading-relaxed text-text">
        A binary search tree keeps keys ordered, so lookups, inserts, and deletes run
        in O(log n) on a balanced tree.
      </p>
      <div className="flex flex-wrap gap-2">
        <span className="rounded-md border border-surface-2 bg-ink px-2.5 py-1 font-mono text-xs text-field">
          [1] Binary search tree
        </span>
        <span className="rounded-md border border-surface-2 bg-ink px-2.5 py-1 font-mono text-xs text-field">
          [2] B-tree
        </span>
      </div>
    </div>
  );
}

export function FieldVisual() {
  const nodes = [
    { x: 40, y: 96, c: "#e0915f" },
    { x: 120, y: 40, c: "#5bc8e8" },
    { x: 120, y: 116, c: "#e0915f" },
    { x: 200, y: 70, c: "#5bc8e8" },
    { x: 168, y: 30, c: "#8b7fe8" },
  ];
  return (
    <svg viewBox="0 0 240 150" className="w-full" aria-hidden="true">
      <g fill="none" strokeWidth="1.4" opacity="0.65">
        <path d="M40 96 C 80 50, 100 44, 120 40" stroke="#e0915f" />
        <path d="M40 96 C 80 110, 100 112, 120 116" stroke="#e0915f" />
        <path d="M120 40 C 150 44, 180 56, 200 70" stroke="#5bc8e8" />
        <path d="M120 116 C 150 104, 180 86, 200 70" stroke="#5bc8e8" />
        <path d="M120 40 C 140 34, 156 32, 168 30" stroke="#8b7fe8" />
      </g>
      {nodes.map((n, i) => (
        <g key={i}>
          <circle cx={n.x} cy={n.y} r="9" fill={n.c} opacity="0.18" />
          <circle cx={n.x} cy={n.y} r="4" fill={n.c} />
        </g>
      ))}
    </svg>
  );
}

export function NotesVisual() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4 rounded-lg border border-surface-2 bg-ink px-4 py-3">
        <span className="font-mono text-sm text-text">algorithms-lecture.pdf</span>
        <span className="flex items-center gap-2 font-mono text-xs">
          <span className="text-muted line-through">Pending</span>
          <span className="text-muted">→</span>
          <span className="text-field">Indexed</span>
        </span>
      </div>
      <p className="font-mono text-xs text-muted">
        visible only in your account · 24 passages
      </p>
    </div>
  );
}

export function PlainVisual() {
  return (
    <pre className="overflow-x-auto rounded-lg border border-surface-2 bg-ink p-4 font-mono text-xs leading-relaxed">
      <code>
        <span className="text-volt">def</span>{" "}
        <span className="text-field">is_palindrome</span>
        <span className="text-text">(s):</span>
        {"\n    "}
        <span className="text-volt">return</span>{" "}
        <span className="text-text">s == s[::-</span>
        <span className="text-copper">1</span>
        <span className="text-text">]</span>
      </code>
    </pre>
  );
}
