const { app, BrowserWindow, dialog } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs");
const http = require("http");
const path = require("path");

const WEB_URL_OVERRIDE = process.env.TOOL_BOND_WEB_URL || "";
const API_HOST = process.env.TOOL_BOND_API_HOST || "127.0.0.1";
const API_PORT = Number(process.env.TOOL_BOND_API_PORT || "8000");

let backendProcess = null;
let webServer = null;
let shutdownStarted = false;

function resolveWindowIconPath() {
  const candidates = [
    path.join(__dirname, "assets", "icon.png"),
    path.join(process.resourcesPath, "assets", "icon.png"),
  ];
  return candidates.find((candidate) => fs.existsSync(candidate)) || undefined;
}

function resolveBackendExecutable() {
  const candidates = [
    path.join(process.resourcesPath, "bin", "tool-bond-api.exe"),
    path.join(__dirname, "standalone-resources", "bin", "tool-bond-api.exe"),
  ];
  return candidates.find((candidate) => fs.existsSync(candidate)) || null;
}

function resolveWebRoot() {
  const candidates = [
    path.join(process.resourcesPath, "web"),
    path.join(__dirname, "standalone-resources", "web"),
    path.join(__dirname, "..", "web", "out"),
  ];
  return candidates.find((candidate) => fs.existsSync(path.join(candidate, "index.html"))) || null;
}

function getMimeType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  switch (ext) {
    case ".html":
      return "text/html; charset=utf-8";
    case ".js":
      return "application/javascript; charset=utf-8";
    case ".css":
      return "text/css; charset=utf-8";
    case ".json":
      return "application/json; charset=utf-8";
    case ".png":
      return "image/png";
    case ".jpg":
    case ".jpeg":
      return "image/jpeg";
    case ".svg":
      return "image/svg+xml";
    case ".ico":
      return "image/x-icon";
    case ".txt":
      return "text/plain; charset=utf-8";
    default:
      return "application/octet-stream";
  }
}

function startStaticWebServer(webRoot) {
  return new Promise((resolve, reject) => {
    const server = http.createServer((req, res) => {
      try {
        const urlPath = new URL(req.url || "/", "http://127.0.0.1").pathname;
        const requested = decodeURIComponent(urlPath);
        const normalized = requested === "/" ? "index.html" : requested.replace(/^\/+/, "");
        const absolutePath = path.resolve(webRoot, normalized);
        const rootResolved = path.resolve(webRoot);

        if (!absolutePath.startsWith(rootResolved)) {
          res.statusCode = 403;
          res.end("Forbidden");
          return;
        }

        let filePath = absolutePath;
        if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
          filePath = path.join(rootResolved, "index.html");
        }

        const payload = fs.readFileSync(filePath);
        res.setHeader("Content-Type", getMimeType(filePath));
        res.end(payload);
      } catch (err) {
        res.statusCode = 500;
        res.end(String(err));
      }
    });

    server.once("error", (err) => reject(err));
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = address && typeof address === "object" ? address.port : 0;
      resolve({
        server,
        url: `http://127.0.0.1:${port}`,
      });
    });
  });
}

function waitForApiReady(timeoutMs = 45000) {
  const startedAt = Date.now();
  const endpoint = `http://${API_HOST}:${API_PORT}/health`;

  return new Promise((resolve, reject) => {
    const ping = () => {
      const req = http.get(endpoint, (res) => {
        if (res.statusCode === 200) {
          resolve();
          res.resume();
          return;
        }
        res.resume();
        retry();
      });
      req.on("error", retry);
      req.setTimeout(1500, () => {
        req.destroy();
        retry();
      });
    };

    const retry = () => {
      if (Date.now() - startedAt > timeoutMs) {
        reject(new Error("Backend health check timeout."));
        return;
      }
      setTimeout(ping, 500);
    };

    ping();
  });
}

async function ensureBackendStarted() {
  if (WEB_URL_OVERRIDE) {
    return;
  }

  const backendExe = resolveBackendExecutable();
  if (!backendExe) {
    throw new Error("Standalone backend executable not found.");
  }

  backendProcess = spawn(backendExe, [], {
    windowsHide: true,
    stdio: "ignore",
    env: {
      ...process.env,
      APP_ENV: "desktop",
      API_SERVICE_NAME: "tool-bond-api",
      API_SERVICE_VERSION: "0.2.0-standalone",
      TOOL_BOND_API_HOST: API_HOST,
      TOOL_BOND_API_PORT: String(API_PORT),
      CORS_ALLOW_ORIGINS: "*",
      PERSISTENCE_BACKEND: "local_file",
    },
  });

  await waitForApiReady();
}

async function createWindow() {
  const iconPath = resolveWindowIconPath();
  const win = new BrowserWindow({
    width: 1360,
    height: 860,
    minWidth: 1024,
    minHeight: 700,
    title: "Tool Bond Desktop",
    icon: iconPath,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  if (WEB_URL_OVERRIDE) {
    await win.loadURL(WEB_URL_OVERRIDE);
    return;
  }

  const webRoot = resolveWebRoot();
  if (webRoot) {
    if (!webServer) {
      webServer = await startStaticWebServer(webRoot);
    }
    await win.loadURL(webServer.url);
    return;
  }

  await win.loadURL("http://localhost:3000");
}

function stopBackend() {
  return new Promise((resolve) => {
    if (!backendProcess || !backendProcess.pid) {
      backendProcess = null;
      resolve();
      return;
    }

    const pid = backendProcess.pid;

    // On Windows kill the whole process tree to avoid orphan child processes.
    if (process.platform === "win32") {
      const killer = spawn("taskkill", ["/PID", String(pid), "/T", "/F"], {
        windowsHide: true,
        stdio: "ignore",
      });
      killer.on("error", () => {
        backendProcess = null;
        resolve();
      });
      killer.on("exit", () => {
        backendProcess = null;
        resolve();
      });
      return;
    }

    try {
      backendProcess.kill("SIGKILL");
    } catch {
      // no-op
    }
    backendProcess = null;
    resolve();
  });
}

function stopWebServer() {
  return new Promise((resolve) => {
    if (!webServer || !webServer.server) {
      webServer = null;
      resolve();
      return;
    }

    webServer.server.close(() => {
      webServer = null;
      resolve();
    });
  });
}

async function shutdownRuntime() {
  await Promise.allSettled([stopWebServer(), stopBackend()]);
}

async function createAndHandleStartup() {
  try {
    await ensureBackendStarted();
  } catch (err) {
    await dialog.showMessageBox({
      type: "error",
      title: "Tool Bond Desktop",
      message: "Unable to start local backend.",
      detail: String(err),
    });
  }
  await createWindow();
}

app.whenReady().then(async () => {
  await createAndHandleStartup();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("before-quit", (event) => {
  if (shutdownStarted) {
    return;
  }
  event.preventDefault();
  shutdownStarted = true;
  shutdownRuntime().finally(() => {
    app.quit();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
