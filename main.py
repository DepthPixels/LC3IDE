import sys
from PySide6.QtCore import QSize, Qt, QVariantAnimation, QEasingCurve, QSequentialAnimationGroup
from PySide6.QtWidgets import (QApplication, QWidget, QMainWindow, QPushButton, 
                               QPlainTextEdit, QDockWidget, QVBoxLayout, QHBoxLayout,
                               QTabWidget, QTabBar, QTextEdit)
from PySide6.QtGui import QColor, QPainter, QTextFormat, QAction
import qtawesome as qta


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.line_number_area = LineNumberArea(self)
        
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        
        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), 
                                        self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(cr.left(), cr.top(), 
                                         self.line_number_area_width(), cr.height())

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(14, 14, 14))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(133, 133, 133))
                painter.drawText(0, int(top), self.line_number_area.width() - 3, 
                               self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(26, 26, 26)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("LC3IDE")
        self.setMinimumSize(QSize(1200, 780))
        self.setStyleSheet("background-color: #0e0e0e")
        
        # Variables
        self.tab_modified = {}
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #0e0e0e;
            }
            QTabBar::tab {
                background-color: #0e0e0e;
                color: #858585;
                padding: 8px 16px;
                border: none;
            }
            QTabBar::tab:selected {
                color: #d4d4d4;
                border-bottom: 2px solid #80CBC4;
            }
            QTabBar::tab:hover {
                background-color: #1a1a1a;
            }
        """)

        # Get the tab bar and create custom corner widget
        tab_bar = self.tabs.tabBar()

        # Create corner widget with buttons
        corner_widget = QWidget()
        corner_layout = QHBoxLayout()
        corner_layout.setContentsMargins(4, 0, 4, 0)
        corner_layout.setSpacing(4)

        # Add "+" button
        self.add_tab_button = QPushButton()
        self.add_tab_button.setIcon(qta.icon("fa5s.plus", color="#858585"))
        self.add_tab_button.setIconSize(QSize(14, 14))
        self.add_tab_button.setFixedSize(QSize(28, 28))
        self.add_tab_button.setFlat(True)
        self.add_tab_button.clicked.connect(lambda: self.add_new_tab())
        self.add_tab_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
            }
        """)
        corner_layout.addWidget(self.add_tab_button)

        # Run button
        self.run_button = QPushButton()
        self.run_button.setIcon(qta.icon("fa5s.play", color="#80CBC4"))
        self.run_button.setIconSize(QSize(14, 14))
        self.run_button.setFixedSize(QSize(28, 28))
        self.run_button.setFlat(True)
        self.run_button.clicked.connect(self.run_code)
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
            }
        """)
        corner_layout.addWidget(self.run_button)

        # Stop button
        self.stop_button = QPushButton()
        self.stop_button.setIcon(qta.icon("fa5s.stop", color="#858585"))
        self.stop_button.setIconSize(QSize(14, 14))
        self.stop_button.setFixedSize(QSize(28, 28))
        self.stop_button.setFlat(True)
        self.stop_button.clicked.connect(self.stop_code)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
            }
        """)
        corner_layout.addWidget(self.stop_button)

        corner_widget.setLayout(corner_layout)
        corner_widget.setStyleSheet("background-color: #0e0e0e;")

        # Set corner widget to the right of tabs
        self.tabs.setCornerWidget(corner_widget, Qt.Corner.TopRightCorner)

        # Set tabs as central widget
        self.setCentralWidget(self.tabs)

        # Add first tab
        self.add_new_tab("Untitled-1")

        
        # Create sidebar dock
        self.files_button = QPushButton()
        self.files_button.setIcon(qta.icon("fa6.folder", color="#858585"))
        self.files_button.setIconSize(QSize(20, 20))
        self.files_button.setFixedSize(QSize(40, 40))
        self.files_button.setFlat(True)
        self.files_button.enterEvent = self.enterDockIcon
        self.files_button.leaveEvent = self.leaveDockIcon
        self.files_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
        """)
        
        # Create bounce animation sequence
        self.bounce_group = QSequentialAnimationGroup()
        
        # Expand animation
        self.expand_anim = QVariantAnimation()
        self.expand_anim.setDuration(120)
        self.expand_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.expand_anim.valueChanged.connect(self.update_icon_size)
        
        # Contract animation
        self.contract_anim = QVariantAnimation()
        self.contract_anim.setDuration(120)
        self.contract_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.contract_anim.valueChanged.connect(self.update_icon_size)
        
        self.bounce_group.addAnimation(self.expand_anim)
        self.bounce_group.addAnimation(self.contract_anim)
        
        # Dock Code
        
        dock = QDockWidget("Dock", self)
        dock.setTitleBarWidget(QWidget())
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                            Qt.DockWidgetArea.RightDockWidgetArea)
        
        dock_content = QWidget()
        dock_content.setStyleSheet("background-color: #0e0e0e;")
        dock_layout = QVBoxLayout()
        dock_layout.addWidget(self.files_button)
        dock_layout.addStretch()
        dock_content.setLayout(dock_layout)
        dock.setWidget(dock_content)
        
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)       
        
        
    # Dock Functions
    def update_icon_size(self, value):
        self.files_button.setIconSize(value)
    
    def enterDockIcon(self, event):
        self.files_button.setIcon(qta.icon("fa6.folder", color="white"))
        self.bounce_group.stop()
        
        current_size = self.files_button.iconSize()
        
        # Expand to bigger size
        self.expand_anim.setStartValue(current_size)
        self.expand_anim.setEndValue(QSize(22, 22))
        
        # Contract back to normal hover size
        self.contract_anim.setStartValue(QSize(24, 24))
        self.contract_anim.setEndValue(QSize(20, 20))
        
        self.bounce_group.start()
    
    def leaveDockIcon(self, event):
        self.files_button.setIcon(qta.icon("fa6.folder", color="#858585"))
        self.bounce_group.stop()
        
        # Simple shrink back
        self.expand_anim.setStartValue(self.files_button.iconSize())
        self.expand_anim.setEndValue(QSize(20, 20))
        self.expand_anim.start()
        
        
        
        
    # Tab Bar Functions
    def add_new_tab(self, title="Untitled"):
        editor = CodeEditor()
        editor.setPlaceholderText("Write your LC-3 code here...")
        editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0e0e0e;
                color: white;
                border: none;
                selection-background-color: #264f78;
            }
        """)
        
        # Connect text change to track modifications
        editor.textChanged.connect(lambda: self.mark_tab_modified(self.tabs.indexOf(editor)))
        
        index = self.tabs.addTab(editor, title)
        self.tab_modified[index] = False
        
        # Create close/dot button
        close_btn = QPushButton()
        close_btn.setIcon(qta.icon("fa5s.circle", color="#858585"))  # Dot icon initially
        close_btn.setIconSize(QSize(10, 10))
        close_btn.setFixedSize(QSize(16, 16))
        close_btn.setFlat(True)
        close_btn.setVisible(False)  # Hidden initially
        close_btn.clicked.connect(lambda: self.close_tab(index))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
            }
        """)
        
        # Store button reference
        close_btn.setProperty("tab_index", index)
        
        self.tabs.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, close_btn)
        self.tabs.setCurrentWidget(editor)
        
        # Add hover events to tab
        tab_bar = self.tabs.tabBar()
        original_event = tab_bar.event
        
        def custom_event(event):
            if event.type() == event.Type.HoverEnter:
                self.update_tab_button_on_hover(index, True)
            elif event.type() == event.Type.HoverLeave:
                self.update_tab_button_on_hover(index, False)
            return original_event(event)
        
        tab_bar.event = custom_event
        tab_bar.setMouseTracking(True)
            
            
    
    def mark_tab_modified(self, index):
        if index >= 0 and not self.tab_modified.get(index, False):
            self.tab_modified[index] = True
            self.update_tab_button(index)
    
    def mark_tab_saved(self, index):
        if index >= 0:
            self.tab_modified[index] = False
            self.update_tab_button(index)
    
    def update_tab_button(self, index):
        button = self.tabs.tabBar().tabButton(index, QTabBar.ButtonPosition.RightSide)
        if button:
            is_modified = self.tab_modified.get(index, False)
            
            if is_modified:
                # Show dot when modified
                button.setIcon(qta.icon("fa5s.circle", color="white"))
                button.setIconSize(QSize(10, 10))
                button.setVisible(True)
            else:
                # Hide when not modified and not hovering
                button.setIcon(qta.icon("fa5s.x", color="white"))
                button.setIconSize(QSize(10, 10))
                button.setVisible(True)
    
    def update_tab_button_on_hover(self, index, is_hovering):
        button = self.tabs.tabBar().tabButton(index, QTabBar.ButtonPosition.RightSide)
        if button:
            is_modified = self.tab_modified.get(index, False)
            
            if is_hovering:
                # Show X on hover
                button.setIcon(qta.icon("fa5s.xmark", color="white"))
                button.setIconSize(QSize(10, 10))
                button.setVisible(True)
            else:
                # Show dot if modified, hide if not
                if is_modified:
                    button.setIcon(qta.icon("fa5s.circle", color="white"))
                    button.setIconSize(QSize(10, 10))
                    button.setVisible(True)
                else:
                    button.setIcon(qta.icon("fa5s.x", color="white"))
                    button.setIconSize(QSize(10, 10))
                    button.setVisible(True)
                    
    
    def close_tab(self, index):
        if self.tabs.count() > 1:
            # Check if modified and prompt to save
            if self.tab_modified.get(index, False):
                # Add save dialog here
                pass
            
            self.tabs.removeTab(index)
            del self.tab_modified[index]

    
    def run_code(self):
        current_editor = self.tabs.currentWidget()
        if current_editor:
            code = current_editor.toPlainText()
            print(f"Running code:\n{code}")
            # Add your run logic here
    
    def stop_code(self):
        print("Stopping code execution")
        # Add your stop logic here


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()