# evo-report-extracter

This package automates logging into the Evo5 platform, navigating to the Opportunities report, filtering by the last week (Sunday to Saturday), and exporting the report to a spreadsheet.

## Requirements

The package depends on `evo-puppeteer` for browser actions.

## Configuration

Configure environment variables in a `.env` file (copied from the root or defined locally):
* `EVO_USER`: The username for Evo5.
* `EVO_PASS`: The password for Evo5.
* `HEADLESS`: `true` (default) or `false` to view the automation.
* `DEBUG`: `true` to save transition screenshots in case of failures and print verbose logs.

## Commands

Run the extraction task using Nx:
```bash
npx nx start evo-report-extracter
```

Or run tests:
```bash
npx nx test evo-report-extracter
```
