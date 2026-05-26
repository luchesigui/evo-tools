import fs from "fs";
import path from "path";
import {
  launchEvoBrowser,
  loginToEvo,
  navigateToOpportunities,
  selectDateInDatePicker,
  uncheckEspeciais,
  triggerSearch,
  triggerExport,
  delay,
  getLastWeekRange
} from "evo-playwright";

/**
 * Executes the conversion (Opportunities) report extraction flow.
 * @param {Object} options
 * @param {boolean} [options.debug]
 * @param {boolean} [options.headless]
 * @param {string} [options.downloadDir]
 */
export async function run(options = {}) {
  const DEBUG = options.debug ?? process.env.DEBUG === "true";
  const HEADLESS = options.headless ?? process.env.HEADLESS !== "false";
  const DOWNLOAD_DIR = options.downloadDir ?? path.resolve("./downloads");

  if (!fs.existsSync(DOWNLOAD_DIR)) {
    fs.mkdirSync(DOWNLOAD_DIR, { recursive: true });
  }

  console.log("-----------------------------------------");
  console.log("Starting Evo Opportunities (Conversion) Report Extractor");
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

    // Calculate last week range using the shared helper
    const { de, ate } = getLastWeekRange();
    console.log(`Date range to extract: ${de.toLocaleDateString()} to ${ate.toLocaleDateString()}`);

    // Update "De" (dtini) calendar field
    console.log("Setting 'De' date filter...");
    await selectDateInDatePicker(contentFrame, "dtini", de);

    // Update "Até" (dtfim) calendar field
    console.log("Setting 'Até' date filter...");
    await selectDateInDatePicker(contentFrame, "dtfim", ate);

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

    // Click Exportar and wait for Playwright download event
    console.log("Clicking Exportar button...");
    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 60000 }),
      triggerExport(contentFrame),
    ]);

    console.log("Waiting for Excel spreadsheet download to complete...");
    const fileName = download.suggestedFilename();
    const filePath = path.join(DOWNLOAD_DIR, fileName);
    await download.saveAs(filePath);
    const stats = fs.statSync(filePath);
    console.log("-----------------------------------------");
    console.log("Extraction completed successfully!");
    console.log(`Spreadsheet Saved: ${fileName}`);
    console.log(`File Size: ${stats.size} bytes`);
    console.log("-----------------------------------------");
    return filePath;
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
    throw error; // Re-throw to propagate back to entrypoint/runner
  } finally {
    if (browser) {
      console.log("Closing browser...");
      await browser.close();
    }
  }
}
