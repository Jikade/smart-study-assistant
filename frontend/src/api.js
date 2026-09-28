import { saveAuth, logoutLocal, state } from './state.js';

const API_BASE = (window.__SSA_CONFIG__?.API_BASE_URL || 'http://127.0.0.1:8000/api/v1').replace(/\/$/, '');
const MEDIA_BASE = (window.__SSA_CONFIG__?.MEDIA_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

export const ENDPOINT_CATALOG = [
  ['GET','/health',false,'Health'],
  ['POST','/auth/register',false,'Auth'], ['POST','/auth/login',false,'Auth'], ['POST','/auth/login-form',false,'Auth'], ['POST','/auth/refresh',false,'Auth'], ['POST','/auth/logout',false,'Auth'], ['GET','/auth/me',true,'Auth'],
  ['PATCH','/users/me',true,'Users'],
  ['GET','/subjects',true,'Subjects'], ['POST','/subjects',true,'Subjects'], ['GET','/subjects/{subject_id}',true,'Subjects'], ['PATCH','/subjects/{subject_id}',true,'Subjects'], ['DELETE','/subjects/{subject_id}',true,'Subjects'],
  ['GET','/documents',true,'Documents'], ['POST','/documents/upload',true,'Documents'], ['GET','/documents/{document_id}',true,'Documents'], ['POST','/documents/{document_id}/process',true,'Documents'], ['GET','/documents/{document_id}/chunks',true,'Documents'], ['POST','/documents/{document_id}/embed',true,'Documents'], ['DELETE','/documents/{document_id}',true,'Documents'],
  ['GET','/chat/conversations',true,'Chat'], ['POST','/chat/conversations',true,'Chat'], ['GET','/chat/conversations/{conversation_id}/messages',true,'Chat'], ['POST','/chat/conversations/{conversation_id}/ask',true,'Chat'],
  ['GET','/quizzes',true,'Quizzes'], ['POST','/quizzes',true,'Quizzes'], ['POST','/quizzes/generate',true,'Quizzes'], ['POST','/quizzes/generate-v5',true,'Quizzes'], ['POST','/quizzes/generate-v5-preview',true,'Quizzes'], ['POST','/quizzes/generate-weak-topic',true,'Quizzes'], ['POST','/quizzes/generate-adaptive',true,'Quizzes'], ['POST','/quizzes/generate-due',true,'Quizzes'], ['GET','/quizzes/{quiz_id}',true,'Quizzes'], ['POST','/quizzes/{quiz_id}/publish',true,'Quizzes'], ['POST','/quizzes/{quiz_id}/attempts',true,'Quizzes'], ['POST','/quizzes/attempts/{attempt_id}/submit',true,'Quizzes'], ['GET','/quizzes/attempts/{attempt_id}/result',true,'Quizzes'],
  ['GET','/flashcards/decks',true,'Flashcards'], ['POST','/flashcards/decks',true,'Flashcards'], ['POST','/flashcards/decks/generate',true,'Flashcards'], ['GET','/flashcards/decks/{deck_id}',true,'Flashcards'], ['GET','/flashcards/due',true,'Flashcards'], ['POST','/flashcards/{flashcard_id}/review',true,'Flashcards'],
  ['GET','/study-plans',true,'Study plans'], ['POST','/study-plans/generate',true,'Study plans'], ['GET','/study-plans/{plan_id}',true,'Study plans'], ['PATCH','/study-plans/tasks/{task_id}',true,'Study plans'],
  ['GET','/analytics/subjects/{subject_id}/topic-mastery',true,'Analytics'], ['GET','/analytics/subjects/{subject_id}/practice-recommendations',true,'Analytics'], ['GET','/analytics/subjects/{subject_id}/study-plan',true,'Analytics'], ['GET','/analytics/subjects/{subject_id}/weak-topics',true,'Analytics'],
  ['GET','/gamification/me',true,'Gamification'],
  ['GET','/community/posts',false,'Community'], ['POST','/community/posts',true,'Community'], ['POST','/community/posts/{post_id}/like',true,'Community'], ['POST','/community/posts/{post_id}/save',true,'Community'], ['POST','/community/posts/{post_id}/fork',true,'Community'],
  ['POST','/exports',true,'Exports'], ['GET','/exports',true,'Exports'], ['GET','/exports/{export_id}/download',true,'Exports'],
  ['GET','/notifications',true,'Notifications'], ['POST','/notifications/{notification_id}/read',true,'Notifications'],
];

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

let refreshing = null;

async function rawRequest(path, options = {}, allowRefresh = true) {
  const headers = new Headers(options.headers || {});
  const body = options.body;
  if (!(body instanceof FormData) && body != null && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  if (state.auth?.access_token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${state.auth.access_token}`);
  }
  headers.set('Accept', 'application/json');

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (response.status === 401 && allowRefresh && state.auth?.refresh_token && !path.startsWith('/auth/refresh')) {
    try {
      if (!refreshing) refreshing = refreshTokens();
      await refreshing;
      refreshing = null;
      return rawRequest(path, options, false);
    } catch (err) {
      refreshing = null;
      logoutLocal();
      window.dispatchEvent(new CustomEvent('ssa:auth-expired'));
      throw err;
    }
  }

  const contentType = response.headers.get('content-type') || '';
  let data = null;
  if (response.status !== 204) {
    if (contentType.includes('application/json')) data = await response.json().catch(() => null);
    else data = await response.text().catch(() => '');
  }

  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map(x => x?.msg || JSON.stringify(x)).join('; ')
      : detail || data?.message || (typeof data === 'string' && data) || `HTTP ${response.status}`;
    throw new ApiError(message, response.status, data);
  }
  return data;
}

function json(method, path, body, params) {
  const q = params ? `?${new URLSearchParams(Object.entries(params).filter(([,v]) => v !== undefined && v !== null).map(([k,v]) => [k, String(v)])).toString()}` : '';
  return rawRequest(`${path}${q}`, { method, body: body == null ? undefined : JSON.stringify(body) });
}

function query(path, params) { return json('GET', path, null, params); }

async function rawBlob(path, allowRefresh = true) {
  const headers = new Headers();
  if (state.auth?.access_token) headers.set('Authorization', `Bearer ${state.auth.access_token}`);
  const response = await fetch(`${API_BASE}${path}`, { headers });

  if (response.status === 401 && allowRefresh && state.auth?.refresh_token) {
    try {
      if (!refreshing) refreshing = refreshTokens();
      await refreshing;
      refreshing = null;
      return rawBlob(path, false);
    } catch (err) {
      refreshing = null;
      logoutLocal();
      window.dispatchEvent(new CustomEvent('ssa:auth-expired'));
      throw err;
    }
  }

  if (!response.ok) {
    const contentType = response.headers.get('content-type') || '';
    let data = null;
    if (contentType.includes('application/json')) data = await response.json().catch(() => null);
    else data = await response.text().catch(() => '');
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map(x => x?.msg || JSON.stringify(x)).join('; ')
      : detail || data?.message || (typeof data === 'string' && data) || `HTTP ${response.status}`;
    throw new ApiError(message, response.status, data);
  }

  return response.blob();
}

export async function refreshTokens() {
  if (!state.auth?.refresh_token) throw new ApiError('Không có refresh token', 401);
  const pair = await rawRequest('/auth/refresh', { method: 'POST', body: JSON.stringify({ refresh_token: state.auth.refresh_token }), headers: { 'Content-Type': 'application/json' } }, false);
  saveAuth(pair);
  return pair;
}

export const api = {
  baseUrl: API_BASE,
  mediaBase: MEDIA_BASE,
  health: () => query('/health'),
  register: payload => json('POST','/auth/register',payload),
  login: payload => json('POST','/auth/login',payload),
  loginForm: async ({ email, password }) => {
    const form = new URLSearchParams({ username: email, password });
    return rawRequest('/auth/login-form', { method: 'POST', body: form, headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
  },
  me: () => query('/auth/me'),
  logout: refresh_token => json('POST','/auth/logout',{ refresh_token }),
  updateMe: payload => json('PATCH','/users/me',payload),

  listSubjects: params => query('/subjects', params),
  createSubject: payload => json('POST','/subjects',payload),
  getSubject: id => query(`/subjects/${id}`),
  updateSubject: (id,payload) => json('PATCH',`/subjects/${id}`,payload),
  deleteSubject: id => json('DELETE',`/subjects/${id}`),

  listDocuments: params => query('/documents', params),
  uploadDocument: async ({ file, subject_id, process_now = false }) => {
    const form = new FormData(); form.append('file', file);
    if (subject_id) form.append('subject_id', String(subject_id));
    form.append('process_now', String(process_now));
    return rawRequest('/documents/upload', { method: 'POST', body: form });
  },
  getDocument: id => query(`/documents/${id}`),
  processDocument: id => json('POST',`/documents/${id}/process`),
  documentChunks: (id, limit=200) => query(`/documents/${id}/chunks`,{limit}),
  embedDocument: (id, force=false) => json('POST',`/documents/${id}/embed`,null,{force}),
  deleteDocument: id => json('DELETE',`/documents/${id}`),

  listConversations: (limit=50) => query('/chat/conversations',{limit}),
  createConversation: payload => json('POST','/chat/conversations',payload),
  messages: id => query(`/chat/conversations/${id}/messages`),
  ask: (id,payload) => json('POST',`/chat/conversations/${id}/ask`,payload),

  listQuizzes: params => query('/quizzes',params),
  createQuiz: payload => json('POST','/quizzes',payload),
  generateQuiz: payload => json('POST','/quizzes/generate',payload),
  generateQuizV5: payload => json('POST','/quizzes/generate-v5',payload),
  previewQuizV5: payload => json('POST','/quizzes/generate-v5-preview',payload),
  generateWeakQuiz: payload => json('POST','/quizzes/generate-weak-topic',payload),
  generateAdaptiveQuiz: payload => json('POST','/quizzes/generate-adaptive',payload),
  generateDueQuiz: payload => json('POST','/quizzes/generate-due',payload),
  getQuiz: id => query(`/quizzes/${id}`),
  publishQuiz: id => json('POST',`/quizzes/${id}/publish`),
  startAttempt: id => json('POST',`/quizzes/${id}/attempts`),
  submitAttempt: (id,answers) => json('POST',`/quizzes/attempts/${id}/submit`,{answers}),
  attemptResult: id => query(`/quizzes/attempts/${id}/result`),

  listDecks: (limit=50) => query('/flashcards/decks',{limit}),
  createDeck: payload => json('POST','/flashcards/decks',payload),
  generateDeck: payload => json('POST','/flashcards/decks/generate',payload),
  getDeck: id => query(`/flashcards/decks/${id}`),
  dueCards: (limit=50) => query('/flashcards/due',{limit}),
  reviewCard: (id,payload) => json('POST',`/flashcards/${id}/review`,payload),

  listStudyPlans: () => query('/study-plans'),
  generateStudyPlan: payload => json('POST','/study-plans/generate',payload),
  getStudyPlan: id => query(`/study-plans/${id}`),
  updateStudyTask: (id,status) => json('PATCH',`/study-plans/tasks/${id}`,{status}),

  topicMastery: id => query(`/analytics/subjects/${id}/topic-mastery`),
  practiceRecommendations: id => query(`/analytics/subjects/${id}/practice-recommendations`),
  analyticsStudyPlan: (id,horizon_days=7) => query(`/analytics/subjects/${id}/study-plan`,{horizon_days}),
  weakTopics: id => query(`/analytics/subjects/${id}/weak-topics`),
  gamification: () => query('/gamification/me'),

  communityPosts: params => query('/community/posts',params),
  publishCommunity: payload => json('POST','/community/posts',payload),
  likePost: id => json('POST',`/community/posts/${id}/like`),
  savePost: id => json('POST',`/community/posts/${id}/save`),
  forkPost: id => json('POST',`/community/posts/${id}/fork`),

  createExport: payload => json('POST','/exports',payload),
  listExports: () => query('/exports'),
  downloadExport: id => rawBlob(`/exports/${id}/download`),
  notifications: unread_only => query('/notifications',{unread_only}),
  markNotificationRead: id => json('POST',`/notifications/${id}/read`),
};
