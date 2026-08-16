import fs from 'node:fs/promises';import path from 'node:path';import { fileURLToPath } from 'node:url';
const packageJson=fileURLToPath(new URL('../package.json',import.meta.url));const installRoot=path.dirname(packageJson);const cliPath=fileURLToPath(new URL('./cli.mjs',import.meta.url));
export async function getRunnerInfo(){const pkg=JSON.parse(await fs.readFile(packageJson,'utf8'));return{version:String(pkg.version),runnerVersion:String(pkg.version),cliPath,installRoot,packageJson,node:process.version};}
