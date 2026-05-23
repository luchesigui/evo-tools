import dotenv from "dotenv";
import fs from "fs";
import path from "path";

import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from local, root, or evo-playwright .env fallback
dotenv.config();
dotenv.config({ path: path.resolve(__dirname, "../../.env") });
dotenv.config({ path: path.resolve(__dirname, "../evo-playwright/.env") });

import {
  launchEvoBrowser,
  loginToEvo,
  navigateToOpportunities,
  selectDateInKendo,
  uncheckEspeciais,
  triggerSearch,
  triggerExport,
  delay
} from "evo-puppeteer";
import { getLastWeekRange } from "./helpers/dateHelper.js";

const DEBUG = process.env.DEBUG === "true";
const HEADLESS = process.env.HEADLESS !== "false";
const DOWNLOAD_DIR = path.resolve("./downloads");

async function main() {
  if (!fs.existsSync(DOWNLOAD_DIR)) {
    fs.mkdirSync(DOWNLOAD_DIR, { recursive: true });
  }

  console.log("-----------------------------------------");
  console.log("Starting Evo Opportunities Report Extractor");
  console.log(`Headless mode: ${HEADLESS}`);
  console.log(`Debug logs/screenshots: ${DEBUG}`);
  console.log(`Download directory: ${DOWNLOAD_DIR}`);
  console.log("-----------------------------------------");

  let browser;
  let page;

  try {
    const setup = await launchEvoBrowser({ headless: HEADLESS });
    browser = setup.browser;
    page = setup.page;

    // Enable console logs forwarding if in debug mode
    if (DEBUG) {
      page.on("console", (msg) => {
        const text = msg.text();
        // Ignore standard noisy vendor/auth logs if they clutter stdout too much
        if (!text.includes("Intercom") && !text.includes("hotjar")) {
          console.log(`[Browser Console] [${msg.type().toUpperCase()}] ${text}`);
        }
      });
    }

    // Configure Chrome DevTools Protocol to allow file downloads in headless mode
    const client = await page.target().createCDPSession();
    await client.send("Page.setDownloadBehavior", {
      behavior: "allow",
      downloadPath: DOWNLOAD_DIR,
    });

    console.log("Logging into Evo5...");
    const loginSuccess = await loginToEvo(page);
    if (!loginSuccess) {
      throw new Error("Evo5 Login failed. Check your EVO_USER and EVO_PASS environment variables.");
    }
    console.log("Login successful.");

    if (DEBUG) {
      await page.screenshot({ path: path.join(DOWNLOAD_DIR, "debug_0_dashboard.png") });
    }

    console.log("Navigating to Opportunities page...");
    await navigateToOpportunities(page);
    console.log("Opportunities page navigation done.");

    if (DEBUG) {
      await page.screenshot({ path: path.join(DOWNLOAD_DIR, "debug_1_oportunidades_page.png") });
    }

    // Target the iframe contentViewport
    const frames = page.frames();
    const contentFrame = frames.find(f => f.name() === "contentViewport" || f.url().includes("evo3.w12app.com.br"));
    if (!contentFrame) {
      throw new Error("Could not find the 'contentViewport' iframe containing the opportunities grid");
    }

    console.log("Found opportunities iframe (contentViewport).");

    // Calculate last week range
    const { de, ate } = getLastWeekRange();
    console.log(`Date range to extract: ${de.toLocaleDateString()} to ${ate.toLocaleDateString()}`);

    // Update "De" (dtini) calendar field
    console.log("Setting 'De' date filter...");
    await selectDateInKendo(contentFrame, "dtini", de);

    // Update "Até" (dtfim) calendar field
    console.log("Setting 'Até' date filter...");
    await selectDateInKendo(contentFrame, "dtfim", ate);

    // Uncheck "Contabilizar especiais"
    console.log("Unchecking 'Contabilizar especiais' checkbox...");
    await uncheckEspeciais(contentFrame);

    if (DEBUG) {
      await page.screenshot({ path: path.join(DOWNLOAD_DIR, "debug_2_filters_applied.png") });
    }

    // Click Search Magnifying Glass
    console.log("Clicking search (lupa) button...");
    await triggerSearch(contentFrame);

    // Wait for the Kendo grid to finish loading and update results
    console.log("Waiting 5 seconds for grid search results to refresh...");
    await delay(5000);

    if (DEBUG) {
      await page.screenshot({ path: path.join(DOWNLOAD_DIR, "debug_3_search_results.png") });
    }

    // Click Exportar
    console.log("Clicking Exportar button...");
    await triggerExport(contentFrame);

    // Wait for download to complete
    console.log("Waiting for Excel spreadsheet download to complete...");
    const timeout = 60000;
    const startTime = Date.now();
    let fileName = null;

    while (Date.now() - startTime < timeout) {
      const files = fs.readdirSync(DOWNLOAD_DIR);
      // Filter out files that are active downloads (.crdownload / .tmp) or debug images
      const activeDownloads = files.filter(f => f.endsWith(".crdownload") || f.endsWith(".tmp"));
      const completedFiles = files.filter(f => f.endsWith(".xlsx") && !f.startsWith("debug_"));

      if (completedFiles.length > 0 && activeDownloads.length === 0) {
        fileName = completedFiles[0];
        break;
      }
      await delay(1000);
    }

    if (!fileName) {
      throw new Error("File download timed out or failed (no Excel file was saved)");
    }

    const filePath = path.join(DOWNLOAD_DIR, fileName);
    const stats = fs.statSync(filePath);
    console.log("-----------------------------------------");
    console.log("Extraction completed successfully!");
    console.log(`Spreadsheet Saved: ${fileName}`);
    console.log(`File Size: ${stats.size} bytes`);
    console.log(`File Path: ${filePath}`);
    console.log("-----------------------------------------");

  } catch (error) {
    console.error("\nFATAL ERROR DURING EXTRACTION:");
    console.error(error.message);

    if (page) {
      try {
        const errorScreenshotPath = path.join(DOWNLOAD_DIR, "error_screenshot.png");
        await page.screenshot({ path: errorScreenshotPath });
        console.log(`Saved failure screenshot to: ${errorScreenshotPath}`);
      } catch (err) {
        console.error("Could not capture failure screenshot:", err.message);
      }
    }
    process.exit(1);
  } finally {
    if (browser) {
      console.log("Closing browser...");
      await browser.close();
    }
  }
}

main();
