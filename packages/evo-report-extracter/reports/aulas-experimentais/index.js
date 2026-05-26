import fs from "fs";
import path from "path";
import {
  launchEvoBrowser,
  loginToEvo,
  navigateToExperimentalClasses,
  getLastWeekRange,
  delay
} from "evo-playwright";

/**
 * Helper to format a Date to YYYY-MM-DD in local time
 * @param {Date} date 
 * @returns {string}
 */
function formatDate(date) {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

/**
 * Executes the Aulas Experimentais report extraction flow.
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
  console.log("Starting Evo Aulas Experimentais Report Extractor");
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

    console.log("Navigating to Aulas Experimentais page...");
    await navigateToExperimentalClasses(page);
    console.log("Aulas Experimentais page navigation done.");

    if (DEBUG) {
      await page.screenshot({ path: path.join(DOWNLOAD_DIR, "debug_1_aulas_exp_page.png") });
    }

    // Set up request / response listeners to intercept the filtered API call
    let apiRequest = null;
    const requestPromise = new Promise((resolve) => {
      page.on("request", (req) => {
        if (req.url().includes("obter-aula-experimental") && req.method() === "POST") {
          try {
            const postData = JSON.parse(req.postData() || "{}");
            if (postData.dataInicioAtividade) {
              apiRequest = req;
              resolve(req);
            }
          } catch (e) {
            // ignore JSON parse errors
          }
        }
      });
    });

    const responsePromise = new Promise((resolve, reject) => {
      page.on("response", async (res) => {
        if (res.url().includes("obter-aula-experimental") && res.request().method() === "POST") {
          try {
            const postData = JSON.parse(res.request().postData() || "{}");
            if (postData.dataInicioAtividade) {
              const json = await res.json();
              resolve(json);
            }
          } catch (err) {
            reject(err);
          }
        }
      });
    });

    // Open the date picker
    const dateBtnSelector = "[data-cy='EFD-DatePickerBTN']";
    await page.waitForSelector(dateBtnSelector, { timeout: 15000 });
    console.log("Opening date picker...");
    await page.click(dateBtnSelector);
    await delay(1500);

    // Click "Semana passada"
    console.log("Selecting 'Semana passada'...");
    const clickedWeek = await page.evaluate(() => {
      const items = Array.from(document.querySelectorAll(".mat-list-item"));
      const targetItem = items.find(item => item.innerText && item.innerText.includes("Semana passada"));
      if (targetItem) {
        targetItem.click();
        return true;
      }
      return false;
    });
    if (!clickedWeek) {
      throw new Error("Could not find or click 'Semana passada' option in date picker menu.");
    }
    await delay(1000);

    if (DEBUG) {
      await page.screenshot({ path: path.join(DOWNLOAD_DIR, "debug_2_week_selected.png") });
    }

    // Click APLICAR
    const applyBtnSelector = "[data-cy='EFD-ApplyButton']";
    await page.waitForSelector(applyBtnSelector, { timeout: 10000 });
    console.log("Clicking APLICAR...");
    await page.click(applyBtnSelector);

    console.log("Waiting for network request and response to resolve...");
    const req = await requestPromise;
    let json = await responsePromise;

    console.log(`Initial response loaded: ${json.resultados.length} rows (total: ${json.totalLinhas}).`);

    // Handle pagination if needed
    if (json.totalLinhas > json.resultados.length) {
      console.log(`Pagination detected. Total lines: ${json.totalLinhas}. Fetching all data...`);
      const allResultsJson = await page.evaluate(async ({ url, headers, postData, total }) => {
        postData.take = total;
        const response = await fetch(url, {
          method: "POST",
          headers: headers,
          body: JSON.stringify(postData)
        });
        return response.json();
      }, {
        url: req.url(),
        headers: req.headers(),
        postData: JSON.parse(req.postData()),
        total: json.totalLinhas
      });
      json = allResultsJson;
      console.log(`Fetched all ${json.resultados.length} rows successfully.`);
    }

    // Map result range to save filename
    const { de, ate } = getLastWeekRange();
    const fromStr = formatDate(de);
    const toStr = formatDate(ate);
    const fileName = `agendamentos-${fromStr}-to-${toStr}.json`;
    const filePath = path.join(DOWNLOAD_DIR, fileName);

    console.log(`Saving report to file: ${fileName}`);
    fs.writeFileSync(filePath, JSON.stringify(json, null, 2));

    const stats = fs.statSync(filePath);
    console.log("-----------------------------------------");
    console.log("Extraction completed successfully!");
    console.log(`File Saved: ${fileName}`);
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
    throw error;
  } finally {
    if (browser) {
      console.log("Closing browser...");
      await browser.close();
    }
  }
}
