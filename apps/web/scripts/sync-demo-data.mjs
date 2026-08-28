import { copyFile, mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const webDirectory = join(scriptDirectory, "..");
const sourceDirectory = join(webDirectory, "..", "..", "examples", "demo-data");
const publicDirectory = join(webDirectory, "public", "demo-data");
const workbooks = ["Curve_swap.xlsx", "bond_storico.xlsx", "Bond_tURCO.xlsx"];

await mkdir(publicDirectory, { recursive: true });
await Promise.all(
  workbooks.map((name) => copyFile(join(sourceDirectory, name), join(publicDirectory, name))),
);

console.log(`Synced ${workbooks.length} synthetic demo workbooks.`);
