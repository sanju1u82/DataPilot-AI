/** Dashboard section navigation. Collapses to a horizontal scroller on mobile. */

const SECTIONS = [
  {
    label: "Analyse",
    items: [
      { id: "overview", name: "Overview" },
      { id: "preview", name: "Data preview" },
      { id: "quality", name: "Data quality" },
      { id: "statistics", name: "Statistics" },
      { id: "insights", name: "Insights" },
    ],
  },
  {
    label: "Model",
    items: [
      { id: "automl", name: "AutoML" },
      { id: "code", name: "Code lab" },
    ],
  },
];

function Sidebar({ active, onSelect }) {
  return (
    <aside className="dp-sidebar">
      {SECTIONS.map((section) => (
        <div className="dp-sidebar-group" key={section.label}>
          <div className="dp-sidebar-label">{section.label}</div>
          {section.items.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`dp-nav-item${active === item.id ? " is-active" : ""}`}
              onClick={() => onSelect(item.id)}
            >
              {item.name}
            </button>
          ))}
        </div>
      ))}
    </aside>
  );
}

export default Sidebar;
