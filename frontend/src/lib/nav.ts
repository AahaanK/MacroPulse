import {
  BarChart3,
  CalendarDays,
  Database,
  FileText,
  FolderOpen,
  Gauge,
  LineChart,
  Network,
  ScatterChart,
} from "lucide-react";

export interface NavItem {
  name: string;
  path: string;
  icon: typeof LineChart;
  description: string;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
  {
    label: "Analyse",
    items: [
      {
        name: "Event study",
        path: "/lab",
        icon: LineChart,
        description: "Measure how an asset moved around each economic release, and whether the move was more than chance.",
      },
      {
        name: "Surprises",
        path: "/surprises",
        icon: ScatterChart,
        description: "Check whether bigger changes in the economic numbers lead to bigger market moves.",
      },
      {
        name: "Cross-asset view",
        path: "/matrix",
        icon: Network,
        description: "Compare how stocks, bonds, the dollar, gold and oil react to the same release.",
      },
      {
        name: "Market conditions",
        path: "/regimes",
        icon: Gauge,
        description: "See whether reactions differ when the market is already calm or nervous.",
      },
    ],
  },
  {
    label: "Browse",
    items: [
      {
        name: "Market overview",
        path: "/overview",
        icon: BarChart3,
        description: "The latest reading of each economic indicator, with its history.",
      },
      {
        name: "Release calendar",
        path: "/events",
        icon: CalendarDays,
        description: "Every economic release in the database, with its exact publication time and values.",
      },
    ],
  },
  {
    label: "Your work",
    items: [
      {
        name: "Workspace",
        path: "/workspace",
        icon: FolderOpen,
        description: "Stress-test a finding, organise projects and keep research notes.",
      },
      {
        name: "Reports",
        path: "/reports",
        icon: FileText,
        description: "Turn any study you've run into a report you can download as PDF or CSV.",
      },
    ],
  },
  {
    label: "System",
    items: [
      {
        name: "Data sources",
        path: "/integrity",
        icon: Database,
        description: "Where the data comes from, how much of it there is, and what the app can't do yet.",
      },
    ],
  },
];

export const NAV_ITEMS: NavItem[] = NAV_GROUPS.flatMap((g) => g.items);

export function findNav(pathname: string): { item?: NavItem; group?: NavGroup } {
  for (const g of NAV_GROUPS) {
    const item = g.items.find((i) => pathname === i.path || pathname.startsWith(`${i.path}/`));
    if (item) return { item, group: g };
  }
  return {};
}
