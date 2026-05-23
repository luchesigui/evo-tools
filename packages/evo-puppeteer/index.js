import puppeteer from "puppeteer";
import { delay, waitAndClick } from "./helpers/browser.js";
import { loginToEvo } from "./modules/auth.js";
import { checkIfItIsClient, searchContact } from "./modules/search.js";
import {
  navigateToOpportunities,
  selectDateInKendo,
  uncheckEspeciais,
  triggerSearch,
  triggerExport,
} from "./modules/opportunities.js";

async function launchEvoBrowser(options = {}) {
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: null,
    args: ["--start-maximized"],
    timeout: 60000,
    ...options,
  });

  const page = await browser.newPage();
  await page.setUserAgent(
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
  );

  return { browser, page };
}

export {
  launchEvoBrowser,
  loginToEvo,
  searchContact,
  checkIfItIsClient,
  delay,
  waitAndClick,
  navigateToOpportunities,
  selectDateInKendo,
  uncheckEspeciais,
  triggerSearch,
  triggerExport,
};
