import { delay, waitAndClick } from "../helpers/browser.js";
import {
  addToCommunicatedIds,
  addToNonExistentClients,
  getAlreadyCommunicatedIds,
} from "../helpers/fileManager.js";
import {
  sendEmailMarketing,
  sendEmailMarketingToClient,
} from "./email-marketing.js";
import {
  checkIfItIsClient,
  sendGeneralMessage,
  sendMessageToClient,
} from "./messaging.js";

const IS_DEBUG_ACTIVE = true;

export const CommunicationTypes = Object.freeze({
  EMAIL: "email",
  MESSAGING: "messaging",
});

async function sendMessage(page, id, typeOfCommunication) {
  try {
    console.log(`Processing ID: ${id}`);

    // Verifica se o ID já foi comunicado
    const alreadyCommunicatedIds = getAlreadyCommunicatedIds();
    if (alreadyCommunicatedIds.includes(String(id))) {
      console.log(`Duplicated contact attempt for the ID: ${id}`);
      return true;
    }

    // Search for the contact
    await waitAndClick(page, "#evoAutocomplete");
    await page.type("#evoAutocomplete", id.toString(), { delay: 20 });

    let noResults = false;
    try {
      await page.waitForSelector(".item-lista", { timeout: 5000 });
    } catch (error) {
      noResults = true;
    }

    if (noResults) {
      console.log(`No results found for ID: ${id}`);
      await page.evaluate(() => {
        const closeButton = document.querySelector(".icone-close-cliente");
        if (closeButton) {
          closeButton.click();
        }
      });

      addToNonExistentClients(id);
    } else {
      await waitAndClick(page, ".item-lista");
      await delay(1000);
      await page.waitForSelector(".md-toolbar-tools a");
      const isClient = await checkIfItIsClient(page);

      if (isClient) {
        await (typeOfCommunication === CommunicationTypes.EMAIL
          ? sendEmailMarketingToClient(page, id)
          : sendMessageToClient(page, id));
      } else {
        await (typeOfCommunication === CommunicationTypes.EMAIL
          ? sendEmailMarketing(page, id)
          : sendGeneralMessage(page, id));
      }

      console.log(`Message sent successfully for ID: ${id}`);
    }

    // Escreve o id no arquivo após sucesso
    addToCommunicatedIds(id);
    return true;
  } catch (error) {
    console.error("Failed to send message for ID:", id);

    if (IS_DEBUG_ACTIVE) {
      console.error("Error details:", error, "\n\n");
    }

    return false;
  }
}

export { sendMessage };
