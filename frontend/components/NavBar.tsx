"use client";

import { useEffect, useState } from "react";

const SECTIONS = [
  { id: "sentinel", label: "Sentinel" },
  { id: "workflow", label: "Before/After" },
  { id: "pipeline", label: "Pipeline" },
  { id: "architecture", label: "Architecture" },
  { id: "screenshots", label: "Screenshots" },
  { id: "systems", label: "Systems" },
  { id: "risk", label: "Risk" },
  { id: "register", label: "Register" },
  { id: "twin", label: "Cx Twin" },
  { id: "standards", label: "Standards" },
  { id: "eval", label: "Eval" },
  { id: "roi", label: "ROI" },
  { id: "scale", label: "Scale" },
  { id: "copilot", label: "Copilot" },
  { id: "refs", label: "Research" },
];

export default function NavBar() {
  const [active, setActive] = useState("");

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActive(entry.target.id);
          }
        }
      },
      { rootMargin: "-40% 0px -50% 0px" }
    );
    for (const s of SECTIONS) {
      const el = document.getElementById(s.id);
      if (el) observer.observe(el);
    }
    return () => observer.disconnect();
  }, []);

  return (
    <nav className="nav-bar">
      {SECTIONS.map((s) => (
        <a
          key={s.id}
          href={`#${s.id}`}
          className={`nav-link ${active === s.id ? "nav-active" : ""}`}
        >
          {s.label}
        </a>
      ))}
    </nav>
  );
}
