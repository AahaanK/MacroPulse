# MacroPulse redesign: what changed

## Running it

Nothing changed in how you start the app:

```bash
# backend (port 8001)
cd backend && uvicorn macropulse.main:app --port 8001
# frontend (port 5175)
cd frontend && npm install && npm run dev
```

Run `npm install` once: three font packages were added (see below).

## Routes

| Path | Page |
|---|---|
| `/` | **New** homepage. "Explore dashboard" opens `/lab` |
| `/lab` | Event study (previously at `/`) |
| `/overview`, `/events`, `/surprises`, `/matrix`, `/regimes`, `/workspace`, `/reports`, `/integrity` | Unchanged paths |
| `/dashboard` | Redirects to `/lab` |
| anything else | "Page not found" with a way back |

## Bugs fixed

1. **Returns were 100× too small** (`backend/macropulse/analytics/event_study.py`).
   `calculate_returns` produces fractions (0.012), but results were labelled "%". A 1.2% move showed
   as "0.01%" everywhere: verdicts, charts, reports, surprises, the cross-asset view and market conditions.
   Percent-return assets are now expressed in percentage points before the study runs. Yields (bp) and the VIX
   (points) are unchanged. The toy-panel unit test now asserts the values its own docstring describes.
   *Studies saved before this fix still contain the old values; re-run them to refresh their reports.*
2. **The default study always returned exactly zero.** It compared SPY with SPY as its own benchmark.
   The default is now "SPY compared with its own average day", and the form warns when asset and benchmark match.
3. **"Shorter estimation window" robustness check excluded every release**
   (`backend/macropulse/api/routers/research.py`). Its window was 110 days, but the engine requires 120.
   It now uses 130 days.
4. **Release times were shifted by the viewer's time zone.** The API sends UTC timestamps without a `Z`, which browsers
   read as local time. They're now parsed as UTC and shown in US Eastern Time.
5. **"Compare other indicators" did nothing** except change its label. It now overlays a second indicator on a right-hand axis.
6. Pages that called `fetch()` directly ignored HTTP errors. All calls now go through the API client and show a
   clear error with a retry button.
7. Notes were always attached to the first project. You can now pick the project.

## Improvements

- Date range, random seed and "reset to defaults" in the event study. Click any release row for its day-by-day moves.
- A plain-English summary above each study's technical verdict.
- Date filters in the release calendar (the API already supported them), plus pagination counts and Escape to close details.
- Correlation view: release days, ordinary days, or the difference between them.
- Market conditions: newest days first, with "show more".
- Tooltips explaining every financial and statistical term (`src/lib/glossary.ts`).
- Self-hosted IBM Plex fonts (`@fontsource/*`): no Google Fonts request, and they work offline.
- Dashboard pages are code-split. The homepage loads about 87 KB gzipped instead of 1.6 MB; Plotly loads only when a chart page opens.
- Responsive layout with a mobile menu drawer, visible keyboard focus, a skip link, and support for reduced motion.

## Design system

- Six palette colours only (plus tints), defined in `tailwind.config.ts`. All text colour pairs meet WCAG AA.
- Shared components live in `src/components/ui.tsx` (Button, Select, Input, Field, Checkbox, Segmented/Tabs, Panel,
  Stat, Term tooltip, Notice, empty, error and loading states). Their styles are in `src/styles/globals.css`.
- Logo: `src/components/Logo.tsx` and `public/favicon.svg`. A flat baseline, an orange release-day marker, and the
  market's reaction after it.
- The homepage figure uses a real study snapshot (`src/data/heroStudy.ts`) so it renders without the API.

## Verified

- `npm run build`, `tsc`, and `vitest` (3/3) pass. Backend `pytest` passes (25/25).
- A scripted browser click-through of 46 checks covered every page, form, dropdown, tab, download and link,
  mobile navigation, and dark mode, with no console errors and no failed API calls.
