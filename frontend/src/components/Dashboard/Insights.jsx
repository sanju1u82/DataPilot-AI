import { Badge, Card } from "../common/Primitives";

const CATEGORY_LABEL = {
  shape: "Shape",
  quality: "Quality",
  distribution: "Distribution",
  categories: "Categories",
  relationships: "Relationships",
};

/** Plain-language findings, grouped by what they are about. */
function Insights({ insights }) {
  const grouped = insights.insights.reduce((groups, insight) => {
    (groups[insight.category] ||= []).push(insight);
    return groups;
  }, {});

  return (
    <div className="dp-stack">
      <div className="dp-headline">{insights.headline}</div>

      {Object.entries(grouped).map(([category, items]) => (
        <Card
          key={category}
          title={CATEGORY_LABEL[category] || category}
          actions={<Badge>{items.length}</Badge>}
        >
          <div className="dp-insight-list">
            {items.map((insight, index) => (
              <div className={`dp-insight tone-${insight.tone}`} key={index}>
                <span className="dp-insight-dot" aria-hidden="true" />
                <span>{insight.message}</span>
              </div>
            ))}
          </div>
        </Card>
      ))}
    </div>
  );
}

export default Insights;
