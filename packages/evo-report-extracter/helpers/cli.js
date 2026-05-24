/**
 * Parses the report type from command-line arguments.
 * Supports positional arguments, --report=TYPE, -r TYPE, and Nx-style --args=TYPE.
 * 
 * @param {string[]} argv The array of command-line arguments (usually process.argv)
 * @returns {string|null} The parsed report type, or null if not found
 */
export function parseReportType(argv) {
  const args = argv.slice(2);
  let reportType = null;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith("--report=")) {
      reportType = arg.split("=")[1];
    } else if (arg === "--report" || arg === "-r") {
      if (i + 1 < args.length) {
        reportType = args[i + 1];
        i++;
      }
    } else if (arg.startsWith("--args=")) {
      reportType = arg.split("=")[1];
    } else if (arg === "--args") {
      if (i + 1 < args.length) {
        reportType = args[i + 1];
        i++;
      }
    } else if (!arg.startsWith("-")) {
      reportType = arg;
    }
  }

  return reportType ? reportType.trim().toLowerCase() : null;
}
