async function loadData() {
  const accountsRes = await fetch('data/accounts.json');
  const postsRes = await fetch('data/posts.json');

  const accounts = await accountsRes.json();
  const posts = await postsRes.json();

  renderSummary(accounts);
  renderTables(accounts);
  renderPosts(posts);
}

function numberFormat(num) {
  return num?.toLocaleString('ko-KR') || '-';
}

function renderSummary(accounts) {
  const totalFollowers = accounts.reduce((sum, item) => sum + (item.followers || 0), 0);
  const avgFollowers = accounts.length ? Math.round(totalFollowers / accounts.length) : 0;

  const ministers = accounts.filter(item => item.level === '장관급').sort((a, b) => b.followers - a.followers);
  const viceMinisters = accounts.filter(item => item.level === '차관급').sort((a, b) => b.followers - a.followers);

  document.getElementById('totalFollowers').textContent = numberFormat(totalFollowers);
  document.getElementById('avgFollowers').textContent = numberFormat(avgFollowers);
  document.getElementById('topMinister').textContent = ministers[0] ? `${ministers[0].agency} (${numberFormat(ministers[0].followers)})` : '-';
  document.getElementById('topViceMinister').textContent = viceMinisters[0] ? `${viceMinisters[0].agency} (${numberFormat(viceMinisters[0].followers)})` : '-';
}

function renderTables(accounts) {
  const ministerTable = document.getElementById('ministerTable');
  const viceMinisterTable = document.getElementById('viceMinisterTable');

  const ministers = accounts.filter(item => item.level === '장관급').sort((a, b) => b.followers - a.followers);
  const viceMinisters = accounts.filter(item => item.level === '차관급').sort((a, b) => b.followers - a.followers);

  ministerTable.innerHTML = ministers.map((item, index) => `
    <tr>
      <td>${index + 1}</td>
      <td>${item.agency}</td>
      <td>${numberFormat(item.followers)}</td>
    </tr>
  `).join('');

  viceMinisterTable.innerHTML = viceMinisters.map((item, index) => `
    <tr>
      <td>${index + 1}</td>
      <td>${item.agency}</td>
      <td>${numberFormat(item.followers)}</td>
    </tr>
  `).join('');
}

function renderPosts(posts) {
  const postGrid = document.getElementById('postGrid');

  postGrid.innerHTML = posts.map(post => `
    <div class="post-card">
      <img class="post-thumb" src="${post.thumbnail || 'https://via.placeholder.com/600x600?text=Instagram'}" alt="${post.agency}" />
      <div class="post-body">
        <h3>${post.agency}</h3>
        <div class="post-meta">${post.date} · ${post.type}</div>
        <div class="post-caption">${post.caption || ''}</div>
        <div class="post-stats">
          조회수: ${numberFormat(post.views)} · 좋아요: ${numberFormat(post.likes)} · 댓글: ${numberFormat(post.comments)}
        </div>
        <a class="post-link" href="${post.link}" target="_blank">게시물 보러가기</a>
      </div>
    </div>
  `).join('');
}

loadData();
