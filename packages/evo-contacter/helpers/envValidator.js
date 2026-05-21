import dotenv from "dotenv";

dotenv.config();

export function envVariablesShouldExist(variables) {
  const missingVars = [];

  for (const variable of variables) {
    if (!process.env[variable]) {
      missingVars.push(variable);
    }
  }

  if (missingVars.length > 0) {
    throw new Error(
      `Required environment variables are missing: ${missingVars.join(", ")}`
    );
  }
}
