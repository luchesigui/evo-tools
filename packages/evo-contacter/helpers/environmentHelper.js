import { envVariablesShouldExist } from "./envValidator.js";
import { getIdsFromExcel } from "./fileManager.js";

export function getIdsBasedOnEnvironment() {
  if (process.env.NODE_ENV?.toLowerCase() === "test") {
    return ["3362769", "2622907"]; // Use the commented version for test environment
  }

  // Require USER_ACCESS_FILE environment variable for production
  envVariablesShouldExist(["USER_ACCESS_FILE"]);
  return getIdsFromExcel(process.env.USER_ACCESS_FILE);
}
