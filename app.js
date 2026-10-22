// 이 파일에는 Meta 액세스 토큰을 절대로 입력하지 마세요.
// 추후 GitHub Actions가 data/dashboard.json을 생성하면 이를 읽습니다.
const AGENCIES=[
 {name:'예시 중앙부처 A',level:'장관급',followers:186400},
 {name:'예시 중앙부처 B',level:'장관급',followers:155200},
 {name:'예시 중앙부처 C',level:'장관급',followers:122800},
 {name:'예시 중앙부처 D',level:'장관급',followers:102500},
 {name:'예시 중앙부처 E',level:'장관급',followers:95600},
 {name:'예시 중앙부처 F',level:'장관급',followers:86400},
 {name:'예시 중앙부처 G',level:'장관급',followers:79300},
 {name:'예시 중앙부처 H',level:'차관급',followers:81400},
 {name:'예시 중앙부처 I',level:'차관급',followers:72200},
 {name:'예시 중앙부처 J',level:'차관급',followers:66600},
 {name:'예시 중앙부처 K',level:'차관급',followers:54100},
 {name:'예시 중앙부처 L',level:'차관급',followers:48100},
 {name:'예시 중앙부처 M',level:'차관급',followers:41500},
 {name:'예시 중앙부처 N',level:'차관급',followers:35700}
];
const dates=['2026-10-14','2026-10-13','2026-10-12','2026-10-11','2026-10-10','2026-10-09','2026-10-08','2026-10-07','2026-10-06','2026-10-04','2026-09-29','2026-09-17'];
const titles=['가을의 도시 풍경을 담았습니다','시민과 함께 만드는 정책 이야기','우리 동네에서 발견한 새로운 변화','직원이 직접 소개하는 현장 이야기','알아두면 쓸모 있는 정책 정보','질문으로 알아보는 주요 사업','현장에서 전하는 일상 속 변화','숏폼으로 만나는 이번 주 소식','공간을 새롭게 이용하는 방법','모두가 함께하는 생활 속 캠페인','10월 주요 일정 한눈에 보기','정책 현장을 찾아서'];
const MOCK_POSTS=Array.from({length:52},(_,i)=>{const a=AGENCIES[i%AGENCIES.length],kind=['VIDEO','CAROUSEL_ALBUM','IMAGE'][i%3];return {id:'sample-'+i,agency:a.name,level:a.level,date:dates[i%dates.length],type:kind,caption:'[가상 예시] '+titles[i%titles.length],likes:Math.max(18,2480-i*37+(i%5)*81),comments:Math.max(0,172-i*3+(i%7)*5),views:kind==='VIDEO'?Math.max(300,93500-i*1273+(i%4)*6200):null,view_delta:kind==='VIDEO'?Math.max(0,3120-i*36):null,permalink:'',thumbnail:''}});
let agencies=AGENCIES,posts=MOCK_POSTS,demo=true,shownPosts=5,rankSizes={minister:5,vice:5},commentMode="all",postView="table";
const $=id=>document.getElementById(id);const num=v=>Number(v||0).toLocaleString('ko-KR');const safe=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const fmt=v=>v===null||v===undefined?'—':num(v);const formatLabel=t=>({VIDEO:'동영상',IMAGE:'이미지',CAROUSEL_ALBUM:'카드뉴스'})[t]||t||'기타';
function updateCollectionStatus(data) {
  const date = new Date(data.collected_at);
  const count = Array.isArray(data.agencies) ? data.agencies.length : 0;

  if (isNaN(date.getTime())) {
    $('collectionStatusText').textContent =
      '마지막 수집 시간을 확인할 수 없습니다.';
    return;
  }

  const dateText = new Intl.DateTimeFormat('ko-KR', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  }).format(date);

  const elapsedDays = (Date.now() - date.getTime()) / 86400000;
  const status = elapsedDays >= 2
    ? '⚠️ 데이터 갱신 지연 확인 필요'
    : '✅ 최근 수집 데이터 확인됨';

  $('collectionStatusText').textContent =
    `${status} | 마지막 수집: ${dateText} | 수집 기관: ${count}개`;
}
function normalize(data){const a=Array.isArray(data.agencies)?data.agencies:[];const p=Array.isArray(data.posts)?data.posts:[];if(!a.length)return false;agencies=a.map(x=>({...x,name:String(x.name||x.username||'알 수 없음'),level:x.level||'기타',followers:Number(x.followers??x.followers_count??0)}));posts=p.map((x,i)=>({...x,id:x.id||'row-'+i,agency:x.agency||x.agency_name||'알 수 없음',level:x.level||agencies.find(a=>a.name===(x.agency||x.agency_name))?.level||'기타',date:String(x.date||x.timestamp||'').slice(0,10),type:x.type||x.media_type||'IMAGE',caption:x.caption||'',likes:Number(x.likes??x.like_count??0),comments:Number(x.comments??x.comments_count??0),views:x.views??x.view_count??null,view_delta:x.view_delta??null,thumbnail:x.thumbnail||x.thumbnail_url||x.media_url||'',media_url:x.media_url||'',video_url:x.video_url||'',children:Array.isArray(x.children)?x.children:Array.isArray(x.media_children)?x.media_children:[],permalink:x.permalink||''}));demo=false;$('demoNotice').hidden=true;$('statusText').textContent='실제 API 수집 · '+agencies.length+'개 계정 · '+(data.updated_at||'업데이트 확인 필요');$('updatedAt').textContent='최근 데이터 수집: '+(data.updated_at||'정보 없음')+' · '+agencies.length+'개 계정';return true}
async function load() {
  try {
    const response = await fetch('dashboard.json?ts=' + Date.now(), {cache: 'no-store'});
    if (!response.ok) throw new Error(`Dashboard manifest HTTP ${response.status}`);
    const data = await response.json();
    if (Array.isArray(data.post_files)) {
      // All archives must load before rendering, to avoid silently missing posts.
      const parts = await Promise.all(data.post_files.map(async file => {
        if (!/^data\/posts-2026-[0-9]{2}-[0-9]{2}\.json$/.test(file)) {
          throw new Error('Invalid post archive filename');
        }
        const result = await fetch(file + '?ts=' + Date.now(), {cache: 'no-store'});
        if (!result.ok) throw new Error(`Post archive HTTP ${result.status}: ${file}`);
        const rows = await result.json();
        if (!Array.isArray(rows)) throw new Error(`Invalid post archive: ${file}`);
        return rows;
      }));
      data.posts = parts.flat();
    }
    if (!normalize(data)) throw new Error('No agencies in dashboard data');
    updateCollectionStatus(data);
  } catch (e) {
    console.error('대시보드 데이터 불러오기 오류:', e);
    $('collectionStatusText').textContent = '⚠️ 수집 데이터를 불러오지 못했습니다. 새로고침하거나 관리자에게 확인해 주세요.';
    $('statusText').textContent = '⚠️ 데이터 불러오기 실패';
    // Do not show demonstration statistics as if they were real.
    agencies = [];
    posts = [];
    demo = false;
    $('demoNotice').hidden = true;
  }
  renderAll();
}
function kpi(label,val,note,ico){return `<div class="card kpi"><div class="kpi-top"><span>${label}</span><span class="kpi-icon">${ico}</span></div><div class="kpi-val">${safe(val)}</div><div class="kpi-note">${safe(note)}</div></div>`}
function videoKpi(label, post, value, icon) {
  if (!post) return kpi(label, '—', '해당 영상 없음', icon);

  return `
    <div class="card kpi">
      <div class="kpi-top">
        <span>${safe(label)}</span>
        <span class="kpi-icon">${icon}</span>
      </div>
      <div style="display:flex;align-items:center;gap:13px;margin-top:15px">
        ${post.thumbnail
          ? `<img src="${safe(post.thumbnail)}" alt="영상 썸네일"
               loading="lazy"
               style="width:90px;height:110px;object-fit:cover;border-radius:9px;flex-shrink:0">`
          : ''}
        <div style="min-width:0;flex:1">
          <div style="font-size:23px;font-weight:800">${safe(value)}</div>
          <div style="font-size:13px;font-weight:700;margin-top:6px">${safe(post.agency)}</div>
          <div style="font-size:12px;color:#6e7889;margin-top:4px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">
            ${safe(post.caption)}
          </div>
          ${post.permalink
            ? `<a href="${safe(post.permalink)}" target="_blank" rel="noopener noreferrer"
                 style="display:inline-block;margin-top:7px;font-size:12px;color:#4866d8;text-decoration:underline">
                 인스타그램 원문 보기 ↗
               </a>`
            : ''}
        </div>
      </div>
    </div>`;
}
function renderKpis(){let total=agencies.reduce((s,a)=>s+a.followers,0),ministers=agencies.filter(a=>a.level==='장관급').sort((a,b)=>b.followers-a.followers),vices=agencies.filter(a=>a.level==='차관급').sort((a,b)=>b.followers-a.followers),now=posts.map(x=>new Date(x.date+'T12:00:00+09:00')).filter(x=>!isNaN(x)),ref=demo?new Date('2026-10-14T12:00:00+09:00'):new Date(),seven=new Date(ref.getTime()-7*86400000),recent=posts.filter(p=>new Date(p.date+'T12:00:00+09:00')>=seven&&new Date(p.date+'T12:00:00+09:00')<=ref),best=recent.filter(p=>p.type==='VIDEO'&&p.views!=null).sort((a,b)=>b.views-a.views)[0],hot=posts.filter(p=>p.type==='VIDEO'&&p.view_delta!=null).sort((a,b)=>b.view_delta-a.view_delta)[0];$('kpis').innerHTML=[kpi('총 팔로워',num(total)+'명',`수집된 ${agencies.length}개 기관 합계`,'♧'),kpi('장관급 채널 1위',ministers[0]?num(ministers[0].followers)+'명':'—',ministers[0]?.name||'수집 데이터 없음','♛'),kpi('차관급 채널 1위',vices[0]?num(vices[0].followers)+'명':'—',vices[0]?.name||'수집 데이터 없음','♕'),kpi('평균 팔로워',agencies.length?num(Math.round(total/agencies.length))+'명':'—',`수집된 ${agencies.length}개 기관 기준`,'≋'),videoKpi('지난 1주일 최고 조회수 영상',best,num(best?.views)+'회','▷'),videoKpi('가장 핫한 영상',hot,'+'+num(hot?.view_delta)+'회','↗')].join('')}
function renderRank(key,level,container,btn){
 const sorted=agencies.filter(a=>a.level===level).sort((a,b)=>b.followers-a.followers);
 const visible=sorted.slice(0,rankSizes[key]);
 $(container).innerHTML=visible.length?visible.map((a,i)=>`<div class="ranking"><span class="number" style="width:32px;white-space:nowrap">${i+1}위</span><span class="avatar" aria-hidden="true">${safe(a.name.slice(-1))}</span><div style="min-width:0"><div class="rank-name">${safe(a.name)}</div><div class="rank-sub">${safe(a.username?'@'+a.username:a.level)}</div></div><span class="rank-count">${num(a.followers)}명</span></div>`).join(''):'<div class="empty">표시할 기관이 없습니다.</div>';
 $(btn).hidden=sorted.length<=5;
 $(btn).textContent=rankSizes[key]>=sorted.length?'접기':'더보기 +5';
 $(btn).onclick=()=>{
  rankSizes[key]=rankSizes[key]>=sorted.length?5:Math.min(rankSizes[key]+5,sorted.length);
  renderRank(key,level,container,btn);
 };
}
function updatePopularPeriod() {
  const ref = demo
    ? new Date('2026-10-14T12:00:00+09:00')
    : new Date();

  const min = new Date(ref.getTime() - 7 * 86400000);

  const formatDate = d => {
    const parts = new Intl.DateTimeFormat('en-US', {
      timeZone: 'Asia/Seoul',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    }).formatToParts(d);

    const get = type => parts.find(p => p.type === type).value;
    return `${get('year')}.${get('month')}.${get('day')}.`;
  };

  $('popularPeriod').textContent =
    `집계 기간: ${formatDate(min)} ~ ${formatDate(ref)}`;
}  
function renderPopular(){
  updatePopularPeriod();
  let ref=demo?new Date('2026-10-14T12:00:00+09:00'):new Date(),min=new Date(ref.getTime()-7*86400000),base=posts.filter(p=>{let d=new Date(p.date+'T12:00:00+09:00');let agency=agencies.find(a=>a.name===p.agency);return d>=min&&d<=ref&&(agency?.level==='장관급'||agency?.level==='차관급')});[['likeTop','likes'],['viewTop','views'],['commentTop','comments']].forEach(([id,metric])=>{let values=base.filter(p=>(metric!=='views'||p.type==='VIDEO')&&(metric!=='comments'||commentMode==='all'||!String(p.caption||'').includes('이벤트'))).sort((a,b)=>Number(b[metric]||0)-Number(a[metric]||0)).slice(0,10);$(id).innerHTML=values.length?values.map((p,i)=>`<div class="popular-row"><span style="color:#9aa4b7;font-size:11px;font-weight:800;width:13px">${i+1}</span><span class="thumb">${p.thumbnail?`<img src="${safe(p.thumbnail)}" alt="" loading="lazy" onerror="this.remove()">`:p.type==='VIDEO'?'▷':'▧'}</span><div class="popular-info"><div class="popular-agency">${safe(p.agency)}</div><div class="popular-caption">${p.permalink?`<a class="link" href="${safe(p.permalink)}" target="_blank" rel="noopener noreferrer">${safe(p.caption)}</a>`:safe(p.caption)}</div><div class="popular-metric">${fmt(p[metric])}${metric==='views'?'회':'개'}</div></div></div>`).join(''):'<div class="empty">해당 기간 게시물이 없습니다.</div>'})}
function setupAgencies(){let sel=$('agency'),prev=sel.value;sel.innerHTML='<option value="">전체 기관</option>'+agencies.slice().sort((a,b)=>a.name.localeCompare(b.name,'ko')).map(a=>`<option value="${safe(a.name)}">${safe(a.name)}</option>`).join('');sel.value=prev}
function filtered(){let agency=$('agency').value,level=$('level').value,format=$('format').value,order=$('order').value,from=$('from').value,to=$('to').value,likes=$('minLikes').value,views=$('minViews').value,comments=$('minComments').value;return posts.filter(p=>
  (!$('keyword').value.trim() ||
   String(p.caption||'').toLowerCase().includes($('keyword').value.trim().toLowerCase())) &&
  (!agency||p.agency===agency)&&(!level||p.level===level)&&(!format||p.type===format)&&
($('eventFilter').value==='all'||($('eventFilter').value==='exclude'?!String(p.caption||'').includes('이벤트'):String(p.caption||'').includes('이벤트')))&&(!from||p.date>=from)&&(!to||p.date<=to)&&(!likes||p.likes>=Number(likes))&&(!views||(p.type==='VIDEO'&&p.views!=null&&Number(p.views)>=Number(views)))&&(!comments||p.comments>=Number(comments))).sort((a,b)=>order==='recent'?b.date.localeCompare(a.date)||String(b.id).localeCompare(String(a.id)):Number(b[order==='likes'?'likes':order==='views'?'views':'comments']||0)-Number(a[order==='likes'?'likes':order==='views'?'views':'comments']||0)||b.date.localeCompare(a.date))}
function renderTable(){
  const data=filtered();
  renderAgencyComparison();$('resultCount').textContent=`검색 결과 ${num(data.length)}개${demo?' · 데모 데이터':''}`;$('postRows').innerHTML=data.length?data.slice(0,shownPosts).map(p=>`<tr><td><strong>${safe(p.agency)}</strong></td><td><span class="badge">${safe(p.level)}</span></td><td style="white-space:nowrap">${safe(p.date)}</td><td><span class="table-thumb">${p.thumbnail?`<img src="${safe(p.thumbnail)}" alt="" width="48" height="48" style="object-fit:cover;border-radius:8px" loading="lazy" onerror="this.remove()">`:p.type==='VIDEO'?'▷':'▧'}</span></td><td class="post"><div class="clip" title="${safe(p.caption)}">${safe(p.caption)}</div><div style="color:#939db0;font-size:11px;margin-top:3px">${formatLabel(p.type)}</div></td><td>${p.type==='VIDEO'?fmt(p.views):'<span class="blank">—</span>'}</td><td>${num(p.likes)}</td><td>${num(p.comments)}</td><td>${p.permalink?`<a class="link" href="${safe(p.permalink)}" target="_blank" rel="noopener noreferrer">보기 ↗</a>`:'<span class="blank">—</span>'}</td></tr>`).join(''):'<tr><td colspan="9"><div class="empty">조건에 맞는 게시물이 없습니다.</div></td></tr>';if(postView==='feed')renderFeed(data);$('postMore').hidden=data.length<=shownPosts;$('postMore').textContent='더보기 +5'}
// 추가 미디어가 제공되는 게시물은 화면 안에서 바로 넘기거나 재생합니다.
const mediaState={};
function mediaItems(p){
 const children=Array.isArray(p.images)&&p.images.length?p.images:Array.isArray(p.children)?p.children:[];
 if(p.type==='CAROUSEL_ALBUM'&&children.length){
  return children.map(c=>typeof c==='string'?{url:c,type:'IMAGE'}:{url:c.media_url||c.url||c.thumbnail_url||'',type:c.media_type||c.type||'IMAGE',poster:c.thumbnail_url||''}).filter(x=>x.url);
 }
 const url=p.type==='VIDEO'?(p.video_url||p.media_url||p.thumbnail):p.media_url||p.thumbnail;
 return url?[{url,type:p.type==='VIDEO'&&Boolean(p.video_url||p.media_url)?'VIDEO':'IMAGE',poster:p.thumbnail}]:[];
}
function mediaHtml(p){
 const items=mediaItems(p),index=Math.min(mediaState[p.id]||0,Math.max(0,items.length-1)),item=items[index];
 if(!item)return `<div class="feed-placeholder">미디어를 불러올 수 없습니다.${p.permalink?' 아래 원문에서 확인해 주세요.':''}</div>`;
 const url=safe(item.url),poster=safe(item.poster||p.thumbnail||'');
 const media=item.type==='VIDEO'?`<video controls preload="none" playsinline ${poster?`poster="${poster}"`:''} src="${url}">이 브라우저에서 동영상 재생을 지원하지 않습니다.</video>`:`<img src="${url}" loading="lazy" alt="${safe(p.agency)} 게시물 이미지" onerror="this.style.display='none';this.parentElement.insertAdjacentHTML('beforeend','<div class=&quot;feed-placeholder&quot;>이미지를 불러올 수 없습니다. 원문에서 확인해 주세요.</div>')">`;
 const arrows=items.length>1?`<div class="feed-arrows"><button type="button" data-media-id="${safe(p.id)}" data-dir="-1" aria-label="이전 장">‹</button><button type="button" data-media-id="${safe(p.id)}" data-dir="1" aria-label="다음 장">›</button></div><span class="feed-page">${index+1} / ${items.length}</span>`:'';
 return media+arrows;
}
function renderFeed(data){
 $('feedViewPanel').innerHTML=data.length?data.slice(0,shownPosts).map(p=>`<article class="feed-card"><div class="feed-head"><div><strong>${safe(p.agency)}</strong><div class="feed-meta">${safe(p.date)} · ${safe(formatLabel(p.type))}</div></div><span class="badge">${safe(p.level)}</span></div><div class="feed-media">${mediaHtml(p)}</div><div class="feed-details"><div class="feed-stats"><span>♥ 좋아요 ${num(p.likes)}</span><span>▤ 댓글 ${num(p.comments)}</span>${p.type==='VIDEO'?`<span>▷ 조회수 ${fmt(p.views)}</span>`:''}</div><div class="feed-caption">${safe(p.caption)}</div>${p.permalink?`<a class="feed-link" target="_blank" rel="noopener noreferrer" href="${safe(p.permalink)}">인스타그램 원문 보기 ↗</a>`:''}${p.type==='CAROUSEL_ALBUM'&&mediaItems(p).length<=1?'<div class="feed-meta">※ 카드뉴스의 전체 장면을 보려면 추가 미디어 수집이 필요합니다.</div>':''}${p.type==='VIDEO'&&!p.video_url&&!p.media_url?'<div class="feed-meta">※ 영상 재생 주소가 수집되지 않아 원문에서 재생해야 합니다.</div>':''}</div></article>`).join(''):'<div class="empty">조건에 맞는 게시물이 없습니다.</div>';
}
function setPostView(view){postView=view;$('tableViewPanel').hidden=view!=='table';$('feedViewPanel').hidden=view!=='feed';['table','feed'].forEach(v=>{const active=v===view;$(v+'View').classList.toggle('active',active);$(v+'View').setAttribute('aria-pressed',String(active))});renderTable()}
function setCommentMode(mode){commentMode=mode;['commentAll','commentNoEvent'].forEach((id,i)=>{const active=(i===0)===(mode==='all');$(id).classList.toggle('active',active);$(id).setAttribute('aria-pressed',String(active))});renderPopular()}
function exportExcel(){const data=filtered();if(!data.length){alert('다운로드할 게시물이 없습니다.');return}const header=['기관','구분','게시일','콘텐츠 유형','게시물 내용','조회수','좋아요','댓글','원문 링크'];const rows=data.map(p=>[p.agency,p.level,p.date,formatLabel(p.type),p.caption,p.type==='VIDEO'&&p.views!=null?p.views:'',p.likes,p.comments,p.permalink]);const filename=`instagram_monitor_${new Date().toISOString().slice(0,10)}${demo?'_DEMO':''}`;if(window.XLSX){const ws=XLSX.utils.aoa_to_sheet([header,...rows]);ws['!cols']=[{wch:24},{wch:10},{wch:13},{wch:15},{wch:75},{wch:13},{wch:13},{wch:13},{wch:52}];const wb=XLSX.utils.book_new();XLSX.utils.book_append_sheet(wb,ws,'게시물');XLSX.writeFile(wb,filename+'.xlsx');return}let csv='\ufeff'+[header,...rows].map(row=>row.map(cell=>'"'+String(cell??'').replace(/^[=+@\-\t\r]/,'\'$&').replace(/"/g,'""')+'"').join(',')).join('\r\n');const link=document.createElement('a');link.href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8;'}));link.download=filename+'.csv';link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);alert('엑셀 라이브러리를 불러오지 못해 엑셀에서 열 수 있는 CSV 파일로 저장했습니다.')}
function exportAgencyComparison() {
  const data = agencyComparisonExportRows;

  if (!data.length) {
    alert('다운로드할 기관별 비교 데이터가 없습니다.');
    return;
  }

  const header = [
    '기관', '게시물 수',
    '좋아요 합계', '평균 좋아요', '최대 좋아요',
    '댓글 합계', '평균 댓글', '최대 댓글',
    '영상 조회수 합계', '영상 평균 조회수', '영상 최대 조회수'
  ];

  const rows = data.map(([name, g]) => [
    name,
    g.count,
    g.likes,
    Math.round(g.likes / g.count),
    g.maxLikes,
    g.comments,
    Math.round(g.comments / g.count),
    g.maxComments,
    g.videoCount ? g.videoViews : '',
    g.videoCount ? Math.round(g.videoViews / g.videoCount) : '',
    g.videoCount ? g.maxVideoViews : ''
  ]);

  const filename = `instagram_agency_comparison_${new Date().toISOString().slice(0,10)}`;

  if (window.XLSX) {
    const ws = XLSX.utils.aoa_to_sheet([header, ...rows]);
    ws['!cols'] = [{wch:25}, ...Array(10).fill({wch:18})];

    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '기관별 성과 비교');
    XLSX.writeFile(wb, filename + '.xlsx');
    return;
  }

  const csv = '\ufeff' + [header, ...rows]
    .map(row => row.map(cell =>
      '"' + String(cell ?? '')
        .replace(/^[=+@\-\t\r]/, "'$&")
        .replace(/"/g, '""') + '"'
    ).join(',')).join('\r\n');

  const link = document.createElement('a');
  link.href = URL.createObjectURL(
    new Blob([csv], {type:'text/csv;charset=utf-8;'})
  );
  link.download = filename + '.csv';
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}
function setupCompareAgencies() {
  const select = $('compareAgency');
  const selected = select.value;

  const level = $('compareLevel').value;

  const names = agencies
    .filter(a => !level || a.level === level)
    .map(a => a.name)
    .sort((a, b) => a.localeCompare(b, 'ko'));

  select.innerHTML =
    '<option value="">전체 기관</option>' +
    names.map(name =>
      `<option value="${safe(name)}">${safe(name)}</option>`
    ).join('');

  select.value = names.includes(selected) ? selected : '';
}
let agencyComparisonExportRows = [];
let compareSortKey = 'count';
let compareSortDirection = 'desc';
document.querySelectorAll('#comparePeriodButtons button').forEach(button => {
  button.addEventListener('click', () => {
    const days = button.dataset.days;

    document.querySelectorAll('#comparePeriodButtons button').forEach(b => {
      b.classList.toggle('active', b === button);
    });

    if (days === 'all') {
      $('compareFrom').value = '2026-01-01';
      $('compareTo').value = '2026-12-31';
    } else {
      const today = new Date();
      const start = new Date(today);
      start.setDate(today.getDate() - Number(days) + 1);

      const localDate = d =>
        `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

      $('compareFrom').value = localDate(start);
      $('compareTo').value = localDate(today);
    }

    renderAgencyComparison();
  });
});  
['compareFrom', 'compareTo'].forEach(id => {
  $(id).addEventListener('change', () => {
    document.querySelectorAll('#comparePeriodButtons button').forEach(button => {
      button.classList.remove('active');
    });
  });
});
function renderAgencyComparison() {
  const level = $('compareLevel').value;
  const agency = $('compareAgency').value;
  const eventMode = $('compareEvent').value;
  const from = $('compareFrom').value;
  const to = $('compareTo').value;

  // 게시물 검색 필터와 독립적으로 비교합니다.
  const data = posts.filter(p => {
    const isEvent = String(p.caption || '').includes('이벤트');

    return (!level || p.level === level)
      && (!agency || p.agency === agency)
      && (eventMode === 'all'
        || (eventMode === 'exclude' && !isEvent)
        || (eventMode === 'only' && isEvent))
      && (!from || p.date >= from)
      && (!to || p.date <= to);
  });

  const groups = {};

  data.forEach(p => {
    if (!groups[p.agency]) {
      groups[p.agency] = {
        count: 0,
        likes: 0,
        maxLikes: 0,
        comments: 0,
        maxComments: 0,
        videoViews: 0,
        maxVideoViews: 0,
        videoCount: 0
      };
    }

    const g = groups[p.agency];

    g.count++;
    g.likes += Number(p.likes || 0);
    g.maxLikes = Math.max(g.maxLikes, Number(p.likes || 0));

    g.comments += Number(p.comments || 0);
    g.maxComments = Math.max(g.maxComments, Number(p.comments || 0));

    if (p.type === 'VIDEO' && p.views != null) {
      const views = Number(p.views);
      g.videoViews += views;
      g.maxVideoViews = Math.max(g.maxVideoViews, views);
      g.videoCount++;
    }
  });

const getSortValue = g => {
  switch (compareSortKey) {
    case 'avgLikes':
      return g.likes / g.count;
    case 'avgComments':
      return g.comments / g.count;
    case 'avgVideoViews':
      return g.videoCount ? g.videoViews / g.videoCount : -1;
    default:
      return g[compareSortKey] ?? 0;
  }
};

const rows = Object.entries(groups).sort((a, b) => {
  const difference = getSortValue(a[1]) - getSortValue(b[1]);

  return compareSortDirection === 'desc'
    ? -difference
    : difference;
});
  agencyComparisonExportRows = rows;
  
  $('agencyComparisonRows').innerHTML = rows.length
    ? rows.map(([name, g]) => `
      <tr>
        <td><strong>${safe(name)}</strong></td>
        <td>${num(g.count)}개</td>
        <td>${num(g.likes)}개</td>
        <td>${num(Math.round(g.likes / g.count))}개</td>
        <td>${num(g.maxLikes)}개</td>
        <td>${num(g.comments)}개</td>
        <td>${num(Math.round(g.comments / g.count))}개</td>
        <td>${num(g.maxComments)}개</td>
        <td>${g.videoCount ? num(g.videoViews) + '회' : '—'}</td>
        <td>${g.videoCount
          ? num(Math.round(g.videoViews / g.videoCount)) + '회'
          : '—'}</td>
        <td>${g.videoCount ? num(g.maxVideoViews) + '회' : '—'}</td>
      </tr>
    `).join('')
    : '<tr><td colspan="11"><div class="empty">조건에 맞는 게시물이 없습니다.</div></td></tr>';
}
$('compareLevel').addEventListener('change', () => {
  setupCompareAgencies();
  renderAgencyComparison();
});
['compareAgency', 'compareEvent', 'compareFrom', 'compareTo'].forEach(id => {
  $(id).addEventListener('change', () => {
    renderAgencyComparison();
  });
});
document.querySelectorAll('.compare-sort').forEach(button => {
  button.addEventListener('click', () => {
    const key = button.dataset.sort;

    if (compareSortKey === key) {
      compareSortDirection =
        compareSortDirection === 'desc' ? 'asc' : 'desc';
    } else {
      compareSortKey = key;
      compareSortDirection = 'desc';
    }

    renderAgencyComparison();
  });
});
document.querySelectorAll('#postPeriodButtons button').forEach(button => {
  button.addEventListener('click', () => {
    const days = button.dataset.days;

document.querySelectorAll('#postPeriodButtons button').forEach(b => {
  b.classList.toggle('active', b === button);
});
    
    if (days === 'all') {
      $('from').value = '2026-01-01';
      $('to').value = '2026-12-31';
    } else {
      const today = new Date();
      const start = new Date(today);
      start.setDate(today.getDate() - Number(days) + 1);

      const localDate = d =>
        `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

      $('from').value = localDate(start);
      $('to').value = localDate(today);
    }

    shownPosts = 5;
    renderTable();
  });
});
['from', 'to'].forEach(id => {
  $(id).addEventListener('change', () => {
    document.querySelectorAll('#postPeriodButtons button').forEach(b => {
      b.classList.remove('active');
    });
  });
});
function renderAll(){
  renderKpis();
  renderRank('minister','장관급','ministerRanks','ministerMore');
  renderRank('vice','차관급','viceRanks','viceMore');
  renderPopular();
  setupAgencies();
  setupCompareAgencies();
  renderTable();
}
['keyword','agency','level','format','eventFilter','order','from','to','minLikes','minViews','minComments'].forEach(id=>$(id).addEventListener(['minLikes','minViews','minComments'].includes(id)?'input':'change',()=>{shownPosts=5;renderTable()}));$('postMore').addEventListener('click',()=>{shownPosts+=5;renderTable()});$('reset').addEventListener('click',()=>{$('keyword').value='';
$('agency').value='';$('level').value='';$('format').value='';
$('eventFilter').value='all';$('order').value='recent';$('from').value='2026-01-01';$('to').value='2026-12-31';
document.querySelectorAll('#postPeriodButtons button').forEach(b => {
  b.classList.toggle('active', b.dataset.days === 'all');
});['minLikes','minViews','minComments'].forEach(id=>$(id).value='');shownPosts=5;renderTable()});$('excel').addEventListener('click',exportExcel);$('downloadAgencyComparison').addEventListener('click', exportAgencyComparison);$('commentAll').addEventListener('click',()=>setCommentMode('all'));$('commentNoEvent').addEventListener('click',()=>setCommentMode('noevent'));$('tableView').addEventListener('click',()=>setPostView('table'));$('feedView').addEventListener('click',()=>setPostView('feed'));$('feedViewPanel').addEventListener('click',e=>{const b=e.target.closest('button[data-media-id]');if(!b)return;const post=posts.find(p=>String(p.id)===b.dataset.mediaId);if(!post)return;const n=mediaItems(post).length;if(!n)return;mediaState[post.id]=((mediaState[post.id]||0)+Number(b.dataset.dir)+n)%n;renderFeed(filtered())});load();
