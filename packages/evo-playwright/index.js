import { chromium } from "playwright";
import { delay, waitAndClick } from "./helpers/browser.js";
import { loginToEvo } from "./modules/auth.js";
import { checkIfItIsClient, searchContact } from "./modules/search.js";

async function launchEvoBrowser(options = {}) {
  const browser = await chromium.launch({
    headless: true,
    args: ["--start-maximized"],
    timeout: 60000,
    ...options,
  });

  const context = await browser.newContext({
    userAgent:
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    viewport: { width: 1920, height: 1080 }, // Set standard desktop resolution for headless mode stability
  });

  const page = await context.newPage();

  return { browser, context, page };
}

export {
  launchEvoBrowser,
  loginToEvo,
  searchContact,
  checkIfItIsClient,
  delay,
  waitAndClick,
};
