import { StatCard } from "../common/Primitives";
import {
  formatBytes,
  formatCompact,
  formatNumber,
  formatPercent,
  scoreTone,
} from "../../utils/format";

/** Headline numbers for the uploaded dataset. */
function DatasetCard({ dataset, profile, quality }) {
  const { overview } = profile;

  // Missing and duplicate counts read as problems, so their tone tracks severity.
  const missingTone =
    overview.missing_percentage > 10
      ? "danger"
      : overview.missing_percentage > 0
        ? "warning"
        : "success";

  const duplicateTone = overview.duplicate_rows > 0 ? "warning" : "success";

  return (
    <div className="dp-stat-grid">
      <StatCard
        label="Dataset size"
        value={formatCompact(overview.rows)}
        hint={`${formatNumber(overview.rows)} rows`}
      />
      <StatCard
        label="Features"
        value={overview.columns}
        hint={`${overview.numeric_columns} numerical · ${overview.categorical_columns} categorical`}
        tone="cyan"
      />
      <StatCard
        label="Missing values"
        value={formatPercent(overview.missing_percentage, 1)}
        hint={`${formatNumber(overview.missing_cells)} of ${formatNumber(overview.total_cells)} cells`}
        tone={missingTone}
      />
      <StatCard
        label="Duplicate rows"
        value={formatNumber(overview.duplicate_rows)}
        hint={formatPercent(overview.duplicate_percentage, 2)}
        tone={duplicateTone}
      />
      <StatCard
        label="Quality score"
        value={`${quality.overall_score}`}
        hint={`${quality.grade} · ${quality.issues.length} issue${quality.issues.length === 1 ? "" : "s"}`}
        tone={scoreTone(quality.overall_score)}
      />
      <StatCard
        label="In memory"
        value={formatBytes(overview.memory_usage_kb * 1024)}
        hint={`file ${formatBytes(dataset.size_bytes)}`}
      />
    </div>
  );
}

export default DatasetCard;
