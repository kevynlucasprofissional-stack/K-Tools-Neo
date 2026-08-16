import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs/promises';
const pkg=JSON.parse(await fs.readFile(new URL('../package.json',import.meta.url),'utf8'));const cli=await fs.readFile(new URL('../src/cli.mjs',import.meta.url),'utf8');const runner=await fs.readFile(new URL('../src/runner.mjs',import.meta.url),'utf8');const browser=await fs.readFile(new URL('../src/playwright-browser.mjs',import.meta.url),'utf8');const session=await fs.readFile(new URL('../src/browser-session.mjs',import.meta.url),'utf8');const controller=await fs.readFile(new URL('../src/page-controller.mjs',import.meta.url),'utf8');
test('V4.2 package exposes standalone CLI and uses playwright-core without bundled browser',()=>{assert.equal(pkg.bin.xcursos,'./src/cli.mjs');assert.ok(pkg.dependencies['playwright-core']);assert.equal(pkg.dependencies.playwright,undefined);assert.equal(Object.keys(pkg.dependencies).some(x=>/modelcontextprotocol/i.test(x)),false);});
test('V4.2 core has no OpenCode, BrowserClaw or MCP dependency and browser path uses CDP',()=>{assert.doesNotMatch(cli+runner,/OpenCode|BrowserClaw|modelcontextprotocol|DEFAULT_MCP_URL|diagnoseMcp/);assert.match(session,/connectOverCDP/);assert.doesNotMatch(session+browser,/launchPersistentContext/);assert.match(runner,/BrowserSession/);assert.match(runner,/PageController/);assert.doesNotMatch(controller,/connectOverCDP/);});
const installer=await fs.readFile(new URL('../install.ps1',import.meta.url),'utf8');const allScript=await fs.readFile(new URL('../download-all.ps1',import.meta.url),'utf8');
test('Windows installer stages playwright-core without downloading Playwright Chromium and creates xcursos.cmd',()=>{assert.match(installer,/\.install-/);assert.match(installer,/npm install --omit=dev/);assert.match(installer,/playwright-core/);assert.doesNotMatch(installer,/playwright install chromium/);assert.match(installer,/Move-Item \$stage \$app/);assert.match(installer,/xcursos\.cmd/);});

test('V4.2 download-all wrapper keeps JSON stdout separate from progress stderr on Windows PowerShell 5.1',()=>{assert.match(allScript,/MaxPasses/);assert.match(allScript,/xcursos download --json/);assert.match(allScript,/AUDIT_INCOMPLETE/);assert.match(allScript,/AUDIT_UNHEALTHY/);assert.match(allScript,/LESSON_REFRESH_RECOVERY_FAILED/);assert.match(allScript,/PAGE_CLOSED/);assert.doesNotMatch(allScript,/2>&1/);assert.match(allScript,/previousErrorActionPreference/);assert.match(allScript,/\$ErrorActionPreference = 'Continue'/);assert.doesNotMatch(allScript,/manifest\.jsonl.*Remove|Remove-Item.*manifest/i);assert.match(installer,/download-all\.ps1/);assert.match(installer,/xcursos-all\.cmd/);});

test('PowerShell 5.1 compatibility: operational ps1 files are ASCII-only and avoid PS7-only null operators',async()=>{
  for(const name of ['download-all.ps1','install.ps1','uninstall.ps1']){
    const bytes=await fs.readFile(new URL(`../${name}`,import.meta.url));
    assert.equal([...bytes].some(byte=>byte>0x7f),false,`${name} contains non-ASCII bytes`);
    const text=bytes.toString('ascii');
    assert.doesNotMatch(text,/\?\.|\?\?/);
  }
});

test('V4.2 release exposes scheduler/network/recovery/runtime modules in syntax check',()=>{for(const name of ['browser-session','page-controller','network-media-observer','lesson-scheduler','retry-policy','scheduler-checkpoint','runtime-stats','auto-throttle','shutdown-controller','adaptive-locator','debug-snapshots','safe-page-content','redirect-auth-observer'])assert.match(pkg.scripts.check,new RegExp(`src/${name}\\.mjs`),name);});

test('V4.2.5 packages navigation/media-readiness modules and release metadata',async()=>{
  const state=await fs.readFile(new URL('../src/state.mjs',import.meta.url),'utf8');
  assert.equal(pkg.version,'4.2.5');
  assert.match(pkg.scripts.check,/src\/navigation-index\.mjs/);assert.match(pkg.scripts.check,/src\/navigation-planner\.mjs/);assert.match(pkg.scripts.check,/src\/observed-navigation\.mjs/);assert.match(pkg.scripts.check,/src\/version-info\.mjs/);assert.match(pkg.scripts.check,/src\/parser\.mjs/);
  assert.match(state,/lesson-navigation-index\.json/);
  assert.match(installer,/V4\.2\.5/);
  assert.match(runner,/MEDIA_NOT_READY/);
  assert.match(runner,/waitForProvenMedia/);
  assert.match(runner,/cleanStart/);
});
