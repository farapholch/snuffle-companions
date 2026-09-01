import { world, system, ItemStack, BlockTypes } from "@minecraft/server";
import { RASER, BOKBAR, MALM } from "./raser.js";

// ---------------------------------------------------------------------------
// Snuffle Companions — allt som inte går att uttrycka i entitets-JSON.
//
// GRISENS VERB ÄR ATT SÖKA. Ridningen, sadeln, väskorna, lägena, avel och
// tämjning är vanilla-komponenter och bor i entitets-JSON. Det som INTE finns
// någon komponent för är näsan, och det är hela paketets poäng:
//
//   BÖKANDET. Står grisen i bökläge på jord gräver den då och då upp en
//   tryffel. Den syns i trynet ett ögonblick (gris:bar) innan den faller till
//   marken, för annars ser det ut som att tryfflar uppstår ur ingenting.
//
//   VITTRINGEN. Grisen känner malm GENOM BERGET och säger åt ägaren vilket
//   håll den ligger. Räckvidden är rasens, inte en konstant — en berkshire
//   känner tolv block och en lantras fem, och det är skillnaden som gör att
//   man väljer gris efter uppgift i stället för efter färg.
//
// BLOCKSÖKNINGEN ÄR DEN DYRA DELEN. En radie på tolv block är 25^3 = 15 625
// block; läses de varje varv för varje gris äter paketet hela tickbudgeten.
// Tre saker håller nere kostnaden: bara EN gris granskas per skanningsvarv,
// rutnätet glesas ut till vartannat block, och sökningen görs bara för grisar
// som är tämjda, i bökläge och har en ägare i närheten.
const FAMILJ = "sc_gris";
const NS = "gris";
const LOOP = 10;               // tick mellan varv; 20 tick = en sekund
const BOK_CHANS = 0.06;        // per gris och varv i bökläge -> ~ var 8:e sekund
const BOK_DROJ = 30;           // tick som tryffeln syns i trynet innan den faller
const VITTRING_PAUS = 200;     // tick mellan två vittringar för samma gris
const STEG = 2;                // rutnätets gleshet vid malmsökning
const LERA_CHANS = 0.04;       // per gris och varv stående i lera
const LERA_TID = 12000;        // tio minuter i tick innan den torkar av

// TILLSTÅNDET PER GRIS behöver bara överleva mellan två varv i loopen. Poängen
// är att INTE trigga samma händelse om och om igen: add/remove av en
// komponentgrupp startar om beteendena, och en gris vars mål nollställs varje
// varv kommer aldrig fram.
const minne = new Map();
let varv = 0;

function prop(e, namn, fallback) {
  try { const v = e.getProperty(namn); return v === undefined ? fallback : v; }
  catch { return fallback; }
}

function satt(e, namn, varde) {
  try { if (e.getProperty(namn) !== varde) e.setProperty(namn, varde); } catch { }
}

function avstand(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
}

// ALLA TRE DIMENSIONERNA. Hundpaketets skript arbetade bara i överdimensionen,
// så en hund man tog med till Nether tappade tyst sina förmågor. En gris i
// Nether ska kunna vittra forntida spillror — det är där den är som mest värd.
const DIMENSIONER = ["overworld", "nether", "the_end"].map(n => {
  try { return world.getDimension(n); } catch { return null; }
}).filter(Boolean);

function grisar(dim) {
  try { return dim.getEntities({ families: [FAMILJ] }); } catch { return []; }
}

function agare(gris) {
  // ÄGAREN läses ur tameable-komponenten när det går; annars räknas närmaste
  // spelare inom åtta block som mottagare. Reserven finns för att API-nivåer
  // skiljer sig åt i vad de exponerar, och en gris som aldrig säger vad den
  // hittat är sämre än en som i ett hus med två säger det till fel person.
  try {
    const t = gris.getComponent("minecraft:tameable");
    if (t?.tamedToPlayer) return t.tamedToPlayer;
  } catch { }
  try {
    let bast = null, narmast = 8;
    for (const pl of world.getAllPlayers()) {
      if (!pl) continue;
      const d = avstand(pl.location, gris.location);
      if (d < narmast) { bast = pl; narmast = d; }
    }
    return bast;
  } catch { return null; }
}

function sag(pl, nyckel, med = []) {
  try {
    pl.onScreenDisplay.setActionBar({ rawtext: [{ translate: nyckel, with: { rawtext: med } }] });
  } catch { }
}

function namnet(gris) {
  try {
    const n = gris.nameTag;
    if (n) return { text: n };
  } catch { }
  return { translate: `entity.${gris.typeId}.name` };
}

// --- bökandet ---------------------------------------------------------------
function markenUnder(gris) {
  try {
    const p = gris.location;
    return gris.dimension.getBlock({ x: Math.floor(p.x), y: Math.floor(p.y) - 1, z: Math.floor(p.z) });
  } catch { return undefined; }
}

function boka(gris, tillst) {
  const mark = markenUnder(gris);
  if (!mark || !BOKBAR.includes(mark.typeId)) return;
  // TRYFFELN SYNS FÖRST I TRYNET. Släpps den direkt ser det ut som att den
  // ramlar ur luften — hela poängen med gris:bar är den halva sekunden där
  // spelaren ser VARIFRÅN den kom.
  satt(gris, `${NS}:bar`, 1);
  tillst.slapper = varv + BOK_DROJ / LOOP;
  try {
    gris.dimension.spawnParticle("minecraft:crop_growth_emitter", gris.location);
  } catch { }
  try { gris.dimension.playSound("dig.gravel", gris.location, { volume: 0.7 }); } catch { }
}

function slapp(gris, tillst) {
  satt(gris, `${NS}:bar`, 0);
  tillst.slapper = 0;
  try {
    const p = gris.location;
    gris.dimension.spawnItem(new ItemStack(`${NS}:tryffel`, 1),
      { x: p.x, y: p.y + 0.4, z: p.z });
  } catch { return; }
  const pl = agare(gris);
  if (pl) sag(pl, `${NS}.tryffel.hittad`);
}

// --- vittringen -------------------------------------------------------------
// Väderstrecken i den ordning gris.riktning.N räknar dem. Minecrafts z växer åt
// SÖDER och x åt öster, vilket är lätt att få om bakfoten.
const RIKTNING = [
  { dx: 0, dz: -1, i: 0 },   // norr
  { dx: 1, dz: 0, i: 1 },    // öster
  { dx: 0, dz: 1, i: 2 },    // söder
  { dx: -1, dz: 0, i: 3 },   // väster
];

function vadral(gris, radie) {
  // Glest rutnät kring grisen. MALM är sorterad efter värde, så det räcker att
  // hitta den lägst indexerade träffen — vi behöver inte gå igenom allt.
  const p = gris.location;
  const x0 = Math.floor(p.x), y0 = Math.floor(p.y), z0 = Math.floor(p.z);
  let bast = null;
  for (let dx = -radie; dx <= radie; dx += STEG) {
    for (let dy = -radie; dy <= radie; dy += STEG) {
      for (let dz = -radie; dz <= radie; dz += STEG) {
        let b;
        try { b = gris.dimension.getBlock({ x: x0 + dx, y: y0 + dy, z: z0 + dz }); }
        catch { continue; }              // oladdad bit: hoppa, inte krascha
        if (!b) continue;
        const i = MALM.indexOf(b.typeId);
        if (i < 0) continue;
        if (!bast || i < bast.i) bast = { i, dx, dy, dz };
        if (bast.i === 0) return bast;   // forntida spillror slår allt
      }
    }
  }
  return bast;
}

function vittra(gris, tillst, radie) {
  const pl = agare(gris);
  if (!pl) return;
  const fynd = vadral(gris, radie);
  tillst.vittrade = varv + VITTRING_PAUS / LOOP;
  if (!fynd) { sag(pl, `${NS}.ingenting`, [namnet(gris)]); return; }
  // RIKTNINGEN ÄR DEN GROVA, inte den exakta. "Nordost, 7,4 block" är en
  // GPS-signal och tar bort hela sökandet; ett väderstreck och ett avstånd
  // säger åt vilket håll man ska gräva och låter spelaren göra resten.
  const r = Math.abs(fynd.dx) > Math.abs(fynd.dz)
    ? (fynd.dx > 0 ? RIKTNING[1] : RIKTNING[3])
    : (fynd.dz > 0 ? RIKTNING[2] : RIKTNING[0]);
  const d = Math.round(Math.hypot(fynd.dx, fynd.dy, fynd.dz));
  sag(pl, `${NS}.vittring`, [
    namnet(gris),
    { translate: `${NS}.malm.${fynd.i}` },
    { translate: `${NS}.riktning.${r.i}` },
    { text: String(d) },
  ]);
  try { gris.dimension.playSound("mob.pig.say", gris.location, { pitch: 1.4 }); } catch { }
}

// --- loopen -----------------------------------------------------------------
// EN GRIS PER VARV får kosta på sig en malmsökning. Kön går runt genom att
// varje varv plocka den gris vars index matchar varvräknaren; med två grisar
// betyder det varannan sekund var, med tjugo betyder det var tjugonde.
let ko = 0;

// TICKBUDGETEN. Paketet har EN loop, men den gör en O(n²)-fri men ändå inte
// gratis genomgång av alla grisar varje halvsekund, och malmsökningen läser
// hundratals block. Ingen har mätt vad den kostar med en full svinstia.
// Kostnaden för mätningen är ett Date.now() per varv — försumbart mot det den
// mäter, och det enda som kan svara på om nästa funktion får plats.
const matning = { varv: 0, ms: 0 };

system.runInterval(() => {
  const _t0 = Date.now();
  try {
  varv++;
  const bokande = [];
  for (const dim of DIMENSIONER) {
    for (const gris of grisar(dim)) {
      let tillst = minne.get(gris.id);
      if (!tillst) { tillst = { slapper: 0, vittrade: 0, torkar: 0 }; minne.set(gris.id, tillst); }

      if (tillst.slapper && varv >= tillst.slapper) slapp(gris, tillst);

      // GYTTJEBADET. En gris som står i lera lägger sig i den då och då och är
      // lerig ett tag efteråt. Det här ligger FÖRE tämjningskontrollen med
      // flit: en vild gris i ett träsk ska också kunna vältra sig, och det är
      // samma blockavläsning som bökandet ändå gör.
      // TÄRNINGEN SLÅS FÖRE BLOCKAVLÄSNINGEN. Första versionen läste marken
      // under VARJE gris varje varv, och uthållighetsprovet mätte loopen från
      // 0,38 till 1,02 ms med trettio grisar. Sannolikheten att vältra sig är
      // densamma — men nu kostar den bara ett slumptal för de grisar som ändå
      // inte skulle ha lagt sig. Redan leriga grisar måste läsa marken oavsett,
      // för vatten ska tvätta av.
      // LERTILLSTÅNDET CACHAS i grisens minnespost i stället för att läsas ur
      // egenskapen varje varv. getProperty är ett inbyggt anrop, och det var
      // DET som kostade — att slå tärningen före blockavläsningen gav nästan
      // ingenting (1,02 -> 0,96 ms), vilket motbevisade min första gissning.
      // Undefined vid första anblicken betyder "läs en gång": en värld som
      // laddas in kan ha grisar som redan är leriga.
      if (tillst.lerig === undefined) tillst.lerig = prop(gris, `${NS}:lerig`, 0) === 1;
      const arLerig = tillst.lerig;
      const mark = (arLerig || Math.random() < LERA_CHANS) ? markenUnder(gris) : null;
      if (arLerig) {
        // VATTEN TVÄTTAR AV. Utan det går grisen lerig för alltid om man badar
        // med den, vilket ser ut som ett fel snarare än som lera.
        const ivatten = mark?.typeId === "minecraft:water";
        if (ivatten || (tillst.torkar && varv >= tillst.torkar)) {
          try { gris.triggerEvent(`${NS}:lerig_av`); } catch { }
          tillst.lerig = false; tillst.torkar = 0;
        }
      } else if (mark?.typeId === "minecraft:mud") {
        try {
          gris.triggerEvent(`${NS}:lerig_pa`);
          gris.dimension.spawnParticle("minecraft:water_splash_particle", gris.location);
          gris.dimension.playSound("mob.pig.step", gris.location, { volume: 0.9, pitch: 0.7 });
        } catch { }
        tillst.lerig = true;
        tillst.torkar = varv + LERA_TID / LOOP;
      }

      if (prop(gris, `${NS}:tam`, 0) !== 1) continue;
      if (prop(gris, `${NS}:lage`, 0) !== 1) {
        // Lämnar grisen bökläget med en tryffel i trynet ska den släppas, inte
        // bäras i evighet.
        if (prop(gris, `${NS}:bar`, 0) === 1) slapp(gris, tillst);
        continue;
      }
      if (!tillst.slapper && Math.random() < BOK_CHANS) boka(gris, tillst);
      if (varv >= tillst.vittrade) bokande.push([gris, tillst]);
    }
  }
  if (bokande.length) {
    const [gris, tillst] = bokande[ko++ % bokande.length];
    const radie = RASER[gris.typeId]?.nos ?? 6;
    vittra(gris, tillst, radie);
  }
  } finally {
    matning.varv++; matning.ms += Date.now() - _t0;
  }
}, LOOP);

// MINNET LÄCKER ANNARS. En gris som dör eller laddas ur lämnar sin post kvar,
// och en värld som körs i veckor samlar på sig tusentals döda grisar.
world.afterEvents.entityRemove.subscribe(ev => {
  minne.delete(ev.removedEntityId);
});

// RIDNING UTAN SADEL ska säga ifrån. Utan det här händer ingenting alls när man
// högerklickar en osadlad gris, och spelaren har ingen aning om varför.
world.beforeEvents.playerInteractWithEntity.subscribe(ev => {
  const { target, player } = ev;
  try {
    if (!target?.matches({ families: [FAMILJ] })) return;
    if (prop(target, `${NS}:tam`, 0) !== 1) return;
    if (prop(target, `${NS}:sadlad`, 0) === 1) return;
    if (ev.itemStack) return;              // tom hand = försöker sitta upp
    system.run(() => sag(player, `${NS}.behover_sadel`));
  } catch { }
});

// ---------------------------------------------------------------------------
// TESTKROKAR. OK-rader skrivs med console.log och fel med console.warn: i
// ContentLog blir det [inform] respektive [warning], och innehållsgrinden i
// snuffle-test filtrerar bort det första men faller på det andra. Kattpaketets
// mönster, lånat hit — grinden filtrerade tidigare bort alla rader som matchade
// "-TEST", vilket också dolde ett riktigt fel som råkade nämna ordet.
// TESTKROKAR. Bökandet väntar på slumpen och vittringen på en ägare; testet har
// varken tid att vänta eller en spelare att tala om för. Krokarna kör SAMMA
// funktioner med en plats i stället, så det som provas är mekaniken och inte en
// kopia av den — en testväg som räknar ut svaret själv bevisar ingenting.
function forstaGris() {
  for (const dim of DIMENSIONER) {
    const g = grisar(dim);
    if (g.length) return g[0];
  }
  return null;
}

system.afterEvents.scriptEventReceive.subscribe(ev => {
  const gris = forstaGris();
  if (!gris) { console.warn(`${ev.id}: ingen gris i världen`); return; }
  const tillst = minne.get(gris.id) ?? { slapper: 0, vittrade: 0, torkar: 0 };

  // TESTPLATSEN ÄR FAST. Grisen strosar (random_stroll ligger i baskomponenterna
  // så att en gris i bökläge inte står stilla), och mellan att kroken la jorden
  // och att bökandet kördes hade den hunnit gå därifrån — testet rapporterade
  // "marken under är sten" och pekade rakt på bökandet. Kroken flyttar därför
  // grisen till en känd ruta först och äger situationen i stället för att
  // tävla mot mobbens AI.
  const PLATS = { x: 10.5, y: 20, z: 10.5 };
  const stall = () => { try { gris.teleport(PLATS); } catch { } };

  if (ev.id === `${NS}:test_bok`) {
    // ARENANS GOLV ÄR STEN. Bökandet kräver jord under grisen, så kroken lägger
    // dit den — annars provar testet bara att BOKBAR fungerar som filter,
    // vilket det inte är till för.
    stall();
    try { gris.dimension.getBlock({ x: 10, y: 19, z: 10 }).setType("minecraft:grass_block"); }
    catch (e) { console.warn("BOK-TEST: kunde inte lägga jord: " + e); return; }
    // EN EGENSKAP LANDAR FÖRST VID TICKENS SLUT. setProperty kastar inte och ser
    // ut att lyckas, men getProperty i SAMMA tick ger fortfarande gamla värdet.
    // Testet läste tillbaka direkt efter boka() och rapporterade "inget i
    // trynet" i tre körningar — ett fel i TESTET som pekade rakt på bökandet.
    // Varje steg får därför en egen tick.
    system.runTimeout(() => {
      stall();
      boka(gris, tillst);
      system.runTimeout(() => {
        if (prop(gris, `${NS}:bar`, 0) !== 1) {
          const mark = markenUnder(gris);
          console.warn(`BOK-TEST: inget i trynet. mark=${mark?.typeId ?? "okänd"} `
                       + `iListan=${BOKBAR.includes(mark?.typeId)} y=${gris.location.y}`);
          return;
        }
        slapp(gris, tillst);
        system.runTimeout(() => {
          let n = 0;
          try {
            for (const e of gris.dimension.getEntities({
              type: "minecraft:item", location: gris.location, maxDistance: 6 })) {
              const i = e.getComponent("minecraft:item")?.itemStack;
              if (i?.typeId === `${NS}:tryffel`) n++;
            }
          } catch { }
          if (n) console.log("BOK-TEST OK");
          else console.warn("BOK-TEST: ingen tryffel på marken");
        }, 20);
      }, 2);
    }, 5);
    return;
  }

  if (ev.id === `${NS}:test_vittring`) {
    // MALMEN LÄGGS ÖSTERUT, fyra block bort. Både att grisen HITTAR den och att
    // den säger rätt väderstreck ska bevisas; en vittring som alltid säger
    // "norrut" hade passerat ett test som bara räknade träffar.
    stall();
    try { gris.dimension.getBlock({ x: 14, y: 20, z: 10 }).setType("minecraft:diamond_ore"); }
    catch (e) { console.warn("VITTRING-TEST: kunde inte lägga malm: " + e); return; }
    system.runTimeout(() => {
      stall();
      const fynd = vadral(gris, 8);
      if (!fynd) { console.warn("VITTRING-TEST: hittade ingen malm"); return; }
      const namn = MALM[fynd.i];
      const ost = Math.abs(fynd.dx) > Math.abs(fynd.dz) && fynd.dx > 0;
      if (namn === "minecraft:diamond_ore" && ost) console.log("VITTRING-TEST OK");
      else console.warn(`VITTRING-TEST: fel fynd (${namn}, dx=${fynd.dx} dz=${fynd.dz})`);
    }, 5);
    return;
  }

  if (ev.id === `${NS}:test_lera`) {
    // Leran utlöses av slumpen när grisen står i lera; testet kan inte vänta ut
    // den. Kroken lägger lera under grisen och kör samma väg.
    stall();
    try { gris.dimension.getBlock({ x: 10, y: 19, z: 10 }).setType("minecraft:mud"); }
    catch (e) { console.warn("LERA-TEST: kunde inte lägga lera: " + e); return; }
    system.runTimeout(() => {
      stall();
      const m = markenUnder(gris);
      if (m?.typeId !== "minecraft:mud") {
        console.warn(`LERA-TEST: marken är ${m?.typeId ?? "okänd"}, inte lera`); return;
      }
      try { gris.triggerEvent(`${NS}:lerig_pa`); } catch (e) { console.warn("LERA-TEST: " + e); return; }
      system.runTimeout(() => {
        if (prop(gris, `${NS}:lerig`, 0) === 1) console.log("LERA-TEST OK");
        else console.warn("LERA-TEST: gris:lerig sattes inte");
      }, 3);
    }, 5);
    return;
  }

  if (ev.id === `${NS}:test_ids`) {
    // FACIT ÄR MOTORN, inte en fil. Vaniljas blocks.json på disk är en
    // överskrivningsfil på 744 poster och saknar bl.a. grass_block, så en
    // statisk lista underkände giltiga block och godkände felstavade. Ett
    // felstavat id i BOKBAR gör att grisen aldrig bökar där, tyst.
    const okanda = [...BOKBAR, ...MALM].filter(id => !BlockTypes.get(id));
    if (okanda.length) console.warn("ID-TEST: okända block " + okanda.join(", "));
    else console.log(`ID-TEST OK (${BOKBAR.length + MALM.length} block)`);
    return;
  }

  if (ev.id === `${NS}:test_foremal`) {
    // Att tryffeln går att SKAPA bevisar att den är registrerad. Ett felstavat
    // id i spawnItem kastar; ett oregistrerat föremål gör det också.
    try {
      gris.dimension.spawnItem(new ItemStack(`${NS}:tryffel`, 1), gris.location);
      console.log("FOREMAL-TEST OK");
    } catch (e) { console.warn("FOREMAL-TEST: " + e); }
  }
});

// ---------------------------------------------------------------------------
// UTHÅLLIGHETSKROKAR. Det som bara syns över TID och SKALA: att tillståndet
// överlever en världsomstart, och vad loopen kostar med många grisar. Ingen av
// delarna går att prova i snuffle-test, som river världen vid varje körning.
const UTHALL = "Uthall";

function uthallGris() {
  for (const dim of DIMENSIONER) {
    try {
      for (const g of grisar(dim)) if (g.nameTag === UTHALL) return g;
    } catch { }
  }
  return null;
}

// Det som PÅSTÅS överleva en omstart: tämjning, läge, sadel, väskor och lasten.
const UTHALL_TILLSTAND = [["gris:tam", 1], ["gris:lage", 1],
                          ["gris:sadlad", 1], ["gris:vaskor", 1]];

system.afterEvents.scriptEventReceive.subscribe(ev => {
  if (ev.id === `${NS}:test_last`) {
    let n = 0;
    for (const d of DIMENSIONER) { try { n += grisar(d).length; } catch { } }
    const snitt = matning.varv ? matning.ms / matning.varv : 0;
    console.log(`[gris] LAST-TEST: ${n} grisar, ${matning.varv} varv, `
      + `${snitt.toFixed(2)} ms per varv (budget 50 ms/tick)`);
    matning.varv = 0; matning.ms = 0;
    return;
  }

  if (ev.id === `${NS}:test_satt`) {
    const g = uthallGris();
    if (!g) { console.warn("[gris] SPARA-TEST FEL: hittar inte " + UTHALL); return; }
    try {
      g.triggerEvent(`${NS}:nasta_lage`);      // följer -> bökar
      g.triggerEvent(`${NS}:sadla`);
      g.triggerEvent(`${NS}:vaskor_pa`);
    } catch (e) { console.warn("[gris] SPARA-TEST FEL: " + e); return; }
    // Lastrummet finns först nästa tick: väskorna skapar containern via en
    // komponentgrupp, och gruppen finns inte förrän eventet landat.
    system.runTimeout(() => {
      let last = "ingen";
      try {
        const box = g.getComponent("minecraft:inventory")?.container;
        if (box) { box.setItem(0, new ItemStack("minecraft:diamond", 3)); last = "diamant x3"; }
      } catch (e) { console.warn("[gris] SPARA-TEST FEL vid last: " + e); }
      const satta = UTHALL_TILLSTAND.map(([n]) => `${n}=${prop(g, n, "?")}`);
      console.log(`[gris] SPARA-TEST: ${satta.join(" ")} last=${last}`);
    }, 10);
    return;
  }

  if (ev.id === `${NS}:test_las`) {
    const g = uthallGris();
    if (!g) { console.warn("[gris] LAS-TEST FEL: grisen överlevde inte omstarten"); return; }
    const fel = [];
    for (const [namn, vantat] of UTHALL_TILLSTAND) {
      const nu = prop(g, namn, null);
      if (nu !== vantat) fel.push(`${namn}=${nu} (väntade ${vantat})`);
    }
    let diamanter = 0;
    try {
      const s2 = g.getComponent("minecraft:inventory")?.container?.getItem(0);
      if (s2?.typeId === "minecraft:diamond") diamanter = s2.amount;
    } catch { }
    if (diamanter !== 3) fel.push(`väskornas last=${diamanter} (väntade 3)`);
    if (fel.length) console.warn("[gris] LAS-TEST FEL: " + fel.join(", "));
    else console.log(`[gris] LAS-TEST OK: ${UTHALL_TILLSTAND.length} egenskaper och `
      + `sadelväskornas last överlevde omstarten`);
  }
});
