import { api } from './api.js';
import { state, saveAuth, saveUi, logoutLocal, isAuthed } from './state.js';
import { toast, setBusy, closeModal, modal, esc } from './ui.js';
import {
  renderRoute, hydrateVisuals, authModal, createSubjectModal, uploadModal, conversationModal,
  generateQuizModal, generateDeckModal, generatePlanModal, publishCommunityModal, exportModal,
  openDocument, openConversation, openQuiz, startQuiz, openDeck, reviewDue, openPlan
} from './views.js';

const app = document.getElementById('app');
let renderId = 0;

function currentRoute(){ return location.hash.replace(/^#/,'') || '/'; }

const SIDEBAR_OVERLAY_QUERY = '(max-width: 1320px)';
function usesOverlaySidebar(){ return window.matchMedia(SIDEBAR_OVERLAY_QUERY).matches; }
function setSidebarDrawer(open){
  saveUi({ sidebarOpen: open });
  document.querySelector('.sidebar')?.classList.toggle('open', open);
  document.querySelector('.mobile-scrim')?.classList.toggle('show', open);
  document.body.classList.toggle('sidebar-drawer-open', open && usesOverlaySidebar());
}
function setSidebarCollapsed(collapsed){
  saveUi({ sidebarCollapsed: collapsed, sidebarOpen: false });
  document.querySelector('.app-shell')?.classList.toggle('sidebar-collapsed', collapsed);
  document.querySelector('.sidebar')?.classList.remove('open');
  document.querySelector('.mobile-scrim')?.classList.remove('show');
}

async function render(){
  const id = ++renderId;
  app.classList.add('is-changing');
  try {
    const result = await renderRoute(currentRoute());
    if (id !== renderId) return;
    app.innerHTML = result.html;
    bindEvents();
    hydrateVisuals();
    requestAnimationFrame(()=>app.classList.remove('is-changing'));
    if(isAuthed()) updateTopbarStatus();
  } catch (e) {
    console.error(e);
    app.innerHTML = `<main class="fatal"><h1>Không thể tải trang</h1><p>${esc(e.message)}</p><button class="btn btn-primary" onclick="location.reload()">Thử lại</button></main>`;
    toast(e.message || 'Có lỗi xảy ra','danger');
  }
}

async function updateTopbarStatus(){
  const el=document.querySelector('[data-health-text]');
  const dot=document.querySelector('.pulse-dot');
  if(!el)return;
  try{
    const h=await api.health();
    el.textContent=`Backend ${h.status} · DB ${h.database||'n/a'}`;
    dot?.classList.toggle('bad',h.status!=='ok');
  }catch{
    el.textContent='Backend không phản hồi'; dot?.classList.add('bad');
  }
  try{
    const n=await api.notifications(true);
    document.querySelector('[data-notif-dot]')?.classList.toggle('show',n.length>0);
  }catch{}
}

function bindEvents(){
  const on=(sel,event,fn)=>document.querySelectorAll(sel).forEach(el=>el.addEventListener(event,fn));
  on('[data-sidebar-toggle]','click',()=>setSidebarDrawer(!document.querySelector('.sidebar')?.classList.contains('open')));
  on('[data-sidebar-close]','click',()=>setSidebarDrawer(false));
  on('[data-sidebar-collapse]','click',()=>setSidebarCollapsed(!document.querySelector('.app-shell')?.classList.contains('sidebar-collapsed')));
  on('.sidebar .nav-link','click',()=>{ if(usesOverlaySidebar()) setSidebarDrawer(false); });
  on('[data-go-notifications]','click',()=>location.hash='#/notifications');
  on('[data-logout]','click',logout);
  on('[data-open-login]','click',()=>{authModal('login');bindModalEvents();});
  on('[data-open-register]','click',()=>{authModal('register');bindModalEvents();});

  on('[data-create-subject]','click',()=>createSubjectModal().then(bindModalEvents));
  on('[data-edit-subject]','click',e=>{try{createSubjectModal(JSON.parse(e.currentTarget.dataset.editSubject)).then(bindModalEvents)}catch{}});
  on('[data-delete-subject]','click',deleteSubject);
  on('[data-open-subject]','click',e=>{saveUi({selectedSubjectId:Number(e.currentTarget.dataset.openSubject)});location.hash='#/analytics';});

  on('[data-upload-document],[data-quick-upload]','click',()=>uploadModal().then(bindModalEvents));
  on('[data-doc-id]','click',e=>openDocument(Number(e.currentTarget.dataset.docId)).then(bindModalEvents).catch(err=>toast(err.message,'danger')));
  on('[data-process-doc]','click',processDoc);
  on('[data-delete-doc]','click',deleteDoc);

  on('[data-new-conversation]','click',()=>conversationModal().then(bindModalEvents));
  on('[data-conversation]','click',e=>openConversation(Number(e.currentTarget.dataset.conversation)).then(bindModalEvents).catch(err=>toast(err.message,'danger')));

  on('[data-generate-quiz]','click',()=>generateQuizModal().then(bindModalEvents));
  on('[data-create-quiz]','click',openManualQuizModal);
  on('[data-quiz-id]','click',e=>openQuiz(Number(e.currentTarget.dataset.quizId)).then(bindModalEvents).catch(err=>toast(err.message,'danger')));
  on('[data-publish-quiz]','click',publishQuiz);

  on('[data-generate-deck]','click',()=>generateDeckModal().then(bindModalEvents));
  on('[data-deck-id]','click',e=>openDeck(Number(e.currentTarget.dataset.deckId)).then(bindModalEvents).catch(err=>toast(err.message,'danger')));
  on('[data-review-due]','click',()=>reviewDue().catch(err=>toast(err.message,'danger')));

  on('[data-generate-plan]','click',()=>generatePlanModal().then(bindModalEvents));
  on('[data-plan-id]','click',e=>openPlan(Number(e.currentTarget.dataset.planId)).then(bindModalEvents).catch(err=>toast(err.message,'danger')));
  on('[data-analytics-subject]','change',e=>{saveUi({selectedSubjectId:Number(e.target.value)});render();});

  on('[data-publish-community]','click',()=>publishCommunityModal().then(bindModalEvents));
  on('[data-like-post]','click',communityLike); on('[data-save-post]','click',communitySave); on('[data-fork-post]','click',communityFork);
  on('[data-create-export]','click',()=>exportModal().then(bindModalEvents));
  on('[data-read-notif]','click',markRead);

  const profile=document.getElementById('profile-form'); if(profile)profile.addEventListener('submit',saveProfile);
  initParallax();
}

function bindModalEvents(){
  const auth=document.getElementById('auth-form'); if(auth)auth.addEventListener('submit',submitAuth);
  document.querySelector('[data-switch-register]')?.addEventListener('click',e=>{e.preventDefault();authModal('register');bindModalEvents();});
  document.querySelector('[data-switch-login]')?.addEventListener('click',e=>{e.preventDefault();authModal('login');bindModalEvents();});
  document.getElementById('subject-form')?.addEventListener('submit',submitSubject);
  document.getElementById('upload-form')?.addEventListener('submit',submitUpload);
  document.getElementById('conversation-form')?.addEventListener('submit',submitConversation);
  document.getElementById('generate-quiz-form')?.addEventListener('submit',submitGenerateQuiz);
  document.getElementById('manual-quiz-form')?.addEventListener('submit',submitManualQuiz);
  document.getElementById('generate-deck-form')?.addEventListener('submit',submitGenerateDeck);
  document.getElementById('generate-plan-form')?.addEventListener('submit',submitGeneratePlan);
  document.getElementById('community-form')?.addEventListener('submit',submitCommunity);
  document.getElementById('export-form')?.addEventListener('submit',submitExport);
  document.getElementById('attempt-form')?.addEventListener('submit',submitAttempt);
  document.querySelector('[data-chat-form]')?.addEventListener('submit',submitChat);
  document.querySelectorAll('[data-process-doc]').forEach(x=>x.addEventListener('click',processDoc));
  document.querySelectorAll('[data-embed-doc]').forEach(x=>x.addEventListener('click',embedDoc));
  document.querySelectorAll('[data-start-quiz]').forEach(x=>x.addEventListener('click',e=>startQuiz(Number(e.currentTarget.dataset.startQuiz)).then(bindModalEvents).catch(err=>toast(err.message,'danger'))));
  document.querySelectorAll('[data-publish-quiz]').forEach(x=>x.addEventListener('click',publishQuiz));
  document.querySelectorAll('.task-status').forEach(x=>x.addEventListener('change',updateTask));
  const type=document.querySelector('[data-resource-type]'); if(type) type.addEventListener('change',()=>{const deck=type.value==='FLASHCARD_DECK'; document.querySelector('[data-quiz-select]')?.closest('label')?.classList.toggle('hidden',deck); document.querySelector('[data-deck-label]')?.classList.toggle('hidden',!deck);});
}

async function submitAuth(e){ e.preventDefault(); const btn=e.submitter; setBusy(btn,true,'Đang xác thực…'); const fd=new FormData(e.currentTarget); try{ const payload={email:fd.get('email'),password:fd.get('password')}; if(e.currentTarget.dataset.mode==='register')payload.full_name=fd.get('full_name'); const pair=e.currentTarget.dataset.mode==='register'?await api.register(payload):await api.login(payload); saveAuth(pair); closeModal(); toast('Đăng nhập thành công','success'); location.hash='#/'; await render(); }catch(err){toast(err.message,'danger');setBusy(btn,false);} }

async function logout(){ try{if(state.auth?.refresh_token)await api.logout(state.auth.refresh_token)}catch{} logoutLocal(); location.hash='#/'; render(); }

async function submitSubject(e){e.preventDefault();const btn=e.submitter;setBusy(btn,true);const fd=new FormData(e.currentTarget);const payload={name:fd.get('name'),description:fd.get('description')||null,color_hex:fd.get('color_hex')||null};try{const id=e.currentTarget.dataset.id;if(id)await api.updateSubject(id,payload);else await api.createSubject(payload);closeModal();toast('Đã lưu môn học','success');render();}catch(err){toast(err.message,'danger');setBusy(btn,false);}}
async function deleteSubject(e){const id=Number(e.currentTarget.dataset.deleteSubject);if(!confirm('Xóa môn học này?'))return;try{await api.deleteSubject(id);toast('Đã xóa môn học','success');render();}catch(err){toast(err.message,'danger')}}
async function submitUpload(e){e.preventDefault();const btn=e.submitter;setBusy(btn,true,'Đang upload…');const fd=new FormData(e.currentTarget);const file=fd.get('file');try{const doc=await api.uploadDocument({file,subject_id:fd.get('subject_id')||null,process_now:fd.get('process_now')==='on'});closeModal();toast(`Upload thành công: ${doc.original_name}`,'success');render();}catch(err){toast(err.message,'danger');setBusy(btn,false)}}
async function processDoc(e){const btn=e.currentTarget;setBusy(btn,true,'Processing…');try{const id=Number(btn.dataset.processDoc);const r=await api.processDocument(id);toast(`READY · ${r.chunks_created} chunks · ${r.embeddings_created} embeddings`,'success');closeModal();render();}catch(err){toast(err.message,'danger');setBusy(btn,false)}}
async function embedDoc(e){const btn=e.currentTarget;setBusy(btn,true,'Embedding…');try{const id=Number(btn.dataset.embedDoc);const r=await api.embedDocument(id,false);toast(`Đã tạo ${r.embeddings_created} embeddings (${r.embedding_model})`,'success');closeModal();render();}catch(err){toast(err.message,'danger');setBusy(btn,false)}}
async function deleteDoc(e){const id=Number(e.currentTarget.dataset.deleteDoc);if(!confirm('Xóa tài liệu này?'))return;try{await api.deleteDocument(id);toast('Đã xóa tài liệu','success');render();}catch(err){toast(err.message,'danger')}}

async function submitConversation(e){e.preventDefault();const btn=e.submitter;setBusy(btn,true);const fd=new FormData(e.currentTarget);const ids=[...e.currentTarget.querySelector('[name=document_ids]').selectedOptions].map(x=>Number(x.value));try{const c=await api.createConversation({title:fd.get('title')||null,subject_id:fd.get('subject_id')?Number(fd.get('subject_id')):null,document_ids:ids});closeModal();toast('Đã tạo cuộc trò chuyện','success');location.hash='#/chat';await render();openConversation(c.id).then(bindModalEvents);}catch(err){toast(err.message,'danger');setBusy(btn,false)}}
async function submitChat(e){e.preventDefault();const btn=e.submitter;const form=e.currentTarget;const id=Number(form.dataset.chatForm);const fd=new FormData(form);const q=String(fd.get('question')||'').trim();if(!q)return;setBusy(btn,true,'Đang hỏi…');const messages=document.querySelector('[data-chat-messages]');messages?.insertAdjacentHTML('beforeend',`<div class="message user"><div class="message-role">Bạn</div><div class="bubble">${esc(q)}</div></div><div class="message assistant pending"><div class="message-role">AI</div><div class="bubble"><span class="typing"><i></i><i></i><i></i></span></div></div>`);form.querySelector('textarea').value='';try{const r=await api.ask(id,{question:q,input_mode:'TEXT',top_k:Number(fd.get('top_k')||5)});document.querySelector('.message.pending')?.remove();messages?.insertAdjacentHTML('beforeend',`<div class="message assistant"><div class="message-role">AI</div><div class="bubble">${esc(r.answer)}</div>${r.model_name?`<small>${esc(r.model_name)}</small>`:''}${r.citations?.length?`<div class="citation-list">${r.citations.map(c=>`<details><summary>Chunk #${c.chunk_id} · score ${c.similarity_score==null?'—':Number(c.similarity_score).toFixed(3)}</summary><p>${esc(c.excerpt)}</p></details>`).join('')}</div>`:''}</div>`);messages?.scrollTo(0,999999);}catch(err){document.querySelector('.message.pending')?.remove();toast(err.message,'danger')}finally{setBusy(btn,false)}}

function openManualQuizModal(){modal({title:'Tạo quiz thủ công',body:`<form id="manual-quiz-form" class="stack-form"><label>Tiêu đề<input class="input" name="title" required value="Quiz thủ công"></label><label>Subject ID (tuỳ chọn)<input class="input" type="number" name="subject_id" min="1"></label><div class="two-col"><label>Độ khó<select class="input" name="difficulty"><option>MEDIUM</option><option>EASY</option><option>HARD</option><option>MIXED</option></select></label><label>Visibility<select class="input" name="visibility"><option>PRIVATE</option><option>UNLISTED</option><option>PUBLIC</option></select></label></div><label>Questions JSON<textarea class="input code-input" name="questions" rows="13">[\n  {\n    "question_text": "Ví dụ: Khái niệm nào đúng?",\n    "difficulty": "MEDIUM",\n    "points": 1,\n    "options": [\n      {"option_key":"A","option_text":"Đáp án A","is_correct":true,"position":1},\n      {"option_key":"B","option_text":"Đáp án B","is_correct":false,"position":2},\n      {"option_key":"C","option_text":"Đáp án C","is_correct":false,"position":3},\n      {"option_key":"D","option_text":"Đáp án D","is_correct":false,"position":4}\n    ]\n  }\n]</textarea></label><button class="btn btn-primary" type="submit">Tạo quiz</button></form>`});bindModalEvents();}
async function submitManualQuiz(e){e.preventDefault();const btn=e.submitter;setBusy(btn,true);const fd=new FormData(e.currentTarget);try{const payload={title:fd.get('title'),difficulty:fd.get('difficulty'),visibility:fd.get('visibility'),subject_id:fd.get('subject_id')?Number(fd.get('subject_id')):null,document_ids:[],questions:JSON.parse(fd.get('questions'))};await api.createQuiz(payload);closeModal();toast('Đã tạo quiz thủ công','success');render();}catch(err){toast(err.message,'danger');setBusy(btn,false)}}
async function submitGenerateQuiz(e){
  e.preventDefault();
  const btn=e.submitter;
  const form=e.currentTarget;
  setBusy(btn,true,'Đang tạo quiz…');

  const fd=new FormData(form);
  const mode=String(fd.get('mode')||'v5');
  const subjectId=fd.get('subject_id')?Number(fd.get('subject_id')):null;
  const documentIds=[...form.querySelectorAll('select[name="document_ids"] option:checked')]
    .map(option=>Number(option.value))
    .filter(Number.isFinite);
  const questionCount=Number(fd.get('question_count')||5);
  const difficulty=String(fd.get('difficulty')||'MEDIUM');
  const durationMinutes=fd.get('duration_minutes')?Number(fd.get('duration_minutes')):null;

  try{
    if(mode==='v5'){
      if(!subjectId) throw new Error('Quiz V5 cần chọn môn học.');
      if(!documentIds.length) throw new Error('Quiz V5 cần chọn ít nhất một tài liệu READY.');

      const payload={
        title:fd.get('title'),
        subject_id:subjectId,
        document_ids:documentIds,
        question_count:Math.max(1,Math.min(5,questionCount)),
        difficulty,
        duration_minutes:durationMinutes,
        visibility:String(fd.get('visibility')||'PRIVATE'),
        subject_family:String(fd.get('subject_family')||'general'),
        max_per_section:Number(fd.get('max_per_section')||2),
      };

      await api.generateQuizV5(payload);
      closeModal();
      toast('Quiz V5 deterministic đã được tạo','success');
      render();
      return;
    }

    const payload={
      title:fd.get('title'),
      subject_id:subjectId,
      document_ids:documentIds,
      question_count:questionCount,
      difficulty,
      duration_minutes:durationMinutes,
    };

    const fn=mode==='weak'
      ? api.generateWeakQuiz
      : mode==='adaptive'
        ? api.generateAdaptiveQuiz
        : mode==='due'
          ? api.generateDueQuiz
          : api.generateQuiz;

    await fn(payload);
    closeModal();
    toast('AI quiz đã được tạo','success');
    render();
  }catch(err){
    console.error('[SSA quiz generation failed]',{
      status:err?.status,
      message:err?.message,
      data:err?.data,
      mode,
      subjectId,
      documentIds,
    });

    const status=err?.status||'—';
    const detail=esc(err?.message||'Không có chi tiết lỗi từ backend');
    const hint=Number(err?.status)===422
      ? 'Quiz V5 chỉ lưu khi tạo đủ số câu hợp lệ từ tài liệu đã chọn. Hãy chọn tài liệu READY khác hoặc giảm số câu.'
      : Number(err?.status)===502
        ? 'Backend đã nhận request nhưng pipeline AI/quality-gate không tạo được dữ liệu hợp lệ.'
        : 'Kiểm tra môn học, tài liệu nguồn và terminal backend để xác định nguyên nhân.';

    modal({
      title:'Không tạo được quiz',
      body:`<div class="quiz-error-panel"><div class="quiz-error-status"><span>HTTP</span><strong>${esc(status)}</strong></div><div><span class="eyebrow">Chi tiết backend</span><p class="quiz-error-detail">${detail}</p><p class="muted">${esc(hint)}</p></div></div>`,
      actions:`<button class="btn btn-primary" data-modal-close>Đóng</button>`
    });
    toast(`Tạo quiz thất bại (HTTP ${status})`,'danger');
    setBusy(btn,false);
  }
}
async function publishQuiz(e){const btn=e.currentTarget;setBusy(btn,true);try{await api.publishQuiz(Number(btn.dataset.publishQuiz));toast('Quiz đã publish','success');closeModal();render();}catch(err){toast(err.message,'danger');setBusy(btn,false)}}
async function submitAttempt(e){e.preventDefault();const btn=e.submitter;setBusy(btn,true,'Đang chấm…');const form=e.currentTarget;const answers=[...form.querySelectorAll('fieldset')].map(fs=>{const q=fs.querySelector('input[type=radio]');const checked=fs.querySelector('input[type=radio]:checked');return{question_id:Number(q.name.replace('q_','')),selected_option_id:checked?Number(checked.value):null}});try{const r=await api.submitAttempt(Number(form.dataset.attemptId),answers);modal({title:'Kết quả quiz',body:`<div class="result-score"><strong>${Number(r.percentage??0).toFixed(1)}%</strong><span>${r.correct_count} đúng · ${r.wrong_count} sai · ${r.unanswered_count} bỏ trống</span></div><div class="score-bar"><i style="width:${Math.max(0,Math.min(100,Number(r.percentage||0)))}%"></i></div>`,actions:`<button class="btn btn-primary" data-modal-close>Kết thúc</button>`});}catch(err){toast(err.message,'danger');setBusy(btn,false)}}

async function submitGenerateDeck(e){
  e.preventDefault();
  const btn=e.submitter;
  const form=e.currentTarget;
  setBusy(btn,true,'AI đang tạo thẻ…');
  const fd=new FormData(form);
  const documentIds=[...form.querySelectorAll('select[name="document_ids"] option:checked')]
    .map(option=>Number(option.value))
    .filter(Number.isFinite);

  try{
    await api.generateDeck({
      title:fd.get('title'),
      subject_id:fd.get('subject_id')?Number(fd.get('subject_id')):null,
      document_ids:documentIds,
      card_count:Number(fd.get('card_count')),
    });
    closeModal();
    toast('Đã tạo flashcard deck','success');
    render();
  }catch(err){
    toast(err.message,'danger');
    setBusy(btn,false);
  }
}
async function submitGeneratePlan(e){e.preventDefault();const btn=e.submitter;setBusy(btn,true);const fd=new FormData(e.currentTarget);try{await api.generateStudyPlan({title:fd.get('title'),subject_id:fd.get('subject_id')?Number(fd.get('subject_id')):null,start_date:fd.get('start_date'),exam_date:fd.get('exam_date'),daily_minutes:Number(fd.get('daily_minutes'))});closeModal();toast('Đã tạo kế hoạch học','success');render();}catch(err){toast(err.message,'danger');setBusy(btn,false)}}
async function updateTask(e){try{await api.updateStudyTask(Number(e.target.dataset.task),e.target.value);toast('Đã cập nhật task','success')}catch(err){toast(err.message,'danger')}}

async function submitCommunity(e){e.preventDefault();const btn=e.submitter;setBusy(btn,true);const fd=new FormData(e.currentTarget);const deck=fd.get('resource_type')==='FLASHCARD_DECK';const payload={quiz_id:deck?null:Number(fd.get('quiz_id')),flashcard_deck_id:deck?Number(fd.get('flashcard_deck_id')):null,title:fd.get('title')||null,description:fd.get('description')||null};try{await api.publishCommunity(payload);closeModal();toast('Đã chia sẻ lên cộng đồng','success');render();}catch(err){toast(err.message,'danger');setBusy(btn,false)}}
async function communityLike(e){try{const r=await api.likePost(Number(e.currentTarget.dataset.likePost));e.currentTarget.textContent=r.liked?'♥ Liked':'♡ Like'}catch(err){toast(err.message,'danger')}}
async function communitySave(e){try{const r=await api.savePost(Number(e.currentTarget.dataset.savePost));e.currentTarget.textContent=r.saved?'▣ Saved':'⌑ Save'}catch(err){toast(err.message,'danger')}}
async function communityFork(e){const btn=e.currentTarget;setBusy(btn,true);try{const r=await api.forkPost(Number(btn.dataset.forkPost));toast(`Đã fork ${r.resource_type} #${r.resource_id}`,'success');setBusy(btn,false)}catch(err){toast(err.message,'danger');setBusy(btn,false)}}
async function submitExport(e){e.preventDefault();const btn=e.submitter;setBusy(btn,true,'Đang xuất…');const fd=new FormData(e.currentTarget);try{await api.createExport({resource_type:fd.get('resource_type'),resource_id:Number(fd.get('resource_id')),file_format:fd.get('file_format')});closeModal();toast('Export đã được tạo','success');render();}catch(err){toast(err.message,'danger');setBusy(btn,false)}}
async function markRead(e){try{await api.markNotificationRead(Number(e.currentTarget.dataset.readNotif));render()}catch(err){toast(err.message,'danger')}}
async function saveProfile(e){e.preventDefault();const btn=e.submitter;setBusy(btn,true);const fd=new FormData(e.currentTarget);try{await api.updateMe({full_name:fd.get('full_name')||undefined,avatar_url:fd.get('avatar_url')||null,timezone:fd.get('timezone')||undefined,locale:fd.get('locale')||undefined});const user=await api.me();saveAuth({...state.auth,user});toast('Đã lưu hồ sơ và cập nhật avatar','success');render();}catch(err){toast(err.message,'danger');setBusy(btn,false)}}

function initParallax(){const stage=document.querySelector('[data-parallax-stage]');if(!stage||matchMedia('(pointer: coarse)').matches)return;stage.addEventListener('pointermove',e=>{const r=stage.getBoundingClientRect();const x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;stage.querySelectorAll('[data-depth]').forEach(el=>{const d=Number(el.dataset.depth||1);el.style.setProperty('--mx',`${x*18*d}px`);el.style.setProperty('--my',`${y*18*d}px`);});});stage.addEventListener('pointerleave',()=>stage.querySelectorAll('[data-depth]').forEach(el=>{el.style.setProperty('--mx','0px');el.style.setProperty('--my','0px');}));}

let sidebarResizeTimer;
window.addEventListener('resize',()=>{
  clearTimeout(sidebarResizeTimer);
  sidebarResizeTimer=setTimeout(()=>{
    if(!usesOverlaySidebar()){
      setSidebarDrawer(false);
      document.body.classList.remove('sidebar-drawer-open');
    }
  },120);
});

window.addEventListener('hashchange',render);
window.addEventListener('ssa:auth-expired',()=>{toast('Phiên đăng nhập đã hết hạn','warning');location.hash='#/';render();});
window.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal();});

async function bootstrap(){
  if(isAuthed()){
    try{const user=await api.me();saveAuth({...state.auth,user});}catch(err){if(err.status===401)logoutLocal();}
  }
  await render();
  setTimeout(()=>document.getElementById('page-loader')?.classList.add('hidden'),350);
}
bootstrap();
