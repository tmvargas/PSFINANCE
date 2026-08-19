const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const baseUrl = process.env.PLA2597_BASE_URL || "http://vps69143.publiccloud.com.br:5001";
const evidenceDir = path.resolve("docs/evidencias/PLA-2597");
const exactPath = "/staging/psfinance/financeiro/extrato?id_empresa=1&id_conta=14&data_ini=2026-08-01&data_fim=2026-08-16";

(async () => {
  fs.mkdirSync(evidenceDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1100 },
    recordHar: { path: path.join(evidenceDir, "extrato-waterfall.har"), content: "omit" },
  });
  const page = await context.newPage();
  const failures = [];
  page.on("requestfailed", (request) => failures.push({
    url: request.url(),
    error: request.failure()?.errorText || "unknown",
  }));

  const startedAt = Date.now();
  const response = await page.goto(`${baseUrl}${exactPath}`, {
    waitUntil: "networkidle",
    timeout: 30000,
  });
  const loadElapsedMs = Date.now() - startedAt;
  await page.screenshot({
    path: path.join(evidenceDir, "extrato-navegador-real-staging.png"),
    fullPage: true,
  });

  const resources = await page.evaluate(() => performance.getEntriesByType("resource").map((entry) => ({
    name: entry.name,
    initiatorType: entry.initiatorType,
    startTimeMs: Number(entry.startTime.toFixed(2)),
    responseEndMs: Number(entry.responseEnd.toFixed(2)),
    durationMs: Number(entry.duration.toFixed(2)),
    transferSize: entry.transferSize,
  })));
  const navigation = await page.evaluate(() => {
    const entry = performance.getEntriesByType("navigation")[0];
    return {
      domContentLoadedMs: Number(entry.domContentLoadedEventEnd.toFixed(2)),
      loadEventMs: Number(entry.loadEventEnd.toFixed(2)),
      durationMs: Number(entry.duration.toFixed(2)),
      transferSize: entry.transferSize,
    };
  });

  const smokePaths = [
    "/staging/psfinance/health",
    "/staging/psfinance/",
    "/staging/psfinance/financeiro/titulos?mes=8&ano=2026&id_empresa=1",
    "/staging/psfinance/financeiro/analise?id_empresa=1&data_ini=2026-08-01&data_fim=2026-08-16",
  ];
  const smoke = [];
  for (const smokePath of smokePaths) {
    const smokeStartedAt = Date.now();
    const smokeResponse = await page.goto(`${baseUrl}${smokePath}`, {
      waitUntil: "networkidle",
      timeout: 30000,
    });
    smoke.push({ path: smokePath, status: smokeResponse?.status(), elapsedMs: Date.now() - smokeStartedAt });
  }

  const result = {
    capturedAt: new Date().toISOString(),
    url: `${baseUrl}${exactPath}`,
    status: response?.status(),
    loadElapsedMs,
    navigation,
    resources,
    requestFailures: failures,
    pendingRequestsAfterNetworkIdle: 0,
    smoke,
  };
  fs.writeFileSync(path.join(evidenceDir, "navegador-real.json"), `${JSON.stringify(result, null, 2)}\n`);
  await context.close();
  const harPath = path.join(evidenceDir, "extrato-waterfall.har");
  const har = JSON.parse(fs.readFileSync(harPath, "utf8"));
  for (const entry of har.log.entries) {
    entry.request.cookies = [];
    entry.response.cookies = [];
    entry.request.headers = entry.request.headers.filter(
      (header) => !["cookie", "authorization"].includes(header.name.toLowerCase()),
    );
    entry.response.headers = entry.response.headers.filter(
      (header) => header.name.toLowerCase() !== "set-cookie",
    );
  }
  fs.writeFileSync(harPath, `${JSON.stringify(har)}\n`);
  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
