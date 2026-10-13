// node extract.js index.html out.json  -> evaluates only the data constants of the web app (no DOM code)
const fs = require("fs"), vm = require("vm");
const src = fs.readFileSync(process.argv[2], "utf8");
function block(name) {
  const m = src.match(new RegExp("const\\s+" + name + "\\s*=\\s*([\\[{])"));
  if (!m) return null;
  let i = m.index + m[0].length - 1, depth = 0, str = null, esc = false;
  for (let j = i; j < src.length; j++) {
    const c = src[j];
    if (str) { if (esc) esc = false; else if (c === "\\") esc = true; else if (c === str) str = null; continue; }
    if (c === '"' || c === "'" || c === "`") { str = c; continue; }
    if (c === "/" && src[j + 1] === "/") { j = src.indexOf("\n", j); continue; }
    if (c === "/" && src[j + 1] === "*") { j = src.indexOf("*/", j) + 1; continue; }
    if (c === "[" || c === "{") depth++;
    if (c === "]" || c === "}") { depth--; if (depth === 0) return src.slice(i, j + 1); }
  }
  return null;
}
const out = {};
for (const n of ["TOPICS", "TEST_QUESTIONS", "FLASHCARDS", "REAL_EXAMS", "LEGISLACION_TOPIC_KEYS", "GEOGRAFIA_TOPIC_KEYS",
                 "FECHAS_TOPIC_KEYS", "PREFIJOS_TOPIC_KEYS"]) {
  const b = block(n);
  out[n] = b ? vm.runInNewContext("(" + b + ")", {}, { timeout: 5000 }) : null;
}
fs.writeFileSync(process.argv[3], JSON.stringify(out));
console.log(Object.fromEntries(Object.entries(out).map(([k, v]) => [k, v ? (Array.isArray(v) ? v.length : Object.keys(v).length) : null])));
