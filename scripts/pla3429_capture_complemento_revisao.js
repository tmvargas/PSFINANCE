const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const baseUrl = process.env.PLA3429_BASE_URL || "http://127.0.0.1:15104/staging/psfinance";
const evidenceDir = path.resolve("docs/evidencias/PLA-3429");

function normalize(text) {
  return text.replace(/\s+/g, " ").trim();
}

async function collect(page, testCase) {
  const url = `${baseUrl}/financeiro/titulos?${new URLSearchParams(testCase.params)}`;
  await page.goto(url, { waitUntil: "networkidle" });

  const rows = await page.locator("tbody tr").evaluateAll((nodes) =>
    nodes.map((node) => node.innerText.replace(/\s+/g, " ").trim()),
  );
  const metrics = await page.locator(".titles-metric").evaluateAll((nodes) =>
    Object.fromEntries(nodes.map((node) => [
      node.querySelector("span").textContent.replace(/\s+/g, " ").trim(),
      node.querySelector("strong").textContent.replace(/\s+/g, " ").trim(),
    ])),
  );
  const selected = {
    empresa: await page.locator("#id_empresa option:checked").textContent(),
    credor: await page.locator("#id_credor option:checked").textContent(),
    situacao: await page.locator("#situacao option:checked").textContent(),
    modo: await page.locator('input[name="modo_vencimento"]:checked').getAttribute("value"),
    emissao: await page.locator("#emissao").inputValue(),
    titulo: await page.locator("#titulo").inputValue(),
  };

  for (const expected of testCase.expectedTitles) {
    if (!rows.some((row) => row.startsWith(`${expected} -`))) {
      throw new Error(`${testCase.id}: título ${expected} não foi retornado`);
    }
  }
  for (const unexpected of testCase.unexpectedTitles || []) {
    if (rows.some((row) => row.startsWith(`${unexpected} -`))) {
      throw new Error(`${testCase.id}: título indevido ${unexpected} foi retornado`);
    }
  }
  if (rows.length !== testCase.expectedRows) {
    throw new Error(`${testCase.id}: esperado ${testCase.expectedRows}, obtido ${rows.length}`);
  }

  if (testCase.screenshot) {
    await page.screenshot({ path: path.join(evidenceDir, testCase.screenshot), fullPage: true });
  }

  return {
    id: testCase.id,
    objetivo: testCase.objective,
    url: page.url(),
    expectedRows: testCase.expectedRows,
    returnedTitles: rows.map((row) => Number(row.match(/^(\d+)\s+-/)?.[1])).filter(Boolean),
    expectedTitles: testCase.expectedTitles,
    unexpectedTitles: testCase.unexpectedTitles || [],
    selected: Object.fromEntries(Object.entries(selected).map(([key, value]) => [key, normalize(value || "")])),
    metrics,
    result: "aprovado",
  };
}

(async () => {
  fs.mkdirSync(evidenceDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
  const cases = [
    {
      id: "credor-positivo",
      objective: "Comprovar credor vinculado à empresa com resultado positivo.",
      params: { mes: "8", ano: "2026", modo_vencimento: "mes", id_empresa: "2", id_credor: "6", situacao: "em_aberto" },
      expectedRows: 1,
      expectedTitles: [69],
      unexpectedTitles: [49],
    },
    {
      id: "emissao-positiva",
      objective: "Comprovar emissão exata combinada com situação Baixada.",
      params: { mes: "8", ano: "2026", modo_vencimento: "mes", id_empresa: "1", emissao: "2026-08-10", situacao: "baixada" },
      expectedRows: 3,
      expectedTitles: [49, 50, 53],
      unexpectedTitles: [54, 55, 69],
    },
    {
      id: "titulo-simples",
      objective: "Comprovar busca por ID em título legado sem parcelas.",
      params: { mes: "8", ano: "2026", modo_vencimento: "mes", id_empresa: "1", titulo: "54", situacao: "em_aberto" },
      expectedRows: 1,
      expectedTitles: [54],
      unexpectedTitles: [66],
    },
    {
      id: "titulo-parcelado",
      objective: "Comprovar busca operacional por descrição em título parcelado.",
      params: { modo_vencimento: "periodo", vencimento_inicial: "2026-08-01", vencimento_final: "2026-08-31", id_empresa: "4", titulo: "TERRENO VIDA NOVA", situacao: "baixada" },
      expectedRows: 1,
      expectedTitles: [66],
      unexpectedTitles: [54],
    },
    {
      id: "combinacao-positiva",
      objective: "Comprovar período, empresa, credor, emissão, título e situação combinados com resultado positivo.",
      params: { modo_vencimento: "periodo", vencimento_inicial: "2026-08-01", vencimento_final: "2026-08-31", id_empresa: "2", id_credor: "6", emissao: "2026-08-01", titulo: "EMAILGO", situacao: "em_aberto" },
      expectedRows: 1,
      expectedTitles: [69],
      unexpectedTitles: [49, 50, 66],
      screenshot: "consulta-titulos-filtro-positivo-5001.png",
    },
  ];

  const results = [];
  for (const testCase of cases) results.push(await collect(page, testCase));
  fs.writeFileSync(
    path.join(evidenceDir, "matriz-complemento-revisao-5001.json"),
    `${JSON.stringify(results, null, 2)}\n`,
  );
  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
