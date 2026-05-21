function delay(time) {
  return new Promise(function (resolve) {
    setTimeout(resolve, time);
  });
}

async function waitAndClick(page, selector, timeout = 30000) {
  await page.waitForSelector(selector, { timeout });
  await page.click(selector);
}

export { delay, waitAndClick };
