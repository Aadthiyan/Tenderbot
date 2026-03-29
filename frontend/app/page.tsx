import Dashboard from "@/components/Dashboard";
import { fetchTenders, TendersResponse } from "@/lib/api";

export const metadata = {
  title: "TenderBot Global — Procurement Intelligence Dashboard",
  description: "AI-powered global tender discovery: SAM.gov, TED EU, UNGM, Find-a-Tender, AusTender, CanadaBuys — scored and enriched by Llama 3.1.",
};

export default async function HomePage() {
  let initialData: TendersResponse = { tenders: [], total: 0 };
  try {
    initialData = await fetchTenders({ score_min: 0, limit: 100 });
  } catch {
    // Backend offline — render empty dashboard; user can start backend and click Run Scrape
  }
  return <Dashboard initialData={initialData} />;
}
