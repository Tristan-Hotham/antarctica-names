// QA: open index.html at desktop and phone widths, log console errors, exercise both maps, take screenshots to qa/.
// Run from the study root with a static server on PORT (default 8802). Leaflet comes from a local npm copy (LEAFLET_DIST).
const { chromium } = require("playwright");
const LF = process.env.LEAFLET_DIST;
(async () => {
  const b = await chromium.launch();
  const errs = [], checks = [];
  const ok = (c, m) => checks.push((c ? "ok   " : "FAIL ") + m);
  for (const [nm, vw, vh] of [["desktop", 1280, 900], ["phone", 390, 844]]) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/googleapis|gstatic|site-nav/, r => r.abort());
    await p.route(/leaflet\.js$/, r => r.fulfill({ path: LF + "/leaflet.js" }));
    await p.route(/leaflet\.css$/, r => r.fulfill({ path: LF + "/leaflet.css" }));
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to load resource/i.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + (process.env.PORT || 8802) + "/index.html", { waitUntil: "load" });
    await p.waitForTimeout(6000);
    await p.screenshot({ path: `qa/${nm}_top.png` });
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(600); await p.locator(sel).screenshot({ path: `qa/${nm}_${f}.png` }); };
    ok(await p.evaluate(() => aReady && wReady), `${nm}: maps ready`);
    await shot("#atlas", "atlas");
    await p.evaluate(() => { const f = F.find(f => f.name === "Queen Maud Land"); pick(f.i, true); }); await p.waitForTimeout(1500);
    ok(await p.locator("#amap .leaflet-popup").count() === 1, `${nm}: feature popup`);
    await shot("#atlas", "pick_qml");
    await p.evaluate(() => { const f = F.find(f => f.name === "Mount Mawson" || f.name === "Mawson Peninsula"); pick(f.i, true); }); await p.waitForTimeout(1500);
    await p.evaluate(() => { const f = F.find(f => f.p >= 0 && PP[f.p].name === "Roald Amundsen"); pick(f.i, true); }); await p.waitForTimeout(1800);
    ok(await p.evaluate(() => S.psel != null && PP[S.psel].name === "Roald Amundsen"), `${nm}: world map follows to Amundsen`);
    await shot("#atlas", "pick_amundsen");
    await p.evaluate(() => { const j = PLACES.findIndex(ps => ps.some(x => x.name === "Ernest Shackleton")); pickPlace(j, true); }); await p.waitForTimeout(2200);
    ok(await p.locator("#wmap .leaflet-popup").count() === 1, `${nm}: birthplace popup`);
    await p.locator("#wmap .leaflet-popup .go").first().click(); await p.waitForTimeout(1500);
    ok(await p.locator("#amap .leaflet-popup").count() === 1, `${nm}: birthplace -> feature`);
    await p.click('#natRow [data-n="3"]'); await p.waitForTimeout(800);
    ok(await p.evaluate(() => S.nat === 3), `${nm}: nation picker`);
    await p.click('#colRow [data-c="kind"]'); await p.waitForTimeout(800);
    await shot("#atlas", "bulgaria_kind");
    await p.click('#natRow .btn:not([data-n])'); await p.click('#colRow [data-c="era"]'); await p.waitForTimeout(800);
    await p.locator("#amap .lyrBtn").click(); await p.waitForTimeout(300);
    await p.locator('#amap .lyrPanel [data-k="claims"]').check(); await p.locator('#amap .lyrPanel [data-k="stations"]').check(); await p.waitForTimeout(600);
    ok(await p.evaluate(() => amap.hasLayer(__layers.claims)), `${nm}: claims layer toggles`);
    await shot("#atlas", "claims_era");
    await p.locator("#amap .lyrBtn").click();
    await p.fill("#q", "shackleton"); await p.waitForTimeout(400);
    ok(await p.locator("#sug li").count() > 0, `${nm}: search suggestions`);
    await p.keyboard.press("Enter"); await p.waitForTimeout(1500);
    ok(await p.evaluate(() => S.sel != null), `${nm}: search picks`);
    for (const c of ["natChart", "claimChart", "decChart", "kindChart", "roleChart", "contChart", "womenChart", "diffTable"]) await shot("#" + c, c);
    ok(await p.locator(".mfs-btn").count() === 2, `${nm}: two full-screen buttons`);
    await p.locator("#atlas").scrollIntoViewIfNeeded();
    await p.locator("#amap .mfs-btn").click(); await p.waitForTimeout(1000);
    ok(await p.evaluate(() => !!document.fullscreenElement || document.getElementById("amap").classList.contains("mfs-fake")), `${nm}: full screen on`);
    await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
    await p.locator("#amap .mfs-btn").click(); await p.waitForTimeout(500);
    if (nm === "phone") { await p.click("#theme"); await p.waitForTimeout(600); await shot("#natChart", "dark_nat"); }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    ok(ov <= 0, `${nm}: horizontal overflow ${ov}px`);
    await p.close();
  }
  console.log(checks.join("\n")); console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
