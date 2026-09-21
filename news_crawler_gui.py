"""PyQt6 기반 네이버 뉴스 크롤러 GUI.

필요 패키지: pip install PyQt6 requests beautifulsoup4 openpyxl
실행:        python news_crawler_gui.py
크롤링 로직은 news_crawler.py 를 그대로 사용한다.
"""
import csv
import json
import re
import sys
import time

import requests
from PyQt6.QtCore import QDate, QThread, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QDesktopServices, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

import news_crawler as nc

COLUMNS = ["제목", "언론사", "시간", "링크"]
LINK_COL = COLUMNS.index("링크")
# (표시 이름, 오늘 기준 며칠 전부터인지) — -1 은 기간 제한 없음, None 은 직접 지정
PERIODS = [("전체", -1), ("최근 1일", 0), ("최근 1주", 7), ("최근 1개월", 30),
           ("최근 1년", 365), ("직접 지정", None)]
FIELDS = ["title", "press", "date", "posted", "url", "original_url", "snippet",
          "summary", "keywords", "content"]

ACCENT = "#3b63e0"
KEYWORD_COLOR = "#2a4bc4"

STYLE = """
* { font-family: "Malgun Gothic", "Segoe UI", sans-serif; font-size: 10pt; color: #1d2433; }
QMainWindow, QWidget#root { background: #f3f5fa; }

QLabel#title { font-size: 20pt; font-weight: 700; }
QLabel#subtitle { color: #6b7590; }
QLabel#fieldLabel { color: #6b7590; font-weight: 600; }

QFrame#card { background: #ffffff; border: 1px solid #e0e5f0; border-radius: 12px; }
QFrame#card QLabel { background: transparent; }

QLineEdit {
    background: #ffffff; border: 1px solid #d5dbe8; border-radius: 8px; padding: 6px 10px;
    selection-background-color: #cddaff; selection-color: #1d2433;
}
QLineEdit:focus { border: 1px solid #3b63e0; }

QPushButton {
    background: #ffffff; border: 1px solid #d5dbe8; border-radius: 8px; padding: 7px 16px;
}
QPushButton:hover { background: #eef2fc; border-color: #b9c6ee; }
QPushButton:pressed { background: #e2e9fb; }
QPushButton:disabled { color: #aab2c5; background: #f6f7fb; border-color: #e6e9f2; }
QPushButton#primary { background: #3b63e0; border: none; color: #ffffff; font-weight: 700; padding: 8px 22px; }
QPushButton#primary:hover { background: #4f7cff; }
QPushButton#primary:disabled { background: #b9c6f0; color: #ffffff; }
QPushButton#danger { color: #c93a3a; border-color: #efc9c9; }
QPushButton#danger:hover { background: #fdf0f0; }
QPushButton#danger:disabled { color: #d8b9b9; border-color: #efe3e3; }

QTableWidget {
    background: #ffffff; border: 1px solid #e0e5f0; border-radius: 12px; outline: 0;
    alternate-background-color: #f8f9fd; selection-background-color: #e4ebff; selection-color: #1d2433;
}
QTableWidget::item { padding: 4px 8px; border: none; }
QHeaderView::section {
    background: #f3f5fa; color: #6b7590; font-weight: 700; border: none;
    border-bottom: 1px solid #e0e5f0; padding: 9px 10px;
}

QGroupBox {
    background: #ffffff; border: 1px solid #e0e5f0; border-radius: 12px;
    margin-top: 14px; padding: 16px 12px 10px 12px; font-weight: 700;
}
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 14px; padding: 0 8px; color: #3b63e0; }

QTextBrowser { background: transparent; border: none; }
QTextBrowser#info { background: #ffffff; border: 1px solid #e0e5f0; border-radius: 12px; padding: 8px 12px; }

QProgressBar { background: #e3e8f4; border: none; border-radius: 5px; max-height: 10px; }
QProgressBar::chunk { background: #3b63e0; border-radius: 5px; }

QSplitter::handle { background: transparent; }
QStatusBar { color: #6b7590; background: transparent; }
QToolTip { background: #1d2433; color: #ffffff; border: none; padding: 5px 8px; }
"""


class CrawlWorker(QThread):
    """UI 가 멈추지 않도록 별도 스레드에서 크롤링한다."""

    found = pyqtSignal(int)            # 검색 결과 기사 수
    article = pyqtSignal(int, dict)    # (진행 번호, 기사)
    message = pyqtSignal(str)
    finished_ok = pyqtSignal()

    def __init__(self, query, limit, start_date=None, end_date=None, delay=1.0):
        super().__init__()
        self.query, self.limit, self.delay = query, limit, delay
        self.start_date, self.end_date = start_date, end_date
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            items = nc.find_articles(self.query, self.limit, self.start_date, self.end_date)
        except Exception as e:  # 네트워크/파싱 오류 모두 화면에 알린다
            self.message.emit(f"검색 페이지 요청 실패: {e}")
            self.finished_ok.emit()
            return
        self.found.emit(len(items))
        for i, item in enumerate(items, 1):
            if self._stop:
                self.message.emit("사용자가 중지했습니다.")
                break
            try:
                art = nc.parse_article(item["naver_url"])
            except requests.RequestException as e:
                self.message.emit(f"[{i}] 요청 실패: {e}")
                continue
            if art is None:
                self.message.emit(f"[{i}] 본문을 찾지 못함")
                continue
            art["title"] = art["title"] or item.get("title", "")
            art["press"] = art["press"] or item.get("press", "")
            art["posted"] = item.get("posted") or (art["date"] or "")[:10]
            art["original_url"] = item.get("original_url", "")
            art["snippet"] = item.get("snippet", "")
            self.article.emit(i, art)
            time.sleep(self.delay)
        self.finished_ok.emit()


def _esc(text):
    return (
        (text or "").replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace("'", "&#39;")
    )


def highlight(text, keywords):
    """HTML 이스케이프 후, 핵심 키워드로 시작하는 단어의 키워드 부분을 굵게 표시한다."""
    escaped = _esc(text)
    if not keywords:
        return escaped
    words = "|".join(re.escape(_esc(k)) for k in sorted(keywords, key=len, reverse=True))
    # 앞에 &, # 가 오면 HTML 엔티티(&amp; &#39;)의 일부이므로 제외한다.
    pattern = re.compile(r"(?<![가-힣A-Za-z0-9&#])(" + words + ")")
    return pattern.sub(rf"<b style='color:{KEYWORD_COLOR}'>\1</b>", escaped)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("네이버 뉴스 크롤러")
        self.resize(1120, 800)
        self.setMinimumSize(900, 640)
        self.articles = []
        self.worker = None

        # --- 입력 위젯 ---
        self.query_edit = QLineEdit()
        self.query_edit.returnPressed.connect(self.start)
        self.default_btn = QPushButton("기본값 설정")
        self.default_btn.setToolTip("검색어를 비워 두고 검색할 때 사용할 기본 검색어를 정합니다.")
        self.default_btn.clicked.connect(self.change_default_query)
        self.refresh_placeholder()
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 50)
        self.limit_spin.setValue(10)
        self.limit_spin.setSuffix(" 건")
        # 기간 필터: 프리셋을 고르면 날짜가 채워지고, "직접 지정"일 때만 날짜를 수정할 수 있다.
        self.period_combo = QComboBox()
        for label, _ in PERIODS:
            self.period_combo.addItem(label)
        self.date_from = QDateEdit(QDate.currentDate())
        self.date_to = QDateEdit(QDate.currentDate())
        for edit in (self.date_from, self.date_to):
            edit.setCalendarPopup(True)
            edit.setDisplayFormat("yyyy-MM-dd")
            edit.setMaximumDate(QDate.currentDate())
        self.period_combo.currentIndexChanged.connect(self.on_period_changed)
        self.on_period_changed(0)
        # 스핀/콤보/날짜 위젯은 기본(Fusion) 모양을 쓰되 높이만 맞춘다.
        for widget in (self.query_edit, self.limit_spin, self.period_combo, self.date_from, self.date_to):
            widget.setMinimumHeight(34)
        self.start_btn = QPushButton("크롤링 시작")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self.start)
        self.stop_btn = QPushButton("중지")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop)

        # --- 헤더 ---
        title = QLabel("뉴스 크롤러")
        title.setObjectName("title")
        subtitle = QLabel("네이버 뉴스 검색 · 3줄 요약 · 핵심 키워드")
        subtitle.setObjectName("subtitle")
        header_box = QVBoxLayout()
        header_box.setSpacing(0)
        header_box.addWidget(title)
        header_box.addWidget(subtitle)

        # --- 검색 카드 (두 줄) ---
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        row1.addWidget(self._label("검색어"))
        row1.addWidget(self.query_edit, 1)
        row1.addWidget(self.default_btn)
        row1.addWidget(self.start_btn)
        row1.addWidget(self.stop_btn)

        row2 = QHBoxLayout()
        row2.setSpacing(10)
        row2.addWidget(self._label("건수"))
        row2.addWidget(self.limit_spin)
        row2.addSpacing(12)
        row2.addWidget(self._label("기간"))
        row2.addWidget(self.period_combo)
        row2.addWidget(self.date_from)
        row2.addWidget(self._label("~"))
        row2.addWidget(self.date_to)
        row2.addStretch(1)

        search_card = QFrame()
        search_card.setObjectName("card")
        card_layout = QVBoxLayout(search_card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(10)
        card_layout.addLayout(row1)
        card_layout.addLayout(row2)

        # --- 결과 표 ---
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        header = self.table.horizontalHeader()
        header.setHighlightSections(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemSelectionChanged.connect(self.show_detail)
        self.table.cellClicked.connect(self.on_cell_clicked)
        self.table.setMouseTracking(True)
        self.table.cellEntered.connect(self.on_cell_hover)

        # --- 상세: 기사 정보 / 요약 / 전문 ---
        self.info = QTextBrowser()
        self.info.setObjectName("info")
        self.info.setOpenExternalLinks(True)
        self.info.setMaximumHeight(118)
        self.info.setPlaceholderText("표에서 기사를 선택하세요.")
        self.summary = QTextBrowser()
        # 요약은 최대 3줄이므로 정확히 3줄 높이로 고정하고 줄바꿈을 끈다.
        self.summary.setLineWrapMode(QTextBrowser.LineWrapMode.NoWrap)
        self.summary.setFixedHeight(self.summary.fontMetrics().lineSpacing() * 3 + 16)
        self.summary.setPlaceholderText("선택한 기사의 요약이 여기에 표시됩니다.")
        self.fulltext = QTextBrowser()
        self.fulltext.setPlaceholderText("선택한 기사의 전문이 여기에 표시됩니다.")

        summary_box = QGroupBox("요약")
        QVBoxLayout(summary_box).addWidget(self.summary)
        full_box = QGroupBox("전문")
        QVBoxLayout(full_box).addWidget(self.fulltext)

        detail_split = QSplitter(Qt.Orientation.Vertical)
        detail_split.addWidget(summary_box)
        detail_split.addWidget(full_box)
        detail_split.setSizes([100, 320])

        detail_panel = QWidget()
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(4)
        detail_layout.addWidget(self.info)
        detail_layout.addWidget(detail_split, 1)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.table)
        splitter.addWidget(detail_panel)
        splitter.setSizes([250, 450])

        # --- 하단 ---
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.save_json_btn = QPushButton("JSON 저장")
        self.save_csv_btn = QPushButton("CSV 저장")
        self.save_xlsx_btn = QPushButton("엑셀 저장")
        self.save_json_btn.clicked.connect(lambda: self.save("json"))
        self.save_csv_btn.clicked.connect(lambda: self.save("csv"))
        self.save_xlsx_btn.clicked.connect(lambda: self.save("xlsx"))
        self.set_save_enabled(False)

        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        bottom.addWidget(self.progress, 1)
        bottom.addWidget(self.save_json_btn)
        bottom.addWidget(self.save_csv_btn)
        bottom.addWidget(self.save_xlsx_btn)

        root = QVBoxLayout()
        root.setContentsMargins(20, 16, 20, 8)
        root.setSpacing(12)
        root.addLayout(header_box)
        root.addWidget(search_card)
        root.addWidget(splitter, 1)
        root.addLayout(bottom)
        central = QWidget()
        central.setObjectName("root")
        central.setLayout(root)
        self.setCentralWidget(central)
        self.statusBar().showMessage("검색어를 입력하고 '크롤링 시작'을 누르세요.")

    @staticmethod
    def _label(text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    # ---------- 동작 ----------
    def set_save_enabled(self, enabled):
        self.save_json_btn.setEnabled(enabled)
        self.save_csv_btn.setEnabled(enabled)
        self.save_xlsx_btn.setEnabled(enabled)

    def refresh_placeholder(self):
        self.query_edit.setPlaceholderText(
            f"검색어 입력 (비워 두면 기본 검색어 '{nc.get_default_query()}' 사용)"
        )

    def change_default_query(self):
        text, ok = QInputDialog.getText(
            self, "기본 검색어 설정",
            "검색어를 비워 두고 검색할 때 사용할 기본 검색어:",
            text=nc.get_default_query(),
        )
        if not ok:
            return
        try:
            nc.set_default_query(text)
        except ValueError:
            QMessageBox.warning(self, "입력 필요", "기본 검색어를 입력하세요.")
            return
        except OSError as e:
            QMessageBox.critical(self, "저장 실패", str(e))
            return
        self.refresh_placeholder()
        self.statusBar().showMessage(f"기본 검색어를 '{text.strip()}'(으)로 저장했습니다.")

    def on_period_changed(self, index):
        days = PERIODS[index][1]
        custom = days is None
        self.date_from.setEnabled(custom)
        self.date_to.setEnabled(custom)
        today = QDate.currentDate()
        if days is not None and days >= 0:
            self.date_to.setDate(today)
            self.date_from.setDate(today.addDays(-days))

    def selected_period(self):
        """(시작일, 종료일) 또는 전체 기간이면 (None, None)."""
        if PERIODS[self.period_combo.currentIndex()][1] == -1:
            return None, None
        return self.date_from.date().toPyDate(), self.date_to.date().toPyDate()

    def start(self):
        query = self.query_edit.text().strip()
        used_default = not query
        if used_default:
            query = nc.get_default_query()
        if self.worker and self.worker.isRunning():
            return
        start_date, end_date = self.selected_period()
        if start_date and start_date > end_date:
            QMessageBox.warning(self, "기간 오류", "시작일이 종료일보다 늦습니다.")
            return
        self.articles.clear()
        self.table.setRowCount(0)
        self.clear_detail()
        self.progress.setValue(0)
        self.set_save_enabled(False)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.statusBar().showMessage(
            f"검색어가 비어 있어 기본 검색어 '{query}'(으)로 검색 중..." if used_default else "검색 중..."
        )

        self.worker = CrawlWorker(query, self.limit_spin.value(), start_date, end_date)
        self.worker.found.connect(self.on_found)
        self.worker.article.connect(self.on_article)
        self.worker.message.connect(self.statusBar().showMessage)
        self.worker.finished_ok.connect(self.on_finished)
        self.worker.start()

    def stop(self):
        if self.worker:
            self.worker.stop()
            self.stop_btn.setEnabled(False)

    def on_found(self, count):
        self.progress.setMaximum(max(count, 1))
        self.statusBar().showMessage(f"기사 {count}건 발견, 본문 수집 중...")

    def on_article(self, index, art):
        self.articles.append(art)
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, key in enumerate(["title", "press", "posted", "url"]):
            item = QTableWidgetItem(art.get(key, ""))
            if col == LINK_COL:  # 링크 칸은 파란 밑줄로 클릭 가능함을 표시
                font = QFont(item.font())
                font.setUnderline(True)
                item.setFont(font)
                item.setForeground(QBrush(QColor(ACCENT)))
                item.setToolTip("클릭하면 브라우저 새 창에서 기사가 열립니다.")
            self.table.setItem(row, col, item)
        self.progress.setValue(index)
        self.statusBar().showMessage(f"[{index}/{self.progress.maximum()}] {art['title']}")

    def on_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.setValue(self.progress.maximum())
        n = len(self.articles)
        if n:
            asked = self.limit_spin.value()
            note = "" if n >= asked else f" (요청 {asked}건 — 검색 결과에 노출된 기사만 수집 가능)"
            self.statusBar().showMessage(f"완료: {n}건 수집{note}")
        else:
            self.statusBar().showMessage("수집된 기사가 없습니다. 다른 검색어를 입력해 보세요.")
        self.set_save_enabled(n > 0)

    def clear_detail(self):
        for view in (self.info, self.summary, self.fulltext):
            view.clear()

    def on_cell_clicked(self, row, col):
        """링크 칸을 클릭하면 기본 브라우저에서 기사 페이지를 연다."""
        if col != LINK_COL:
            return
        url = self.articles[row]["url"]
        if not QDesktopServices.openUrl(QUrl(url)):
            QMessageBox.warning(self, "열기 실패", f"브라우저를 열 수 없습니다.\n{url}")

    def on_cell_hover(self, row, col):
        self.table.viewport().setCursor(
            Qt.CursorShape.PointingHandCursor if col == LINK_COL else Qt.CursorShape.ArrowCursor
        )

    def show_detail(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        art = self.articles[rows[0].row()]
        self.clear_detail()

        keywords = art.get("keywords") or nc.extract_keywords(art["content"])
        original = art.get("original_url")
        chips = " ".join(
            f"<span style='background-color:#e4ebff; color:{KEYWORD_COLOR}'>&nbsp;<b>{_esc(k)}</b>&nbsp;</span>"
            for k in keywords
        )
        self.info.setHtml(
            f"<div style='font-size:14pt; font-weight:700'>{_esc(art['title'])}</div>"
            f"<div style='color:#6b7590; margin-top:4px'>{_esc(art['press'])} · "
            f"{_esc(art['date'] or art['posted'])} &nbsp;|&nbsp; "
            f"<a href='{_esc(art['url'])}' style='color:{ACCENT}'>네이버 기사</a>"
            + (f" · <a href='{_esc(original)}' style='color:{ACCENT}'>원문</a>" if original else "")
            + "</div>"
            + (f"<div style='margin-top:6px'><span style='color:#6b7590'>핵심 키워드</span> &nbsp;{chips}</div>"
               if keywords else "")
        )

        content = art["content"]
        summary = art.get("summary") or nc.summarize(content)
        self.summary.setHtml("<br>".join(highlight(line, keywords) for line in summary.split("\n")))
        self.fulltext.setHtml(
            "".join(
                f"<p style='margin:0 0 9px 0; line-height:165%'>{highlight(line, keywords)}</p>"
                for line in content.split("\n") if line.strip()
            )
        )

    def save(self, kind):
        path, _ = QFileDialog.getSaveFileName(
            self, "저장", f"news_result.{kind}",
            "Excel (*.xlsx)" if kind == "xlsx" else f"{kind.upper()} (*.{kind})",
        )
        if not path:
            return
        try:
            if kind == "xlsx":
                nc.save_excel(self.articles, path)
            elif kind == "json":
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.articles, f, ensure_ascii=False, indent=2)
            else:
                with open(path, "w", encoding="utf-8-sig", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
                    w.writeheader()
                    w.writerows({k: nc.cell_text(v) for k, v in a.items()} for a in self.articles)
        except (OSError, ValueError) as e:
            QMessageBox.critical(self, "저장 실패", str(e))
            return
        self.statusBar().showMessage(f"저장 완료: {path}")

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
