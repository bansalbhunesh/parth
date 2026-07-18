import Link from "./AppLink";
import SiteNav from "./SiteNav";
import CopilotDrawer from "./CopilotDrawer";
import ThemeToggle from "./ThemeToggle";

/**
 * The single product shell header. One nav, every route: the accessible names
 * Overview / Analyze / Interventions / Evidence are stable contracts used by
 * the browser journeys and by people who have learned the product once.
 */
export default function SiteHeader() {
  return (
    <header className="site-header">
      <Link href="/" className="wordmark" aria-label="Pramaan home">
        Pramaan<span aria-hidden="true">/</span>
      </Link>
      <SiteNav />
      <div className="header-actions">
        <CopilotDrawer />
        <ThemeToggle />
      </div>
    </header>
  );
}
