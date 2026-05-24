import { describe, expect, it } from "vitest";
import { parseReportType } from "../helpers/cli.js";

describe("CLI Helper", () => {
  describe("parseReportType", () => {
    it("should return null when no arguments are provided", () => {
      const argv = ["node", "index.js"];
      expect(parseReportType(argv)).toBeNull();
    });

    it("should parse positional argument as report type", () => {
      const argv = ["node", "index.js", "conversion"];
      expect(parseReportType(argv)).toBe("conversion");
    });

    it("should parse --report flag", () => {
      const argv = ["node", "index.js", "--report", "conversion"];
      expect(parseReportType(argv)).toBe("conversion");
    });

    it("should parse --report= style flag", () => {
      const argv = ["node", "index.js", "--report=conversion"];
      expect(parseReportType(argv)).toBe("conversion");
    });

    it("should parse -r flag", () => {
      const argv = ["node", "index.js", "-r", "conversion"];
      expect(parseReportType(argv)).toBe("conversion");
    });

    it("should parse Nx --args style flag", () => {
      const argv = ["node", "index.js", "--args", "conversion"];
      expect(parseReportType(argv)).toBe("conversion");
    });

    it("should parse Nx --args= style flag", () => {
      const argv = ["node", "index.js", "--args=conversion"];
      expect(parseReportType(argv)).toBe("conversion");
    });

    it("should normalize report type to lowercase and trimmed", () => {
      const argv = ["node", "index.js", "  Conversion  "];
      expect(parseReportType(argv)).toBe("conversion");
    });
  });
});
