import React, { Suspense, lazy, useEffect, useState } from "react";
import { BrowserRouter, Link, Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";

import { api } from "./api/client";
import { Banner } from "./components/Banner";
import { Navbar } from "./components/Navbar";
import { Sidebar } from "./components/Sidebar";
import { EmptyState, Skeleton, buttonClass } from "./components/ui";
import { useTheme } from "./hooks/useTheme";
import { findNav } from "./lib/nav";

// Pages. The homepage loads immediately; dashboard pages (and the Plotly charting library
// they use) are split into separate chunks and fetched on first visit.
import { Landing } from "./pages/Landing";
const page = <K extends string>(loader: () => Promise<Record<K, React.ComponentType<any>>>, name: K) =>
  lazy(() => loader().then((m) => ({ default: m[name] })));
const EventStudyLab = page(() => import("./pages/EventStudyLab"), "EventStudyLab");
const MacroOverview = page(() => import("./pages/MacroOverview"), "MacroOverview");
const EventExplorer = page(() => import("./pages/EventExplorer"), "EventExplorer");
const SurpriseAnalyzer = page(() => import("./pages/SurpriseAnalyzer"), "SurpriseAnalyzer");
const CrossAssetMatrix = page(() => import("./pages/CrossAssetMatrix"), "CrossAssetMatrix");
const RegimeAnalysis = page(() => import("./pages/RegimeAnalysis"), "RegimeAnalysis");
const ResearchWorkspace = page(() => import("./pages/ResearchWorkspace"), "ResearchWorkspace");
const Reports = page(() => import("./pages/Reports"), "Reports");
const DataIntegrity = page(() => import("./pages/DataIntegrity"), "DataIntegrity");

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const SIDEBAR_KEY = "macropulse-sidebar-collapsed";

function MainLayout({ isDark, toggleTheme }: { isDark: boolean; toggleTheme: () => void }) {
  const location = useLocation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem(SIDEBAR_KEY) === "1";
    } catch {
      return false;
    }
  });
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    try {
      localStorage.setItem(SIDEBAR_KEY, sidebarCollapsed ? "1" : "0");
    } catch {
      /* storage unavailable */
    }
  }, [sidebarCollapsed]);

  // Close the mobile drawer on navigation and on Escape.
  useEffect(() => setMobileOpen(false), [location.pathname]);
  useEffect(() => {
    if (!mobileOpen) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setMobileOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [mobileOpen]);

  const { data: dataStatus } = useQuery({
    queryKey: ["dataStatus"],
    queryFn: api.getDataStatus,
  });

  const { data: health, isError: healthError } = useQuery({
    queryKey: ["health"],
    queryFn: api.getHealth,
    refetchInterval: 30000,
  });

  const { item, group } = findNav(location.pathname);
  useEffect(() => {
    document.title = item ? `${item.name} · MacroPulse` : "MacroPulse";
  }, [item]);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-palladian dark:bg-abyssal text-abyssal dark:text-palladian">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 btn btn-primary"
      >
        Skip to content
      </a>
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Banner
          message={dataStatus?.banner_message}
          action={
            <Link to="/integrity" className="underline underline-offset-2 decoration-abyssal/30 hover:decoration-abyssal dark:decoration-palladian/30 dark:hover:decoration-palladian">
              About the data
            </Link>
          }
        />

        <Navbar
          pageTitle={item?.name ?? "Page not found"}
          section={group?.label}
          isDark={isDark}
          onToggleTheme={toggleTheme}
          onOpenMenu={() => setMobileOpen(true)}
          dataMode={dataStatus?.data_mode || "DEMO"}
          apiHealthy={healthError ? false : health ? health.status === "healthy" : undefined}
        />

        <main id="main" className="flex-1 overflow-y-auto">
          <div key={location.pathname} className="page-enter">
            <Suspense
              fallback={
                <div className="mx-auto max-w-page px-4 sm:px-6 py-6 space-y-5" aria-busy>
                  <Skeleton className="h-8 w-64" />
                  <Skeleton className="h-28 w-full" />
                  <Skeleton className="h-80 w-full" />
                </div>
              }
            >
              <Outlet />
            </Suspense>
          </div>
        </main>
      </div>
    </div>
  );
}

function NotFound() {
  return (
    <div className="p-6">
      <EmptyState
        title="This page doesn't exist"
        action={
          <Link to="/lab" className={buttonClass("primary")}>
            Go to the event study
          </Link>
        }
      >
        The link may be out of date. Use the menu to find what you were looking for.
      </EmptyState>
    </div>
  );
}

function AppRoutes() {
  const { isDark, toggleTheme } = useTheme();
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route element={<MainLayout isDark={isDark} toggleTheme={toggleTheme} />}>
        <Route path="/lab" element={<EventStudyLab isDark={isDark} />} />
        <Route path="/overview" element={<MacroOverview isDark={isDark} />} />
        <Route path="/events" element={<EventExplorer isDark={isDark} />} />
        <Route path="/surprises" element={<SurpriseAnalyzer isDark={isDark} />} />
        <Route path="/matrix" element={<CrossAssetMatrix isDark={isDark} />} />
        <Route path="/regimes" element={<RegimeAnalysis isDark={isDark} />} />
        <Route path="/workspace" element={<ResearchWorkspace isDark={isDark} />} />
        <Route path="/reports" element={<Reports isDark={isDark} />} />
        <Route path="/integrity" element={<DataIntegrity isDark={isDark} />} />
        <Route path="/dashboard" element={<Navigate to="/lab" replace />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
