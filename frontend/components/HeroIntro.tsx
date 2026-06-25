export default function HeroIntro() {
  return (
    <section className="hero-intro">
      <div className="hero-intro-glow" />
      <div className="hero-intro-badge">ET AI HACKATHON 2026 · PROBLEM STATEMENT 4</div>
      <h1 className="hero-intro-title">
        What if every vendor submittal was reviewed
        <br />
        <span className="hero-intro-accent">before a single bolt turns on site?</span>
      </h1>
      <p className="hero-intro-body">
        In EPC data-centre projects, deviations between design specs, vendor submittals, and governing standards
        hide in thousands of pages of unstructured documents. Today, they surface during commissioning —
        <strong> 33 weeks too late</strong>, causing seven-figure rework.
      </p>
      <p className="hero-intro-body">
        <strong>Pramaan</strong> deploys 5 AI agents to cross-reference every requirement against every submittal
        against every standard — and catches deviations the day the document is uploaded.
      </p>
      <div className="hero-intro-stats">
        <div className="hero-intro-stat">
          <div className="hero-intro-stat-val">40 MW</div>
          <div className="hero-intro-stat-label">Tier IV data centre</div>
        </div>
        <div className="hero-intro-stat">
          <div className="hero-intro-stat-val">7</div>
          <div className="hero-intro-stat-label">Standards cross-checked</div>
        </div>
        <div className="hero-intro-stat">
          <div className="hero-intro-stat-val">33</div>
          <div className="hero-intro-stat-label">Requirements tracked</div>
        </div>
        <div className="hero-intro-stat">
          <div className="hero-intro-stat-val">87</div>
          <div className="hero-intro-stat-label">Submittals reviewed</div>
        </div>
      </div>
    </section>
  );
}
