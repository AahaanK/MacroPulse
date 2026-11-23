import React from "react";
import { Menu, Moon, Sun } from "lucide-react";

import { HelpTip } from "./ui";

interface NavbarProps {
  pageTitle: string;
  section?: string;
  isDark: boolean;
  onToggleTheme: () => void;
  onOpenMenu?: () => void;
  dataMode?: "LIVE" | "DEMO";
  /** undefined while the first health check is in flight */
  apiHealthy?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  pageTitle,
  section,
  isDark,
  onToggleTheme,
  onOpenMenu,
  dataMode = "DEMO",
  apiHealthy,
}) => {
  return (
    <header className="h-14 shrink-0 border-b border-oatmeal/80 dark:border-blue-fantastic bg-palladian-light/80 dark:bg-abyssal/90 backdrop-blur px-3 sm:px-5 flex items-center justify-between gap-3">
      <div className="flex min-w-0 items-center gap-2">
        {onOpenMenu && (
          <button type="button" onClick={onOpenMenu} aria-label="Open menu" className="btn btn-ghost btn-icon lg:hidden -ml-1">
            <Menu />
          </button>
        )}
        <div className="min-w-0 flex items-baseline gap-2 text-[13px]">
          {section && (
            <>
              <span className="hidden sm:inline text-oatmeal-dark dark:text-oatmeal">{section}</span>
              <span className="hidden sm:inline text-oatmeal dark:text-blue-fantastic-light" aria-hidden>
                /
              </span>
            </>
          )}
          <span className="truncate font-medium text-abyssal dark:text-palladian">{pageTitle}</span>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-1 sm:gap-4 text-xs">
        <span className="hidden md:inline-flex items-center gap-1.5 text-blue-fantastic dark:text-oatmeal">
          {dataMode === "LIVE" ? "Live data" : "Sample data"}
          <HelpTip term="demo_data" />
        </span>
        <span className="hidden md:block h-4 w-px bg-oatmeal dark:bg-blue-fantastic" aria-hidden />
        <span
          className={`hidden sm:inline ${
            apiHealthy === false ? "text-truffle dark:text-truffle-soft font-medium" : "text-oatmeal-dark dark:text-oatmeal"
          }`}
          role="status"
        >
          {apiHealthy === undefined ? "Connecting…" : apiHealthy ? "Server connected" : "Server unreachable"}
        </span>
        <button
          type="button"
          onClick={onToggleTheme}
          title={isDark ? "Switch to light theme" : "Switch to dark theme"}
          aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
          className="btn btn-ghost btn-icon"
        >
          {isDark ? <Sun /> : <Moon />}
        </button>
      </div>
    </header>
  );
};
