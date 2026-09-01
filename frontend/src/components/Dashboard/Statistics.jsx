import { Badge, Card, EmptyState } from "../common/Primitives";
import { formatDecimal, formatNumber, formatPercent } from "../../utils/format";

function NumericTable({ columns }) {
  return (
    <Card title={`Numerical columns (${columns.length})`} flush>
      <div className="dp-table-scroll">
        <table className="dp-table">
          <thead>
            <tr>
              <th>Column</th>
              <th>Mean</th>
              <th>Median</th>
              <th>Std dev</th>
              <th>Min</th>
              <th>Q1</th>
              <th>Q3</th>
              <th>Max</th>
              <th>Skew</th>
              <th>Outliers</th>
            </tr>
          </thead>
          <tbody>
            {columns.map((column) => (
              <tr key={column.name}>
                <td style={{ fontWeight: 600 }}>{column.name}</td>
                {column.all_missing ? (
                  <td colSpan={9} className="is-null">
                    no values
                  </td>
                ) : (
                  <>
                    <td>{formatDecimal(column.mean)}</td>
                    <td>{formatDecimal(column.median)}</td>
                    <td>{formatDecimal(column.std)}</td>
                    <td>{formatDecimal(column.min)}</td>
                    <td>{formatDecimal(column.q1)}</td>
                    <td>{formatDecimal(column.q3)}</td>
                    <td>{formatDecimal(column.max)}</td>
                    <td>{formatDecimal(column.skewness, 2)}</td>
                    <td>
                      {column.outliers > 0 ? (
                        <Badge tone={column.outlier_percentage >= 5 ? "warning" : ""}>
                          {formatNumber(column.outliers)} ·{" "}
                          {formatPercent(column.outlier_percentage, 1)}
                        </Badge>
                      ) : (
                        <span className="text-faint">none</span>
                      )}
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function CategoricalTable({ columns }) {
  return (
    <Card title={`Categorical columns (${columns.length})`} flush>
      <div className="dp-table-scroll">
        <table className="dp-table">
          <thead>
            <tr>
              <th>Column</th>
              <th>Unique values</th>
              <th>Most frequent</th>
              <th>Count</th>
              <th>Share</th>
              <th>Balance</th>
            </tr>
          </thead>
          <tbody>
            {columns.map((column) => (
              <tr key={column.name}>
                <td style={{ fontWeight: 600 }}>{column.name}</td>
                {column.all_missing ? (
                  <td colSpan={5} className="is-null">
                    no values
                  </td>
                ) : (
                  <>
                    <td>{formatNumber(column.unique)}</td>
                    <td>{String(column.top_value)}</td>
                    <td>{formatNumber(column.top_count)}</td>
                    <td>{formatPercent(column.top_percentage, 1)}</td>
                    <td>
                      {column.is_imbalanced ? (
                        <Badge tone="warning">imbalanced</Badge>
                      ) : (
                        <Badge tone="success">balanced</Badge>
                      )}
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function DatetimeTable({ columns }) {
  return (
    <Card title={`Date columns (${columns.length})`} flush>
      <div className="dp-table-scroll">
        <table className="dp-table">
          <thead>
            <tr>
              <th>Column</th>
              <th>Earliest</th>
              <th>Latest</th>
              <th>Span (days)</th>
              <th>Distinct dates</th>
            </tr>
          </thead>
          <tbody>
            {columns.map((column) => (
              <tr key={column.name}>
                <td style={{ fontWeight: 600 }}>{column.name}</td>
                {column.all_missing ? (
                  <td colSpan={4} className="is-null">
                    no values
                  </td>
                ) : (
                  <>
                    <td className="mono">{String(column.min).slice(0, 19)}</td>
                    <td className="mono">{String(column.max).slice(0, 19)}</td>
                    <td>{formatNumber(column.span_days)}</td>
                    <td>{formatNumber(column.unique)}</td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function Statistics({ statistics }) {
  const hasAny =
    statistics.numeric.length ||
    statistics.categorical.length ||
    statistics.datetime.length;

  if (!hasAny) {
    return (
      <Card title="Statistics">
        <EmptyState
          title="No statistics to show"
          message="No numerical, categorical or date columns were detected in this dataset."
        />
      </Card>
    );
  }

  return (
    <div className="dp-stack">
      {statistics.numeric.length > 0 && <NumericTable columns={statistics.numeric} />}
      {statistics.categorical.length > 0 && (
        <CategoricalTable columns={statistics.categorical} />
      )}
      {statistics.datetime.length > 0 && <DatetimeTable columns={statistics.datetime} />}
    </div>
  );
}

export default Statistics;
