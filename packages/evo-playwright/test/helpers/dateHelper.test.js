import { describe, expect, it } from "vitest";
import { getLastWeekRange } from "../../helpers/dateHelper.js";

describe("Date Helper", () => {
  describe("getLastWeekRange", () => {
    it("should calculate correct range when current day is a Saturday (e.g. May 23, 2026)", () => {
      // 2026-05-23 is Saturday
      const baseDate = new Date(2026, 4, 23); // month is 0-indexed, so 4 is May
      const { de, ate } = getLastWeekRange(baseDate);

      // Should be previous week Sunday (May 10) to Saturday (May 16)
      expect(de.getFullYear()).toBe(2026);
      expect(de.getMonth()).toBe(4); // May
      expect(de.getDate()).toBe(10);
      expect(de.getHours()).toBe(0);
      expect(de.getMinutes()).toBe(0);

      expect(ate.getFullYear()).toBe(2026);
      expect(ate.getMonth()).toBe(4); // May
      expect(ate.getDate()).toBe(16);
      expect(ate.getHours()).toBe(23);
      expect(ate.getMinutes()).toBe(59);
    });

    it("should calculate correct range when current day is a Sunday (e.g. May 24, 2026)", () => {
      // 2026-05-24 is Sunday
      const baseDate = new Date(2026, 4, 24);
      const { de, ate } = getLastWeekRange(baseDate);

      // Should be previous week Sunday (May 17) to Saturday (May 23)
      expect(de.getFullYear()).toBe(2026);
      expect(de.getMonth()).toBe(4);
      expect(de.getDate()).toBe(17);

      expect(ate.getFullYear()).toBe(2026);
      expect(ate.getMonth()).toBe(4);
      expect(ate.getDate()).toBe(23);
    });

    it("should calculate correct range when spanning across years (e.g. Jan 1, 2026 - Thursday)", () => {
      // 2026-01-01 is Thursday
      const baseDate = new Date(2026, 0, 1);
      const { de, ate } = getLastWeekRange(baseDate);

      // Should be Sunday Dec 21, 2025 to Saturday Dec 27, 2025
      expect(de.getFullYear()).toBe(2025);
      expect(de.getMonth()).toBe(11); // December
      expect(de.getDate()).toBe(21);

      expect(ate.getFullYear()).toBe(2025);
      expect(ate.getMonth()).toBe(11); // December
      expect(ate.getDate()).toBe(27);
    });
  });
});
