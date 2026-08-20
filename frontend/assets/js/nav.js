// Shared secondary nav strip for all logged-in app pages.
// Usage: <div id="appNavMount"></div> then renderAppNav('dashboard') in a script tag.

const APP_NAV_ITEMS = [
  { key: "dashboard",  href: "dashboard.html",  label: "Today" },
  { key: "twin",       href: "twin.html",       label: "Digital Twin" },
  { key: "tasks",      href: "tasks.html",      label: "Recovery Tasks" },
  { key: "cravings",   href: "cravings.html",   label: "Cravings" },
  { key: "journal",    href: "journal.html",    label: "Journal" },
  { key: "triggers",   href: "triggers.html",   label: "Triggers" },
  { key: "analytics",  href: "analytics.html",  label: "Analytics" },
  { key: "wellness",   href: "wellness.html",   label: "Wellness Lab" },
  { key: "coach",      href: "coach.html",      label: "Recovery Coach" },
  { key: "journey",    href: "journey.html",    label: "My Journey" },
  { key: "resources",  href: "resources.html",  label: "Resources" },
  { key: "profile",    href: "profile.html",    label: "Profile" },
];

function renderAppNav(activeKey) {
  const mount = document.getElementById("appNavMount");
  if (!mount) return;
  mount.innerHTML = `
    <div class="app-nav">
      <div class="wrap app-nav-inner">
        ${APP_NAV_ITEMS.map(item => `
          <a href="${item.href}" class="app-nav-item${item.key === activeKey ? " active" : ""}">${item.label}</a>
        `).join("")}
      </div>
    </div>
  `;
}
