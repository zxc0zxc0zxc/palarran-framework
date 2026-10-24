'use strict';
// Optional existing Playwright only. No installs, profile reuse, raw logs or arbitrary evaluate steps.
const fs = require('node:fs');
const path = require('node:path');
let browser;
process.on('SIGTERM', async () => {
  try { if (browser) await browser.close(); } finally { process.exit(2); }
});
(async () => {
  let result = {status:'INCONCLUSIVE', engine:'chromium', assertions:0};
  let page, request, context, blocked=0, errors=0, launched=false, activeOp;
  try {
    const input = fs.readFileSync(0, 'utf8');
    if (Buffer.byteLength(input)>1048576) throw new Error('packet');
    request=JSON.parse(input);
    const {chromium}=require(request.module);
    const {expect}=require(path.join(path.dirname(request.module),'test.js'));
    browser=await chromium.launch({headless:true, executablePath:request.executable, timeout:request.timeout_ms});
    context=await browser.newContext({viewport:request.step.viewport, serviceWorkers:'block',acceptDownloads:false});
    context.setDefaultTimeout(request.timeout_ms);
    if (typeof context.routeWebSocket!=='function') throw new Error('unsupported_browser_runtime');
    await context.routeWebSocket('**/*', socket => { blocked++; socket.close(); });
    const origin=new URL(request.base_url).origin;
    await context.route('**/*', route => {
      const r=route.request();
      if (new URL(r.url()).origin!==origin || (!request.allow_effects && !['GET','HEAD','OPTIONS'].includes(r.method()))) {
        blocked++; return route.abort();
      }
      return route.continue();
    });
    page=await context.newPage();
    page.on('pageerror',()=>{errors++;});
    page.on('console',msg=>{if(msg.type()==='error') errors++;});
    const locate = l => l.role ? page.getByRole(l.role,{name:l.name,exact:true}) : l.label ? page.getByLabel(l.label,{exact:true}) : page.getByTestId(l.test_id);
    launched=true;
    for (const a of request.step.actions) {
      activeOp=a.op;
      if (a.op==='goto') await page.goto(new URL(a.path,request.base_url).href,{waitUntil:'domcontentloaded'});
      else if (a.op==='fill') await locate(a.locator).fill(a.value);
      else if (a.op==='click') await locate(a.locator).click();
      else if (a.op==='press') await locate(a.locator).press(a.key);
      else if (a.op==='reload') await page.reload({waitUntil:'domcontentloaded'});
      else if (a.op==='expect_text') {await expect(locate(a.locator)).toHaveText(a.value,{timeout:request.timeout_ms});result.assertions++;}
      else if (a.op==='expect_visible') {await expect(locate(a.locator)).toBeVisible({timeout:request.timeout_ms});result.assertions++;}
      else throw new Error('action');
    }
    result.status=errors ? 'FAIL' : blocked ? 'INCONCLUSIVE' : result.assertions>0 ? 'PASS' : 'INCONCLUSIVE';
  } catch (_) { result.status=blocked || !browser?.isConnected() ? 'INCONCLUSIVE' : launched && ['expect_text','expect_visible'].includes(activeOp) ? 'FAIL' : 'INCONCLUSIVE'; }
  finally {
    if (request?.screenshot && page && !page.isClosed()) {
      try {await page.screenshot({path:request.screenshot,fullPage:false,timeout:Math.min(2000,request.timeout_ms)}); fs.chmodSync(request.screenshot,0o600);result.capture='capture.png';} catch (_) {result.status='INCONCLUSIVE';}
    }
    result.blocked_requests=blocked;result.page_errors=errors;
    if (browser) {
      result.browser_version=browser.version();
      try {await browser.close();}catch(_){result.status='INCONCLUSIVE';}
    }
    process.stdout.write(JSON.stringify(result));
    process.exitCode=result.status==='PASS'?0:result.status==='FAIL'?1:2;
  }
})().catch(()=>{process.stdout.write(JSON.stringify({status:'INCONCLUSIVE'}));process.exitCode=2;});
