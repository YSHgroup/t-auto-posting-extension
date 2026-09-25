import { defineManifest } from "@crxjs/vite-plugin";

export default defineManifest({
  manifest_version: 3,
  name: "Telegram Auto Bot",
  version: "0.1.0",
  description: "Independent Telegram automation assistant (mock data mode).",
  permissions: ["storage", "sidePanel"],
  host_permissions: ["http://localhost:8000/*", "https://*/*"],
  action: {
    default_title: "Telegram Auto Bot",
  },
  side_panel: {
    default_path: "sidepanel.html",
  },
  background: {
    service_worker: "src/background.ts",
    type: "module",
  },
});
