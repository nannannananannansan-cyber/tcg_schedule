let allEvents = [];

let selectedGame = "all";
let selectedArea = "all";
let keyword = "";


async function loadEvents() {
  const response = await fetch("../data/events.json");

  if (!response.ok) {
    throw new Error("大会データを取得できませんでした");
  }

  const data = await response.json();

  allEvents = data.events;

  render();
}


function render() {
  const events = getFilteredEvents();

  renderDateNav(events);
  renderEvents(events);
}


/* --------------------
   Filter
-------------------- */

function getFilteredEvents() {
  return allEvents.filter(event => {

    const gameMatched =
      selectedGame === "all" ||
      event.game === selectedGame;


    const areaMatched =
      selectedArea === "all" ||
      getArea(event.address) === selectedArea;


    const keywordMatched =
      matchesKeyword(event);


    return (
      gameMatched &&
      areaMatched &&
      keywordMatched
    );
  });
}


function matchesKeyword(event) {
  if (!keyword) {
    return true;
  }

  const searchTarget = [
    event.shop_name,
    event.event_name,
    event.address,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  return searchTarget.includes(keyword);
}


/* --------------------
   Area
-------------------- */

function getArea(address) {
  if (!address) {
    return "osaka-other";
  }

  const normalizedAddress = address
    .replace(/\s/g, "")
    .replace(/　/g, "");


  if (
    normalizedAddress.includes("浪速区日本橋") ||
    normalizedAddress.includes("浪速区難波") ||
    normalizedAddress.includes("中央区難波") ||
    normalizedAddress.includes("中央区難波千日前")
  ) {
    return "namba";
  }


  if (
    normalizedAddress.includes("西心斎橋") ||
    normalizedAddress.includes("東心斎橋") ||
    normalizedAddress.includes("心斎橋筋")
  ) {
    return "shinsaibashi";
  }


  if (
    normalizedAddress.includes("北区梅田") ||
    normalizedAddress.includes("北区芝田") ||
    normalizedAddress.includes("北区茶屋町") ||
    normalizedAddress.includes("北区曽根崎")
  ) {
    return "umeda";
  }


  if (
    normalizedAddress.includes("阿倍野区") ||
    normalizedAddress.includes("天王寺区")
  ) {
    return "tennoji";
  }


  if (
    normalizedAddress.includes("堺市")
  ) {
    return "sakai";
  }


  if (
    normalizedAddress.includes("東大阪市") ||
    normalizedAddress.includes("八尾市")
  ) {
    return "higashiosaka-yao";
  }


  if (
    normalizedAddress.includes("豊中市") ||
    normalizedAddress.includes("吹田市") ||
    normalizedAddress.includes("高槻市") ||
    normalizedAddress.includes("茨木市") ||
    normalizedAddress.includes("箕面市") ||
    normalizedAddress.includes("池田市") ||
    normalizedAddress.includes("摂津市")
  ) {
    return "hokusetsu";
  }


  if (
    normalizedAddress.includes("大阪市")
  ) {
    return "osaka-city-other";
  }


  return "osaka-other";
}


/* --------------------
   Events
-------------------- */

function renderEvents(events) {
  const container =
    document.getElementById("events");

  const summary =
    document.getElementById("summary");


  summary.textContent =
    `${events.length}件の大会`;


  container.innerHTML = "";


  if (events.length === 0) {
    container.innerHTML = `
      <div class="empty">
        条件に一致する大会がありません
      </div>
    `;

    return;
  }


  const grouped =
    groupByDate(events);


  for (
    const [date, dateEvents]
    of Object.entries(grouped)
  ) {
    const section =
      document.createElement("section");

    section.className =
      "date-group";

    section.id =
      createDateSectionId(date);


    const title =
      document.createElement("h2");

    title.className =
      "date-title";

    title.innerHTML = `
      <span class="date-title-main">
        ${formatDate(date)}
      </span>

      <span class="date-title-count">
        ${dateEvents.length}件
      </span>
    `;


    section.appendChild(title);


    for (const event of dateEvents) {
      section.appendChild(
        createEventCard(event)
      );
    }


    container.appendChild(section);
  }
}


/* --------------------
   Date navigation
-------------------- */

function renderDateNav(events) {
  const container =
    document.getElementById("date-nav");

  container.innerHTML = "";


  const grouped =
    groupByDate(events);

  const dates =
    Object.keys(grouped);


  for (const date of dates) {
    const button =
      document.createElement("button");

    button.className =
      "date-button";

    button.innerHTML = `
      <span class="date-button-label">
        ${getRelativeDateLabel(date)}
      </span>

      <span class="date-button-date">
        ${formatShortDate(date)}
      </span>
    `;


    button.addEventListener(
      "click",
      () => {
        const section =
          document.getElementById(
            createDateSectionId(date)
          );

        if (!section) {
          return;
        }

        section.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
    );


    container.appendChild(button);
  }
}


function groupByDate(events) {
  const groups = {};

  for (const event of events) {
    if (!groups[event.date]) {
      groups[event.date] = [];
    }

    groups[event.date].push(event);
  }

  return groups;
}


/* --------------------
   Event card
-------------------- */

function createEventCard(event) {
  const card =
    document.createElement("div");

  card.className =
    "event-card";


  const gameName =
    event.game === "pokemon"
      ? "ポケモン"
      : "ロルカナ";


  const meta = [];


  if (event.entry_fee) {
    meta.push(
      escapeHtml(event.entry_fee)
    );
  }


  if (event.capacity) {
    meta.push(
      `定員 ${event.capacity}名`
    );
  }


  if (event.regulation) {
    meta.push(
      escapeHtml(event.regulation)
    );
  }


  if (event.full) {
    meta.push(
      `<span class="full">満員</span>`
    );
  }


  if (event.cancelled) {
    meta.push(
      `<span class="full">中止</span>`
    );
  }


  const sourceLink =
    event.source_url
      ? `
        <a
          class="source-link"
          href="${escapeHtml(event.source_url)}"
          target="_blank"
          rel="noopener noreferrer"
        >
          公式で見る ↗
        </a>
      `
      : "";


  card.innerHTML = `
    <div class="event-time">
      ${escapeHtml(event.start_time)}
    </div>

    <div class="event-content">

      <div class="event-top">

        <div
          class="game-badge game-${event.game}"
        >
          ${gameName}
        </div>

        ${sourceLink}

      </div>

      <div class="shop-name">
        ${escapeHtml(event.shop_name)}
      </div>

      <div class="event-name">
        ${escapeHtml(event.event_name)}
      </div>

      <div class="event-meta">

        ${meta
          .map(
            item =>
              `<span>${item}</span>`
          )
          .join("")}

      </div>

    </div>
  `;


  return card;
}


/* --------------------
   Date
-------------------- */

function formatDate(dateString) {
  const date =
    createLocalDate(dateString);

  return new Intl.DateTimeFormat(
    "ja-JP",
    {
      month: "numeric",
      day: "numeric",
      weekday: "short",
    }
  ).format(date);
}


function formatShortDate(dateString) {
  const date =
    createLocalDate(dateString);

  return new Intl.DateTimeFormat(
    "ja-JP",
    {
      month: "numeric",
      day: "numeric",
    }
  ).format(date);
}


function getRelativeDateLabel(dateString) {
  const target =
    createLocalDate(dateString);

  const today =
    new Date();

  today.setHours(0, 0, 0, 0);


  const diff =
    Math.round(
      (
        target.getTime() -
        today.getTime()
      ) /
      (
        1000 *
        60 *
        60 *
        24
      )
    );


  if (diff === 0) {
    return "今日";
  }

  if (diff === 1) {
    return "明日";
  }


  return new Intl.DateTimeFormat(
    "ja-JP",
    {
      weekday: "short",
    }
  ).format(target);
}


function createLocalDate(dateString) {
  const [
    year,
    month,
    day
  ] =
    dateString
      .split("-")
      .map(Number);


  return new Date(
    year,
    month - 1,
    day
  );
}


function createDateSectionId(date) {
  return `date-${date}`;
}


/* --------------------
   Escape
-------------------- */

function escapeHtml(value) {
  const div =
    document.createElement("div");

  div.textContent =
    value ?? "";

  return div.innerHTML;
}


/* --------------------
   Game filter
-------------------- */

document
  .querySelectorAll(
    "#game-filters .filter"
  )
  .forEach(button => {

    button.addEventListener(
      "click",
      () => {

        document
          .querySelectorAll(
            "#game-filters .filter"
          )
          .forEach(button => {
            button.classList.remove(
              "active"
            );
          });


        button.classList.add(
          "active"
        );


        selectedGame =
          button.dataset.game;


        render();
      }
    );
  });


/* --------------------
   Area filter
-------------------- */

document
  .getElementById("area-filter")
  .addEventListener(
    "change",
    event => {

      selectedArea =
        event.target.value;

      render();
    }
  );


/* --------------------
   Keyword filter
-------------------- */

document
  .getElementById("keyword-filter")
  .addEventListener(
    "input",
    event => {

      keyword =
        event.target.value
          .trim()
          .toLowerCase();

      render();
    }
  );


/* --------------------
   Start
-------------------- */

loadEvents().catch(error => {
  console.error(error);

  document.getElementById(
    "events"
  ).textContent =
    "大会データの読み込みに失敗しました。";
});