import { delay, waitAndClick } from "../helpers/browser.js";

async function login(page) {
  try {
    // Navigate to the login page
    await page.goto(
      "https://evo5.w12app.com.br/#/acesso/panobiancos/autenticacao"
    );

    // Wait for the login form to be loaded
    await delay(1000);
    await waitAndClick(page, "#usuario");

    // Fill in the login credentials
    await page.type("#usuario", "gui.olhenrique@gmail.com", { delay: 20 });

    await waitAndClick(page, "#senha");
    await page.type("#senha", "dbt8rzu3RKP2fyd-aqd", { delay: 20 });

    // Click the login button
    await waitAndClick(page, 'button[type="submit"]');

    // Wait for navigation after login
    await page.waitForNavigation();

    console.log("Login successful!");
    return true;
  } catch (error) {
    console.error("Login failed:", error);
    return false;
  }
}

export { login };
