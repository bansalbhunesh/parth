import { cpSync, existsSync, mkdirSync } from "node:fs";

const standaloneRoot = ".next/standalone";
const staticSource = ".next/static";
const staticTarget = `${standaloneRoot}/.next/static`;

if (!existsSync(`${standaloneRoot}/server.js`)) {
  throw new Error("standalone build is missing; run `npm run build` first");
}

mkdirSync(`${standaloneRoot}/.next`, { recursive: true });
cpSync(staticSource, staticTarget, { recursive: true, force: true });
if (existsSync("public")) {
  cpSync("public", `${standaloneRoot}/public`, { recursive: true, force: true });
}

process.env.HOSTNAME ||= "127.0.0.1";
process.env.PORT ||= "3100";
await import("../.next/standalone/server.js");
