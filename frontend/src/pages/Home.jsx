import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Layout/Navbar";
import UploadBox from "../components/Upload/UploadBox";
import ProcessingSteps from "../components/Upload/ProcessingSteps";
import { Card } from "../components/common/Primitives";
import { uploadCSV } from "../services/api";

const FEATURES = [
  {
    title: "Automatic profiling",
    text: "Types, cardinality, missingness and duplicates detected on upload.",
  },
  {
    title: "Data quality scoring",
    text: "Four weighted dimensions and a ranked list of what to fix first.",
  },
  {
    title: "Plain-language insights",
    text: "Skew, outliers, imbalance and correlation, explained in sentences.",
  },
  {
    title: "AutoML in one click",
    text: "Problem detection, preprocessing, model comparison and predictions.",
  },
];

function Home() {
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleUpload = async (file) => {
    setBusy(true);
    setError(null);
    setProgress(0);

    try {
      const data = await uploadCSV(file, setProgress);
      // The dataset id goes in the URL so the dashboard survives a refresh.
      navigate(`/dashboard/${data.dataset.dataset_id}`);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <>
      <Navbar />

      <div className="dp-hero">
        <span className="dp-hero-pill">
          <span aria-hidden="true">✦</span> AutoML & data analysis
        </span>
        <h1>
          Turn raw data into <span className="dp-hero-gradient">actionable insights</span>
          , automatically.
        </h1>
        <p>
          Upload a dataset and DataPilot profiles it, scores its quality, explains
          what it found, and trains a model — without writing any code.
        </p>
      </div>

      <div className="dp-upload-wrap">
        {busy && progress >= 100 ? (
          <Card title="Analysing your dataset">
            <ProcessingSteps />
          </Card>
        ) : (
          <UploadBox
            onUpload={handleUpload}
            busy={busy}
            progress={progress}
            serverError={error}
          />
        )}
      </div>

      <div className="dp-feature-grid">
        {FEATURES.map((feature) => (
          <div className="dp-feature" key={feature.title}>
            <div className="dp-feature-title">{feature.title}</div>
            <div className="dp-feature-text">{feature.text}</div>
          </div>
        ))}
      </div>
    </>
  );
}

export default Home;
