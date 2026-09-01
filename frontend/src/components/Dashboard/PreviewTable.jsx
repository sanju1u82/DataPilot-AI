import { Card } from "../common/Primitives";
import { formatCell, formatNumber } from "../../utils/format";

/**
 * First rows of the dataset.
 *
 * The table scrolls inside its own container so a wide dataset never forces the
 * page itself to scroll sideways.
 */
function PreviewTable({ preview }) {
  return (
    <Card title="Dataset preview" flush>
      <div className="dp-table-scroll" style={{ maxHeight: 520 }}>
        <table className="dp-table">
          <thead>
            <tr>
              <th style={{ width: 52 }}>#</th>
              {preview.columns.map((column) => (
                <th key={column}>
                  <div>{column}</div>
                  <div className="dp-col-type">{preview.data_types[column]}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {preview.rows.map((row, index) => (
              <tr key={index}>
                <td className="text-faint">{index + 1}</td>
                {preview.columns.map((column) => {
                  const value = formatCell(row[column]);
                  return (
                    <td key={column} className={value === null ? "is-null" : undefined}>
                      {value === null ? "null" : value}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="dp-table-caption">
        Showing {preview.showing} of {formatNumber(preview.total_rows)} rows ·{" "}
        {preview.columns.length} columns
      </div>
    </Card>
  );
}

export default PreviewTable;
