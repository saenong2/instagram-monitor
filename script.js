async function loadData() {
  try {
    const [accountsRes, postsRes] = await Promise.all([
      fetch("./data/accounts.json"),
      fetch("./data/posts.json"),
    ]);

    const accounts = await accountsRes.json();
    const posts = await postsRes.json();

    renderDashboard(accounts);
    renderPosts(posts);
  } catch (error) {
    console.error("데이터 로딩 실패:", error);
  }
}

function numberFormat(num) {
  if (num === null || num === undefined || isNaN(num)) return "-";
  return Number(num).toLocaleString("ko-KR");
}

function renderDashboard(accounts) {
  const ministerAccounts = accounts
    .filter((a) => a.level === "장관급")
    .sort((a, b) => b.followers - a.followers);

  const viceAccounts = accounts
    .filter((a) => a.level === "차관급")
    .sort((a, b) => b.followers - a.followers);

  const totalFollowers = accounts.reduce((sum, a) => sum + (a.followers || 0), 0);
  const avgFollowers = accounts.length ? Math.round(totalFollowers / accounts.length) : 0;

  document.getElementById("totalFollowers").textContent = numberFormat(totalFollowers);
  document.getElementById("topMinister").textContent = ministerAccounts.length
    ? `${ministerAccounts[0].agency} (${numberFormat(ministerAccounts[0].followers)})`
    : "-";
  document.getElementById("topVice").textContent = viceAccounts.length
    ? `${viceAccounts[0].agency} (${numberFormat(viceAccounts[0].followers)})`
    : "-";
  document.getElementById("avgFollowers").textContent = numberFormat(avgFollowers);

  renderRankingTable("ministerRanking", ministerAccounts);
  renderRankingTable("viceRanking", viceAccounts);
}

function renderRankingTable(targetId, data) {
  const tbody = document.getElementById(targetId);
  if (!tbody) return;

  tbody.innerHTML = "";

  data.forEach((item, index) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td>${item.agency}</td>
      <td>${numberFormat(item.followers)}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderPosts(posts) {
  const container = document.getElementById("postsContainer");
  if (!container) return;

  container.innerHTML = "";

  if (!posts || posts.length === 0) {
    container.innerHTML = `<p style="color:#666;">표시할 콘텐츠가 없습니다.</p>`;
    return;
  }

  posts
    .sort((a, b) => new Date(b.date) - new Date(a.date))
    .forEach((post) => {
      const card = document.createElement("div");
      card.className = "post-card";

      card.innerHTML = `
        <div class="post-thumb">
          ${
            post.thumbnail
              ? `<img src="${post.thumbnail}" alt="${post.agency}" onerror="this.style.display='none'; this.parentElement.innerHTML='썸네일 없음';">`
              : "썸네일 없음"
          }
        </div>
        <div class="post-body">
          <h3>${post.agency}</h3>
          <p class="meta">${post.date} · ${post.type}</p>
          <p class="caption">${post.caption || "-"}</p>
          <p class="stats">
            조회수: ${numberFormat(post.views)} · 좋아요: ${numberFormat(post.likes)} · 댓글: ${numberFormat(post.comments)}
          </p>
          <a href="${post.link}" target="_blank" class="view-btn">게시물 보러가기</a>
        </div>
      `;

      container.appendChild(card);
    });
}

loadData();
