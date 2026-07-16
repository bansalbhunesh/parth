import type { AnalyzeDeviation, CompoundRisk, Remediation } from "./model";
import { humanizeRiskTarget } from "./resolution-model";

interface RiskRemediationProps {
  compoundRisk?: CompoundRisk;
  remediation?: Remediation;
  deviations?: AnalyzeDeviation[];
}

const BAND_CLASS: Record<string, string> = {
  Critical: "rr-band-critical",
  High: "rr-band-high",
  Moderate: "rr-band-moderate",
  Low: "rr-band-low",
};

const pct = (value: number): number => Math.round(value * 100);

export default function RiskRemediation({ compoundRisk, remediation, deviations = [] }: RiskRemediationProps) {
  if (!compoundRisk || compoundRisk.deviation_count === 0) return null;

  const bandClass = BAND_CLASS[compoundRisk.risk_band] ?? "rr-band-low";
  const cliff = compoundRisk.schedule_cliff;
  const clusters = compoundRisk.clusters.slice(0, 3);
  const top = remediation?.highest_leverage ?? null;

  return (
    <section className="rr-panel" aria-label="Systemic risk and remediation">
      <div className="rr-head">
        <span className="rr-title">Systemic risk</span>
        <span className={`rr-band ${bandClass}`}>
          {compoundRisk.risk_band} · {pct(compoundRisk.project_compound_risk)}%
        </span>
      </div>

      {cliff ? (
        <p className="rr-cliff">
          Schedule cliff at <strong>week {cliff.week_fail}</strong>: {cliff.converging_deviations} findings fail together.
        </p>
      ) : null}

      {clusters.length > 0 ? (
        <ul className="rr-clusters">
          {clusters.map((cluster) => (
            <li key={`${cluster.kind}-${cluster.key}`} className="rr-cluster">
              <span className="rr-cluster-key">{humanizeRiskTarget(String(cluster.key), deviations)}</span>
              <span className="rr-cluster-meta">
                {cluster.member_count} findings · {pct(cluster.compound_risk)}%
              </span>
            </li>
          ))}
        </ul>
      ) : null}

      {top ? (
        <div className="rr-fix">
          <span className="rr-fix-label">Fix this first</span>
          <span className="rr-fix-target">{humanizeRiskTarget(top.target, deviations)}</span>
          <span className="rr-fix-gain">
            −{pct(top.risk_reduction)}% risk{top.clears_schedule_cliff ? " · clears the cliff" : ""}
          </span>
        </div>
      ) : null}

      <p className="rr-method">{compoundRisk.method}</p>
    </section>
  );
}
