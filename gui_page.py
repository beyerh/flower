"""HTML/CSS/JS for the Flower GUI (served by flower.py)."""

PAGE_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Flower</title>
<style>
  :root {
    --bg: #f4f6f9; --card: #fff; --ink: #1e2430; --muted: #6b7480;
    --line: #dfe4ea; --accent: #3d6fb4; --accent-soft: #eaf1fa;
    --danger: #c0504d; --ok: #3f8f5f; --radius: 10px;
  }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
    font:13px/1.5 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  header { background:var(--card); border-bottom:1px solid var(--line);
    padding:12px 20px; display:flex; align-items:center; gap:16px;
    position:sticky; top:0; z-index:20; }
  header h1 { font-size:16px; margin:0; font-weight:600; }
  header .sub { color:var(--muted); font-size:12px; }
  header .spacer { flex:1; }
  .layout { display:grid; grid-template-columns:320px 1fr; gap:16px; padding:16px; align-items:start; }
  .stack { display:flex; flex-direction:column; gap:14px; }
  .stack.left { max-height:calc(100vh - 70px); overflow-y:auto; position:sticky; top:62px; padding-right:4px; }
  .stack.right { position:sticky; top:62px; max-height:calc(100vh - 70px); overflow-y:auto; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:var(--radius); overflow:visible; }
  .card > h2 { margin:0; padding:10px 14px; font-size:13px; font-weight:600;
    border-bottom:1px solid var(--line); background:#fbfcfd;
    display:flex; align-items:center; gap:8px; cursor:pointer; user-select:none; }
  .card > h2 .chev { color:var(--muted); font-size:11px; transition:transform .15s; }
  .card.collapsed > h2 .chev { transform:rotate(-90deg); }
  .card.collapsed > .body { display:none; }
  .body { padding:12px 14px; }
  .plots { display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; }
  @media (max-width:1400px) { .plots { grid-template-columns:1fr 1fr; } }
  @media (max-width:900px) { .plots { grid-template-columns:1fr; } }
  label.field { display:block; margin-bottom:10px; }
  label.field .name { font-weight:500; }
  label.field .hint { color:var(--muted); font-size:11.5px; margin:1px 0 4px; }
  input[type=text],input[type=number],select {
    width:100%; padding:5px 7px; border:1px solid var(--line);
    border-radius:6px; font:inherit; background:#fff; color:var(--ink); }
  input:focus,select:focus { outline:2px solid var(--accent-soft); border-color:var(--accent); }
  .grid2 { display:grid; grid-template-columns:1fr 1fr; gap:0 10px; }
  .switch { display:flex; align-items:center; gap:8px; margin-bottom:10px; }
  .switch input { width:15px; height:15px; accent-color:var(--accent); }
  .switch .txt .name { font-weight:500; }
  .switch .txt .hint { color:var(--muted); font-size:11.5px; }
  button { font:inherit; padding:6px 12px; border-radius:7px; border:1px solid var(--line);
    background:#fff; color:var(--ink); cursor:pointer; }
  button:hover { background:#f2f5f9; }
  button.primary { background:var(--accent); border-color:var(--accent); color:#fff; font-weight:600; }
  button.primary:hover { filter:brightness(1.07); }
  button.ghost { border-style:dashed; color:var(--muted); }
  button.mini { padding:2px 7px; font-size:12px; line-height:1.4; }
  .btnrow { display:flex; gap:8px; flex-wrap:wrap; }
  table.samples { width:100%; border-collapse:collapse; }
  table.samples td { padding:3px 2px; vertical-align:middle; }
  table.samples input[type=color] { width:26px; height:24px; padding:0; border:1px solid var(--line);
    border-radius:5px; background:none; cursor:pointer; }
  table.samples .count { color:var(--muted); font-size:11.5px; white-space:nowrap; }
  .dropzone { border:2px dashed var(--line); border-radius:var(--radius); padding:14px;
    text-align:center; color:var(--muted); margin-top:10px; transition:.15s; }
  .dropzone.hot { border-color:var(--accent); background:var(--accent-soft); color:var(--accent); }
  .browser { margin-top:10px; border:1px solid var(--line); border-radius:8px; }
  .browser .path { padding:6px 8px; border-bottom:1px solid var(--line);
    font-size:11.5px; color:var(--muted); word-break:break-all; background:#fbfcfd; }
  .browser ul { list-style:none; margin:0; padding:4px; max-height:210px; overflow:auto; }
  .browser li { padding:4px 7px; border-radius:6px; cursor:pointer;
    display:flex; align-items:center; gap:7px; }
  .browser li:hover { background:var(--accent-soft); }
  .browser li.done { color:var(--muted); cursor:default; }
  .browser li.done:hover { background:none; }
  .plotbox { position:relative; line-height:0; }
  .plotbox img { max-width:100%; border-radius:6px; }
  .plotbox canvas { position:absolute; left:0; top:0; cursor:crosshair; }
  .plotwrap { display:flex; align-items:stretch; gap:0; }
  .plotwrap .y-col { display:flex; align-items:center; justify-content:center; width:28px; flex-shrink:0; position:relative; }
  .plotwrap .y-col .ylbl { writing-mode:vertical-rl; transform:rotate(180deg); font-size:12px; font-weight:500;
    cursor:pointer; padding:6px 4px; border:1px solid var(--line); border-radius:6px; background:#fff;
    white-space:nowrap; user-select:none; }
  .plotwrap .y-col .ylbl:hover { background:var(--accent-soft); border-color:var(--accent); }
  .plotwrap .y-col .dd { position:absolute; left:calc(100% + 4px); top:50%; transform:translateY(-50%); z-index:30;
    background:#fff; border:1px solid var(--line); border-radius:6px; box-shadow:0 4px 14px rgba(0,0,0,.12);
    max-height:260px; overflow-y:auto; min-width:120px; display:none; }
  .plotwrap .y-col .dd.open { display:block; }
  .plotwrap .main-col { flex:1; min-width:0; }
  .axis-x { text-align:center; padding:4px 0 0; }
  .al { font-size:12px; font-weight:500; cursor:pointer; padding:3px 10px;
    border:1px solid var(--line); border-radius:6px; background:#fff; white-space:nowrap;
    position:relative; user-select:none; display:inline-block; }
  .al:hover { background:var(--accent-soft); border-color:var(--accent); }
  .al .dd { position:absolute; bottom:calc(100% + 2px); left:50%; transform:translateX(-50%); z-index:30;
    background:#fff; border:1px solid var(--line); border-radius:6px; box-shadow:0 4px 14px rgba(0,0,0,.12);
    max-height:260px; overflow-y:auto; min-width:120px; display:none; }
  .al .dd.open { display:block; }
  .al .dd div { padding:4px 10px; cursor:pointer; font-size:12px; font-weight:400; white-space:nowrap; }
  .al .dd div:hover { background:var(--accent-soft); }
  .al .dd div.sel { color:var(--accent); font-weight:600; }
  .tag { font-size:11.5px; color:var(--muted); }
  .statline { font-size:11.5px; color:var(--muted); margin-top:8px; }
  .statline b { color:var(--ink); font-weight:600; }
  .banner { padding:8px 12px; border-radius:8px; font-size:12px; margin-bottom:10px; display:none; }
  .banner.err { display:block; background:#fdecea; color:#8f2c28; border:1px solid #f5c6c2; }
  .banner.ok { display:block; background:#eaf6ef; color:#24623f; border:1px solid #c2e2ce; }
  pre.snippet { background:#1e2430; color:#dbe3ef; padding:10px; border-radius:8px;
    font-size:11px; overflow:auto; max-height:220px; margin:8px 0 0; }
  .spin { display:inline-block; width:12px; height:12px; border:2px solid var(--line);
    border-top-color:var(--accent); border-radius:50%; animation:sp .7s linear infinite; }
  @keyframes sp { to { transform:rotate(360deg); } }
  .gate-mode { display:flex; gap:4px; margin-bottom:8px; flex-wrap:wrap; align-items:center; }
  .gate-mode button { padding:4px 10px; font-size:12px; }
  .gate-mode button.active { background:var(--accent); color:#fff; border-color:var(--accent); }
  .quad-grid { display:grid; grid-template-columns:1fr 1fr; gap:4px; margin:8px 0; }
  .quad-grid button { padding:6px; font-size:11px; text-align:center; }
  .quad-grid button.active { background:var(--accent); color:#fff; border-color:var(--accent); }
  .gate-section { border-top:1px solid var(--line); margin-top:12px; padding-top:12px; }
  .gate-section:first-child { border-top:none; margin-top:0; padding-top:0; }
  .gate-section h3 { margin:0 0 8px; font-size:12px; font-weight:600; color:var(--muted); }
</style>
</head>
<body>

<header>
  <h1>Flower</h1>
  <span class="sub" id="hdrinfo"></span>
  <span class="spacer"></span>
  <span id="busy" class="tag"></span>
  <button class="primary" onclick="save()">Save all</button>
</header>

<div class="layout">
  <!-- left column -->
  <div class="stack left">
    <div class="card" id="card-files">
      <h2 onclick="toggle('card-files')"><span class="chev">&#9660;</span> Samples</h2>
      <div class="body">
        <table class="samples" id="sampletable"></table>
        <div class="dropzone" id="drop">Drop <b>.fcs</b> files here</div>
        <div class="btnrow" style="margin-top:10px;">
          <button onclick="browse()">Browse folder&hellip;</button>
          <button class="ghost" onclick="clearAll()">Remove all</button>
        </div>
        <div class="browser" id="browser" style="display:none;">
          <div class="path" id="browserpath"></div>
          <ul id="browserlist"></ul>
        </div>
      </div>
    </div>

    <div class="card" id="card-gate">
      <h2 onclick="toggle('card-gate')"><span class="chev">&#9660;</span> Gating</h2>
      <div class="body">
        <label class="field"><span class="name">Gating sample</span>
          <select id="ssample" onchange="switchSample()"></select></label>

        <div class="gate-section">
          <h3>Gating scatter (FSC/SSC)</h3>
          <div class="gate-mode">
            <button id="sm_polygon" class="active" onclick="setScatterMode('polygon')">Polygon</button>
            <button id="sm_quadrant" onclick="setScatterMode('quadrant')">Quadrant</button>
            <button onclick="clearScatterGate()">Clear</button>
          </div>
          <div id="quadrantUI" style="display:none;">
            <div class="grid2">
              <label class="field"><span class="name">X threshold</span>
                <input type="number" id="qthr_x" step="any" onchange="updateQuadrant()"></label>
              <label class="field"><span class="name">Y threshold</span>
                <input type="number" id="qthr_y" step="any" onchange="updateQuadrant()"></label>
            </div>
            <div class="quad-grid">
              <button id="q_UL" onclick="toggleQuadrant('UL')">UL</button>
              <button id="q_UR" onclick="toggleQuadrant('UR')">UR</button>
              <button id="q_LL" onclick="toggleQuadrant('LL')">LL</button>
              <button id="q_LR" onclick="toggleQuadrant('LR')">LR</button>
            </div>
          </div>
          <div id="polygonUI" class="btnrow">
            <button onclick="closeGate()">Close gate</button>
            <button onclick="undoVertex()">Undo point</button>
          </div>
        </div>

        <div class="gate-section">
          <h3>Histogram interval</h3>
          <div class="gate-mode">
            <button onclick="clearHistGate()">Clear interval</button>
          </div>
          <div class="hint" style="color:var(--muted);">Click two points on the histogram to set bounds. Drag handles to adjust.</div>
        </div>

        <div class="gate-section">
          <h3>Analysis scatter</h3>
          <div class="gate-mode">
            <button id="am_polygon" class="active" onclick="setAnalysisMode('polygon')">Polygon</button>
            <button id="am_quadrant" onclick="setAnalysisMode('quadrant')">Quadrant</button>
            <button onclick="clearAnalysisGate()">Clear</button>
          </div>
          <div id="aquadrantUI" style="display:none;">
            <div class="grid2">
              <label class="field"><span class="name">X threshold</span>
                <input type="number" id="aqthr_x" step="any" onchange="updateAnalysisQuadrant()"></label>
              <label class="field"><span class="name">Y threshold</span>
                <input type="number" id="aqthr_y" step="any" onchange="updateAnalysisQuadrant()"></label>
            </div>
            <div class="quad-grid">
              <button id="aq_UL" onclick="toggleAnalysisQuadrant('UL')">UL</button>
              <button id="aq_UR" onclick="toggleAnalysisQuadrant('UR')">UR</button>
              <button id="aq_LL" onclick="toggleAnalysisQuadrant('LL')">LL</button>
              <button id="aq_LR" onclick="toggleAnalysisQuadrant('LR')">LR</button>
            </div>
          </div>
          <div id="apolygonUI" class="btnrow">
            <button onclick="closeAnalysisGate()">Close gate</button>
            <button onclick="undoAnalysisVertex()">Undo point</button>
          </div>
        </div>

        <div class="statline" id="gatestats"></div>
      </div>
    </div>

    <div id="settings"></div>
  </div>

  <!-- right column -->
  <div class="stack right">
    <div class="banner" id="banner"></div>
    <div class="plots">
      <div class="card">
        <h2><span class="chev" style="visibility:hidden">&#9660;</span> Gating scatter <span class="tag" id="scatter_size"></span></h2>
        <div class="body">
          <div class="plotwrap">
            <div class="y-col">
              <div class="ylbl" id="scatter_y_label" onclick="toggleAxisDD('scatter_y')"><span id="scatter_y_val"></span></div>
              <div class="dd" id="scatter_y_dd"></div>
            </div>
            <div class="main-col">
              <div class="plotbox" id="scatterbox">
                <img id="scatterimg" alt="gating scatter">
                <canvas id="scattercv"></canvas>
              </div>
              <div class="axis-x">
                <div class="al" id="scatter_x_label" onclick="toggleAxisDD('scatter_x')"><span id="scatter_x_val"></span><div class="dd" id="scatter_x_dd"></div></div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="card">
        <h2><span class="chev" style="visibility:hidden">&#9660;</span> Histogram <span class="tag" id="hist_size"></span></h2>
        <div class="body">
          <div class="plotwrap">
            <div class="y-col" style="visibility:hidden"></div>
            <div class="main-col">
              <div class="plotbox" id="histbox">
                <img id="histimg" alt="histogram">
                <canvas id="histcv"></canvas>
              </div>
              <div class="axis-x">
                <div class="al" id="channel_label" onclick="toggleAxisDD('channel')"><span id="channel_val"></span><div class="dd" id="channel_dd"></div></div>
              </div>
            </div>
          </div>
          <div class="statline" id="histstats"></div>
        </div>
      </div>
      <div class="card">
        <h2><span class="chev" style="visibility:hidden">&#9660;</span> Analysis scatter <span class="tag" id="analysis_size"></span></h2>
        <div class="body">
          <div class="plotwrap">
            <div class="y-col">
              <div class="ylbl" id="analysis_y_label" onclick="toggleAxisDD('analysis_y')"><span id="analysis_y_val"></span></div>
              <div class="dd" id="analysis_y_dd"></div>
            </div>
            <div class="main-col">
              <div class="plotbox" id="analysisbox">
                <img id="analysisimg" alt="analysis scatter">
                <canvas id="analysiscv"></canvas>
              </div>
              <div class="axis-x">
                <div class="al" id="analysis_x_label" onclick="toggleAxisDD('analysis_x')"><span id="analysis_x_val"></span><div class="dd" id="analysis_x_dd"></div></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="card collapsed" id="card-snippet">
      <h2 onclick="toggle('card-snippet')"><span class="chev">&#9660;</span> Reproducible script snippet</h2>
      <div class="body">
        <div class="tag">Paste into <b>plot_ecd_histogram.py</b> to rerun without the GUI.</div>
        <pre class="snippet" id="snippet">Save once to generate the snippet.</pre>
      </div>
    </div>
  </div>
</div>

<script>
let SCHEMA=[], DEFAULTS={}, SAMPLES=[], CHANNELS=[];
let SCATTER_META=null, HIST_META=null, ANALYSIS_META=null;
let SCATTER_GATES={}, HIST_GATES={}, ANALYSIS_GATES={};
let activeIdx=0, busy=0;

// Gating scatter state
let verts=[], closed=false, scatterMode="polygon";
let quadThr={x:0,y:0}, quadSel=new Set();

// Analysis scatter state
let aVerts=[], aClosed=false, analysisMode="polygon";
let aQuadThr={x:0,y:0}, aQuadSel=new Set();

// Histogram interval state
let histInterval=null, histDragging=null;

function toggle(id){ document.getElementById(id).classList.toggle("collapsed"); }
function el(id){ return document.getElementById(id); }
function setBusy(d){ busy+=d; el("busy").innerHTML=busy>0?'<span class="spin"></span>':""; }
function banner(msg,kind){ const b=el("banner"); b.className="banner "+(kind||""); b.textContent=msg||""; if(!msg) b.style.display="none"; }
async function api(path,body){
  setBusy(1);
  try{
    const r=await fetch(path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body||{})});
    const j=await r.json();
    if(j.error){ banner(j.error,"err"); throw new Error(j.error); }
    return j;
  } finally { setBusy(-1); }
}

/* settings — channel fields are handled by axis-label dropdowns, not here */
const CHANNEL_KEYS = new Set(["channel","scatter_x","scatter_y","analysis_x","analysis_y"]);
function fieldHtml(f){
  if(f.type==="bool") return `<div class="switch"><input type="checkbox" id="f_${f.key}" ${DEFAULTS[f.key]?"checked":""} onchange="refresh()"><span class="txt"><span class="name">${f.label}</span><span class="hint">${f.help}</span></span></div>`;
  if(f.type==="choice"||f.type==="channel"){
    const opts=(f.type==="channel"?CHANNELS:f.options)||[];
    return `<label class="field"><span class="name">${f.label}</span><span class="hint">${f.help}</span><select id="f_${f.key}" onchange="refresh()">${opts.map(o=>`<option ${o===DEFAULTS[f.key]?"selected":""}>${o}</option>`).join("")}</select></label>`;
  }
  const num=f.type==="int"||f.type==="float";
  return `<label class="field"><span class="name">${f.label}</span><span class="hint">${f.help}</span><input type="${num?"number":"text"}" id="f_${f.key}" step="${f.type==="float"?"any":"1"}" value="${DEFAULTS[f.key]}" onchange="refresh()"></label>`;
}
function buildSettings(){
  el("settings").innerHTML=SCHEMA.map((group,gi)=>{
    const vis=group.fields.filter(f=>!CHANNEL_KEYS.has(f.key));
    const wide=vis.filter(f=>f.type==="bool"||f.type==="choice");
    const narrow=vis.filter(f=>!wide.includes(f));
    return `<div class="card collapsed" id="card-g${gi}"><h2 onclick="toggle('card-g${gi}')"><span class="chev">&#9660;</span> ${group.name}</h2><div class="body">${wide.map(fieldHtml).join("")}${narrow.length?`<div class="grid2">${narrow.map(fieldHtml).join("")}</div>`:""}</div></div>`;
  }).join("");
}
function settings(){
  const out={};
  SCHEMA.forEach(g=>g.fields.forEach(f=>{
    if(CHANNEL_KEYS.has(f.key)){ out[f.key]=el(f.key+"_val").textContent; return; }
    const n=el("f_"+f.key); if(!n) return; out[f.key]=f.type==="bool"?n.checked:n.value;
  }));
  return out;
}

/* samples */
function renderSamples(){
  el("sampletable").innerHTML=SAMPLES.map((s,i)=>{
    const sg=SCATTER_GATES[String(i)], hg=HIST_GATES[String(i)], ag=ANALYSIS_GATES[String(i)];
    let icons="";
    if(sg) icons+='<span style="color:var(--ok);font-size:10px;" title="scatter gate">S</span>';
    if(hg) icons+='<span style="color:var(--ok);font-size:10px;" title="histogram gate">H</span>';
    if(ag) icons+='<span style="color:var(--ok);font-size:10px;" title="analysis gate">A</span>';
    if(!sg&&!hg&&!ag) icons='<span style="color:var(--line);font-size:14px;">&#9675;</span>';
    return `<tr><td><input type="checkbox" ${s.active!==false?"checked":""} id="a_${i}" onchange="toggleActive(${i})" style="width:15px;height:15px;accent-color:var(--accent);"></td><td style="font-size:10px;">${icons}</td><td><input type="color" value="${s.color}" oninput="updateSample(${i})" id="c_${i}"></td><td style="width:100%"><input type="text" value="${s.label}" onchange="updateSample(${i})" id="l_${i}"></td><td class="count">${s.n.toLocaleString()}</td><td><button class="mini" onclick="move(${i},-1)">&#9650;</button></td><td><button class="mini" onclick="move(${i},1)">&#9660;</button></td><td><button class="mini" onclick="removeSample(${i})">&times;</button></td></tr>`;
  }).join("")||'<tr><td class="count">No samples loaded.</td></tr>';

  const sel=el("ssample"); const keep=sel.selectedIndex;
  sel.innerHTML=SAMPLES.map((s,i)=>{let m="";if(SCATTER_GATES[String(i)]||HIST_GATES[String(i)]||ANALYSIS_GATES[String(i)])m=" \u2713";return `<option value="${i}">${s.label}${m}</option>`;}).join("");
  activeIdx=Math.max(0,Math.min(keep,SAMPLES.length-1)); sel.selectedIndex=activeIdx;
  loadGatesForActive();
  el("hdrinfo").textContent=SAMPLES.length?`${SAMPLES.length} sample(s)`:"no samples";
}
/* axis-label channel dropdowns */
function initAxisLabels(){
  for(const key of CHANNEL_KEYS){
    const val=el(key+"_val"), dd=el(key+"_dd");
    if(!val||!dd) continue;
    val.textContent=DEFAULTS[key];
    dd.innerHTML=CHANNELS.map(c=>`<div class="${c===DEFAULTS[key]?"sel":""}" onclick="pickChannel('${key}','${c}')">${c}</div>`).join("");
  }
}
function toggleAxisDD(key){
  const dd=el(key+"_dd"); if(!dd) return;
  const open=dd.classList.contains("open");
  document.querySelectorAll(".dd.open").forEach(d=>d.classList.remove("open"));
  if(!open) dd.classList.add("open");
}
function pickChannel(key,ch){
  el(key+"_val").textContent=ch;
  el(key+"_dd").classList.remove("open");
  el(key+"_dd").querySelectorAll("div").forEach(d=>d.classList.toggle("sel",d.textContent===ch));
  refresh();
}
document.addEventListener("click",e=>{
  if(!e.target.closest(".al")&&!e.target.closest(".ylbl")) document.querySelectorAll(".dd.open").forEach(d=>d.classList.remove("open"));
});
async function updateSample(i){ const j=await api("/api/samples/update",{index:i,label:el("l_"+i).value,color:el("c_"+i).value}); SAMPLES=j.samples; renderSamples(); refresh(); }
async function toggleActive(i){ const j=await api("/api/samples/update",{index:i,active:el("a_"+i).checked}); SAMPLES=j.samples; refresh(); }
async function removeSample(i){ applySamples(await api("/api/samples/remove",{index:i})); }
async function move(i,d){ applySamples(await api("/api/samples/move",{index:i,delta:d})); }
async function clearAll(){ while(SAMPLES.length){SAMPLES=(await api("/api/samples/remove",{index:0})).samples;} applySamples({samples:SAMPLES,channels:CHANNELS}); }
function applySamples(j){ SAMPLES=j.samples; if(j.channels){CHANNELS=j.channels; initAxisLabels();} renderSamples(); refresh(); }

/* browse */
async function browse(dir){
  const j=await api("/api/browse",{dir:dir});
  el("browser").style.display="block"; el("browserpath").textContent=j.dir;
  el("browserlist").innerHTML=`<li onclick="browse('${j.parent.replace(/\\/g,"\\\\")}')">&#8598; parent</li>`+
    j.folders.map(f=>`<li onclick="browse('${(j.dir+"/"+f).replace(/\\/g,"\\\\")}')">&#128193; ${f}</li>`).join("")+
    j.files.map(f=>f.loaded?`<li class="done">&#10003; ${f.name}</li>`:`<li onclick="addPath('${(j.dir+"/"+f.name).replace(/\\/g,"\\\\")}')">&#128202; ${f.name}</li>`).join("");
}
async function addPath(p){ applySamples(await api("/api/samples/add",{paths:[p]})); browse(el("browserpath").textContent); }

/* drag&drop */
const dz=el("drop");
dz.addEventListener("dragover",e=>{e.preventDefault();dz.classList.add("hot");});
dz.addEventListener("dragleave",()=>dz.classList.remove("hot"));
dz.addEventListener("drop",async e=>{
  e.preventDefault();dz.classList.remove("hot");
  const files=[...e.dataTransfer.files].filter(f=>f.name.toLowerCase().endsWith(".fcs"));
  if(!files.length){banner("Only .fcs files.","err");return;}
  const payload=await Promise.all(files.map(f=>new Promise(res=>{const r=new FileReader();r.onload=()=>res({name:f.name,data:r.result.split(",")[1]});r.readAsDataURL(f);})));
  applySamples(await api("/api/samples/upload",{files:payload}));
  banner(`Loaded ${payload.length} file(s).`,"ok");
});

/* plots */
async function drawScatter(){
  if(!SAMPLES.length){el("scatterimg").removeAttribute("src");return;}
  activeIdx=Math.max(0,el("ssample").selectedIndex);
  const j=await api("/api/scatter",{index:activeIdx,settings:settings()});
  SCATTER_META=j.meta; el("scatterimg").src="data:image/png;base64,"+j.img;
  el("scatterimg").onload=()=>sizeCanvas("scatter"); el("scatter_size").textContent=`${SCATTER_META.width}\u00d7${SCATTER_META.height}px`;
  showGateStats(j.stats);
}
async function drawAnalysis(){
  if(!SAMPLES.length){el("analysisimg").removeAttribute("src");return;}
  const j=await api("/api/analysis_scatter",{index:activeIdx,settings:settings()});
  ANALYSIS_META=j.meta; el("analysisimg").src="data:image/png;base64,"+j.img;
  el("analysisimg").onload=()=>sizeCanvas("analysis"); el("analysis_size").textContent=`${ANALYSIS_META.width}\u00d7${ANALYSIS_META.height}px`;
}
async function drawHistogram(){
  if(!SAMPLES.length){el("histimg").removeAttribute("src");return;}
  const j=await api("/api/histogram",{settings:settings()});
  HIST_META=j.meta; el("histimg").src="data:image/png;base64,"+j.img;
  el("histimg").onload=()=>sizeCanvas("hist"); el("hist_size").textContent=`${HIST_META.width}\u00d7${HIST_META.height}px`;
  el("histstats").innerHTML=j.stats.filter(s=>s.active).map(s=>`<b>${s.label}</b>: ${s.plotted.toLocaleString()} events`).join(" &nbsp;|&nbsp; ");
}
function showGateStats(stats){
  el("gatestats").innerHTML=stats.map(s=>
    `<b>${s.label}</b>`+
    (s.has_scatter_gate?' S\u2713':'')+(s.has_hist_gate?' H\u2713':'')+(s.has_analysis_gate?' A\u2713':'')+
    `: ${s.scatter_kept.toLocaleString()}/${s.total.toLocaleString()} (${s.scatter_percent}%)`+
    (s.has_hist_gate?` \u2192 ${s.plotted.toLocaleString()} plotted`:'')
  ).join("<br>");
}
function refresh(){ drawScatter(); drawHistogram(); drawAnalysis(); }
function switchSample(){
  activeIdx=Math.max(0,el("ssample").selectedIndex);
  loadGatesForActive(); drawScatter(); drawAnalysis();
}
function loadGatesForActive(){
  const sg=SCATTER_GATES[String(activeIdx)], hg=HIST_GATES[String(activeIdx)], ag=ANALYSIS_GATES[String(activeIdx)];
  // gating scatter
  if(sg&&sg.type==="polygon"){verts=sg.verts.map(v=>[...v]);closed=true;setScatterMode("polygon");}
  else if(sg&&sg.type==="quadrant"){verts=[];closed=false;quadThr={x:sg.x_threshold,y:sg.y_threshold};quadSel=new Set(sg.quadrants||[]);setScatterMode("quadrant");}
  else{verts=[];closed=false;setScatterMode("polygon");}
  // hist
  if(hg&&hg.type==="interval"){histInterval={lo:hg.lo,hi:hg.hi,y:hg.y_pos||0};}else{histInterval=null;}
  // analysis
  if(ag&&ag.type==="polygon"){aVerts=ag.verts.map(v=>[...v]);aClosed=true;setAnalysisMode("polygon");}
  else if(ag&&ag.type==="quadrant"){aVerts=[];aClosed=false;aQuadThr={x:ag.x_threshold,y:ag.y_threshold};aQuadSel=new Set(ag.quadrants||[]);setAnalysisMode("quadrant");}
  else{aVerts=[];aClosed=false;setAnalysisMode("polygon");}
  overlayScatter(); overlayHist(); overlayAnalysis();
}

/* canvas helpers */
function sizeCanvas(which){
  if(which==="scatter"){const img=el("scatterimg"),cv=el("scattercv");cv.width=img.clientWidth;cv.height=img.clientHeight;overlayScatter();}
  if(which==="hist"){const img=el("histimg"),cv=el("histcv");cv.width=img.clientWidth;cv.height=img.clientHeight;overlayHist();}
  if(which==="analysis"){const img=el("analysisimg"),cv=el("analysiscv");cv.width=img.clientWidth;cv.height=img.clientHeight;overlayAnalysis();}
}
const BBOX=[0.15,0.14,0.80,0.80];
function toPx(meta,x,y){
  const img=meta===SCATTER_META?el("scatterimg"):meta===ANALYSIS_META?el("analysisimg"):el("histimg");
  const w=img.clientWidth,h=img.clientHeight,sc=meta.scale||"log";
  let fx,fy;
  if(sc==="log"){
    fx=(Math.log10(x)-Math.log10(meta.xlim[0]))/(Math.log10(meta.xlim[1])-Math.log10(meta.xlim[0]));
    fy=(Math.log10(y)-Math.log10(meta.ylim[0]))/(Math.log10(meta.ylim[1])-Math.log10(meta.ylim[0]));
  } else {
    fx=(x-meta.xlim[0])/(meta.xlim[1]-meta.xlim[0]);
    fy=(y-meta.ylim[0])/(meta.ylim[1]-meta.ylim[0]);
  }
  return [(BBOX[0]+fx*BBOX[2])*w,(1-BBOX[1]-fy*BBOX[3])*h];
}
function toData(meta,px,py){
  const img=meta===SCATTER_META?el("scatterimg"):meta===ANALYSIS_META?el("analysisimg"):el("histimg");
  const w=img.clientWidth,h=img.clientHeight,sc=meta.scale||"log";
  const fx=(px/w-BBOX[0])/BBOX[2], fy=(1-py/h-BBOX[1])/BBOX[3];
  if(sc==="log"){
    return [10**(Math.log10(meta.xlim[0])+fx*(Math.log10(meta.xlim[1])-Math.log10(meta.xlim[0]))),
            10**(Math.log10(meta.ylim[0])+fy*(Math.log10(meta.ylim[1])-Math.log10(meta.ylim[0])))];
  }
  return [meta.xlim[0]+fx*(meta.xlim[1]-meta.xlim[0]),meta.ylim[0]+fy*(meta.ylim[1]-meta.ylim[0])];
}

/* gating scatter */
function setScatterMode(mode){
  scatterMode=mode;
  el("sm_polygon").classList.toggle("active",mode==="polygon");
  el("sm_quadrant").classList.toggle("active",mode==="quadrant");
  el("polygonUI").style.display=mode==="polygon"?"flex":"none";
  el("quadrantUI").style.display=mode==="quadrant"?"block":"none";
  if(mode==="quadrant"&&SCATTER_META){
    if(quadThr.x===0){const xl=SCATTER_META.xlim,yl=SCATTER_META.ylim;quadThr.x=Math.sqrt(xl[0]*xl[1]);quadThr.y=Math.sqrt(yl[0]*yl[1]);el("qthr_x").value=quadThr.x.toExponential(2);el("qthr_y").value=quadThr.y.toExponential(2);}
    updateQuadrantUI();
  }
  overlayScatter();
}
function overlayScatter(){
  const cv=el("scattercv"),ctx=cv.getContext("2d");ctx.clearRect(0,0,cv.width,cv.height);
  if(!SCATTER_META)return;
  if(scatterMode==="polygon"&&verts.length){
    ctx.strokeStyle="#C44E52";ctx.lineWidth=1.5;ctx.beginPath();
    verts.forEach((v,i)=>{const[x,y]=toPx(SCATTER_META,v[0],v[1]);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});
    if(closed)ctx.closePath();ctx.stroke();
    ctx.fillStyle="#C44E52";verts.forEach(v=>{const[x,y]=toPx(SCATTER_META,v[0],v[1]);ctx.beginPath();ctx.arc(x,y,3,0,6.2832);ctx.fill();});
  }
  if(scatterMode==="quadrant"&&quadThr.x>0){
    const[qx,qy]=toPx(SCATTER_META,quadThr.x,quadThr.y);
    const img=el("scatterimg"),w=img.clientWidth,h=img.clientHeight;
    ctx.strokeStyle="#C44E52";ctx.lineWidth=1.5;ctx.setLineDash([5,3]);
    ctx.beginPath();ctx.moveTo(qx,(1-BBOX[1]-BBOX[3])*h);ctx.lineTo(qx,(1-BBOX[1])*h);ctx.stroke();
    ctx.beginPath();ctx.moveTo(BBOX[0]*w,qy);ctx.lineTo((BBOX[0]+BBOX[2])*w,qy);ctx.stroke();
    ctx.setLineDash([]);
    ctx.font="11px sans-serif";ctx.fillStyle="#C44E52";
    const labels={UL:[qx-15,qy-8],UR:[qx+8,qy-8],LL:[qx-15,qy+16],LR:[qx+8,qy+16]};
    for(const q of quadSel){const[lx,ly]=labels[q];ctx.fillText(q,lx,ly);}
  }
}
el("scattercv").addEventListener("click",e=>{
  if(!SCATTER_META)return;
  if(scatterMode==="polygon"){
    if(closed){verts=[];closed=false;}
    const r=e.target.getBoundingClientRect();verts.push(toData(SCATTER_META,e.clientX-r.left,e.clientY-r.top));overlayScatter();
  }
});
el("scattercv").addEventListener("dblclick",()=>{if(scatterMode==="polygon")closeGate();});
async function closeGate(){
  if(verts.length<3){banner("Need at least 3 corners.","err");return;}
  closed=true;overlayScatter();
  const gate={type:"polygon",x:settings().scatter_x,y:settings().scatter_y,verts:verts};
  await api("/api/gate/set",{index:activeIdx,gate_type:"scatter",gate:gate});
  SCATTER_GATES[String(activeIdx)]=gate;renderSamples();refresh();
}
function undoVertex(){verts.pop();closed=false;overlayScatter();}
async function clearScatterGate(){
  verts=[];closed=false;quadSel.clear();overlayScatter();
  delete SCATTER_GATES[String(activeIdx)];
  await api("/api/gate/clear",{index:activeIdx,gate_type:"scatter"});
  renderSamples();refresh();
}
function toggleQuadrant(q){if(quadSel.has(q))quadSel.delete(q);else quadSel.add(q);updateQuadrantUI();sendQuadrantGate();}
function updateQuadrantUI(){for(const q of["UL","UR","LL","LR"])el("q_"+q).classList.toggle("active",quadSel.has(q));}
async function updateQuadrant(){
  quadThr.x=parseFloat(el("qthr_x").value)||0;quadThr.y=parseFloat(el("qthr_y").value)||0;
  overlayScatter();sendQuadrantGate();
}
async function sendQuadrantGate(){
  if(quadSel.size===0)return;
  const gate={type:"quadrant",x:settings().scatter_x,y:settings().scatter_y,x_threshold:quadThr.x,y_threshold:quadThr.y,quadrants:[...quadSel]};
  await api("/api/gate/set",{index:activeIdx,gate_type:"scatter",gate:gate});
  SCATTER_GATES[String(activeIdx)]=gate;renderSamples();refresh();
}

/* analysis scatter */
function setAnalysisMode(mode){
  analysisMode=mode;
  el("am_polygon").classList.toggle("active",mode==="polygon");
  el("am_quadrant").classList.toggle("active",mode==="quadrant");
  el("apolygonUI").style.display=mode==="polygon"?"flex":"none";
  el("aquadrantUI").style.display=mode==="quadrant"?"block":"none";
  if(mode==="quadrant"&&ANALYSIS_META){
    if(aQuadThr.x===0){const xl=ANALYSIS_META.xlim,yl=ANALYSIS_META.ylim;aQuadThr.x=Math.sqrt(xl[0]*xl[1]);aQuadThr.y=Math.sqrt(yl[0]*yl[1]);el("aqthr_x").value=aQuadThr.x.toExponential(2);el("aqthr_y").value=aQuadThr.y.toExponential(2);}
    updateAnalysisQuadrantUI();
  }
  overlayAnalysis();
}
function overlayAnalysis(){
  const cv=el("analysiscv"),ctx=cv.getContext("2d");ctx.clearRect(0,0,cv.width,cv.height);
  if(!ANALYSIS_META)return;
  if(analysisMode==="polygon"&&aVerts.length){
    ctx.strokeStyle="#C44E52";ctx.lineWidth=1.5;ctx.beginPath();
    aVerts.forEach((v,i)=>{const[x,y]=toPx(ANALYSIS_META,v[0],v[1]);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});
    if(aClosed)ctx.closePath();ctx.stroke();
    ctx.fillStyle="#C44E52";aVerts.forEach(v=>{const[x,y]=toPx(ANALYSIS_META,v[0],v[1]);ctx.beginPath();ctx.arc(x,y,3,0,6.2832);ctx.fill();});
  }
  if(analysisMode==="quadrant"&&aQuadThr.x>0){
    const[qx,qy]=toPx(ANALYSIS_META,aQuadThr.x,aQuadThr.y);
    const img=el("analysisimg"),w=img.clientWidth,h=img.clientHeight;
    ctx.strokeStyle="#C44E52";ctx.lineWidth=1.5;ctx.setLineDash([5,3]);
    ctx.beginPath();ctx.moveTo(qx,(1-BBOX[1]-BBOX[3])*h);ctx.lineTo(qx,(1-BBOX[1])*h);ctx.stroke();
    ctx.beginPath();ctx.moveTo(BBOX[0]*w,qy);ctx.lineTo((BBOX[0]+BBOX[2])*w,qy);ctx.stroke();
    ctx.setLineDash([]);
    ctx.font="11px sans-serif";ctx.fillStyle="#C44E52";
    const labels={UL:[qx-15,qy-8],UR:[qx+8,qy-8],LL:[qx-15,qy+16],LR:[qx+8,qy+16]};
    for(const q of aQuadSel){const[lx,ly]=labels[q];ctx.fillText(q,lx,ly);}
  }
}
el("analysiscv").addEventListener("click",e=>{
  if(!ANALYSIS_META)return;
  if(analysisMode==="polygon"){
    if(aClosed){aVerts=[];aClosed=false;}
    const r=e.target.getBoundingClientRect();aVerts.push(toData(ANALYSIS_META,e.clientX-r.left,e.clientY-r.top));overlayAnalysis();
  }
});
el("analysiscv").addEventListener("dblclick",()=>{if(analysisMode==="polygon")closeAnalysisGate();});
async function closeAnalysisGate(){
  if(aVerts.length<3){banner("Need at least 3 corners.","err");return;}
  aClosed=true;overlayAnalysis();
  const gate={type:"polygon",x:settings().analysis_x,y:settings().analysis_y,verts:aVerts};
  await api("/api/gate/set",{index:activeIdx,gate_type:"analysis",gate:gate});
  for(let i=0;i<SAMPLES.length;i++)ANALYSIS_GATES[String(i)]=gate;
  renderSamples();refresh();
}
function undoAnalysisVertex(){aVerts.pop();aClosed=false;overlayAnalysis();}
async function clearAnalysisGate(){
  aVerts=[];aClosed=false;aQuadSel.clear();overlayAnalysis();
  for(let i=0;i<SAMPLES.length;i++)delete ANALYSIS_GATES[String(i)];
  await api("/api/gate/clear",{index:activeIdx,gate_type:"analysis"});
  renderSamples();refresh();
}
function toggleAnalysisQuadrant(q){if(aQuadSel.has(q))aQuadSel.delete(q);else aQuadSel.add(q);updateAnalysisQuadrantUI();sendAnalysisQuadrantGate();}
function updateAnalysisQuadrantUI(){for(const q of["UL","UR","LL","LR"])el("aq_"+q).classList.toggle("active",aQuadSel.has(q));}
async function updateAnalysisQuadrant(){
  aQuadThr.x=parseFloat(el("aqthr_x").value)||0;aQuadThr.y=parseFloat(el("aqthr_y").value)||0;
  overlayAnalysis();sendAnalysisQuadrantGate();
}
async function sendAnalysisQuadrantGate(){
  if(aQuadSel.size===0)return;
  const gate={type:"quadrant",x:settings().analysis_x,y:settings().analysis_y,x_threshold:aQuadThr.x,y_threshold:aQuadThr.y,quadrants:[...aQuadSel]};
  await api("/api/gate/set",{index:activeIdx,gate_type:"analysis",gate:gate});
  for(let i=0;i<SAMPLES.length;i++)ANALYSIS_GATES[String(i)]=gate;
  renderSamples();refresh();
}

/* histogram interval */
function toPxHist(x,yFrac){
  const img=el("histimg"),w=img.clientWidth,h=img.clientHeight,s=settings();
  const xl=parseFloat(s.xlim_lo),xh=parseFloat(s.xlim_hi);
  let fx; if(s.x_scale==="log"){fx=(Math.log10(x)-Math.log10(xl))/(Math.log10(xh)-Math.log10(xl));}
  else{fx=(x-xl)/(xh-xl);}
  return [(BBOX[0]+fx*BBOX[2])*w,(1-BBOX[1]-yFrac*BBOX[3])*h];
}
function toDataHistX(px){
  const img=el("histimg"),w=img.clientWidth,s=settings();
  const xl=parseFloat(s.xlim_lo),xh=parseFloat(s.xlim_hi);
  const fx=(px/w-BBOX[0])/BBOX[2];
  if(s.x_scale==="log")return 10**(Math.log10(xl)+fx*(Math.log10(xh)-Math.log10(xl)));
  return xl+fx*(xh-xl);
}
function overlayHist(){
  const cv=el("histcv"),ctx=cv.getContext("2d");ctx.clearRect(0,0,cv.width,cv.height);
  if(!histInterval||!HIST_META)return;
  const[lx,ly]=toPxHist(histInterval.lo,histInterval.y);
  const[rx,ry]=toPxHist(histInterval.hi,histInterval.y);
  ctx.strokeStyle="#C44E52";ctx.lineWidth=1.5;ctx.setLineDash([4,3]);
  ctx.beginPath();ctx.moveTo(lx,ly);ctx.lineTo(rx,ry);
  ctx.moveTo(lx,ly);ctx.lineTo(lx,ly+20);ctx.moveTo(rx,ry);ctx.lineTo(rx,ry+20);ctx.stroke();
  ctx.setLineDash([]);ctx.fillStyle="#C44E52";
  ctx.beginPath();ctx.arc(lx,ly,4,0,6.2832);ctx.fill();
  ctx.beginPath();ctx.arc(rx,ry,4,0,6.2832);ctx.fill();
}
el("histcv").addEventListener("mousedown",e=>{
  if(!HIST_META)return;
  const r=e.target.getBoundingClientRect(),px=e.clientX-r.left,py=e.clientY-r.top;
  if(histInterval){
    const[lx,ly]=toPxHist(histInterval.lo,histInterval.y);
    const[rx,ry]=toPxHist(histInterval.hi,histInterval.y);
    if(Math.hypot(px-lx,py-ly)<8){histDragging="left";return;}
    if(Math.hypot(px-rx,py-ry)<8){histDragging="right";return;}
    if(Math.abs(py-ly)<8&&px>Math.min(lx,rx)&&px<Math.max(lx,rx)){histDragging="line";return;}
  }
  const xval=toDataHistX(px);
  if(!histInterval||histInterval.lo===null){
    histInterval={lo:xval,hi:null,y:Math.max(0.1,Math.min(0.9,1-(py/r.height-BBOX[1])/BBOX[3]))};overlayHist();
  } else if(histInterval.hi===null){
    histInterval.hi=xval;if(histInterval.hi<histInterval.lo){[histInterval.lo,histInterval.hi]=[histInterval.hi,histInterval.lo];}
    sendHistGate();overlayHist();
  }
});
el("histcv").addEventListener("mousemove",e=>{
  if(!histDragging||!histInterval)return;
  const r=e.target.getBoundingClientRect(),px=e.clientX-r.left,py=e.clientY-r.top;
  const xval=toDataHistX(px);
  if(histDragging==="left")histInterval.lo=Math.min(xval,histInterval.hi);
  else if(histDragging==="right")histInterval.hi=Math.max(xval,histInterval.lo);
  else if(histDragging==="line")histInterval.y=Math.max(0.1,Math.min(0.9,1-(py/r.height-BBOX[1])/BBOX[3]));
  overlayHist();
});
el("histcv").addEventListener("mouseup",()=>{if(histDragging){histDragging=null;sendHistGate();}});
async function sendHistGate(){
  if(!histInterval||histInterval.hi===null)return;
  const gate={type:"interval",channel:settings().channel,lo:histInterval.lo,hi:histInterval.hi,y_pos:histInterval.y};
  await api("/api/gate/set",{index:activeIdx,gate_type:"histogram",gate:gate});
  HIST_GATES[String(activeIdx)]=gate;renderSamples();refresh();
}
async function clearHistGate(){
  histInterval=null;overlayHist();
  delete HIST_GATES[String(activeIdx)];
  await api("/api/gate/clear",{index:activeIdx,gate_type:"histogram"});
  renderSamples();refresh();
}

window.addEventListener("resize",()=>{if(SCATTER_META)sizeCanvas("scatter");if(HIST_META)sizeCanvas("hist");if(ANALYSIS_META)sizeCanvas("analysis");});

/* save */
async function save(){
  const j=await api("/api/save",{settings:settings(),scatter_index:activeIdx});
  let msg="Saved: "+j.pdf+"  |  "+j.png;
  if(j.scatter_pdf)msg+="  |  "+j.scatter_pdf;
  if(j.analysis_pdf)msg+="  |  "+j.analysis_pdf;
  if(j.xlsx)msg+="  |  "+j.xlsx;
  banner(msg,"ok"); el("snippet").textContent=j.snippet;
  el("card-snippet").classList.remove("collapsed");
}

/* init */
(async function init(){
  const j=await api("/api/init");
  SCHEMA=j.schema;DEFAULTS=j.defaults;SAMPLES=j.samples;CHANNELS=j.channels;
  SCATTER_GATES=j.scatter_gates||{};HIST_GATES=j.hist_gates||{};ANALYSIS_GATES=j.analysis_gates||{};
  buildSettings();renderSamples();initAxisLabels();refresh();
})();
</script>
</body>
</html>
"""
