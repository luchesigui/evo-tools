import dotenv from "dotenv";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";
import { getLastWeekRange } from "evo-playwright";
import { run as runConversion } from "./reports/conversion/index.js";
import { run as runAulasExperimentais } from "./reports/aulas-experimentais/index.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from local, root, or evo-playwright .env fallback
dotenv.config();
dotenv.config({ path: path.resolve(__dirname, "../../.env") });
dotenv.config({ path: path.resolve(__dirname, "../evo-playwright/.env") });

const REPORTS = {
  conversion: runConversion,
  "aulas-experimentais": runAulasExperimentais,
};

/**
 * Calculates date range, target period, and week index (S1-S5) using majority-days rule.
 * Wednesday of the week determines the majority month and the week index.
 * 
 * @param {Date} [referenceDate] 
 * @returns {{ de: Date, ate: Date, wednesday: Date, period: string, weekIndex: string }}
 */
export function calculateWednesdayMetrics(referenceDate = new Date()) {
  const { de, ate } = getLastWeekRange(referenceDate);

  // Wednesday is 3 days after Sunday (de)
  const wednesday = new Date(de);
  wednesday.setDate(de.getDate() + 3);

  const year = wednesday.getFullYear();
  const month = String(wednesday.getMonth() + 1).padStart(2, '0');
  const period = `${year}-${month}-01`;

  // Calculate week index of Wednesday in the target month (S1 to S5)
  const dayOfMonth = wednesday.getDate();
  const weekIndexNum = Math.floor((dayOfMonth - 1) / 7);
  const weekIndex = `S${weekIndexNum + 1}`;

  return {
    de,
    ate,
    wednesday,
    period,
    weekIndex,
  };
}

/**
 * Parses arguments from CLI and environment.
 */
export function parseArgs(argv) {
  const args = argv.slice(2);
  const options = {};
  let positional = [];

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith("--gym=")) {
      options.gym = arg.split("=")[1];
    } else if (arg === "--gym") {
      if (i + 1 < args.length) {
        options.gym = args[i + 1];
        i++;
      }
    } else if (arg.startsWith("--dashboard-url=")) {
      options.dashboardUrl = arg.split("=")[1];
    } else if (arg === "--dashboard-url") {
      if (i + 1 < args.length) {
        options.dashboardUrl = args[i + 1];
        i++;
      }
    } else if (arg.startsWith("--cron-secret=")) {
      options.cronSecret = arg.split("=")[1];
    } else if (arg === "--cron-secret") {
      if (i + 1 < args.length) {
        options.cronSecret = args[i + 1];
        i++;
      }
    } else if (arg.startsWith("--period=")) {
      options.period = arg.split("=")[1];
    } else if (arg === "--period") {
      if (i + 1 < args.length) {
        options.period = args[i + 1];
        i++;
      }
    } else if (arg.startsWith("--week-index=")) {
      options.weekIndex = arg.split("=")[1];
    } else if (arg === "--week-index") {
      if (i + 1 < args.length) {
        options.weekIndex = args[i + 1];
        i++;
      }
    } else if (arg.startsWith("--report-type=")) {
      options.reportType = arg.split("=")[1];
    } else if (arg === "--report-type") {
      if (i + 1 < args.length) {
        options.reportType = args[i + 1];
        i++;
      }
    } else if (arg.startsWith("--args=")) {
      options.reportType = arg.split("=")[1];
    } else if (arg === "--args") {
      if (i + 1 < args.length) {
        options.reportType = args[i + 1];
        i++;
      }
    } else if (!arg.startsWith("-")) {
      positional.push(arg);
    }
  }

  const dashboardUrl = options.dashboardUrl || process.env.DASHBOARD_URL;
  const cronSecret = options.cronSecret || process.env.CRON_SECRET;
  const gym = options.gym || process.env.GYM;
  const period = options.period || process.env.PERIOD;
  const weekIndex = options.weekIndex || process.env.WEEK_INDEX;
  const reportType = options.reportType || positional[0] || process.env.REPORT_TYPE;

  return {
    dashboardUrl,
    cronSecret,
    gym,
    period,
    weekIndex,
    reportType: reportType ? reportType.trim().toLowerCase() : null
  };
}

function printUsage() {
  console.log("\nUsage:");
  console.log("  node extract-and-upload.js <report-type> [options]");
  console.log("\nOptions:");
  console.log("  --gym <gym-slug>             Gym slug (e.g. panobianco-sjc-satelite)");
  console.log("  --dashboard-url <url>        Dashboard API URL");
  console.log("  --cron-secret <secret>       Authorization token for dashboard");
  console.log("  --period <YYYY-MM-01>        Target month");
  console.log("  --week-index <S1-S5>         Week index");
  console.log("");
}

async function main() {
  // If this file is executed directly (not imported as a module)
  if (process.argv[1] && fs.realpathSync(process.argv[1]) === fs.realpathSync(fileURLToPath(import.meta.url))) {
    const config = parseArgs(process.argv);

    if (!config.reportType) {
      console.error("[ERROR] Report type is missing.");
      printUsage();
      process.exit(1);
    }

    const runReport = REPORTS[config.reportType];
    if (!runReport) {
      console.error(`[ERROR] Unknown report type: "${config.reportType}"`);
      console.error(`Available report types: ${Object.keys(REPORTS).join(", ")}`);
      process.exit(1);
    }

    if (!config.gym) {
      console.error("[ERROR] Gym name (--gym or GYM env var) is required.");
      process.exit(1);
    }

    if (!config.dashboardUrl) {
      console.error("[ERROR] Dashboard URL (--dashboard-url or DASHBOARD_URL env var) is required.");
      process.exit(1);
    }

    if (!config.cronSecret) {
      console.error("[ERROR] Cron secret (--cron-secret or CRON_SECRET env var) is required.");
      process.exit(1);
    }

    // Calculate metrics using majority-days Wednesday rule
    const metrics = calculateWednesdayMetrics();
    const targetPeriod = config.period || metrics.period;
    
    let targetWeekIndex = config.weekIndex !== undefined ? config.weekIndex : metrics.weekIndex;
    if (targetWeekIndex !== null && targetWeekIndex !== undefined) {
      const numericIndex = Number(targetWeekIndex);
      if (!isNaN(numericIndex) && numericIndex >= 0 && numericIndex <= 4 && String(targetWeekIndex).trim() !== "") {
        targetWeekIndex = `S${numericIndex + 1}`;
      }
    }

    console.log("-----------------------------------------");
    console.log("Extraction & Upload Parameters:");
    console.log(`Report Type:     ${config.reportType}`);
    console.log(`Gym:             ${config.gym}`);
    console.log(`Period:          ${targetPeriod}`);
    console.log(`Week Index:      ${targetWeekIndex}`);
    console.log(`Dashboard URL:   ${config.dashboardUrl}`);
    console.log("-----------------------------------------");

    try {
      console.log(`Running extraction for "${config.reportType}"...`);
      const filePath = await runReport();
      if (!filePath || !fs.existsSync(filePath)) {
        throw new Error(`Report extractor did not return a valid file path: ${filePath}`);
      }

      console.log(`\nPreparing upload of file: ${filePath}`);
      const fileBuffer = fs.readFileSync(filePath);
      const fileBlob = new Blob([fileBuffer]);
      
      const formData = new FormData();
      formData.append("file", fileBlob, path.basename(filePath));

      const url = new URL(`${config.dashboardUrl}/api/parse/${config.reportType}`);
      url.searchParams.append("save", "true");
      url.searchParams.append("gym", config.gym);
      url.searchParams.append("period", targetPeriod);
      if (targetWeekIndex) {
        url.searchParams.append("weekIndex", targetWeekIndex);
      }

      console.log(`Uploading to: ${url.toString()}`);
      const response = await fetch(url.toString(), {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${config.cronSecret}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Upload failed with status ${response.status}: ${errorText}`);
      }

      const responseData = await response.json().catch(() => null) || await response.text();
      console.log("\n-----------------------------------------");
      console.log("Upload completed successfully!");
      console.log("Response:", responseData);
      console.log("-----------------------------------------");

    } catch (error) {
      console.error("\n[ERROR] Execution failed:", error.message);
      process.exit(1);
    }
  }
}

main();
