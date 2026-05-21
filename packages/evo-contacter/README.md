# Evo5 Web Scraper

This is a web scraper built with Puppeteer.js to automate the login process for the Evo5 system.

## Setup

1. Make sure you have Node.js installed on your system
2. Install the dependencies:

```bash
npm install
```

## Running the Script

To run the script, use:

```bash
npm start
```

The script will:

1. Open a Chrome browser window
2. Navigate to the login page
3. Automatically fill in the login credentials
4. Submit the form

## Notes

- The browser window will remain open after login for debugging purposes
- To close the browser automatically, uncomment the `await browser.close();` line in the code
- To run in headless mode (no visible browser), change `headless: false` to `headless: true` in the code
