import { describe, expect, it } from "vitest";
import { calculateWednesdayMetrics, parseArgs } from "../extract-and-upload.js";

describe("extract-and-upload.js", () => {
  describe("calculateWednesdayMetrics", () => {
    it("should calculate correct Wednesday metrics for May 25, 2026", () => {
      // May 25, 2026 is a Monday.
      // Last week Sunday is May 17, 2026.
      // Wednesday of last week is May 20, 2026.
      // Target period is 2026-05-01.
      // 20th of May is third Wednesday (S3).
      const refDate = new Date("2026-05-25T12:00:00Z");
      const metrics = calculateWednesdayMetrics(refDate);
      expect(metrics.period).toBe("2026-05-01");
      expect(metrics.weekIndex).toBe("S3");
    });

    it("should calculate correct Wednesday metrics for June 8, 2026", () => {
      // June 8, 2026 is Monday.
      // Last week Sunday is May 31, 2026.
      // Wednesday is June 3, 2026.
      // Target period is 2026-06-01 (since June 3 is in June, and majority days of week May 31 - June 6 are in June).
      // June 3 is first Wednesday (S1).
      const refDate = new Date("2026-06-08T12:00:00Z");
      const metrics = calculateWednesdayMetrics(refDate);
      expect(metrics.period).toBe("2026-06-01");
      expect(metrics.weekIndex).toBe("S1");
    });

    it("should calculate correct Wednesday metrics for June 4, 2026", () => {
      // June 4, 2026 is Thursday.
      // Last week Sunday is May 24, 2026.
      // Wednesday is May 27, 2026.
      // Target period is 2026-05-01.
      // May 27 is fourth Wednesday (S4).
      const refDate = new Date("2026-06-04T12:00:00Z");
      const metrics = calculateWednesdayMetrics(refDate);
      expect(metrics.period).toBe("2026-05-01");
      expect(metrics.weekIndex).toBe("S4");
    });
  });

  describe("parseArgs", () => {
    it("should parse options correctly from command line arguments", () => {
      const argv = [
        "node",
        "extract-and-upload.js",
        "conversion",
        "--gym",
        "panobianco-sjc-satelite",
        "--dashboard-url",
        "http://localhost:3000",
        "--cron-secret",
        "test-secret",
        "--period",
        "2026-05-01",
        "--week-index",
        "S2"
      ];
      const parsed = parseArgs(argv);
      expect(parsed.reportType).toBe("conversion");
      expect(parsed.gym).toBe("panobianco-sjc-satelite");
      expect(parsed.dashboardUrl).toBe("http://localhost:3000");
      expect(parsed.cronSecret).toBe("test-secret");
      expect(parsed.period).toBe("2026-05-01");
      expect(parsed.weekIndex).toBe("S2");
    });

    it("should parse --gym= and other equal-separated flags", () => {
      const argv = [
        "node",
        "extract-and-upload.js",
        "--report-type=conversion",
        "--gym=panobianco-sjc-satelite",
        "--dashboard-url=http://localhost:3000",
        "--cron-secret=test-secret"
      ];
      const parsed = parseArgs(argv);
      expect(parsed.reportType).toBe("conversion");
      expect(parsed.gym).toBe("panobianco-sjc-satelite");
      expect(parsed.dashboardUrl).toBe("http://localhost:3000");
      expect(parsed.cronSecret).toBe("test-secret");
    });

    it("should fall back to environment variables", () => {
      process.env.DASHBOARD_URL = "http://env-url:3000";
      process.env.CRON_SECRET = "env-secret";
      process.env.GYM = "env-gym";
      process.env.REPORT_TYPE = "conversion";

      const argv = ["node", "extract-and-upload.js"];
      const parsed = parseArgs(argv);

      expect(parsed.reportType).toBe("conversion");
      expect(parsed.gym).toBe("env-gym");
      expect(parsed.dashboardUrl).toBe("http://env-url:3000");
      expect(parsed.cronSecret).toBe("env-secret");

      // Clean up
      delete process.env.DASHBOARD_URL;
      delete process.env.CRON_SECRET;
      delete process.env.GYM;
      delete process.env.REPORT_TYPE;
    });
  });
});
