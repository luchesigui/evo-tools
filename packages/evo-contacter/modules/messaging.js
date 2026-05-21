import { delay, waitAndClick } from "../helpers/browser.js";

const CHATPRO_FLOW_NAME = "Agregadores 1~3 - Jun";

async function checkIfItIsClient(page) {
  await page.waitForSelector(".md-toolbar-tools a");
  const isClient = await page.evaluate(() => {
    return document
      .querySelector(".md-toolbar-tools a")
      .innerText.includes("Cliente");
  });
  return isClient;
}

async function selectChatProFlow(page) {
  await waitAndClick(page, "#fluxoBot");

  await page.evaluate(
    ({ chatProFlowName }) => {
      const chatProFlow = [...document.querySelectorAll("mat-option")].find(
        (el) => el.innerText.toLowerCase() === chatProFlowName.toLowerCase()
      );
      if (!chatProFlow) {
        throw new Error("Chat Pro Flow not found");
      }
      return chatProFlow.click();
    },
    { chatProFlowName: CHATPRO_FLOW_NAME }
  );
}

async function sendGeneralMessage(page, id) {
  console.log(`Sending message to ${id}`);

  await delay(1000);
  const tab = await page.evaluate(() => {
    return document.querySelector("#mat-tab-label-1-4") ? 1 : 3;
  });

  await waitAndClick(page, `#mat-tab-label-${tab}-4`);
  await waitAndClick(page, `#mat-tab-content-${tab}-4 a`);

  await selectChatProFlow(page);

  await waitAndClick(
    page,
    `#mat-tab-content-${tab}-4 evo-button.m-t-sm.m-l-sm > button`
  );
}

async function sendMessageToClient(page, id) {
  await waitAndClick(page, "header nav > ul > li:nth-child(5) > a");
  await delay(1000);
  await sendGeneralMessage(page, id);
}

export { checkIfItIsClient, sendGeneralMessage, sendMessageToClient };
