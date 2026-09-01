import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import Navbar from "../components/Layout/Navbar";
import Sidebar from "../components/Layout/Sidebar";
import DatasetCard from "../components/Dashboard/DatasetCard";
import PreviewTable from "../components/Dashboard/PreviewTable";
import ColumnTable from "../components/Dashboard/ColumnTable";
import DataQuality from "../components/Dashboard/DataQuality";
import Statistics from "../components/Dashboard/Statistics";
import Charts from "../components/Dashboard/Charts";
import Insights from "../components/Dashboard/Insights";
import AutoML from "../components/Dashboard/AutoML";
import CodeLab from "../components/Dashboard/CodeLab";
import { Card, ErrorState, Loading } from "../components/common/Primitives";
import { fetchSummary } from "../services/api";

const SECTION_TITLES = {
  overview: "Overview",
  preview: "Data preview",
  quality: "Data quality",
  statistics: "Statistics",
  insights: "Insights",
  automl: "AutoML",
  code: "Code lab",
};

function Dashboard() {
  const { datasetId } = useParams();
  const navigate = useNavigate();

  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const [section, setSection] = useState("overview");

  useEffect(() => {
    let cancelled = false;
    setSummary(null);
    setError(null);

    fetchSummary(datasetId)
      .then((data) => !cancelled && setSummary(data))
      .catch((err) => !cancelled && setError(err.message));

    return () => {
      cancelled = true;
    };
  }, [datasetId]);

  if (error) {
    return (
      <>
        <Navbar />
        <ErrorState
          title="We couldn't load this dataset"
          message={error}
          action={
            <button
              type="button"
              className="dp-btn dp-btn-primary"
              onClick={() => navigate("/")}
            >
              Upload a dataset
            </button>
          }
        />
      </>
    );
  }

  if (!summary) {
    return (
      <>
        <Navbar />
        <Loading title="Loading analysis…" message="Fetching the dataset profile." />
      </>
    );
  }

  const { dataset, preview, profile, statistics, quality, insights } = summary;

  const sections = {
    overview: (
      <div className="dp-stack">
        <DatasetCard dataset={dataset} profile={profile} quality={quality} />
        <div className="dp-headline">{insights.headline}</div>
        <ColumnTable profile={profile} />
        <Charts statistics={statistics} />
      </div>
    ),
    preview: <PreviewTable preview={preview} />,
    quality: <DataQuality quality={quality} />,
    statistics: <Statistics statistics={statistics} />,
    insights: <Insights insights={insights} />,
    automl: <AutoML datasetId={datasetId} />,
    code: <CodeLab datasetId={datasetId} profile={profile} />,
  };

  return (
    <>
      <Navbar dataset={dataset}>
        <button
          type="button"
          className="dp-btn dp-btn-ghost"
          onClick={() => navigate("/")}
        >
          New dataset
        </button>
      </Navbar>

      <div className="app-shell">
        <Sidebar active={section} onSelect={setSection} />

        <main className="app-main">
          <div className="section-title">
            <div>
              <div className="eyebrow">DataPilot AI</div>
              <h2 style={{ fontSize: 24 }}>{SECTION_TITLES[section]}</h2>
            </div>
          </div>

          {sections[section] ?? (
            <Card title="Not found">
              <p className="text-dim">That section doesn't exist.</p>
            </Card>
          )}
        </main>
      </div>
    </>
  );
}

export default Dashboard;
