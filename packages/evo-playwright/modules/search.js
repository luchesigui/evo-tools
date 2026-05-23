import { delay, waitAndClick } from "../helpers/browser.js";

async function checkIfItIsClient(page) {
  await page.waitForSelector(".md-toolbar-tools a");
  const isClient = await page.evaluate(() => {
    return document
      .querySelector(".md-toolbar-tools a")
      .innerText.includes("Cliente");
  });
  return isClient;
}

async function searchContact(page, id) {
  // Search for the contact
  await waitAndClick(page, "#evoAutocomplete");
  // Use pressSequentially to mimic typing so autocomplete dropdown gets triggered
  await page.locator("#evoAutocomplete").pressSequentially(id.toString(), { delay: 20 });

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
    return { success: false, isClient: false };
  }

  await waitAndClick(page, ".item-lista");
  await delay(1000);
  await page.waitForSelector(".md-toolbar-tools a");
  const isClient = await checkIfItIsClient(page);

  return { success: true, isClient };
}

export { checkIfItIsClient, searchContact };
