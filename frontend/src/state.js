const TOKEN_KEY = 'ssa_auth';
const UI_KEY = 'ssa_ui';

const UI_DEFAULTS = {
  sidebarOpen: false,
  sidebarCollapsed: false,
  selectedSubjectId: null,
};

export const state = {
  auth: loadJson(TOKEN_KEY, null),
  ui: { ...UI_DEFAULTS, ...loadJson(UI_KEY, {}) },
  cache: new Map(),
  currentRoute: location.hash.replace(/^#/, '') || '/',
};

function loadJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export function saveAuth(auth) {
  state.auth = auth;
  if (auth) localStorage.setItem(TOKEN_KEY, JSON.stringify(auth));
  else localStorage.removeItem(TOKEN_KEY);
}

export function saveUi(patch) {
  state.ui = { ...state.ui, ...patch };
  localStorage.setItem(UI_KEY, JSON.stringify(state.ui));
}

export function logoutLocal() {
  saveAuth(null);
  saveUi({ selectedSubjectId: null });
  state.cache.clear();
}

export function isAuthed() {
  return Boolean(state.auth?.access_token);
}
