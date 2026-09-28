from __future__ import annotations

from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / "src" / "views.js"

MARKER = "SSA-FE-LR-V1"


def _backup(path: Path) -> None:
    backup = path.with_name(
        path.stem + "_before_frontend_learning_reliability_v1" + path.suffix
    )
    if not backup.exists():
        shutil.copy2(path, backup)
        print(f"[OK] backup: {backup.name}")


def _replace_function(
    text: str,
    *,
    start_name: str,
    next_name: str,
    replacement: str,
) -> str:
    pattern = re.compile(
        rf"export async function {re.escape(start_name)}\(\)\{{.*?"
        rf"(?=export async function {re.escape(next_name)}\(\))",
        flags=re.S,
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(
            f"{start_name}: expected exactly one function block, "
            f"found {len(matches)}"
        )
    return pattern.sub(replacement.rstrip() + "\n\n", text, count=1)


def main() -> None:
    if not VIEWS.exists():
        raise SystemExit(f"Missing: {VIEWS}")

    text = VIEWS.read_text(encoding="utf-8")

    if MARKER in text:
        print("[SKIP] frontend learning reliability patch already applied")
        return

    _backup(VIEWS)

    flashcards = r'''export async function flashcardsView(){
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
}'''

    analytics = r'''export async function analyticsView(){
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
}'''

    text = _replace_function(
        text,
        start_name="flashcardsView",
        next_name="studyPlansView",
        replacement=flashcards,
    )

    text = _replace_function(
        text,
        start_name="analyticsView",
        next_name="communityView",
        replacement=analytics,
    )

    # Marker as a harmless comment close to the file start.
    text = "// SSA-FE-LR-V1\n" + text

    VIEWS.write_text(text, encoding="utf-8")

    print()
    print("=" * 76)
    print("FRONTEND LEARNING RELIABILITY V1 APPLIED")
    print("=" * 76)
    print("[OK] mastery_score is rendered as backend 0..100 percent")
    print("[OK] weak topic score no longer multiplies by 100")
    print("[OK] Analytics auxiliary API failure no longer crashes whole page")
    print("[OK] Flashcard due API failure no longer hides deck library")
    print("=" * 76)


if __name__ == "__main__":
    main()
