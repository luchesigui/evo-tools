import { describe, expect, it } from "vitest";
import { delay } from "../../helpers/browser.js";

describe("Integration Tests", () => {
  describe("Basic functionality", () => {
    it("should delay for the specified time", async () => {
      const start = Date.now();
      await delay(50);
      const end = Date.now();

      expect(end - start).toBeGreaterThanOrEqual(45);
      expect(end - start).toBeLessThan(100);
    });

    it("should handle zero delay", async () => {
      const start = Date.now();
      await delay(0);
      const end = Date.now();

      expect(end - start).toBeLessThan(10);
    });
  });
});
