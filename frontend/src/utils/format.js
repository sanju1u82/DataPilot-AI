/** Display formatting shared across the dashboard. */

export const formatNumber = (value) =>
  value === null || value === undefined || Number.isNaN(value)
    ? "—"
    : Number(value).toLocaleString();

/** Compact form for numbers that need to fit in a stat card. */
export const formatCompact = (value) => {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const number = Number(value);
  if (Math.abs(number) >= 1_000_000) return `${(number / 1_000_000).toFixed(1)}M`;
  if (Math.abs(number) >= 10_000) return `${(number / 1000).toFixed(1)}K`;
  return number.toLocaleString();
};

export const formatPercent = (value, digits = 1) =>
  value === null || value === undefined || Number.isNaN(value)
    ? "—"
    : `${Number(value).toFixed(digits)}%`;

/** Keep long decimals from blowing out table column widths. */
export const formatDecimal = (value, digits = 3) => {
  if (value === null || value === undefined || value === "") return "—";
  const number = Number(value);
  if (Number.isNaN(number)) return String(value);
  if (Number.isInteger(number)) return number.toLocaleString();
  if (Math.abs(number) < 0.001 && number !== 0) return number.toExponential(2);
  return number.toFixed(digits);
};

export const formatBytes = (bytes) => {
  if (!bytes && bytes !== 0) return "—";
  const units = ["B", "KB", "MB", "GB"];
  let value = Number(bytes);
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(value >= 100 || unit === 0 ? 0 : 1)} ${units[unit]}`;
};

/** Render a cell value, marking nulls so they read as missing, not blank. */
export const formatCell = (value) => {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "boolean") return String(value);
  if (typeof value === "number") return formatDecimal(value, 4);
  return String(value);
};

/** Map a 0-100 score onto the palette's tone names. */
export const scoreTone = (score) => {
  if (score === null || score === undefined) return "accent";
  if (score >= 90) return "success";
  if (score >= 75) return "accent";
  if (score >= 60) return "warning";
  return "danger";
};

export const severityTone = (severity) =>
  ({ high: "danger", medium: "warning", low: "accent" }[severity] || "accent");

export const TYPE_TONE = {
  numeric: "cyan",
  categorical: "accent",
  boolean: "success",
  datetime: "warning",
  text: "warning",
  identifier: "danger",
};
