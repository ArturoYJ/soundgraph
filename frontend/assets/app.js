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
  songs: "/songs",
};
const links = { discover: "#/descubrir", playlists: "#/playlists", editorial: "#/editorial" };
const playlistPath = id => paths.playlists + "/" + encodeURIComponent(id);
const playlistLink = id => "#/playlists/" + encodeURIComponent(id);
const editorialPath = id => paths.songs + "/" + encodeURIComponent(id) + "/editorial";
const trackPath = (playlistId, songId) => playlistPath(playlistId) + "/tracks/" + encodeURIComponent(songId);
let profile = null;
let routeRequest = 0;
let sheetRequest = 0;
let sheetFocus = null;
let saving = false;
let leaving = false;
let sheetDismiss = null;
let dirtyEditor = null;

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
  get("editor-link").hidden = profile.role !== "editor";
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
  const editorial = /^#\/editorial(?:\?after=([A-Za-z0-9][A-Za-z0-9-]{0,63}))?$/.exec(location.hash);
  if (editorial) return { page: "editorial", after: editorial[1] };
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
  const editorial = current.page === "editorial";
  const back = current.page === "detail";
  Object.entries({
    "discover-link": discover,
    "lists-link": back || current.page === "playlists",
    "editor-link": editorial && profile.role === "editor",
  }).forEach(([id, active]) => {
    if (active) get(id).setAttribute("aria-current", "page");
    else get(id).removeAttribute("aria-current");
  });
  view.replaceChildren();
  if (back) view.append(link("← Volver a mis playlists", links.playlists, "quiet compact back"));
  const title = heading(
    discover ? "Descubre música" : back ? "Playlist" : editorial ? "Catálogo editorial" : "Mis playlists",
    discover ? "Recomendaciones basadas en escuchas compartidas." :
      editorial && profile.role === "editor" ? "Elige una canción para consultar y actualizar sus notas." : null,
  );
  document.title = title.textContent + " · SoundGraph";
  if (focus || oldActive === document.body) title.focus();
  if (editorial && profile.role !== "editor") {
    view.append(panel("Esta sección solo está disponible para el perfil Editor.",
      actions(link("Ir a Descubrir", links.discover)), true));
    return;
  }
  const wait = loading(discover ? "Cargando recomendaciones…" :
    editorial ? "Cargando catálogo…" : "Cargando playlists…", view, discover);
  try {
    const data = await api(discover ? paths.recommendations : back ? playlistPath(current.id) :
      editorial ? paths.songs + (current.after ? "?after=" + encodeURIComponent(current.after) : "") :
        paths.playlists);
    if (token !== routeRequest) return;
    wait.remove();
    if (discover) renderDiscover(data);
    else if (back) renderPlaylist(data, title);
    else if (editorial) renderEditorial(data, current.after);
    else renderPlaylists(data);
  } catch (error) {
    if (token !== routeRequest) return;
    wait.remove();
    if (expired(error)) return;
    const retry = button("Reintentar", () => renderRoute({ focus: true }), "primary");
    const other = link(discover ? "Ir a Mis playlists" : "Ir a Descubrir", discover ? links.playlists : links.discover, "quiet");
    if (back && error.code === "playlist_not_found") view.append(panel("No encontramos esa playlist.", null, true));
    else {
      const copy = discover ? "No pudimos cargar las recomendaciones." : back ? "No pudimos cargar esta playlist." :
        editorial ? editError(error, "No pudimos cargar el catálogo.") : "No pudimos cargar tus playlists.";
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
  const tools = actions(button("Crear playlist", e => playlistNameSheet(e.currentTarget), "primary"));
  tools.classList.add("page-actions");
  view.append(tools);
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

function renderPlaylist(playlist, title) {
  const { name, tracks, trackCount } = playlist;
  title.textContent = name;
  document.title = name + " · SoundGraph";
  title.after(el("p", countLabel(trackCount), "muted"));
  const tools = actions(
    button("Renombrar", e => playlistNameSheet(e.currentTarget, playlist)),
    button("Eliminar playlist", e => deletePlaylistSheet(e.currentTarget, playlist), "danger-outline"),
  );
  if (tracks.length >= 2 && tracks.length <= 1000) {
    tools.prepend(button("Reordenar pistas", e => reorderSheet(e.currentTarget, playlist), "primary"));
  }
  tools.classList.add("page-actions");
  view.append(tools);
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
    const remove = button("Quitar", e => removeTrackSheet(e.currentTarget, playlist, track), "quiet compact");
    remove.classList.add("track-action");
    remove.setAttribute("aria-label", "Quitar " + (track.song?.title ?? "pista sin ficha") + " de la playlist");
    li.append(number, text, remove);
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
  sheetDismiss = null;
  dirtyEditor = null;
  const target = sheetFocus;
  sheetFocus = null;
  if (sheet.open) sheet.close();
  sheet.replaceChildren();
  if (restore && target?.isConnected) target.focus();
}

sheet.addEventListener("cancel", event => {
  event.preventDefault();
  if (!saving) {
    if (sheetDismiss) sheetDismiss();
    else closeSheet();
  }
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
        const result = await api(trackPath(selected.playlistId, song.songId), { method: "PUT" });
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

function editError(error, fallback) {
  switch (error.code) {
    case "editor_required": return "Solo el perfil Editor puede consultar y editar estas fichas.";
    case "playlist_not_found": return "La playlist ya no está disponible.";
    case "song_not_found": return "La ficha ya no está disponible.";
    case "invalid_track_order": return "Las pistas cambiaron. Cierra este diálogo y vuelve a abrir la playlist antes de reordenar.";
    case "invalid_input": return "Revisa los campos e inténtalo de nuevo.";
    default: return fallback;
  }
}

function managementForm(form, { label, pending, danger = false, cancel = () => closeSheet(), request, fallback, success }) {
  const warning = notice("", true);
  warning.hidden = true;
  const cancelButton = button("Cancelar", cancel, "quiet");
  const submit = el("button", label, "button " + (danger ? "danger" : "primary"));
  submit.type = "submit";
  form.append(warning, actions(cancelButton, submit));
  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (saving) return;
    warning.hidden = true;
    let send;
    try {
      // Read and validate the form before disabling its controls.
      send = request();
    } catch (error) {
      warning.textContent = error.message;
      warning.hidden = false;
      return;
    }
    const version = sheetRequest;
    const enabled = [...form.elements].filter(control => !control.disabled);
    saving = true;
    for (const control of enabled) control.disabled = true;
    submit.textContent = pending;
    let result;
    try {
      result = await send();
    } catch (error) {
      if (version !== sheetRequest || expired(error)) return;
      warning.textContent = editError(error, fallback);
      warning.hidden = false;
      return;
    } finally {
      if (version === sheetRequest) {
        saving = false;
        for (const control of enabled) control.disabled = false;
        submit.textContent = label;
        if (!warning.hidden) submit.focus();
      }
    }
    if (version === sheetRequest) success(result);
  });
}

function finishManagement(message, destination = null) {
  closeSheet({ restore: false });
  if (destination) history.pushState(null, "", destination);
  notify(message, "success");
  renderRoute({ focus: true });
}

function playlistNameSheet(origin, playlist = null) {
  openSheet("management", playlist ? "Renombrar playlist" : "Crear playlist", origin);
  const form = el("form");
  const input = el("input");
  input.id = "playlist-name";
  input.type = "text";
  input.required = true;
  input.value = playlist?.name ?? "";
  input.setAttribute("aria-describedby", "playlist-name-help");
  const field = el("label", "Nombre");
  field.htmlFor = input.id;
  const help = el("p", "1 a 100 caracteres, sin contar espacios al inicio o al final.", "secondary-text");
  help.id = "playlist-name-help";
  form.append(field, input, help);
  managementForm(form, {
    label: playlist ? "Guardar cambios" : "Crear",
    pending: playlist ? "Guardando…" : "Creando…",
    fallback: playlist ? "No pudimos confirmar el cambio de nombre." :
      "No pudimos confirmar la creación. Revisa Mis playlists antes de volver a intentarlo.",
    request: () => {
      const name = input.value.trim();
      if (!name || [...name].length > 100) {
        input.focus();
        throw new Error("El nombre debe tener de 1 a 100 caracteres.");
      }
      return () => api(playlist ? playlistPath(playlist.playlistId) : paths.playlists,
        { method: playlist ? "PATCH" : "POST", body: { name } });
    },
    success: result => finishManagement((playlist ? "Playlist renombrada: " : "Playlist creada: ") + result.name),
  });
  sheet.append(form);
  input.focus();
}

function confirmRemoval(origin, title, description, path, outcome, destination = null) {
  openSheet("management", title, origin);
  sheet.append(el("p", description, "muted"));
  const form = el("form");
  managementForm(form, {
    label: destination ? "Eliminar playlist" : "Quitar pista",
    pending: destination ? "Eliminando…" : "Quitando…",
    danger: true,
    fallback: "No pudimos confirmar la operación. Comprueba el estado de la playlist.",
    request: () => () => api(path, { method: "DELETE" }),
    success: () => finishManagement(outcome, destination),
  });
  sheet.append(form);
}

function deletePlaylistSheet(origin, playlist) {
  confirmRemoval(origin, "¿Eliminar esta playlist?",
    "Eliminarás «" + playlist.name + "» y su lista de pistas. Las canciones seguirán en el catálogo.",
    playlistPath(playlist.playlistId), "Playlist eliminada.", links.playlists);
}

function removeTrackSheet(origin, playlist, track) {
  const name = track.song?.title ?? "la pista sin ficha";
  confirmRemoval(origin, "¿Quitar esta pista?", "Se quitará «" + name + "» de «" + playlist.name + "».",
    trackPath(playlist.playlistId, track.songId), "Pista retirada de la playlist.");
}

function reorderSheet(origin, playlist) {
  openSheet("management", "Reordenar pistas", origin);
  sheet.append(el("p", "Los cambios se aplican al guardar el orden.", "muted"));
  const draft = [...playlist.tracks];
  const form = el("form");
  const list = el("ol", null, "tracks order-list");
  const feedback = el("p", "", "secondary-text");
  feedback.setAttribute("role", "status");

  function draw(focusIndex, direction) {
    list.replaceChildren();
    draft.forEach((track, i) => {
      const row = el("li", null, "track-row surface");
      const title = track.song?.title ?? "Ficha no disponible";
      const name = el("span", (i + 1) + ". " + title);
      const controls = [-1, 1].map(step => {
        const label = step < 0 ? "Subir" : "Bajar";
        const move = button(label, () => {
          [draft[i], draft[i + step]] = [draft[i + step], draft[i]];
          feedback.textContent = title + " ahora está en la posición " + (i + step + 1) + ".";
          draw(i + step, step);
        }, "compact");
        move.setAttribute("aria-label", label + " " + title);
        move.disabled = i + step < 0 || i + step >= draft.length;
        return move;
      });
      row.append(name, actions(...controls));
      list.append(row);
      if (i === focusIndex) {
        const preferred = controls[direction < 0 ? 0 : 1];
        (preferred.disabled ? controls.find(control => !control.disabled) : preferred)?.focus();
      }
    });
  }

  form.append(list, feedback);
  draw();
  managementForm(form, {
    label: "Guardar orden",
    pending: "Guardando…",
    request: () => () => api(playlistPath(playlist.playlistId) + "/track-order",
      { method: "PUT", body: { songIds: draft.map(track => track.songId) } }),
    fallback: "No pudimos confirmar el nuevo orden. Tu borrador sigue abierto.",
    success: () => finishManagement("Orden de las pistas actualizado."),
  });
  sheet.append(form);
}

function renderEditorial({ items, nextAfter }, after) {
  if (!items.length) view.append(panel("No encontramos fichas en esta página."));
  else {
    const list = el("ul", null, "playlists");
    for (const item of items) {
      const row = el("li", null, "surface playlist-row");
      const open = button("Editar notas", e => editorialSheet(e.currentTarget, item), "primary");
      open.setAttribute("aria-label", "Editar notas de " + item.title);
      row.append(el("h2", item.title), open);
      list.append(row);
    }
    view.append(list);
  }
  const pagination = actions();
  if (after) pagination.append(link("Volver al inicio del catálogo", links.editorial, "quiet"));
  if (nextAfter) pagination.append(link("Siguiente página", links.editorial + "?after=" + encodeURIComponent(nextAfter)));
  if (pagination.childElementCount) {
    pagination.classList.add("page-actions", "follow");
    view.append(pagination);
  }
}

async function editorialSheet(origin, item) {
  openSheet("editorial", "Editar notas", origin);
  sheet.append(el("p", item.title, "muted"));
  const wait = loading("Cargando ficha…", sheet);
  const cancel = actions(button("Cancelar", () => closeSheet(), "quiet"));
  sheet.append(cancel);
  const version = sheetRequest;
  let song;
  try {
    song = await api(editorialPath(item.songId));
  } catch (error) {
    if (version !== sheetRequest || expired(error)) return;
    wait.replaceWith(notice(editError(error, "No pudimos cargar la ficha."), true));
    cancel.append(button("Reintentar", () => editorialSheet(origin, item)));
    return;
  }
  if (version !== sheetRequest) return;
  wait.remove();
  cancel.remove();
  if (song.editorial.notes.length > 20) {
    sheet.append(notice("Esta ficha supera el máximo de notas que permite editar la demo.", true),
      actions(button("Cerrar", () => closeSheet(), "quiet")));
    return;
  }
  const artistName = artist(song);
  if (artistName) sheet.append(el("p", artistName, "secondary-text"));
  const form = el("form");
  const fields = el("div", null, "editorial-fields");
  const editors = [];
  let fieldSerial = 0;
  const empty = song.editorial.notes.length === 0;
  const original = JSON.stringify(song.editorial.notes.map(({ text, source }) => ({ text, source })));
  const add = button("Añadir otra nota", () => appendNote({ text: "", source: "" }, true));
  form.append(fields, actions(add));
  const read = () => editors.map(({ text, source }) => ({ text: text.value, source: source.value }));
  const isDirty = () => {
    const notes = read();
    return !(empty && notes.length === 1 && !notes[0].text && !notes[0].source) && JSON.stringify(notes) !== original;
  };

  function appendNote(note, focus = false) {
    const id = ++fieldSerial;
    const group = el("fieldset", null, "editorial-note");
    const legend = el("legend", "Nota " + (editors.length + 1));
    const text = el("textarea");
    const source = el("input");
    source.type = "text";
    text.rows = 4;
    text.id = "editorial-text-" + id;
    source.id = "editorial-source-" + id;
    text.required = source.required = true;
    text.value = note.text;
    source.value = note.source;
    const textLabel = el("label", "Texto (1–1000 caracteres)");
    const sourceLabel = el("label", "Fuente (1–200 caracteres)");
    textLabel.htmlFor = text.id;
    sourceLabel.htmlFor = source.id;
    const entry = { text, source, legend };
    group.append(legend, textLabel, text, sourceLabel, source);
    if (focus) {
      group.append(actions(button("Quitar nota nueva", () => {
        editors.splice(editors.indexOf(entry), 1);
        group.remove();
        editors.forEach((editor, i) => { editor.legend.textContent = "Nota " + (i + 1); });
        add.disabled = false;
        add.focus();
      }, "quiet compact")));
    }
    fields.append(group);
    editors.push(entry);
    add.disabled = editors.length >= 20;
    if (focus) text.focus();
  }

  for (const note of empty ? [{ text: "", source: "" }] : song.editorial.notes) appendNote(note);
  const discard = el("div", null, "discard-prompt");
  discard.hidden = true;
  discard.append(notice("Hay cambios sin guardar en esta ficha."));
  let leave = () => closeSheet();
  const stay = button("Seguir editando", () => {
    discard.hidden = true;
    form.hidden = false;
    editors[0].text.focus();
  }, "primary");
  discard.append(actions(stay, button("Descartar cambios", () => leave(), "danger-outline")));

  function tryLeave(onDiscard = () => closeSheet()) {
    if (!isDirty()) return onDiscard();
    leave = onDiscard;
    form.hidden = true;
    discard.hidden = false;
    stay.focus();
  }

  dirtyEditor = { isDirty, tryLeave, hash: location.hash };
  sheetDismiss = () => discard.hidden ? tryLeave() : stay.click();
  managementForm(form, {
    label: "Guardar nota",
    pending: "Guardando…",
    cancel: () => tryLeave(),
    fallback: "No pudimos confirmar el guardado. Tus cambios siguen en el formulario.",
    request: () => {
      const notes = read().map(({ text, source }) => ({ text: text.trim(), source: source.trim() }));
      const invalid = notes.findIndex(({ text, source }) => !text || [...text].length > 1000 ||
        !source || [...source].length > 200);
      if (invalid >= 0) {
        const text = notes[invalid].text;
        (!text || [...text].length > 1000 ? editors[invalid].text : editors[invalid].source).focus();
        throw new Error("Revisa el texto o la fuente de la nota " + (invalid + 1) + ".");
      }
      return () => api(editorialPath(song.songId), { method: "PATCH", body: { notes } });
    },
    success: () => finishManagement("Notas guardadas en «" + song.title + "»."),
  });
  sheet.append(form, discard);
}

get("notification-link").addEventListener("click", resetNotification);
document.querySelector(".skip").addEventListener("click", event => {
  event.preventDefault();
  get("main").focus();
});
window.addEventListener("beforeunload", event => {
  if (dirtyEditor?.isDirty()) {
    event.preventDefault();
    event.returnValue = "";
  }
});
window.addEventListener("hashchange", () => {
  if (dirtyEditor?.isDirty() && location.hash !== dirtyEditor.hash) {
    const destination = location.hash;
    history.replaceState(null, "", "/" + dirtyEditor.hash);
    dirtyEditor.tryLeave(() => {
      closeSheet({ restore: false });
      if (destination) location.hash = destination;
      else {
        history.replaceState(null, "", "/");
        resetNotification();
        renderRoute({ focus: true });
      }
    });
    return;
  }
  closeSheet({ restore: false });
  resetNotification();
  renderRoute({ focus: true });
});
restoreSession();
