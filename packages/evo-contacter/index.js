import dotenv from "dotenv";

// Load environment variables first, before any other imports
dotenv.config();

import { launchEvoBrowser, loginToEvo, delay } from "evo-puppeteer";
import { getIdsBasedOnEnvironment } from "./helpers/environmentHelper.js";
import {
  getAlreadyCommunicatedIds,
  getIdsToCommunicate,
  removeCommunicatedIdsFile,
} from "./helpers/fileManager.js";
import { sendEmailToContact } from "./modules/contactProcessor.js";

const allIds = getIdsBasedOnEnvironment();

async function main() {
  const alreadyCommunicatedIds = getAlreadyCommunicatedIds();
  const ids = getIdsToCommunicate(allIds, alreadyCommunicatedIds);

  let browser;
  try {
    // Launch the browser using the generic package
    const setup = await launchEvoBrowser();
    browser = setup.browser;
    const page = setup.page;

    // Perform login using the generic package
    const loginSuccess = await loginToEvo(page);
    if (!loginSuccess) {
      throw new Error("Login failed");
    }

    // Process each ID for email sending
    for (const id of ids) {
      const success = await sendEmailToContact(page, id);
      if (!success) {
        throw new Error(`Failed to send email for ID ${id}`);
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
    if (browser) await browser.close();
  }
}

// Run the main function
main();
