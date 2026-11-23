/**
 * Shared chart theme for Plotly.js visual components.
 *
 * Six-colour palette only (plus tints):
 *   palladian #EEE9DF · oatmeal #C9C1B1 · blue-fantastic #2C3B4D
 *   burning-flame #FFB162 · truffle #A35139 · abyssal #1B2632
 *
 * Light theme: navy carries the data, orange marks bands and highlights, terracotta marks negatives.
 * Dark theme: orange carries the data, terracotta tint marks negatives.
 */

export interface ThemeColors {
  background: string;
  cardBg: string;
  text: string;
  textMuted: string;
  gridColor: string;
  lineColor: string;
  primarySeries: string;
  accentSeries: string;
  positiveSeries: string;
  negativeSeries: string;
  neutralSeries: string;
  bandFill: string;
  marker: string;
}

export const getChartThemeColors = (isDark: boolean): ThemeColors => {
  if (isDark) {
    return {
      background: "#1B2632",
      cardBg: "#212E3C",
      text: "#EEE9DF",
      textMuted: "#C9C1B1",
      gridColor: "rgba(201, 193, 177, 0.10)",
      lineColor: "rgba(201, 193, 177, 0.28)",
      primarySeries: "#EEE9DF",
      accentSeries: "#FFB162",
      positiveSeries: "#FFB162",
      negativeSeries: "#D69580",
      neutralSeries: "#C9C1B1",
      bandFill: "rgba(255, 177, 98, 0.14)",
      marker: "rgba(255, 177, 98, 0.6)",
    };
  }

  return {
    background: "#EEE9DF",
    cardBg: "#F8F5F0",
    text: "#1B2632",
    textMuted: "#6E6555",
    gridColor: "rgba(201, 193, 177, 0.45)",
    lineColor: "#C9C1B1",
    primarySeries: "#2C3B4D",
    accentSeries: "#2C3B4D",
    positiveSeries: "#2C3B4D",
    negativeSeries: "#A35139",
    neutralSeries: "#C9C1B1",
    bandFill: "rgba(255, 177, 98, 0.32)",
    marker: "rgba(163, 81, 57, 0.55)",
  };
};

const FONT = "'IBM Plex Sans', system-ui, sans-serif";

export const getBasePlotlyLayout = (isDark: boolean): Partial<Plotly.Layout> => {
  const colors = getChartThemeColors(isDark);
  const axis = {
    gridcolor: colors.gridColor,
    linecolor: colors.lineColor,
    tickcolor: colors.lineColor,
    ticklen: 4,
    tickfont: { family: FONT, size: 11, color: colors.textMuted },
    zerolinecolor: colors.lineColor,
    zerolinewidth: 1,
    automargin: true,
    title: { font: { family: FONT, size: 11, color: colors.textMuted }, standoff: 10 },
  };

  return {
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { family: FONT, size: 11, color: colors.text },
    margin: { l: 52, r: 16, t: 16, b: 44 },
    hoverlabel: {
      bgcolor: isDark ? "#131C25" : "#1B2632",
      bordercolor: isDark ? "#3A4D64" : "#1B2632",
      font: { family: FONT, size: 12, color: "#EEE9DF" },
      align: "left",
    },
    hovermode: "closest",
    xaxis: { ...axis, showgrid: false } as Partial<Plotly.LayoutAxis>,
    yaxis: { ...axis } as Partial<Plotly.LayoutAxis>,
    legend: {
      font: { family: FONT, size: 11, color: colors.textMuted },
      bgcolor: "transparent",
      orientation: "h",
      yanchor: "bottom",
      y: 1.0,
      xanchor: "right",
      x: 1,
    },
  };
};

/** Vertical dashed line marking the release day on a category x-axis. */
export const releaseDayShape = (isDark: boolean, x: string | number = "Release"): Partial<Plotly.Shape> => ({
  type: "line",
  xref: "x",
  yref: "paper",
  x0: x,
  x1: x,
  y0: 0,
  y1: 1,
  line: { color: getChartThemeColors(isDark).marker, width: 1, dash: "dot" },
  layer: "below",
});

export const plotConfig: Partial<Plotly.Config> = { displayModeBar: false, responsive: true };
