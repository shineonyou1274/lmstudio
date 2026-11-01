"""학생용 한 장. 학생 한 명에게 줄 수 있는 HTML 파일을 만든다.

실행:  python grade_lab/student_sheet.py            (모든 학생)
       python grade_lab/student_sheet.py S014       (한 명)
결과:  grade_lab/output/students/<학생번호>.html

이 파일에는 그 학생 본인의 점수와, 성적표에 원래 나오는 전체 통계(과목평균·분포비율·수강자수)만 들어간다.
다른 학생의 점수·이름·번호는 넣지 않는다(테스트로 확인).
'기말 시뮬레이션'의 필요한 점수는 교사 컴퓨터에서 전체 자료로 미리 계산한 결과만 담는다.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import analysis  # noqa: E402
import naesin  # noqa: E402
import simulate  # noqa: E402

OUT_DIR = HERE / "output" / "students"


def compute(data_dir: Path) -> dict:
    """교사 쪽 전체 계산(한 번만). 결과에는 모든 학생이 들어 있으므로 그대로 내보내지 않는다."""
    data = analysis.load(data_dir)
    result = analysis.analyze(data)
    rules = naesin.load_rules(data_dir)
    sems = rules["semesters"]
    exam_ids = {e["exam_id"] for e in data["exams"]}
    sim = None
    for i, sem in enumerate(sems):
        if sem["midterm"] in exam_ids and sem.get("final") not in exam_ids:
            sim = simulate.simulate(data, rules, sem, sems[i - 1] if i > 0 else None)
    return {"result": result, "rules": rules,
            "transcripts": [t for t in (naesin.transcript(data, rules, s) for s in sems) if t], "sim": sim}


def student_payload(full: dict, sid: str) -> dict:
    """한 학생 몫만 골라 담는다. 여기서 빠뜨린 것은 학생 파일에 절대 들어가지 않는다."""
    res, rules = full["result"], full["rules"]
    st = next(s for s in res["students"] if s["student_id"] == sid)
    exam_mean = {e["exam_id"]: (e["fields"].get("raw") or {}).get("mean") for e in res["exams"]}
    series = [{"title": se["title"], "field": se["field"],
               "points": [{"label": p["label"], "value": p["value"], "note": p["note"],
                           "mean": exam_mean.get(p["exam_id"]) if se["field"] == "raw" else None}
                          for p in se["points"]]}
              for se in st["series"]]
    transcripts = []
    for t in full["transcripts"]:
        row = t["rows"].get(sid)
        transcripts.append({
            "semester": t["semester"], "subject": t["subject"], "credits": t["credits"],
            "n": t["n"], "mean": t["mean"], "dist": t["dist"],
            "row": None if row is None else {k: row[k] for k in ("total", "achievement", "grade", "below_min")},
            "excluded": row is None,
        })
    items = None
    item_exams = [eid for eid, v in st["items"].items() if v]
    if item_exams:
        eid = item_exams[-1]
        it = st["items"][eid]
        label = next(e["label"] for e in res["exams"] if e["exam_id"] == eid)
        items = {"label": label, "area": it["area"], "wrong": it["wrong"]}
    sim = None
    S = full["sim"]
    if S:
        me = S["students"].get(sid)
        sem = next(s for s in rules["semesters"] if s["semester"] == S["semester"])
        sim = {"semester": S["semester"], "subject": S["subject"], "n": S["n"], "runs": S["runs"],
               "weights": S["weights"], "performance_max": S["performance_max"],
               "scenarios": S["scenarios"], "cutoffs": sem["achievement"]["cutoffs"],
               "model": {k: S["model"][k] for k in ("a", "b", "sd", "n", "fallback")},
               "me": me}
    assumed = [name for name, key in (("석차를 매기는 점수", "rank_basis"),) if rules[key]["status"] == "가정"]
    assumed += [f"{s['semester']}학기 반영 비율" for s in rules["semesters"] if s["weights_status"] == "가정"]
    return {"student": {k: st[k] for k in ("class", "number", "name")}, "series": series,
            "transcripts": transcripts, "items": items, "sim": sim,
            "rules_note": {"assumed": assumed, "guide": rules.get("guide", {}).get("title", "")},
            "storage_key": f"plan-{st['class']}-{st['number']}"}


def _jsonable(o):
    from decimal import Decimal
    if isinstance(o, Decimal):
        return int(o) if o == o.to_integral_value() else float(o)
    raise TypeError(type(o))


def render(payload: dict) -> str:
    stamp = datetime.now().strftime("%Y-%m-%d")
    return (TEMPLATE.replace("__DATA__", json.dumps(payload, ensure_ascii=False, default=_jsonable))
            .replace("__STAMP__", stamp))


def build(data_dir: Path, only: list[str] | None = None) -> list[Path]:
    full = compute(data_dir)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for st in full["result"]["students"]:
        sid = st["student_id"]
        if only and sid not in only:
            continue
        path = OUT_DIR / f"{sid}.html"
        path.write_text(render(student_payload(full, sid)), encoding="utf-8")
        out.append(path)
    return out


TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>기말 준비 한 장</title>
<style>
:root{
  --bg:#fbf8f6; --surface:#ffffff; --ink:#18233a; --ink-2:#4a5468; --muted:#7a8293;
  --line:#e6e0dc; --grid:#efeae6; --accent:#c94f7c; --s1:#2f5bb0; --s2:#c94f7c;
  --tag:#f7e6ec; --tag-ink:#8a2f52; --warn-bg:#fff4e0; --warn-ink:#7a4a00;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#0f1420; --surface:#141a26; --ink:#eef1f7; --ink-2:#b8c0d0; --muted:#8a93a6;
    --line:#2a3245; --grid:#222a3a; --accent:#e0608f; --s1:#5d8ae0; --s2:#e0608f;
    --tag:#3a1f2c; --tag-ink:#f2b3c9; --warn-bg:#3a2d10; --warn-ink:#f3d79a;
  }
}
:root[data-theme="dark"]{
  --bg:#0f1420; --surface:#141a26; --ink:#eef1f7; --ink-2:#b8c0d0; --muted:#8a93a6;
  --line:#2a3245; --grid:#222a3a; --accent:#e0608f; --s1:#5d8ae0; --s2:#e0608f;
  --tag:#3a1f2c; --tag-ink:#f2b3c9; --warn-bg:#3a2d10; --warn-ink:#f3d79a;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"Pretendard","Apple SD Gothic Neo","Malgun Gothic","Noto Sans KR",sans-serif;line-height:1.6}
.wrap{max-width:860px;margin:0 auto;padding:32px 16px 64px}
header{border-bottom:3px solid var(--ink);padding-bottom:16px;margin-bottom:8px}
.kicker{font-size:12px;letter-spacing:.18em;color:var(--accent);font-weight:700}
h1{font-family:"Noto Serif KR","Batang","AppleMyungjo",serif;font-size:clamp(28px,6vw,40px);line-height:1.2;margin:6px 0 4px;font-weight:800;letter-spacing:-.02em}
h2{font-family:"Noto Serif KR","Batang","AppleMyungjo",serif;font-size:21px;margin:30px 0 4px}
h2 .no{color:var(--accent);margin-right:8px}
.who{color:var(--ink-2);margin:0}
.sub{color:var(--muted);font-size:13px;margin:0 0 12px}
.notice{background:var(--warn-bg);color:var(--warn-ink);border-radius:10px;padding:10px 14px;font-size:13px;margin-top:12px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px}
.grid{display:grid;gap:12px;align-items:start;grid-template-columns:repeat(auto-fit,minmax(min(100%,330px),1fr))}
.kv{display:flex;gap:22px;flex-wrap:wrap;font-variant-numeric:tabular-nums}
.kv div{color:var(--muted);font-size:12px}
.kv b{display:block;font-family:"Noto Serif KR","Batang",serif;font-size:28px;color:var(--ink);line-height:1.2}
.kv b small{font-size:14px;color:var(--muted);font-family:inherit}
table{border-collapse:collapse;width:100%;font-size:14px;font-variant-numeric:tabular-nums}
th,td{padding:8px 6px;text-align:right;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600;font-size:12px}
td.l,th.l{text-align:left}
td:first-child{white-space:nowrap}
tr:last-child td{border-bottom:0}
.official th,.official td{text-align:center;white-space:nowrap}
.scroll{overflow-x:auto}
.plus{color:var(--accent);font-weight:700}
.small{font-size:12px;color:var(--muted)}
.picker{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:6px 0 12px}
select,textarea{font:inherit;padding:8px 10px;border-radius:10px;border:1px solid var(--line);background:var(--surface);color:var(--ink)}
.seg{display:flex;flex-wrap:wrap;gap:6px}
.seg button,.btn{font:inherit;font-size:13px;border:1px solid var(--line);border-radius:99px;background:var(--surface);color:var(--ink-2);padding:6px 12px;cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--bg);border-color:var(--ink);font-weight:700}
.stack{display:flex;height:28px;border-radius:8px;overflow:hidden;margin:8px 0 4px}
.stack div{display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;overflow:hidden}
.goal{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 10px}
.goal label{border:1px solid var(--line);border-radius:10px;padding:6px 10px;font-size:14px;cursor:pointer;background:var(--surface)}
.goal input{margin-right:6px}
.goal label:has(input:checked){border-color:var(--accent);color:var(--accent);font-weight:700}
.answer{font-size:15px;margin:6px 0 12px;padding:10px 12px;border-left:4px solid var(--accent);background:var(--tag);color:var(--tag-ink);border-radius:0 10px 10px 0}
.field{margin:10px 0}
.field label{display:block;font-weight:700;font-size:14px;margin-bottom:4px}
.field textarea{width:100%;min-height:64px;resize:vertical}
.wrongs{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
.wrongs span{font-size:12px;border:1px solid var(--accent);color:var(--accent);border-radius:8px;padding:2px 8px;font-weight:600}
svg{display:block;width:100%;height:auto;overflow:visible}
svg text{fill:var(--muted);font-size:11px;font-family:inherit}
.legend{display:flex;gap:14px;font-size:12px;color:var(--ink-2);margin:4px 0 0;flex-wrap:wrap}
.legend i{display:inline-block;width:18px;height:0;border-top:2px solid;vertical-align:middle;margin-right:6px}
ul.read{padding-left:18px;margin:6px 0;color:var(--ink-2);font-size:14px}
ul.read li{margin:4px 0}
footer{margin-top:28px;color:var(--muted);font-size:12px;border-top:1px solid var(--line);padding-top:10px}
@media print{
  @page{size:A4;margin:12mm}
  :root{--bg:#fff;--surface:#fff}
  body{font-size:11px;line-height:1.45;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  h1{font-size:26px;margin:2px 0}
  header{padding-bottom:8px}
  h2{break-after:avoid}
  .pb{break-before:page;margin-top:0}
  .sub{margin-bottom:6px}
  .grid{gap:8px}
  .kv b{font-size:22px}
  svg{max-height:120px}
  th,td{padding:4px}
  .field{margin:6px 0}
  .stack{height:22px}
  .wrap{max-width:none;padding:0}
  .noprint{display:none!important}
  .card{break-inside:avoid;padding:10px}
  h2{margin-top:10px;font-size:15px}
  textarea{border:1px solid #999;min-height:46px}
  .grid{grid-template-columns:1fr 1fr}
  .grid>.card[style*="1/-1"]{grid-column:1/-1}
  .read li{margin:1px 0}
  .notice{padding:6px 10px}
}
</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="kicker">2학기 기말 준비 · 한 장</div>
  <h1 id="title"></h1>
  <p class="who" id="who"></p>
  <div class="notice">⚠ 연습용 <b>가상 자료</b>입니다. 실제 성적이 아닙니다.<br>
  이 파일에는 <b>내 점수</b>와 성적표에 원래 나오는 전체 통계(과목평균·분포비율)만 들어 있어요. 다른 친구의 점수는 들어 있지 않아요.</div>
</header>

<h2><span class="no">1</span>지금 내 위치</h2>
<p class="sub">지금까지 본 시험 결과예요.</p>
<div class="grid" id="now"></div>

<h2><span class="no">2</span>기말에서 몇 점이 필요할까?</h2>
<p class="sub" id="simSub"></p>
<div class="noprint" id="simControls">
  <div class="picker"><label for="perf"><b>수행평가 예상</b></label><select id="perf"></select></div>
  <div class="picker"><b>친구들의 기말은?</b><div class="seg" id="scen"></div></div>
</div>
<div class="grid" id="sim"></div>

<h2 class="pb"><span class="no">3</span>내 목표와 계획</h2>
<p class="sub">목표는 내가 정해요. 고르면 필요한 점수가 아래에 나와요. 적은 내용은 이 컴퓨터의 브라우저에만 저장돼요.</p>
<div class="card">
  <b>내 목표</b>
  <div class="goal" id="goal"></div>
  <div class="answer" id="answer">목표를 하나 골라 보세요.</div>
  <div class="field"><label for="q1">중간고사에서 점수를 잃은 곳은 어디였나요?</label><textarea id="q1" placeholder="예: 서술형 어법, 시간이 부족했던 마지막 지문"></textarea></div>
  <div class="field"><label for="q2">기말까지 할 일 세 가지</label><textarea id="q2" placeholder="1.&#10;2.&#10;3."></textarea></div>
  <div class="field"><label for="q3">선생님께 물어보고 싶은 것</label><textarea id="q3"></textarea></div>
  <div class="noprint" style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn" id="print" type="button">🖨 인쇄하기</button><button class="btn" id="clear" type="button">적은 내용 지우기</button></div>
</div>

<div id="itemsBox"></div>

<h2><span class="no" id="readNo">5</span>이 종이를 읽는 법</h2>
<ul class="read">
  <li><b>성취도(A~E)</b>는 내 점수만으로 정해져요. 그래서 필요한 점수가 정확히 나와요.</li>
  <li><b>석차등급(1~5)</b>은 친구들 점수에 따라 달라져요. 그래서 “친구들이 1학기와 비슷하게 시험을 본다면”이라고 가정하고, 가능한 경우를 여러 번 만들어 계산했어요. <b>예측이 아니에요.</b></li>
  <li><b>반반</b>은 만들어 본 경우의 절반에서 목표를 이룬 점수, <b>안정권</b>은 10번 중 8번 이룬 점수예요.</li>
  <li>수행평가는 기말 뒤에 하니까 예상 점수를 골라서 볼 수 있어요.</li>
  <li>얼마나 오래 공부해야 하는지는 알 수 없어요. 대신 <b>중간보다 몇 점 더</b> 필요한지 보여 줘요.</li>
  <li id="ruleNote"></li>
</ul>
<footer>만든 날: __STAMP__ · 인터넷 연결 없이 열리고, 적은 내용은 어디로도 보내지 않아요.</footer>
</div>

<script>
const P = __DATA__;
const $ = s => document.querySelector(s);
const GCOL = ['#1f3f80','#2f5bb0','#6b8fd0','#a3bae6','#d3def2'], GINK = ['#fff','#fff','#fff','#18233a','#18233a'];
const st = P.student, S = P.sim, me = S && S.me;
$('#title').textContent = `${st.name}의 기말 준비`;
$('#who').textContent = `${st['class']}반 ${st.number}번`;

// 1 지금 내 위치
(function(){
  const box = $('#now');
  const nae = P.series.find(s => s.field === 'raw' && s.title.startsWith('내신'));
  const last = arr => [...arr].reverse().find(p => p.value != null);
  let kv = '';
  if (nae) { const p = last(nae.points); if (p) kv += `<div>${p.label}<b>${p.value}<small>점</small></b>전체 평균 ${p.mean != null ? p.mean.toFixed(1) : '—'}점</div>`; }
  P.transcripts.forEach(t => { if (t.row) kv += `<div>${t.semester}학기 성취도·등급<b>${t.row.achievement} · ${t.row.grade}<small>등급</small></b>원점수 ${t.row.total}점</div>`; });
  const mock = P.series.find(s => s.field === 'grade'), mp = mock && last(mock.points);
  if (mp) kv += `<div>${mp.label}<b>${mp.value}<small>등급</small></b>영어 절대평가</div>`;
  let html = `<div class="card"><div class="kv">${kv}</div></div>`;
  if (nae) html += `<div class="card"><b>내신 시험 점수</b><p class="small" style="margin:0">실선 = 나 · 점선 = 전체 평균</p>${chart(nae.points)}</div>`;
  P.transcripts.forEach(t => {
    if (!t.row) { html += `<div class="card"><b>${t.semester}학기 성적표</b><p class="small">결시가 있어 학교 규정으로 처리 중이에요. 선생님께 확인하세요.</p></div>`; return; }
    html += `<div class="card" style="grid-column:1/-1"><b>${t.semester}학기 성적표 · ${t.subject}</b>
      <div class="scroll"><table class="official"><tr><th>학점</th><th>원점수/과목평균</th><th>성취도(수강자수)</th><th>A</th><th>B</th><th>C</th><th>D</th><th>E</th><th>석차등급</th></tr>
      <tr><td>${t.credits}</td><td>${t.row.total}/${t.mean.toFixed(1)}</td><td><b>${t.row.achievement}</b>(${t.n})</td>
      ${'ABCDE'.split('').map(L => `<td>${t.dist[L].toFixed(1)}</td>`).join('')}<td><b>${t.row.grade}</b></td></tr></table></div></div>`;
  });
  box.innerHTML = html;
})();
function chart(pts){
  const W = 300, H = 150, L = 28, R = 14, T = 12, B = 24, n = pts.length;
  const X = i => n === 1 ? W / 2 : L + (W - L - R) * i / (n - 1), Y = v => T + (H - T - B) * (100 - v) / 100;
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="내신 점수 변화">`;
  [0, 50, 100].forEach(v => s += `<line x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--grid)"/><text x="${L-6}" y="${Y(v)+4}" text-anchor="end">${v}</text>`);
  pts.forEach((p, i) => s += `<text x="${X(i)}" y="${H-6}" text-anchor="middle">${p.label.replace('고사', '')}</text>`);
  const line = (vals, col, dash) => { let d = '', pen = false;
    vals.forEach((v, i) => { if (v == null) { pen = false; return; } d += (pen ? 'L' : 'M') + X(i) + ',' + Y(v); pen = true; });
    return d ? `<path d="${d}" fill="none" stroke="${col}" stroke-width="2" ${dash ? 'stroke-dasharray="5 4"' : ''}/>` : ''; };
  s += line(pts.map(p => p.mean), 'var(--s2)', true) + line(pts.map(p => p.value), 'var(--s1)', false);
  pts.forEach((p, i) => { if (p.value != null) s += `<circle cx="${X(i)}" cy="${Y(p.value)}" r="4.5" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"/><text x="${X(i)}" y="${Y(p.value)-9}" text-anchor="middle" style="fill:var(--ink);font-weight:700">${p.value}</text>`;
    else s += `<text x="${X(i)}" y="${T+10}" text-anchor="middle" style="fill:var(--accent);font-weight:700">${p.note}</text>`; });
  return s + '</svg>';
}

// 2 시뮬레이션
let scen = S ? S.scenarios[0].key : null;
function need(f, mid){
  if (f == null) return { main: '만점이어도 어려워요', diff: '' };
  if (f <= 0) return { main: '이미 충분해요', diff: '' };
  const d = f - mid;
  return { main: `${f}점 이상`, diff: d > 0 ? `<span class="plus">중간보다 +${d}점</span>` : `중간보다 ${-d}점 낮아도 돼요` };
}
function goals(){
  const pk = $('#perf').value, mid = me.mid, out = [];
  'ABCD'.split('').forEach(L => out.push({ key: 'a' + L, label: `성취도 ${L}`, f: me.achievement[pk][L], kind: 'a' }));
  [1,2,3,4].forEach(g => { const v = me.grade[scen][pk][g]; out.push({ key: 'g' + g, label: `${g}등급 이상`, f: v.p80, f50: v.p50, kind: 'g' }); });
  return out;
}
function renderSim(){
  if (!me) return;
  const pk = $('#perf').value, mid = me.mid, sc = S.scenarios.find(x => x.key === scen);
  const pr = me.predict[scen][pk], best = pr.indexOf(Math.max(...pr)), ach = me.achievement[pk];
  const achAtMid = 'ABCD'.split('').find(L => ach[L] != null && ach[L] <= mid) || 'E';
  const stack = pr.map((p, i) => p > 0 ? `<div style="width:${p*100}%;background:${GCOL[i]};color:${GINK[i]}">${p >= .1 ? (i+1) + '등급 ' + Math.round(p*100) + '%' : ''}</div>` : '').join('');
  const aRows = 'ABCD'.split('').map(L => { const t = need(ach[L], mid);
    return `<tr><td class="l"><b>${L}</b> <span class="small">(${S.cutoffs[L]}점~)</span></td><td>${t.main}</td><td class="l small">${t.diff}</td></tr>`; }).join('');
  const gRows = [1,2,3,4].map(g => { const v = me.grade[scen][pk][g], a = need(v.p50, mid), b = need(v.p80, mid);
    return `<tr><td class="l"><b>${g}등급</b> 이상</td><td>${a.main}</td><td>${b.main}</td></tr>`; }).join('');
  $('#sim').innerHTML = `
    <div class="card" style="grid-column:1/-1"><b>기말도 중간만큼(${mid}점) 본다면</b>
      <p class="small" style="margin:0">${sc.label} · 수행평가 ${me.perf_levels.find(l => l.key === pk).label}</p>
      <div class="kv" style="margin-top:6px"><div>성취도<b>${achAtMid}</b></div><div>석차등급 (가장 많이 나온 경우)<b>${best+1}<small>등급 · ${Math.round(pr[best]*100)}%</small></b></div></div>
      <div class="stack" role="img" aria-label="석차등급이 나온 비율">${stack}</div>
      <p class="small" style="margin:0">${S.runs}번 만들어 본 경우 중 각 등급이 나온 비율</p></div>
    <div class="card"><b>성취도 목표</b><p class="small" style="margin:0">정확히 계산돼요</p>
      <table><tr><th class="l">목표</th><th>필요한 기말</th><th class="l"></th></tr>${aRows}</table></div>
    <div class="card"><b>석차등급 목표</b><p class="small" style="margin:0">반반 = 절반의 경우 · 안정권 = 10번 중 8번</p>
      <table><tr><th class="l">목표</th><th>반반</th><th>안정권</th></tr>${gRows}</table></div>`;
  renderGoal();
}
function renderGoal(){
  if (!me) return;
  const gs = goals(), box = $('#goal'), saved = load().goal;
  box.innerHTML = gs.map(g => `<label><input type="radio" name="goal" value="${g.key}" ${saved === g.key ? 'checked' : ''}>${g.label}</label>`).join('');
  const g = gs.find(x => x.key === saved);
  if (!g) { $('#answer').textContent = '목표를 하나 골라 보세요.'; return; }
  const t = need(g.f, me.mid);
  $('#answer').innerHTML = g.kind === 'a'
    ? `<b>${g.label}</b>: 기말 <b>${t.main}</b> ${t.diff ? '· ' + t.diff : ''}`
    : `<b>${g.label}</b>: 안정권은 기말 <b>${t.main}</b> ${t.diff ? '· ' + t.diff : ''}${g.f50 != null && g.f50 !== g.f ? ` <span class="small">(반반은 ${g.f50}점)</span>` : ''}`;
}
(function(){
  if (!me) {
    $('#simControls').style.display = 'none';
    $('#simSub').textContent = S ? '중간고사 결시가 있어 학교 규정으로 처리 중이에요. 선생님과 함께 확인하세요.' : '아직 계산할 시험이 없어요.';
    $('#goal').innerHTML = ''; $('#answer').textContent = '선생님과 함께 목표를 정해 보세요.'; return;
  }
  const w = S.weights;
  $('#simSub').innerHTML = `${S.semester}학기 ${S.subject} 성적 = 중간 ${w.midterm}% + 기말 ${w.final}% + 수행평가 ${w.performance}%`;
  $('#perf').innerHTML = me.perf_levels.map(l => `<option value="${l.key}">${l.label}</option>`).join('');
  $('#scen').innerHTML = S.scenarios.map(x => `<button type="button" data-k="${x.key}" aria-pressed="${x.key === scen}">${x.label}</button>`).join('');
  $('#scen').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; scen = b.dataset.k;
    $('#scen').querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', x === b)); renderSim(); });
  $('#perf').addEventListener('change', renderSim);
  $('#goal').addEventListener('change', e => { save({ goal: e.target.value }); renderGoal(); });
  renderSim();
})();

// 3 저장 (이 브라우저에만)
function load(){ try { return JSON.parse(localStorage.getItem(P.storage_key) || '{}'); } catch (e) { return {}; } }
function save(part){ try { localStorage.setItem(P.storage_key, JSON.stringify(Object.assign(load(), part))); } catch (e) {} }
['q1','q2','q3'].forEach(id => { const el = $('#' + id); el.value = load()[id] || ''; el.addEventListener('input', () => save({ [id]: el.value })); });
$('#print').addEventListener('click', () => print());
$('#clear').addEventListener('click', () => { if (!confirm('적은 내용을 지울까요?')) return; try { localStorage.removeItem(P.storage_key); } catch (e) {}
  ['q1','q2','q3'].forEach(id => $('#' + id).value = ''); renderGoal(); });

// 4 다시 볼 문항
(function(){
  const it = P.items; if (!it) { $('#readNo').textContent = '4'; return; }
  const easy = it.wrong.filter(w => 'AB'.includes(w.band));
  $('#itemsBox').innerHTML = `<h2><span class="no">4</span>${it.label}에서 다시 볼 문항</h2>
    <p class="sub">전국에서 정답률이 높았던(A·B) 문항 중에 내가 틀린 문항이에요. 기말 준비와 함께 다시 풀어 보세요.</p>
    <div class="card"><div class="kv"><div>듣기<b>${it.area['듣기'].got}<small> / ${it.area['듣기'].max}</small></b></div><div>읽기<b>${it.area['읽기'].got}<small> / ${it.area['읽기'].max}</small></b></div></div>
    <div class="wrongs">${easy.map(w => `<span>${w.item_no}번 ${w.type}</span>`).join('') || '<span>없어요 👍</span>'}</div>
    <p class="small" style="margin:8px 0 0">틀린 문항 전체 ${it.wrong.length}개 중 ${easy.length}개</p></div>`;
})();
$('#ruleNote').innerHTML = `계산 규칙은 ${P.rules_note.guide || '교육청 지침'}을 따랐어요.` +
  (P.rules_note.assumed.length ? ` 아직 우리 학교 규정으로 확인하지 못한 것: ${P.rules_note.assumed.join(', ')}.` : '');
</script>
</body>
</html>
"""


if __name__ == "__main__":
    args = sys.argv[1:]
    src = HERE / "data" / "sample"
    if args and Path(args[0]).is_dir():
        src, args = Path(args[0]), args[1:]
    if not (src / "scores.csv").exists():
        import generate_sample
        generate_sample.main()
    paths = build(src, args or None)
    print(f"학생용 한 장 {len(paths)}개를 만들었습니다: {OUT_DIR}")
