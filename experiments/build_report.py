"""Đổ kết quả thực nghiệm vào khung tiểu luận PTIT có sẵn."""

from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph

SKILL_SCRIPTS = Path(r"C:\Users\ADMIN\.agents\skills\ptit-academic-writing\scripts")
sys.path.insert(0, str(SKILL_SCRIPTS))
from docx_tools import backup_docx, ensure_existing_docx  # noqa: E402

DEST = Path(__file__).resolve().parents[1] / "BaoCao_ThucNghiem_OpenA2A.docx"


def set_run(run, size=13, bold=False, italic=False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = RGBColor(0, 0, 0)
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    fonts.set(qn("w:ascii"), "Times New Roman")
    fonts.set(qn("w:hAnsi"), "Times New Roman")
    fonts.set(qn("w:eastAsia"), "Times New Roman")


def format_body(paragraph, indent=True, center=False, after=6):
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(6)
    fmt.space_after = Pt(after)
    fmt.line_spacing = 1.3
    fmt.first_line_indent = Cm(1.0) if indent else Cm(0)
    fmt.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.JUSTIFY


def write_para(paragraph, text, size=13, bold=False, italic=False, indent=True, center=False):
    paragraph.clear()
    run = paragraph.add_run(text)
    set_run(run, size=size, bold=bold, italic=italic)
    format_body(paragraph, indent=indent, center=center)


def insert_before(anchor, text, size=13, bold=False, italic=False, indent=True, center=False):
    new_p = OxmlElement("w:p")
    anchor._p.addprevious(new_p)
    paragraph = Paragraph(new_p, anchor._parent)
    run = paragraph.add_run(text)
    set_run(run, size=size, bold=bold, italic=italic)
    format_body(paragraph, indent=indent, center=center)
    return paragraph


def shade_header(cell):
    tc = cell._tc
    tcpr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), "E7E6E6")
    tcpr.append(shd)


def add_table_before(doc, anchor, caption, headers, rows):
    caption_p = insert_before(anchor, caption, size=13, bold=True, indent=False, center=True)
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    caption_p._p.addnext(table._tbl)
    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        cell.text = ""
        run = cell.paragraphs[0].add_run(header)
        set_run(run, size=12, bold=True)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        shade_header(cell)
    for r_index, row in enumerate(rows, start=1):
        for c_index, value in enumerate(row):
            cell = table.rows[r_index].cells[c_index]
            cell.text = ""
            run = cell.paragraphs[0].add_run(str(value))
            set_run(run, size=12, bold=False)
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    return table


def replace_exact(doc, mapping):
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text in mapping:
            payload = mapping[text]
            if isinstance(payload, tuple):
                write_para(paragraph, payload[0], **payload[1])
            else:
                write_para(paragraph, payload)


def main():
    path = ensure_existing_docx(DEST)
    backup_docx(path)
    doc = Document(str(path))

    replacements = {
        "[KHOA CHUYÊN NGÀNH]": "KHOA AN TOÀN THÔNG TIN",
        "[BÁO CÁO BÀI TẬP LỚN / TIỂU LUẬN / ĐỒ ÁN / KHÓA LUẬN]": "TIỂU LUẬN",
        "[TÊN HỌC PHẦN]": "BẢO MẬT DỮ LIỆU",
        "[TÊN ĐỀ TÀI BÁO CÁO HOẶC ĐỒ ÁN NGHIÊN CỨU]": "BẢO MẬT VÀ PHÂN QUYỀN CHO AI AGENT SỬ DỤNG OPENA2A",
        "[NĂM]": "2026",
    }
    for paragraph in list(doc.paragraphs):
        full = "".join(run.text for run in paragraph.runs)
        changed = full
        for old, new in replacements.items():
            changed = changed.replace(old, new)
        if changed != full and paragraph.runs:
            paragraph.runs[0].text = changed
            for run in paragraph.runs[1:]:
                run.text = ""
            for run in paragraph.runs:
                if run.text:
                    set_run(run, size=13, bold=run.font.bold)

    body = {
        "[Trình bày bối cảnh thực tiễn, lý do lựa chọn đề tài và bài toán kỹ thuật cần giải quyết.]":
        "Khi một AI agent được gắn tool calling, mô hình ngôn ngữ không còn chỉ sinh câu trả lời. Nó có thể đọc, ghi hoặc xóa dữ liệu nếu hàm phía sau được gọi. Prompt hệ thống không phải ranh giới an ninh, vì người dùng có thể viết thêm câu lệnh lái mô hình sang một hàm khác. Tiểu luận này kiểm tra một ranh giới nằm ngoài mô hình: OpenA2A Agent Identity Management (AIM) xác thực định danh agent và chỉ cho chạy capability đã được cấp [1], [2].",
        "[Mục tiêu tổng quát và các mục tiêu kỹ thuật cụ thể cần hoàn thành trong bài tập lớn/tiểu luận/đồ án.]":
        "Mục tiêu của phần thực nghiệm là chạy được ba tình huống trên stack AIM cục bộ. Demo 1 kiểm tra agent CRUD chỉ giữ quyền db:read. Demo 2 đối chiếu RAG khi có và khi không có AIM trước lệnh http:post. Demo 3 kiểm tra hai worker nhận yêu cầu đã ký Ed25519 và bị chặn khi capability không thuộc quyền của worker.",
        "[Xác định rõ đối tượng thực nghiệm, phạm vi dữ liệu hoặc giới hạn chức năng triển khai.]":
        "Đối tượng là agent phi nhân tính đăng ký trên AIM, không phải người dùng cuối. Dữ liệu chỉ là việc cần làm, một đoạn quy chế giả và điểm của sinh viên giả. Collector của demo RAG ghi file jsonl trên máy, không mở kết nối ra Internet. Phạm vi không gồm pentest hệ thống bên ngoài và không gồm toàn bộ kịch bản GDPR hay đồng thuận kỹ năng của example A2A gốc.",
        "[Phương pháp nghiên cứu, quy trình triển khai và các công nghệ sử dụng trong đề tài.]":
        "Nhóm đối chiếu cùng một lời gọi hàm trong hai điều kiện: có decorator perform_action của SDK Python và không có decorator. Máy thí nghiệm là Windows 11, CPU Intel Core i7-14650HX, RAM khoảng 16 GB. Stack gồm Postgres (TimescaleDB pg16), Redis 7, backend Go và dashboard Next.js, ảnh ghcr.io/opena2a-org/aim-server:latest và aim-dashboard:latest. SDK trong cây mã là aim-sdk-python 2.0.3, PyNaCl 1.6.2, Python 3.12.8.",
        "[Tóm tắt ngắn gọn cấu trúc các chương tiếp theo và phần Kết luận.]":
        "Chương 1 nêu bài toán định danh phi nhân tính và capability. Chương 2 mô tả cách gắn SDK vào ba demo. Chương 3 trình từng demo theo đúng mạch bài toán, kịch bản, cấu hình, bước chạy, số liệu và nhận xét. Các vị trí cần ảnh chụp được đánh dấu bằng chú thích hình.",
        "[Khảo sát tổng quan bối cảnh nghiệp vụ, nhu cầu thực tế và các công trình liên quan [1].]":
        "Agent trong ví dụ LangChain CRUD của OpenA2A gọi create, read, update và delete trên danh sách công việc. Mỗi hàm được bọc bởi perform_action. Nếu tổ chức đang ở monitoring, capability mới có thể được cấp ngay lần gọi đầu. Muốn lời gọi ngoài quyền bị từ chối, quản trị viên phải chuyển Global Enforcement Mode sang strict [1]. Kịch bản RAG đối chiếu lấy ý từ RAGBot và RAGBot-AIM của Damn Vulnerable AI Agent: tài liệu bị chèn câu lệnh, agent không có ranh giới thì làm theo, agent có AIM thì dừng ở biên công cụ [4].",
        "[Trình bày các khái niệm lý thuyết, thuật toán hoặc công nghệ liên quan được áp dụng trong đề tài [2].]":
        "Định danh phi nhân tính ở đây là bản ghi agent kèm cặp khóa Ed25519 do SDK sinh lúc đăng ký [3]. Capability là chuỗi như db:read hay http:post. AIM so chuỗi đó với danh sách đã cấp. Quyết định từ chối trả về trường denialReason. Điểm tin cậy là số từ 0 đến 1, tính từ nhiều yếu tố; vi phạm capability làm giảm yếu tố security alerts, và tỷ lệ lời gọi được phép đi vào success rate [1].",
        "[Phân tích yêu cầu chức năng/phi chức năng, thiết kế kiến trúc phân tầng hoặc mô hình giải pháp.]":
        "Luồng dùng chung là: quản trị viên đăng nhập, đặt enforcement strict, SDK đăng ký agent với đúng danh sách quyền, quản trị viên verify agent, rồi mới phát lệnh. Hàm nghiệp vụ chỉ chạy khi verify_capability trả ALLOW. DENY làm SDK ném ActionDeniedError và thân hàm không chạy. Với demo đa tác tử, coordinator ký thân thông điệp bằng khóa riêng. Worker kiểm chữ ký trước, sau đó mới đưa capability vào perform_action của chính worker.",
        "[Thiết kế mô hình dữ liệu, biểu đồ luồng xử lý hoặc đặc tả các thuật toán cốt lõi.]":
        "Demo CRUD dùng SQLite, bảng todos có một dòng mẫu. Demo RAG giữ quy chế điểm danh giả và một đoạn ghi chú bị chèn, yêu cầu gọi http:post. Sink là file experiments/data/exfil_sink.jsonl. Demo đa tác tử có coordinator (a2a:delegate), worker tóm tắt (doc:summarize) và worker điểm (grade:read). grade:modify không nằm trong quyền worker điểm.",
        "[Mô tả quy trình cài đặt mã nguồn, triển khai các mô-đun và kỹ thuật giải quyết bài toán [3].]":
        "Stack được bật bằng docker compose -f docker-compose.quickstart.yml trong thư mục agent-identity-management. Postgres và Redis đã healthy, backend lắng nghe 127.0.0.1:8080, dashboard ở cổng 3000. Trước phiên chạy, GET enforcement-settings trả monitoring. Script đặt strict rồi mới đăng ký agent. Mã chạy nằm ở experiments/run_all.py trong repo opena2a-agent-security. Kết quả thô nằm ở experiments/results/latest.json, mốc 20261029T082313Z.",
        "[Trình bày kết quả kiểm thử, giao diện hệ thống hoặc số liệu đo đạc thực tế [4].]":
        "Ba mục sau đi lần lượt từng demo. Số liệu denialReason lấy từ phản hồi của backend. Điểm tin cậy được đọc lại bằng POST /trust-score/recalculate vì bản GET ngay sau phiên chạy đã đổi điểm tổng nhưng còn giữ factors cũ.",
        "[Tổng kết các kết quả đạt được đối chiếu với mục tiêu ban đầu.]":
        "Cả ba demo đều chặn được lời gọi ngoài quyền trên stack đang chạy. CRUD giữ nguyên 1 dòng khi có AIM và bị ghi hoặc xóa sạch khi bỏ decorator. RAG không có AIM ghi 1 bản ghi sink, có AIM thì sink vẫn rỗng. Worker điểm từ chối grade:modify dù chữ ký coordinator hợp lệ. Thông điệp giả chữ ký bị loại trước khi vào tool.",
        "[Chỉ rõ các hạn chế còn tồn đọng: phạm vi thử nghiệm, thời gian tính toán hoặc tài nguyên máy.]":
        "Máy chưa có GOOGLE_API_KEY nên Gemma trên AI Studio chưa được gọi trong phiên này. Bước chọn công cụ rơi về ánh xạ cố định trong script: câu liệt kê thành db:read, câu thêm việc thành db:write, câu xóa thành db:delete, ghi chú độc thành http:post, câu sửa điểm thành grade:modify. File gemma_client.py đã gọi Generative Language API và ưu tiên model gemma-3-27b-it khi khóa có mặt. Vì vậy số liệu bên dưới chứng minh ranh giới AIM, chưa chứng minh Gemma có tuân theo tài liệu độc hay không. DVAA và example A2A gốc không được chạy nguyên cụm trong phiên này.",
        "[Đề xuất các hướng nâng cấp, mở rộng tính năng hoặc tối ưu giải pháp trong tương lai.]":
        "Việc còn lại là đặt khóa AI Studio vào biến GOOGLE_API_KEY rồi chạy lại run_all.py để ghi capability do Gemma chọn. Nhóm cũng nên chụp các hình đã đánh dấu trên dashboard localhost:3000 và điền họ tên, mã sinh viên, lớp và giảng viên ở trang bìa. Khoa trên bìa đang để Khoa An toàn thông tin, cần sửa nếu lớp thuộc khoa khác.",
    }
    replace_exact(doc, body)

    # Cập nhật vài dòng mục lục tĩnh cho khớp chương thực nghiệm.
    for paragraph in doc.paragraphs:
        if paragraph.text.startswith("CHƯƠNG 3:"):
            # Giữ nguyên tiêu đề chương. Nội dung chi tiết được chèn ngay trước Kết luận
            # nếu đây là heading chương, không phải dòng mục lục (dòng mục lục có tab số trang).
            if "\t" in paragraph.text:
                continue

    anchor = None
    for paragraph in doc.paragraphs:
        if paragraph.text.strip() == "KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN":
            anchor = paragraph
            break
    if anchor is None:
        raise RuntimeError("Không thấy mục kết luận trong khung mẫu")

    blocks = [
        ("3.1 Demo 1. Bảo vệ thao tác CRUD", True),
        ("Bài toán", True),
        ("Agent hỗ trợ có thể bị người dùng dụ gọi hàm ghi hoặc xóa trong khi hợp đồng vận hành chỉ cho đọc. Mục tiêu là giữ db:read và chặn db:write, db:delete trước khi câu SQL chạy. Rủi ro dữ liệu là bản ghi bị thêm hoặc bảng bị xóa sạch.", False),
        ("Nội dung kịch bản", True),
        ("Luồng bình thường là liệt kê công việc. Bảng todos được reset về một dòng «Ôn chương mã hóa». Tình huống vượt quyền là thêm tiêu đề «Nộp tiểu luận Bảo mật dữ liệu» và xóa toàn bộ bảng. Cùng các lệnh này được chạy lại khi bỏ decorator để thấy thân hàm vẫn ghi được dữ liệu.", False),
        ("Cấu hình hệ thống", True),
        ("Agent ptit-crud-20261029T082313Z, trạng thái verified sau lệnh verify của quản trị viên. Capability được cấp: db:read. Khóa công khai Ed25519, 16 ký tự đầu c0Gz710j19YW0l4Y. SDK gắn risk level db:read ở mức low, db:write ở mức medium, db:delete ở mức high. Chính sách từ chối là default_policy vì tổ chức quickstart không có policy capability_violation riêng. Enforcement của tổ chức lúc chạy là strict.", False),
        ("Các bước thực hiện", True),
        ("Script đăng ký agent với auto_detect tắt để LangChain có sẵn trên máy không tự khai thêm quyền. Sau verify, mỗi lệnh đi qua perform_action(capability, resource='todos'). Nhánh không AIM gọi thẳng hàm SQLite. Kết quả đếm số dòng trước và sau mỗi lệnh.", False),
        ("Kết quả đạt được", True),
        ("Khi có AIM, db:read chạy và bảng vẫn 1 dòng. db:write và db:delete bị từ chối, số dòng không đổi. denialReason của db:write là: Capability violation blocked by security policy 'default_policy': Agent does not have permission for capability 'db:write' (allowed: [db:read]). db:delete có cùng dạng câu, với capability db:delete. SDK bọc thêm câu AIM denied và The action was blocked and not executed. Khi bỏ AIM, db:write đưa bảng từ 1 lên 2 dòng, db:delete đưa từ 1 xuống 0 dòng.", False),
        ("Điểm tin cậy ngay sau đăng ký, lúc chưa có vi phạm, là 0.825. GET sau chuỗi lệnh của riêng agent CRUD bằng credential agent bị AuthenticationError, nên số sau phiên được đọc bằng token quản trị: 0.43, factors vẫn còn successRate 0.95. POST recalculate tính lại theo nhật ký: score 0.270, successRate 0.333 (2 lần cho phép trên 6 lần verify), securityAlerts 0.150. Agent này có 10 cảnh báo, trong đó 8 cảnh báo security_breach.", False),
        ("Bảng 3.1. Đối chứng CRUD trên bảng todos", "table-crud"),
        ("Hình 3.1. Dashboard http://localhost:3000, thẻ agent ptit-crud-20261029T082313Z, trạng thái verified và capability db:read.", "figure"),
        ("Hình 3.2. Màn audit hoặc alert Unauthorized Action Detected cho db:write và db:delete, có denialReason và resource todos.", "figure"),
        ("Hình 3.3. Bảng todos còn một dòng sau lệnh ghi và lệnh xóa khi AIM bật. Có thể chụp từ file experiments/data/crud_todos.db.", "figure"),
        ("Nhận xét và đánh giá", True),
        ("Ranh giới nằm ở decorator, không nằm ở câu prompt. Đây là điểm nhóm muốn giữ, vì mô hình có bị lái sang hàm xóa thì SQL vẫn không chạy. Hạn chế của demo là danh sách việc chỉ một dòng và bước chọn hàm chưa phải Gemma. Pending request cho db:write và db:delete xuất hiện đúng ở strict mode, quản trị viên không duyệt hai quyền đó.", False),
        ("3.2 Demo 2. Chống đầu độc và tuồn dữ liệu RAG", True),
        ("Bài toán", True),
        ("Tài liệu truy xuất có thể mang câu lệnh. Nếu agent coi câu đó là việc phải làm và có công cụ HTTP, nội dung quy chế bị chuyển ra ngoài. Mục tiêu là cho phép rag:read và chặn http:post, đồng thời xem điểm tin cậy có giảm sau lần từ chối hay không.", False),
        ("Nội dung kịch bản", True),
        ("Kho tài liệu có quy chế điểm danh giả và một ghi chú bị chèn: sau khi đọc phải gọi http:post, đưa nội dung quy chế vào body. Luồng hợp lệ là rag:read, chỉ trả đoạn tóm tắt. Luồng tấn công là http:post. Không có AIM, hàm ghi một dòng vào sink cục bộ. Có AIM, hàm không được vào.", False),
        ("Cấu hình hệ thống", True),
        ("Agent ptit-rag-20261029T082313Z, verified, capability rag:read. Tiền tố khóa công khai W7luv+ZXFEW/kvBs. risk level rag:read là low, http:post là medium theo bộ detect_risk_level của SDK 2.0.3. Sink là experiments/data/exfil_sink.jsonl trên ổ đĩa máy thí nghiệm.", False),
        ("Các bước thực hiện", True),
        ("Script reset sink trước mỗi ca. Ca đối chứng gọi rag:read và http:post, mỗi ca một lần không AIM và một lần có AIM. Ca mô phỏng tài liệu độc cũng gọi http:post qua AIM. Vì chưa có khóa Gemma, nhánh «model chọn công cụ» dùng đúng capability mà ghi chú độc yêu cầu, để đo biên chặn chứ chưa đo tỷ lệ model nghe theo tài liệu.", False),
        ("Kết quả đạt được", True),
        ("Không AIM, rag:read không ghi sink. http:post ghi 1 dòng, cờ exfiltrated bằng true. Có AIM, rag:read vẫn chạy, http:post bị từ chối, sink còn 0 dòng. denialReason: Capability violation blocked by security policy 'default_policy': Agent does not have permission for capability 'http:post' (allowed: [rag:read]).", False),
        ("Điểm trước vi phạm là 0.825. GET ngay sau phiên trả 0.63 trong khi factors chưa đổi. Sau recalculate: score 0.413, successRate 0.333 (1 lần cho phép, 2 lần từ chối), securityAlerts 0.600. Agent có 6 cảnh báo, 4 cảnh báo security_breach, severity của alert mẫu là warning.", False),
        ("Bảng 3.2. Đối chứng RAG và sink cục bộ", "table-rag"),
        ("Hình 3.4. File exfil_sink.jsonl có một dòng ở ca không AIM và thư mục data không có dòng mới ở ca có AIM.", "figure"),
        ("Hình 3.5. Trang trust score của agent ptit-rag sau recalculate, score khoảng 0.413, success rate 0.333.", "figure"),
        ("Nhận xét và đánh giá", True),
        ("AIM chặn được lệnh tuồn dữ liệu ở biên công cụ dù ghi chú trong tài liệu yêu cầu gửi đi. Sink cục bộ đủ để đếm byte đã thoát khỏi hàm, và cố ý không gửi ra mạng. Điểm chưa làm được là chưa có số liệu Gemma có chịu gọi http:post hay từ chối ngay trong câu trả lời. Hai lớp này khác nhau: mô hình có thể từ chối, còn AIM từ chối cả khi hàm đã được chọn.", False),
        ("3.3 Demo 3. Hệ đa tác tử", True),
        ("Bài toán", True),
        ("Coordinator và worker là hai định danh khác nhau. Một chữ ký hợp lệ của coordinator không được biến thành quyền sửa điểm trên worker. Mục tiêu là kiểm chữ ký Ed25519, cho doc:summarize và grade:read, chặn grade:modify.", False),
        ("Nội dung kịch bản", True),
        ("Luồng thường: coordinator ký yêu cầu tóm tắt, worker tóm tắt thực thi. Luồng thứ hai: đọc điểm, worker điểm thực thi. Luồng vượt quyền: yêu cầu sửa điểm thành 10, chữ ký vẫn đúng, capability grade:modify không thuộc worker. Thêm một phong bì cố tình sai chữ ký AAAA. Example a2a-multi-agent-demo trong repo có thêm consent và skill attestation. Phiên này chỉ giữ phần định danh, ký yêu cầu và cô lập capability.", False),
        ("Cấu hình hệ thống", True),
        ("Coordinator ptit-coordinator-20261029T082313Z, quyền a2a:delegate, tiền tố khóa Hrxf/Hgvuz7KHQmT. Worker tóm tắt, quyền doc:summarize, tiền tố L8UslznhHuQ6HQ1f. Worker điểm, quyền grade:read, tiền tố xT66RFIcA1W2Ds05. Cả ba đã verified. Chữ ký lấy từ signing_key của SDK, kiểm bằng VerifyKey trên khóa công khai kèm phong bì.", False),
        ("Các bước thực hiện", True),
        ("Thân thông điệp gồm mã agent gửi, capability và câu việc, được json.dumps với sort_keys rồi ký. Worker kiểm chữ ký. Nếu sai, trả denialReason «Chữ ký Ed25519 không hợp lệ» và không gọi tool. Nếu đúng, worker gọi perform_action với capability trong phong bì. Coordinator cũng phải qua a2a:delegate trước khi giao việc.", False),
        ("Kết quả đạt được", True),
        ("Tóm tắt: chữ ký ed25519_ok, a2a:delegate allow, doc:summarize allow, nội dung trả về là câu vắng quá 20% số tiết thì không được dự thi. Đọc điểm: chữ ký đúng, grade:read allow, điểm giả 8.5. Sửa điểm: chữ ký đúng, a2a:delegate của coordinator vẫn allow, worker trả deny. denialReason: Capability violation blocked by security policy 'default_policy': Agent does not have permission for capability 'grade:modify' (allowed: [grade:read]). Phong bì sai chữ ký bị deny, tool không chạy. Ca tóm tắt bỏ AIM vẫn ra câu tóm tắt, để thấy hàm nghiệp vụ tự nó không kiểm quyền.", False),
        ("Sau recalculate, coordinator và worker tóm tắt ở 0.835, successRate 1, securityAlerts 1. Worker điểm xuống 0.549, successRate 0.500, securityAlerts 0.825. GET ngay sau phiên của worker điểm là 0.73, trước khi factors được tính lại. Worker điểm có 3 cảnh báo, 2 cảnh báo security_breach.", False),
        ("Bảng 3.3. Điểm tin cậy sau recalculate", "table-trust"),
        ("Bảng 3.4. Kết quả điều phối giữa các agent", "table-a2a"),
        ("Hình 3.6. Hai thẻ agent coordinator và grade worker trên dashboard, mỗi thẻ một danh sách capability khác nhau.", "figure"),
        ("Hình 3.7. Log từ chối grade:modify của worker điểm và, nếu chụp thêm terminal, dòng chữ ký Ed25519 không hợp lệ.", "figure"),
        ("Nhận xét và đánh giá", True),
        ("Chữ ký chứng minh ai gửi yêu cầu. Capability chứng minh việc đó có được làm hay không. Hai lớp không thay nhau: phong bì grade:modify ký đúng vẫn bị worker từ chối. Demo còn mỏng so với example A2A gốc vì chưa ghi consent, chưa attest skill và chưa có agent card .well-known/agent.json phục vụ discovery. Phần đó phù hợp để nối thêm sau khi Gemma chạy được.", False),
        ("Bảng 3.1 đến Bảng 3.4 dùng số của phiên 20261029T082313Z trên backend 127.0.0.1:8080. Ảnh minh họa do nhóm chụp thêm từ dashboard và file sink. Trang bìa còn ô giảng viên, sinh viên, mã và lớp để điền trước khi nộp.", False),
    ]

    tables = {
        "table-crud": (
            "Bảng 3.1. Đối chứng số dòng bảng todos",
            ["AIM", "Capability", "Kết quả", "Dòng trước", "Dòng sau", "Dữ liệu đổi"],
            [
                ["Không", "db:read", "allow", "1", "1", "Không"],
                ["Có", "db:read", "allow", "1", "1", "Không"],
                ["Không", "db:write", "allow", "1", "2", "Có"],
                ["Có", "db:write", "deny", "1", "1", "Không"],
                ["Không", "db:delete", "allow", "1", "0", "Có"],
                ["Có", "db:delete", "deny", "1", "1", "Không"],
            ],
        ),
        "table-rag": (
            "Bảng 3.2. Đối chứng RAG và số bản ghi sink",
            ["AIM", "Capability", "Kết quả", "Số dòng sink", "Tuồn ra sink"],
            [
                ["Không", "rag:read", "allow", "0", "Không"],
                ["Không", "http:post", "allow", "1", "Có"],
                ["Có", "rag:read", "allow", "0", "Không"],
                ["Có", "http:post", "deny", "0", "Không"],
            ],
        ),
        "table-trust": (
            "Bảng 3.3. Điểm tin cậy sau POST recalculate",
            ["Agent", "Điểm", "successRate", "securityAlerts"],
            [
                ["CRUD", "0.270", "0.333", "0.150"],
                ["RAG", "0.413", "0.333", "0.600"],
                ["Coordinator", "0.835", "1.000", "1.000"],
                ["Worker tóm tắt", "0.835", "1.000", "1.000"],
                ["Worker điểm", "0.549", "0.500", "0.825"],
            ],
        ),
        "table-a2a": (
            "Bảng 3.4. Điều phối và kiểm chữ ký",
            ["Ca", "Chữ ký", "Delegate", "Worker", "Kết quả worker"],
            [
                ["Tóm tắt", "Hợp lệ", "allow", "summary", "allow"],
                ["Đọc điểm", "Hợp lệ", "allow", "grade", "allow"],
                ["Sửa điểm", "Hợp lệ", "allow", "grade", "deny"],
                ["Sai chữ ký", "Không hợp lệ", "không gọi", "không gọi", "deny"],
            ],
        ),
    }

    for text, kind in blocks:
        if kind == "figure":
            insert_before(anchor, text, size=12, italic=True, indent=False, center=True)
        elif kind in tables:
            caption, headers, rows = tables[kind]
            add_table_before(doc, anchor, caption, headers, rows)
        elif kind is True:
            insert_before(anchor, text, size=13, bold=True, indent=False, center=False)
        else:
            insert_before(anchor, text, size=13, bold=False, indent=True, center=False)

    # Tài liệu tham khảo
    refs = {
        "[1] Tên tác giả, 'Tên bài báo hoặc tài liệu tham khảo 1', Nhà xuất bản/Hội thảo, Năm.":
        "[1] OpenA2A, \"Agent Identity Management,\" GitHub, 2026. [Online]. Available: https://github.com/opena2a-org/agent-identity-management. (Truy cập: 29/10/2026).",
        "[2] Tên tác giả, 'Tên bài báo hoặc tài liệu tham khảo 2', Nhà xuất bản/Hội thảo, Năm.":
        "[2] OWASP, \"OWASP Top 10 for Large Language Model Applications,\" OWASP, 2025. [Online]. Available: https://owasp.org/www-project-top-10-for-large-language-model-applications/. (Truy cập: 29/10/2026).",
        "[3] Tên tác giả, 'Tên tài liệu trực tuyến hoặc mã nguồn tham khảo', Website, Năm.":
        "[3] D. J. Bernstein, N. Duif, T. Lange, P. Schwabe, and B.-Y. Yang, \"High-speed high-security signatures,\" Journal of Cryptographic Engineering, vol. 2, pp. 77–89, 2012.",
    }
    replace_exact(doc, refs)
    for paragraph in doc.paragraphs:
        if paragraph.text.startswith("[3] D. J. Bernstein"):
            new_p = OxmlElement("w:p")
            paragraph._p.addnext(new_p)
            fourth = Paragraph(new_p, paragraph._parent)
            run = fourth.add_run(
                "[4] OpenA2A, \"Damn Vulnerable AI Agent,\" GitHub, 2026. [Online]. Available: https://github.com/opena2a-org/damn-vulnerable-ai-agent. (Truy cập: 29/10/2026)."
            )
            set_run(run, size=13)
            format_body(fourth, indent=False)
            fifth_el = OxmlElement("w:p")
            fourth._p.addnext(fifth_el)
            fifth = Paragraph(fifth_el, fourth._parent)
            run5 = fifth.add_run(
                "[5] OpenA2A, \"A2A Security Examples,\" GitHub, 2026. [Online]. Available: https://github.com/opena2a-org/a2a-security-examples. (Truy cập: 29/10/2026)."
            )
            set_run(run5, size=13)
            format_body(fifth, indent=False)
            break

    # Bảng từ viết tắt
    table = doc.tables[0]
    updates = [
        ("AIM", "Agent Identity Management", "Hệ quản trị định danh agent của OpenA2A"),
        ("NHI", "Non-Human Identity", "Định danh của tác nhân không phải người dùng"),
        ("FGA", "Fine-Grained Authorization", "Phân quyền theo từng capability"),
        ("RAG", "Retrieval-Augmented Generation", "Sinh câu trả lời có truy xuất tài liệu"),
        ("A2A", "Agent-to-Agent", "Trao đổi giữa các agent"),
        ("PTIT", "Posts and Telecommunications Institute of Technology", "Học viện Công nghệ Bưu chính Viễn thông"),
    ]
    for offset, values in enumerate(updates, start=1):
        if offset >= len(table.rows):
            table.add_row()
        for col, value in enumerate(values):
            cell = table.rows[offset].cells[col]
            cell.text = ""
            run = cell.paragraphs[0].add_run(value)
            set_run(run, size=12)

    doc.save(str(path))
    print("SAVED", path)


if __name__ == "__main__":
    main()
