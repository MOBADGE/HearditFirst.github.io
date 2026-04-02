const CATEGORY_ORDER = ["tech", "world", "health", "gaming"];

const BIAS_REPLACEMENTS = [
  [/\bbrutal\b/gi, "significant"],
  [/\bchaotic\b/gi, "disruptive"],
  [/\bdevastate(?:s|d)?\b/gi, "damage"],
  [/\bviolent\b/gi, "severe"],
  [/\balarming\b/gi, "notable"],
  [/\bpunishing\b/gi, "sustained"],
  [/\bbreakthrough\b/gi, "development"],
  [/\btransform\b/gi, "change"],
  [/\bsurge\b/gi, "increase"],
  [/\bcrack down\b/gi, "increase oversight"],
  [/\bracing\b/gi, "preparing"],
  [/\bmounting fears\b/gi, "growing concern"],
  [/\bhigh-stakes\b/gi, "ongoing"],
  [/\bteeter\b/gi, "continue"],
  [/\bbattle over\b/gi, "discuss"],
  [/\bcelebrate\b/gi, "report"],
];

const fallbackData = {
  site: {
    name: "A Little Birdy Told Me",
    domain: "alittlebirdy.org",
  },
  generatedAt: null,
  categories: {
    tech: {
      label: "Tech desk",
      overview: "Current tech coverage centers on AI oversight, security posture reviews, and semiconductor supply resilience.",
      items: [
        {
          title: "Chipmakers increase backup capacity after a key fabrication slowdown",
          sourceLine: "Industry leaders scramble after a brutal fabrication setback raises fears of a global device shortage.",
          facts: "Several manufacturers reported slower output at a major facility and said contingency production lines are being activated while partners review delivery schedules.",
          urgency: "Monitoring",
          updated: "12 min ago",
          tags: ["Supply chain", "Semiconductors", "Manufacturing"],
          source: "Reuters",
          link: "#",
        },
        {
          title: "New AI disclosure rules move toward enforcement in several markets",
          sourceLine: "Governments crack down on opaque AI giants as pressure mounts for sweeping accountability.",
          facts: "Regulators in multiple regions released implementation timelines for labeling synthetic media and documenting high-risk model uses.",
          urgency: "Policy shift",
          updated: "35 min ago",
          tags: ["AI", "Regulation", "Compliance"],
          source: "AP",
          link: "#",
        },
        {
          title: "Cloud providers review security posture after coordinated intrusion reports",
          sourceLine: "A deeply alarming breach wave sends companies racing to contain fallout across the cloud.",
          facts: "Security teams are rotating credentials, reviewing tenant isolation logs, and advising customers to patch exposed integrations while incident scopes remain under review.",
          urgency: "Active review",
          updated: "51 min ago",
          tags: ["Cybersecurity", "Cloud", "Enterprise"],
          source: "The Verge",
          link: "#",
        },
      ],
    },
    world: {
      label: "World desk",
      overview: "World coverage is focused on transport disruptions, diplomatic negotiations, and recovery activity after severe weather events.",
      items: [
        {
          title: "Regional transport routes reopen in stages after overnight port disruption",
          sourceLine: "A chaotic port shutdown throws trade into turmoil and rattles nearby governments.",
          facts: "Authorities reopened selected freight corridors while cargo backlogs are assessed and shipping groups adjust schedules.",
          urgency: "Developing",
          updated: "18 min ago",
          tags: ["Trade", "Infrastructure", "Logistics"],
          source: "BBC",
          link: "#",
        },
        {
          title: "Diplomatic teams extend talks as negotiators refine ceasefire language",
          sourceLine: "Tense high-stakes talks teeter as rival camps battle over a fragile truce.",
          facts: "Mediators said draft language is still being revised, with aid access and monitoring mechanisms among the remaining issues.",
          urgency: "Negotiations",
          updated: "42 min ago",
          tags: ["Diplomacy", "Conflict", "Aid access"],
          source: "Reuters",
          link: "#",
        },
        {
          title: "Power restoration expands after severe weather damaged transmission lines",
          sourceLine: "Violent storms devastate communities and leave officials under intense pressure.",
          facts: "Utility crews reported gradual service restoration, while emergency shelters remain open in several districts and damage counts are still being updated.",
          urgency: "Recovery",
          updated: "1 hr ago",
          tags: ["Weather", "Energy", "Emergency response"],
          source: "AP",
          link: "#",
        },
      ],
    },
    health: {
      label: "Health desk",
      overview: "Health reporting is centered on hospital capacity, updated guidance for higher-risk groups, and new clinical trial readouts.",
      items: [
        {
          title: "Hospitals adjust staffing as respiratory admissions trend upward",
          sourceLine: "Doctors face an alarming surge as hospitals brace for another punishing wave.",
          facts: "Several systems increased overnight staffing, expanded triage guidance, and asked clinics to monitor bed use as respiratory cases rise.",
          urgency: "Capacity watch",
          updated: "16 min ago",
          tags: ["Hospitals", "Respiratory illness", "Capacity"],
          source: "BBC",
          link: "#",
        },
        {
          title: "Public health agencies update vaccine guidance for higher-risk groups",
          sourceLine: "Officials urgently push updated shots amid mounting fears of widespread complications.",
          facts: "The revised guidance prioritizes older adults and immunocompromised groups and includes timing recommendations for clinics and pharmacies.",
          urgency: "Guidance update",
          updated: "39 min ago",
          tags: ["Vaccines", "Public health", "Guidance"],
          source: "STAT",
          link: "#",
        },
        {
          title: "Clinical trial data shows improved response rates in targeted therapy study",
          sourceLine: "Researchers celebrate a breakthrough that could transform care for thousands overnight.",
          facts: "Early trial results showed higher response rates for a targeted therapy, though researchers said larger follow-up studies are still needed.",
          urgency: "Research",
          updated: "58 min ago",
          tags: ["Clinical trials", "Oncology", "Research"],
          source: "The New York Times",
          link: "#",
        },
      ],
    },
    gaming: {
      label: "Gaming desk",
      overview: "Gaming coverage is focused on platform changes, studio plans, release timing, and legal or policy shifts that affect players and developers.",
      items: [
        {
          title: "Valve refreshes Steam discovery tools with a broader storefront update",
          sourceLine: "Steam quietly drops a dramatic storefront revamp aimed at changing how players discover games overnight.",
          facts: "Valve introduced a beta storefront refresh with updated recommendation panels, clearer event surfaces, and improved navigation for users browsing new releases and discounts.",
          urgency: "Platform update",
          updated: "22 min ago",
          tags: ["Steam", "Storefront", "PC gaming"],
          source: "PC Gamer",
          link: "#",
        },
        {
          title: "Blizzard hiring signals continued work on an unannounced shooter project",
          sourceLine: "Blizzard sparks speculation again as fans race to decode a major hiring push for a mystery shooter.",
          facts: "A new leadership role tied to an open-world shooter suggests Blizzard is still staffing a large project, though the company has not announced a title or release window.",
          urgency: "Studio watch",
          updated: "46 min ago",
          tags: ["Blizzard", "Studios", "Shooter"],
          source: "GameSpot",
          link: "#",
        },
        {
          title: "Patent dispute around creature-battle mechanics faces new scrutiny",
          sourceLine: "Nintendo’s controversial patent fight takes a shocking turn that could reshape how studios build game systems.",
          facts: "US patent reviewers issued a nonfinal rejection affecting claims around battle mechanics, creating uncertainty about how broadly the patent can be enforced.",
          urgency: "Legal review",
          updated: "1 hr ago",
          tags: ["Nintendo", "Patents", "Game industry"],
          source: "Polygon",
          link: "#",
        },
      ],
    },
  },
};

const labelMap = {
  tech: "Tech desk",
  world: "World desk",
  health: "Health desk",
  gaming: "Gaming desk",
};

function sanitizeLine(text) {
  return BIAS_REPLACEMENTS.reduce((current, [pattern, replacement]) => current.replace(pattern, replacement), text);
}

function normalizeStory(story, tone) {
  return {
    ...story,
    tone,
    source: story.source || labelMap[tone],
    link: story.link || `./${tone}.html`,
    sourceLine: story.sourceLine || story.facts || story.title,
    facts: story.facts || story.cleanLine || story.title,
    tags: Array.isArray(story.tags) ? story.tags : [],
    cleanLine: story.cleanLine || sanitizeLine(story.sourceLine || story.facts || story.title),
  };
}

function normalizeCategory(tone, category = {}) {
  return {
    label: category.label || labelMap[tone],
    overview: category.overview || fallbackData.categories[tone]?.overview || "",
    items: (category.items || []).map((story) => normalizeStory(story, tone)),
  };
}

function normalizeData(raw) {
  const categories = {};

  CATEGORY_ORDER.forEach((tone) => {
    categories[tone] = normalizeCategory(tone, raw.categories?.[tone] || fallbackData.categories[tone]);
  });

  return {
    site: raw.site || fallbackData.site,
    generatedAt: raw.generatedAt || null,
    categories,
  };
}

function allStories(data) {
  return CATEGORY_ORDER.flatMap((tone) =>
    (data.categories[tone]?.items || []).map((story) => ({ ...normalizeStory(story, tone), tone }))
  );
}

function getLeadStories(data) {
  return CATEGORY_ORDER.flatMap((tone) => {
    const lead = data.categories[tone]?.items?.[0];
    return lead ? [lead] : [];
  });
}

function getToneColor(tone) {
  switch (tone) {
    case "tech":
      return "#0e5c66";
    case "world":
      return "#6b4f10";
    case "health":
      return "#356b39";
    case "gaming":
      return "#6d2f86";
    default:
      return "#bc3f28";
  }
}

function makeFrontlineCard(story) {
  return `
    <article class="frontline-card" data-tone="${story.tone}">
      <div class="card-label">
        <span>${labelMap[story.tone]}</span>
        <span class="dot"></span>
        <span>${story.urgency}</span>
      </div>
      <h3>${story.title}</h3>
      <p>${story.facts}</p>
      <a class="card-link" href="./${story.tone}.html">Open ${story.tone} desk</a>
    </article>
  `;
}

function makeSnapshotCard(tone, category) {
  const lead = category.items[0];
  if (!lead) {
    return `
      <article class="snapshot-card" data-tone="${tone}">
        <div>
          <p class="eyebrow">${category.label || labelMap[tone]}</p>
          <h3>Waiting for fresh items</h3>
          <p>${category.overview || "This desk will refill as soon as new reporting is available."}</p>
        </div>
        <a class="card-link" href="./${tone}.html">Open ${tone} desk</a>
      </article>
    `;
  }
  return `
    <article class="snapshot-card" data-tone="${tone}">
      <div>
        <p class="eyebrow">${category.label || labelMap[tone]}</p>
        <h3>${lead.title}</h3>
        <p>${category.overview || lead.cleanLine}</p>
      </div>
      <div class="summary-points">
        ${category.items.slice(0, 3).map((item) => `<span>${item.urgency}: ${item.facts}</span>`).join("")}
      </div>
      <a class="card-link" href="./${tone}.html">Read all ${tone} updates</a>
    </article>
  `;
}

function makeStoryCard(story) {
  const sourceLink = story.link && story.link !== "#" ? `<a class="card-link" href="${story.link}" target="_blank" rel="noopener noreferrer">Read source</a>` : "";
  const tags = story.tags.length ? story.tags.map((tag) => `<span>${tag}</span>`).join("") : "<span>Latest update</span>";

  return `
    <article class="story-card" data-tone="${story.tone}">
      <div class="story-meta">
        <span>${labelMap[story.tone]}</span>
        <span class="dot"></span>
        <span>${story.source}</span>
        <span class="dot"></span>
        <span>${story.updated}</span>
        <span class="dot"></span>
        <span>${story.urgency}</span>
      </div>
      <h3>${story.title}</h3>
      <p>${story.facts}</p>
      <div class="story-layers">
        <div class="story-layer source">
          <strong>Incoming language</strong>
          <p>${story.sourceLine}</p>
        </div>
        <div class="story-layer clean">
          <strong>Neutral brief</strong>
          <p>${story.cleanLine}</p>
        </div>
      </div>
      <div class="story-tags">
        ${tags}
      </div>
      ${sourceLink}
    </article>
  `;
}

function renderHome(data) {
  const combined = allStories(data);
  const leadStories = getLeadStories(data);
  const homeFrontlines = document.getElementById("home-frontlines");
  const tickerTrack = document.getElementById("ticker-track");
  const snapshotRow = document.getElementById("snapshot-row");
  const headlineCount = document.getElementById("headline-count");

  if (headlineCount) {
    headlineCount.textContent = String(combined.length).padStart(2, "0");
  }

  if (homeFrontlines) {
    homeFrontlines.innerHTML = leadStories.length
      ? leadStories.map(makeFrontlineCard).join("")
      : `<article class="frontline-card"><h3>Waiting for fresh items</h3><p>The live desk will populate as soon as the backend finds current reporting.</p></article>`;
  }

  if (tickerTrack) {
    const chips = combined.map(
      (story) => `
        <div class="ticker-chip">
          <span style="background:${getToneColor(story.tone)}">${story.tone.slice(0, 1).toUpperCase()}</span>
          <strong>${story.title}</strong>
          <small>${story.updated}</small>
        </div>
      `
    );
    tickerTrack.innerHTML = `${chips.join("")}${chips.join("")}`;
  }

  if (snapshotRow) {
    snapshotRow.innerHTML = CATEGORY_ORDER
      .map((tone) => makeSnapshotCard(tone, data.categories[tone]))
      .join("");
  }
}

function renderCategory(page, data) {
  const feed = document.getElementById("category-feed");
  const category = data.categories[page];

  if (!feed || !category) {
    return;
  }

  feed.innerHTML = category.items.length
    ? category.items.map(makeStoryCard).join("")
    : `<article class="story-card" data-tone="${page}"><h3>No fresh items right now</h3><p>This desk will repopulate when the backend finds new reports from its source feeds.</p></article>`;
}

async function fetchLiveData() {
  const response = await fetch("./api/briefs?category=all", {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`API returned ${response.status}`);
  }

  return normalizeData(await response.json());
}

function renderPage(data) {
  const page = document.body.dataset.page;
  if (page === "home") {
    renderHome(data);
  } else {
    renderCategory(page, data);
  }
}

async function boot() {
  const baseline = normalizeData(fallbackData);
  renderPage(baseline);

  try {
    const live = await fetchLiveData();
    renderPage(live);
  } catch (error) {
    console.warn("Falling back to bundled sample data.", error);
  }
}

boot();
