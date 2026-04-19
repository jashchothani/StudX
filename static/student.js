// student.js — Student portal logic

const TIMETABLE = {
  Mon:[
    {time:'08:00–09:00',sub:'PRP (CL)',room:'CR 105',fac:'SM',type:'class'},
    {time:'09:00–10:00',sub:'PRP (CL)',room:'CR 105',fac:'SM',type:'class'},
    {time:'10:00–11:00',sub:'Library',room:'—',fac:'—',type:'class'},
    {time:'11:00–12:00',sub:'RECESS',room:'',fac:'',type:'break'},
    {time:'12:00–01:00',sub:'IOT (CL)',room:'CR 106',fac:'SRK',type:'class'},
    {time:'01:00–02:00',sub:'IOT (CL)',room:'CR 106',fac:'SRK',type:'class'},
    {time:'02:00–04:00',sub:'PSP (LL)',room:'Lab 3/4',fac:'GS',type:'lab'},
  ],
  Tue:[
    {time:'08:00–09:00',sub:'CSY (CL)',room:'CR 105',fac:'PPB',type:'class'},
    {time:'09:00–10:00',sub:'CSY (CL)',room:'CR 105',fac:'PPB',type:'class'},
    {time:'10:00–11:00',sub:'RECESS',room:'',fac:'',type:'break'},
    {time:'11:00–12:00',sub:'IOT (CL)',room:'CR 105',fac:'SRK',type:'class'},
    {time:'12:00–01:00',sub:'NWA (LL)',room:'LAB 5',fac:'PN',type:'lab'},
    {time:'01:00–02:00',sub:'PRP (LL)',room:'LAB 4',fac:'SM',type:'lab'},
    {time:'02:00–04:00',sub:'CSY (LL)',room:'LAB 5',fac:'PPB',type:'lab'},
  ],
  Wed:[
    {time:'09:00–10:00',sub:'GE (CL)',room:'CR 204',fac:'VF',type:'class'},
    {time:'10:00–11:00',sub:'GE (CL)',room:'CR 204',fac:'VF',type:'class'},
    {time:'11:00–12:00',sub:'OSY (CL)',room:'CR 105',fac:'JSK',type:'class'},
    {time:'12:00–01:00',sub:'NWA (CL)',room:'CR 105',fac:'PN',type:'class'},
    {time:'01:00–02:00',sub:'RECESS',room:'',fac:'',type:'break'},
    {time:'02:00–03:00',sub:'OSY (LL)',room:'LAB 4',fac:'JSK',type:'lab'},
    {time:'03:00–04:00',sub:'IOT (LL)',room:'LAB 5',fac:'SRK',type:'lab'},
  ],
  Thu:[
    {time:'08:00–09:00',sub:'NWA (CL)',room:'CR 105',fac:'PN',type:'class'},
    {time:'09:00–10:00',sub:'OSY (CL)',room:'CR 106',fac:'JSK',type:'class'},
    {time:'10:00–11:00',sub:'IOT (CL)',room:'CR 204',fac:'SRK',type:'class'},
    {time:'11:00–12:00',sub:'RECESS',room:'',fac:'',type:'break'},
    {time:'12:00–01:00',sub:'PRP (CL)',room:'CR 105',fac:'SM',type:'class'},
    {time:'01:00–02:00',sub:'CSY (CL)',room:'CR 105',fac:'PPB',type:'class'},
  ],
  Fri:[
    {time:'08:00–09:00',sub:'GE (CL)',room:'CR 204',fac:'VF',type:'class'},
    {time:'09:00–10:00',sub:'PRP (CL)',room:'CR 105',fac:'SM',type:'class'},
    {time:'10:00–11:00',sub:'OSY (CL)',room:'CR 105',fac:'JSK',type:'class'},
    {time:'11:00–12:00',sub:'RECESS',room:'',fac:'',type:'break'},
    {time:'12:00–01:00',sub:'NWA (CL)',room:'CR 106',fac:'PN',type:'class'},
    {time:'01:00–02:00',sub:'IOT (TL)',room:'CR 105',fac:'SRK',type:'class'},
  ]
};

const DAYS=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
let currentDay = DAYS[new Date().getDay()] || 'Mon';
if(!TIMETABLE[currentDay]) currentDay='Mon';
let qrScanner=null;
let attSessionToken=null;
let streamRef=null;

function initStudentPortal(){
  renderTodayTT();
  loadAttSummary();
  loadAssignments();
  loadMeetings();
  setupDayTabs();
  renderTTTable(currentDay);
  pollAttSession();
}

// ──────────────────────────────
// TIMETABLE
// ──────────────────────────────
function renderTodayTT(){
  const now=new Date();
  const h=now.getHours(),m=now.getMinutes();
  const schedule=TIMETABLE[currentDay]||[];
  const root=document.getElementById('today-tt');
  if(!root)return;
  if(!schedule.length){root.innerHTML='<div style="color:#9ca3af;font-size:.83rem;text-align:center;padding:20px">No classes today 🎉</div>';return;}
  root.innerHTML=schedule.map(c=>{
    const startH=parseInt(c.time.split('–')[0]);
    const isNow=c.type!=='break'&&startH===h&&m<60;
    const badgeHtml=c.type==='break'?'<span class="badge badge-gray">Break</span>':c.type==='lab'?'<span class="badge badge-cyan">Lab</span>':'';
    return `<div class="tt-row${isNow?' now':''}">
      ${isNow?'<div class="now-dot"></div>':'<div style="width:7px"></div>'}
      <div class="tt-time">${c.time}</div>
      <div style="flex:1"><div class="tt-sub">${c.sub}</div>${c.room?`<div class="tt-meta">${c.room}·Prof.${c.fac}</div>`:''}</div>
      ${isNow?'<span class="badge badge-purple">NOW</span>':badgeHtml}
    </div>`;
  }).join('');
}

function setupDayTabs(){
  const tabs=document.querySelectorAll('.day-tab');
  const days=['Mon','Tue','Wed','Thu','Fri'];
  const todayIdx=days.indexOf(currentDay);
  if(tabs.length&&todayIdx>=0){
    tabs[todayIdx].className='btn btn-sm btn-primary day-tab';
  }
}

function switchDay(day,btn){
  document.querySelectorAll('.day-tab').forEach(b=>b.className='btn btn-sm btn-outline day-tab');
  btn.className='btn btn-sm btn-primary day-tab';
  renderTTTable(day);
}

function renderTTTable(day){
  const schedule=TIMETABLE[day]||[];
  const now=new Date();
  const root=document.getElementById('tt-table');
  if(!root)return;
  if(!schedule.length){root.innerHTML='<p style="color:#9ca3af;text-align:center;padding:20px">No classes</p>';return;}
  root.innerHTML=`<table class="tbl">
    <tr><th>Time</th><th>Subject</th><th>Type</th><th>Room</th><th>Faculty</th></tr>
    ${schedule.map(c=>{
      const startH=parseInt(c.time.split('–')[0]);
      const isNow=c.type!=='break'&&startH===now.getHours()&&day===currentDay;
      const type=c.type==='break'?'<span class="badge badge-gray">Break</span>':c.type==='lab'?'<span class="badge badge-cyan">Lab</span>':'<span class="badge badge-blue">Theory</span>';
      return `<tr${isNow?' style="background:#f5f3ff"':''}>
        <td style="color:var(--c1);font-weight:700">${c.time}${isNow?'<span class="badge badge-purple" style="margin-left:6px">NOW</span>':''}</td>
        <td><strong>${c.sub}</strong></td><td>${type}</td><td>${c.room||'—'}</td><td>${c.fac||'—'}</td>
      </tr>`;
    }).join('')}
  </table>`;
}

// ──────────────────────────────
// ATTENDANCE SUMMARY
// ──────────────────────────────
function loadAttSummary(){
  fetch('/api/student_attendance').then(r=>r.json()).then(d=>{
    const el=document.getElementById('att-summary');
    const ovEl=document.getElementById('ov-pct');
    if(ovEl)ovEl.textContent=d.pct+'%';
    if(d.pct<75){
      const al=document.getElementById('att-alert');
      const am=document.getElementById('att-alert-msg');
      if(al){al.classList.remove('hidden');am.textContent=`Your overall attendance is ${d.pct}% — below 75% threshold. Take action immediately!`;}
    }
    if(!el)return;
    if(!d.logs||!d.logs.length){el.innerHTML='<p style="color:#9ca3af;text-align:center;padding:16px">No attendance records yet.</p>';return;}
    el.innerHTML=`<table class="tbl"><tr><th>Date</th><th>Subject</th><th>Method</th></tr>
      ${d.logs.slice(0,15).map(l=>`<tr><td style="color:#6b7280">${l.log_date||''}</td><td><strong>${l.subject||'—'}</strong></td>
      <td><span class="badge badge-green">${l.method}</span></td></tr>`).join('')}</table>
      <div style="margin-top:12px;padding:14px;background:#f5f3ff;border-radius:10px;display:flex;gap:24px">
        <div><div style="font-size:1.4rem;font-weight:800;color:var(--c1)">${d.present}</div><div style="font-size:.72rem;color:#9ca3af">Sessions Attended</div></div>
        <div><div style="font-size:1.4rem;font-weight:800;color:#6b7280">${d.total}</div><div style="font-size:.72rem;color:#9ca3af">Total Sessions</div></div>
        <div><div style="font-size:1.4rem;font-weight:800;color:${d.pct>=75?'#10b981':'#ef4444'}">${d.pct}%</div><div style="font-size:.72rem;color:#9ca3af">Attendance</div></div>
      </div>`;
  }).catch(()=>{});
}

// ──────────────────────────────
// ATTENDANCE SESSION POLLING
// ──────────────────────────────
function pollAttSession(){
  // In production this would use WebSocket; here we poll every 5s
  setInterval(()=>{
    if(document.getElementById('tab-attendance')&&!document.getElementById('tab-attendance').classList.contains('hidden')){
      checkIfSessionOpen();
    }
  },5000);
}

function checkIfSessionOpen(){
  // Simplified: just show active zone if token stored in sessionStorage
  if(sessionStorage.getItem('qr_token')){
    showAttActive(sessionStorage.getItem('qr_token'));
  }
}

// Called when teacher sends the token (in real app via WebSocket push)
function showAttActive(token){
  attSessionToken=token;
  const w=document.getElementById('att-waiting-banner');
  const a=document.getElementById('att-active-zone');
  if(w)w.style.display='none';
  if(a)a.classList.remove('hidden');
  startQRScanner(token);
}

// ──────────────────────────────
// QR SCANNER
// ──────────────────────────────
async function startQRScanner(expectedToken){
  try{
    if(qrScanner){await qrScanner.stop().catch(()=>{}); qrScanner=null;}
    qrScanner=new Html5Qrcode('qr-reader');
    await qrScanner.start(
      {facingMode:'environment'},
      {fps:10,qrbox:{width:200,height:200}},
      async(text)=>{
        await qrScanner.stop().catch(()=>{});qrScanner=null;
        await markAttendance(text,'qr');
      },
      ()=>{}
    );
    setScanStatus('info','Point camera at the QR code on the board');
  }catch(e){
    setScanStatus('error','Camera access denied. Use Face verification instead.');
  }
}

function setScanStatus(type,msg){
  const el=document.getElementById('scan-status');
  if(!el)return;
  el.className='status-msg '+type+' mt14';
  const icons={info:'fa-camera',success:'fa-circle-check',error:'fa-triangle-exclamation',loading:'fa-spinner spin'};
  el.innerHTML=`<i class="fa-solid ${icons[type]||'fa-info'}"></i> ${msg}`;
}

// ──────────────────────────────
// FACE VERIFICATION
// ──────────────────────────────
async function startFaceVerify(){
  if(!attSessionToken){
    const el=document.getElementById('face-result');
    if(el){el.classList.remove('hidden');el.innerHTML='<div class="status-msg error"><i class="fa-solid fa-triangle-exclamation"></i> No active session. Wait for teacher to start attendance.</div>';}
    return;
  }
  const video=document.getElementById('webcam');
  const canvas=document.getElementById('canvas');
  const camArea=document.getElementById('face-cam-area');
  const resultEl=document.getElementById('face-result');
  try{
    const stream=await navigator.mediaDevices.getUserMedia({video:true});
    streamRef=stream;
    video.srcObject=stream;
    video.style.display='block';
    if(camArea)camArea.style.display='none';
    if(resultEl){resultEl.classList.remove('hidden');resultEl.innerHTML='<div class="status-msg loading"><i class="fa-solid fa-spinner spin"></i> Scanning face... hold still</div>';}
    setTimeout(async()=>{
      canvas.width=video.videoWidth;
      canvas.height=video.videoHeight;
      canvas.getContext('2d').drawImage(video,0,0);
      const dataUrl=canvas.toDataURL('image/jpeg');
      stream.getTracks().forEach(t=>t.stop());
      video.style.display='none';
      if(camArea)camArea.style.display='flex';
      // Send to face verify endpoint
      const res=await fetch('/api/verify_face',{
        method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({token:attSessionToken,image:dataUrl})
      });
      const data=await res.json();
      if(data.status==='success'){
        if(resultEl)resultEl.innerHTML='<div class="status-msg success"><i class="fa-solid fa-circle-check"></i> Attendance marked via Face+QR ✓</div>';
        if(typeof confetti!=='undefined')confetti({particleCount:100,spread:60,origin:{y:.6}});
      } else {
        if(resultEl)resultEl.innerHTML=`<div class="status-msg error"><i class="fa-solid fa-triangle-exclamation"></i> ${data.msg||'Verification failed'}</div>`;
      }
    },2000);
  }catch(e){
    if(resultEl){resultEl.classList.remove('hidden');resultEl.innerHTML='<div class="status-msg error"><i class="fa-solid fa-triangle-exclamation"></i> Camera access failed.</div>';}
  }
}

async function markAttendance(token,method){
  setScanStatus('loading','Verifying...');
  try{
    const res=await fetch('/api/mark_attendance',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({token,method})
    });
    const data=await res.json();
    if(data.status==='success'){
      setScanStatus('success',data.msg);
      if(typeof confetti!=='undefined')confetti({particleCount:100,spread:60});
    } else {
      setScanStatus('error',data.msg||'Failed');
    }
  }catch(e){setScanStatus('error','Network error');}
}

// ──────────────────────────────
// ASSIGNMENTS
// ──────────────────────────────
function loadAssignments(){
  fetch('/api/assignments').then(r=>r.json()).then(d=>{
    const list=document.getElementById('assignments-list');
    const pending=document.getElementById('pending-asgn');
    const ov=document.getElementById('ov-pending');
    if(!d.assignments||!d.assignments.length){
      if(list)list.innerHTML='<div class="card" style="text-align:center;padding:30px;color:#9ca3af">No assignments yet.</div>';
      return;
    }
    if(ov)ov.textContent=d.assignments.length;
    if(pending){
      pending.innerHTML=d.assignments.slice(0,3).map(a=>`
      <div class="asgn-card">
        <div style="display:flex;justify-content:space-between;align-items:flex-start"><div>
          <div class="asgn-title">${a.title}</div>
          <div class="asgn-meta">${a.subject||''} · Due ${a.due_date||'TBD'}</div>
        </div><span class="badge badge-red">Pending</span></div>
        <div style="margin-top:10px"><button class="btn btn-primary btn-sm" onclick="showTab('assignments',null)"><i class="fa-solid fa-paper-plane"></i> Submit</button></div>
      </div>`).join('');
    }
    if(list){
      list.innerHTML=d.assignments.map(a=>`
      <div class="asgn-card">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">
          <div><div class="asgn-title">${a.title}</div><div class="asgn-meta">${a.subject||''} · Due ${a.due_date||'TBD'} · Max ${a.max_marks||100} marks</div></div>
          <span class="badge badge-red">Pending</span>
        </div>
        <div class="asgn-desc">${a.description||''}</div>
        <div class="flex"><button class="btn btn-primary btn-sm" onclick="submitAssignment(${a.id},this)"><i class="fa-solid fa-paper-plane"></i> Submit</button>
        <button class="btn btn-outline btn-sm"><i class="fa-solid fa-paperclip"></i> Attach</button></div>
      </div>`).join('');
    }
  }).catch(()=>{});
}

async function submitAssignment(id,btn){
  btn.innerHTML='<i class="fa-solid fa-spinner spin"></i> Submitting...';
  const res=await fetch('/api/submit_assignment',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({assignment_id:id,notes:'Submitted from portal'})
  });
  const d=await res.json();
  if(d.status==='ok'){btn.innerHTML='<i class="fa-solid fa-check"></i> Submitted!';btn.style.background='#10b981';}
}

// ──────────────────────────────
// MEETINGS
// ──────────────────────────────
function loadMeetings(){
  const el=document.getElementById('meetings-list');
  if(!el)return;
  fetch('/api/meetings').then(r=>r.json()).then(d=>{
    if(!d.meetings||!d.meetings.length){el.innerHTML='<p style="color:#9ca3af;font-size:.83rem">No meetings scheduled.</p>';return;}
    el.innerHTML=d.meetings.map(m=>`
    <div class="meeting-card mb10" style="border:1px solid #e8eaf2;border-radius:12px;padding:14px;cursor:pointer;transition:.2s">
      <div style="font-weight:700;font-size:.88rem;color:#1a1d2e">${m.title}</div>
      <div style="font-size:.73rem;color:#9ca3af;margin-top:3px">${m.scheduled_at||'Soon'}</div>
      <button class="btn btn-primary btn-sm mt14" onclick="this.textContent='Joined!'"><i class="fa-solid fa-video"></i> Join</button>
    </div>`).join('');
  }).catch(()=>{el.innerHTML='<p style="color:#9ca3af">Loading...</p>';});
}

// ──────────────────────────────
// CHAT
// ──────────────────────────────
function openChat(id,name,av){
  document.querySelectorAll('.chat-item').forEach(i=>i.classList.remove('active'));
  event.currentTarget.classList.add('active');
  const hd=document.getElementById('chat-hd-name');
  const hdAv=document.getElementById('chat-hd-av');
  if(hd)hd.textContent=name;
  if(hdAv)hdAv.textContent=av;
}
function sendChatMsg(){
  const inp=document.getElementById('chat-inp');
  const txt=inp.value.trim();
  if(!txt)return;
  const msgs=document.getElementById('chat-msgs');
  const d=document.createElement('div');
  d.className='msg mine';
  d.innerHTML=`<div class="av" style="background:var(--c3);color:var(--c1)">${STUDENT_AV}</div>
  <div><div class="msg-bubble mine">${txt}</div><div class="msg-time">Now</div></div>`;
  msgs.appendChild(d);
  inp.value='';
  msgs.scrollTop=msgs.scrollHeight;
}
function filterChats(q){
  document.querySelectorAll('.chat-item').forEach(el=>{
    el.style.display=el.querySelector('.ci-name').textContent.toLowerCase().includes(q.toLowerCase())?'flex':'none';
  });
}

// ──────────────────────────────
// AI TUTOR
// ──────────────────────────────
async function aiSend(preset){
  const inp=document.getElementById('ai-inp');
  const text=preset||inp.value.trim();
  if(!text)return;
  inp.value='';
  const msgs=document.getElementById('ai-msgs');
  const ud=document.createElement('div');
  ud.style.cssText='display:flex;justify-content:flex-end;margin-bottom:6px';
  ud.innerHTML=`<div class="msg-bubble mine" style="max-width:70%">${text}</div>`;
  msgs.appendChild(ud);
  const td=document.createElement('div');
  td.className='ai-bubble';
  td.innerHTML='<div class="ai-typing"><span></span><span></span><span></span></div>';
  msgs.appendChild(td);
  msgs.scrollTop=msgs.scrollHeight;
  try{
    const res=await fetch('/api/ai_chat',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({message:text})
    });
    const d=await res.json();
    td.textContent=d.reply||'I can help with that! (Full AI integration connects here.)';
  }catch(e){
    td.textContent='Smart AI responses are available when connected to the Anthropic API.';
  }
  msgs.scrollTop=msgs.scrollHeight;
}