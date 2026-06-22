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
  return (
    <div className="stats-bar">
      <div className="stat">
        <div className="stat-val stat-critical">{totalFindings}</div>
        <div className="stat-label">Deviations found</div>
      </div>
      <div className="stat">
        <div className="stat-val stat-critical">{critical}</div>
        <div className="stat-label">Critical</div>
      </div>
      <div className="stat">
        <div className="stat-val stat-warn">{major}</div>
        <div className="stat-label">Major</div>
      </div>
      <div className="stat">
        <div className="stat-val stat-lead">{maxLeadWeeks}w</div>
        <div className="stat-label">Max lead time</div>
      </div>
      <div className="stat">
        <div className="stat-val stat-lead">{meanLeadWeeks}w</div>
        <div className="stat-label">Mean lead time</div>
      </div>
      <div className="stat">
        <div className="stat-val stat-ok">{systemsScanned}</div>
        <div className="stat-label">Systems scanned</div>
      </div>
    </div>
  );
}
