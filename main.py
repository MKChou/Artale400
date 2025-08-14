import sys
import os
from typing import List, Optional
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QSettings, QTimer
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, 
                           QVBoxLayout, QHBoxLayout, QMessageBox)
from PyQt5.QtGui import QFont, QPalette, QColor, QKeySequence, QPainter, QPixmap
from PyQt5.QtWidgets import QShortcut
import datetime


def resource_path(relative_path: str) -> str:
    """在開發與 PyInstaller 打包後皆可取得資源路徑"""
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


class LookupTable:
    """查表邏輯封裝類別"""
    
    def __init__(self):
        self._table = {
            "0011": "211", "0101": "121", "0110": "112",
            "1110": "220", "1101": "202", "1011": "022",
            "1120": "310", "1210": "130", "1012": "031",
            "1102": "301", "1201": "103", "1021": "013",
            "2211": "400", "2121": "040", "2112": "004"
        }
    
    def lookup(self, key: str) -> str:
        """查表方法"""
        return self._table.get(key, "查無對應")
    
    def has_key(self, key: str) -> bool:
        """檢查鍵值是否存在"""
        return key in self._table


class NumberSelector(QWidget):
    """數字選擇器組件"""
    
    selectionChanged = pyqtSignal(int, int)  # 位置, 數字
    
    def __init__(self, position: int, parent=None):
        super().__init__(parent)
        self.position = position
        self.selected_number = 0
        self.buttons: List[QPushButton] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """設置UI佈局"""
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(4)
        layout.setContentsMargins(2, 2, 2, 2)
        
        for num in range(3):
            btn = self._create_number_button(num)
            self.buttons.append(btn)
            layout.addWidget(btn)
        
        self.setLayout(layout)
        self._update_button_styles()
    
    def _create_number_button(self, number: int) -> QPushButton:
        """創建數字按鈕"""
        btn = QPushButton(str(number))
        btn.setFixedSize(45, 45)
        btn.clicked.connect(lambda: self.select_number(number))
        return btn
    
    def select_number(self, number: int):
        """選擇數字"""
        self.selected_number = number
        self._update_button_styles()
        self.selectionChanged.emit(self.position, number)
    
    def _update_button_styles(self):
        """更新按鈕樣式"""
        for i, btn in enumerate(self.buttons):
            if i == self.selected_number:
                btn.setStyleSheet(self._get_selected_style())
            else:
                btn.setStyleSheet(self._get_default_style())
    
    def _get_selected_style(self) -> str:
        """選中按鈕樣式"""
        return """
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: 2px solid #c0392b;
                border-radius: 12px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #c0392b;
                border: 2px solid #a93226;
            }
            QPushButton:pressed {
                background-color: #a93226;
                border: 2px solid #8b2635;
            }
        """
    
    def _get_default_style(self) -> str:
        """默認按鈕樣式"""
        return """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: 2px solid #2980b9;
                border-radius: 12px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #2980b9;
                border: 2px solid #1f618d;
            }
            QPushButton:pressed {
                background-color: #1f618d;
                border: 2px solid #154360;
            }
        """

    def set_selected_number(self, number: int):
        """外部設定選擇數字，並更新樣式"""
        if number not in (0, 1, 2):
            return
        self.selected_number = number
        self._update_button_styles()


class DisplayPanel(QWidget):
    """顯示面板組件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """設置UI"""
        layout = QVBoxLayout()
        layout.setSpacing(3)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 結果顯示
        self.result_label = QLabel("結果：")
        self.result_label.setFont(QFont("Microsoft JhengHei", 14, QFont.Bold))
        self.result_label.setStyleSheet(
            "color: #e74c3c; background-color: #fff5f5; padding: 8px; "
            "border-radius: 8px; border: 1px solid #fadbd8;"
        )
        self.result_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.result_label)
        self.setLayout(layout)
    
    def update_result(self, result: str):
        """更新結果顯示"""
        self.result_label.setText(f"結果：{result}")


class DraggableWindow(QWidget):
    """可拖動視窗基類"""
    
    def __init__(self):
        super().__init__()
        self.dragging = False
        self.drag_pos = QPoint()
    
    def mousePressEvent(self, event):
        """滑鼠按下事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        """滑鼠移動事件"""
        if self.dragging:
            self.move(event.globalPos() - self.drag_pos)
    
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = False


class OverlayWindow(DraggableWindow):
    """主視窗類別"""
    
    def __init__(self):
        super().__init__()
        self.lookup_table = LookupTable()
        self.current_selection = [0, 0, 0, 0]
        self.number_selectors: List[NumberSelector] = []
        self.settings = QSettings()
        # 浮水印設定
        self.watermark_opacity: float = 0.25
        watermark_file = resource_path("image.png")
        self.watermark_pixmap = QPixmap(watermark_file) if os.path.exists(watermark_file) else QPixmap()
        
        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        self._setup_shortcuts()
        self._load_settings()
    
    def _setup_window(self):
        """設置視窗屬性"""
        self.setWindowTitle("查表小工具")
        self.resize(400, 320)
        self.move(500, 300)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # 設置視窗透明度
        self.setWindowOpacity(0.95)
        
        # 設置半透明白色背景和圓角樣式
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 15px;
            }
        """)
        
        # 設置背景顏色為半透明
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(255, 255, 255, 230))
        self.setPalette(palette)
    
    def _setup_ui(self):
        """設置使用者介面"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # 頂部列：標題（左）與說明按鈕、關閉按鈕（右）ㄕ
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 4)
        
        # 左邊標題
        title_label = QLabel("女神速解小工具")
        title_label.setFont(QFont("Microsoft JhengHei", 12, QFont.Bold))
        title_label.setStyleSheet("color: #e74c3c; padding: 4px; background: transparent;")
        
        # 動態圓點
        self.status_dot = QLabel("●")
        self.status_dot.setFont(QFont("Microsoft JhengHei", 14, QFont.Bold))
        
        # 星期顏色對應表
        self.weekday_colors = {
            0: "#f39c12",  # 星期一：橘色
            1: "#f1c40f",  # 星期二：黃色
            2: "#9b59b6",  # 星期三：紫色
            3: "#34495e",  # 星期四：靛色
            4: "#3498db",  # 星期五：藍色
            5: "#27ae60",  # 星期六：綠色
            6: "#e74c3c"   # 星期日：紅色
        }
        
        # 初始化圓點顏色
        self._update_dot_color()
        
        # 設置定時器來檢查時間並更新顏色
        self.color_timer = QTimer()
        self.color_timer.timeout.connect(self._check_and_update_color)
        self.color_timer.start(60000)  # 每分鐘檢查一次
        
        help_btn = self._create_help_button()
        close_button = self._create_close_button()
        
        top_bar.addWidget(title_label, 0, alignment=Qt.AlignLeft)
        top_bar.addWidget(self.status_dot, 0, alignment=Qt.AlignLeft)
        top_bar.addStretch()  # 中間彈性空間
        top_bar.addWidget(help_btn, 0, alignment=Qt.AlignRight)
        top_bar.addWidget(close_button, 0, alignment=Qt.AlignRight)
        main_layout.addLayout(top_bar)
        
        # 創建數字選擇器
        for pos in range(4):
            selector = NumberSelector(pos, self)
            self.number_selectors.append(selector)
            main_layout.addWidget(selector)
        
        # 創建顯示面板
        self.display_panel = DisplayPanel(self)
        main_layout.addWidget(self.display_panel)

        self.setLayout(main_layout)
    
    def _create_close_button(self) -> QPushButton:
        """創建關閉按鈕（右上）"""
        btn = QPushButton("關閉")
        btn.setFixedHeight(28)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: 1px solid #c0392b;
                padding: 4px 10px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
                border: 1px solid #a93226;
            }
            QPushButton:pressed {
                background-color: #a93226;
                border: 1px solid #8b2635;
            }
        """)
        btn.setToolTip("關閉視窗")
        btn.clicked.connect(self.close)
        return btn

    def _create_help_button(self) -> QPushButton:
        """創建功能說明按鈕"""
        btn = QPushButton("說明")
        btn.setFixedHeight(28)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: 1px solid #7f8c8d;
                padding: 4px 10px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7f8c8d; }
            QPushButton:pressed { background-color: #707b7c; }
        """)
        btn.setToolTip("顯示功能說明與免責聲明")
        btn.clicked.connect(self._show_help)
        return btn

    def _get_current_weekday_color(self):
        """獲取當前星期對應的顏色"""
        now = datetime.datetime.now()
        # 如果時間在13:00之前，使用前一天的顏色
        if now.hour < 13:
            # 前一天
            yesterday = now - datetime.timedelta(days=1)
            weekday = yesterday.weekday()
        else:
            # 當天
            weekday = now.weekday()
        
        return self.weekday_colors[weekday]
    
    def _update_dot_color(self):
        """更新圓點顏色"""
        color = self._get_current_weekday_color()
        self.status_dot.setStyleSheet(f"color: {color}; padding: 2px; background: transparent;")
    
    def _check_and_update_color(self):
        """檢查時間並更新顏色"""
        now = datetime.datetime.now()
        # 在13:00時更新顏色
        if now.hour == 13 and now.minute == 0:
            self._update_dot_color()
    
    def _show_help(self):
        """顯示功能說明與免責聲明對話框"""
        text = (
            "【功能說明】\n"
            "• 數字選擇：點選四行按鈕設定 0/1/2，結果即時更新\n"
            "• 結果顯示：面板顯示400任務的答案\n"
            "• 圓點顏色：會跟隨著CD房任務需求做變化\n"

            "\n【快捷鍵】\n"
            "• Esc：關閉視窗\n"
            "• Alt + ↑/↓：調整透明度\n"
            "• Alt + ←/→：等比縮放視窗大小\n"

            "\n【其他功能】\n"
            "• 程式會自動保存視窗位置/大小、透明度與選擇值\n"
            "• 下次開啟時自動還原上次的設定\n"

            "\n" + "="*50 + "\n"

            "【免責聲明】\n"
            "使用須知與責任聲明\n"

            "\n1. 自行承擔風險\n"
            "   • 本工具僅供參考使用\n"
            "   • 使用者應自行評估風險並承擔所有後果\n"
            "   • 使用前請詳細閱讀相關遊戲的服務條款與使用規範\n"

            "2. 遊戲規則遵循\n"
            "   • 使用者有責任確保使用本工具不違反任何遊戲的服務條款\n"
            "   • 若因使用本工具導致帳號被封禁或其他懲罰，概由使用者自行負責\n"

            "3. 技術風險\n"
            "   • 本工具可能存在程式錯誤或相容性問題\n"
            "   • 使用者應自行備份重要資料\n"
            "   • 開發者不對任何資料遺失負責\n"

            "4. 法律責任\n"
            "   • 使用者應確保使用本工具符合當地法律法規\n"
            "   • 任何因使用本工具產生的法律問題由使用者自行承擔\n"

            "5. 開發者聲明\n"
            "   • 開發者不對使用本工具所產生的任何直接或間接損失負責\n"
            "   • 本工具按「現狀」提供，不提供任何明示或暗示的保證\n"

            "\n" + "="*50 + "\n"

            "作者：fdrgrhppfhfq\n"
            "版本：1.2.1\n"
        )
        QMessageBox.information(self, "說明", text)
    
    def _connect_signals(self):
        """連接信號"""
        for selector in self.number_selectors:
            selector.selectionChanged.connect(self._on_selection_changed)
    
    def _setup_shortcuts(self):
        """設定快捷鍵：Esc 關閉、Alt+上下 調整透明度、Alt+左右 調整大小"""
        QShortcut(QKeySequence(Qt.Key_Escape), self, activated=self.close)
        QShortcut(QKeySequence("Alt+Up"), self, activated=lambda: self._adjust_opacity(0.05))
        QShortcut(QKeySequence("Alt+Down"), self, activated=lambda: self._adjust_opacity(-0.05))
        # Alt + 左右：調整畫面大小（等比縮放）
        QShortcut(QKeySequence("Alt+Right"), self, activated=lambda: self._adjust_size(1.1))
        QShortcut(QKeySequence("Alt+Left"), self, activated=lambda: self._adjust_size(0.9))
    
    def _on_selection_changed(self, position: int, number: int):
        """處理選擇變更事件"""
        self.current_selection[position] = number
        self._update_display()
        self._save_selection()
    
    def _update_display(self): 
        """更新顯示"""
        selection_str = "".join(map(str, self.current_selection))
        result = self.lookup_table.lookup(selection_str)
        
        self.display_panel.update_result(result)

    def paintEvent(self, event):
        """繪製浮水印於視窗中央（在子元件之下/背景上層）"""
        super().paintEvent(event)
        if self.watermark_pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, on=True)
        painter.setOpacity(self.watermark_opacity)
        # 依視窗尺寸縮放，取視窗較短邊的 60%
        target_w = int(self.width() * 0.6)
        target_h = int(self.height() * 0.6)
        scaled = self.watermark_pixmap.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()

    def _adjust_opacity(self, delta: float):
        """調整視窗透明度，範圍 0.2 ~ 1.0"""
        new_opacity = max(0.2, min(1.0, round(self.windowOpacity() + delta, 2)))
        self.setWindowOpacity(new_opacity)
        self._save_opacity(new_opacity)

    def _adjust_size(self, scale: float):
        """等比調整視窗大小，限制在合理範圍並即時保存幾何"""
        scale = max(0.1, min(10.0, float(scale)))
        new_w = int(max(280, min(1600, round(self.width() * scale))))
        new_h = int(max(220, min(1200, round(self.height() * scale))))
        self.resize(new_w, new_h)
        self._save_geometry()

    def _load_settings(self):
        """載入設定（視窗位置/大小、透明度、選擇值）"""
        geometry = self.settings.value("window/geometry")
        if geometry is not None:
            try:
                self.restoreGeometry(geometry)
            except Exception:
                pass
        opacity = self.settings.value("window/opacity", type=float)
        if opacity:
            try:
                self.setWindowOpacity(float(opacity))
            except Exception:
                pass
        selection = self.settings.value("state/selection")
        if isinstance(selection, str) and len(selection) == 4 and all(ch in "012" for ch in selection):
            self.current_selection = [int(ch) for ch in selection]
            for idx, selector in enumerate(self.number_selectors):
                selector.set_selected_number(self.current_selection[idx])
            self._update_display()

    def _save_geometry(self):
        try:
            self.settings.setValue("window/geometry", self.saveGeometry())
        except Exception:
            pass

    def _save_opacity(self, value: float):
        try:
            self.settings.setValue("window/opacity", float(value))
        except Exception:
            pass

    def _save_selection(self):
        try:
            selection_str = "".join(map(str, self.current_selection))
            self.settings.setValue("state/selection", selection_str)
        except Exception:
            pass

    def closeEvent(self, event):
        """關閉事件：保存幾何與狀態"""
        self._save_geometry()
        self._save_selection()
        self._save_opacity(self.windowOpacity())
        return super().closeEvent(event)


class Application:
    """應用程式管理類別"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setOrganizationName("fdrgrhppfhfq")
        self.app.setApplicationName("查表小工具")
        self.window: Optional[OverlayWindow] = None
    
    def run(self):
        """執行應用程式"""
        try:
            print("啟動查表小工具...")
            self.window = OverlayWindow()
            print("顯示視窗...")
            self.window.show()
            print("進入事件循環...")
            return self.app.exec_()
        except Exception as e:
            print(f"應用程式執行錯誤：{e}")
            return 1


def main():
    """主函數"""
    app = Application()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
