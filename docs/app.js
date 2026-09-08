'use strict';
const LABELS={all:'전체',headliners:'유명 아티스트',korean:'한국 가수',picks:'놓치기 아쉬운 클래식',classical:'클래식 전체',jazz:'재즈',discovery:'새로운 음악',exhibition:'전시'};
const GENRES=['Rock','Pop','K-pop','Metal','Hip-hop / R&B','Jazz','Electronic','Folk / Country','Classical','Other'];
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl=s=>{try{const u=new URL(s);return ['http:','https:'].includes(u.protocol)?u.href:'#';}catch{return '#';}};
const TODAY=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/London',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
let visibleLimit=40;
let lastSignature='';
let EVENTS=[],activeCat='all',sortKey='period',sortDir=1,onlySaved=false,sourceWarnings=0,loadFailed=false;
let saved=new Set();
try{const stored=JSON.parse(localStorage.getItem('london-culture-saved')||'[]');if(Array.isArray(stored))saved=new Set(stored);}catch{}
const key=e=>[e.url,e.start,e.time].join('|');
const isCat=(e,c)=>c==='all'||(c==='discovery'?!!e.discovery:c==='jazz'?e.genre==='Jazz':c==='picks'?e.collection==='classical'&&e.featured:e.collection===c);
const dated=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s);
function dateLabel(s){return dated(s)?s.replaceAll('-','.'):'';}
function period(e){if(e.start===e.end&&e.start)return dateLabel(e.start)+(e.time?' · '+e.time:'');if(e.start&&e.end)return dateLabel(e.start)+' – '+dateLabel(e.end);return e.end?dateLabel(e.end)+'까지':dateLabel(e.start);}
function status(e){if(e.collection==='exhibition'&&(!e.start||e.start<=TODAY)&&e.end>=TODAY){const days=(Date.parse(e.end)-Date.parse(TODAY))/86400000;return days<=14?'곧 종료':'전시 중';}return e.start===TODAY?'오늘':'';}
function venueGroup(name){
  const n=(name||'').trim();
  if(/vortex/i.test(n))return 'Vortex';
  if(/ronnie.*scott/i.test(n))return "Ronnie Scott's";
  if(/barbican/i.test(n))return 'Barbican';
  if(/royal albert hall/i.test(n))return 'Royal Albert Hall';
  if(/royal festival hall/i.test(n))return 'Royal Festival Hall';
  if(/queen elizabeth hall/i.test(n))return 'Queen Elizabeth Hall';
  if(/kings place/i.test(n))return 'Kings Place';
  if(/wigmore hall/i.test(n))return 'Wigmore Hall';
  return n;
}
function buildVenues(){
  const current=$('venue').value;
  const venues=[...new Set(EVENTS.filter(e=>isCat(e,activeCat)).map(e=>venueGroup(e.venue)).filter(n=>n&&n!=='London'))].sort((a,b)=>a.localeCompare(b));
  $('venue').innerHTML='<option value="all">전체 장소</option>'+venues.map(v=>'<option value="'+esc(v)+'">'+esc(v)+'</option>').join('');
  $('venue').value=venues.includes(current)?current:'all';
}
function buildFilters(){
  $('filters').innerHTML=Object.entries(LABELS).map(([k,v])=>`<button data-c="${k}" class="${k===activeCat?'active':''}" aria-pressed="${k===activeCat}">${v}<small>${EVENTS.filter(e=>isCat(e,k)).length}</small></button>`).join('');
  $('filters').querySelectorAll('button').forEach(b=>b.onclick=()=>{activeCat=b.dataset.c;$('genre').value='all';buildFilters();buildVenues();render();});
}
$('genre').innerHTML='<option value="all">전체 장르</option>'+GENRES.map(g=>`<option value="${esc(g)}">${esc(g)}</option>`).join('');
function sortValue(e){if(sortKey==='title')return e.title||'';if(sortKey==='venue')return e.venue||'';if(sortKey==='type')return e.genre||e.type||'';if(sortKey==='ending')return e.end||e.start||'9999';return (e.start&&e.start>=TODAY?e.start:TODAY)+(e.time||'');}
function render(){
  if(loadFailed)return;
  const q=$('q').value.toLocaleLowerCase().trim(),genre=$('genre').value,venue=$('venue').value,days=Number($('range').value);
  const end=days?new Date(Date.parse(TODAY)+(days-1)*86400000).toISOString().slice(0,10):null;
  const list=EVENTS.filter(e=>isCat(e,activeCat)&&(venue==='all'||venueGroup(e.venue)===venue)&&(genre==='all'||e.genre===genre)&&(!onlySaved||saved.has(key(e)))&&(!end||(!e.start||e.start<=end))&&(!q||[e.title,e.subtitle,e.venue,e.programme,e.genre,e.source,...(e.reasons||[])].join(' ').toLocaleLowerCase().includes(q)));
  const signature=JSON.stringify([activeCat,q,genre,venue,days,onlySaved,sortKey,sortDir]);
  if(signature!==lastSignature){visibleLimit=40;lastSignature=signature;}
  list.sort((a,b)=>sortDir*String(sortValue(a)).localeCompare(String(sortValue(b)))||String(a.title).localeCompare(String(b.title)));
  $('genre').disabled=activeCat==='exhibition';
  $('empty').style.display=list.length?'none':'block';
  $('count').textContent=`${list.length}개의 일정 · 종료된 일정은 자동으로 숨깁니다.`;
  $('context').textContent=(activeCat==='jazz'?'런던 재즈 공연과 재즈 클럽 프로그램입니다. 공연장별로 골라 보세요.':activeCat==='discovery'?'EartH·Serious 공개 일정에서 찾은 음악입니다. 관심 목록 밖의 아티스트도 포함합니다.':activeCat==='picks'?'관심 연주자·지휘자·방문 오케스트라가 포함된 클래식입니다. 선정 이유를 확인해 보세요.':activeCat==='korean'?'한국 가수 관심 목록과 K-pop 분류로 찾은 런던 일정입니다. 밴드·인디 공연도 포함됩니다.':activeCat==='headliners'?'Bon Jovi 등을 포함한 관심 목록 기준입니다. 트리뷰트·클럽 파티는 제외합니다.':genre!=='all'?`${genre} · 관심 목록에 맞는 음악 일정입니다.`:'취향 분류와 음악 장르, 기간을 조합해 일정을 찾아보세요.')+(sourceWarnings?` 일부 소스(${sourceWarnings}개)의 갱신을 확인해야 합니다. 하단 수집 상태를 확인하세요.`:'');
  $('list').innerHTML=list.slice(0,visibleLimit).map(e=>`<article class="row"><div class="year">${esc(period(e))}${status(e)?`<br><strong>${esc(status(e))}</strong>`:''}</div><div>${e.featured?'<span class="tag">CLASSICAL PICK</span>':''}<div class="title-en"><a href="${esc(safeUrl(e.url))}" target="_blank" rel="noopener noreferrer">${esc(e.title)} ↗</a></div>${e.subtitle?`<div class="title-sub">${esc(e.subtitle)}</div>`:''}${e.schedule_note?`<div class="programme">${esc(e.schedule_note)}</div>`:''}${e.programme?`<div class="programme">${esc(e.programme)}</div>`:''}${(e.reasons||[]).length?`<div class="reason">${e.reasons.map(esc).join('<br>')}</div>`:''}${e.verification_mode==='manual'?`<div class="stale">직접 확인 ${esc((e.verified_at||'').slice(0,10))} · 예매 전 원본 확인</div>`:''}${e.stale?'<div class="stale">이전 수집 정보 · 원본에서 일정 확인 필요</div>':''}<button class="bookmark" data-key="${esc(key(e))}" aria-pressed="${saved.has(key(e))}" aria-label="${esc(e.title)} 저장">${saved.has(key(e))?'저장됨 ✓':'일정 저장 +'}</button></div><div class="type">${esc(e.genre||e.type)}<span class="src">${esc(e.source)}${e.verification_source?' · '+esc(e.verification_source)+' 확인':''}</span>${e.price?`<span class="price">${esc(e.price)}</span>`:''}</div><div class="loc">${esc(e.venue||'공연장 확인 필요')}<span class="sub">London</span></div></article>`).join('');
  $('more').hidden=list.length<=visibleLimit;
  $('more').textContent='일정 더 보기 ('+Math.min(visibleLimit,list.length)+' / '+list.length+')';
  $('list').querySelectorAll('.bookmark').forEach(b=>b.onclick=()=>{const k=b.dataset.key;saved.has(k)?saved.delete(k):saved.add(k);try{localStorage.setItem('london-culture-saved',JSON.stringify([...saved]));}catch{}render();});
  document.querySelectorAll('[data-sort]').forEach(h=>{const on=h.dataset.sort===sortKey;h.classList.toggle('sorted',on);h.querySelector('.ind').textContent=on?(sortDir===1?'↑':'↓'):'';});
}
function load(data){
  if(!Array.isArray(data.events))throw new Error('Invalid events data');
  EVENTS=data.events.filter(e=>e.collection&&dated(e.end||e.start)&&(e.end||e.start)>=TODAY);
  sourceWarnings=(data.sources||[]).filter(s=>s.status!=='ok').length;
  const updated=Date.parse(data.updated);
  const old=!Number.isFinite(updated)||(Date.now()-updated)>36*3600000;
  $('updated').textContent=(old?'갱신 지연 · ':'마지막 수집 시도 · ')+(Number.isFinite(updated)?new Intl.DateTimeFormat('ko-KR',{timeZone:'Europe/London',dateStyle:'medium',timeStyle:'short'}).format(new Date(updated)):'확인 필요');
  $('sources').innerHTML=(data.sources||[]).map(s=>`<div><strong>${esc(s.name)}</strong> · ${s.status==='ok'?'수집 완료':s.status==='manual'?'등록 정보 · 직접 확인':'갱신 실패'} · ${s.count}개${s.last_success?' · 마지막 확인 '+esc(s.last_success.slice(0,10)):''}${s.status==='unavailable'?'<br>원본 목록을 확인하세요. 최근에 확인한 정보가 있으면 최대 7일간 표시합니다.':''}</div>`).join('');
  if(sourceWarnings||old)$('source-details').open=true;
  buildFilters();buildVenues();render();
}
async function fetchEvents(){try{const r=await fetch('events.json?_='+Date.now());if(!r.ok)throw new Error('HTTP');load(await r.json());}catch{loadFailed=true;$('updated').textContent='일정을 불러오지 못했습니다';$('list').innerHTML='';$('empty').style.display='block';$('empty').innerHTML='일정 데이터를 불러오지 못했습니다. 연결을 확인한 뒤 다시 시도해 주세요.<br><button id="retry">다시 시도</button>';$('retry').onclick=()=>location.reload();}}
$('q').addEventListener('input',render);
['genre','range','venue'].forEach(id=>$(id).addEventListener('change',render));
$('sort').onchange=()=>{sortKey=$('sort').value;sortDir=1;render();};
$('saved').onclick=()=>{onlySaved=!onlySaved;$('saved').setAttribute('aria-pressed',String(onlySaved));render();};
$('reset').onclick=()=>{activeCat='all';onlySaved=false;sortKey='period';sortDir=1;$('q').value='';['genre','range','venue'].forEach(id=>$(id).value='all');$('sort').value='period';$('saved').setAttribute('aria-pressed','false');buildFilters();buildVenues();render();};
document.querySelectorAll('[data-sort]').forEach(h=>{h.tabIndex=0;h.setAttribute('role','button');function sort(){if(sortKey===h.dataset.sort)sortDir*=-1;else{sortKey=h.dataset.sort;sortDir=1;}$('sort').value=sortKey;render();}h.onclick=sort;h.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();sort();}};});
$('more').onclick=()=>{visibleLimit+=40;render();};
fetchEvents();
