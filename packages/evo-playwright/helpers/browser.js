function delay(time) {
  return new Promise((resolve) => {
    setTimeout(resolve, time);
  });
}

async function waitAndClick(page, selector, timeout = 30000) {
  // Playwright has built-in auto-waiting for selector visibility, stability, and clickability
  await page.click(selector, { timeout });
}

export { delay, waitAndClick };
