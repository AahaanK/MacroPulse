import React from "react";
import Plot from "react-plotly.js";
import { AARPoint } from "../types";
import { tauLabel } from "../lib/format";
import { getBasePlotlyLayout, getChartThemeColors, plotConfig, releaseDayShape } from "./chartTheme";

interface CAARLineChartProps {
  aarSeries: AARPoint[];
  isDark: boolean;
  unit?: string;
  assetSymbol?: string;
}

/** Running total of the average extra move, with its 95% bootstrap range. */
export const CAARLineChart: React.FC<CAARLineChartProps> = ({ aarSeries, isDark, unit = "%", assetSymbol = "SPY" }) => {
  const colors = getChartThemeColors(isDark);
  const layout = getBasePlotlyLayout(isDark);

  const taus = aarSeries.map((p) => tauLabel(p.tau));
  const caars = aarSeries.map((p) => p.caar);
  const bootLower = aarSeries.map((p) => p.caar_bootstrap_lower);
  const bootUpper = aarSeries.map((p) => p.caar_bootstrap_upper);

  return (
    <div className="w-full h-72" role="img" aria-label={`Line chart of the cumulative average extra move for ${assetSymbol}, with a 95% range band.`}>
      <Plot
        data={[
          {
            type: "scatter",
            mode: "lines",
            x: taus,
            y: bootUpper,
            line: { width: 0, color: "transparent" },
            showlegend: false,
            hoverinfo: "skip",
          },
          {
            type: "scatter",
            mode: "lines",
            x: taus,
            y: bootLower,
            fill: "tonexty",
            fillcolor: colors.bandFill,
            line: { width: 0, color: "transparent" },
            name: "95% range",
            customdata: bootUpper,
            hovertemplate: `95% range: %{y:+.3f} to %{customdata:+.3f}${unit}<extra></extra>`,
          },
          {
            type: "scatter",
            mode: "lines+markers",
            x: taus,
            y: caars,
            line: { color: colors.accentSeries, width: 2.25, shape: "linear" },
            marker: { size: 6, color: colors.accentSeries, line: { color: isDark ? "#212E3C" : "#F8F5F0", width: 1.5 } },
            name: "Running total",
            hovertemplate: `Day %{x}<br>Running total: %{y:+.3f}${unit}<extra></extra>`,
          },
        ]}
        layout={{
          ...layout,
          shapes: [releaseDayShape(isDark)],
          yaxis: { ...layout.yaxis, title: { ...(layout.yaxis as any).title, text: `Running total of extra moves (${unit})` }, ticksuffix: unit === "%" ? "%" : "" },
          xaxis: { ...layout.xaxis, type: "category", title: { ...(layout.xaxis as any).title, text: "Trading days from the release" } },
          autosize: true,
        }}
        useResizeHandler
        style={{ width: "100%", height: "100%" }}
        config={plotConfig}
      />
    </div>
  );
};
