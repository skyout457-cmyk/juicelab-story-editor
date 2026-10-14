'use strict';
const VERSION = 1, KEY = 'jl-story-editor-v1';
let CAT = null, S = null; // catalog, state {cur, autoFw, scenes:[{id,title,lines}]}
const $ = s => document.querySelector(s);
const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
const emptyLine = () => ({type: 'line', who: '', face: '', emote: '', text: ''});
const emptyAction = () => ({type: 'action', text: ''});
const isAct = l => l.type === 'action';
const newScene = t => ({id: uid(), title: t || '', lines: [emptyLine()]});
const FW = {'?': '？', '!': '！', ',': '，', ':': '：', ';': '；', '(': '（', ')': '）'};
const toFw = s => s.replace(/[?!,:;()]/g, c => FW[c]).replace(/\.\.\.+/g, '……');
const hasHalf = s => /[?!,:;()]|\.\.\./.test(s);

function load() {
  try { S = JSON.parse(localStorage.getItem(KEY)); } catch (e) { S = null; }
  if (!S || !Array.isArray(S.scenes) || !S.scenes.length) S = {cur: 0, autoFw: false, scenes: [newScene('新場景')]};
  if (S.cur >= S.scenes.length) S.cur = 0;
}
let saveT = 0;
function save() { clearTimeout(saveT); saveT = setTimeout(() => localStorage.setItem(KEY, JSON.stringify(S)), 250); }
const scene = () => S.scenes[S.cur];
const speaker = label => CAT.speakers.find(s => s.label === label);
function toast(m) { const t = $('#toast'); t.textContent = m; t.hidden = false; clearTimeout(t._t); t._t = setTimeout(() => t.hidden = true, 2600); }

function opt(v, label, sel) { const o = document.createElement('option'); o.value = v; o.textContent = label; if (v === sel) o.selected = true; return o; }
function el(tag, cls, kids) { const e = document.createElement(tag); if (cls) e.className = cls; (kids || []).forEach(k => e.append(k)); return e; }

function renderScenes() {
  const sel = $('#sceneSel'); sel.innerHTML = '';
  S.scenes.forEach((sc, i) => sel.append(opt(String(i), (sc.title || '（未命名）') + `（${sc.lines.length}行）`, String(S.cur))));
  $('#sceneTitle').value = scene().title; $('#autoFw').checked = !!S.autoFw;
}
function lineProblems(l) {
  if (isAct(l)) return hasHalf(l.text) ? ['有半形標點'] : [];
  const p = [], sp = speaker(l.who);
  if (!sp) p.push('請選「誰」');
  else if (sp.faces.length && !sp.faces.some(f => f.key === l.face)) p.push('請選表情');
  if (hasHalf(l.text)) p.push('有半形標點（？！，：；（）……要用全形）');
  if (sp && sp.kind === 'narration' && l.text && !/^（.*）$/s.test(l.text.trim())) p.push('旁白要用全形括號（）包住');
  return p;
}
function renderLines() {
  const ol = $('#lines'); ol.innerHTML = '';
  scene().lines.forEach((l, i) => ol.append(lineCard(l, i)));
  renderScenes();
}
function lineCard(l, i) {
  if (isAct(l)) return actionCard(l, i);
  const sp = speaker(l.who), li = el('li', 'line' + (sp && sp.kind === 'narration' ? ' narr' : ''));
  li.append(el('div', 'num', [`第 ${i + 1} 行`]));
  const who = document.createElement('select'); who.append(opt('', '誰？（必選）', l.who));
  CAT.speakers.forEach(s => who.append(opt(s.label, s.label, l.who)));
  const face = document.createElement('select');
  if (sp && !sp.faces.length) { face.append(opt('', '（旁白沒有表情）', '')); face.disabled = true; }
  else { face.append(opt('', sp ? '表情（必選）' : '先選誰', l.face)); (sp ? sp.faces : []).forEach(f => face.append(opt(f.key, f.key + (f.note ? '（' + f.note + '）' : ''), l.face))); }
  const emo = document.createElement('select'); emo.append(opt('', '表符（不用）', l.emote));
  CAT.emotes.forEach(e => emo.append(opt(e.label.replace(/ #\d+$/, '').replace(/^#\d+（未命名）$/, '#' + e.n), e.label, l.emote)));
  if (sp && sp.kind === 'narration') { emo.value = ''; emo.disabled = true; }
  const tx = document.createElement('textarea'); tx.value = l.text; tx.placeholder = sp && sp.kind === 'narration' ? '（旁白內容）' : '說了什麼';
  const warn = el('div', 'warn');
  const check = () => { const p = lineProblems(l); warn.textContent = p.join('、'); li.classList.toggle('bad', p.length > 0 && !!(l.who || l.text)); };
  who.onchange = () => { l.who = who.value; const s = speaker(l.who); if (!s || !s.faces.some(f => f.key === l.face)) l.face = ''; if (s && s.kind === 'narration') { l.emote = ''; if (!l.text) l.text = '（）'; } save(); renderLines(); };
  face.onchange = () => { l.face = face.value; save(); check(); };
  emo.onchange = () => { l.emote = emo.value; save(); };
  tx.oninput = () => { if (S.autoFw && hasHalf(tx.value)) { const p = tx.selectionStart; tx.value = toFw(tx.value); tx.setSelectionRange(p, p); } l.text = tx.value; save(); check(); };
  const lab = (t, c) => { const w = el('label', '', [t]); w.append(c); return w; };
  li.append(el('div', 'row', [lab('誰', who), lab('表情', face)]), el('div', 'row', [lab('表符', emo), el('div')]), tx, warn);
  cardTools(l, i, li);
  check(); return li;
}

function cardTools(l, i, li) {
  const L = scene().lines, b = (t, f, cls) => { const x = el('button', cls, [t]); x.onclick = () => { f(); save(); renderLines(); }; return x; };
  li.append(el('div', 'tools', [
    b('↑', () => { if (i > 0) [L[i - 1], L[i]] = [L[i], L[i - 1]]; }),
    b('↓', () => { if (i < L.length - 1) [L[i + 1], L[i]] = [L[i], L[i + 1]]; }),
    b('插入', () => L.splice(i + 1, 0, isAct(l) ? emptyAction() : {...emptyLine(), who: l.who, face: l.face})),
    b('複製', () => L.splice(i + 1, 0, {...l})),
    b('刪除', () => { if (confirm(`刪除第 ${i + 1} 行？`)) { L.splice(i, 1); if (!L.length) L.push(emptyLine()); } }, 'danger')]));
}
function actionCard(l, i) {
  const li = el('li', 'line act');
  li.append(el('div', 'num', [`🎬 動作卡・第 ${i + 1} 行`]));
  const tx = document.createElement('textarea'); tx.value = l.text; tx.placeholder = '鏡頭、走位、人物動作……';
  const warn = el('div', 'warn');
  tx.oninput = () => { if (S.autoFw && hasHalf(tx.value)) { const p = tx.selectionStart; tx.value = toFw(tx.value); tx.setSelectionRange(p, p); } l.text = tx.value; save(); warn.textContent = lineProblems(l).join('、'); };
  li.append(tx, warn); warn.textContent = lineProblems(l).join('、'); cardTools(l, i, li); return li;
}
function exportObj() {
  const sc = scene();
  return {format: 'juicelab-story-editor-1', version: VERSION, exported: new Date().toISOString(),
    scene: {id: sc.id, title: sc.title}, lines: sc.lines.filter(l => isAct(l) ? l.text.trim() : (l.who || l.text)).map(l => isAct(l) ? {type: 'action', text: l.text} : {type: 'line', who: l.who, face: l.face, emote: l.emote, text: l.text})};
}
async function doSave() {
  const sc = scene(), o = exportObj(), bad = o.lines.filter(l => lineProblems(l).length).length;
  if (bad && !confirm(`有 ${bad} 行還有問題（紅框），還是要存嗎？`)) return;
  const name = ((sc.title || 'scene').replace(/[\\/:*?"<>|\s]+/g, '_')) + '.json';
  const file = new File([JSON.stringify(o, null, 1)], name, {type: 'application/json'});
  if (navigator.canShare && navigator.canShare({files: [file]})) {
    try { await navigator.share({files: [file]}); toast('已開啟分享，選「雲端硬碟」→「JuiceLab 劇情編輯」'); return; }
    catch (e) { if (e.name === 'AbortError') return; }
  }
  const a = document.createElement('a'); a.href = URL.createObjectURL(file); a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000); toast('已下載 ' + name);
}
function doImport(f) {
  const r = new FileReader();
  r.onload = () => { try {
    const o = JSON.parse(r.result); if (!o || !Array.isArray(o.lines)) throw 0;
    const sc = {id: (o.scene && o.scene.id) || uid(), title: (o.scene && o.scene.title) || f.name.replace(/\.json$/, ''),
      lines: o.lines.map(l => l.type === 'action' ? {type: 'action', text: l.text || ''} : {type: 'line', who: l.who || '', face: l.face || '', emote: l.emote || '', text: l.text || ''})};
    if (!sc.lines.length) sc.lines.push(emptyLine());
    const i = S.scenes.findIndex(s => s.id === sc.id);
    if (i >= 0 && confirm('已經有這個場景，要覆蓋嗎？（取消＝另存成新場景）')) S.scenes[i] = sc, S.cur = i;
    else { if (i >= 0) sc.id = uid(); S.scenes.push(sc); S.cur = S.scenes.length - 1; }
    save(); renderLines(); toast('已開啟：' + sc.title);
  } catch (e) { toast('這個檔案不是劇情檔'); } };
  r.readAsText(f);
}

function bind() {
  $('#sceneSel').onchange = e => { S.cur = +e.target.value; save(); renderLines(); };
  $('#sceneTitle').oninput = e => { scene().title = e.target.value; save(); renderScenes(); };
  $('#newScene').onclick = () => { S.scenes.push(newScene('新場景 ' + (S.scenes.length + 1))); S.cur = S.scenes.length - 1; save(); renderLines(); $('#sceneTitle').focus(); };
  $('#menuBtn').onclick = () => $('#menu').hidden = !$('#menu').hidden;
  $('#renameScene').onclick = () => { $('#menu').hidden = true; $('#sceneTitle').focus(); };
  $('#dupScene').onclick = () => { const c = JSON.parse(JSON.stringify(scene())); c.id = uid(); c.title += '（複製）'; S.scenes.push(c); S.cur = S.scenes.length - 1; save(); renderLines(); $('#menu').hidden = true; };
  $('#delScene').onclick = () => { if (!confirm(`刪除場景「${scene().title}」？`)) return; S.scenes.splice(S.cur, 1); if (!S.scenes.length) S.scenes.push(newScene('新場景')); S.cur = 0; save(); renderLines(); $('#menu').hidden = true; };
  $('#autoFw').onchange = e => { S.autoFw = e.target.checked; if (S.autoFw) scene().lines.forEach(l => l.text = toFw(l.text)); save(); renderLines(); };
  $('#addLine').onclick = () => { const L = scene().lines, last = [...L].reverse().find(x => !isAct(x)) || {}; L.push({...emptyLine(), who: last.who || '', face: last.face || ''}); save(); renderLines(); window.scrollTo(0, document.body.scrollHeight); };
  $('#addAct').onclick = () => { scene().lines.push(emptyAction()); save(); renderLines(); window.scrollTo(0, document.body.scrollHeight); };
  $('#saveBtn').onclick = doSave;
  $('#importBtn').onclick = () => $('#fileIn').click();
  $('#fileIn').onchange = e => { if (e.target.files[0]) doImport(e.target.files[0]); e.target.value = ''; };
}
async function start() {
  try { CAT = await (await fetch('catalog.json', {cache: 'no-cache'})).json(); }
  catch (e) { document.body.innerHTML = '<p style="padding:20px">讀不到 catalog.json，請連上網路再開一次。</p>'; return; }
  $('#ver').textContent = `資料：${CAT.speakers.map(s => s.label + ' ' + s.faces.length + ' 表情').join('、')}、表符 ${CAT.emotes.length} 個`;
  load(); bind(); renderLines();
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js');
}
start();
