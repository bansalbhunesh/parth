import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const entry = path.join(root, "app", "globals.css");
const outputDir = path.join(root, "app", "styles");
const targetLines = 420;
const maxLines = 500;

function sourceText() {
  const entryText = fs.readFileSync(entry, "utf8");
  const imports = [...entryText.matchAll(/^@import "\.\/styles\/(global-\d+\.css)";$/gm)];
  if (!imports.length) return entryText;
  return imports
    .map((match) => fs.readFileSync(path.join(outputDir, match[1]), "utf8").trimEnd())
    .join("\n\n");
}

function splitAtTopLevel(text) {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const chunks = [];
  let depth = 0;
  let start = 0;
  let inComment = false;

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    for (let offset = 0; offset < line.length; offset += 1) {
      if (!inComment && line.slice(offset, offset + 2) === "/*") {
        inComment = true;
        offset += 1;
      } else if (inComment && line.slice(offset, offset + 2) === "*/") {
        inComment = false;
        offset += 1;
      } else if (!inComment && line[offset] === "{") {
        depth += 1;
      } else if (!inComment && line[offset] === "}") {
        depth -= 1;
      }
    }
    if (depth < 0) throw new Error(`Unbalanced closing brace at line ${index + 1}`);
    const length = index - start + 1;
    if (depth === 0 && length >= targetLines) {
      chunks.push(lines.slice(start, index + 1).join("\n").trim());
      start = index + 1;
    }
  }
  if (depth !== 0 || inComment) throw new Error("Unbalanced CSS block or comment");
  if (start < lines.length) chunks.push(lines.slice(start).join("\n").trim());
  return chunks.filter(Boolean);
}

const chunks = splitAtTopLevel(sourceText());
if (chunks.some((chunk) => chunk.split("\n").length > maxLines)) {
  throw new Error(`A generated stylesheet exceeds ${maxLines} lines`);
}

fs.mkdirSync(outputDir, { recursive: true });
chunks.forEach((chunk, index) => {
  const filename = `global-${String(index + 1).padStart(2, "0")}.css`;
  fs.writeFileSync(path.join(outputDir, filename), `${chunk}\n`, "utf8");
});
const imports = chunks
  .map((_chunk, index) => `@import "./styles/global-${String(index + 1).padStart(2, "0")}.css";`)
  .join("\n");
fs.writeFileSync(entry, `${imports}\n`, "utf8");
console.log(`Split global CSS into ${chunks.length} ordered files (max ${maxLines} lines).`);
