import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
import { parseReportType } from "./helpers/cli.js";
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

async function main() {
  const reportType = parseReportType(process.argv);

  if (!reportType) {
    console.error("\n[ERROR] Report type parameter is missing.");
    printUsage();
    process.exit(1);
  }

  const runReport = REPORTS[reportType];

  if (!runReport) {
    console.error(`\n[ERROR] Unknown report type: "${reportType}"`);
    printUsage();
    process.exit(1);
  }

  try {
    await runReport();
  } catch (error) {
    // Error is already printed inside the report run function
    process.exit(1);
  }
}

function printUsage() {
  console.log("\nUsage:");
  console.log("  npx nx start evo-report-extracter --args=\"REPORT_TYPE\"");
  console.log("  or");
  console.log("  node index.js REPORT_TYPE");
  console.log("\nAvailable report types:");
  Object.keys(REPORTS).forEach(type => {
    console.log(`  - ${type}`);
  });
  console.log("");
}

main();
