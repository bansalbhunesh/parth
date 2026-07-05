"use client";

import { useEffect, useRef, useState } from "react";
import { getMetrics } from "../lib/api";

function AnimatedMetric({ value, label, suffix = "", color = "var(--lead)", delay = 0 }: {
  value: number; label: string; suffix?: string; color?: string; delay?: number;
}) {
  const [current, setCurrent] = useState(0);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        observer.disconnect();
        // Honor prefers-reduced-motion: the CSS rule only zeroes CSS animations,
        // not this rAF count-up, so gate it explicitly and snap to the final value.
        if (typeof window !== "undefined" &&
            window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
          setCurrent(value);
          return;
        }
        setTimeout(() => {
          const start = performance.now();
          function tick(now: number) {
            const t = Math.min((now - start) / 1400, 1);
            const eased = 1 - Math.pow(1 - t, 4);
            setCurrent(Math.round(eased * value * 1000) / 1000);
            if (t < 1) requestAnimationFrame(tick);
          }
          requestAnimationFrame(tick);
        }, delay);
      },
      { threshold: 0.2 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [value, delay]);

  return (
    <div className="eval-metric" ref={ref}>
      <div className="eval-metric-val" style={{ color }}>
        {current.toFixed(3)}{suffix}
      </div>
      <div className="eval-metric-label">{label}</div>
      <div className="eval-metric-bar">
        <div
          className="eval-metric-fill"
          style={{ width: `${current * 100}%`, background: color }}
        />
      </div>
    </div>
  );
}

interface Metrics {
  detection: {
    total_deviations: number;
    critical: number;
    major: number;
    baseline_precision: number;
    baseline_recall: number;
    baseline_f1: number;
    false_positive_rate: number;
  };
  commissioning: {
    cx_prediction_accuracy: number;
    mean_lead_time_weeks: number;
    max_lead_time_weeks: number;
    total_lead_time_weeks: number;
  };
  corpus: {
    systems: number;
    total_requirements: number;
    true_negative_systems: number;
  };
  citation_faithfulness: number;
}

const FALLBACK: Metrics = {
  detection: {
    total_deviations: 14, critical: 7, major: 6,
    baseline_precision: 1.0, baseline_recall: 1.0, baseline_f1: 1.0,
    false_positive_rate: 0.0,
  },
  commissioning: {
    cx_prediction_accuracy: 1.0,
    mean_lead_time_weeks: 19.1, max_lead_time_weeks: 33,
    total_lead_time_weeks: 267,
  },
  corpus: { systems: 7, total_requirements: 14000, true_negative_systems: 3 },
  citation_faithfulness: 1.0,
};

export default function EvalDashboard() {
  const [m, setM] = useState<Metrics>(FALLBACK);
  const [live, setLive] = useState(false);

  useEffect(() => {
    getMetrics().then((data) => {
      // A degraded backend returns {detection:{}, error:...} with HTTP 200.
      // Only switch to live data when a real numeric metric is present, so the
      // dashboard never renders NaN / crashes on `.toFixed` of undefined.
      const d = data as { detection?: { baseline_f1?: unknown }; error?: unknown } | null;
      if (d && !d.error && d.detection && typeof d.detection.baseline_f1 === "number") {
        setM(data as unknown as Metrics);
        setLive(true);
      }
    });
  }, []);

  return (
    <div className="eval-dashboard">
      <div className="eval-header">
        <div className="eval-badge">
          EVAL HARNESS
          {live && <span className="eval-live-dot" />}
        </div>
        <div className="eval-desc">
          This is the <strong>synthetic-corpus integrity check</strong>: the deterministic harness recovers
          every seeded deviation <em>by construction</em>, which is why these numbers are 1.000 — a plumbing
          check, not an accuracy claim. The measured accuracy signal is the frozen <code>ps4_external_v1</code>
          benchmark (v1.2): <strong>recall 0.862 · precision 0.953 · F1 0.905 · FAR 0.000</strong> — see{" "}
          <a href="/evidence" style={{ color: "var(--accent)" }}>/evidence</a>. All metrics computed by{" "}
          <code>eval/run_eval.py</code> — reproducible, auditable, no cherry-picking.
          {live && <span style={{ color: "var(--ok)", marginLeft: 8, fontSize: 11 }}>LIVE from /metrics</span>}
        </div>
      </div>

      <div className="eval-grid">
        <div className="eval-section">
          <div className="eval-section-title">Detection · synthetic corpus (by construction)</div>
          <AnimatedMetric value={m.detection.baseline_precision} label="Precision" color="var(--ok)" delay={0} />
          <AnimatedMetric value={m.detection.baseline_recall} label="Recall" color="var(--ok)" delay={150} />
          <AnimatedMetric value={m.detection.baseline_f1} label="F1 Score" color="var(--ok)" delay={300} />
        </div>

        <div className="eval-section">
          <div className="eval-section-title">Quality metrics</div>
          <AnimatedMetric value={m.commissioning.cx_prediction_accuracy} label="Cx-test prediction accuracy" color="var(--lead)" delay={200} />
          <AnimatedMetric value={m.citation_faithfulness} label="Citation faithfulness" color="var(--accent)" delay={350} />
          <AnimatedMetric value={1.0 - m.detection.false_positive_rate} label="True-negative accuracy" color="var(--warn)" delay={500} />
        </div>

        <div className="eval-section">
          <div className="eval-section-title">Impact</div>
          <div className="eval-impact-row">
            <div className="eval-impact">
              <div className="eval-impact-val" style={{ color: "var(--lead)" }}>{m.commissioning.total_lead_time_weeks}w</div>
              <div className="eval-impact-label">Total lead-time window (scenario)</div>
            </div>
            <div className="eval-impact">
              <div className="eval-impact-val" style={{ color: "var(--lead)" }}>{m.commissioning.max_lead_time_weeks}w</div>
              <div className="eval-impact-label">Max single finding</div>
            </div>
            <div className="eval-impact">
              <div className="eval-impact-val" style={{ color: "var(--fault)" }}>{m.detection.total_deviations}</div>
              <div className="eval-impact-label">Deviations caught</div>
            </div>
            <div className="eval-impact">
              <div className="eval-impact-val" style={{ color: "var(--ok)" }}>{Math.round(m.detection.false_positive_rate * 100)}</div>
              <div className="eval-impact-label">False positives</div>
            </div>
          </div>
        </div>
      </div>

      <div className="eval-comparison">
        <div className="eval-comparison-title">Synthetic corpus (by construction) vs reasoning-core target</div>
        <div className="eval-comparison-grid">
          <div className="eval-comp-header">Metric</div>
          <div className="eval-comp-header">Synthetic corpus (deterministic)</div>
          <div className="eval-comp-header">Reasoning core (acceptance target)</div>

          {[
            ["Precision", m.detection.baseline_precision.toFixed(3), "≥ 0.85"],
            ["Recall", m.detection.baseline_recall.toFixed(3), "≥ 0.85"],
            ["F1", m.detection.baseline_f1.toFixed(3), "≥ 0.92"],
            ["Cx prediction", m.commissioning.cx_prediction_accuracy.toFixed(3), "≥ 0.85"],
            ["Citations", "N/A", "≥ 0.95"],
            ["Unstructured input", "No", "Yes"],
          ].map(([metric, baseline, llm]) => (
            <div key={metric} style={{ display: "contents" }}>
              <div className="eval-comp-cell eval-comp-metric">{metric}</div>
              <div className="eval-comp-cell eval-comp-baseline">{baseline}</div>
              <div className="eval-comp-cell eval-comp-llm">{llm}</div>
            </div>
          ))}
        </div>
        <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 10 }}>
          Left column: the synthetic corpus recovers all seeded deviations by construction (integrity check).
          Right column: acceptance targets, not measured scores. The measured reasoning-core result is the frozen{" "}
          <code>ps4_external_v1</code> benchmark (v1.2) — recall 0.862, precision 0.953, F1 0.905 — reported on{" "}
          <a href="/evidence" style={{ color: "var(--accent)" }}>/evidence</a>.
        </div>
      </div>
    </div>
  );
}
