"use client";

import { useEffect, useRef, useState } from "react";

function AnimatedNumber({ target, suffix = "", duration = 1200 }: { target: number; suffix?: string; duration?: number }) {
  const [value, setValue] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        observer.disconnect();
        const start = performance.now();
        function tick(now: number) {
          const t = Math.min((now - start) / duration, 1);
          const eased = 1 - Math.pow(1 - t, 3);
          setValue(Math.round(eased * target));
          if (t < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
      },
      { threshold: 0.3 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [target, duration]);

  return <span ref={ref}>{value}{suffix}</span>;
}

export default function StatsBar({
  totalFindings,
  critical,
  major,
  maxLeadWeeks,
  meanLeadWeeks,
  systemsScanned,
}: {
  totalFindings: number;
  critical: number;
  major: number;
  maxLeadWeeks: number;
  meanLeadWeeks: number;
  systemsScanned: number;
}) {
  const totalSavings = 144;

  return (
    <div className="stats-bar">
      <div className="stat">
        <div className="stat-val stat-critical">
          <AnimatedNumber target={totalFindings} />
        </div>
        <div className="stat-label">Deviations found</div>
      </div>
      <div className="stat">
        <div className="stat-val stat-critical">
          <AnimatedNumber target={critical} />
        </div>
        <div className="stat-label">Critical</div>
      </div>
      <div className="stat">
        <div className="stat-val stat-warn">
          <AnimatedNumber target={major} />
        </div>
        <div className="stat-label">Major</div>
      </div>
      <div className="stat">
        <div className="stat-val stat-lead">
          <AnimatedNumber target={maxLeadWeeks} suffix="w" />
        </div>
        <div className="stat-label">Max lead time</div>
      </div>
      <div className="stat">
        <div className="stat-val stat-lead">
          <AnimatedNumber target={meanLeadWeeks} suffix="w" />
        </div>
        <div className="stat-label">Mean lead time</div>
      </div>
      <div className="stat stat-hero">
        <div className="stat-val stat-lead">
          <AnimatedNumber target={totalSavings} suffix="w" duration={1800} />
        </div>
        <div className="stat-label">Total savings</div>
      </div>
    </div>
  );
}
