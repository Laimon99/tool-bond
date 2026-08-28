"use client";

import { FormEvent, useMemo, useState } from "react";

const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const API_BASE_URL = configuredApiBaseUrl === "same-origin" ? "" : configuredApiBaseUrl;
const API_DISPLAY_URL = API_BASE_URL || "same origin";
const IS_PUBLIC_DEMO = process.env.NEXT_PUBLIC_PUBLIC_DEMO === "true";

type JsonObject = Record<string, unknown>;
type JsonValue = JsonObject | null;
type PriceInputType = "clean_price" | "ytm";
type InterpolationMode = "linear" | "loglinear";
type FxRateSide = "ask" | "mid" | "bid";
type ActiveTab = "manual" | "upload";

type ManualFormState = {
  requestId: string;
  settlementDate: string;
  usdBudget: string;
  spotUsdTry: string;
  couponRateAnnual: string;
  couponFrequency: string;
  faceValuePerUnit: string;
  issueDate: string;
  maturityDate: string;
  scheduleDatesText: string;
  priceType: PriceInputType;
  priceValue: string;
  fxInterpolation: InterpolationMode;
  fxRateSide: FxRateSide;
  dfPointsText: string;
  fxPillarsText: string;
  includeBreakdown: boolean;
  persistRun: boolean;
  roundingDecimals: string;
};

type BreakdownRow = {
  date: string;
  tryCashflow: number | null;
  fxRate: number | null;
  fxRateSide: string;
  usdCashflow: number | null;
  usdDf: number | null;
  pvUsd: number | null;
};

type ApiError = { code: string; message: string; field?: string };

type ResultSummary = {
  status: string;
  runId: string;
  npvUsd: number | null;
  pvUsdTotal: number | null;
  notionalTry: number | null;
  units: number | null;
  dirtyPricePercent: number | null;
  breakdownRows: BreakdownRow[];
  assumptions: Record<string, string | number>;
  warnings: string[];
  errors: ApiError[];
};

type ImportSummary = {
  settlementDate: string;
  usdBudget: number | null;
  spotUsdTry: number | null;
  priceType: string;
  priceValue: number | null;
  fxPillarsCount: number;
  dfPointsCount: number;
};

const DEMO_DEFAULTS: ManualFormState = {
  requestId: "req_public_demo_001",
  settlementDate: "2026-02-20",
  usdBudget: "100000",
  spotUsdTry: "43.76",
  couponRateAnnual: "0.275",
  couponFrequency: "1",
  faceValuePerUnit: "10000",
  issueDate: "2023-03-06",
  maturityDate: "2028-03-06",
  scheduleDatesText: "2024-03-06\n2025-03-06\n2026-03-06\n2027-03-06\n2028-03-06",
  priceType: "clean_price",
  priceValue: "90",
  fxInterpolation: "linear",
  fxRateSide: "ask",
  dfPointsText: "2026-03-06,0.995\n2027-03-06,0.955\n2028-03-06,0.910",
  fxPillarsText: "2026-03-06,44.2,44.3\n2027-03-06,58.0,58.1\n2028-03-06,75.0,75.2",
  includeBreakdown: true,
  persistRun: false,
  roundingDecimals: "6",
};

async function postJson(url: string, payload: JsonValue) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const json = await response.json();
  return { status: response.status, json };
}

function asRecord(value: unknown): JsonObject | null {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as JsonObject) : null;
}

function toNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function formatNumber(value: number | null, digits = 2): string {
  if (value === null) return "—";
  return value.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function isIsoDate(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function parsePositiveNumber(label: string, raw: string, errors: string[], allowZero = false): number {
  const value = Number(raw);
  if (!Number.isFinite(value) || (allowZero ? value < 0 : value <= 0)) {
    errors.push(`${label} must be ${allowZero ? "zero or greater" : "greater than zero"}.`);
    return 0;
  }
  return value;
}

function parseInteger(label: string, raw: string, allowed: number[], errors: string[]): number {
  const value = Number(raw);
  if (!Number.isInteger(value) || !allowed.includes(value)) {
    errors.push(`${label} must be one of: ${allowed.join(", ")}.`);
    return allowed[0];
  }
  return value;
}

function buildManualPayload(form: ManualFormState): { payload: JsonValue; errors: string[] } {
  const errors: string[] = [];
  if (!/^[A-Za-z0-9._-]{3,80}$/.test(form.requestId.trim())) {
    errors.push("Request ID must contain 3–80 letters, numbers, dots, underscores or hyphens.");
  }

  [
    ["Settlement date", form.settlementDate],
    ["Issue date", form.issueDate],
    ["Maturity date", form.maturityDate],
  ].forEach(([label, value]) => {
    if (!isIsoDate(value)) errors.push(`${label} must use YYYY-MM-DD.`);
  });

  if (isIsoDate(form.issueDate) && isIsoDate(form.maturityDate) && form.issueDate >= form.maturityDate) {
    errors.push("Maturity date must be after issue date.");
  }

  const usdBudget = parsePositiveNumber("USD budget", form.usdBudget, errors);
  const spotUsdTry = parsePositiveNumber("Spot USDTRY", form.spotUsdTry, errors);
  const couponRateAnnual = parsePositiveNumber("Annual coupon rate", form.couponRateAnnual, errors, true);
  const couponFrequency = parseInteger("Coupon frequency", form.couponFrequency, [1, 2, 4], errors);
  const faceValuePerUnit = parsePositiveNumber("Face value per unit", form.faceValuePerUnit, errors);
  const priceValue = parsePositiveNumber("Price input", form.priceValue, errors, form.priceType === "ytm");
  const roundingDecimals = parseInteger("Rounding decimals", form.roundingDecimals, [0, 1, 2, 3, 4, 5, 6, 7, 8], errors);

  if (form.priceType === "clean_price" && priceValue > 200) errors.push("Clean price cannot exceed 200.");
  if (form.priceType === "ytm" && priceValue > 10) errors.push("Yield must be entered as a decimal between 0 and 10.");

  const scheduleDates = form.scheduleDatesText
    .split(/\r?\n|;/)
    .map((item) => item.trim())
    .filter(Boolean);
  if (!scheduleDates.length) errors.push("At least one coupon date is required.");
  if (new Set(scheduleDates).size !== scheduleDates.length) errors.push("Coupon dates must be unique.");
  scheduleDates.forEach((value) => {
    if (!isIsoDate(value)) errors.push(`Invalid coupon date: ${value}.`);
  });

  const dfPoints: Array<{ date: string; df: number }> = [];
  form.dfPointsText
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean)
    .forEach((line, index) => {
      const [date, rawDf, extra] = line.split(",").map((item) => item.trim());
      const df = Number(rawDf);
      if (extra !== undefined || !isIsoDate(date || "") || !Number.isFinite(df) || df <= 0) {
        errors.push(`USD discount row ${index + 1} must be YYYY-MM-DD,df.`);
      } else {
        dfPoints.push({ date, df });
      }
    });
  if (!dfPoints.length) errors.push("At least one USD discount-factor point is required.");

  const fxPillars: Array<{ end_date: string; bid: number; ask: number }> = [];
  form.fxPillarsText
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean)
    .forEach((line, index) => {
      const [endDate, rawBid, rawAsk, extra] = line.split(",").map((item) => item.trim());
      const bid = Number(rawBid);
      const ask = Number(rawAsk);
      if (
        extra !== undefined ||
        !isIsoDate(endDate || "") ||
        !Number.isFinite(bid) ||
        bid <= 0 ||
        !Number.isFinite(ask) ||
        ask <= 0 ||
        bid > ask
      ) {
        errors.push(`FX row ${index + 1} must be YYYY-MM-DD,bid,ask with bid ≤ ask.`);
      } else {
        fxPillars.push({ end_date: endDate, bid, ask });
      }
    });
  if (!fxPillars.length) errors.push("At least one FX-forward pillar is required.");

  if (errors.length) return { payload: null, errors };

  return {
    payload: {
      request_id: form.requestId.trim(),
      input_mode: "manual",
      valuation: {
        settlement_date: form.settlementDate,
        usd_budget: usdBudget,
        spot_usdtry: spotUsdTry,
        bond: {
          coupon_rate_annual: couponRateAnnual,
          coupon_frequency: couponFrequency,
          face_value_per_unit: faceValuePerUnit,
          issue_date: form.issueDate,
          maturity_date: form.maturityDate,
          schedule_dates: scheduleDates,
          day_count: "ACT/365F",
        },
        usd_discount_curve: { df_points: dfPoints },
        fx_forward_curve: { interpolation: form.fxInterpolation, pillars: fxPillars },
        price_input: { type: form.priceType, value: priceValue },
        options: {
          include_breakdown: form.includeBreakdown,
          persist_run: form.persistRun,
          rounding_decimals: roundingDecimals,
          fx_rate_side: form.fxRateSide,
        },
      },
    },
    errors: [],
  };
}

function extractErrors(value: unknown): ApiError[] {
  if (!Array.isArray(value)) return [];
  return value
    .map(asRecord)
    .filter((item): item is JsonObject => item !== null)
    .map((item) => ({
      code: typeof item.code === "string" ? item.code : "UNKNOWN",
      message: typeof item.message === "string" ? item.message : "Unknown error",
      field: typeof item.field === "string" ? item.field : undefined,
    }));
}

function extractResultSummary(lastResponse: JsonValue): ResultSummary | null {
  const root = asRecord(lastResponse);
  if (!root || typeof root.status !== "string") return null;
  const result = asRecord(root.result);
  const breakdown = Array.isArray(result?.breakdown) ? result.breakdown : [];
  const assumptions = asRecord(result?.model_assumptions) || {};

  return {
    status: root.status,
    runId: typeof root.run_id === "string" ? root.run_id : "—",
    npvUsd: toNumber(result?.npv_usd),
    pvUsdTotal: toNumber(result?.pv_usd_total),
    notionalTry: toNumber(result?.notional_try),
    units: toNumber(result?.units),
    dirtyPricePercent: toNumber(result?.dirty_price_percent),
    breakdownRows: breakdown
      .map(asRecord)
      .filter((row): row is JsonObject => row !== null)
      .map((row) => ({
        date: typeof row.date === "string" ? row.date : "—",
        tryCashflow: toNumber(row.try_cashflow),
        fxRate: toNumber(row.fwd_usdtry_rate),
        fxRateSide: typeof row.fx_rate_side === "string" ? row.fx_rate_side : "—",
        usdCashflow: toNumber(row.usd_cashflow),
        usdDf: toNumber(row.usd_df),
        pvUsd: toNumber(row.pv_usd),
      })),
    assumptions: Object.fromEntries(
      Object.entries(assumptions).filter((entry): entry is [string, string | number] =>
        ["string", "number"].includes(typeof entry[1]),
      ),
    ),
    warnings: Array.isArray(root.warnings) ? root.warnings.filter((item): item is string => typeof item === "string") : [],
    errors: extractErrors(root.errors),
  };
}

function extractImportSummary(normalizedPayload: JsonValue): ImportSummary | null {
  const valuation = asRecord(asRecord(normalizedPayload)?.valuation);
  if (!valuation) return null;
  const priceInput = asRecord(valuation.price_input);
  const discountCurve = asRecord(valuation.usd_discount_curve);
  const fxCurve = asRecord(valuation.fx_forward_curve);
  return {
    settlementDate: typeof valuation.settlement_date === "string" ? valuation.settlement_date : "—",
    usdBudget: toNumber(valuation.usd_budget),
    spotUsdTry: toNumber(valuation.spot_usdtry),
    priceType: typeof priceInput?.type === "string" ? priceInput.type : "—",
    priceValue: toNumber(priceInput?.value),
    fxPillarsCount: Array.isArray(fxCurve?.pillars) ? fxCurve.pillars.length : 0,
    dfPointsCount: Array.isArray(discountCurve?.df_points) ? discountCurve.df_points.length : 0,
  };
}

function InputField({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint && <small>{hint}</small>}
    </label>
  );
}

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("manual");
  const [manualForm, setManualForm] = useState<ManualFormState>(DEMO_DEFAULTS);
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploadBudget, setUploadBudget] = useState("100000");
  const [usdFlatRate, setUsdFlatRate] = useState("0.05");
  const [autoRunAfterImport, setAutoRunAfterImport] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errorText, setErrorText] = useState("");
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [importWarnings, setImportWarnings] = useState<string[]>([]);
  const [normalizedPayload, setNormalizedPayload] = useState<JsonValue>(null);
  const [lastResponse, setLastResponse] = useState<JsonValue>(null);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  const result = useMemo(() => extractResultSummary(lastResponse), [lastResponse]);
  const importSummary = useMemo(() => extractImportSummary(normalizedPayload), [normalizedPayload]);
  const canUpload = uploadFiles.length > 0;

  function updateManual<K extends keyof ManualFormState>(field: K, value: ManualFormState[K]) {
    setManualForm((previous) => ({ ...previous, [field]: value }));
  }

  function resetOutput() {
    setErrorText("");
    setValidationErrors([]);
    setImportWarnings([]);
    setNormalizedPayload(null);
    setLastResponse(null);
  }

  function switchTab(tab: ActiveTab) {
    setActiveTab(tab);
    resetOutput();
  }

  async function runManual(form: ManualFormState) {
    resetOutput();
    const built = buildManualPayload(form);
    if (built.errors.length) {
      setValidationErrors(built.errors);
      return;
    }
    setIsLoading(true);
    try {
      const { status, json } = await postJson(`${API_BASE_URL}/run-valuation`, built.payload);
      if (status >= 400) setErrorText(`The API rejected the valuation (${status}).`);
      setLastResponse(json);
      window.setTimeout(() => document.querySelector("#results")?.scrollIntoView({ behavior: "smooth" }), 50);
    } catch (error) {
      setErrorText(`Could not reach the API at ${API_DISPLAY_URL}. ${String(error)}`);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleManualSubmit(event: FormEvent) {
    event.preventDefault();
    await runManual(manualForm);
  }

  async function runExample() {
    setActiveTab("manual");
    setManualForm(DEMO_DEFAULTS);
    await runManual(DEMO_DEFAULTS);
  }

  async function handleUploadSubmit(event: FormEvent) {
    event.preventDefault();
    resetOutput();
    setIsLoading(true);
    try {
      const formData = new FormData();
      uploadFiles.forEach((file) => formData.append("files", file));
      formData.append("usd_budget", uploadBudget);
      formData.append("usd_flat_rate", usdFlatRate);
      formData.append("include_breakdown", "true");
      formData.append("persist_run", "false");
      formData.append("rounding_decimals", "6");

      const response = await fetch(`${API_BASE_URL}/import/excel`, { method: "POST", body: formData });
      const importJson = await response.json();
      const normalized = asRecord(importJson.normalized_request);
      setNormalizedPayload(normalized);
      setImportWarnings(
        Array.isArray(importJson.warnings)
          ? importJson.warnings.filter((item: unknown): item is string => typeof item === "string")
          : [],
      );

      if (response.status >= 400 || importJson.status !== "success" || !normalized) {
        setErrorText(`The workbooks could not be normalized (${response.status}).`);
        setLastResponse(importJson);
        return;
      }

      if (autoRunAfterImport) {
        const valuation = await postJson(`${API_BASE_URL}/run-valuation`, normalized);
        if (valuation.status >= 400) setErrorText(`The normalized valuation failed (${valuation.status}).`);
        setLastResponse(valuation.json);
      }
      window.setTimeout(() => document.querySelector("#results")?.scrollIntoView({ behavior: "smooth" }), 50);
    } catch (error) {
      setErrorText(`Could not complete the Excel flow. ${String(error)}`);
    } finally {
      setIsLoading(false);
    }
  }

  const interpretation = !result || result.npvUsd === null || result.pvUsdTotal === null
    ? null
    : result.npvUsd >= 0
      ? `The estimated hedged cash-flow value is ${formatNumber(result.npvUsd)} USD above the initial budget.`
      : `The estimated hedged cash-flow value is ${formatNumber(Math.abs(result.npvUsd))} USD below the initial budget.`;

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="BondFX home">
          <img src="/images/bondfx-logo.png" alt="" />
          <span>BondFX</span>
        </a>
        <nav aria-label="Project links">
          <a href="#workspace">Demo</a>
          <a href="#method">Method</a>
          <a href="https://github.com/Laimon99/tool-bond" target="_blank" rel="noreferrer">GitHub ↗</a>
        </nav>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow">Explainable fixed-income engineering</p>
          <h1>From TRY bond cash flows to an auditable USD valuation.</h1>
          <p className="lede">Explore how a bond purchase, a USDTRY forward curve and USD discount factors combine into one transparent NPV.</p>
          <div className="hero-actions">
            <button className="button primary" type="button" onClick={runExample} disabled={isLoading}>{isLoading ? "Calculating…" : "Run the example"}</button>
            <a className="button secondary" href="#method">See the method</a>
          </div>
          <p className="microcopy">Synthetic inputs · No sign-up · {IS_PUBLIC_DEMO ? "Results are not persisted" : "Results are not persisted by default"}</p>
        </div>
        <aside className="hero-card" aria-label="Valuation workflow summary">
          <p className="card-kicker">One contract, two input paths</p>
          <div className="flow-line"><span>01</span><div><strong>Normalize</strong><small>Guided form or Excel</small></div></div>
          <div className="flow-line"><span>02</span><div><strong>Value</strong><small>Cash flows, FX forwards, discounting</small></div></div>
          <div className="flow-line"><span>03</span><div><strong>Explain</strong><small>Assumptions and row-level audit trail</small></div></div>
        </aside>
      </section>

      <div className="disclaimer" role="note"><strong>Educational model.</strong> Not investment advice, an executable quote or a production pricing library.</div>

      <section className="method" id="method">
        <div><span>1</span><h2>Size the purchase</h2><p>Convert the USD budget to TRY, then derive units from the bond dirty price.</p></div>
        <div><span>2</span><h2>Translate cash flows</h2><p>Convert every TRY payment using the selected forward side and interpolation.</p></div>
        <div><span>3</span><h2>Discount to USD</h2><p>Apply USD discount factors and compare present value with the initial budget.</p></div>
      </section>

      <section className="workspace" id="workspace">
        <div className="section-heading"><div><p className="eyebrow">Interactive demo</p><h2>Build a valuation</h2></div><span className="api-status">API: {API_DISPLAY_URL}</span></div>

        <div className="tabs" role="tablist" aria-label="Input method">
          <button role="tab" aria-selected={activeTab === "manual"} className={activeTab === "manual" ? "active" : ""} onClick={() => switchTab("manual")} type="button">Guided inputs</button>
          <button role="tab" aria-selected={activeTab === "upload"} className={activeTab === "upload" ? "active" : ""} onClick={() => switchTab("upload")} type="button">Excel import</button>
        </div>

        {activeTab === "manual" ? (
          <form onSubmit={handleManualSubmit} className="form-panel">
            <div className="form-intro"><h3>Core scenario</h3><p>The demo is pre-filled with synthetic values. Change any field or run it as-is.{IS_PUBLIC_DEMO ? " The free API may need up to about a minute to wake after inactivity." : ""}</p></div>
            <div className="input-grid four">
              <InputField label="USD budget"><input type="number" min="0.01" step="any" value={manualForm.usdBudget} onChange={(e) => updateManual("usdBudget", e.target.value)} /></InputField>
              <InputField label="Spot USDTRY" hint="TRY per USD"><input type="number" min="0.01" step="any" value={manualForm.spotUsdTry} onChange={(e) => updateManual("spotUsdTry", e.target.value)} /></InputField>
              <InputField label="Settlement date"><input type="date" value={manualForm.settlementDate} onChange={(e) => updateManual("settlementDate", e.target.value)} /></InputField>
              <InputField label="Price input"><div className="joined-input"><select value={manualForm.priceType} onChange={(e) => updateManual("priceType", e.target.value as PriceInputType)}><option value="clean_price">Clean price</option><option value="ytm">Yield</option></select><input aria-label="Price value" type="number" min="0" step="any" value={manualForm.priceValue} onChange={(e) => updateManual("priceValue", e.target.value)} /></div></InputField>
            </div>

            <details className="advanced">
              <summary><span>Advanced model inputs</span><small>Bond schedule, curves and execution assumptions</small></summary>
              <div className="advanced-body">
                <h4>Bond definition</h4>
                <div className="input-grid four">
                  <InputField label="Annual coupon" hint="Decimal, e.g. 0.275"><input type="number" min="0" step="any" value={manualForm.couponRateAnnual} onChange={(e) => updateManual("couponRateAnnual", e.target.value)} /></InputField>
                  <InputField label="Coupons per year"><select value={manualForm.couponFrequency} onChange={(e) => updateManual("couponFrequency", e.target.value)}><option value="1">Annual</option><option value="2">Semi-annual</option><option value="4">Quarterly</option></select></InputField>
                  <InputField label="Face value per unit"><input type="number" min="0.01" step="any" value={manualForm.faceValuePerUnit} onChange={(e) => updateManual("faceValuePerUnit", e.target.value)} /></InputField>
                  <InputField label="Day count"><input value="ACT/365F" disabled /></InputField>
                  <InputField label="Issue date"><input type="date" value={manualForm.issueDate} onChange={(e) => updateManual("issueDate", e.target.value)} /></InputField>
                  <InputField label="Maturity date"><input type="date" value={manualForm.maturityDate} onChange={(e) => updateManual("maturityDate", e.target.value)} /></InputField>
                </div>
                <InputField label="Coupon dates" hint="One ISO date per line"><textarea rows={5} value={manualForm.scheduleDatesText} onChange={(e) => updateManual("scheduleDatesText", e.target.value)} /></InputField>
                <div className="curve-grid">
                  <InputField label="USD discount factors" hint="YYYY-MM-DD,df"><textarea rows={5} value={manualForm.dfPointsText} onChange={(e) => updateManual("dfPointsText", e.target.value)} /></InputField>
                  <InputField label="USDTRY forward pillars" hint="YYYY-MM-DD,bid,ask"><textarea rows={5} value={manualForm.fxPillarsText} onChange={(e) => updateManual("fxPillarsText", e.target.value)} /></InputField>
                </div>
                <h4>Execution and output</h4>
                <div className="input-grid four">
                  <InputField label="FX interpolation"><select value={manualForm.fxInterpolation} onChange={(e) => updateManual("fxInterpolation", e.target.value as InterpolationMode)}><option value="linear">Linear</option><option value="loglinear">Log-linear</option></select></InputField>
                  <InputField label="FX rate side"><select value={manualForm.fxRateSide} onChange={(e) => updateManual("fxRateSide", e.target.value as FxRateSide)}><option value="ask">Ask</option><option value="mid">Mid</option><option value="bid">Bid</option></select></InputField>
                  <InputField label="Rounding decimals"><input type="number" min="0" max="8" step="1" value={manualForm.roundingDecimals} onChange={(e) => updateManual("roundingDecimals", e.target.value)} /></InputField>
                  <InputField label="Request ID"><input type="text" value={manualForm.requestId} onChange={(e) => updateManual("requestId", e.target.value)} /></InputField>
                </div>
                <div className="check-row">
                  <label><input type="checkbox" checked={manualForm.includeBreakdown} onChange={(e) => updateManual("includeBreakdown", e.target.checked)} /> Include cash-flow breakdown</label>
                  <label><input type="checkbox" checked={manualForm.persistRun} disabled={IS_PUBLIC_DEMO} onChange={(e) => updateManual("persistRun", e.target.checked)} /> {IS_PUBLIC_DEMO ? "Persistence disabled in public demo" : "Persist this run locally"}</label>
                </div>
              </div>
            </details>

            <button className="button primary submit" type="submit" disabled={isLoading}>{isLoading ? "Calculating…" : "Run valuation"}</button>
          </form>
        ) : (
          <form onSubmit={handleUploadSubmit} className="form-panel upload-panel">
            <div className="form-intro"><h3>Reproduce the Excel workflow</h3><p>Download the three synthetic workbooks, then select them together. No client or live market data is included.</p></div>
            <div className="downloads">
              <a href="/demo-data/Curve_swap.xlsx" download><span>FX curve</span><strong>Curve_swap.xlsx</strong></a>
              <a href="/demo-data/bond_storico.xlsx" download><span>Bond history</span><strong>bond_storico.xlsx</strong></a>
              <a href="/demo-data/Bond_tURCO.xlsx" download><span>Yield input</span><strong>Bond_tURCO.xlsx</strong></a>
            </div>
            <InputField label="Select the three workbooks" hint="Accepted formats: .xlsx and .xlsm; up to 10 MB each"><input type="file" accept=".xlsx,.xlsm" multiple onChange={(e) => setUploadFiles(Array.from(e.target.files || []))} /></InputField>
            <div className="input-grid two">
              <InputField label="USD budget"><input type="number" min="0.01" step="any" value={uploadBudget} onChange={(e) => setUploadBudget(e.target.value)} /></InputField>
              <InputField label="Flat USD rate" hint="Used to synthesize discount factors"><input type="number" min="0" step="any" value={usdFlatRate} onChange={(e) => setUsdFlatRate(e.target.value)} /></InputField>
            </div>
            <label className="single-check"><input type="checkbox" checked={autoRunAfterImport} onChange={(e) => setAutoRunAfterImport(e.target.checked)} /> Run valuation immediately after normalization</label>
            <button className="button primary submit" type="submit" disabled={isLoading || !canUpload}>{isLoading ? "Processing…" : "Normalize and value"}</button>
          </form>
        )}

        {(errorText || validationErrors.length > 0) && <div className="callout error-box" role="alert"><strong>Check the input</strong>{errorText && <p>{errorText}</p>}{validationErrors.length > 0 && <ul>{validationErrors.map((item) => <li key={item}>{item}</li>)}</ul>}</div>}
      </section>

      <section className="results" id="results" aria-live="polite">
        <div className="section-heading"><div><p className="eyebrow">Model output</p><h2>Valuation result</h2></div>{result && <span className={`status ${result.status}`}>{result.status}</span>}</div>

        {!result && !importSummary ? (
          <div className="empty-state"><span>∿</span><h3>Ready when you are</h3><p>Run the pre-filled example or import the synthetic workbooks to see a complete audit trail.</p></div>
        ) : (
          <>
            {interpretation && <div className={`interpretation ${(result?.npvUsd || 0) >= 0 ? "positive" : "negative"}`}><span>What this means</span><strong>{interpretation}</strong><p>NPV = present value of hedged USD cash flows minus the initial USD budget.</p></div>}
            {result?.status === "success" && (
              <>
                <div className="metric-grid">
                  <div className="metric featured"><span>NPV</span><strong>{formatNumber(result.npvUsd)}</strong><small>USD</small></div>
                  <div className="metric"><span>Present value</span><strong>{formatNumber(result.pvUsdTotal)}</strong><small>USD</small></div>
                  <div className="metric"><span>Invested notional</span><strong>{formatNumber(result.notionalTry)}</strong><small>TRY</small></div>
                  <div className="metric"><span>Bond units</span><strong>{formatNumber(result.units, 4)}</strong><small>units</small></div>
                </div>
                {result.breakdownRows.length > 0 && <div className="result-block"><div className="block-heading"><h3>Cash-flow audit trail</h3><span>{result.breakdownRows.length} future payments</span></div><div className="table-wrap"><table><thead><tr><th>Date</th><th>TRY cash flow</th><th>USDTRY rate</th><th>Side</th><th>USD cash flow</th><th>USD DF</th><th>PV USD</th></tr></thead><tbody>{result.breakdownRows.map((row, index) => <tr key={`${row.date}-${index}`}><td>{row.date}</td><td>{formatNumber(row.tryCashflow)}</td><td>{formatNumber(row.fxRate, 4)}</td><td>{row.fxRateSide}</td><td>{formatNumber(row.usdCashflow)}</td><td>{formatNumber(row.usdDf, 6)}</td><td>{formatNumber(row.pvUsd)}</td></tr>)}</tbody></table></div></div>}
                <div className="assumption-grid"><div><span>Dirty price</span><strong>{formatNumber(result.dirtyPricePercent, 4)}%</strong></div>{Object.entries(result.assumptions).map(([key, value]) => <div key={key}><span>{key.replaceAll("_", " ")}</span><strong>{String(value)}</strong></div>)}</div>
              </>
            )}
            {importSummary && <div className="import-summary"><strong>Normalized Excel input</strong><span>Settlement {importSummary.settlementDate}</span><span>Budget {formatNumber(importSummary.usdBudget)} USD</span><span>Spot {formatNumber(importSummary.spotUsdTry, 4)}</span><span>{importSummary.fxPillarsCount} FX pillars</span><span>{importSummary.dfPointsCount} discount points</span><span>{importSummary.priceType}: {formatNumber(importSummary.priceValue, 6)}</span></div>}
            {[...importWarnings, ...(result?.warnings || [])].length > 0 && <div className="callout warning"><strong>Model notices</strong><ul>{[...new Set([...importWarnings, ...(result?.warnings || [])])].map((item) => <li key={item}>{item}</li>)}</ul></div>}
            {result && result.errors.length > 0 && <div className="callout error-box"><strong>API errors</strong><ul>{result.errors.map((item, index) => <li key={`${item.code}-${index}`}>{item.code}: {item.message}{item.field ? ` [${item.field}]` : ""}</li>)}</ul></div>}
          </>
        )}

        <details className="technical" open={showTechnicalDetails} onToggle={(e) => setShowTechnicalDetails(e.currentTarget.open)}>
          <summary>Technical JSON and endpoint</summary><p>API endpoint: {API_DISPLAY_URL}</p>
          <h3>Normalized request</h3><pre>{normalizedPayload ? JSON.stringify(normalizedPayload, null, 2) : "Available after an Excel import."}</pre>
          <h3>Latest response</h3><pre>{lastResponse ? JSON.stringify(lastResponse, null, 2) : "Available after a run."}</pre>
        </details>
      </section>

      <footer><div><img src="/images/bondfx-logo.png" alt="" /><strong>BondFX</strong></div><p>Transparent finance engineering, built as a public educational proof of concept.</p><a href="https://github.com/Laimon99/tool-bond" target="_blank" rel="noreferrer">View source on GitHub ↗</a></footer>
    </main>
  );
}
