import React from "react";
import Plot from "react-plotly.js";
import { AARPoint } from "../types";
import { tauLabel } from "../lib/format";
import { getBasePlotlyLayout, getChartThemeColors, plotConfig, releaseDayShape } from "./chartTheme";

interface AARBarChartProps {
  aarSeries: AARPoint[];
  isDark: boolean;
  unit?: string;
  assetSymbol?: string;
}

/** Average extra move on each day of the window, with 95% error bars. */
export const AARBarChart: React.FC<AARBarChartProps> = ({ aarSeries, isDark, unit = "%", assetSymbol = "SPY" }) => {
  const colors = getChartThemeColors(isDark);
  const layout = getBasePlotlyLayout(isDark);

  const taus = aarSeries.map((p) => tauLabel(p.tau));
  const aars = aarSeries.map((p) => p.aar);
  const errors = aarSeries.map((p) => p.aar_se * 1.96);
  const barColors = aars.map((v) => (v >= 0 ? colors.positiveSeries : colors.negativeSeries));

  return (
    <div className="w-full h-72" aria-label={`Bar chart of the average daily extra move for ${assetSymbol} on each day around the release.`} role="img">
      <Plot
        data={[
          {
            type: "bar",
            x: taus,
            y: aars,
            error_y: { type: "data", array: errors, visible: true, color: colors.textMuted, thickness: 1, width: 5 },
            marker: { color: barColors, opacity: 0.9 },
            width: 0.55,
            name: `Average extra move (${unit})`,
            hovertemplate: `Day %{x}<br>Average extra move: %{y:+.3f}${unit}<br>95% range: ±%{error_y.array:.3f}${unit}<extra></extra>`,
          } as any,
        ]}
        layout={{
          ...layout,
          shapes: [releaseDayShape(isDark)],
          yaxis: { ...layout.yaxis, title: { ...(layout.yaxis as any).title, text: `Average extra move (${unit})` }, ticksuffix: unit === "%" ? "%" : "" },
          xaxis: { ...layout.xaxis, type: "category", title: { ...(layout.xaxis as any).title, text: "Trading days from the release" } },
          bargap: 0.4,
          autosize: true,
        }}
        useResizeHandler
        style={{ width: "100%", height: "100%" }}
        config={plotConfig}
      />
    </div>
  );
};
