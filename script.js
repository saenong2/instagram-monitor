async function loadData() {
  try {
    const accountsRes = await fetch("./data/accounts.json");
    const postsRes = await fetch("./data/posts.json");

    if (!accountsRes.ok) {
      throw new Error(`accounts.json 불러오기 실패: ${accountsRes.status}`);
    }

    if (!postsRes.ok) {
      throw new Error(`posts.json 불러오기 실패: ${postsRes.status}`);
    }

    const accounts = await accountsRes.json();
    const posts = await postsRes.json();

    renderSummary(accounts);
    renderTables(accounts);
    renderPosts(posts);
  } catch (error) {
    console.error("데이터 로딩 오류:", error);

    document.getElementById("totalFollowers").textContent = "오류";
    document.getElementById("topMinister").textContent = "오류";
    document.getElementById("topViceMinister").textContent = "오류";
    document.getElementById("avgFollowers").textContent = "오류";

    document.getElementById("ministerTable").innerHTML =
      `<tr><td colspan="3">데이터를 불러오지 못했습니다.</td></tr>`;

    document.getElementById("viceMinisterTable").innerHTML =
      `<tr><td colspan="3">데이터를 불러오지 못했습니다.</td></tr>`;

    document.getElementById("postGrid").innerHTML =
      `<div class="card">콘텐츠 데이터를 불러오지 못했습니다.<br>${error.message}</div>`;
  }
}

function numberFormat(num) {
  if (num === null || num === undefined || num === "") return "-";
  const n = Number(num);
  return Number.isNaN(n) ? "-" : n.toLocaleString("ko-KR");
}

function renderSummary(accounts) {
  const totalFollowers = accounts.reduce((sum, item) => sum + (item.followers || 0), 0);
  const avgFollowers = accounts.length ? Math.round(totalFollowers / accounts.length) : 0;

  const ministers = accounts
    .filter((item) => item.level === "장관급")
    .sort((a, b) => (b.followers || 0) - (a.followers || 0));

  const viceMinisters = accounts
    .filter((item) => item.level === "차관급")
    .sort((a, b) => (b.followers || 0) - (a.followers || 0));

  document.getElementById("totalFollowers").textContent = numberFormat(totalFollowers);
  document.getElementById("avgFollowers").textContent = numberFormat(avgFollowers);

  document.getElementById("topMinister").textContent = ministers[0]
    ? `${ministers[0].agency} (${numberFormat(ministers[0].followers)})`
    : "-";

  document.getElementById("topViceMinister").textContent = viceMinisters[0]
    ? `${viceMinisters[0].agency} (${numberFormat(viceMinisters[0].followers)})`
    : "-";
}

function renderTables(accounts) {
  const ministerTable = document.getElementById("ministerTable");
  const viceMinisterTable = document.getElementById("viceMinisterTable");

  const ministers = accounts
    .filter((item) => item.level === "장관급")
    .sort((a, b) => (b.followers || 0) - (a.followers || 0));

  const viceMinisters = accounts
    .filter((item) => item.level === "차관급")
    .sort((a, b) => (b.followers || 0) - (a.followers || 0));

  ministerTable.innerHTML = ministers
    .map(
      (item, index) => `
      <tr>
        <td>${index + 1}</td>
        <td>${item.agency}</td>
        <td>${numberFormat(item.followers)}</td>
      </tr>
    `
    )
    .join("");

  viceMinisterTable.innerHTML = viceMinisters
    .map(
      (item, index) => `
      <tr>
        <td>${index + 1}</td>
        <td>${item.agency}</td>
        <td>${numberFormat(item.followers)}</td>
      </tr>
    `
    )
    .join("");
}

function renderPosts(posts) {
  const postGrid = document.getElementById("postGrid");

  if (!posts || posts.length === 0) {
    postGrid.innerHTML = `<div class="card">표시할 콘텐츠가 없습니다.</div>`;
    return;
  }

  const sortedPosts = [...posts].sort((a, b) => {
    return new Date(b.date) - new Date(a.date);
  });

  postGrid.innerHTML = sortedPosts
    .map(
      (post) => `
      <div class="post-card">
        ${
          post.thumbnail
            ? `<img class="post-thumb" src="${post.thumbnail}" alt="${post.agency}" onerror="this.outerHTML='<div class=&quot;post-thumb placeholder-thumb&quot;>썸네일 없음</div>'" />`
            : `<div class="post-thumb placeholder-thumb">썸네일 없음</div>`
        }
        <div class="post-body">
          <h3>${post.agency}</h3>
          <div class="post-meta">${post.date || "-"} · ${post.type || "-"}</div>
          <div class="post-caption">${post.caption || "-"}</div>
          <div class="post-stats">
            조회수: ${numberFormat(post.views)} · 좋아요: ${numberFormat(post.likes)} · 댓글: ${numberFormat(post.comments)}
          </div>
          <a class="post-link" href="${post.link || "#"}" target="_blank" rel="noopener noreferrer">게시물 보러가기</a>
        </div>
      </div>
    `
    )
    .join("");
}

loadData();
