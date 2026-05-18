// ═══════════════════════════════════════════════════
//  PERSISTENCE
// ═══════════════════════════════════════════════════
const S = {
  get: k  => localStorage.getItem(`vcal_${k}`) ?? '',
  set: (k,v) => localStorage.setItem(`vcal_${k}`, v),
  getJSON: (k, def=[]) => { try { return JSON.parse(localStorage.getItem(`vcal_${k}`)) ?? def } catch { return def } },
  setJSON: (k,v) => localStorage.setItem(`vcal_${k}`, JSON.stringify(v)),
};

// ═══════════════════════════════════════════════════
//  CALENDAR COLORS  (assigned per name)
// ═══════════════════════════════════════════════════
const CAL_NAMED = {
  gym:['#10B981','rgba(16,185,129,.12)'],       workout:['#10B981','rgba(16,185,129,.12)'],
  fitness:['#10B981','rgba(16,185,129,.12)'],    sport:['#10B981','rgba(16,185,129,.12)'],
  exams:['#EF4444','rgba(239,68,68,.12)'],       exam:['#EF4444','rgba(239,68,68,.12)'],
  test:['#EF4444','rgba(239,68,68,.12)'],
  work:['#3B82F6','rgba(59,130,246,.12)'],       office:['#3B82F6','rgba(59,130,246,.12)'],
  class:['#F59E0B','rgba(245,158,11,.12)'],      school:['#F59E0B','rgba(245,158,11,.12)'],
  university:['#F59E0B','rgba(245,158,11,.12)'],
  personal:['#8B5CF6','rgba(139,92,246,.12)'],   home:['#8B5CF6','rgba(139,92,246,.12)'],
  family:['#EC4899','rgba(236,72,153,.12)'],
};
let googleCalColors = {}; // populated from /calendars endpoint

function calColor(name) {
  if (!name) return ['#14B8A6','rgba(20,184,166,.12)'];
  if (googleCalColors[name]) return [googleCalColors[name], googleCalColors[name]+'22'];
  const k = name.toLowerCase();
  for (const [n,v] of Object.entries(CAL_NAMED)) if (k.includes(n)) return v;
  let h = 0;
  for (let i=0;i<k.length;i++) h=((h<<5)-h+k.charCodeAt(i))|0;
  const hue = ((Math.abs(h)%12)+1)*30;
  return [`hsl(${hue},65%,55%)`, `hsl(${hue},65%,55%,.12)`];
}

// ═══════════════════════════════════════════════════
//  THEME
// ═══════════════════════════════════════════════════
const Theme = {
  init() {
    const stored = S.get('theme') || 'dark';
    this.apply(stored);
    this._sync(stored);
    window.matchMedia('(prefers-color-scheme:dark)').addEventListener('change', ()=>{
      if (S.get('theme')==='system') this.apply('system');
    });
  },
  apply(mode) {
    const r = mode==='system'
      ? (window.matchMedia('(prefers-color-scheme:light)').matches ? 'light':'dark')
      : mode;
    document.documentElement.setAttribute('data-theme', r);
    document.getElementById('themeColorMeta').content = r==='light' ? '#F8FAFC':'#070B14';
    document.getElementById('iSun').classList.toggle('hidden', r==='light');
    document.getElementById('iMoon').classList.toggle('hidden', r==='dark');
  },
  set(mode) { S.set('theme', mode); this.apply(mode); this._sync(mode); },
  toggle() { const c=document.documentElement.getAttribute('data-theme'); this.set(c==='dark'?'light':'dark'); },
  _sync(mode) {
    document.querySelectorAll('[data-tv]').forEach(b=>b.classList.toggle('active', b.dataset.tv===mode));
  }
};

// ═══════════════════════════════════════════════════
//  TOASTS
// ═══════════════════════════════════════════════════
function toast(msg, type='info', ms=3200) {
  const wrap = document.getElementById('toastWrap');
  const el   = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span class="toast-dot"></span>${esc(msg)}`;
  wrap.appendChild(el);
  const rm = () => { el.classList.add('removing'); el.addEventListener('animationend',()=>el.remove(),{once:true}); };
  const t = setTimeout(rm, ms);
  el.addEventListener('click', ()=>{ clearTimeout(t); rm(); });
}

// ═══════════════════════════════════════════════════
//  CONFETTI
// ═══════════════════════════════════════════════════
const Confetti = (() => {
  const canvas = document.getElementById('confettiCanvas');
  const ctx    = canvas.getContext('2d');
  let particles=[], running=false, animId;

  function fire() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    canvas.style.display = 'block';
    const colors = ['#14B8A6','#FFFFFF','#F97316','#A78BFA','#34D399','#FCD34D'];
    particles = Array.from({length:90}, ()=>({
      x: canvas.width/2 + (Math.random()-.5)*canvas.width*.5,
      y: canvas.height*.65,
      vx:(Math.random()-.5)*10,
      vy:-(Math.random()*10+5),
      color:colors[Math.floor(Math.random()*colors.length)],
      size:Math.random()*7+3,
      rot:Math.random()*Math.PI*2,
      rotS:(Math.random()-.5)*.25,
      a:1,
      shape:Math.random()>.5?'r':'c'
    }));
    if (!running) { running=true; draw(); }
    setTimeout(stop, 2800);
  }

  function draw() {
    if (!running) return;
    animId = requestAnimationFrame(draw);
    ctx.clearRect(0,0,canvas.width,canvas.height);
    particles.forEach(p=>{
      p.x+=p.vx; p.y+=p.vy; p.vy+=.25;
      p.rot+=p.rotS; p.a=Math.max(0,p.a-.007);
      ctx.save(); ctx.globalAlpha=p.a; ctx.fillStyle=p.color;
      ctx.translate(p.x,p.y); ctx.rotate(p.rot);
      if (p.shape==='r') ctx.fillRect(-p.size/2,-p.size/4,p.size,p.size/2);
      else { ctx.beginPath();ctx.arc(0,0,p.size/2,0,Math.PI*2);ctx.fill(); }
      ctx.restore();
    });
  }

  function stop() {
    running=false; cancelAnimationFrame(animId);
    ctx.clearRect(0,0,canvas.width,canvas.height);
    canvas.style.display='none';
  }

  return { fire };
})();

// ═══════════════════════════════════════════════════
//  WAVEFORM (canvas — idle sine + recording bars)
// ═══════════════════════════════════════════════════
const Wave = (() => {
  const canvas = document.getElementById('waveCanvas');
  const ctx    = canvas.getContext('2d');
  let analyser=null, animId, mode='idle';

  function resize() {
    const dpr=devicePixelRatio||1, r=canvas.getBoundingClientRect();
    canvas.width=r.width*dpr; canvas.height=r.height*dpr;
    ctx.setTransform(dpr,0,0,dpr,0,0);
  }

  function primary() {
    return getComputedStyle(document.documentElement).getPropertyValue('--primary').trim();
  }

  function draw() {
    animId = requestAnimationFrame(draw);
    const W=canvas.getBoundingClientRect().width, H=canvas.getBoundingClientRect().height;
    if (!W) return;
    ctx.clearRect(0,0,W,H);

    if (mode==='recording' && analyser) {
      const data=new Uint8Array(analyser.frequencyBinCount);
      analyser.getByteFrequencyData(data);
      const bars=28, gap=3, bw=(W-(bars-1)*gap)/bars;
      for (let i=0;i<bars;i++) {
        const v=data[Math.floor(i*data.length/bars)]/255;
        const bh=Math.max(2,v*H*.82);
        const x=i*(bw+gap), y=(H-bh)/2;
        ctx.globalAlpha=.5+v*.5;
        ctx.fillStyle=primary();
        _rr(x,y,bw,bh,Math.min(bw/2,4));
        ctx.fill();
      }
    } else {
      // Idle: gentle sine wave
      const t=Date.now()/1600;
      ctx.strokeStyle=primary();
      ctx.lineWidth=1.5;
      ctx.globalAlpha=.25+Math.sin(t)*.08;
      ctx.beginPath();
      for (let x=0;x<=W;x+=2) {
        const y=H/2+Math.sin(x/W*Math.PI*5+t)*H*.12;
        x===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
      }
      ctx.stroke();
    }
  }

  function _rr(x,y,w,h,r) {
    ctx.beginPath();
    ctx.moveTo(x+r,y);ctx.lineTo(x+w-r,y);ctx.quadraticCurveTo(x+w,y,x+w,y+r);
    ctx.lineTo(x+w,y+h-r);ctx.quadraticCurveTo(x+w,y+h,x+w-r,y+h);
    ctx.lineTo(x+r,y+h);ctx.quadraticCurveTo(x,y+h,x,y+h-r);
    ctx.lineTo(x,y+r);ctx.quadraticCurveTo(x,y,x+r,y);
    ctx.closePath();
  }

  function start(stream) {
    const ac=new (window.AudioContext||window.webkitAudioContext)();
    analyser=ac.createAnalyser(); analyser.fftSize=64;
    ac.createMediaStreamSource(stream).connect(analyser);
    mode='recording';
  }

  function stop() { mode='idle'; analyser=null; }

  function init() {
    resize();
    new ResizeObserver(resize).observe(canvas);
    draw();
  }

  return { init, start, stop };
})();

// ═══════════════════════════════════════════════════
//  RECORDING
// ═══════════════════════════════════════════════════
let mediaRecorder=null, audioChunks=[], isRecording=false;
let recordedBlob=null, recordedMime='';
let timerInterval=null, timerSecs=0;

async function toggleRecord() {
  if (navigator.vibrate) navigator.vibrate(10);
  isRecording ? stopRecording() : await startRecording();
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({audio:true});
    const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')?'audio/webm;codecs=opus'
               : MediaRecorder.isTypeSupported('audio/webm')?'audio/webm':'audio/mp4';
    mediaRecorder = new MediaRecorder(stream, {mimeType:mime});
    audioChunks=[];
    mediaRecorder.ondataavailable = e=>{ if(e.data.size>0) audioChunks.push(e.data); };
    mediaRecorder.onstop = ()=>{
      recordedMime=mime;
      recordedBlob=new Blob(audioChunks,{type:mime});
      stream.getTracks().forEach(t=>t.stop());
      stopTimer();
      Wave.stop();
      setRecUI('ready');
      if (document.getElementById('autoSubmitToggle').checked) {
        setTimeout(handleSubmit, 500);
      }
    };
    mediaRecorder.start(200);
    isRecording=true;
    Wave.start(stream);
    startTimer();
    setRecUI('recording');
  } catch {
    toast('Microphone access denied — allow it in browser settings.', 'error');
  }
}

function stopRecording() {
  if (mediaRecorder && isRecording) { mediaRecorder.stop(); isRecording=false; }
}

function startTimer() {
  timerSecs=0;
  timerInterval=setInterval(()=>{
    timerSecs++;
    const m=Math.floor(timerSecs/60), s=timerSecs%60;
    document.getElementById('recTimer').textContent=`${m}:${s.toString().padStart(2,'0')}`;
  },1000);
}
function stopTimer() { clearInterval(timerInterval); timerInterval=null; }

function setRecUI(state) {
  const card=document.getElementById('recCard');
  const btn=document.getElementById('micBtn');
  const st=document.getElementById('micStatus');
  card.classList.remove('recording','ready');
  if (state==='recording') {
    card.classList.add('recording');
    btn.textContent='⏹'; btn.setAttribute('aria-label','Stop recording');
    st.textContent='Recording — tap to stop';
  } else if (state==='ready') {
    card.classList.add('ready');
    btn.textContent='🎤'; btn.setAttribute('aria-label','Record');
    st.textContent='✓ Recording ready';
    if (navigator.vibrate) navigator.vibrate([10,50,10]);
  } else {
    btn.textContent='🎤'; btn.setAttribute('aria-label','Record');
    st.textContent='Tap to record';
    document.getElementById('recTimer').textContent='0:00';
  }
}

// ═══════════════════════════════════════════════════
//  OFFLINE QUEUE
// ═══════════════════════════════════════════════════
function setOffline(offline) {
  document.getElementById('offlineBanner').classList.toggle('show', offline);
}

window.addEventListener('online',  ()=>{ setOffline(false); flushQueue(); });
window.addEventListener('offline', ()=> setOffline(true));

async function flushQueue() {
  const q = S.getJSON('queue', []);
  if (!q.length) return;
  toast(`Sending ${q.length} queued event(s)…`, 'info');
  S.setJSON('queue', []);
  for (const item of q) {
    try {
      const form = new FormData();
      form.append('text', item.text);
      form.append('timezone', item.timezone);
      form.append('secret', item.secret);
      form.append('default_reminder', item.default_reminder);
      await fetch('/parse', {method:'POST', body:form});
    } catch {}
  }
  toast('Queued events sent!', 'success');
}

// ═══════════════════════════════════════════════════
//  SUBMIT
// ═══════════════════════════════════════════════════
async function handleSubmit() {
  const text   = document.getElementById('textInput').value.trim();
  const secret = document.getElementById('pwInput').value.trim();
  const tz     = S.get('timezone') || Intl.DateTimeFormat().resolvedOptions().timeZone;
  const reminder = document.getElementById('sReminder')?.value || '30';

  if (!text && !recordedBlob) { toast('Record a voice note or type first.','info'); return; }

  // Offline: queue text-only requests
  if (!navigator.onLine && !recordedBlob) {
    const q = S.getJSON('queue', []);
    q.push({text, timezone:tz, secret, default_reminder:reminder});
    S.setJSON('queue', q);
    toast('You\'re offline — event queued for when you reconnect.', 'warn');
    document.getElementById('textInput').value='';
    return;
  }

  setLoading(true, recordedBlob ? 'Transcribing audio…' : 'Parsing with AI…');
  clearResults();

  try {
    const form = new FormData();
    if (recordedBlob) {
      const ext=recordedMime.includes('mp4')?'m4a':'webm';
      form.append('audio', recordedBlob, `recording.${ext}`);
      setLoading(true,'Transcribing, then creating events…');
    } else {
      form.append('text', text);
    }
    form.append('timezone', tz);
    form.append('default_reminder', reminder);
    if (secret) form.append('secret', secret);

    const res  = await fetch('/parse', {method:'POST', body:form});
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error||'Server error');

    renderResults(data);
    const n = data.created?.length||0;
    if (n>0) {
      Confetti.fire();
      if (navigator.vibrate) navigator.vibrate([15,50,15,50,25]);
      toast(`${n} item${n>1?'s':''} added to your calendar 🎉`, 'success', 4000);
    }

    // Reset
    recordedBlob=null;
    document.getElementById('textInput').value='';
    setRecUI('idle');
    // Refresh today preview
    loadToday();

  } catch(err) {
    renderError(err.message);
    toast(err.message, 'error');
  } finally {
    setLoading(false);
  }
}

function setLoading(show, msg='Processing…') {
  document.getElementById('loadingEl').classList.toggle('hidden',!show);
  if (show) document.getElementById('loadingTxt').textContent=msg;
  document.getElementById('submitBtn').disabled=show;
}
function clearResults() { document.getElementById('resultsEl').innerHTML=''; }

function renderResults(data) {
  const el=document.getElementById('resultsEl');
  let html='';
  if (data.transcript) html+=`<div class="transcript">"${esc(data.transcript)}"</div>`;
  if (!data.created?.length) {
    html+=`<div class="empty"><span class="empty-ico">🤔</span>No events found. Try including a date or time.</div>`;
  } else {
    html+='<div class="card" style="padding:4px 16px">';
    data.created.forEach((item,i)=>{
      const isEvent=item.type==='event';
      let detail='';
      if (isEvent) {
        if(item.date) detail+=item.date;
        if(item.time) detail+=` · ${item.time}`;
        if(item.location) detail+=` · ${esc(item.location)}`;
      } else {
        detail=item.deadline?`Due ${item.deadline}`:'No deadline';
      }
      const [col, bg] = calColor(item.calendar||'');
      const badge = item.calendar
        ? `<span class="cal-badge" style="color:${col};background:${bg};border-color:${col}33">${esc(item.calendar)}</span>` : '';
      const copyData = esc(`${item.type==='event'?'📅':'📋'} ${item.title}${detail?' · '+detail:''}`);
      html+=`<div class="result-item" style="animation-delay:${i*55}ms">
        <div class="ri-icon ${isEvent?'event':'task'}">${isEvent?'📅':'📋'}</div>
        <div class="ri-body">
          <div class="ri-title">${esc(item.title)}</div>
          <div class="ri-meta">${detail}</div>
        </div>
        <div class="ri-actions">
          ${badge}
          <button class="copy-btn" onclick="copyText('${copyData}')" title="Copy">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          </button>
        </div>
      </div>`;
    });
    html+='</div>';
  }
  el.innerHTML=html;
}

function renderError(msg) {
  document.getElementById('resultsEl').innerHTML=`<div class="error-card">⚠ ${esc(msg)}</div>`;
}

function copyText(text) {
  navigator.clipboard?.writeText(text).then(()=>toast('Copied!','info',1800));
}

// ═══════════════════════════════════════════════════
//  TODAY'S PREVIEW
// ═══════════════════════════════════════════════════
let todayOpen = S.get('todayOpen')!=='false';

async function loadToday() {
  const secret=S.get('secret');
  const tz=S.get('timezone')||Intl.DateTimeFormat().resolvedOptions().timeZone;
  const params=new URLSearchParams({timezone:tz,...(secret?{secret}:{})});
  try {
    const res  = await fetch(`/today?${params}`);
    const events = await res.json();
    const count=document.getElementById('todayCount');
    const list=document.getElementById('todayList');
    count.textContent=events.length?`${events.length} event${events.length>1?'s':''}` : 'Free day';
    if (!events.length) {
      list.innerHTML='<p style="font-size:13px;color:var(--text3);text-align:center;padding:4px 0 10px">Nothing scheduled today 🎉</p>';
    } else {
      list.innerHTML=events.map(e=>`
        <div class="today-event">
          ${e.allDay?'<span class="today-allday">ALL DAY</span>':`<span class="today-time">${esc(e.time||'?')}</span>`}
          <span class="today-title">${esc(e.title)}</span>
        </div>`).join('');
    }
    applyTodayOpen();
  } catch {}
}

function applyTodayOpen() {
  const list=document.getElementById('todayList');
  const chev=document.getElementById('todayChevron');
  list.classList.toggle('hidden',!todayOpen);
  chev.classList.toggle('open',todayOpen);
}

document.getElementById('todayHeader').addEventListener('click', ()=>{
  todayOpen=!todayOpen;
  S.set('todayOpen', todayOpen);
  applyTodayOpen();
});

// ═══════════════════════════════════════════════════
//  HISTORY
// ═══════════════════════════════════════════════════
let historyData=[];

async function loadHistory() {
  const el=document.getElementById('historyList');
  const secret=S.get('secret');
  const params=new URLSearchParams(secret?{secret}:{});
  try {
    const res  = await fetch(`/history?${params}`);
    historyData = await res.json();

    // Stats
    const totalEv = historyData.reduce((s,r)=>s+(r.event_count||0),0);
    const totalTa = historyData.reduce((s,r)=>s+(r.task_count||0),0);
    document.getElementById('sTotalEvents').textContent=totalEv;
    document.getElementById('sTotalTasks').textContent=totalTa;
    // Top calendar
    const calCounts={};
    historyData.forEach(r=>(r.events||[]).forEach(e=>{
      if(e.calendar) calCounts[e.calendar]=(calCounts[e.calendar]||0)+1;
    }));
    const topCal=Object.entries(calCounts).sort((a,b)=>b[1]-a[1])[0];
    document.getElementById('sTopCal').textContent=topCal?topCal[0].split(' ')[0].substring(0,6):'—';

    if (!historyData.length) {
      el.innerHTML='<div class="empty" style="padding:28px 16px"><span class="empty-ico">📭</span>No history yet. Create your first event!</div>';
      return;
    }

    renderHistoryList();
  } catch {
    el.innerHTML='<div class="error-card" style="margin:0">Could not load history. Check your password.</div>';
  }
}

function renderHistoryList() {
  const el=document.getElementById('historyList');
  el.innerHTML=historyData.map((row,idx)=>{
    const items=[...(row.events||[]),...(row.tasks||[])];
    const preview=items.length?items[0].title:row.input_text;
    const count=(row.event_count||0)+(row.task_count||0);
    const ago=timeAgo(row.created_at);
    const detail=items.map(e=>`<div class="hi-detail-item">${esc(e.title||e.title)}</div>`).join('');
    return `<div class="hi-wrap" id="hiw-${idx}">
      <div class="hi-swipe-del" id="hid-${idx}" onclick="deleteHistoryRow(${idx})">🗑 Delete</div>
      <div class="hi-item" id="hii-${idx}"
           data-idx="${idx}"
           ontouchstart="swipeStart(event,${idx})"
           ontouchmove="swipeMove(event,${idx})"
           ontouchend="swipeEnd(event,${idx})"
           onclick="toggleHistoryExpand(${idx})">
        <div class="hi-icon">📅</div>
        <div class="hi-body">
          <div class="hi-input">${esc(preview)}</div>
          <div class="hi-meta">${count} item${count!==1?'s':''} created</div>
          <div class="hi-time">${ago}</div>
        </div>
      </div>
      ${detail?`<div class="hi-detail" id="hid2-${idx}"><div class="hi-detail-inner">${detail}</div></div>`:''}
    </div>`;
  }).join('');
}

function toggleHistoryExpand(idx) {
  const el=document.getElementById(`hid2-${idx}`);
  if (el) el.classList.toggle('open');
}

// Swipe to delete
const swipeState={};
function swipeStart(e,idx) {
  swipeState[idx]={startX:e.touches[0].clientX, active:true};
}
function swipeMove(e,idx) {
  if(!swipeState[idx]?.active) return;
  const dx=swipeState[idx].startX-e.touches[0].clientX;
  if(dx>15) {
    document.getElementById(`hii-${idx}`).style.transform=`translateX(-${Math.min(dx,80)}px)`;
    document.getElementById(`hid-${idx}`)?.classList.toggle('show', dx>50);
  }
}
function swipeEnd(e,idx) {
  if(!swipeState[idx]?.active) return;
  const dx=swipeState[idx].startX-e.changedTouches[0].clientX;
  swipeState[idx]={active:false};
  if(dx<60) {
    document.getElementById(`hii-${idx}`).style.transform='';
    document.getElementById(`hid-${idx}`)?.classList.remove('show');
  }
}

async function deleteHistoryRow(idx) {
  // We don't have row IDs from historyData easily; use input text to re-fetch
  // For now, delete from display and reload
  const row=historyData[idx];
  const secret=S.get('secret');
  // We'll pass a re-query; backend deletes by id which we need to include
  // Since we don't store id in historyData, reload and match
  const params=new URLSearchParams(secret?{secret}:{});
  try {
    // Reload with IDs
    const res=await fetch(`/history?${params}`);
    const fresh=await res.json();
    if(!fresh[idx]) return;
    await fetch(`/history?${params}&id=${encodeURIComponent(fresh[idx].id||idx)}`, {method:'DELETE'});
  } catch {}
  historyData.splice(idx,1);
  renderHistoryList();
  toast('Entry deleted','info',2000);
}

function timeAgo(iso) {
  const d=(Date.now()-new Date(iso))/1000;
  if(d<60)   return 'Just now';
  if(d<3600) return `${Math.floor(d/60)}m ago`;
  if(d<86400)return `${Math.floor(d/3600)}h ago`;
  if(d<604800)return `${Math.floor(d/86400)}d ago`;
  return new Date(iso).toLocaleDateString();
}

async function exportHistory() {
  const secret=S.get('secret');
  const params=secret?`?secret=${encodeURIComponent(secret)}`:'';
  window.location.href=`/history/export${params}`;
  toast('Downloading CSV…','info');
}

let confirmCallback=null;
function confirmClearHistory() {
  document.getElementById('confirmIco').textContent='🗑';
  document.getElementById('confirmTitle').textContent='Clear all history?';
  document.getElementById('confirmText').textContent='This permanently deletes all history entries. You can\'t undo this.';
  confirmCallback=doClearHistory;
  document.getElementById('confirmModal').classList.add('show');
}
function closeConfirm() {
  document.getElementById('confirmModal').classList.remove('show');
  confirmCallback=null;
}
document.getElementById('confirmOk').addEventListener('click',()=>{ confirmCallback?.(); closeConfirm(); });

async function doClearHistory() {
  const secret=S.get('secret');
  const params=secret?`?secret=${encodeURIComponent(secret)}`:'';
  try {
    await fetch(`/history${params}`, {method:'DELETE'});
    historyData=[];
    document.getElementById('historyList').innerHTML='<div class="empty" style="padding:28px 16px"><span class="empty-ico">📭</span>History cleared.</div>';
    document.getElementById('sTotalEvents').textContent='0';
    document.getElementById('sTotalTasks').textContent='0';
    document.getElementById('sTopCal').textContent='—';
    toast('History cleared','success');
  } catch { toast('Failed to clear history','error'); }
}

// ═══════════════════════════════════════════════════
//  TABS
// ═══════════════════════════════════════════════════
document.querySelectorAll('.tab').forEach(btn=>{
  btn.addEventListener('click',()=>{
    document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p=>p.classList.add('hidden'));
    btn.classList.add('active');
    const panel=document.getElementById(`panel-${btn.dataset.panel}`);
    panel.classList.remove('hidden');
    if(btn.dataset.panel==='history') loadHistory();
  });
});

// ═══════════════════════════════════════════════════
//  QUICK PHRASES
// ═══════════════════════════════════════════════════
function renderPhrases() {
  const phrases=S.getJSON('phrases',['Gym session','Team standup','Coffee with']);
  const row=document.getElementById('phrasesRow');
  row.innerHTML=phrases.map(p=>
    `<button class="phrase-chip" onclick="usePhrase('${esc(p)}')">${esc(p)}</button>`
  ).join('')+`<button class="phrase-chip add-btn" onclick="openSettings();setTimeout(()=>document.getElementById('phraseInput').focus(),400)">+ Add</button>`;
}

function usePhrase(p) {
  document.getElementById('textInput').value=p+' ';
  document.getElementById('textInput').focus();
}

function addPhrase() {
  const inp=document.getElementById('phraseInput');
  const val=inp.value.trim();
  if(!val) return;
  const phrases=S.getJSON('phrases',['Gym session','Team standup','Coffee with']);
  if(!phrases.includes(val)) { phrases.push(val); S.setJSON('phrases',phrases); }
  inp.value='';
  renderPhrases();
  renderPhrasesMgr();
  toast('Phrase added','success',2000);
}

function renderPhrasesMgr() {
  const phrases=S.getJSON('phrases',['Gym session','Team standup','Coffee with']);
  const mgr=document.getElementById('phrasesMgr');
  mgr.innerHTML=phrases.map((p,i)=>
    `<div class="pmgr-chip">${esc(p)}<button class="pmgr-del" onclick="deletePhrase(${i})">×</button></div>`
  ).join('');
}

function deletePhrase(i) {
  const phrases=S.getJSON('phrases',[]);
  phrases.splice(i,1);
  S.setJSON('phrases',phrases);
  renderPhrases();
  renderPhrasesMgr();
}

// ═══════════════════════════════════════════════════
//  SETTINGS
// ═══════════════════════════════════════════════════
const overlay=document.getElementById('settingsOverlay');

function openSettings() {
  document.getElementById('sPw').value=S.get('secret');
  document.getElementById('sTz').value=S.get('timezone')||Intl.DateTimeFormat().resolvedOptions().timeZone;
  const rem=S.get('reminder')||'30';
  document.getElementById('sReminder').value=rem;
  renderPhrasesMgr();
  loadCalendarsForSettings();
  overlay.classList.add('open');
  document.body.style.overflow='hidden';
}

function closeSettings() {
  overlay.classList.remove('open');
  document.body.style.overflow='';
}

async function loadCalendarsForSettings() {
  const secret=S.get('secret');
  const params=secret?`?secret=${encodeURIComponent(secret)}`:'';
  try {
    const res=await fetch(`/calendars${params}`);
    const cals=await res.json();
    googleCalColors={};
    cals.forEach(c=>{ googleCalColors[c.name]=c.color; });
    const sel=document.getElementById('sDefCal');
    const saved=S.get('defCal');
    sel.innerHTML=`<option value="">AI decides</option>`+cals.map(c=>
      `<option value="${esc(c.name)}" ${c.name===saved?'selected':''}>${esc(c.name)}</option>`
    ).join('');
  } catch {
    document.getElementById('sDefCal').innerHTML='<option value="">AI decides</option>';
  }
}

document.getElementById('settingsBtn').addEventListener('click', openSettings);
document.getElementById('closeSettings').addEventListener('click', closeSettings);
overlay.addEventListener('click', e=>{ if(e.target===overlay) closeSettings(); });

document.getElementById('saveSettingsBtn').addEventListener('click',()=>{
  const pw=document.getElementById('sPw').value;
  const tz=document.getElementById('sTz').value.trim();
  const reminder=document.getElementById('sReminder').value;
  const defCal=document.getElementById('sDefCal').value;
  S.set('secret', pw);
  S.set('timezone', tz || Intl.DateTimeFormat().resolvedOptions().timeZone);
  S.set('reminder', reminder);
  S.set('defCal', defCal);
  document.getElementById('pwInput').value=pw;
  document.getElementById('pwIcon').classList.toggle('open', !!pw);
  closeSettings();
  toast('Settings saved ✓','success');
  loadToday();
});

// Theme buttons
document.querySelectorAll('[data-tv]').forEach(b=>{
  b.addEventListener('click',()=>Theme.set(b.dataset.tv));
});
document.getElementById('themeBtn').addEventListener('click',()=>Theme.toggle());

// ═══════════════════════════════════════════════════
//  KEYBOARD SHORTCUTS
// ═══════════════════════════════════════════════════
document.addEventListener('keydown', e=>{
  if(e.key==='Escape') { closeSettings(); closeConfirm(); }
  if((e.metaKey||e.ctrlKey)&&e.key==='Enter') { e.preventDefault(); handleSubmit(); }
  if((e.metaKey||e.ctrlKey)&&e.key==='r')     { e.preventDefault(); toggleRecord(); }
});

// ═══════════════════════════════════════════════════
//  ONBOARDING
// ═══════════════════════════════════════════════════
function finishOnboarding() {
  S.set('onboarded','1');
  const el=document.getElementById('onboarding');
  el.classList.add('out');
  setTimeout(()=>{ el.style.display='none'; },500);
}

// ═══════════════════════════════════════════════════
//  UTILITY
// ═══════════════════════════════════════════════════
function esc(s) {
  if(!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ═══════════════════════════════════════════════════
//  INIT
// ═══════════════════════════════════════════════════
(function init() {
  Theme.init();
  Wave.init();

  // Restore password
  const pw=S.get('secret');
  if(pw) {
    document.getElementById('pwInput').value=pw;
    document.getElementById('pwIcon').classList.add('open');
  }

  // Auto-detect timezone if not set
  if(!S.get('timezone')) S.set('timezone', Intl.DateTimeFormat().resolvedOptions().timeZone);

  // Restore reminder default
  const rem=S.get('reminder');
  if(rem) document.getElementById('sReminder').value=rem;

  // Offline check
  if(!navigator.onLine) setOffline(true);

  // Mic button
  document.getElementById('micBtn').addEventListener('click', toggleRecord);

  // Password field
  document.getElementById('pwInput').addEventListener('input', function(){
    S.set('secret', this.value);
    document.getElementById('pwIcon').classList.toggle('open', !!this.value);
  });

  // Auto-submit toggle restore
  const autoVal=S.get('autoSubmit')==='1';
  document.getElementById('autoSubmitToggle').checked=autoVal;
  document.getElementById('autoSubmitToggle').addEventListener('change', function(){
    S.set('autoSubmit', this.checked?'1':'0');
  });

  // Phrases
  renderPhrases();

  // Today's events
  loadToday();

  // Onboarding
  if(!S.get('onboarded')) {
    // Show onboarding
  } else {
    document.getElementById('onboarding').style.display='none';
  }
})();
