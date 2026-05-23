import { delay, waitAndClick } from "../helpers/browser.js";

async function loginToEvo(page, username, password) {
  const user = username || process.env.EVO_USER;
  const pass = password || process.env.EVO_PASS;

  if (!user || !pass) {
    throw new Error("Evo credentials (EVO_USER / EVO_PASS) must be provided in the environment or as parameters.");
  }

  try {
    // Navigate to the login page
    await page.goto(
      "https://evo5.w12app.com.br/#/acesso/panobiancos/autenticacao"
    );

    // Wait for the login form to be loaded
    await delay(1000);
    
    // Use pressSequentially with delay to trigger Angular's input event listeners correctly
    await waitAndClick(page, "input#usuario");
    await page.locator("input#usuario").pressSequentially(user, { delay: 20 });

    await waitAndClick(page, "input#senha");
    await page.locator("input#senha").pressSequentially(pass, { delay: 20 });

    // Click the login button
    await waitAndClick(page, 'button[type="submit"]');

    // Wait for the dashboard search field to appear (indicates successful login)
    await page.waitForSelector("#evoAutocomplete", { timeout: 30000 });

    console.log("Login successful!");
    return true;
  } catch (error) {
    console.error("Login failed:", error);
    return false;
  }
}

export { loginToEvo };
