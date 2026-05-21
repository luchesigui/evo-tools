import { delay, waitAndClick } from "../helpers/browser.js";
import { envVariablesShouldExist } from "../helpers/envValidator.js";

envVariablesShouldExist(["EMAIL_TEMPLATE_NAME"]);

const EMAIL_TEMPLATE_NAME = process.env.EMAIL_TEMPLATE_NAME;
const EMAIL_SUBJECT = process.env.EMAIL_SUBJECT;

async function selectEmailMarketingTemplate(page) {
  await waitAndClick(page, "#selecioneTemplateMensagem");

  await page.evaluate(
    ({ emailTemplateName }) => {
      const emailTemplate = [
        ...document.querySelectorAll("mat-option .mat-option-text"),
      ].find((el) => el.innerText.trim() === emailTemplateName);

      console.log(
        [...document.querySelectorAll("mat-option .mat-option-text")].map(
          (el) => el.innerText.trim()
        )
      );

      if (!emailTemplate) {
        throw new Error("Email Marketing Template not found");
      }

      return emailTemplate.click();
    },
    { emailTemplateName: EMAIL_TEMPLATE_NAME }
  );
}

export async function sendEmailMarketing(page, id, isClient) {
  console.log(`Sending e-mail to ${id}`);
  const emailTabId = isClient ? 2 : 3;

  await delay(1000);

  await waitAndClick(
    page,
    `.mat-tab-labels [role=tab]:nth-child(${emailTabId})`
  );
  await waitAndClick(page, ".mat-tab-body-active button");

  await selectEmailMarketingTemplate(page);

  await delay(1000);

  if (EMAIL_SUBJECT) {
    await page.type("#assuntoEmail", EMAIL_SUBJECT);
  }

  await waitAndClick(
    page,
    ".mat-tab-body-active evo-button.m-t-sm.m-l-sm > button"
  );
}

export async function sendEmailMarketingToClient(page, id) {
  await waitAndClick(page, "header nav > ul > li:nth-child(5) > a");
  await delay(1000);
  await sendEmailMarketing(page, id, true);
}
