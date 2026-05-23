import { delay, waitAndClick } from "../helpers/browser.js";

const MONTHS_PT = [
  "janeiro", "fevereiro", "março", "abril", "maio", "junho",
  "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
];

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

/**
 * Dynamically selects a target date in the Kendo UI datepicker calendar.
 * If the calendar opens in the wrong month, it clicks prev/next buttons until it matches.
 * @param {import("playwright").Frame} frame 
 * @param {string} inputId The ID of the input element (e.g. "dtini", "dtfim")
 * @param {Date} targetDate The date to select
 * @param {number} delayMs Delay between steps to allow transition animations
 */
async function selectDateInKendo(frame, inputId, targetDate, delayMs = 1000) {
  // Wait for the input selector
  await frame.waitForSelector(`#${inputId}`);
  
  // Click the k-select trigger button of the datepicker
  await frame.evaluate((id) => {
    const input = document.getElementById(id);
    const parent = input.closest(".k-datepicker");
    const trigger = parent ? parent.querySelector(".k-select") : input.nextElementSibling;
    if (trigger) trigger.click();
    else input.click();
  }, inputId);
  
  await delay(delayMs);
  
  const dateviewId = `#${inputId}_dateview`;
  await frame.waitForSelector(dateviewId);
  
  const targetMonthName = MONTHS_PT[targetDate.getMonth()];
  const targetYear = targetDate.getFullYear();
  const targetDay = targetDate.getDate().toString();
  
  let attempts = 0;
  while (attempts < 12) {
    const headerInfo = await frame.evaluate((dvId) => {
      const dv = document.querySelector(dvId);
      const navFast = dv ? dv.querySelector(".k-nav-fast") : null;
      return navFast ? navFast.innerText.toLowerCase() : "";
    }, dateviewId);
    
    if (headerInfo.includes(targetMonthName) && headerInfo.includes(targetYear.toString())) {
      break;
    }
    
    // Parse current month and year from header (e.g. "abril 2026")
    const match = headerInfo.match(/([a-zç]+)\s+(\d{4})/);
    if (match) {
      const currentMonthName = match[1];
      const currentYear = parseInt(match[2], 10);
      const currentMonthIdx = MONTHS_PT.indexOf(currentMonthName);
      
      const currentMonthDate = new Date(currentYear, currentMonthIdx, 1);
      const targetMonthDate = new Date(targetYear, targetDate.getMonth(), 1);
      
      if (targetMonthDate > currentMonthDate) {
        // Target is in the future, click next
        await frame.evaluate((dvId) => {
          const dv = document.querySelector(dvId);
          const nextBtn = dv ? dv.querySelector(".k-nav-next") : null;
          if (nextBtn) nextBtn.click();
        }, dateviewId);
      } else {
        // Target is in the past, click prev
        await frame.evaluate((dvId) => {
          const dv = document.querySelector(dvId);
          const prevBtn = dv ? dv.querySelector(".k-nav-prev") : null;
          if (prevBtn) prevBtn.click();
        }, dateviewId);
      }
    } else {
      // Fallback
      await frame.evaluate((dvId) => {
        const dv = document.querySelector(dvId);
        const nextBtn = dv ? dv.querySelector(".k-nav-next") : null;
        if (nextBtn) nextBtn.click();
      }, dateviewId);
    }
    
    await delay(delayMs);
    attempts++;
  }
  
  // Select the day cell
  const clickedDay = await frame.evaluate(({ dvId, dayStr }) => {
    const dv = document.querySelector(dvId);
    if (!dv) return false;
    
    const cells = Array.from(dv.querySelectorAll("td"));
    const targetCell = cells.find(cell => {
      return cell.innerText.trim() === dayStr && !cell.classList.contains("k-other-month");
    });
    
    if (targetCell) {
      const link = targetCell.querySelector("a");
      if (link) link.click();
      else targetCell.click();
      return true;
    }
    return false;
  }, { dvId: dateviewId, dayStr: targetDay });
  
  if (!clickedDay) {
    throw new Error(`Could not click on day cell ${targetDay} in calendar popup #${inputId}_dateview`);
  }
  
  await delay(500);
}

/**
 * Unchecks the "Contabilizar especiais" checkbox in the frame.
 * @param {import("playwright").Frame} frame 
 */
async function uncheckEspeciais(frame) {
  const result = await frame.evaluate(() => {
    const checkbox = document.getElementById("especiais");
    if (checkbox) {
      if (checkbox.checked) {
        checkbox.click();
        return "unchecked";
      }
      return "already unchecked";
    }
    return "not found";
  });

  if (result === "not found") {
    throw new Error("Could not find '#especiais' checkbox element");
  }
}

/**
 * Clicks the magnifying glass search button.
 * @param {import("playwright").Frame} frame 
 */
async function triggerSearch(frame) {
  const selector = "#btnPesquisar";
  await frame.waitForSelector(selector);
  await frame.click(selector);
}

/**
 * Clicks the "Exportar" button to download spreadsheet.
 * @param {import("playwright").Frame} frame 
 */
async function triggerExport(frame) {
  const selector = "button.k-grid-excel";
  await frame.waitForSelector(selector);
  await frame.click(selector);
}

export {
  navigateToOpportunities,
  selectDateInKendo,
  uncheckEspeciais,
  triggerSearch,
  triggerExport,
};
