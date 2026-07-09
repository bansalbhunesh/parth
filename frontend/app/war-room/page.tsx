import Link from "next/link";
import WarRoomConsole from "../../components/WarRoomConsole";
import {
  getProjectGraph,
  getProjects,
  getRegister,
  getRemediation,
  getSchedule,
  getSupplyChain,
} from "../../lib/api";

export const revalidate = 600;

export const metadata = {
  title: "Pramaan - Commissioning War Room",
  description: "Experimental intervention console for EPC deviation intelligence.",
};

export default async function WarRoomPage() {
  const [deviations, schedule, supply, graph, remediation, projects] = await Promise.all([
    getRegister(),
    getSchedule(),
    getSupplyChain(),
    getProjectGraph(),
    getRemediation(),
    getProjects(),
  ]);

  return (
    <main className="wr-page">
      <nav className="wr-nav" aria-label="War room navigation">
        <Link href="/judge">Judge mode</Link>
        <Link href="/">Dashboard</Link>
        <Link href="/evidence">Evidence</Link>
      </nav>
      <WarRoomConsole
        deviations={deviations}
        schedule={schedule}
        supply={supply}
        graph={graph}
        remediation={remediation}
        projects={projects}
      />
    </main>
  );
}
