import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
// Self-hosted IBM Plex (no third-party font requests; works offline).
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/ibm-plex-serif/400.css";
import "@fontsource/ibm-plex-serif/500.css";
import "@fontsource/ibm-plex-mono/400.css";
import "./styles/globals.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
