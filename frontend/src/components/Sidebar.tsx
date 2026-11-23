import React from "react";
import { Link, NavLink } from "react-router-dom";
import { PanelLeftClose, PanelLeftOpen, X } from "lucide-react";

import { NAV_GROUPS } from "../lib/nav";
import { Logo, LogoMark } from "./Logo";

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  /** Mobile drawer state. On large screens the sidebar is always visible. */
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggleCollapse, mobileOpen = false, onCloseMobile }) => {
  const content = (isDrawer: boolean) => {
    const narrow = collapsed && !isDrawer;
    return (
      <div className="flex h-full flex-col">
        <div className={`flex h-14 shrink-0 items-center border-b border-blue-fantastic/80 ${narrow ? "justify-center px-2" : "justify-between pl-4 pr-2"}`}>
          <Link to="/" title="MacroPulse homepage" className="rounded focus-visible:outline-offset-4">
            {narrow ? <LogoMark size={28} tone="dark" /> : <Logo tone="dark" size={26} />}
          </Link>
          {isDrawer ? (
            <button
              type="button"
              onClick={onCloseMobile}
              aria-label="Close menu"
              className="btn btn-sm btn-icon border-transparent text-oatmeal hover:bg-blue-fantastic hover:text-palladian"
            >
              <X />
            </button>
          ) : (
            !narrow && (
              <button
                type="button"
                onClick={onToggleCollapse}
                aria-label="Collapse sidebar"
                title="Collapse sidebar"
                className="btn btn-sm btn-icon border-transparent text-oatmeal hover:bg-blue-fantastic hover:text-palladian"
              >
                <PanelLeftClose />
              </button>
            )
          )}
        </div>

        <nav className="flex-1 overflow-y-auto px-2.5 py-4" aria-label="Main">
          {NAV_GROUPS.map((group) => (
            <div key={group.label} className="mb-5 last:mb-0">
              {narrow ? (
                <div className="mx-2 mb-2 h-px bg-blue-fantastic/80" aria-hidden />
              ) : (
                <div className="px-2.5 pb-1.5 text-2xs font-medium text-oatmeal/60">{group.label}</div>
              )}
              <ul className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <li key={item.path}>
                      <NavLink
                        to={item.path}
                        onClick={isDrawer ? onCloseMobile : undefined}
                        title={narrow ? item.name : undefined}
                        className={({ isActive }) =>
                          `group relative flex h-9 items-center gap-3 rounded text-[13px] transition-colors ${
                            narrow ? "justify-center" : "px-2.5"
                          } ${
                            isActive
                              ? "bg-blue-fantastic text-palladian font-medium"
                              : "text-oatmeal hover:bg-blue-fantastic/50 hover:text-palladian"
                          }`
                        }
                      >
                        {({ isActive }) => (
                          <>
                            {isActive && (
                              <span className="absolute left-0 top-2 bottom-2 w-[2px] rounded-full bg-burning-flame" aria-hidden />
                            )}
                            <Icon className={`h-4 w-4 shrink-0 ${isActive ? "text-burning-flame" : ""}`} strokeWidth={1.75} />
                            {!narrow && <span className="truncate">{item.name}</span>}
                          </>
                        )}
                      </NavLink>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        <div className={`shrink-0 border-t border-blue-fantastic/80 ${narrow ? "p-2 flex justify-center" : "px-4 py-3"}`}>
          {narrow ? (
            <button
              type="button"
              onClick={onToggleCollapse}
              aria-label="Expand sidebar"
              title="Expand sidebar"
              className="btn btn-sm btn-icon border-transparent text-oatmeal hover:bg-blue-fantastic hover:text-palladian"
            >
              <PanelLeftOpen />
            </button>
          ) : (
            <div className="flex items-center justify-between text-2xs text-oatmeal/60">
              <span>Version 1.0.0</span>
              <Link to="/" className="hover:text-palladian underline-offset-2 hover:underline">
                Homepage
              </Link>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Desktop */}
      <aside
        className={`hidden lg:block shrink-0 bg-abyssal dark:bg-abyssal-dark border-r border-abyssal-dark transition-[width] duration-200 ease-out ${
          collapsed ? "w-16" : "w-60"
        }`}
      >
        {content(false)}
      </aside>

      {/* Mobile drawer */}
      <div className={`lg:hidden fixed inset-0 z-40 ${mobileOpen ? "" : "pointer-events-none"}`} aria-hidden={!mobileOpen}>
        <div
          className={`absolute inset-0 bg-abyssal-dark/60 transition-opacity duration-200 ${mobileOpen ? "opacity-100" : "opacity-0"}`}
          onClick={onCloseMobile}
        />
        <aside
          role="dialog"
          aria-modal="true"
          aria-label="Main menu"
          className={`absolute inset-y-0 left-0 w-72 max-w-[85vw] bg-abyssal transition-[transform,visibility] duration-200 ease-out ${
            mobileOpen ? "translate-x-0 visible shadow-[8px_0_30px_rgba(19,28,37,0.35)]" : "-translate-x-full invisible"
          }`}
        >
          {mobileOpen && content(true)}
        </aside>
      </div>
    </>
  );
};
