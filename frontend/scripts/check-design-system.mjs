import { readdirSync, readFileSync, statSync } from "node:fs";
import { extname, join, relative } from "node:path";

const root = new URL("..", import.meta.url).pathname.replace(/^\/(.:)/, "$1");
const targets = [join(root, "app"), join(root, "components")];
const failures = [];

function walk(directory) {
  for (const name of readdirSync(directory)) {
    const path = join(directory, name);
    if (statSync(path).isDirectory()) {
      walk(path);
      continue;
    }
    const extension = extname(path);
    if (!new Set([".css", ".tsx"]).has(extension)) continue;
    const source = readFileSync(path, "utf8");
    const checks = extension === ".css"
      ? [
          [/(?:#[0-9a-f]{3,8}\b|rgba?\()/i, "raw color; use a semantic OKLCH token"],
          [/border-left\s*:\s*(?:[3-9]|\d{2,})px/i, "prohibited thick status side stripe"],
        ]
      : [[/style\s*=\s*\{\{/i, "inline style; use the design system"]];
    for (const [pattern, message] of checks) {
      if (pattern.test(source)) failures.push(`${relative(root, path)}: ${message}`);
    }
  }
}

for (const target of targets) walk(target);
if (failures.length) {
  console.error(`Design-system checks failed:\n- ${failures.join("\n- ")}`);
  process.exit(1);
}
console.log("Design-system checks passed: semantic colors, complete boundaries, no inline styles.");
