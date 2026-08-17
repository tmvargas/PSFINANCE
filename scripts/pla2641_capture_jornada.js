const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const baseUrl = process.env.PLA2641_BASE_URL || "http://127.0.0.1:15104";
const evidenceDir = path.resolve("docs/evidencias/PLA-2641");
const results = [];

function money(text) {
  return text.replace(/\s+/g, " ").trim();
}

(async () => {
  fs.mkdirSync(evidenceDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });

  const cases = [
    { id: "todas", month: "8", year: "2026", company: "1", situation: "todas", screenshot: true },
    { id: "em-aberto", month: "8", year: "2026", company: "1", situation: "em_aberto", screenshot: true },
    { id: "baixada", month: "8", year: "2026", company: "1", situation: "baixada", screenshot: true },
    { id: "invalida", month: "8", year: "2026", company: "1", situation: "invalida", screenshot: true },
    { id: "todas-empresas", month: "8", year: "2026", company: "", situation: "todas" },
    { id: "julho-empresa-1", month: "7", year: "2026", company: "1", situation: "todas" },
    { id: "agosto-2025-empresa-1", month: "8", year: "2025", company: "1", situation: "todas" },
  ];

  for (const testCase of cases) {
    const { situation } = testCase;
    console.log(`Preparando caso ${testCase.id}`);
    await page.goto(`${baseUrl}/financeiro/titulos`, { waitUntil: "domcontentloaded" });
    await page.selectOption("#mes", testCase.month);
    await page.selectOption("#ano", testCase.year);
    const companyOptions = await page.locator("#id_empresa option").evaluateAll((options) =>
      options.map((option) => ({ value: option.value, label: option.textContent.trim() })),
    );
    const company = companyOptions.find((option) => option.value === testCase.company);
    if (!company) throw new Error(`Empresa ${testCase.company} não encontrada no caso ${testCase.id}`);
    await page.selectOption("#id_empresa", company.value);
    if (situation === "invalida") {
      await page.evaluate(() => {
        const option = document.createElement("option");
        option.value = "invalida";
        option.textContent = "Inválida";
        document.querySelector("#situacao").appendChild(option);
      });
    }
    await page.selectOption("#situacao", situation);

    const startedAt = Date.now();
    await Promise.all([
      page.waitForURL((url) => url.searchParams.has("situacao"), { timeout: 10000, waitUntil: "commit" }),
      page.locator("form.titles-filter button[type=submit]").click(),
    ]);
    console.log(`Carregado ${page.url()}`);
    const elapsedMs = Date.now() - startedAt;
    const metrics = await page.locator(".titles-metric").evaluateAll((nodes) =>
      Object.fromEntries(nodes.map((node) => {
        const label = node.querySelector("span").textContent.trim();
        const value = node.querySelector("strong").textContent.trim();
        return [label, value];
      })),
    );
    const rows = await page.locator("tbody tr").count();
    const selectedSituation = await page.locator("#situacao option:checked").textContent();
    const result = {
      id: testCase.id,
      month: testCase.month,
      year: testCase.year,
      requestedSituation: situation,
      selectedSituation: selectedSituation.trim(),
      company,
      url: page.url(),
      elapsedMs,
      rows,
      metrics: Object.fromEntries(Object.entries(metrics).map(([key, value]) => [key, money(value)])),
    };
    results.push(result);
    if (testCase.screenshot) {
      await page.screenshot({
        path: path.join(evidenceDir, `consulta-titulos-${testCase.id}-staging.png`),
        fullPage: true,
      });
    }
  }

  fs.writeFileSync(
    path.join(evidenceDir, "jornada-real.json"),
    `${JSON.stringify(results, null, 2)}\n`,
  );
  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
