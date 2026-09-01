import { Badge, Card } from "../common/Primitives";
import { TYPE_TONE, formatNumber, formatPercent } from "../../utils/format";

/** Per-column structure: type, missingness, cardinality and any warning flags. */
function ColumnTable({ profile }) {
  return (
    <Card title={`Columns (${profile.columns.length})`} flush>
      <div className="dp-table-scroll" style={{ maxHeight: 520 }}>
        <table className="dp-table">
          <thead>
            <tr>
              <th>Column</th>
              <th>Detected type</th>
              <th>Pandas dtype</th>
              <th>Missing</th>
              <th>Unique</th>
              <th>Flags</th>
              <th>Sample values</th>
            </tr>
          </thead>
          <tbody>
            {profile.columns.map((column) => (
              <tr key={column.name}>
                <td style={{ fontWeight: 600 }}>{column.name}</td>
                <td>
                  <Badge tone={TYPE_TONE[column.semantic_type] || ""}>
                    {column.semantic_type}
                  </Badge>
                </td>
                <td className="mono text-faint">{column.dtype}</td>
                <td>
                  {column.missing === 0 ? (
                    <span className="text-faint">none</span>
                  ) : (
                    <>
                      {formatNumber(column.missing)}{" "}
                      <span className="text-faint">
                        ({formatPercent(column.missing_percentage, 1)})
                      </span>
                    </>
                  )}
                </td>
                <td>{formatNumber(column.unique)}</td>
                <td>
                  <div className="dp-row" style={{ gap: 6 }}>
                    {column.is_empty && <Badge tone="danger">empty</Badge>}
                    {column.is_constant && !column.is_empty && (
                      <Badge tone="warning">constant</Badge>
                    )}
                    {column.is_identifier && <Badge tone="danger">id</Badge>}
                    {!column.is_empty && !column.is_constant && !column.is_identifier && (
                      <span className="text-faint">—</span>
                    )}
                  </div>
                </td>
                <td
                  className="text-dim"
                  style={{ maxWidth: 260, overflow: "hidden", textOverflow: "ellipsis" }}
                  title={column.sample_values.join(", ")}
                >
                  {column.sample_values.length
                    ? column.sample_values.slice(0, 3).join(", ")
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

export default ColumnTable;
