// 프로젝트를 추가하려면 이 배열에 항목을 더하세요.
// link 가 있으면 "데모 실행" 링크가 표시되고, 없으면 note 가 표시됩니다.
const PROJECTS = [
  {
    title: "Snake: You vs AI",
    description: "사람과 AI 뱀이 사과를 두고 경쟁하는 게임. AI는 최단 경로 탐색과 안전 공간 판단으로 움직입니다.",
    tech: ["Python", "tkinter"],
    note: "Python 데스크톱 앱 · 로컬에서 python snake.py 로 실행",
  },
  {
    title: "Tetris",
    description: "고스트 블록, 레벨, 더블탭 빠른 낙하를 지원하는 브라우저 테트리스.",
    tech: ["HTML5", "CSS3", "JavaScript"],
    link: "../game02/tetris.html",
  },
];

(function () {
  const $ = (sel) => document.querySelector(sel);

  // Projects
  const grid = $("#projectGrid");
  PROJECTS.forEach((p) => {
    const card = document.createElement("article");
    card.className = "card";

    const h3 = document.createElement("h3");
    h3.textContent = p.title;

    const desc = document.createElement("p");
    desc.textContent = p.description;

    const tags = document.createElement("ul");
    tags.className = "tags";
    p.tech.forEach((t) => {
      const li = document.createElement("li");
      li.textContent = t;
      tags.appendChild(li);
    });

    card.append(h3, desc, tags);

    if (p.link) {
      const a = document.createElement("a");
      a.className = "card-link";
      a.href = p.link;
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = "데모 실행 →";
      card.appendChild(a);
    } else if (p.note) {
      const note = document.createElement("span");
      note.className = "card-note";
      note.textContent = p.note;
      card.appendChild(note);
    }
    grid.appendChild(card);
  });

  // Mobile menu
  const toggle = $("#navToggle");
  const menu = $("#navMenu");
  function setMenu(open) {
    menu.classList.toggle("open", open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "메뉴 닫기" : "메뉴 열기");
  }
  toggle.addEventListener("click", () => setMenu(!menu.classList.contains("open")));
  menu.addEventListener("click", (e) => { if (e.target.closest("a")) setMenu(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") setMenu(false); });

  // Highlight current section in nav
  const links = [...menu.querySelectorAll("a")];
  const sections = links.map((a) => document.querySelector(a.getAttribute("href")));
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        links.forEach((a) =>
          a.classList.toggle("active", a.getAttribute("href") === "#" + entry.target.id)
        );
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    sections.forEach((s) => s && io.observe(s));
  }

  // Copy email
  const status = $("#copyStatus");
  $("#copyBtn").addEventListener("click", async () => {
    const email = $("#emailText").textContent.trim();
    try {
      await navigator.clipboard.writeText(email);
      status.textContent = "이메일 주소를 복사했습니다.";
    } catch {
      status.textContent = "복사에 실패했습니다. 주소를 직접 선택해 복사해 주세요.";
    }
    setTimeout(() => (status.textContent = ""), 2500);
  });

  $("#year").textContent = new Date().getFullYear();
})();
