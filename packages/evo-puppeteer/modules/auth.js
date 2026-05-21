import { delay, waitAndClick } from "../helpers/browser.js";

async function loginToEvo(page, username, password) {
  const user = username || process.env.EVO_USER || "gui.olhenrique@gmail.com";
  const pass = password || process.env.EVO_PASS || "dbt8rzu3RKP2fyd-aqd";

  try {
    // Navigate to the login page
    await page.goto(
      "https://evo5.w12app.com.br/#/acesso/panobiancos/autenticacao"
    );

    // Wait for the login form to be loaded
    await delay(1000);
    await waitAndClick(page, "#usuario");

    // Fill in the login credentials
    await page.type("#usuario", user, { delay: 20 });

    await waitAndClick(page, "#senha");
    await page.type("#senha", pass, { delay: 20 });

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

export { loginToEvo };
