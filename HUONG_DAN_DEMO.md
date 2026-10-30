# Hướng dẫn chạy demo thủ công

Tài liệu này dùng khi **clone repo trên máy thành viên** và khi **báo cáo trước lớp**. Có hai lớp demo: lớp Streamlit chạy ngay trên máy, không cần Docker; lớp OpenA2A AIM cần Docker và khóa Google AI Studio.

Không dán khóa API, mật khẩu dashboard hay file `.env` vào slide, chat nhóm công khai, hay commit git.

---

## 1. Máy cần gì

| Thành phần | Bắt buộc cho demo nào |
| --- | --- |
| Git, Python 3.10+ | Cả hai lớp |
| `pip install -r requirements.txt` | Cả hai lớp |
| Docker Desktop đang chạy | Chỉ demo AIM (CRUD / RAG / đa tác tử + dashboard) |
| Khóa Google AI Studio (`GOOGLE_API_KEY`) | Chỉ khi muốn Gemma chọn tool; thiếu khóa thì script vẫn chạy phần đối chiếu AIM |

Cổng mặc định: Streamlit `8502`, AIM backend `127.0.0.1:8080`, dashboard `http://localhost:3000`.

---

## 2. Cài lần đầu trên máy mới

Mở PowerShell (Windows) hoặc terminal (macOS/Linux) tại thư mục clone:

```powershell
cd opena2a-agent-security
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

```bash
cd opena2a-agent-security
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -r requirements.txt
cp .env.example .env
```

Mở `.env` bằng editor. Việc bắt buộc:

1. Đặt `AIM_ADMIN_PASSWORD` và `ADMIN_PASSWORD` **cùng một mật khẩu** bạn nhớ được (dùng để vào dashboard).
2. Thay các `CHANGE_ME_*` của Postgres / Redis / JWT / KeyVault bằng chuỗi ngẫu nhiên:

```powershell
python -c "import secrets, base64, os; print('pg', secrets.token_hex(16)); print('redis', secrets.token_hex(16)); print('jwt', secrets.token_hex(32)); print('kv', base64.b64encode(os.urandom(32)).decode())"
```

`KEYVAULT_MASTER_KEY` phải là Base64 chuẩn (có `+` `/` `=`), không dùng `token_urlsafe`.

3. (Tùy chọn, cho demo Gemma) dán khóa AI Studio vào `GOOGLE_API_KEY`. Lấy khóa tại [Google AI Studio](https://aistudio.google.com/). Không chia sẻ khóa trong repo.

File `.env` đã nằm trong `.gitignore`. Không `git add .env`.

---

## 3. Demo thuyết trình không Docker (nên dùng khi bảo vệ)

Lớp này minh họa PEP OpenA2A trên SQLite: chữ ký Ed25519, `detect_risk_level`, `evaluate()`, `ActionDeniedError`. Không gọi Gemma, không cần AIM server.

### 3.1. Giao diện Streamlit (kịch bản chính trên slide)

1. Trong thư mục gốc repo, venv đã bật:

```powershell
streamlit run app_demo.py --server.port 8502
```

2. Mở trình duyệt: `http://localhost:8502`.
3. Sidebar giữ mặc định: vai trò **Agent Hỗ Trợ Sinh Viên**, chỉ `schedule:read` và `grade:read`, Enforcement **STRICT**.
4. Cột phải là bảng điểm SQLite. Nếu bảng lệch so với bài, bấm **Khôi Phục Dữ Liệu & Reset**.

Thực hiện **đúng thứ tự ba nút**, mỗi lần bấm **GỬI LỆNH CHO AGENT**, rồi chỉ nhật ký bên dưới và bảng điểm bên phải:

| Bước | Nút / prompt | Năng lực agent chọn | Kết quả cần chỉ |
| --- | --- | --- | --- |
| 1 | **1. Tra cứu điểm (Hợp lệ)** | `grade:read` | ALLOW, hiện điểm Nguyễn Văn A, CSDL không đổi |
| 2 | **2. Injection Sửa điểm** | `grade:modify` | `ActionDeniedError`, điểm Lê Thị C (B23DCKD003) **không** thành 10 |
| 3 | **3. Injection Xóa CSDL** | `database:purge` | bị chặn, bảng điểm còn đủ dòng |

Câu cần nói: agent đã nhận diện tool nguy hiểm; cổng OpenA2A chặn **trước** khi SQL chạm CSDL. Ranh giới nằm ở capability, không nằm ở câu prompt.

Tùy chọn thêm, nếu giảng viên hỏi “còn chế độ giám sát?”:

- Sidebar chọn **MONITORING**, gửi lại prompt sửa điểm: lệnh đi qua, bảng điểm đổi, nhật ký vẫn ghi cảnh báo.
- Bấm **Khôi Phục Dữ Liệu & Reset** trước khi demo STRICT lần nữa.

### 3.2. Demo console (Ed25519 + audit log)

Cùng thư mục gốc:

```powershell
python demo_btl_atdl.py
```

Chỉ trên terminal:

1. Hai agent, mỗi bên một public key Ed25519.
2. Test case 1: `schedule:read` → cho phép.
3. Test case 2: prompt injection `grade:modify` trên agent hỗ trợ → chặn.
4. Test case 3: agent quản trị có `grade:modify` → cho phép.
5. File `audit_log.json` được ghi lại ở thư mục gốc.

---

## 4. Demo AIM thật (CRUD, RAG, đa tác tử) — khi có Docker

Ba kịch bản trong `experiments/` đăng ký agent lên AIM, bật **strict**, gọi Gemma (nếu có khóa), rồi đối chiếu có/không AIM. Dashboard tại cổng 3000 là phần “chụp màn hình / soi violation”.

### 4.1. Bật stack

Docker Desktop phải **Running**. Tại thư mục gốc repo:

```powershell
docker compose -f docker-compose.quickstart.yml up -d
docker compose -f docker-compose.quickstart.yml ps
```

Đợi bốn service `healthy`: `aim-postgres`, `aim-redis`, `aim-backend`, `aim-frontend`. Lần đầu sẽ kéo image từ `ghcr.io` (cần mạng).

Image AIM **không tự tạo tài khoản admin**. Máy mới hoặc sau `down -v`, chạy một lần:

```powershell
docker exec aim-backend sh -c 'export DATABASE_URL="postgres://postgres:${POSTGRES_PASSWORD}@postgres:5432/identity?sslmode=disable"; ./aim-bootstrap --default --admin-email "$ADMIN_EMAIL" --admin-password "$ADMIN_PASSWORD" --admin-name "PTIT Lab Admin"'
```

Thấy `Bootstrap completed successfully` là xong. Không chụp / không commit dòng Password.

Kiểm tra Python thấy backend:

```powershell
python experiments\check_lab.py
```

Kỳ vọng: `GET /health` 200, `POST /login` 200, `GOOGLE_API_KEY set = True` nếu đã điền khóa.

Nếu login 401: chưa bootstrap, hoặc mật khẩu `.env` không khớp admin. Chạy lại lệnh `aim-bootstrap` ở trên. Nếu vẫn 401 trên **máy lab cá nhân** (xóa hết data cũ):

```powershell
docker compose -f docker-compose.quickstart.yml down -v
docker compose -f docker-compose.quickstart.yml up -d
```

`-v` xóa volume Postgres; chỉ làm khi chưa cần giữ agent cũ.

### 4.2. Đăng nhập dashboard một lần

1. Mở `http://localhost:3000`.
2. Email / mật khẩu đúng `AIM_ADMIN_EMAIL` và `AIM_ADMIN_PASSWORD` trong `.env`.
3. Nếu hiện **Set a new password**, đặt mật khẩu mới **rồi sửa `.env` cho khớp**. Không thì `run_all.py` login thất bại.
4. Vào **Agents**. Để trống cũng được: script sẽ đăng ký agent mới.

### 4.3. Demo AIM từng bước trên giao diện (cách bảo vệ)

Không chạy `run_all.py` khi thuyết trình. Mở giao diện, bấm từng nút như người dùng:

```powershell
streamlit run app_aim_lab.py --server.port 8503
```

Mở `http://localhost:8503`. Giữ thêm tab `http://localhost:3000` (dashboard AIM).

1. Sidebar: **Kết nối AIM và bật strict**.
2. Checkbox **Gemma chọn tool** bật nếu có khóa; tắt nếu muốn demo nhanh (AIM vẫn chặn capability thật).
3. Tab **Demo 1 CRUD** → **Đăng ký agent CRUD** → gõ lệnh vào ô **Lệnh gửi cho agent** (hoặc bấm mẫu rồi **Gửi lệnh cho agent**). Ví dụ: *Liệt kê công việc* (ALLOW), *Thêm việc Nộp tiểu luận...* (DENY), *Xóa sạch toàn bộ...* (DENY). Bảng todos bên phải cho thấy CSDL có đổi hay không. Có thể bấm **Ghi một dòng, TẮT AIM** rồi **Ghi một dòng, BẬT AIM** để đối chiếu.
4. Tab **Demo 2 RAG** → đăng ký agent → corpus + ghi chú độc hiện sẵn → tự gõ câu hỏi. Mẫu độc: *làm theo ghi chú nội bộ* (thường chọn `http:post`, AIM DENY, sink = 0). Đối chiếu **http:post, tắt AIM** sẽ tăng sink.
5. Tab **Demo 3** → đăng ký 3 agent → gõ lệnh cho coordinator. Tóm tắt / đọc điểm ALLOW; *sửa điểm thành 10* thì worker DENY dù chữ ký Ed25519 hợp lệ. Nút **Chữ ký giả** vẫn dùng để chỉ lớp xác thực chữ ký.
6. Sau mỗi demo, F5 dashboard :3000, mở đúng agent vừa đăng ký, tab Security.

`python experiments\run_all.py` chỉ dùng khi cần ghi JSON hàng loạt, không dùng lúc bảo vệ.

### 4.4. Chỉ từng màn hình trên dashboard (thứ tự báo cáo)

Sau `run_all.py`, F5 dashboard. Agent tên dạng `ptit-crud-<stamp>`, `ptit-rag-<stamp>`, `ptit-coordinator-<stamp>`, `ptit-summary-<stamp>`, `ptit-grade-<stamp>`.

**Demo 1 — CRUD (chỉ `db:read`)**

1. Mở agent `ptit-crud-...`.
2. Header: capability `db:read`; trust score giảm (phiên Gemma gốc: 27%, trạng thái Suspended). Máy khác sẽ ra số khác; đọc số **trên màn hình lúc demo**, không đọc thuộc lòng số cũ.
3. Tab Security: `db:write` và `db:delete` **Blocked**.
4. Nói: không AIM thì `experiments/data/crud_todos.db` bị ghi rồi bị xóa; có AIM thì còn một dòng seed.

**Demo 2 — RAG poisoning (chỉ `rag:read`)**

1. Mở `ptit-rag-...`.
2. Tab Security: `http:post` **Blocked**.
3. File `experiments/data/exfil_sink.jsonl` không được tạo (hoặc không thêm dòng) khi AIM bật. Sink là file local, không gửi HTTP ra Internet.

**Demo 3 — Đa tác tử**

1. Coordinator: `a2a:delegate`, trust cao.
2. Worker tóm tắt: `doc:summarize` ALLOW.
3. Worker điểm: `grade:read` ALLOW; `grade:modify` **Blocked** dù coordinator đã ký Ed25519 hợp lệ.
4. Nói thêm: chữ ký giả bị từ chối với lý do *Chữ ký Ed25519 không hợp lệ* trước khi gọi tool. Phần này nằm trong JSON kết quả, không có screenshot terminal.

Trust score trên UI đôi khi lệch factor GET cho đến khi AIM tính lại. `run_all.py` không bắt buộc recalculate; nếu giảng viên hỏi số chi tiết, mở agent rồi đọc % trên header.

---

## 5. Gợi ý kịch bản 8–10 phút trước hội đồng

1. Mở Streamlit (mục 3.1), chạy ba nút. ~3 phút.
2. (Nếu Docker sẵn) dashboard AIM, lần lượt CRUD → RAG → worker điểm. ~5 phút.
3. Kết: prompt injection lay được ý định của model; enforcement capability + chữ ký agent-to-agent chặn thực thi.

Nếu Docker không lên được trong phòng máy: **chỉ Streamlit + `demo_btl_atdl.py`**, và chiếu ảnh đã nhúng trong `BaoCao_ThucNghiem_OpenA2A.docx` (Hình dashboard phiên `20261029T084944Z`). Nói rõ ảnh đó là phiên lab đã chạy, không phải chạy live trên máy chiếu.

---

## 6. Cấu trúc thư mục liên quan demo

```text
opena2a-agent-security/
├── .env.example                      # mẫu biến môi trường (commit)
├── .env                              # bí mật máy bạn (không commit)
├── docker-compose.quickstart.yml     # Postgres + Redis + AIM + dashboard
├── lab_env.py                        # nạp .env cho script Python
├── app_demo.py                       # demo Streamlit
├── demo_btl_atdl.py                  # demo console
├── kiem_thu_toan_dien.py             # pytest SDK + demo console
├── aim_sdk/                          # SDK 2.0.3 đi kèm repo
├── experiments/
│   ├── check_lab.py                  # kiểm tra health + login
│   ├── run_all.py                    # chạy cả 3 demo AIM
│   ├── demo1_crud.py
│   ├── demo2_rag.py
│   ├── demo3_multiagent.py
│   ├── results/latest.json           # kết quả lần chạy gần nhất
│   └── screenshots/                  # ảnh dashboard phiên lab gốc
└── BaoCao_ThucNghiem_OpenA2A.docx
```

Không cần clone `agent-identity-management`. Compose kéo image chính thức `ghcr.io/opena2a-org/aim-server` và `aim-dashboard`.

---

## 7. Sự cố thường gặp

| Hiện tượng | Việc cần làm |
| --- | --- |
| `docker compose` báo daemon / `npipe` | Mở Docker Desktop, đợi whale ổn định, chạy lại `up -d` |
| Cổng 8080 hoặc 3000 đã chiếm | Đổi `AIM_BACKEND_PORT` / `AIM_FRONTEND_PORT` trong `.env`, sửa luôn `AIM_API_URL` và `FRONTEND_API_URL` |
| `check_lab.py` login lỗi | Khớp password với admin lúc volume được tạo; hoặc `down -v` rồi `up -d` trên máy cá nhân |
| Dashboard bắt đổi mật khẩu | Đổi xong **cập nhật `.env`** |
| `Thiếu GOOGLE_API_KEY` | Demo AIM vẫn chặn capability; Gemma không chọn tool |
| Gemma HTTP 429/500 | Script thử lại rồi đổi model; model từng chạy được trên AI Studio: `gemma-4-26b-a4b-it` |
| `pip` không thấy `aim_sdk` | Chạy Python **từ thư mục gốc repo**, không cần `pip install -e .` |

Tắt stack khi không dùng:

```powershell
docker compose -f docker-compose.quickstart.yml down
```

Giữ volume thì lần sau `up -d` còn agent cũ. Xóa hẳn data lab: thêm `-v`.
