import React from "react";
import Plot from "react-plotly.js";
import { getBasePlotlyLayout, getChartThemeColors, plotConfig } from "./chartTheme";

interface CARHistogramProps {
  carValues: number[];
  meanCar: number;
  medianCar: number;
  isDark: boolean;
  unit?: string;
  windowLabel?: string;
}

/** How the individual releases' total extra moves are spread out. */
export const CARHistogram: React.FC<CARHistogramProps> = ({ carValues, meanCar, medianCar, isDark, unit = "%" }) => {
  const colors = getChartThemeColors(isDark);
  const layout = getBasePlotlyLayout(isDark);
  const fmt = (v: number) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${Math.abs(v).toFixed(2)}${unit}`;

  return (
    <div className="w-full h-72" role="img" aria-label="Histogram of the total extra move for each release.">
      <Plot
        data={[
          {
            type: "histogram",
            x: carValues,
            nbinsx: 20,
            marker: {
              color: isDark ? "rgba(201, 193, 177, 0.45)" : "rgba(44, 59, 77, 0.55)",
              line: { color: isDark ? "#212E3C" : "#F8F5F0", width: 1 },
            },
            name: "Releases",
            hovertemplate: `Total extra move: %{x}<br>Releases: %{y}<extra></extra>`,
          } as any,
        ]}
        layout={{
          ...layout,
          xaxis: { ...layout.xaxis, title: { ...(layout.xaxis as any).title, text: `Total extra move per release (${unit})` }, ticksuffix: unit === "%" ? "%" : "" },
          yaxis: { ...layout.yaxis, title: { ...(layout.yaxis as any).title, text: "Number of releases" } },
          margin: { ...layout.margin, t: 30 },
          bargap: 0.08,
          shapes: [
            { type: "line", x0: meanCar, x1: meanCar, y0: 0, y1: 1, yref: "paper", line: { color: colors.positiveSeries, width: 1.75 } },
            { type: "line", x0: medianCar, x1: medianCar, y0: 0, y1: 1, yref: "paper", line: { color: colors.textMuted, width: 1.25, dash: "dot" } },
          ],
          annotations: [
            {
              x: meanCar,
              y: 1.06,
              yref: "paper",
              text: `Average ${fmt(meanCar)}`,
              showarrow: false,
              font: { size: 11, color: colors.positiveSeries },
              xanchor: meanCar >= medianCar ? "left" : "right",
            },
            {
              x: medianCar,
              y: 1.06,
              yref: "paper",
              text: `Median ${fmt(medianCar)}`,
              showarrow: false,
              font: { size: 11, color: colors.textMuted },
              xanchor: meanCar >= medianCar ? "right" : "left",
            },
          ],
          autosize: true,
        }}
        useResizeHandler
        style={{ width: "100%", height: "100%" }}
        config={plotConfig}
      />
    </div>
  );
};
