"use client";

import { usePathname } from "next/navigation";

const ROUTES = [
  { href: "/", label: "Overview" },
  { href: "/judge", label: "Analyze" },
  { href: "/war-room", label: "Interventions" },
  { href: "/evidence", label: "Evidence" },
];

/**
 * Plain anchors keep navigation working before hydration and without
 * JavaScript; the pathname only decorates the current route once hydrated.
 */
export default function SiteNav() {
  const pathname = usePathname();
  return (
    <nav className="site-nav jm-topnav" aria-label="Primary navigation">
      {ROUTES.map((route) => (
        <a
          key={route.href}
          href={route.href}
          aria-current={pathname === route.href ? "page" : undefined}
        >
          {route.label}
        </a>
      ))}
    </nav>
  );
}
