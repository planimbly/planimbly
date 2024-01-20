const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    experimentalStudio: true,
    baseUrl: 'http://localhost:8000',
    setupNodeEvents(on, config) {
      
    },
  },
});