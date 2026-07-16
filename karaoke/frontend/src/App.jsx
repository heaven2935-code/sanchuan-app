import { useEffect, useRef, useState } from "react";
import UrlForm from "./components/UrlForm";
import ProgressPanel from "./components/ProgressPanel";
import KaraokePlayer from "./components/KaraokePlayer";
import { createJob, getJob } from "./lib/api";
import "./App.css";

const POLL_INTERVAL_MS = 800;

export default function App() {
  const [phase, setPhase] = useState("input"); // input | loading | player
  const [job, setJob] = useState(null);
  const pollRef = useRef(null);

  useEffect(() => () => clearInterval(pollRef.current), []);

  function pollJob(jobId) {
    clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const data = await getJob(jobId);
        setJob(data);
        if (data.status === "ready" || data.status === "error") {
          clearInterval(pollRef.current);
          if (data.status === "ready") setPhase("player");
        }
      } catch (err) {
        clearInterval(pollRef.current);
        setJob({ status: "error", error: err.message });
      }
    }, POLL_INTERVAL_MS);
  }

  async function handleSubmitUrl(url) {
    setPhase("loading");
    setJob({ status: "pending", progress: 0 });
    try {
      const { job_id } = await createJob(url);
      pollJob(job_id);
    } catch (err) {
      setJob({ status: "error", error: err.message });
    }
  }

  function handleReset() {
    clearInterval(pollRef.current);
    setPhase("input");
    setJob(null);
  }

  return (
    <div className="app-shell">
      {phase === "input" && <UrlForm onSubmit={handleSubmitUrl} disabled={false} />}
      {phase === "loading" && <ProgressPanel job={job} onRetry={handleReset} onCancel={handleReset} />}
      {phase === "player" && job && <KaraokePlayer job={job} onReset={handleReset} />}
    </div>
  );
}
