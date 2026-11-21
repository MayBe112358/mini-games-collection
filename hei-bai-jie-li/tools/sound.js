/* ===== 声音：生成式背景音乐 + 音效（Web Audio 实时合成，无外部文件） ===== */
const Sound = (() => {
  // 五档难度各一种情绪：根音(MIDI)、音阶、和弦进行(相对根音的半音)、速度、亮度、旋律密度
  const MOODS = [
    { root: 62, scale: [0, 2, 4, 7, 9], bpm: 76, bright: 2600, dens: .42,          // 入门：D 大调五声，明亮
      prog: [[0, 4, 7, 11], [-3, 0, 4, 7], [-7, -3, 0, 4], [-5, -1, 2, 7]] },
    { root: 65, scale: [0, 2, 4, 7, 9], bpm: 72, bright: 2200, dens: .40,          // 简单：F 大调，柔和
      prog: [[0, 4, 7, 14], [-5, -1, 2, 7], [-3, 0, 4, 9], [-7, -3, 0, 7]] },
    { root: 57, scale: [0, 2, 3, 7, 9], bpm: 68, bright: 1900, dens: .36,          // 中等：A 多利亚，若有所思
      prog: [[0, 3, 7, 10], [-2, 2, 5, 9], [5, 9, 12, 16], [3, 7, 10, 14]] },
    { root: 52, scale: [0, 2, 3, 7, 8], bpm: 64, bright: 1600, dens: .32,          // 困难：E 小调，紧张
      prog: [[0, 3, 7, 14], [-4, 0, 3, 8], [-7, -4, 0, 3], [-5, -2, 2, 7]] },
    { root: 50, scale: [0, 1, 5, 7, 10], bpm: 58, bright: 1300, dens: .28,         // 大师：D 日本都节调式，空灵深沉
      prog: [[0, 7, 12, 15], [1, 5, 8, 13], [-2, 5, 10, 14], [0, 5, 7, 12]] },
  ];
  const GAIN = 3;                                          // 整体响度补偿（各声部本身很轻）
  const hz = m => 440 * Math.pow(2, (m - 69) / 12);

  let ctx = null, master, music, sfx, delayIn, timer = null;
  const LEVEL = { music: .55, sfx: .8 };
  let mood = MOODS[0], moodIdx = 0, step = 0, nextT = 0, melPos = 2, lastNote = 0;
  let cfg = { music: true, sfx: true, vol: .7 };

  function build(c) {
    ctx = c;
    master = ctx.createGain(); master.gain.value = cfg.vol * GAIN;
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -16; comp.ratio.value = 4; comp.attack.value = .01; comp.release.value = .3;
    master.connect(comp); comp.connect(ctx.destination);

    // 混响：用衰减噪声生成冲激响应
    const len = Math.floor(ctx.sampleRate * 3.2), ir = ctx.createBuffer(2, len, ctx.sampleRate);
    for (let ch = 0; ch < 2; ch++) { const d = ir.getChannelData(ch); let s = 12345 + ch * 777;
      for (let i = 0; i < len; i++) { s = (s * 16807) % 2147483647; d[i] = ((s / 2147483647) * 2 - 1) * Math.pow(1 - i / len, 2.6); } }
    // 音乐和音效各走一条总线，干声和混响都在总线开关之后，关掉就彻底没声
    const bus = on => { const out = ctx.createGain(), inp = ctx.createGain(), wetIn = ctx.createGain(), conv = ctx.createConvolver();
      out.gain.value = on; conv.buffer = ir; wetIn.gain.value = .5;
      inp.connect(out); wetIn.connect(conv); conv.connect(out); out.connect(master);
      return { in: inp, wetIn, out }; };
    music = bus(cfg.music ? LEVEL.music : 0); sfx = bus(cfg.sfx ? LEVEL.sfx : 0);
    // 乒乓式回声：给旋律一点空间感
    delayIn = ctx.createGain(); const dl = ctx.createDelay(2), fb = ctx.createGain(), lp = ctx.createBiquadFilter();
    dl.delayTime.value = 60 / mood.bpm * .75; fb.gain.value = .32; lp.type = 'lowpass'; lp.frequency.value = 2400;
    delayIn.connect(dl); dl.connect(lp); lp.connect(fb); fb.connect(dl); lp.connect(music.in); lp.connect(music.wetIn);
    delayIn._dl = dl;
  }

  /* --- 乐器 --- */
  function voice(dest, f, t, dur, { type = 'sine', att = .01, peak = .2, rel = 1, det = 0, send = .3, cutoff = 0 } = {}) {
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type; o.frequency.value = f; o.detune.value = det;
    const bus = dest.in ? dest : null; dest = bus ? bus.in : dest;
    let out = g;
    if (cutoff) { const fl = ctx.createBiquadFilter(); fl.type = 'lowpass'; fl.frequency.value = cutoff; fl.Q.value = .3; g.connect(fl); out = fl; }
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(peak, t + att);
    g.gain.setValueAtTime(peak, t + Math.max(att, dur));
    g.gain.exponentialRampToValueAtTime(.0001, t + Math.max(att, dur) + rel);
    o.connect(g); out.connect(dest);
    if (send && bus) { const s = ctx.createGain(); s.gain.value = send; out.connect(s); s.connect(bus.wetIn); }
    o.start(t); o.stop(t + Math.max(att, dur) + rel + .05);
  }
  function pluck(dest, m, t, vel = 1, send = .35) {      // 拨弦/钟琴般的音色
    const f = hz(m);
    voice(dest, f, t, 0, { type: 'sine', att: .005, peak: .16 * vel, rel: 1.6, send });
    voice(dest, f * 2, t, 0, { type: 'sine', att: .003, peak: .035 * vel, rel: .5, send: 0 });
    voice(dest, f, t, 0, { type: 'triangle', att: .004, peak: .04 * vel, rel: .25, det: 4, send: 0 });
  }
  function pad(m, t, dur) {                               // 柔和的长音铺底
    for (const det of [-7, 7]) voice(music, hz(m), t, dur, { type: 'triangle', att: 2.2, peak: .022, rel: 3, det, send: .6, cutoff: mood.bright * .5 });
  }

  /* --- 作曲：每个八分音符排一次 --- */
  function scheduleStep(t) {
    const spb = 60 / mood.bpm, chord = mood.prog[Math.floor(step / 16) % mood.prog.length];
    if (step % 16 === 0) {
      const dur = spb * 8;
      chord.forEach(n => pad(mood.root - 12 + n, t, dur));
      voice(music, hz(mood.root - 24 + chord[0]), t, dur * .6, { type: 'sine', att: .8, peak: .09, rel: 2.5, send: .2 });
    }
    // 旋律：在音阶上随机游走，强拍更容易出音
    const strong = step % 4 === 0 ? 1.6 : step % 2 === 0 ? 1 : .55;
    if (Math.random() < mood.dens * strong && t - lastNote > spb * .45) {
      melPos += [-2, -1, -1, 0, 1, 1, 2][Math.floor(Math.random() * 7)];
      melPos = Math.max(0, Math.min(9, melPos));
      const sc = mood.scale, m = mood.root + sc[melPos % sc.length] + 12 * Math.floor(melPos / sc.length);
      pluck(music, m, t, .55 + Math.random() * .35); lastNote = t;
      if (Math.random() < .35) { const s = ctx.createGain(); s.gain.value = .5; s.connect(delayIn); pluck(s, m, t, .4, 0); }
    }
    step++;
  }
  function tick() {
    if (!ctx) return;
    const spb = 60 / mood.bpm / 2;
    if (nextT < ctx.currentTime) nextT = ctx.currentTime + .05;
    // 音乐关掉时不再排音符，只让节拍继续走（音效取和弦还要用）
    while (nextT < ctx.currentTime + .35) { if (cfg.music) scheduleStep(nextT); else step++; nextT += spb; }
  }

  /* --- 对外接口 --- */
  function ensure() {                       // 必须在用户手势里调用（浏览器自动播放限制）
    if (!ctx) {
      const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return;
      try { build(new AC()); } catch (e) { return; }
      timer = setInterval(tick, 100);
    }
    if (ctx.state === 'suspended' && !document.hidden && (cfg.music || cfg.sfx)) ctx.resume().catch(() => {});
  }
  function setMood(i) {
    if (i === moodIdx && ctx) return;
    moodIdx = i; mood = MOODS[i] || MOODS[0];
    step = 0; melPos = 2;
    if (delayIn) delayIn._dl.delayTime.setTargetAtTime(60 / mood.bpm * .75, ctx.currentTime, .5);
  }
  function setCfg(c) {
    cfg = { ...cfg, ...c };
    if (!ctx) return;
    const now = ctx.currentTime;
    master.gain.setTargetAtTime(cfg.vol * GAIN, now, .05);
    music.out.gain.setTargetAtTime(cfg.music ? LEVEL.music : 0, now, .08);
    sfx.out.gain.setTargetAtTime(cfg.sfx ? LEVEL.sfx : 0, now, .03);
    if (!cfg.music && !cfg.sfx) setTimeout(() => { if (!cfg.music && !cfg.sfx) ctx.suspend().catch(() => {}); }, 400);
    else if (ctx.state === 'suspended' && !document.hidden) ctx.resume().catch(() => {});
  }
  const chordNow = () => mood.prog[Math.floor(Math.max(0, step - 1) / 16) % mood.prog.length];
  const now = () => ctx.currentTime + .01;
  const ok = () => {
    if (!ctx || !cfg.sfx || document.hidden) return false;
    if (ctx.state === 'suspended') ctx.resume().catch(() => {});   // 刚从全关切回来时先唤醒
    return true; };
  const fx = {
    // 黑走低音、白走高音，音高取自当前和弦，和背景音乐始终协和
    move(isWhite) { if (!ok()) return; const c = chordNow(), n = c[Math.floor(Math.random() * c.length)];
      pluck(sfx, mood.root + n + (isWhite ? 12 : -12), now(), .7, .25); },
    star() { if (!ok()) return; const c = chordNow(), t = now();
      [0, 1, 2, 3].forEach((k, j) => pluck(sfx, mood.root + 12 + c[k % c.length] + (k > 2 ? 12 : 0), t + j * .07, .8, .5)); },
    bad() { if (!ok()) return; const t = now();
      voice(sfx, 110, t, 0, { type: 'sine', att: .005, peak: .25, rel: .18, send: 0 });
      voice(sfx, 82, t, 0, { type: 'triangle', att: .005, peak: .12, rel: .14, send: 0, cutoff: 400 }); },
    stuck() { if (!ok()) return; const t = now(), r = mood.root;
      pluck(sfx, r + 3, t, .7); pluck(sfx, r - 2, t + .22, .7); pluck(sfx, r - 9, t + .44, .8); },
    undo() { if (!ok()) return; pluck(sfx, mood.root + mood.scale[1] + 12, now(), .35, .2); },
    win(stars) { if (!ctx || document.hidden || (!cfg.music && !cfg.sfx)) return;
      if (ctx.state === 'suspended') ctx.resume().catch(() => {});
      const t = now(), c = chordNow();
      music.out.gain.setTargetAtTime(cfg.music ? .15 : 0, t, .1);      // 过关时音乐让一让
      music.out.gain.setTargetAtTime(cfg.music ? LEVEL.music : 0, t + 2.6, .8);
      if (!cfg.sfx) return;
      const notes = [0, 1, 2, 3, 0, 1, 2, 3].map((k, j) => mood.root + c[k] + (j > 3 ? 12 : 0));
      notes.slice(0, 5 + stars).forEach((m, j) => pluck(sfx, m, t + j * .09, .75, .55));
      if (stars === 3) setTimeout(() => fx.star(), 750); },
  };
  document.addEventListener('visibilitychange', () => {
    if (!ctx) return;
    if (document.hidden) ctx.suspend().catch(() => {}); else if (cfg.music || cfg.sfx) ctx.resume().catch(() => {});
  });
  // 给离线渲染测试用：在 OfflineAudioContext 上排好一段音乐
  function renderInto(offCtx, moodI, seconds) {
    build(offCtx); setMood(moodI); moodIdx = moodI; mood = MOODS[moodI]; step = 0; nextT = .05;
    const spb = 60 / mood.bpm / 2;
    while (nextT < seconds - 4) { scheduleStep(nextT); nextT += spb; }
  }
  return { ensure, setMood, setCfg, fx, renderInto, get cfg() { return cfg; }, get state() { return ctx ? ctx.state : 'none'; } };
})();
