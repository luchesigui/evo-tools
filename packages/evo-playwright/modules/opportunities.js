import { delay } from "../helpers/browser.js";

/**
 * Navigates to the Opportunities page from the dashboard
 * by typing "Oportunidade" in the sidebar search and clicking the item under Gerencial.
 * @param {import("playwright").Page} page 
 */
async function navigateToOpportunities(page) {
  const searchSelector = "input[placeholder*='Pesquisar no menu']";
  await page.waitForSelector(searchSelector, { timeout: 15000 });
  await page.locator(searchSelector).pressSequentially("Oportunidade", { delay: 100 });
  await delay(3000);

  const clicked = await page.evaluate(() => {
    const allLi = Array.from(document.querySelectorAll("li"));
    const gerencialLi = allLi.find(li => {
      const a = li.querySelector("a");
      return a && a.innerText && a.innerText.includes("Gerencial");
    });
    if (!gerencialLi) return false;
    const subLink = Array.from(gerencialLi.querySelectorAll("a")).find(a => {
      return a.innerText && a.innerText.trim() === "Oportunidades";
    });
    if (subLink) {
      subLink.click();
      return true;
    }
    return false;
  });

  if (!clicked) {
    throw new Error("Could not click on 'Oportunidades' menu item under 'Gerencial'");
  }

  // Allow navigation to complete
  await delay(7000);
}

export {
  navigateToOpportunities,
};

