import { searchContact } from "evo-puppeteer";
import {
  addToCommunicatedIds,
  addToNonExistentClients,
  getAlreadyCommunicatedIds,
} from "../helpers/fileManager.js";
import {
  sendEmailMarketing,
  sendEmailMarketingToClient,
} from "./email-marketing.js";

const IS_DEBUG_ACTIVE = true;

async function sendEmailToContact(page, id) {
  try {
    console.log(`Processing ID: ${id}`);

    // Verifica se o ID já foi comunicado
    const alreadyCommunicatedIds = getAlreadyCommunicatedIds();
    if (alreadyCommunicatedIds.includes(String(id))) {
      console.log(`Duplicated contact attempt for the ID: ${id}`);
      return true;
    }

    // Search and select contact using the generic package
    const { success, isClient } = await searchContact(page, id);

    if (!success) {
      addToNonExistentClients(id);
    } else {
      if (isClient) {
        await sendEmailMarketingToClient(page, id);
      } else {
        await sendEmailMarketing(page, id);
      }
      console.log(`Email sent successfully for ID: ${id}`);
    }

    // Escreve o id no arquivo após sucesso
    addToCommunicatedIds(id);
    return true;
  } catch (error) {
    console.error("Failed to send email for ID:", id);

    if (IS_DEBUG_ACTIVE) {
      console.error("Error details:", error, "\n\n");
    }

    return false;
  }
}

export { sendEmailToContact };
