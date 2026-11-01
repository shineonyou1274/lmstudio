"""분석 결과를 브라우저로 여는 HTML 한 장으로 만든다.

실행:  python grade_lab/report.py            (가상 자료 사용)
       python grade_lab/report.py <자료폴더>  (같은 형식의 다른 CSV 폴더)
결과:  grade_lab/output/report.html

인터넷 연결 없이 열린다. 외부 글꼴·스크립트를 불러오지 않는다.
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
from decimal import Decimal  # noqa: E402

OUT = HERE / "output" / "report.html"


def build(data_dir: Path) -> Path:
    data = analysis.load(data_dir)
    result = analysis.analyze(data)
    rules = naesin.load_rules(data_dir)
    sems = rules["semesters"]
    result["naesin"] = {
        "rules": rules,
        "transcripts": [t for t in (naesin.transcript(data, rules, s) for s in sems) if t],
        # 기말이 아직 없는 가장 최근 학기를 시뮬레이션한다.
        "sim": None,
    }
    exam_ids = {e["exam_id"] for e in data["exams"]}
    for i, sem in enumerate(sems):
        if sem["midterm"] in exam_ids and sem.get("final") not in exam_ids:
            result["naesin"]["sim"] = simulate.simulate(data, rules, sem, sems[i - 1] if i > 0 else None)
    payload = json.dumps(result, ensure_ascii=False, default=_jsonable)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = TEMPLATE.replace("__DATA__", payload).replace("__STAMP__", stamp).replace(
        "__SOURCE__", str(Path(data_dir).name)
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    return OUT


def _jsonable(o):
    if isinstance(o, Decimal):
        return int(o) if o == o.to_integral_value() else float(o)
    raise TypeError(type(o))


TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>성적 분석실</title>
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
.wrap{max-width:1080px;margin:0 auto;padding:40px 16px 80px}
header{border-bottom:3px solid var(--ink);padding-bottom:20px;margin-bottom:28px}
.kicker{font-size:13px;letter-spacing:.18em;color:var(--accent);font-weight:700}
h1{font-family:"Noto Serif KR","Batang","AppleMyungjo",serif;font-size:clamp(32px,6vw,52px);
  line-height:1.15;margin:6px 0 10px;font-weight:800;letter-spacing:-.02em}
h2{font-family:"Noto Serif KR","Batang","AppleMyungjo",serif;font-size:26px;margin:48px 0 6px;letter-spacing:-.01em}
h2 .no{color:var(--accent);margin-right:10px}
.lede{color:var(--ink-2);margin:0}
.sub{color:var(--muted);font-size:14px;margin:0 0 16px}
.notice{background:var(--warn-bg);color:var(--warn-ink);border-radius:10px;padding:12px 16px;font-size:14px;margin-top:16px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:14px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:14px;font-variant-numeric:tabular-nums}
th,td{padding:10px 12px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}
th{color:var(--muted);font-weight:600;font-size:12px;background:var(--surface)}
td.l,th.l{text-align:left}
tr:last-child td{border-bottom:0}
.tag{display:inline-block;font-size:12px;padding:2px 8px;border-radius:99px;background:var(--tag);color:var(--tag-ink);font-weight:600}
.na{color:var(--muted)}
.grid{display:grid;gap:16px;align-items:start;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.chart-title{font-weight:700;margin:0 0 2px}
.chart-sub{color:var(--muted);font-size:12px;margin:0 0 8px}
svg{display:block;width:100%;height:auto;overflow:visible}
svg text{fill:var(--muted);font-size:11px;font-family:inherit}
.legend{display:flex;gap:14px;font-size:12px;color:var(--ink-2);margin:4px 0 0;flex-wrap:wrap}
.legend i{display:inline-block;width:18px;height:0;border-top:2px solid;vertical-align:middle;margin-right:6px}
.picker{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:8px 0 16px}
select{font:inherit;padding:8px 12px;border-radius:10px;border:1px solid var(--line);background:var(--surface);color:var(--ink)}
.changes{list-style:none;padding:0;margin:10px 0 0;font-size:13px;color:var(--ink-2)}
.changes li{padding:3px 0}
.tip{position:fixed;pointer-events:none;background:var(--ink);color:var(--bg);font-size:12px;padding:6px 10px;
  border-radius:8px;opacity:0;transition:opacity .1s;z-index:9;white-space:nowrap}
.method li{margin:6px 0;color:var(--ink-2)}
.band{display:inline-block;min-width:22px;text-align:center;font-size:11px;font-weight:700;padding:1px 6px;border-radius:6px;
  border:1px solid var(--line);color:var(--ink-2)}
.low{color:var(--accent);font-weight:700}
.bar{display:inline-block;height:8px;border-radius:4px;background:var(--s1);vertical-align:middle;margin-right:8px}
.wrongs{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.wrongs span{font-size:12px;border:1px solid var(--line);border-radius:8px;padding:2px 8px;color:var(--ink-2)}
.wrongs span.easy{border-color:var(--accent);color:var(--accent);font-weight:600}
.kv{display:flex;gap:24px;flex-wrap:wrap;font-variant-numeric:tabular-nums}
.kv b{font-size:22px;color:var(--ink)}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden;flex-wrap:wrap}
.seg button{font:inherit;font-size:13px;border:0;background:var(--surface);color:var(--ink-2);padding:8px 12px;cursor:pointer}
.seg button+button{border-left:1px solid var(--line)}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--bg);font-weight:700}
.status{display:inline-block;font-size:11px;padding:1px 7px;border-radius:99px;font-weight:700}
.status.assume{background:var(--warn-bg);color:var(--warn-ink)}
.status.ok{background:var(--tag);color:var(--tag-ink)}
.big{font-family:"Noto Serif KR","Batang","AppleMyungjo",serif;font-size:30px;font-weight:800;color:var(--ink);line-height:1.2}
.stack{display:flex;height:30px;border-radius:8px;overflow:hidden;margin:10px 0 6px}
.stack div{display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#fff;min-width:0;overflow:hidden}
.need th,.need td{white-space:normal;padding:8px 6px}
.need td:first-child{white-space:nowrap}
.plus{color:var(--accent);font-weight:700}
.small{font-size:12px;color:var(--muted)}
.official th,.official td{text-align:center}
footer{margin-top:48px;color:var(--muted);font-size:12px;border-top:1px solid var(--line);padding-top:12px}
</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="kicker">SCHOOL AI LAB · 성적 분석실</div>
  <h1>고1 영어 성적 분석<br>가상 자료 시험판</h1>
  <p class="lede">시험별 요약, 학기 성적, 학생별 변화, 기말 시뮬레이션을 보여 줍니다. 계산은 코드가 하며, AI 해석은 아직 붙이지 않았습니다.</p>
  <div class="notice">⚠ 이 화면의 학생과 점수는 모두 <b>가상 자료</b>입니다. 실제 학생 정보가 아닙니다.<br>
  🔒 <b>교사용 화면</b>입니다. 파일 안에 모든 학생의 점수가 들어 있으니 학생에게 파일을 그대로 주지 마세요.</div>
</header>

<h2><span class="no">01</span>시험별 요약</h2>
<p class="sub">결시는 통계에서 빼고 따로 셉니다. 응시했지만 필요한 칸이 빈 경우는 ‘누락’으로 따로 셉니다. 빈칸(—)은 그 시험에서 제공되지 않는 항목입니다.</p>
<div class="tablewrap"><table id="summary"></table></div>

<h2><span class="no">02</span>모의고사 등급 분포</h2>
<p class="sub">영어는 절대평가입니다. 막대 위에 마우스를 올리면 인원이 보입니다.</p>
<div class="grid" id="dists"></div>

<h2><span class="no">03</span>전국연합 문항 분석</h2>
<p class="sub">문항마다 전국 정답률 구간(A 80~100% … E 0~20%)과 우리 학생 정답률을 나란히 봅니다. 결시자는 분모에서 뺍니다.</p>
<div class="picker"><label for="itemExam"><b>시험 선택</b></label><select id="itemExam"></select></div>
<div class="card" id="itemChart"></div>
<div class="grid" style="margin-top:16px">
  <div class="card"><p class="chart-title">유형별 우리 학생 정답률</p><p class="chart-sub">유형에 속한 문항을 묶어 계산 (맞힌 수 ÷ 응답 수)</p><table id="typeTable"></table></div>
  <div class="card"><p class="chart-title">자료 점검</p><p class="chart-sub">원점수가 맞힌 문항 배점의 합과 같은지 확인합니다</p><div id="checkBox"></div></div>
</div>
<details style="margin-top:16px"><summary class="chart-sub" style="cursor:pointer">45문항 전체 표로 보기</summary>
<div class="tablewrap" style="margin-top:8px"><table id="itemTable"></table></div></details>

<h2><span class="no">04</span>학기 성적 (성적표 형식)</h2>
<p class="sub">중간·기말·수행평가가 모두 끝난 학기만 계산합니다. 반영 비율과 성취도 기준은 아래 07의 규칙을 따릅니다.</p>
<div id="transcripts"></div>

<h2><span class="no">05</span>학생별 보기</h2>
<p class="sub">같은 항목끼리만 잇습니다. 내신과 모의고사는 섞지 않습니다.</p>
<div class="picker"><label for="who"><b>학생 선택</b></label><select id="who"></select></div>
<div class="grid" id="student"></div>

<h2><span class="no">06</span>기말 시뮬레이션</h2>
<p class="sub" id="simSub"></p>
<div class="picker"><label for="who2"><b>학생</b></label><select id="who2"></select>
  <label for="perf"><b>수행평가 가정</b></label><select id="perf"></select></div>
<div class="picker"><b>다른 학생들의 기말</b><div class="seg" id="scen"></div></div>
<div class="grid" id="sim"></div>
<div class="notice" id="simNote"></div>

<h2><span class="no">07</span>적용한 규칙과 계산 방법</h2>
<p class="sub"><span class="status assume">가정</span> 표시는 학교 학업성적관리규정으로 아직 확인하지 않은 규칙입니다. <code>rules.json</code>에서 바꿀 수 있습니다.</p>
<div class="tablewrap"><table id="rulesTable"></table></div>
<ul class="method">
  <li><b>문항 비교</b>: 우리 학생 정답률이 들어가는 구간을 전국 구간과 비교해 ‘높음 / 범위 안 / 낮음’으로 표시합니다. 구간 경계값(예: 80%)은 위쪽 구간(A)에 넣었습니다.</li>
  <li><b>평균·중앙값·표준편차</b>: 결시자와 해당 칸이 빈 학생은 빼고 계산합니다. 표준편차는 모집단 표준편차(인원수 n으로 나눔)입니다.</li>
  <li><b>모의고사 등급</b>은 순서를 나타내는 값이라 평균 대신 <b>분포와 중앙값</b>으로 보여 줍니다. 등급은 숫자가 작아지면 ‘상승’입니다.</li>
  <li><b>학기 성적</b>: 지필 결시·수행 결시 학생은 학교 규정의 인정점이 있어야 계산할 수 있어 빼고 계산했습니다. 그래서 다른 학생의 석차등급도 실제와 조금 다를 수 있습니다.</li>
  <li><b>석차등급 시뮬레이션은 예측이 아닙니다.</b> “다른 학생들이 1학기와 비슷한 흐름으로 기말을 본다면”이라는 가정 아래, 가능한 경우를 여러 번 만들어 본 결과입니다. 시험 범위·난이도·학생 노력처럼 자료에 없는 요인은 반영하지 못합니다.</li>
  <li><b>필요한 공부량</b>은 자료로 알 수 없어 ‘필요한 점수 차이’로만 보여 줍니다.</li>
  <li><b>점수 변화의 원인</b>은 이 자료로 알 수 없습니다.</li>
  <li>모든 계산은 손으로 계산한 작은 자료, 표준 통계 모듈, 하나씩 다 따져 보는 느린 계산과 대조해 검증했습니다(<code>grade_lab/tests</code>).</li>
</ul>

<footer>자료: __SOURCE__ · 만든 시각: __STAMP__ · 이 파일은 인터넷 연결 없이 열리며 외부로 자료를 보내지 않습니다.</footer>
</div>
<div class="tip" id="tip"></div>

<script>
const R = __DATA__;
const $ = s => document.querySelector(s);
const fmt = (v, d=1) => v == null ? '<span class="na">—</span>' : (Number.isInteger(v) ? v : v.toFixed(d));
const tip = $('#tip');
function showTip(e, html){ tip.innerHTML = html; tip.style.opacity = 1;
  tip.style.left = Math.min(e.clientX + 12, innerWidth - tip.offsetWidth - 8) + 'px';
  tip.style.top = (e.clientY - 34) + 'px'; }
function hideTip(){ tip.style.opacity = 0; }

// 01 요약표
(function(){
  const h = `<tr><th class="l">종류</th><th class="l">시험</th><th>날짜</th><th>응시</th><th>결시</th><th>누락</th>
    <th>원점수 평균</th><th>중앙값</th><th>표준편차</th><th>최저~최고</th><th>등급 중앙값</th></tr>`;
  const rows = R.exams.map(e => {
    const r = e.fields.raw, g = e.fields.grade;
    return `<tr><td class="l"><span class="tag">${e.kind}</span></td><td class="l">${e.label}</td><td>${e.date}</td>
      <td>${e.n_taken}</td><td>${e.n_absent}</td><td>${e.n_missing}</td>
      <td>${fmt(r&&r.mean)}</td><td>${fmt(r&&r.median)}</td><td>${fmt(r&&r.sd)}</td>
      <td>${r ? r.min + '~' + r.max : fmt(null)}</td><td>${fmt(g&&g.median)}</td></tr>`;
  }).join('');
  $('#summary').innerHTML = h + rows;
})();

// 02 등급 분포 (시험마다 작은 막대그래프)
(function(){
  const box = $('#dists');
  R.exams.filter(e => e.grade_dist).forEach(e => {
    const counts = Object.values(e.grade_dist), step = Math.max(1, Math.ceil(Math.max(1, ...counts) / 4)), max = step * Math.ceil(Math.max(1, ...counts) / step);
    const W = 320, H = 170, L = 26, B = 22, T = 10, bw = (W - L) / 9;
    let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${e.label} 등급 분포">`;
    for (let k = 0; k <= max; k += step) {
      const y = H - B - (H - B - T) * k / max;
      s += `<line x1="${L}" x2="${W}" y1="${y}" y2="${y}" stroke="var(--grid)"/><text x="${L-6}" y="${y+4}" text-anchor="end">${k}</text>`;
    }
    counts.forEach((c, i) => {
      const x = L + i * bw, bh = (H - B - T) * c / max, y = H - B - bh;
      if (c > 0) s += `<path d="M${x+2},${H-B} V${y+4} q0,-4 4,-4 H${x+bw-6} q4,0 4,4 V${H-B} Z" fill="var(--s1)"/>`;
      s += `<rect x="${x}" y="${T}" width="${bw}" height="${H-B-T}" fill="transparent" data-tip="${i+1}등급: ${c}명"/>`;
      s += `<text x="${x + bw/2}" y="${H-6}" text-anchor="middle">${i+1}</text>`;
    });
    s += `</svg>`;
    const d = document.createElement('div'); d.className = 'card';
    d.innerHTML = `<p class="chart-title">${e.label}</p><p class="chart-sub">${e.kind} · 응시 ${e.n_taken}명 · 가로축 등급</p>` + s;
    box.appendChild(d);
  });
})();

// 03 학생별 변화
function lineChart(series, classMean){
  const pts = series.points, n = pts.length, isGrade = series.field === 'grade';
  const W = 320, H = 190, L = 30, Rr = 16, T = 14, B = 26;
  const lo = isGrade ? 1 : 0, hi = isGrade ? 9 : 100;
  const X = i => n === 1 ? (L + W - Rr) / 2 : L + (W - L - Rr) * i / (n - 1);
  const Y = v => isGrade ? T + (H - T - B) * (v - lo) / (hi - lo) : T + (H - T - B) * (hi - v) / (hi - lo);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${series.title}">`;
  (isGrade ? [1,3,5,7,9] : [0,25,50,75,100]).forEach(v => {
    s += `<line x1="${L}" x2="${W-Rr}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--grid)"/><text x="${L-6}" y="${Y(v)+4}" text-anchor="end">${v}</text>`;
  });
  pts.forEach((p, i) => { s += `<text x="${X(i)}" y="${H-6}" text-anchor="middle">${p.label.replace(/^\d학기 /, '').replace(/고사$/, '').replace(/ (전국연합|모의평가)$/, '')}</text>`; });
  const path = (vals, color, dash) => {
    let d = '', pen = false;
    vals.forEach((v, i) => { if (v == null) { pen = false; return; } d += (pen ? 'L' : 'M') + X(i) + ',' + Y(v); pen = true; });
    return d ? `<path d="${d}" fill="none" stroke="${color}" stroke-width="2" ${dash ? 'stroke-dasharray="5 4"' : ''}/>` : '';
  };
  if (classMean) s += path(classMean, 'var(--s2)', true);
  s += path(pts.map(p => p.value), 'var(--s1)', false);
  if (classMean) classMean.forEach((v, i) => { if (v != null)
    s += `<circle cx="${X(i)}" cy="${Y(v)}" r="4" fill="var(--s2)" stroke="var(--surface)" stroke-width="2" data-tip="${pts[i].label} 전체 평균 ${v.toFixed(1)}점"/>`; });
  pts.forEach((p, i) => {
    if (p.value == null) {
      s += `<text x="${X(i)}" y="${T + 12}" text-anchor="middle" style="fill:var(--accent);font-weight:700">${p.note}</text>`;
      return;
    }
    const lbl = isGrade ? p.value + '등급' : p.value + '점';
    s += `<circle cx="${X(i)}" cy="${Y(p.value)}" r="5" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"/>`;
    s += `<circle cx="${X(i)}" cy="${Y(p.value)}" r="14" fill="transparent" data-tip="${p.label}: ${lbl}"/>`;
  });
  return s + '</svg>';
}
function renderStudent(id){
  const st = R.students.find(s => s.student_id === id), box = $('#student');
  const meanOf = (exId) => { const e = R.exams.find(x => x.exam_id === exId); return e && e.fields.raw ? e.fields.raw.mean : null; };
  box.innerHTML = '';
  st.series.forEach(se => {
    const cm = se.field === 'raw' ? se.points.map(p => meanOf(p.exam_id)) : null;
    const d = document.createElement('div'); d.className = 'card';
    const legend = cm ? `<div class="legend"><span><i style="border-color:var(--s1)"></i>${st.name}</span><span><i style="border-color:var(--s2);border-top-style:dashed"></i>전체 평균</span></div>` : '';
    const sub = se.field === 'grade' ? '세로축: 위쪽이 1등급' : '세로축: 0~100점';
    const ch = se.changes.map(c => `<li>${c.from} → ${c.to}: <b>${c.text}</b></li>`).join('');
    const rows = se.points.map(p => `<tr><td class="l">${p.label}</td><td>${p.value == null ? '<span class="na">' + p.note + '</span>' : p.value}</td></tr>`).join('');
    d.innerHTML = `<p class="chart-title">${se.title}</p><p class="chart-sub">${sub}</p>${lineChart(se, cm)}${legend}
      <ul class="changes">${ch}</ul>
      <details><summary class="chart-sub" style="cursor:pointer;margin-top:8px">표로 보기</summary><table>${rows}</table></details>`;
    box.appendChild(d);
  });
  Object.entries(st.items || {}).forEach(([eid, it]) => {
    const ex = R.exams.find(x => x.exam_id === eid);
    const d = document.createElement('div'); d.className = 'card';
    if (!it) { d.innerHTML = `<p class="chart-title">${ex.label} 문항</p><p class="chart-sub">응시 자료 없음(결시)</p>`; box.appendChild(d); return; }
    const w = it.wrong.map(x => `<span class="${'AB'.includes(x.band) ? 'easy' : ''}" title="${x.type} · ${x.points}점 · 전국 ${x.band}">${x.item_no}번 ${x.band}</span>`).join('');
    d.innerHTML = `<p class="chart-title">${ex.label} 문항</p><p class="chart-sub">영역별 득점과 틀린 문항(옆 글자는 전국 정답률 구간)</p>
      <div class="kv"><div>듣기<br><b>${it.area['듣기'].got}</b> / ${it.area['듣기'].max}</div><div>읽기<br><b>${it.area['읽기'].got}</b> / ${it.area['읽기'].max}</div></div>
      <p class="chart-sub" style="margin-top:10px">틀린 문항 ${it.wrong.length}개 · 그중 전국 정답률이 높은 A·B 문항 <b class="low">${it.wrong_easy}개</b> (테두리 강조)</p>
      <div class="wrongs">${w || '<span>없음</span>'}</div>`;
    box.appendChild(d);
  });
  (R.naesin.transcripts || []).forEach(t => {
    const d = document.createElement('div'); d.className = 'card'; d.style.gridColumn = '1 / -1';
    const r = t.rows[id], ex = t.excluded.find(e => e.student_id === id);
    const head = `<p class="chart-title">${t.semester}학기 성적표 · ${t.subject}</p>`;
    if (!r) { d.innerHTML = head + `<p class="chart-sub">계산 제외: ${ex ? ex.reason : '자료 없음'}</p>`; box.appendChild(d); return; }
    d.innerHTML = head + `<p class="chart-sub">나이스 학기 성적표와 같은 열 구성 · 석차는 교사 검산용</p>
      <div style="overflow-x:auto"><table class="official"><tr><th>학점</th><th>원점수/과목평균</th><th>성취도(수강자수)</th>
      <th>A</th><th>B</th><th>C</th><th>D</th><th>E</th><th>석차등급</th><th>석차(검산용)</th></tr>
      <tr><td>${t.credits}</td><td>${r.total}/${t.mean.toFixed(1)}</td><td><b>${r.achievement}</b>(${t.n})</td>
      ${'ABCDE'.split('').map(L => `<td>${t.dist[L].toFixed(1)}</td>`).join('')}<td><b>${r.grade}</b></td><td>${r.rank}</td></tr></table></div>
      <p class="small">반올림 전 합계 ${(+r.raw).toFixed(2)}점</p>`;
    box.appendChild(d);
  });
}

// 04 학기 성적
(function(){
  const box = $('#transcripts'), N = R.naesin, ratio = N.rules.grade_ratio.cumulative;
  if (!N.transcripts.length) { box.innerHTML = '<p class="chart-sub">중간·기말·수행평가가 모두 있는 학기가 아직 없습니다.</p>'; return; }
  N.transcripts.forEach(t => {
    const exp = ratio.map((c, i) => c - (i ? ratio[i-1] : 0));
    const dist = 'ABCDE'.split('').map(L => `<tr><td class="l">${L}</td><td class="l"><span class="bar" style="width:${t.dist[L]*2}px"></span>${t.dist[L].toFixed(1)}%</td></tr>`).join('');
    const gc = [1,2,3,4,5].map((g, i) => `<tr><td class="l">${g}등급</td><td>${exp[i]}%</td><td>${ratio[i]}%</td><td>${t.grade_counts[g]}명</td>
      <td>${(100*t.grade_counts[g]/t.n).toFixed(1)}%</td></tr>`).join('');
    const exc = t.excluded.length ? `<p class="small" style="margin-top:8px">계산 제외 ${t.excluded.length}명: ${t.excluded.map(e => e.student_id + ' (' + e.reason + ')').join(', ')}</p>` : '';
    const d = document.createElement('div');
    d.innerHTML = `<div class="grid">
      <div class="card"><p class="chart-title">${t.semester}학기 · ${t.subject} · ${t.credits}학점</p><p class="chart-sub">학기 원점수 기준</p>
        <div class="kv"><div>수강자수<br><b>${t.n}</b>명</div><div>과목평균<br><b>${t.mean.toFixed(1)}</b></div></div>${exc}</div>
      <div class="card"><p class="chart-title">성취도별 분포비율</p><p class="chart-sub">절대평가 · 성적표에 그대로 찍히는 값</p><table>${dist}</table></div>
      <div class="card"><p class="chart-title">석차등급 인원</p><p class="chart-sub">상대평가 · 동점자 때문에 기준 비율과 조금 다를 수 있음</p>
        <table><tr><th class="l">등급</th><th>기준</th><th>누적</th><th>실제</th><th>실제 비율</th></tr>${gc}</table></div></div>`;
    box.appendChild(d);
  });
})();

// 06 기말 시뮬레이션
const GCOL = ['#1f3f80','#2f5bb0','#6b8fd0','#a3bae6','#d3def2'], GINK = ['#fff','#fff','#fff','#18233a','#18233a'];
let simScen = null;
function needText(f, mid, pmax){
  if (f == null) return { main: '만점이어도 어려움', diff: '' };
  if (f <= 0) return { main: '이미 확보', diff: '' };
  const d = f - mid;
  return { main: `${f}점 이상`, diff: d > 0 ? `<span class="plus">+${d}점</span>` : `${d}점` };
}
function renderSim(){
  const S = R.naesin.sim, box = $('#sim'); if (!S) return;
  const id = $('#who2').value, st = S.students[id];
  if (!st) {
    const ex = S.excluded.find(e => e.student_id === id);
    box.innerHTML = `<div class="card"><p class="chart-title">시뮬레이션 불가</p><p class="chart-sub">${ex ? ex.reason : '자료 없음'}</p></div>`;
    $('#perf').innerHTML = ''; return;
  }
  const keep = $('#perf').value;
  $('#perf').innerHTML = st.perf_levels.map(l => `<option value="${l.key}">${l.label}</option>`).join('');
  if (st.perf_levels.some(l => l.key === keep)) $('#perf').value = keep;
  const pk = $('#perf').value, mid = st.mid, scen = S.scenarios.find(x => x.key === simScen);
  const gr = st.grade[simScen][pk], pr = st.predict[simScen][pk], ach = st.achievement[pk];
  const best = pr.indexOf(Math.max(...pr));
  const achAtMid = 'ABCD'.split('').find(L => ach[L] != null && ach[L] <= mid) || 'E';
  const stack = pr.map((p, i) => p > 0 ? `<div style="width:${p*100}%;background:${GCOL[i]};color:${GINK[i]}" data-tip="${i+1}등급 ${(p*100).toFixed(0)}%">${p >= .08 ? (i+1) + '등급 ' + (p*100).toFixed(0) + '%' : ''}</div>` : '').join('');
  const gRows = [1,2,3,4].map(g => {
    const v = gr[g], a = needText(v.p50, mid), b = needText(v.p80, mid);
    const note = v.p80 == null && v.p_at_max > 0 ? `<span class="small"> (만점이면 가능성 ${(v.p_at_max*100).toFixed(0)}%)</span>` : '';
    return `<tr><td class="l"><b>${g}등급</b> 이상</td><td>${a.main}</td><td>${b.main}${note}</td><td>${b.diff || a.diff}</td></tr>`;
  }).join('');
  const aRows = 'ABCD'.split('').map(L => { const t = needText(ach[L], mid);
    return `<tr><td class="l"><b>${L}</b> 이상 (${R.naesin.rules.semesters.find(x => x.semester === S.semester).achievement.cutoffs[L]}점~)</td><td>${t.main}</td><td>${t.diff}</td></tr>`; }).join('');
  box.innerHTML = `
    <div class="card"><p class="chart-title">기말을 중간만큼(${mid}점) 보면</p>
      <p class="chart-sub">${scen.label} · 수행평가 ${st.perf_levels.find(l => l.key === pk).label}</p>
      <div class="kv"><div>성취도<br><span class="big">${achAtMid}</span></div><div>석차등급 (가장 많이 나온 경우)<br><span class="big">${best+1}등급</span> <span class="small">${(pr[best]*100).toFixed(0)}%</span></div></div>
      <div class="stack" role="img" aria-label="석차등급 가능성">${stack}</div>
      <p class="small">${S.runs}번 모의로 만든 결과 중 각 등급이 나온 비율 · 성취도는 정확한 계산</p></div>
    <div class="card"><p class="chart-title">석차등급 목표 → 필요한 기말 점수</p>
      <p class="chart-sub">반반 = 모의 결과의 50%에서 목표 달성 · 안정권 = 80%에서 달성</p>
      <table class="need"><tr><th class="l">목표</th><th>반반</th><th>안정권</th><th>중간 대비</th></tr>${gRows}</table></div>
    <div class="card"><p class="chart-title">성취도 목표 → 필요한 기말 점수</p>
      <p class="chart-sub">내 점수만으로 정해지므로 정확히 계산됩니다</p>
      <table class="need"><tr><th class="l">목표</th><th>필요한 기말</th><th>중간 대비</th></tr>${aRows}</table></div>`;
}
(function(){
  const S = R.naesin.sim;
  if (!S) { $('#simSub').textContent = '중간고사는 있고 기말고사는 아직 없는 학기가 없어 시뮬레이션하지 않았습니다.'; return; }
  const w = S.weights, m = S.model;
  $('#simSub').innerHTML = `${S.semester}학기 ${S.subject} · 중간 ${w.midterm}% + 기말 ${w.final}% + 수행 ${w.performance}% (수행 ${S.performance_max}점 만점) · 응시자 ${S.n}명. 수행평가는 기말 뒤에 하므로 예상 점수를 골라 봅니다.`;
  simScen = S.scenarios[0].key;
  $('#scen').innerHTML = S.scenarios.map(x => `<button type="button" data-k="${x.key}" aria-pressed="${x.key === simScen}">${x.label}</button>`).join('');
  $('#scen').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return;
    simScen = b.dataset.k; $('#scen').querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', x === b)); renderSim(); });
  $('#perf').addEventListener('change', renderSim);
  $('#simNote').innerHTML = `<b>이 결과는 예측이 아니라 “이런 조건이면”의 계산입니다.</b><br>
    다른 학생 기말 점수 = ${m.a.toFixed(1)} + ${m.b.toFixed(2)} × 중간 점수, 여기에 ±${m.sd.toFixed(1)}점 정도 흔들림을 넣어 ${S.runs}번 만들었습니다
    (${m.fallback ? '1학기 자료가 부족해 정한 기본값' : '1학기 중간→기말 ' + m.n + '명 자료로 맞춤'}). ${S.others_perf_note}.
    ${S.excluded.length ? '<br>시뮬레이션 제외: ' + S.excluded.map(e => e.student_id + ' (' + e.reason + ')').join(', ') : ''}`;
})();

// 07 규칙 표
(function(){
  const r = R.naesin.rules, tag = st => `<span class="status ${st === '확인됨' ? 'ok' : 'assume'}">${st}</span>`;
  const rows = [
    ['석차등급 비율', r.grade_ratio.cumulative.map((c, i) => c - (i ? r.grade_ratio.cumulative[i-1] : 0)).join(' / ') + ' %', r.grade_ratio.status, r.grade_ratio.source || ''],
    ['동점자 처리', r.tie_method.value, r.tie_method.status, r.tie_method.choices[r.tie_method.value]],
    ['등급 경계 방식', r.cut_method.value, r.cut_method.status, r.cut_method.choices[r.cut_method.value]],
    ['원점수 반올림', r.total_rounding.places === 0 ? '정수로 반올림' : '소수 ' + r.total_rounding.places + '자리', r.total_rounding.status, '0.5는 올림'],
  ];
  r.semesters.forEach(s => {
    rows.push([`${s.semester}학기 반영 비율`, `중간 ${s.weights.midterm} / 기말 ${s.weights.final} / 수행 ${s.weights.performance}`, s.weights_status, '교과 담당 교사가 정함']);
    const c = s.achievement.cutoffs;
    rows.push([`${s.semester}학기 성취도 기준`, `${s.achievement.mode} · A ${c.A} / B ${c.B} / C ${c.C} / D ${c.D}`, s.achievement.status, '고정분할 또는 변동분할']);
  });
  $('#rulesTable').innerHTML = '<tr><th class="l">항목</th><th class="l">지금 값</th><th class="l">상태</th><th class="l">설명</th></tr>' +
    rows.map(x => `<tr><td class="l">${x[0]}</td><td class="l">${x[1]}</td><td class="l">${tag(x[2])}</td><td class="l small">${x[3]}</td></tr>`).join('');
})();
// 04 문항 분석
function renderItems(eid){
  const ia = R.items[eid];
  const W = 900, H = 246, L = 34, Rr = 8, T = 28, B = 26, n = ia.items.length, cw = (W - L - Rr) / n;
  const Y = v => T + (H - T - B) * (100 - v) / 100;
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="문항별 정답률">`;
  [0, 20, 40, 60, 80, 100].forEach(v => { s += `<line x1="${L}" x2="${W-Rr}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--grid)"/><text x="${L-6}" y="${Y(v)+4}" text-anchor="end">${v}</text>`; });
  const lx = L + 17 * cw; s += `<line x1="${lx}" x2="${lx}" y1="${T}" y2="${H-B}" stroke="var(--line)" stroke-dasharray="3 3"/>`;
  s += `<text x="${L + 8.5*cw}" y="14" text-anchor="middle" style="font-weight:700">듣기 1~17</text><text x="${lx + (n-17)*cw/2}" y="14" text-anchor="middle" style="font-weight:700">읽기 18~45</text>`;
  ia.items.forEach((it, i) => {
    const x = L + i * cw, [lo, hi] = it.band_range;
    s += `<rect x="${x+2}" y="${Y(hi)}" width="${cw-4}" height="${Y(lo)-Y(hi)}" rx="3" fill="var(--s1)" opacity=".14"/>`;
    if (it.class_rate != null) {
      const low = it.position === '낮음';
      s += `<circle cx="${x+cw/2}" cy="${Y(it.class_rate)}" r="${low ? 5 : 4}" fill="${low ? 'var(--accent)' : 'var(--s1)'}" stroke="var(--surface)" stroke-width="2"/>`;
    }
    s += `<rect x="${x}" y="${T}" width="${cw}" height="${H-B-T}" fill="transparent" data-tip="${it.item_no}번 ${it.type} · ${it.points}점 · 전국 ${it.band}(${lo}~${hi}%) · 우리 학생 ${it.class_rate == null ? '—' : it.class_rate.toFixed(0) + '%'} · ${it.position}"/>`;
    if (it.item_no === 1 || it.item_no % 5 === 0) s += `<text x="${x+cw/2}" y="${H-8}" text-anchor="middle">${it.item_no}</text>`;
  });
  s += '</svg>';
  const lows = ia.items.filter(i => i.position === '낮음');
  $('#itemChart').innerHTML = `<p class="chart-title">문항별 우리 학생 정답률</p>
    <p class="chart-sub">옅은 막대 = 전국 정답률 구간 · 점 = 우리 학생 정답률 · 가로축 문항 번호 · 마우스를 올리면 자세히</p>
    <div style="overflow-x:auto"><div style="min-width:560px">${s}</div></div>
    <div class="legend"><span><i style="border-color:var(--s1);border-top-width:8px;opacity:.3"></i>전국 구간</span><span>● 우리 학생</span><span class="low">● 전국 구간보다 낮음</span></div>
    <p class="chart-sub" style="margin-top:10px">전국 구간보다 낮은 문항 <b class="low">${lows.length}개</b>: ${lows.map(i => i.item_no + '번(' + i.type + ')').join(', ') || '없음'}</p>`;
  $('#typeTable').innerHTML = '<tr><th class="l">유형</th><th>문항</th><th class="l">정답률</th></tr>' + ia.types.map(t =>
    `<tr><td class="l">${t.type}</td><td>${t.n_items}</td><td class="l"><span class="bar" style="width:${(t.rate||0)*0.8}px"></span>${t.rate == null ? '—' : t.rate.toFixed(0) + '%'}</td></tr>`).join('');
  $('#checkBox').innerHTML = ia.check_problems.length
    ? `<p class="low">확인 필요 ${ia.check_problems.length}건</p><ul class="changes">${ia.check_problems.map(p => `<li>${p}</li>`).join('')}</ul>`
    : `<p>✓ 응시자 전원의 원점수가 맞힌 문항 배점의 합과 일치합니다. (만점 ${ia.max_points}점)</p>`;
  $('#itemTable').innerHTML = '<tr><th>번호</th><th class="l">영역</th><th class="l">유형</th><th>배점</th><th>전국 구간</th><th>우리 학생 정답률</th><th class="l">비교</th></tr>' +
    ia.items.map(i => `<tr><td>${i.item_no}</td><td class="l">${i.area}</td><td class="l">${i.type}</td><td>${i.points}</td>
      <td><span class="band">${i.band}</span> ${i.band_range[0]}~${i.band_range[1]}%</td><td>${i.class_rate == null ? '—' : i.class_rate.toFixed(1) + '%'} (${i.n_correct}/${i.n})</td>
      <td class="l ${i.position === '낮음' ? 'low' : ''}">${i.position}</td></tr>`).join('');
}
(function(){
  const ids = Object.keys(R.items || {}), sel = $('#itemExam');
  if (!ids.length) { $('#itemChart').innerHTML = '<p class="chart-sub">문항 자료(items.csv, responses.csv)가 없습니다.</p>'; return; }
  sel.innerHTML = ids.map(id => `<option value="${id}">${R.exams.find(e => e.exam_id === id).label}</option>`).join('');
  sel.addEventListener('change', () => renderItems(sel.value));
  renderItems(ids[0]);
})();
(function(){
  const sel = $('#who'), sel2 = $('#who2');
  const classes = [...new Set(R.students.map(s => s['class']))];
  const opts = classes.map(c => `<optgroup label="${c}반">` + R.students.filter(s => s['class'] === c)
    .map(s => `<option value="${s.student_id}">${c} ${s.number}번 ${s.name}</option>`).join('') + '</optgroup>').join('');
  sel.innerHTML = opts; sel2.innerHTML = opts;
  sel.addEventListener('change', () => { sel2.value = sel.value; renderStudent(sel.value); renderSim(); });
  sel2.addEventListener('change', () => { sel.value = sel2.value; renderStudent(sel2.value); renderSim(); });
  renderStudent(R.students[0].student_id); renderSim();
  document.addEventListener('mousemove', e => { const t = e.target.closest('[data-tip]'); t ? showTip(e, t.dataset.tip) : hideTip(); });
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "data" / "sample"
    if not (src / "scores.csv").exists():
        import generate_sample
        generate_sample.main()
    path = build(src)
    print(f"보고서를 만들었습니다: {path}")
    print("이 파일을 더블클릭하면 브라우저에서 열립니다.")
