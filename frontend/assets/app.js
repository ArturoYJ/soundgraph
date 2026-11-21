const get = id => document.getElementById(id);
const view = get("view");
const sheet = get("sheet");
const loginForm = get("login-form");
const loginWarning = get("login-warning");
const loginSubmit = get("login-submit");
const paths = {
  session: "/demo/sessions/current",
  recommendations: "/recommendations",
  playlists: "/playlists",
};
const links = { discover: "#/descubrir", playlists: "#/playlists" };
const playlistPath = id => paths.playlists + "/" + encodeURIComponent(id);
const playlistLink = id => "#/playlists/" + encodeURIComponent(id);
let profile = null;
let routeRequest = 0;
let sheetRequest = 0;
let sheetFocus = null;
let saving = false;
let leaving = false;

class RequestError extends Error {
  constructor(status, code) {
    super(code || "request_failed");
    this.status = status;
    this.code = code;
  }
}

async function api(path, { method = "GET", body } = {}) {
  const response = await fetch("/api/v1" + path, {
    method, credentials: "same-origin", cache: "no-store",
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(10000),
  });
  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) throw new RequestError(response.status, data?.code);
  if (response.status !== 204 && data === null) throw new RequestError(response.status);
  return data;
}

function el(tag, text, className) {
  const item = document.createElement(tag);
  if (text != null) item.textContent = text;
  if (className) item.className = className;
  return item;
}

function button(text, callback, variant = "") {
  const item = el("button", text, "button " + variant);
  item.type = "button";
  item.addEventListener("click", callback);
  return item;
}

function link(text, href, variant = "") {
  const item = el("a", text, "button " + variant);
  item.href = href;
  return item;
}

function actions(...children) {
  const item = el("div", null, "actions");
  item.append(...children);
  return item;
}

function panel(text, controls = null, assertive = false) {
  const item = el("div", null, "panel");
  const message = el("p", text);
  if (assertive) message.setAttribute("role", "alert");
  item.append(message);
  if (controls) item.append(controls);
  return item;
}

function heading(title, subtitle) {
  const head = el("header", null, "page-head");
  const h = el("h1", title);
  h.tabIndex = -1;
  head.append(h);
  if (subtitle) head.append(el("p", subtitle, "muted"));
  view.append(head);
  return h;
}

function notice(text, urgent = false) {
  const item = el("p", text, "notice" + (urgent ? " error" : ""));
  item.setAttribute("role", urgent ? "alert" : "status");
  return item;
}

function loading(text, target, skeleton = false) {
  const block = el("div", null, skeleton ? "panel" : "muted");
  const status = el("p", text);
  status.setAttribute("role", "status");
  block.append(status);
  if (skeleton) {
    const placeholders = el("div", null, "skeleton");
    placeholders.setAttribute("aria-hidden", "true");
    placeholders.append(el("span"), el("span"), el("span"));
    block.append(placeholders);
  }
  target.append(block);
  return block;
}

function resetNotification() {
  get("notification").hidden = true;
  get("notification-link").hidden = true;
  get("notification-text").textContent = "";
}

function notify(text, kind, destination) {
  const item = get("notification");
  const target = get("notification-link");
  item.dataset.kind = kind;
  item.hidden = false;
  target.hidden = !destination;
  if (destination) target.href = destination;
  get("notification-text").textContent = text;
}

function showLogin(message = "", focus = false) {
  profile = null;
  routeRequest++;
  closeSheet({ restore: false });
  resetNotification();
  get("nav").hidden = true;
  get("account").hidden = true;
  get("login").hidden = false;
  view.replaceChildren();
  loginForm.reset();
  loginWarning.hidden = !message;
  loginWarning.textContent = message;
  document.title = "Acceso · SoundGraph";
  if (focus) get("login-title").focus();
}

function showAccount(nextProfile) {
  profile = nextProfile;
  get("login").hidden = true;
  get("nav").hidden = false;
  get("account").hidden = false;
  get("profile-name").textContent = profile.displayName;
  get("avatar").textContent = profile.displayName.trim().slice(0, 1).toLocaleUpperCase("es");
  get("logout").setAttribute("aria-label", "Salir de la sesión de " + profile.displayName);
}

function expired(error) {
  if (!(error instanceof RequestError) || error.status !== 401) return false;
  showLogin("Tu sesión terminó. Vuelve a entrar.", true);
  return true;
}

async function restoreSession() {
  view.replaceChildren();
  loading("Comprobando la sesión…", view);
  try {
    showAccount(await api(paths.session));
    await renderRoute();
  } catch (error) {
    if (error.status === 401) return showLogin();
    view.replaceChildren();
    heading("SoundGraph");
    view.append(panel("No pudimos comprobar la sesión.", actions(button("Reintentar", restoreSession)), true));
  }
}

loginForm.addEventListener("submit", async event => {
  event.preventDefault();
  if (loginSubmit.disabled) return;
  loginWarning.hidden = true;
  loginSubmit.disabled = true;
  loginSubmit.textContent = "Entrando…";
  const code = get("code");
  const select = get("profile");
  const credentials = { profileId: select.value, code: code.value };
  select.disabled = code.disabled = true;
  try {
    const next = await api("/demo/sessions", { method: "POST", body: credentials });
    loginForm.reset();
    showAccount(next);
    await renderRoute({ focus: true });
  } catch (error) {
    code.value = "";
    loginWarning.hidden = false;
    loginWarning.textContent = error.code === "invalid_credentials" ? "El perfil o el código no son válidos."
      : error.code === "invalid_input" ? "Revisa el perfil y el código."
      : "No pudimos iniciar la sesión. Intenta de nuevo.";
  } finally {
    loginSubmit.disabled = select.disabled = code.disabled = false;
    loginSubmit.textContent = "Entrar";
    if (!profile) code.focus();
  }
});

get("logout").addEventListener("click", async () => {
  if (leaving) return;
  leaving = get("logout").disabled = true;
  try {
    await api(paths.session, { method: "DELETE" });
    history.replaceState(null, "", "/");
    showLogin("", true);
  } catch {
    notify("No pudimos cerrar la sesión. Intenta de nuevo.", "error");
  } finally {
    leaving = get("logout").disabled = false;
  }
});

function route() {
  if (location.hash === links.playlists) return { page: "playlists" };
  const match = /^#\/playlists\/([A-Za-z0-9][A-Za-z0-9-]{0,63})$/.exec(location.hash);
  if (match) return { page: "detail", id: match[1] };
  return { page: "discover" };
}

async function renderRoute({ focus = false } = {}) {
  if (!profile) return;
  const token = ++routeRequest;
  const current = route();
  const oldActive = document.activeElement;
  const discover = current.page === "discover";
  ["discover-link", "lists-link"].forEach((id, index) => {
    if (discover === (index === 0)) get(id).setAttribute("aria-current", "page");
    else get(id).removeAttribute("aria-current");
  });
  view.replaceChildren();
  const back = current.page === "detail";
  if (back) view.append(link("← Volver a mis playlists", links.playlists, "quiet compact back"));
  const title = heading(
    discover ? "Descubre música" : back ? "Playlist" : "Mis playlists",
    discover ? "Recomendaciones basadas en escuchas compartidas." : null,
  );
  document.title = title.textContent + " · SoundGraph";
  if (focus || oldActive === document.body) title.focus();
  const wait = loading(discover ? "Cargando recomendaciones…" : "Cargando playlists…", view, discover);
  try {
    const data = await api(discover ? paths.recommendations : back ? playlistPath(current.id) : paths.playlists);
    if (token !== routeRequest) return;
    wait.remove();
    if (discover) renderDiscover(data);
    else if (back) renderPlaylist(data, title);
    else renderPlaylists(data);
  } catch (error) {
    if (token !== routeRequest) return;
    wait.remove();
    if (expired(error)) return;
    const retry = button("Reintentar", () => renderRoute({ focus: true }), "primary");
    const other = link(discover ? "Ir a Mis playlists" : "Ir a Descubrir", discover ? links.playlists : links.discover, "quiet");
    if (back && error.code === "playlist_not_found") view.append(panel("No encontramos esa playlist.", null, true));
    else {
      const copy = discover ? "No pudimos cargar las recomendaciones." : back ? "No pudimos cargar esta playlist." : "No pudimos cargar tus playlists.";
      view.append(panel(copy, actions(retry, other), true));
    }
  }
}

function artist(song) {
  return song.editorial.credits.filter(credit => credit.role.toLocaleLowerCase("es") === "artista")
    .map(credit => credit.name).join(", ");
}

function initials(text) {
  return (text.match(/[\p{L}\p{N}]+/gu) || []).slice(0, 2)
    .map(part => part.slice(0, 1).toLocaleUpperCase("es")).join("") || "♪";
}

function reason(affinity) {
  return affinity === 1 ? "1 perfil con escuchas en común también escuchó esta canción"
    : affinity + " perfiles con escuchas en común también escucharon esta canción";
}

function countLabel(count, short = false) {
  if (short) return count + (count === 1 ? " canción" : " canciones");
  return count + (count === 1 ? " pista guardada" : " pistas guardadas");
}

function renderDiscover({ items, partial }) {
  if (partial) view.append(notice("Algunas recomendaciones no se muestran porque su ficha no está disponible."));
  if (!items.length) {
    if (!partial) view.append(panel("Todavía no hay recomendaciones para este perfil.", actions(link("Ir a Mis playlists", links.playlists, "primary"))));
    return;
  }
  const list = el("ul", null, "song-list");
  for (const rec of items) {
    const { song, affinity } = rec;
    const row = el("li", null, "song surface");
    const grid = el("div", null, "song-inner");
    const name = artist(song);
    const monogram = el("span", initials(name || song.title), "monogram");
    monogram.setAttribute("aria-hidden", "true");
    const description = el("div");
    description.append(el("h2", song.title, "song-title"));
    if (name) description.append(el("p", name, "muted"));
    const openDetail = button("Ver ficha", e => songSheet(rec, e.currentTarget));
    const openSave = button("Guardar en playlist", e => saveSheet(rec, e.currentTarget), "primary");
    const why = el("p", reason(affinity), "reason");
    const controls = actions(openDetail, openSave);
    // One DOM structure serves desktop and mobile; visual subgrid spans the mobile card.
    grid.append(monogram, description, why, controls);
    row.append(grid);
    list.append(row);
  }
  view.append(list);
}

function renderPlaylists({ items }) {
  if (!items.length) {
    view.append(panel("Este perfil todavía no tiene playlists."));
    return;
  }
  const list = el("ul", null, "playlists");
  for (const item of items) {
    const li = el("li", null, "surface playlist-row");
    const text = el("div");
    text.append(el("h2", item.name), el("p", countLabel(item.trackCount), "secondary-text"));
    const open = link("Abrir", playlistLink(item.playlistId), "primary");
    open.setAttribute("aria-label", "Abrir " + item.name);
    li.append(text, open);
    list.append(li);
  }
  view.append(list);
}

function renderPlaylist({ name, tracks, trackCount }, title) {
  title.textContent = name;
  document.title = name + " · SoundGraph";
  title.after(el("p", countLabel(trackCount), "muted"));
  if (!tracks.length) {
    view.append(panel("Aún no hay canciones guardadas.", actions(link("Ir a Descubrir", links.discover, "primary"))));
    return;
  }
  view.append(el("h3", "Orden de la playlist"));
  const list = el("ol", null, "tracks");
  for (const track of tracks) {
    const li = el("li", null, "surface track-row");
    const number = el("span", String(track.position).padStart(2, "0"), "track-number");
    number.setAttribute("aria-hidden", "true");
    const text = el("div");
    text.append(el("strong", track.song?.title ?? "Ficha no disponible"));
    const name = track.song && artist(track.song);
    if (name) text.append(el("p", name, "secondary-text"));
    li.append(number, text);
    list.append(li);
  }
  const next = link("Seguir descubriendo", links.discover);
  next.classList.add("follow");
  view.append(list, next);
}

function openSheet(kind, title, restore) {
  if (sheet.open) closeSheet({ restore: false });
  sheetFocus = restore;
  sheet.dataset.kind = kind;
  const heading = el("h2", title);
  heading.id = "sheet-title";
  heading.tabIndex = -1;
  sheet.replaceChildren(heading);
  sheet.showModal();
  heading.focus();
  return heading;
}

function closeSheet({ restore = true } = {}) {
  sheetRequest++;
  saving = false;
  const target = sheetFocus;
  sheetFocus = null;
  if (sheet.open) sheet.close();
  sheet.replaceChildren();
  if (restore && target?.isConnected) target.focus();
}

sheet.addEventListener("cancel", event => {
  event.preventDefault();
  if (!saving) closeSheet();
});

function songSheet(rec, origin) {
  const { song, affinity } = rec;
  openSheet("detail", song.title, origin);
  for (const credit of song.editorial.credits) {
    const role = credit.role.charAt(0).toLocaleUpperCase("es") + credit.role.slice(1);
    sheet.append(el("p", role + ": " + credit.name, "muted"));
  }
  sheet.append(el("p", reason(affinity), "reason"));
  for (const note of song.editorial.notes) {
    const block = el("div", null, "note");
    block.append(el("p", note.text), el("p", "Fuente: " + note.source, "secondary-text"));
    sheet.append(block);
  }
  const control = actions(button("Cerrar", () => closeSheet(), "quiet"), button("Guardar en playlist",
    () => saveSheet(rec, origin, () => songSheet(rec, origin)), "primary"));
  control.classList.add("end-actions");
  sheet.append(control);
}

async function saveSheet({ song, affinity }, origin, back = null) {
  resetNotification();
  openSheet("save", "Guardar en playlist", origin);
  let request = ++sheetRequest;
  sheet.append(el("p", song.title, "muted"));
  const loadingState = loading("Cargando playlists…", sheet);
  const cancel = button("Cancelar", () => back ? back() : closeSheet(), "quiet");
  let pendingActions = actions(cancel);
  sheet.append(pendingActions);
  try {
    const { items } = await api(paths.playlists);
    if (request !== sheetRequest) return;
    loadingState.remove();
    if (!items.length) {
      pendingActions.before(el("p", "No hay playlists disponibles para guardar en este perfil.", "notice"));
      return;
    }
    const form = el("form");
    const fields = el("fieldset");
    const prompt = el("legend", "Selecciona una playlist", "secondary-text");
    fields.append(prompt);
    for (const playlist of items) {
      const label = el("label", null, "picker");
      const radio = el("input");
      radio.type = "radio";
      radio.name = "playlist";
      radio.value = playlist.playlistId;
      radio.required = true;
      radio.checked = items.length === 1;
      label.append(radio, el("span", playlist.name + " · " + countLabel(playlist.trackCount, true)));
      fields.append(label);
    }
    const warning = notice("", true);
    warning.hidden = true;
    const go = el("a", "Ver playlist", "button quiet");
    go.hidden = true;
    go.addEventListener("click", () => closeSheet({ restore: false }));
    const save = el("button", "Guardar", "button primary");
    save.type = "submit";
    form.append(fields, warning, actions(cancel, go, save));
    pendingActions.replaceWith(form);
    form.addEventListener("submit", async event => {
      event.preventDefault();
      if (saving) return;
      const selected = items.find(item => item.playlistId === new FormData(form).get("playlist"));
      if (!selected) return;
      const target = playlistLink(selected.playlistId);
      const operation = sheetRequest;
      saving = fields.disabled = save.disabled = cancel.disabled = true;
      save.textContent = "Guardando…";
      warning.hidden = go.hidden = true;
      try {
        const result = await api(playlistPath(selected.playlistId) + "/tracks/" + encodeURIComponent(song.songId), { method: "PUT" });
        if (operation !== sheetRequest) return;
        closeSheet();
        notify((result.created ? "Guardada en " : "Ya estaba en ") + selected.name, result.created ? "success" : "neutral", target);
      } catch (error) {
        if (operation !== sheetRequest || expired(error)) return;
        warning.hidden = false;
        warning.textContent = error.code === "playlist_not_found" ? "La playlist ya no está disponible." :
          error.code === "song_not_found" ? "La ficha de esta canción ya no está disponible." :
            "No pudimos confirmar el guardado.";
        save.textContent = "Reintentar";
        if (!["playlist_not_found", "song_not_found"].includes(error.code)) {
          go.href = target;
          go.hidden = false;
        }
      } finally {
        if (operation === sheetRequest) {
          saving = fields.disabled = save.disabled = cancel.disabled = false;
          save.focus();
        }
      }
    });
  } catch (error) {
    if (request !== sheetRequest || expired(error)) return;
    loadingState.replaceWith(notice("No pudimos cargar tus playlists.", true));
    pendingActions.append(button("Reintentar", () => saveSheet({ song, affinity }, origin, back), "primary"));
  }
}

get("notification-link").addEventListener("click", resetNotification);
document.querySelector(".skip").addEventListener("click", event => {
  event.preventDefault();
  get("main").focus();
});
window.addEventListener("hashchange", () => {
  closeSheet({ restore: false });
  resetNotification();
  renderRoute({ focus: true });
});
restoreSession();
