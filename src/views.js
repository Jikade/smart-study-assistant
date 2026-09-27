// SSA-FE-LR-V1
import { api, ENDPOINT_CATALOG } from './api.js';
import { state, saveAuth, saveUi, logoutLocal, isAuthed } from './state.js';
import { esc, fmtDate, fmtBytes, toast, modal, closeModal, button, badge, emptyState, skeletonCards, setBusy, icon, revealElements, initTilt } from './ui.js';

const nav = [
  ['/', 'home', 'Tổng quan'], ['subjects','book','Môn học'], ['documents','file','Tài liệu'], ['chat','chat','AI Chat'],
  ['quizzes','quiz','Quiz'], ['flashcards','cards','Flashcards'], ['study-plans','plan','Kế hoạch'], ['analytics','chart','Phân tích'],
  ['community','globe','Cộng đồng'], ['exports','download','Xuất file'], ['notifications','bell','Thông báo'], ['profile','user','Hồ sơ']
];

function routeTo(path){ location.hash = `#${path.startsWith('/')?path:`/${path}`}`; }
function pageHeader(kicker,title,desc,actions=''){ return `<section class="page-heading reveal"><div><span class="eyebrow">${esc(kicker)}</span><h1>${title}</h1><p>${esc(desc)}</p></div>${actions?`<div class="heading-actions">${actions}</div>`:''}</section>`; }
function surface(inner, cls=''){ return `<div class="surface ${cls}">${inner}</div>`; }
function statusTone(status=''){ const s=String(status).toUpperCase(); if(['READY','ACTIVE','PUBLISHED','COMPLETED','STRONG','SUCCEEDED'].includes(s))return'success'; if(['FAILED','WEAK','REMOVED'].includes(s))return'danger'; if(['PROCESSING','RUNNING','DEVELOPING','IN_PROGRESS'].includes(s))return'warning'; return'neutral'; }
function selectedSubject(){ return Number(state.ui.selectedSubjectId) || null; }
async function getSubjects(){ const r=await api.listSubjects({limit:100,offset:0}); return r.items||[]; }
async function subjectSelect(name='subject_id', value=selectedSubject(), allowNone=true){ const subjects=await getSubjects(); return `<select name="${name}" class="input"><option value="">${allowNone?'Không gắn môn học':'Chọn môn học'}</option>${subjects.map(s=>`<option value="${s.id}" ${Number(value)===s.id?'selected':''}>${esc(s.name)}</option>`).join('')}</select>`; }
function formDataObject(form){ return Object.fromEntries(new FormData(form).entries()); }

function avatarMarkup(user, cls='avatar') {
  const name = String(user?.full_name || 'Sinh viên');
  const initial = esc((name[0] || 'S').toUpperCase());
  const rawUrl = String(user?.avatar_url || '').trim();
  if (!rawUrl) return `<div class="${cls}"><span>${initial}</span></div>`;
  const url = esc(rawUrl);
  return `<div class="${cls} has-image"><img src="${url}" alt="${esc(name)}" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove();this.parentElement.classList.remove('has-image')"><span>${initial}</span></div>`;
}

export function shell(content, route='/', {publicPage=false}={}){
  if(publicPage) return content;
  const user=state.auth?.user;
  return `<div class="app-shell ${state.ui.sidebarCollapsed?'sidebar-collapsed':''}">
    <aside class="sidebar ${state.ui.sidebarOpen?'open':''}" aria-label="Điều hướng chính">
      <div class="sidebar-header">
        <a class="brand" href="#/" title="Smart Study Assistant"><div class="brand-mark">S</div><div class="brand-copy"><strong>Smart Study</strong><span>Assistant</span></div></a>
        <button class="icon-btn sidebar-collapse-btn" data-sidebar-collapse title="${state.ui.sidebarCollapsed?'Mở rộng sidebar':'Thu gọn sidebar'}" aria-label="${state.ui.sidebarCollapsed?'Mở rộng sidebar':'Thu gọn sidebar'}">${icon('menu')}</button>
      </div>
      <div class="sidebar-scroll">
        <nav>${nav.map(([path,ic,label])=>`<a href="#/${path==='/'?'':path}" title="${esc(label)}" class="nav-link ${(route==='/'?path==='/':route.startsWith('/'+path))?'active':''}">${icon(ic)}<span class="nav-label">${label}</span></a>`).join('')}</nav>
        <div class="sidebar-card"><span class="eyebrow sidebar-card-copy">API runtime</span><strong><span class="endpoint-count">62</span><span class="endpoint-label"> endpoints</span></strong><small class="sidebar-card-copy">FastAPI · PostgreSQL · RAG</small><a class="sidebar-card-link" href="#/developer"><span class="sidebar-card-copy">Xem endpoint map</span>${icon('arrow')}</a></div>
        <div class="sidebar-user">${avatarMarkup(user,'avatar')}<div class="user-copy"><strong>${esc(user?.full_name||'Sinh viên')}</strong><small>${esc(user?.email||'')}</small></div><button class="icon-btn" data-logout title="Đăng xuất" aria-label="Đăng xuất">${icon('arrow')}</button></div>
      </div>
    </aside>
    <div class="mobile-scrim ${state.ui.sidebarOpen?'show':''}" data-sidebar-close></div>
    <main class="main"><header class="topbar"><button class="icon-btn menu-btn" data-sidebar-toggle title="Mở menu" aria-label="Mở menu">${icon('menu')}</button><div class="topbar-status"><span class="pulse-dot"></span><span data-health-text>Đang kiểm tra backend…</span></div><div class="topbar-actions"><button class="icon-btn" data-go-notifications>${icon('bell')}<span class="notif-dot" data-notif-dot></span></button>${avatarMarkup(user,'mini-avatar')}</div></header><div class="page-transition"><div class="content">${content}</div></div></main>
  </div>`;
}

export function landing(){
 return `<div class="landing">
  <header class="landing-nav"><a class="brand" href="#/"><div class="brand-mark">S</div><div><strong>Smart Study</strong><span>Assistant</span></div></a><nav><a href="#features">Tính năng</a><a href="#workflow">Quy trình</a><a href="#tech">Công nghệ</a></nav><div class="landing-actions">${button('Đăng nhập',{variant:'ghost',attrs:'data-open-login'})}${button('Bắt đầu học',{attrs:'data-open-register'})}</div></header>
  <section class="hero"><div class="hero-copy reveal"><span class="eyebrow pill">Học sâu hơn · nhớ lâu hơn · có dẫn chứng</span><h1>Biến tài liệu thành<br><em>hệ sinh thái học tập</em><br>của riêng bạn.</h1><p>Upload tài liệu, hỏi đáp RAG, tạo quiz thích ứng, flashcards lặp lại ngắt quãng, kế hoạch ôn tập và phân tích điểm yếu — tất cả trong một trải nghiệm duy nhất.</p><div class="hero-cta">${button('Dùng thử ngay',{iconName:'spark',attrs:'data-open-register'})}<a href="#workflow" class="text-link">Xem cách hoạt động ${icon('arrow')}</a></div><div class="trust-row"><span><b>59</b> API endpoint</span><span><b>RAG</b> grounded</span><span><b>SSA-SR</b> spaced repetition</span></div></div>
  <div class="hero-stage reveal" data-parallax-stage>
    <div class="stage-ring ring-one"></div><div class="stage-ring ring-two"></div>
    <div class="buddy buddy-main" data-depth="1.6"><div class="buddy-face"><i></i><i></i><b></b></div><span class="buddy-label">AI Tutor</span></div>
    <div class="buddy buddy-small one" data-depth="2.4"><div class="buddy-face"><i></i><i></i><b></b></div></div>
    <div class="buddy buddy-small two" data-depth="1.2"><div class="buddy-face"><i></i><i></i><b></b></div></div>
    <div class="float-card fc-one" data-depth="2"><span>Mastery</span><strong>82%</strong><div class="mini-progress"><i style="width:82%"></i></div></div>
    <div class="float-card fc-two" data-depth="1.4"><span>Streak</span><strong>🔥 12 ngày</strong></div>
    <div class="sparkle s1">✦</div><div class="sparkle s2">✦</div><div class="sparkle s3">✦</div>
  </div></section>
  <section class="marquee"><div>RAG • QUIZ ADAPTIVE • FLASHCARDS • SPACED REPETITION • ANALYTICS • COMMUNITY • EXPORT • <span>RAG • QUIZ ADAPTIVE • FLASHCARDS • SPACED REPETITION • ANALYTICS • COMMUNITY • EXPORT •</span></div></section>
  <section id="features" class="landing-section"><div class="section-intro reveal"><span class="eyebrow">Học theo cách não bộ cần</span><h2>Mỗi tính năng là một <em>vòng lặp học tập.</em></h2></div><div class="feature-grid">
   ${[['01','Tài liệu → tri thức','PDF, DOCX, TXT được xử lý, chia chunk cấu trúc và embedding để truy xuất có căn cứ.','peach'],['02','Quiz biết bạn yếu gì','Quiz thường, weak-topic, adaptive và due giúp luyện đúng phần cần ưu tiên.','lime'],['03','Flashcards đúng thời điểm','SSA-SR lên lịch ôn lại dựa trên phản hồi Again / Hard / Good / Easy.','lavender'],['04','Analytics thành hành động','Mastery, weak topics, recommendations và spaced study-plan chuyển dữ liệu thành bước học tiếp theo.','sky']].map(([n,t,d,c])=>`<article class="feature-card ${c} reveal" data-tilt><span>${n}</span><h3>${t}</h3><p>${d}</p><div class="feature-arrow">${icon('arrow')}</div></article>`).join('')}
  </div></section>
  <section id="workflow" class="story-section"><div class="story-sticky"><span class="eyebrow">Một vòng học hoàn chỉnh</span><h2>Từ file thô tới<br><em>tiến bộ đo được.</em></h2></div><div class="story-steps">${[['Upload','Đưa giáo trình vào hệ thống.'],['Ground','Chunk + embedding + retrieval bảo toàn nguồn.'],['Practice','Chat, quiz và flashcards biến đọc thụ động thành luyện tập.'],['Measure','Mastery và streak phản hồi ngược vào kế hoạch học.']].map((x,i)=>`<div class="story-step reveal"><b>0${i+1}</b><div><h3>${x[0]}</h3><p>${x[1]}</p></div></div>`).join('')}</div></section>
  <section id="tech" class="cta-section reveal"><div class="cta-buddy"><div class="buddy buddy-static"><div class="buddy-face"><i></i><i></i><b></b></div></div></div><div><span class="eyebrow">Sẵn sàng kết nối backend</span><h2>Học thông minh không cần giao diện phức tạp.</h2><p>Frontend này map trực tiếp API FastAPI hiện tại và tự làm mới access token khi hết hạn.</p>${button('Tạo tài khoản',{attrs:'data-open-register'})}</div></section>
  <footer><div class="brand"><div class="brand-mark">S</div><div><strong>Smart Study</strong><span>Assistant</span></div></div><p>Designed for focused learning.</p><a href="https://github.com/Jikade/smart-study-assistant-backend" target="_blank">Backend repository ↗</a></footer>
 </div>`;
}

export function authModal(mode='login'){
 const isLogin=mode==='login';
 modal({ title:isLogin?'Chào mừng bạn quay lại':'Tạo không gian học tập', body:`<form id="auth-form" class="stack-form" data-mode="${mode}">${!isLogin?`<label>Họ và tên<input class="input" name="full_name" required minlength="2" placeholder="Nguyễn Văn A"></label>`:''}<label>Email<input class="input" name="email" type="email" required placeholder="student@example.com"></label><label>Mật khẩu<input class="input" name="password" type="password" required minlength="8" placeholder="Tối thiểu 8 ký tự"></label><button class="btn btn-primary btn-block" type="submit">${isLogin?'Đăng nhập':'Tạo tài khoản'}</button><p class="form-switch">${isLogin?'Chưa có tài khoản? <a href="#" data-switch-register>Đăng ký</a>':'Đã có tài khoản? <a href="#" data-switch-login>Đăng nhập</a>'}</p></form>` });
}

export async function dashboard(){
 const [subjects,docs,quizzes,decks,plans,gam,notifs] = await Promise.all([
  api.listSubjects({limit:6,offset:0}).catch(()=>({items:[],total:0})), api.listDocuments({limit:5,offset:0}).catch(()=>({items:[],total:0})), api.listQuizzes({limit:5}).catch(()=>[]), api.listDecks(5).catch(()=>[]), api.listStudyPlans().catch(()=>[]), api.gamification().catch(()=>null), api.notifications(true).catch(()=>[])
 ]);
 const content = `${pageHeader('Tổng quan','Hôm nay học gì?','Một màn hình để nhìn thấy nhịp học, tài liệu và nhiệm vụ quan trọng nhất.',button('Upload tài liệu',{iconName:'plus',attrs:'data-quick-upload'}))}
 <section class="stats-grid reveal"><div class="stat-card accent-black"><span>XP tổng</span><strong>${gam?.xp_total??0}</strong><small>Level ${gam?.level_no??1}</small></div><div class="stat-card accent-lime"><span>Chuỗi học</span><strong>${gam?.current_streak??0}</strong><small>ngày liên tiếp</small></div><div class="stat-card accent-peach"><span>Tài liệu</span><strong>${docs.total??0}</strong><small>${docs.items?.filter(d=>d.status==='READY').length||0} file READY gần đây</small></div><div class="stat-card accent-lavender"><span>Thông báo</span><strong>${notifs.length}</strong><small>chưa đọc</small></div></section>
 <section class="dashboard-grid"><div>${surface(`<div class="surface-head"><div><span class="eyebrow">Môn học</span><h3>Không gian đang hoạt động</h3></div><a href="#/subjects">Xem tất cả</a></div>${subjects.items?.length?`<div class="subject-list">${subjects.items.map(s=>`<button class="subject-row" data-open-subject="${s.id}"><span class="subject-dot" style="--dot:${esc(s.color_hex||'#b8ff5a')}"></span><div><strong>${esc(s.name)}</strong><small>${esc(s.description||'Chưa có mô tả')}</small></div>${icon('arrow')}</button>`).join('')}</div>`:emptyState('Chưa có môn học','Tạo môn học đầu tiên để gom tài liệu, quiz và analytics.')}`,'reveal')}</div>
 <div>${surface(`<div class="surface-head"><div><span class="eyebrow">Tiến độ</span><h3>Nhịp học</h3></div></div><div class="level-orbit"><div class="level-ring" style="--p:${Math.min(100,(gam?.xp_total||0)%100)}"><span>${gam?.level_no??1}</span></div><div><strong>Level ${gam?.level_no??1}</strong><p>Longest streak: ${gam?.longest_streak??0} ngày</p></div></div>${gam?.recent_xp?.slice(0,4).map(x=>`<div class="xp-row"><span>+${x.amount} XP</span><small>${esc(x.description||x.source_type)}</small></div>`).join('')||'<p class="muted">Chưa có giao dịch XP.</p>'}`,'reveal')}</div></section>
 <section>${surface(`<div class="surface-head"><div><span class="eyebrow">Gần đây</span><h3>Tiếp tục học</h3></div></div><div class="continue-grid">${docs.items?.slice(0,2).map(d=>`<article class="continue-card"><span class="file-chip">${esc((d.file_extension||'FILE').replace('.','').toUpperCase())}</span><h4>${esc(d.original_name)}</h4>${badge(d.status,statusTone(d.status))}<button class="text-button" data-doc-id="${d.id}">Mở tài liệu ${icon('arrow')}</button></article>`).join('')||''}${quizzes.slice(0,1).map(q=>`<article class="continue-card dark"><span class="file-chip">QUIZ</span><h4>${esc(q.title)}</h4><p>${q.question_count} câu · ${esc(q.difficulty)}</p><button class="text-button light" data-quiz-id="${q.id}">Luyện ngay ${icon('arrow')}</button></article>`).join('')||''}${decks.slice(0,1).map(d=>`<article class="continue-card purple"><span class="file-chip">DECK</span><h4>${esc(d.title)}</h4><p>${esc(d.generation_mode)} · ${esc(d.status)}</p><button class="text-button" data-deck-id="${d.id}">Ôn flashcards ${icon('arrow')}</button></article>`).join('')||''}</div>`,'reveal')}</section>`;
 return content;
}

export async function subjectsView(){ const r=await api.listSubjects({limit:100,offset:0}); return `${pageHeader('Môn học','Tổ chức kiến thức theo ngữ cảnh.','Mỗi môn học là một không gian độc lập cho tài liệu, quiz, chat và analytics.',button('Tạo môn học',{iconName:'plus',attrs:'data-create-subject'}))}${r.items.length?`<div class="card-grid">${r.items.map(s=>`<article class="surface subject-card reveal" data-tilt><div class="subject-cover" style="--subject:${esc(s.color_hex||'#b8ff5a')}"><span>${esc(s.name.slice(0,2).toUpperCase())}</span></div><div class="subject-card-body"><div class="row-between"><h3>${esc(s.name)}</h3>${badge(s.is_archived?'Archived':'Active',s.is_archived?'neutral':'success')}</div><p>${esc(s.description||'Chưa có mô tả.')}</p><div class="card-actions"><button class="btn btn-soft" data-open-subject="${s.id}">Mở</button><button class="icon-btn" data-edit-subject='${esc(JSON.stringify(s))}'>✎</button><button class="icon-btn danger" data-delete-subject="${s.id}">${icon('trash')}</button></div></div></article>`).join('')}</div>`:emptyState('Chưa có môn học','Tạo môn học đầu tiên để bắt đầu.',button('Tạo môn học',{attrs:'data-create-subject'}))}`; }

export async function documentsView(){ const r=await api.listDocuments({limit:100,offset:0}); return `${pageHeader('Thư viện','Tài liệu là nguồn sự thật.','Quản lý file, xử lý chunk và embedding trước khi dùng cho RAG/quiz.',button('Upload tài liệu',{iconName:'plus',attrs:'data-upload-document'}))}${surface(`<div class="table-wrap"><table><thead><tr><th>Tài liệu</th><th>Trạng thái</th><th>Kích thước</th><th>Trang</th><th>Cập nhật</th><th></th></tr></thead><tbody>${r.items.map(d=>`<tr><td><div class="doc-name"><span class="file-chip">${esc((d.file_extension||'file').replace('.','').toUpperCase())}</span><div><strong>${esc(d.original_name)}</strong><small>${esc(d.mime_type||'')}</small></div></div></td><td>${badge(d.status,statusTone(d.status))}</td><td>${fmtBytes(d.file_size_bytes)}</td><td>${d.page_count??'—'}</td><td>${fmtDate(d.updated_at,true)}</td><td><div class="table-actions"><button class="icon-btn" title="Xem" data-doc-id="${d.id}">${icon('arrow')}</button><button class="icon-btn" title="Process" data-process-doc="${d.id}">${icon('spark')}</button><button class="icon-btn danger" data-delete-doc="${d.id}">${icon('trash')}</button></div></td></tr>`).join('')}</tbody></table></div>`,'reveal')}`; }

export async function chatView(){ const convos=await api.listConversations(50); return `${pageHeader('AI Chat','Hỏi từ chính tài liệu của bạn.','Câu trả lời RAG đi kèm citations để bạn truy về chunk nguồn.',button('Cuộc trò chuyện mới',{iconName:'plus',attrs:'data-new-conversation'}))}<div class="chat-layout"><aside class="surface conversation-list reveal"><h3>Cuộc trò chuyện</h3>${convos.length?convos.map(c=>`<button class="conversation-item" data-conversation="${c.id}"><span>${icon('chat')}</span><div><strong>${esc(c.title||`Conversation #${c.id}`)}</strong><small>${fmtDate(c.updated_at,true)}</small></div></button>`).join(''):'<p class="muted">Chưa có cuộc trò chuyện.</p>'}</aside><section class="surface chat-panel reveal" id="chat-panel">${emptyState('Chọn một cuộc trò chuyện','Hoặc tạo mới để bắt đầu hỏi tài liệu.')}</section></div>`; }

export async function quizzesView(){ const items=await api.listQuizzes({limit:100}); return `${pageHeader('Quiz','Luyện tập có chủ đích.','Tạo thủ công hoặc dùng AI: normal, weak-topic, adaptive và due.',`<div class="button-cluster">${button('Tạo AI quiz',{iconName:'spark',attrs:'data-generate-quiz'})}${button('Tạo thủ công',{variant:'soft',attrs:'data-create-quiz'})}</div>`)}${items.length?`<div class="card-grid">${items.map(q=>`<article class="surface quiz-card reveal" data-tilt><div class="quiz-top"><span class="quiz-index">${String(q.id).padStart(2,'0')}</span>${badge(q.status,statusTone(q.status))}</div><h3>${esc(q.title)}</h3><p>${esc(q.description||`${q.question_count} câu hỏi`)}</p><div class="meta-row"><span>${esc(q.difficulty)}</span><span>${q.duration_minutes?`${q.duration_minutes} phút`:'Không giới hạn'}</span><span>${esc(q.generation_mode)}</span></div><div class="card-actions">${button('Mở quiz',{variant:'soft',attrs:`data-quiz-id="${q.id}"`})}${q.status!=='PUBLISHED'?button('Publish',{variant:'ghost',attrs:`data-publish-quiz="${q.id}"`}):''}</div></article>`).join('')}</div>`:emptyState('Chưa có quiz','Tạo quiz đầu tiên từ tài liệu của bạn.')}`; }

export async function flashcardsView(){
  // SSA-FE-LR-V1: one auxiliary request must not make the whole page unusable.
  const [decksResult,dueResult]=await Promise.allSettled([
    api.listDecks(100),
    api.dueCards(100),
  ]);

  if(decksResult.status!=='fulfilled') throw decksResult.reason;

  const decks=decksResult.value||[];
  const due=dueResult.status==='fulfilled'?(dueResult.value||[]):[];
  const dueWarning=dueResult.status==='rejected'
    ? `<div class="surface reveal"><div class="error-box">Không tải được lịch flashcard đến hạn: ${esc(dueResult.reason?.message||'Unknown error')}. Danh sách deck vẫn được hiển thị.</div></div>`
    : '';

  return `${pageHeader(
    'Flashcards',
    'Ôn đúng lúc, không ôn quá mức.',
    'Rating 0–3 cập nhật lịch review theo spaced repetition.',
    `<div class="button-cluster">${button(
      `Ôn ${due.length} thẻ đến hạn`,
      {attrs:'data-review-due'}
    )}${button(
      'Tạo deck AI',
      {variant:'soft',attrs:'data-generate-deck'}
    )}</div>`
  )}${dueWarning}<div class="stats-grid compact"><div class="stat-card accent-lime"><span>Đến hạn</span><strong>${due.length}</strong></div><div class="stat-card accent-lavender"><span>Deck</span><strong>${decks.length}</strong></div></div>${decks.length?`<div class="card-grid">${decks.map(d=>`<article class="surface deck-card reveal" data-tilt><div class="deck-stack"><i></i><i></i><span>${esc(d.title.slice(0,1).toUpperCase())}</span></div><div><div class="row-between"><h3>${esc(d.title)}</h3>${badge(d.status,statusTone(d.status))}</div><p>${esc(d.description||'Bộ thẻ học tập')}</p><div class="meta-row"><span>${esc(d.generation_mode)}</span><span>${esc(d.visibility)}</span></div>${button('Mở deck',{variant:'soft',attrs:`data-deck-id="${d.id}"`})}</div></article>`).join('')}</div>`:emptyState('Chưa có flashcard deck','Hãy tạo deck từ tài liệu để bắt đầu lặp lại ngắt quãng.')}`;
}

export async function studyPlansView(){ const plans=await api.listStudyPlans(); return `${pageHeader('Kế hoạch học','Biến deadline thành lịch học vừa sức.','Tạo kế hoạch theo ngày thi và ngân sách phút học mỗi ngày.',button('Tạo kế hoạch',{iconName:'plus',attrs:'data-generate-plan'}))}${plans.length?`<div class="plan-list">${plans.map(p=>`<article class="surface plan-row reveal"><div class="plan-date"><b>${new Date(p.exam_date||p.start_date).getDate()}</b><span>${new Intl.DateTimeFormat('vi-VN',{month:'short'}).format(new Date(p.exam_date||p.start_date))}</span></div><div class="plan-main"><div class="row-between"><h3>${esc(p.title)}</h3>${badge(p.status,statusTone(p.status))}</div><p>${fmtDate(p.start_date)} → ${fmtDate(p.exam_date)} · ${p.daily_minutes} phút/ngày</p></div><button class="btn btn-soft" data-plan-id="${p.id}">Mở kế hoạch</button></article>`).join('')}</div>`:emptyState('Chưa có kế hoạch','Tạo kế hoạch dựa trên ngày bắt đầu, ngày thi và thời lượng học mỗi ngày.')}`; }

export async function analyticsView(){
  const subjects=await getSubjects();
  const sid=selectedSubject()||subjects[0]?.id;

  if(!sid) return `${pageHeader(
    'Analytics',
    'Đọc dữ liệu học tập.',
    'Mastery, weak topics và recommendations giúp quyết định học gì tiếp theo.'
  )}${emptyState(
    'Cần ít nhất một môn học',
    'Tạo môn học và luyện quiz để analytics có dữ liệu.'
  )}`;

  saveUi({selectedSubjectId:sid});

  // SSA-FE-LR-V1: mastery is the primary dataset.  Optional analytics
  // panels degrade independently instead of crashing the whole route.
  const [masteryResult,weakResult,recsResult,planResult]=await Promise.allSettled([
    api.topicMastery(sid),
    api.weakTopics(sid),
    api.practiceRecommendations(sid),
    api.analyticsStudyPlan(sid,7),
  ]);

  if(masteryResult.status!=='fulfilled') throw masteryResult.reason;

  const mastery=masteryResult.value;
  const weak=weakResult.status==='fulfilled'
    ? weakResult.value
    : {count:0,topics:[]};
  const recs=recsResult.status==='fulfilled'
    ? recsResult.value
    : {strategy:'Unavailable',recommendations:[]};
  const plan=planResult.status==='fulfilled'
    ? planResult.value
    : {algorithm:'Unavailable',days:[]};

  const warnings=[
    weakResult.status==='rejected'?'weak topics':null,
    recsResult.status==='rejected'?'recommendations':null,
    planResult.status==='rejected'?'study plan':null,
  ].filter(Boolean);

  const warningHtml=warnings.length
    ? `<section class="surface reveal"><div class="error-box">Một phần Analytics tạm thời không tải được: ${esc(warnings.join(', '))}. Topic mastery vẫn được hiển thị.</div></section>`
    : '';

  return `${pageHeader(
    'Analytics',
    esc(mastery.subject_name),
    'Theo dõi mức độ nắm vững từng topic và lịch spaced practice.',
    `<select class="input subject-switch" data-analytics-subject>${subjects.map(s=>`<option value="${s.id}" ${s.id===sid?'selected':''}>${esc(s.name)}</option>`).join('')}</select>`
  )}${warningHtml}<section class="stats-grid"><div class="stat-card accent-black"><span>Tổng topic</span><strong>${mastery.summary.total_topics}</strong></div><div class="stat-card accent-peach"><span>Weak</span><strong>${mastery.summary.weak_topics}</strong></div><div class="stat-card accent-lavender"><span>Developing</span><strong>${mastery.summary.developing_topics}</strong></div><div class="stat-card accent-lime"><span>Strong</span><strong>${mastery.summary.strong_topics}</strong></div></section><section class="analytics-grid"><div class="surface reveal"><div class="surface-head"><div><span class="eyebrow">Topic mastery</span><h3>Mức độ nắm vững</h3></div></div><div class="mastery-list">${mastery.topics.map(t=>{const score=Math.max(0,Math.min(100,Number(t.mastery_score||0)));return `<div class="mastery-row"><div><strong>${esc(t.title)}</strong><small>${t.attempts} attempts · ${t.correct_answers} đúng · ${score.toFixed(1)}%</small></div><div class="mastery-bar"><i style="width:${score}%"></i></div>${badge(t.status,statusTone(t.status))}</div>`;}).join('')||'<p class="muted">Chưa có topic data.</p>'}</div></div><div class="surface reveal"><div class="surface-head"><div><span class="eyebrow">Ưu tiên</span><h3>Đề xuất luyện tập</h3></div><span>${esc(recs.strategy||'')}</span></div><div class="recommend-list">${(recs.recommendations||[]).map(r=>`<div class="recommend-item"><b>#${r.rank}</b><div><strong>${esc(r.title)}</strong><p>${esc(r.reason)}</p></div></div>`).join('')||'<p class="muted">Chưa có đề xuất.</p>'}</div></div></section><section class="surface reveal"><div class="surface-head"><div><span class="eyebrow">7 ngày tới</span><h3>Spaced practice</h3></div><span>${esc(plan.algorithm||'')}</span></div><div class="timeline">${(plan.days||[]).map(d=>`<div class="timeline-day"><div class="timeline-date"><b>${new Date(d.date).getDate()}</b><span>${new Intl.DateTimeFormat('vi-VN',{weekday:'short'}).format(new Date(d.date))}</span></div><div>${d.items.map(i=>`<div class="timeline-item"><strong>${esc(i.title)}</strong><small>${i.interval_days} ngày · priority ${Number(i.priority_score).toFixed(2)} · ${esc(i.due_status)}</small></div>`).join('')||'<span class="muted">Không có topic</span>'}</div></div>`).join('')||'<p class="muted">Chưa có lịch spaced practice.</p>'}</div></section><section class="surface reveal"><div class="surface-head"><div><span class="eyebrow">Weak topics</span><h3>${weak.count||0} topic cần chú ý</h3></div></div><div class="chip-wrap">${(weak.topics||[]).map(x=>`<span class="topic-chip">${esc(x.title)} · ${Math.max(0,Math.min(100,Number(x.mastery_score||0))).toFixed(0)}%</span>`).join('')||'<span class="muted">Không có weak topic theo ngưỡng hiện tại.</span>'}</div></section>`;
}

export async function communityView(){ const posts=await api.communityPosts({limit:50,offset:0}); return `${pageHeader('Cộng đồng','Học cùng nhau mà không lộ nguồn riêng tư.','Publish quiz/deck, like, save và fork nội dung công khai.',button('Chia sẻ tài nguyên',{iconName:'plus',attrs:'data-publish-community'}))}${posts.length?`<div class="community-grid">${posts.map(p=>{const id=p.post_id??p.id; return `<article class="surface community-card reveal"><div class="community-visual ${p.resource_type==='QUIZ'?'visual-quiz':'visual-deck'}"><span>${esc(p.resource_type||'STUDY')}</span><b>${esc((p.title||'Shared resource').slice(0,1))}</b></div><div class="community-body"><span class="eyebrow">${esc(p.resource_type||'RESOURCE')}</span><h3>${esc(p.title||'Tài nguyên học tập')}</h3><p>${esc(p.description||'Được chia sẻ trong cộng đồng Smart Study.')}</p><div class="community-actions"><button class="chip-btn" data-like-post="${id}">${p.liked_by_me?'♥ Liked':'♡ Like'} · ${Number(p.like_count||0)}</button><button class="chip-btn" data-save-post="${id}">${p.saved_by_me?'▣ Saved':'⌑ Save'} · ${Number(p.save_count||0)}</button><button class="chip-btn dark" data-fork-post="${id}">Fork ↗</button></div></div></article>`}).join('')}</div>`:emptyState('Cộng đồng đang trống','Hãy publish một quiz hoặc flashcard deck đầu tiên.')}`; }

export async function exportsView(){ const rows=await api.listExports(); return `${pageHeader('Xuất file','Đưa nội dung ra khỏi trình duyệt.','Tạo PDF/DOCX cho quiz, flashcard deck hoặc study plan.',button('Tạo export',{iconName:'download',attrs:'data-create-export'}))}${surface(`<div class="table-wrap"><table><thead><tr><th>Loại</th><th>ID tài nguyên</th><th>Format</th><th>Status</th><th>Ngày tạo</th><th></th></tr></thead><tbody>${rows.map(r=>`<tr><td>${esc(r.resource_type)}</td><td>#${r.resource_id}</td><td>${badge(r.file_format,'neutral')}</td><td>${badge(r.status,statusTone(r.status))}</td><td>${fmtDate(r.created_at,true)}</td><td>${r.file_url?`<button class="btn btn-soft btn-sm" data-download-export="${r.id}" data-download-filename="${esc(`${String(r.resource_type||'export').toLowerCase()}_${r.resource_id}.${String(r.file_format||'bin').toLowerCase()}`)}">Tải file</button>`:esc(r.error_message||'—')}</td></tr>`).join('')}</tbody></table></div>`,'reveal')}`; }

export async function notificationsView(){ const rows=await api.notifications(false); return `${pageHeader('Thông báo','Đừng bỏ lỡ một nhịp học.','Theo dõi hệ thống, lịch review và các sự kiện liên quan tài khoản.')}${rows.length?`<div class="notification-list">${rows.map(n=>`<article class="surface notification-row reveal ${n.is_read?'read':'unread'}"><div class="notif-icon">${icon('bell')}</div><div><div class="row-between"><h3>${esc(n.title)}</h3><small>${fmtDate(n.created_at,true)}</small></div><p>${esc(n.message)}</p>${n.payload?`<code>${esc(JSON.stringify(n.payload))}</code>`:''}</div>${!n.is_read?`<button class="btn btn-soft btn-sm" data-read-notif="${n.id}">Đã đọc</button>`:''}</article>`).join('')}</div>`:emptyState('Không có thông báo','Khi có sự kiện mới, chúng sẽ xuất hiện ở đây.')}`; }

export async function profileView(){ const user=await api.me(); return `${pageHeader('Hồ sơ','Cài đặt danh tính học tập.','Các trường này map trực tiếp PATCH /users/me.')}${surface(`<form class="profile-form" id="profile-form">${avatarMarkup(user,'profile-avatar-large')}<div class="profile-fields"><label>Họ tên<input class="input" name="full_name" value="${esc(user.full_name)}" minlength="2"></label><label>Email<input class="input" value="${esc(user.email)}" disabled></label><label>Avatar URL<input class="input" name="avatar_url" value="${esc(user.avatar_url||'')}" placeholder="https://..."></label><div class="two-col"><label>Timezone<input class="input" name="timezone" value="${esc(user.timezone||'UTC')}"></label><label>Locale<input class="input" name="locale" value="${esc(user.locale||'vi-VN')}"></label></div>${button('Lưu thay đổi',{attrs:'type="submit"'})}</div></form>`,'reveal')}`; }

export function developerView(){ const groups=Object.groupBy?Object.groupBy(ENDPOINT_CATALOG,x=>x[3]):ENDPOINT_CATALOG.reduce((a,x)=>((a[x[3]]??=[]).push(x),a),{}); return `${pageHeader('Developer','Endpoint coverage map.','62 endpoint /api/v1 được API client frontend khai báo và có thể theo dõi từ đây.')}<div class="endpoint-summary reveal"><strong>${ENDPOINT_CATALOG.length}</strong><span>endpoint mapped</span><code>${esc(api.baseUrl)}</code></div>${Object.entries(groups).map(([g,items])=>surface(`<div class="surface-head"><div><span class="eyebrow">Module</span><h3>${esc(g)}</h3></div><span>${items.length} routes</span></div><div class="endpoint-list">${items.map(([m,p,a])=>`<div><span class="method method-${m.toLowerCase()}">${m}</span><code>${esc(p)}</code>${a?badge('JWT','neutral'):badge('Public','success')}</div>`).join('')}</div>`,'reveal endpoint-group')).join('')}`; }

// Detail renderers
export async function openDocument(id){ const [doc,chunks]=await Promise.all([api.getDocument(id),api.documentChunks(id).catch(()=>[])]); modal({title:doc.original_name,wide:true,body:`<div class="detail-meta">${badge(doc.status,statusTone(doc.status))}<span>${fmtBytes(doc.file_size_bytes)}</span><span>${doc.page_count??'—'} trang</span><span>${esc(doc.mime_type||'')}</span></div>${doc.processing_error?`<div class="error-box">${esc(doc.processing_error)}</div>`:''}<h3>Active chunks (${chunks.length})</h3><div class="chunk-list">${chunks.map(c=>`<article><div><b>#${c.chunk_index}</b><span>${c.char_count??c.content.length} chars</span>${c.page_start?`<span>p.${c.page_start}${c.page_end&&c.page_end!==c.page_start?`–${c.page_end}`:''}</span>`:''}</div><p>${esc(c.content)}</p></article>`).join('')||'<p class="muted">Chưa có chunk. Hãy process tài liệu.</p>'}</div>`,actions:`${button('Process',{variant:'soft',attrs:`data-process-doc="${id}"`})}${button('Embed',{attrs:`data-embed-doc="${id}"`})}` ,wide:true}); }

export async function openConversation(id){ const panel=document.getElementById('chat-panel'); if(!panel)return; const msgs=await api.messages(id); panel.innerHTML=`<div class="chat-messages" data-chat-messages>${msgs.map(m=>`<div class="message ${m.role.toLowerCase()}"><div class="message-role">${m.role==='ASSISTANT'?'AI':'Bạn'}</div><div class="bubble">${esc(m.content)}</div><small>${m.model_name?esc(m.model_name)+' · ':''}${fmtDate(m.created_at,true)}</small></div>`).join('')}</div><form class="chat-composer" data-chat-form="${id}"><textarea name="question" class="input" rows="2" required placeholder="Hỏi về tài liệu trong cuộc trò chuyện…"></textarea><input type="number" name="top_k" min="1" max="20" value="5" title="Top K"><button class="btn btn-primary" type="submit">Gửi ${icon('arrow')}</button></form>`; panel.querySelector('[data-chat-messages]')?.scrollTo(0,999999); }

export async function openQuiz(id){ const quiz=await api.getQuiz(id); modal({title:quiz.title,wide:true,body:`<div class="detail-meta">${badge(quiz.status,statusTone(quiz.status))}${badge(quiz.difficulty,'neutral')}<span>${quiz.question_count} câu</span><span>${quiz.duration_minutes?quiz.duration_minutes+' phút':'Không giới hạn'}</span></div><div class="question-preview">${(quiz.questions||[]).map((q,i)=>`<article><span class="q-num">${i+1}</span><div><h4>${esc(q.question_text)}</h4><div class="option-preview">${(q.options||[]).map(o=>`<span>${o.option_key}. ${esc(o.option_text)}</span>`).join('')}</div></div></article>`).join('')}</div>`,actions:`${button('Bắt đầu làm',{attrs:`data-start-quiz="${id}"`})}${quiz.status!=='PUBLISHED'?button('Publish',{variant:'soft',attrs:`data-publish-quiz="${id}"`}):''}`}); }

export async function startQuiz(id){ closeModal(); const data=await api.startAttempt(id); const answers={}; modal({title:`Làm quiz #${data.quiz_id}`,wide:true,body:`<form id="attempt-form" data-attempt-id="${data.attempt_id}"><div class="attempt-head"><span>Bắt đầu: ${fmtDate(data.started_at,true)}</span><span>${data.duration_minutes?data.duration_minutes+' phút':'Không giới hạn'}</span></div><div class="attempt-questions">${data.questions.map((q,i)=>`<fieldset><legend><b>${i+1}.</b> ${esc(q.question_text)}</legend>${q.options.map(o=>`<label class="quiz-option"><input type="radio" name="q_${q.id}" value="${o.id}"><span><b>${o.option_key}</b>${esc(o.option_text)}</span></label>`).join('')}</fieldset>`).join('')}</div><button class="btn btn-primary btn-block" type="submit">Nộp bài</button></form>`}); }

export async function openDeck(id){ const deck=await api.getDeck(id); modal({title:deck.title,wide:true,body:`<div class="detail-meta">${badge(deck.status,statusTone(deck.status))}${badge(deck.generation_mode,'neutral')}<span>${deck.cards?.length||0} thẻ</span></div><div class="flash-grid">${(deck.cards||[]).map(c=>`<div class="flashcard-mini" tabindex="0"><div><span>Mặt trước</span><strong>${esc(c.front_text)}</strong></div><div><span>Mặt sau</span><strong>${esc(c.back_text)}</strong>${c.hint?`<small>Hint: ${esc(c.hint)}</small>`:''}</div></div>`).join('')}</div>`}); }

export async function reviewDue(){ const cards=await api.dueCards(100); if(!cards.length){toast('Không có thẻ đến hạn.','success');return;} let i=0; const started=new Map(); const show=()=>{ const c=cards[i]; const root=modal({title:`Ôn flashcard ${i+1}/${cards.length}`,body:`<div class="review-card" data-review-card><div class="review-front"><span>Câu hỏi</span><h2>${esc(c.front_text)}</h2>${c.hint?`<p>Gợi ý: ${esc(c.hint)}</p>`:''}<button class="btn btn-soft" data-reveal-answer>Hiện đáp án</button></div><div class="review-back"><span>Đáp án</span><h2>${esc(c.back_text)}</h2><div class="rating-grid">${[['0','Again'],['1','Hard'],['2','Good'],['3','Easy']].map(([r,l])=>`<button class="rating r-${r}" data-rate="${r}" data-card="${c.id}">${l}</button>`).join('')}</div></div></div>`}); started.set(c.id,performance.now()); root.querySelector('[data-reveal-answer]')?.addEventListener('click',()=>root.querySelector('[data-review-card]')?.classList.add('flipped')); root.querySelectorAll('[data-rate]').forEach(b=>b.addEventListener('click',async()=>{setBusy(b,true); try{await api.reviewCard(c.id,{rating:Number(b.dataset.rate),response_time_ms:Math.round(performance.now()-started.get(c.id))}); i++; if(i<cards.length)show(); else{closeModal();toast('Hoàn tất phiên ôn tập!','success');}}catch(e){setBusy(b,false);toast(e.message,'danger')}})); }; show(); }

export async function openPlan(id){ const p=await api.getStudyPlan(id); modal({title:p.title,wide:true,body:`<div class="detail-meta">${badge(p.status,statusTone(p.status))}<span>${fmtDate(p.start_date)} → ${fmtDate(p.exam_date)}</span><span>${p.daily_minutes} phút/ngày</span></div><div class="task-list">${p.tasks.map(t=>`<article class="task-row ${t.status==='COMPLETED'?'done':''}"><div><span class="task-date">${fmtDate(t.task_date)}</span><h4>${esc(t.title)}</h4><p>${esc(t.description||'')}</p></div><select class="input task-status" data-task="${t.id}"><option ${t.status==='PENDING'?'selected':''}>PENDING</option><option ${t.status==='IN_PROGRESS'?'selected':''}>IN_PROGRESS</option><option ${t.status==='COMPLETED'?'selected':''}>COMPLETED</option><option ${t.status==='SKIPPED'?'selected':''}>SKIPPED</option></select></article>`).join('')}</div>`}); }

// Form modal factories
export async function createSubjectModal(subject=null){ modal({title:subject?'Chỉnh sửa môn học':'Tạo môn học',body:`<form id="subject-form" data-id="${subject?.id||''}" class="stack-form"><label>Tên<input class="input" name="name" required value="${esc(subject?.name||'')}"></label><label>Mô tả<textarea class="input" name="description" rows="3">${esc(subject?.description||'')}</textarea></label><label>Màu<input class="input color-input" name="color_hex" type="color" value="${esc(subject?.color_hex||'#b8ff5a')}"></label><button class="btn btn-primary" type="submit">Lưu môn học</button></form>`}); }
export async function uploadModal(){ modal({title:'Upload tài liệu',body:`<form id="upload-form" class="stack-form"><label>File<input class="input" name="file" type="file" accept=".pdf,.docx,.txt" required></label><label>Môn học${await subjectSelect()}</label><label class="switch-row"><input type="checkbox" name="process_now" checked><span>Process ngay sau upload</span></label><button class="btn btn-primary" type="submit">Upload</button><div class="upload-progress" data-upload-progress><i></i></div></form>`}); }
export async function conversationModal(){ const docs=await api.listDocuments({limit:100,offset:0}); modal({title:'Cuộc trò chuyện mới',body:`<form id="conversation-form" class="stack-form"><label>Tiêu đề<input class="input" name="title" placeholder="Ôn tập chương 1"></label><label>Môn học${await subjectSelect()}</label><label>Tài liệu liên quan<select class="input" name="document_ids" multiple size="6">${docs.items.map(d=>`<option value="${d.id}">${esc(d.original_name)}</option>`).join('')}</select><small>Giữ Ctrl/Cmd để chọn nhiều file.</small></label><button class="btn btn-primary" type="submit">Tạo cuộc trò chuyện</button></form>`}); }
async function readyDocumentMultiSelect(name='document_ids'){
  const result=await api.listDocuments({limit:100,offset:0});
  const documents=(result?.items||[]).filter(doc=>String(doc.status||'').toUpperCase()==='READY');

  if(!documents.length){
    return `<div class="error-box">Chưa có tài liệu READY. Hãy xử lý tài liệu trước khi tạo học liệu AI.</div>`;
  }

  return `<select class="input" name="${esc(name)}" multiple size="${Math.min(7,Math.max(3,documents.length))}">${documents.map(doc=>`<option value="${doc.id}">${esc(doc.original_name||doc.title||`Tài liệu #${doc.id}`)} · môn #${doc.subject_id??'—'}</option>`).join('')}</select><small class="muted">Giữ Ctrl/Cmd để chọn nhiều tài liệu.</small>`;
}

export async function generateQuizModal(){
  const [subjectHtml,documentHtml]=await Promise.all([
    subjectSelect('subject_id',selectedSubject(),false),
    readyDocumentMultiSelect('document_ids'),
  ]);

  modal({
    title:'Tạo quiz',
    body:`<form id="generate-quiz-form" class="stack-form">
      <label>Kiểu tạo
        <select class="input" name="mode">
          <option value="v5">V5 Deterministic (khuyến nghị)</option>
          <option value="normal">AI V4 / Normal</option>
          <option value="weak">Weak topic</option>
          <option value="adaptive">Adaptive</option>
          <option value="due">Due</option>
        </select>
      </label>
      <label>Tiêu đề<input class="input" name="title" required value="Quiz ôn tập"></label>
      <label>Môn học${subjectHtml}</label>
      <label>Tài liệu nguồn${documentHtml}</label>
      <div class="two-col">
        <label>Số câu<input class="input" type="number" name="question_count" min="1" max="5" value="5"></label>
        <label>Độ khó
          <select class="input" name="difficulty">
            <option>MEDIUM</option>
            <option>EASY</option>
            <option>HARD</option>
          </select>
        </label>
      </div>
      <div class="two-col">
        <label>Nhóm môn
          <select class="input" name="subject_family">
            <option value="general">General</option>
            <option value="history">History</option>
            <option value="economics">Economics</option>
            <option value="biology">Biology</option>
            <option value="physics">Physics</option>
            <option value="geography">Geography</option>
          </select>
        </label>
        <label>Tối đa / section<input class="input" type="number" name="max_per_section" min="1" max="50" value="2"></label>
      </div>
      <div class="two-col">
        <label>Thời lượng (phút)<input class="input" type="number" name="duration_minutes" min="1" value="15"></label>
        <label>Quyền xem
          <select class="input" name="visibility">
            <option value="PRIVATE">PRIVATE</option>
            <option value="UNLISTED">UNLISTED</option>
            <option value="PUBLIC">PUBLIC</option>
          </select>
        </label>
      </div>
      <p class="muted">V5 yêu cầu ít nhất một tài liệu READY và hỗ trợ 1–5 câu. Các mode V4 vẫn được giữ để tương thích.</p>
      <button class="btn btn-primary" type="submit">Tạo quiz</button>
    </form>`
  });
}

export async function generateDeckModal(){
  const [subjectHtml,documentHtml]=await Promise.all([
    subjectSelect(),
    readyDocumentMultiSelect('document_ids'),
  ]);

  modal({
    title:'Tạo flashcard bằng AI',
    body:`<form id="generate-deck-form" class="stack-form">
      <label>Tiêu đề<input class="input" name="title" required value="Flashcards ôn tập"></label>
      <label>Môn học${subjectHtml}</label>
      <label>Tài liệu nguồn (tuỳ chọn)${documentHtml}</label>
      <label>Số thẻ<input class="input" type="number" name="card_count" min="1" max="100" value="20"></label>
      <button class="btn btn-primary" type="submit">Tạo deck</button>
    </form>`
  });
}

export async function generatePlanModal(){ const today=new Date().toISOString().slice(0,10); const exam=new Date(Date.now()+14*864e5).toISOString().slice(0,10); modal({title:'Tạo kế hoạch học',body:`<form id="generate-plan-form" class="stack-form"><label>Tiêu đề<input class="input" name="title" required value="Kế hoạch ôn thi"></label><label>Môn học${await subjectSelect()}</label><div class="two-col"><label>Ngày bắt đầu<input class="input" type="date" name="start_date" value="${today}" required></label><label>Ngày thi<input class="input" type="date" name="exam_date" value="${exam}" required></label></div><label>Phút/ngày<input class="input" type="number" name="daily_minutes" min="1" max="720" value="60"></label><button class="btn btn-primary" type="submit">Tạo kế hoạch</button></form>`}); }
export async function publishCommunityModal(){ const [quizzes,decks]=await Promise.all([api.listQuizzes({limit:100}),api.listDecks(100)]); modal({title:'Chia sẻ tài nguyên',body:`<form id="community-form" class="stack-form"><label>Loại<select class="input" name="resource_type" data-resource-type><option value="QUIZ">Quiz</option><option value="FLASHCARD_DECK">Flashcard deck</option></select></label><label>Quiz<select class="input" name="quiz_id" data-quiz-select>${quizzes.map(q=>`<option value="${q.id}">${esc(q.title)}</option>`).join('')}</select></label><label class="hidden" data-deck-label>Deck<select class="input" name="flashcard_deck_id">${decks.map(d=>`<option value="${d.id}">${esc(d.title)}</option>`).join('')}</select></label><label>Tiêu đề bài chia sẻ<input class="input" name="title"></label><label>Mô tả<textarea class="input" name="description" rows="3"></textarea></label><button class="btn btn-primary" type="submit">Publish</button></form>`}); }
export async function exportModal(){
 const [quizzes,decks,plans]=await Promise.all([
  api.listQuizzes({limit:100}),
  api.listDecks(100),
  api.listStudyPlans()
 ]);
 const resources=[
  ...(quizzes||[]).map(x=>({type:'QUIZ',id:x.id,title:x.title||`Quiz #${x.id}`})),
  ...(decks||[]).map(x=>({type:'FLASHCARD_DECK',id:x.id,title:x.title||`Flashcard #${x.id}`})),
  ...(plans||[]).map(x=>({type:'STUDY_PLAN',id:x.id,title:x.title||`Study plan #${x.id}`}))
 ];
 const options=resources.length
  ? resources.map(r=>`<option value="${esc(`${r.type}:${r.id}`)}">[${r.type==='FLASHCARD_DECK'?'Flashcard':r.type==='STUDY_PLAN'?'Study Plan':'Quiz'}] ${esc(r.title)} (#${r.id})</option>`).join('')
  : '<option value="" disabled selected>Chưa có tài nguyên để xuất</option>';
 modal({title:'Tạo export',body:`<form id="export-form" class="stack-form"><label>Tài nguyên<select class="input" name="resource" required>${options}</select></label><label>Định dạng<select class="input" name="file_format"><option>DOCX</option><option>PDF</option></select></label><button class="btn btn-primary" type="submit" ${resources.length?'':'disabled'}>Xuất file</button></form>`});
}

export async function renderRoute(route){
 const clean=route.replace(/^#?/,'')||'/';
 if(!isAuthed()) return {html:landing(),publicPage:true,route:'/'};
 let content;
 switch(clean){
  case '/': content=await dashboard(); break; case '/subjects': content=await subjectsView(); break; case '/documents': content=await documentsView(); break; case '/chat': content=await chatView(); break; case '/quizzes': content=await quizzesView(); break; case '/flashcards': content=await flashcardsView(); break; case '/study-plans': content=await studyPlansView(); break; case '/analytics': content=await analyticsView(); break; case '/community': content=await communityView(); break; case '/exports': content=await exportsView(); break; case '/notifications': content=await notificationsView(); break; case '/profile': content=await profileView(); break; case '/developer': content=developerView(); break; default: content=emptyState('Không tìm thấy trang',clean,button('Về tổng quan',{attrs:'onclick="location.hash=\'#\/\'"'}));
 }
 return {html:shell(content,clean),route:clean};
}

export function hydrateVisuals(){ revealElements(); initTilt(); }
