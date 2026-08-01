"use strict";

const path = require("path");
const { execFileSync } = require("child_process");

const root = path.resolve(__dirname, "..");
execFileSync(process.execPath, [path.join(__dirname, "build_v6_english_manuscript_docx.js")], {
  cwd: root,
  env: { ...process.env, PLANT_CELLFM_EDITION: "v7" },
  stdio: "inherit",
});
