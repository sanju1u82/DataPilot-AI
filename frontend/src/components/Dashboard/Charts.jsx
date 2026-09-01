import { useState } from "react";
import { Card, EmptyState } from "../common/Primitives";
import { formatDecimal, formatNumber, formatPercent } from "../../utils/format";

/**
 * Distribution charts.
 *
 * Every chart here shows a single series — counts for one column — so each uses
 * one flat hue and needs no legend; the card title names the series. Magnitude
 * is carried by bar length alone.
 */

function Histogram({ column }) {
  const [hovered, setHovered] = useState(null);
  const peak = Math.max(...column.bins.map((bin) => bin.count), 1);
  const total = column.bins.reduce((sum, bin) => sum + bin.count, 0);

  const first = column.bins[0];
  const last = column.bins[column.bins.length - 1];

  return (
    <Card title={column.name}>
      <div className="dp-histogram" onMouseLeave={() => setHovered(null)}>
        {column.bins.map((bin, index) => (
          <div
            key={index}
            className={`dp-histogram-bar${hovered === index ? " is-hovered" : ""}`}
            style={{ height: `${Math.max((bin.count / peak) * 100, 1.5)}%` }}
            onMouseEnter={() => setHovered(index)}
          />
        ))}

        {hovered !== null && (
          <div
            className="dp-tooltip"
            style={{
              left: `${((hovered + 0.5) / column.bins.length) * 100}%`,
              bottom: "100%",
            }}
          >
            <div className="dp-tooltip-value">
              {formatNumber(column.bins[hovered].count)} rows
            </div>
            <div className="text-dim">
              {formatDecimal(column.bins[hovered].start, 2)} –{" "}
              {formatDecimal(column.bins[hovered].end, 2)}
            </div>
          </div>
        )}
      </div>

      <div className="dp-axis">
        <span>{formatDecimal(first.start, 2)}</span>
        <span className="text-faint">{formatNumber(total)} values</span>
        <span>{formatDecimal(last.end, 2)}</span>
      </div>
    </Card>
  );
}

function FrequencyBars({ column }) {
  const peak = Math.max(...column.distribution.map((entry) => entry.count), 1);

  return (
    <Card title={column.name}>
      {column.distribution.map((entry) => (
        <div className="dp-bar-row" key={String(entry.value)}>
          <div className="dp-bar-head">
            <span className="dp-bar-label" title={String(entry.value)}>
              {String(entry.value)}
            </span>
            <span className="dp-bar-count">
              {formatNumber(entry.count)} · {formatPercent(entry.percentage, 1)}
            </span>
          </div>
          <div className="dp-bar-track">
            <div
              className="dp-bar-fill"
              style={{ width: `${Math.max((entry.count / peak) * 100, 1)}%` }}
            />
          </div>
        </div>
      ))}

      {column.other_categories > 0 && (
        <div className="dp-meter-note" style={{ marginTop: 12 }}>
          + {formatNumber(column.other_categories)} more categories not shown
        </div>
      )}
    </Card>
  );
}

function Charts({ statistics }) {
  const categoricalWithData = statistics.categorical.filter(
    (column) => !column.all_missing && column.distribution?.length
  );

  if (!statistics.histograms.length && !categoricalWithData.length) {
    return (
      <Card title="Distributions">
        <EmptyState
          title="Nothing to chart"
          message="This dataset has no numerical or categorical columns with enough variation to plot."
        />
      </Card>
    );
  }

  return (
    <div className="dp-stack">
      {statistics.histograms.length > 0 && (
        <div>
          <div className="section-title">
            <h2>Numerical distributions</h2>
            <span className="text-faint" style={{ fontSize: 13 }}>
              {statistics.histograms.length} column
              {statistics.histograms.length === 1 ? "" : "s"}
            </span>
          </div>
          <div className="dp-chart-grid">
            {statistics.histograms.map((column) => (
              <Histogram key={column.name} column={column} />
            ))}
          </div>
        </div>
      )}

      {categoricalWithData.length > 0 && (
        <div>
          <div className="section-title">
            <h2>Category frequencies</h2>
            <span className="text-faint" style={{ fontSize: 13 }}>
              top {Math.max(...categoricalWithData.map((c) => c.distribution.length))} values
              per column
            </span>
          </div>
          <div className="dp-chart-grid">
            {categoricalWithData.map((column) => (
              <FrequencyBars key={column.name} column={column} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Charts;
