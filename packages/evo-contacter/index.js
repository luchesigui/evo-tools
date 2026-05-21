import dotenv from "dotenv";

// Load environment variables first, before any other imports
dotenv.config();

import puppeteer from "puppeteer";
import { delay } from "./helpers/browser.js";
import { getIdsBasedOnEnvironment } from "./helpers/environmentHelper.js";
import {
  getAlreadyCommunicatedIds,
  getIdsToCommunicate,
  removeCommunicatedIdsFile,
} from "./helpers/fileManager.js";
import { login } from "./modules/auth.js";
import { CommunicationTypes, sendMessage } from "./modules/contactProcessor.js";

const allIds = getIdsBasedOnEnvironment();
const typeOfCommunication = CommunicationTypes.EMAIL;

async function main() {
  const alreadyCommunicatedIds = getAlreadyCommunicatedIds();
  const ids = getIdsToCommunicate(allIds, alreadyCommunicatedIds);

  let browser;
  try {
    // Launch the browser
    browser = await puppeteer.launch({
      headless: true,
      defaultViewport: null,
      args: ["--start-maximized"],
      timeout: 60000,
    });

    // Create a new page
    const page = await browser.newPage();
    await page.setUserAgent(
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    );

    // Perform login
    const loginSuccess = await login(page);
    if (!loginSuccess) {
      throw new Error("Login failed");
    }

    // Process each ID
    for (const id of ids) {
      const messageSuccess = await sendMessage(page, id, typeOfCommunication);
      if (!messageSuccess) {
        throw new Error(`Failed to send message for ID ${id}`);
      }
      // Add a small delay between processing IDs
      await delay(2000);
    }

    // Se chegou aqui, todos foram bem-sucedidos
    removeCommunicatedIdsFile();
  } catch (error) {
    console.error("An error occurred:", error);

    if (browser) {
      await browser.close();
    }

    await main();
  } finally {
    // Uncomment to close browser when done
    if (browser) await browser.close();
  }
}

// Run the main function
main();
