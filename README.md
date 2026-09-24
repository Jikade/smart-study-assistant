# Smart Study Assistant Frontend

Frontend SPA responsive cho backend FastAPI tại:

- Backend: https://github.com/Jikade/smart-study-assistant-backend
- API mặc định: `http://127.0.0.1:8000/api/v1`
- Frontend dev: `http://127.0.0.1:5173`

## Thiết kế

Giao diện lấy cảm hứng từ phong cách editorial/playful của `moneyincheck.org`: typography lớn, khối màu pastel, vật thể/nhân vật nổi, chuyển động nền, parallax, hover tilt, scroll reveal, page transition và các section kể chuyện. Không sao chép logo, text, hình ảnh hay tài sản độc quyền của website tham khảo.

Animation được làm bằng CSS + JavaScript thuần, không cần framework animation.

## Công nghệ

- HTML5
- CSS3 responsive
- JavaScript ES Modules
- Fetch API
- LocalStorage cho access/refresh token và UI preferences
- Không cần npm dependency để chạy

## Chạy local

### 1. Chạy backend

Từ repo backend:

```powershell
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Kiểm tra:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/api/v1/health
```

### 2. Chạy frontend

```powershell
cd smart-study-assistant-frontend
python -m http.server 5173
```

Mở:

```text
http://127.0.0.1:5173
```

Hoặc:

```powershell
npm run dev
```

`npm run dev` ở đây chỉ gọi Python HTTP server, không cài dependency.

## Cấu hình API

File `config.js`:

```js
window.__SSA_CONFIG__ = {
  API_BASE_URL: localStorage.getItem('ssa_api_base') || 'http://127.0.0.1:8000/api/v1',
  MEDIA_BASE_URL: localStorage.getItem('ssa_media_base') || 'http://127.0.0.1:8000'
};
```

Đổi backend runtime trực tiếp trong DevTools:

```js
localStorage.setItem('ssa_api_base', 'https://api.example.com/api/v1');
localStorage.setItem('ssa_media_base', 'https://api.example.com');
location.reload();
```

## CORS backend

Frontend port 5173 phải nằm trong `CORS_ORIGINS` của backend. Cấu hình development phù hợp:

```env
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://127.0.0.1:5173"]
```

Nếu backend chỉ có `localhost:5173` nhưng bạn mở frontend bằng `127.0.0.1:5173`, browser xem đó là origin khác. Thêm cả hai origin để tránh lỗi CORS.

## Authentication

`src/api.js`:

1. Lưu `access_token` và `refresh_token` sau login/register.
2. Tự thêm `Authorization: Bearer ...`.
3. Khi endpoint trả `401`, client gọi `/auth/refresh` đúng một lần.
4. Refresh token rotation trả token pair mới và được lưu lại.
5. Nếu refresh thất bại, local auth bị xóa và UI quay về landing/login.

## 59 endpoint được map

`src/api.js` chứa `ENDPOINT_CATALOG` đúng 59 endpoint `/api/v1`, chia theo:

- Health: 1
- Auth: 6
- Users: 1
- Subjects: 5
- Documents: 7
- Chat: 4
- Quizzes: 11
- Flashcards: 6
- Study plans: 4
- Analytics: 4
- Gamification: 1
- Community: 5
- Exports: 2
- Notifications: 2

Trong app, mở `Developer` từ sidebar card để xem toàn bộ map method/path/JWT.

## Màn hình

- Landing / Login / Register
- Dashboard
- Subjects
- Documents + upload/process/embed/chunks/delete
- RAG Chat + citations
- Quizzes + AI modes + manual JSON authoring + attempt + submit
- Flashcard decks + due review + rating 0–3 + response time
- Study plans + task status
- Analytics: topic mastery, weak topics, recommendations, spaced study plan
- Gamification trên dashboard
- Community: publish/like/save/fork
- Exports: PDF/DOCX job
- Notifications
- Profile
- Developer endpoint coverage

## Responsive

Breakpoints chính:

- Desktop: > 1180px
- Laptop/tablet landscape: <= 1180px
- Tablet: <= 860px
- Mobile: <= 580px

Sidebar chuyển thành drawer trên tablet/mobile. Tables có horizontal scroll thay vì phá layout. Grid 4→2→1 cột. Chat và analytics chuyển sang single-column.

## Accessibility / motion

Có hỗ trợ `prefers-reduced-motion: reduce` để tắt animation gần như hoàn toàn.

## Syntax check

```powershell
npm run check
```

Kiểm tra ES syntax cho:

- `src/api.js`
- `src/state.js`
- `src/ui.js`
- `src/views.js`
- `src/app.js`

## Lưu ý backend thực tế

- AI quiz / AI flashcard cần AI provider hoạt động; backend có thể trả `503/422` nếu model chưa cấu hình hoặc output model không hợp lệ.
- Embed yêu cầu document trạng thái `READY`.
- Chat RAG có thể dùng vector similarity hoặc fallback PostgreSQL FTS theo backend.
- Community GET posts là public; các action like/save/fork cần đăng nhập.
- Export `file_url` được ghép với `MEDIA_BASE_URL`.
## Responsive sidebar behavior

- Desktop (>1320px): sidebar supports expanded/collapsed mode and remembers the choice in localStorage.
- Laptop / iPad landscape (861–1320px): compact 88px rail; the top-bar menu opens a full sidebar overlay without shifting the main content.
- Mobile (<=860px): off-canvas drawer with backdrop.
- The sidebar body has its own vertical scrollbar, so navigation, API card, profile and logout always remain reachable on short screens.



### V3 fixes
- Long document names containing underscores now wrap inside dashboard continue cards.
- Avatar URL is rendered in sidebar, topbar and profile; profile save re-fetches `/auth/me` after PATCH.
- AI quiz generation failures now show HTTP status and backend `detail`, and log structured diagnostics to the browser console.
