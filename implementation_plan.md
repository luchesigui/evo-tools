# Implementation Plan: Evo Tools - Extraction and Upload

Implement the report runner modification and the upload CLI script in the `evo-tools` monorepo.

## Proposed Changes

### 1. Update Conversion Report Extractor:
- File: `packages/evo-report-extracter/reports/conversion/index.js`
- Modify the `run` function to return the downloaded file path (`filePath`) when successful.

### 2. New CLI script for extraction and upload:
- File: `packages/evo-report-extracter/extract-and-upload.js`
- The script should:
  - Extract the previous week range using `getLastWeekRange()`.
  - Calculate the Wednesday of the week to determine:
    - Target month (`YYYY-MM-01`).
    - Week index (0 to 4) of that Wednesday in the target month (S1 to S5).
  - Run the specified report extraction (e.g. `conversion`) to download the report Excel file.
  - Send a POST request to `${DASHBOARD_URL}/api/parse/${reportType}` with:
    - Query parameters: `save=true`, `gym`, `period` (target month), `weekIndex` (if applicable).
    - Header: `Authorization: Bearer ${CRON_SECRET}`.
    - Body: `multipart/form-data` containing the file.
- Accepts command-line parameters or environment variables for `DASHBOARD_URL`, `CRON_SECRET`, `GYM`, `PERIOD`, `WEEK_INDEX`, and `REPORT_TYPE`.

## Verification Plan
- Run the script with test credentials pointing to a local or staging dashboard instance:
  ```bash
  CRON_SECRET=test-secret DASHBOARD_URL=http://localhost:3000 node extract-and-upload.js conversion --gym=panobianco-sjc-satelite
  ```
- Verify the file is correctly generated, the correct week/month are calculated, and the upload succeeds.
