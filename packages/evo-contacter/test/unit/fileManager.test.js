import { describe, expect, it } from "vitest";
import { getIdsToCommunicate } from "../../helpers/fileManager.js";

describe("File Manager Unit Tests", () => {
  describe("getIdsToCommunicate", () => {
    it("should return all IDs when no already communicated IDs", () => {
      const allIds = ["123", "456", "789"];
      const alreadyCommunicatedIds = [];

      const result = getIdsToCommunicate(allIds, alreadyCommunicatedIds);

      expect(result).toEqual(allIds);
    });

    it("should filter out already communicated IDs", () => {
      const allIds = ["123", "456", "789", "101"];
      const alreadyCommunicatedIds = ["123", "789"];

      const result = getIdsToCommunicate(allIds, alreadyCommunicatedIds);

      expect(result).toEqual(["456", "101"]);
    });

    it("should handle string/number ID comparisons", () => {
      const allIds = [123, 456, 789];
      const alreadyCommunicatedIds = ["123", "456"];

      const result = getIdsToCommunicate(allIds, alreadyCommunicatedIds);

      expect(result).toEqual([789]);
    });

    it("should return empty array when all IDs are already communicated", () => {
      const allIds = ["123", "456"];
      const alreadyCommunicatedIds = ["123", "456", "789"];

      const result = getIdsToCommunicate(allIds, alreadyCommunicatedIds);

      expect(result).toEqual([]);
    });

    it("should handle empty arrays", () => {
      const result = getIdsToCommunicate([], []);
      expect(result).toEqual([]);
    });

    it("should handle mixed data types", () => {
      const allIds = ["123", 456, "789"];
      const alreadyCommunicatedIds = [123, "456"];

      const result = getIdsToCommunicate(allIds, alreadyCommunicatedIds);

      // The function converts allIds items to String for comparison
      // '123' is not filtered by 123 (number), 456 is filtered by '456' (string)
      expect(result).toEqual(["123", "789"]);
    });
  });
});
