"use strict";
const payload = JSON.parse(document.getElementById("map-data").textContent),
  data = payload.content,
  records = data.records,
  costs = data.costs;
const $ = (id) => document.getElementById(id),
  el = (tag, text, cls) => {
    const n = document.createElement(tag);
    if (text !== undefined) n.textContent = text;
    if (cls) n.className = cls;
    return n;
  };
const labels = {
  planned: "Planifiée",
  active: "En cours",
  submitted: "En revue",
  accepted: "Acceptée",
  cancelled: "Annulée",
  proposed: "Proposée",
  superseded: "Remplacée",
  open: "Ouvert",
  resolved: "Résolu",
  approve: "Approuvée",
  request_changes: "À reprendre",
};
const money = (n) =>
  n === null
    ? "Non calculable"
    : new Intl.NumberFormat("fr-FR", {
        style: "currency",
        currency: costs.currency,
      }).format(n / 100);
const filtered = (items) =>
  items.filter((x) =>
    JSON.stringify(x)
      .toLocaleLowerCase()
      .includes($("search").value.toLocaleLowerCase()),
  );
const badge = (text, type = "") => el("span", text, "pill " + type);
function details(record) {
  const d = el("details"),
    s = el("summary", "Voir la fiche source et ses références");
  d.append(s, el("pre", JSON.stringify(record, null, 2)));
  return d;
}
function notice(text, bad = false) {
  return el("div", text, "notice" + (bad ? " error" : ""));
}
function empty(text) {
  return el("div", text, "empty");
}
function metric(label, value, hint) {
  const n = el("div", undefined, "metric");
  n.append(
    el("div", label, "label"),
    el("div", value, "value"),
    el("div", hint, "hint"),
  );
  return n;
}
function section(title, note) {
  const f = document.createDocumentFragment();
  f.append(el("h2", title), el("p", note, "section-note"));
  return f;
}
function cardList(items, titleFor, statusFor) {
  const frag = document.createDocumentFragment(),
    shown = filtered(items);
  $("count").textContent = shown.length + " fiche(s)";
  if (!shown.length)
    frag.append(
      empty(
        "Aucune fiche dans cette vue. Les agents alimentent les sources ; la carte est régénérée.",
      ),
    );
  for (const r of shown) {
    const c = el("article", undefined, "card"),
      row = el("div", undefined, "row");
    row.append(el("h3", titleFor(r)), badge(statusFor(r)));
    c.append(row, el("code", r.id), details(r));
    frag.append(c);
  }
  return frag;
}
function overview() {
  const f = document.createDocumentFragment(),
    metrics = el("div", undefined, "metrics");
  metrics.append(
    metric(
      "Missions exécutées",
      costs.executed_tasks,
      costs.run_count + " exécutions enregistrées",
    ),
    metric(
      "Livrables acceptés",
      costs.accepted_deliverables,
      costs.accepted_tasks + " missions acceptées",
    ),
    metric(
      "Coût connu",
      money(costs.total_known_cost_minor),
      costs.missing_cost_runs + " montant(s) inconnu(s)",
    ),
    metric(
      "Coût / livrable accepté",
      money(costs.cost_per_accepted_deliverable_minor),
      costs.estimated_cost_runs
        ? "Inclut des estimations"
        : "Échecs et reprises inclus",
    ),
  );
  f.append(metrics);
  const grid = el("div", undefined, "grid"),
    left = el("div", undefined, "card"),
    right = el("div", undefined, "card");
  left.append(el("h2", "Travail en cours"));
  const tasks = filtered(records.tasks).filter((t) =>
    ["active", "submitted", "planned"].includes(t.status),
  );
  if (!tasks.length)
    left.append(el("p", "Aucune mission en attente ou en cours.", "sub"));
  for (const t of tasks) {
    const row = el("div", undefined, "row"),
      label = el("div", t.title, "task-title");
    label.append(el("small", t.owner + " · " + t.id));
    row.append(label, badge(labels[t.status]));
    left.append(row);
  }
  right.append(el("h2", "État des contrôles"));
  right.append(
    notice(
      data.validation.ok
        ? "Structure des fiches vérifiée. Les tests produit restent des preuves distinctes."
        : "Des incohérences de fiches demandent une correction.",
      !data.validation.ok,
    ),
  );
  for (const text of [...data.validation.errors, ...data.validation.warnings])
    right.append(el("p", text, "section-note"));
  right.append(
    el(
      "p",
      records.evidence.length +
        " vérification(s) exécutée(s) · " +
        records.reviews.length +
        " revue(s) déclarée(s)",
      "sub",
    ),
  );
  grid.append(left, right);
  f.append(
    grid,
    notice(
      "Réservations actives : consulter « framework lease list ». Elles sont locales au clone et ne sont pas incluses dans cet instantané.",
    ),
  );
  $("count").textContent = records.tasks.length + " missions";
  return f;
}
function economics() {
  const f = section(
    "Économie des livraisons",
    "Montants dans la devise du projet. Chaque tentative, échec, revue et coordination est comptabilisé.",
  );
  if (!costs.complete)
    f.append(
      notice(
        "Coûts incomplets : les ratios concernés restent non calculables. Un montant inconnu ne vaut pas zéro.",
      ),
    );
  if (costs.estimated_cost_runs)
    f.append(
      notice(
        "Certains coûts sont estimés. Ces ratios ne sont pas des coûts entièrement facturés.",
      ),
    );
  const metrics = el("div", undefined, "metrics");
  metrics.append(
    metric(
      "Coût connu total",
      money(costs.total_known_cost_minor),
      "Portefeuille complet",
    ),
    metric(
      "Par mission exécutée",
      money(costs.cost_per_executed_task_minor),
      "Toutes les tentatives incluses",
    ),
    metric(
      "Par mission acceptée",
      money(costs.cost_per_accepted_task_minor),
      "Échecs des autres missions inclus",
    ),
    metric(
      "Par livrable accepté",
      money(costs.cost_per_accepted_deliverable_minor),
      "Nombre de livrables du contrat",
    ),
  );
  f.append(metrics);
  const wrap = el("div", undefined, "table-wrap card"),
    table = el("table"),
    head = el("tr");
  for (const h of [
    "Mission",
    "Exécutions",
    "Coût connu",
    "Budget",
    "Livrables acceptés",
    "Mesure",
  ])
    head.append(el("th", h));
  const thead = el("thead");
  thead.append(head);
  table.append(thead);
  const tbody = el("tbody"),
    rows = filtered(costs.tasks);
  for (const r of rows) {
    const row = el("tr");
    for (const v of [
      r.title,
      r.runs,
      money(r.known_cost_minor),
      money(r.budget_minor),
      r.accepted_deliverables,
      r.complete
        ? r.estimated_cost_runs
          ? "Estimée"
          : "Renseignée"
        : "Incomplète",
    ])
      row.append(el("td", v));
    if (r.over_budget) row.lastChild.append(badge("Budget dépassé", "warn"));
    tbody.append(row);
  }
  table.append(tbody);
  wrap.append(table);
  f.append(wrap);
  for (const group of costs.by_role || []) {
    f.append(el("p", group.name + " : " + money(group.known_cost_minor) +
      " connus · " + group.runs + " appels · " + group.missing_cost_runs + " coûts inconnus"));
  }
  $("count").textContent = rows.length + " missions";
  return f;
}
function proof() {
  const f = section(
    "Preuves et revues",
    "Une vérification est liée à une empreinte du contenu et du contrat. Les identités des revues sont déclaratives.",
  );
  const legend = el("div", undefined, "legend");
  legend.append(
    badge("Déclaré par un agent"),
    badge("Vérification exécutée"),
    badge("Acceptation enregistrée"),
  );
  f.append(legend);
  f.append(
    cardList(
      [...records.evidence, ...records.reviews],
      (r) => r.task + " · " + r.id,
      (r) =>
        (r.verdict
          ? labels[r.verdict] + " · déclarée"
          : r.passed
            ? "Vérification réussie"
            : "Vérification échouée") +
        (r.fingerprint !== data.fingerprint ? " · contenu ancien" : ""),
    ),
  );
  return f;
}
const views = [
  ["overview", "Vue d’ensemble", overview],
  [
    "tasks",
    "Missions",
    () =>
      cardList(
        records.tasks,
        (r) => r.title,
        (r) => labels[r.status],
      ),
  ],
  [
    "decisions",
    "Décisions",
    () =>
      cardList(
        records.decisions,
        (r) => r.title,
        (r) =>
          r.status === "active" ? "Active" : labels[r.status] || r.status,
      ),
  ],
  [
    "risks",
    "Risques",
    () =>
      cardList(
        [...records.findings, ...records.exceptions],
        (r) => r.title || r.reason,
        (r) =>
          r.severity
            ? labels[r.status] + " · " + r.severity
            : "Exception déclarée",
      ),
  ],
  ["orchestrations", "Orchestration", () => cardList(
    records.orchestrations || [],
    r => r.task + " · " + r.profile.roles.orchestrator.model,
    r => r.status + " · " + r.steps.length + " appels · tour " + r.round
  )],
  ["proof", "Preuves", proof],
  ["costs", "Coûts", economics],
  [
    "memory",
    "Journaux",
    () =>
      cardList(
        records.runs,
        (r) => r.task + " · " + r.model,
        (r) => r.outcome + " · " + r.cost_source,
      ),
  ],
];
let active = "overview";
function render() {
  const selected = views.find((v) => v[0] === active);
  $("view").replaceChildren(selected[2]());
  for (const button of $("navigation").children)
    button.setAttribute("aria-current", String(button.dataset.view === active));
}
for (const [id, label] of views) {
  const b = el("button", label);
  b.dataset.view = id;
  b.onclick = () => {
    active = id;
    render();
  };
  $("navigation").append(b);
}
$("project").textContent = data.policy.project;
$("subtitle").textContent =
  "Du besoin au livrable accepté, avec les décisions et les preuves.";
$("health").textContent = data.validation.ok
  ? "Fiches cohérentes"
  : "À examiner";
if (!data.validation.ok) $("health").classList.add("bad");
$("footer").textContent =
  "Générée le " +
  payload.generated_at +
  " · Commit observé " +
  payload.observed_head +
  " · Empreinte " +
  data.fingerprint +
  " · Régénérer : framework map";
$("search").addEventListener("input", render);
render();
