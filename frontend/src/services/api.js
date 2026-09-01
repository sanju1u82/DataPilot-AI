import axios from "axios";

const BACKEND_PORT = import.meta.env.VITE_API_PORT || "8000";

/**
 * Work out where the backend lives.
 *
 * No hostname is hardcoded. In Codespaces the frontend runs on a forwarded
 * port named `<workspace>-5173.app.github.dev` and the backend on the matching
 * `-8000` host, so the API URL is derived from wherever the page is served.
 * That keeps working after a Codespace rebuild, which a pasted URL does not.
 */
export function resolveBaseUrl() {
  const configured = import.meta.env.VITE_API_URL;
  if (configured) {
    return configured.replace(/\/+$/, "");
  }

  // Production build. FastAPI serves these files itself, so the API is on the
  // same origin and a relative base is correct — guessing a port here would
  // send requests to localhost on the visitor's own machine.
  if (!import.meta.env.DEV) {
    return "";
  }

  if (typeof window !== "undefined") {
    const { protocol, hostname, port } = window.location;

    const forwardedPort = hostname.match(/^(.*)-(\d+)\.(app\.github\.dev|githubpreview\.dev)$/);
    if (forwardedPort) {
      const [, workspace, , domain] = forwardedPort;
      return `${protocol}//${workspace}-${BACKEND_PORT}.${domain}`;
    }

    // Local dev: same host as the Vite server, different port.
    if (port) {
      return `${protocol}//${hostname}:${BACKEND_PORT}`;
    }
  }

  return `http://localhost:${BACKEND_PORT}`;
}

export const API_BASE_URL = resolveBaseUrl();

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

/** Turn any axios failure into the message the UI should show. */
function toFriendlyError(error) {
  const backendMessage = error?.response?.data?.message;
  if (backendMessage) {
    const wrapped = new Error(backendMessage);
    wrapped.code = error.response.data.code;
    wrapped.status = error.response.status;
    return wrapped;
  }

  if (error?.code === "ECONNABORTED") {
    return new Error("That took too long to finish. Try a smaller dataset.");
  }

  // No response at all: the backend is down, or its port is still private.
  if (!error?.response) {
    const target =
      API_BASE_URL ||
      (typeof window !== "undefined" ? window.location.origin : "the server");
    return new Error(
      `Couldn't reach the API at ${target}. Check the backend is running — ` +
        "and in Codespaces, that port 8000 is set to Public."
    );
  }

  return new Error("Something went wrong. Please try again.");
}

async function request(promise) {
  try {
    const response = await promise;
    return response.data;
  } catch (error) {
    throw toFriendlyError(error);
  }
}

export const uploadCSV = (file, onProgress) => {
  const formData = new FormData();
  formData.append("file", file);

  return request(
    client.post("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (event) => {
        if (onProgress && event.total) {
          onProgress(Math.round((event.loaded / event.total) * 100));
        }
      },
    })
  );
};

export const fetchSummary = (datasetId) =>
  request(client.get(`/dataset/${datasetId}/summary`));

export const fetchGeneratedCode = (datasetId, target) =>
  request(
    client.get(`/dataset/${datasetId}/code`, {
      params: target ? { target } : undefined,
    })
  );

export const fetchTargetSuggestions = (datasetId) =>
  request(client.get(`/dataset/${datasetId}/targets`));

export const startTraining = (datasetId, target) =>
  request(client.post(`/dataset/${datasetId}/train`, { target }));

export const fetchRun = (runId) => request(client.get(`/run/${runId}`));

export const fetchPredictionSchema = (runId) =>
  request(client.get(`/run/${runId}/schema`));

export const predict = (runId, rows) =>
  request(client.post(`/run/${runId}/predict`, { rows }));

export default client;
