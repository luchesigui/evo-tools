import { beforeEach, describe, expect, it, vi } from "vitest";
import { waitAndClick } from "../../helpers/browser.js";

describe("Browser Helpers", () => {
  describe("waitAndClick", () => {
    let mockPage;

    beforeEach(() => {
      mockPage = {
        waitForSelector: vi.fn(),
        click: vi.fn(),
      };
    });

    it("should wait for selector and then click", async () => {
      mockPage.waitForSelector.mockResolvedValue();
      mockPage.click.mockResolvedValue();

      await waitAndClick(mockPage, "#test-selector");

      expect(mockPage.waitForSelector).toHaveBeenCalledWith("#test-selector", {
        timeout: 30000,
      });
      expect(mockPage.click).toHaveBeenCalledWith("#test-selector");
    });

    it("should use custom timeout when provided", async () => {
      mockPage.waitForSelector.mockResolvedValue();
      mockPage.click.mockResolvedValue();

      await waitAndClick(mockPage, "#test-selector", 5000);

      expect(mockPage.waitForSelector).toHaveBeenCalledWith("#test-selector", {
        timeout: 5000,
      });
    });

    it("should propagate errors from waitForSelector", async () => {
      const error = new Error("Selector not found");
      mockPage.waitForSelector.mockRejectedValue(error);

      await expect(waitAndClick(mockPage, "#test-selector")).rejects.toThrow(
        "Selector not found"
      );
      expect(mockPage.click).not.toHaveBeenCalled();
    });

    it("should propagate errors from click", async () => {
      const error = new Error("Click failed");
      mockPage.waitForSelector.mockResolvedValue();
      mockPage.click.mockRejectedValue(error);

      await expect(waitAndClick(mockPage, "#test-selector")).rejects.toThrow(
        "Click failed"
      );
    });
  });
});
