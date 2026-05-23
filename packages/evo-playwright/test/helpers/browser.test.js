import { beforeEach, describe, expect, it, vi } from "vitest";
import { waitAndClick } from "../../helpers/browser.js";

describe("Playwright Browser Helpers", () => {
  describe("waitAndClick", () => {
    let mockPage;

    beforeEach(() => {
      mockPage = {
        click: vi.fn(),
      };
    });

    it("should call click with selector and timeout", async () => {
      mockPage.click.mockResolvedValue();

      await waitAndClick(mockPage, "#test-selector");

      expect(mockPage.click).toHaveBeenCalledWith("#test-selector", {
        timeout: 30000,
      });
    });

    it("should use custom timeout when provided", async () => {
      mockPage.click.mockResolvedValue();

      await waitAndClick(mockPage, "#test-selector", 5000);

      expect(mockPage.click).toHaveBeenCalledWith("#test-selector", {
        timeout: 5000,
      });
    });

    it("should propagate errors from click", async () => {
      const error = new Error("Click failed");
      mockPage.click.mockRejectedValue(error);

      await expect(waitAndClick(mockPage, "#test-selector")).rejects.toThrow(
        "Click failed"
      );
    });
  });
});
