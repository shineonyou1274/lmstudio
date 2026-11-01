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

OUT = HERE / "output" / "report.html"


def build(data_dir: Path) -> Path:
    data = analysis.load(data_dir)
    result = analysis.analyze(data)
    payload = json.dumps(result, ensure_ascii=False)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = TEMPLATE.replace("__DATA__", payload).replace("__STAMP__", stamp).replace(
        "__SOURCE__", str(Path(data_dir).name)
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    return OUT


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
footer{margin-top:48px;color:var(--muted);font-size:12px;border-top:1px solid var(--line);padding-top:12px}
</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="kicker">SCHOOL AI LAB · 성적 분석실</div>
  <h1>영어 성적 분석<br>가상 자료 시험판</h1>
  <p class="lede">시험별 요약과 학생별 변화를 보여 줍니다. 계산은 코드가 하며, AI 해석은 아직 붙이지 않았습니다.</p>
  <div class="notice">⚠ 이 화면의 학생과 점수는 모두 <b>가상 자료</b>입니다. 실제 학생 정보가 아닙니다.</div>
</header>

<h2><span class="no">01</span>시험별 요약</h2>
<p class="sub">결시는 통계에서 빼고 따로 셉니다. 응시했지만 필요한 칸이 빈 경우는 ‘누락’으로 따로 셉니다. 빈칸(—)은 그 시험에서 제공되지 않는 항목입니다.</p>
<div class="tablewrap"><table id="summary"></table></div>

<h2><span class="no">02</span>모의고사 등급 분포</h2>
<p class="sub">영어는 절대평가입니다. 막대 위에 마우스를 올리면 인원이 보입니다.</p>
<div class="grid" id="dists"></div>

<h2><span class="no">03</span>학생별 변화</h2>
<p class="sub">같은 항목끼리만 잇습니다. 내신과 모의고사는 섞지 않습니다. 평가원은 원점수가 없어 등급으로만 비교합니다.</p>
<div class="picker"><label for="who"><b>학생 선택</b></label><select id="who"></select></div>
<div class="grid" id="student"></div>

<h2><span class="no">04</span>전국연합 문항 분석</h2>
<p class="sub">문항마다 전국 정답률 구간(A 80~100% … E 0~20%)과 우리 반 정답률을 나란히 봅니다. 결시자는 분모에서 뺍니다.</p>
<div class="picker"><label for="itemExam"><b>시험 선택</b></label><select id="itemExam"></select></div>
<div class="card" id="itemChart"></div>
<div class="grid" style="margin-top:16px">
  <div class="card"><p class="chart-title">유형별 우리 반 정답률</p><p class="chart-sub">유형에 속한 문항을 묶어 계산 (맞힌 수 ÷ 응답 수)</p><table id="typeTable"></table></div>
  <div class="card"><p class="chart-title">자료 점검</p><p class="chart-sub">원점수가 맞힌 문항 배점의 합과 같은지 확인합니다</p><div id="checkBox"></div></div>
</div>
<details style="margin-top:16px"><summary class="chart-sub" style="cursor:pointer">45문항 전체 표로 보기</summary>
<div class="tablewrap" style="margin-top:8px"><table id="itemTable"></table></div></details>

<h2><span class="no">05</span>계산 방법과 한계</h2>
<ul class="method">
  <li><b>문항 비교</b>: 우리 반 정답률이 들어가는 구간을 전국 구간과 비교해 ‘높음 / 범위 안 / 낮음’으로 표시합니다. 구간 경계값(예: 80%)은 위쪽 구간(A)에 넣었습니다. 한 반은 인원이 적어 몇 명 차이로도 구간이 바뀝니다.</li>
  <li><b>평균·중앙값·표준편차</b>: 결시자와 해당 칸이 빈 학생은 빼고 계산합니다. 표준편차는 모집단 표준편차(인원수 n으로 나눔)입니다.</li>
  <li><b>등급</b>은 순서를 나타내는 값이라 평균 대신 <b>분포와 중앙값</b>으로 보여 줍니다.</li>
  <li><b>변화</b>: 바로 앞 시험과 비교합니다. 둘 중 하나라도 값이 없으면 ‘비교 불가’와 그 이유를 적습니다. 등급은 숫자가 작아지면 ‘상승’입니다.</li>
  <li><b>전국연합과 평가원</b>은 출제 기관과 응시 집단이 달라, 같은 등급이라도 난이도가 다를 수 있습니다.</li>
  <li><b>점수 변화의 원인</b>은 이 자료로 알 수 없습니다. 시험 난이도, 범위, 컨디션 등 자료에 없는 요인이 있습니다.</li>
  <li>모든 계산은 손으로 계산한 작은 자료와, 파이썬 표준 통계 모듈로 따로 계산한 값에 대조해 검증했습니다(<code>grade_lab/tests</code>).</li>
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
    s += `<circle cx="${X(i)}" cy="${Y(v)}" r="4" fill="var(--s2)" stroke="var(--surface)" stroke-width="2" data-tip="${pts[i].label} 반 평균 ${v.toFixed(1)}점"/>`; });
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
    const legend = cm ? `<div class="legend"><span><i style="border-color:var(--s1)"></i>${st.name}</span><span><i style="border-color:var(--s2);border-top-style:dashed"></i>반 평균</span></div>` : '';
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
}
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
    s += `<rect x="${x}" y="${T}" width="${cw}" height="${H-B-T}" fill="transparent" data-tip="${it.item_no}번 ${it.type} · ${it.points}점 · 전국 ${it.band}(${lo}~${hi}%) · 우리 반 ${it.class_rate == null ? '—' : it.class_rate.toFixed(0) + '%'} · ${it.position}"/>`;
    if (it.item_no === 1 || it.item_no % 5 === 0) s += `<text x="${x+cw/2}" y="${H-8}" text-anchor="middle">${it.item_no}</text>`;
  });
  s += '</svg>';
  const lows = ia.items.filter(i => i.position === '낮음');
  $('#itemChart').innerHTML = `<p class="chart-title">문항별 우리 반 정답률</p>
    <p class="chart-sub">옅은 막대 = 전국 정답률 구간 · 점 = 우리 반 정답률 · 가로축 문항 번호 · 마우스를 올리면 자세히</p>
    <div style="overflow-x:auto"><div style="min-width:560px">${s}</div></div>
    <div class="legend"><span><i style="border-color:var(--s1);border-top-width:8px;opacity:.3"></i>전국 구간</span><span>● 우리 반</span><span class="low">● 전국 구간보다 낮음</span></div>
    <p class="chart-sub" style="margin-top:10px">전국 구간보다 낮은 문항 <b class="low">${lows.length}개</b>: ${lows.map(i => i.item_no + '번(' + i.type + ')').join(', ') || '없음'}</p>`;
  $('#typeTable').innerHTML = '<tr><th class="l">유형</th><th>문항</th><th class="l">정답률</th></tr>' + ia.types.map(t =>
    `<tr><td class="l">${t.type}</td><td>${t.n_items}</td><td class="l"><span class="bar" style="width:${(t.rate||0)*0.8}px"></span>${t.rate == null ? '—' : t.rate.toFixed(0) + '%'}</td></tr>`).join('');
  $('#checkBox').innerHTML = ia.check_problems.length
    ? `<p class="low">확인 필요 ${ia.check_problems.length}건</p><ul class="changes">${ia.check_problems.map(p => `<li>${p}</li>`).join('')}</ul>`
    : `<p>✓ 응시자 전원의 원점수가 맞힌 문항 배점의 합과 일치합니다. (만점 ${ia.max_points}점)</p>`;
  $('#itemTable').innerHTML = '<tr><th>번호</th><th class="l">영역</th><th class="l">유형</th><th>배점</th><th>전국 구간</th><th>우리 반 정답률</th><th class="l">비교</th></tr>' +
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
  const sel = $('#who');
  sel.innerHTML = R.students.map(s => `<option value="${s.student_id}">${s.number}번 ${s.name}</option>`).join('');
  sel.addEventListener('change', () => renderStudent(sel.value));
  renderStudent(R.students[0].student_id);
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
