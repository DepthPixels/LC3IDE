import sys, os, subprocess
import qtawesome as qta

from PySide6.QtCore import QSize, Qt, QVariantAnimation, QEasingCurve, QSequentialAnimationGroup, QEvent
from PySide6.QtWidgets import (QApplication, QWidget, QMainWindow, QPushButton, 
                               QPlainTextEdit, QDockWidget, QVBoxLayout, QHBoxLayout,
                               QTabWidget, QTabBar, QTextEdit, QFileDialog, QMessageBox)
from PySide6.QtGui import QColor, QPainter, QTextFormat, QAction


def update_assembler():
    assembler_path = os.path.join(os.getcwd(), 'LC3Assembler')
    process = subprocess.Popen(
            "cmd.exe",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False
        )
    if os.path.isdir(assembler_path):
        process.stdin.write("cd LC3Assembler\n")
        process.stdin.write("git pull\n")
        stdout_data, stderr_data = process.communicate()
    else:
        process.stdin.write("git clone https://github.com/DepthPixels/LC3Assembler.git\n")
        stdout_data, stderr_data = process.communicate()
        
    process.stdin.close()


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


class CustomTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.hovered_tab = -1
    
    def mouseMoveEvent(self, event):
        new_hovered = self.tabAt(event.pos())
        if new_hovered != self.hovered_tab:
            old_hovered = self.hovered_tab
            self.hovered_tab = new_hovered
            
            # Update both old and new hovered tabs
            main_window = self.window()
            if hasattr(main_window, 'update_tab_button_state'):
                if old_hovered >= 0:
                    main_window.update_tab_button_state(old_hovered, False)
                if new_hovered >= 0:
                    main_window.update_tab_button_state(new_hovered, True)
        super().mouseMoveEvent(event)
    
    def leaveEvent(self, event):
        if self.hovered_tab >= 0:
            old_hovered = self.hovered_tab
            self.hovered_tab = -1
            main_window = self.window()
            if hasattr(main_window, 'update_tab_button_state'):
                main_window.update_tab_button_state(old_hovered, False)
        super().leaveEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("LC3IDE")
        self.setMinimumSize(QSize(1200, 780))
        self.setStyleSheet("background-color: #0e0e0e")
        
        # Variables
        self.tab_modified = {}
        self.tab_file_paths = {}
        
        # Keyboard Shortcuts
        save_shortcut = QAction("Save", self)
        save_shortcut.setShortcut("Ctrl+S")
        save_shortcut.triggered.connect(self.save_file)
        self.addAction(save_shortcut)
        
        save_as_shortcut = QAction("Save As", self)
        save_as_shortcut.setShortcut("Ctrl+Shift+S")
        save_as_shortcut.triggered.connect(self.save_file_as)
        self.addAction(save_as_shortcut)
        
        open_shortcut = QAction("Open", self)
        open_shortcut.setShortcut("Ctrl+O")
        open_shortcut.triggered.connect(self.open_file)
        self.addAction(open_shortcut)
        
        # Create tab widget with custom tab bar
        self.tabs = QTabWidget()
        custom_tab_bar = CustomTabBar(self.tabs)
        self.tabs.setTabBar(custom_tab_bar)
        self.tabs.setTabsClosable(False)  # We handle close buttons manually
        
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

        # assemble button
        self.assemble_button = QPushButton()
        self.assemble_button.setIcon(qta.icon("fa5s.play", color="#80CBC4"))
        self.assemble_button.setIconSize(QSize(14, 14))
        self.assemble_button.setFixedSize(QSize(28, 28))
        self.assemble_button.setFlat(True)
        self.assemble_button.clicked.connect(self.assemble_code)
        self.assemble_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
            }
        """)
        corner_layout.addWidget(self.assemble_button)

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
        self.files_button.clicked.connect(self.open_file)
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
    def add_new_tab(self, title="Untitled", file_path=None, content=""):
        editor = CodeEditor()
        editor.setPlaceholderText("Write your LC-3 code here...")
        editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0e0e0e;
                color: #d4d4d4;
                border: none;
                selection-background-color: #264f78;
            }
        """)
        
        # Set content if opening file
        if content:
            editor.setPlainText(content)
        
        index = self.tabs.addTab(editor, title)
        self.tab_modified[index] = False
        self.tab_file_paths[index] = file_path
        
        # Connect text change AFTER adding tab
        editor.textChanged.connect(lambda: self.mark_tab_modified(self.tabs.indexOf(editor)))
        
        # Create close/dot button
        close_btn = QPushButton()
        close_btn.setIcon(qta.icon("fa6s.circle", color="#d4d4d4"))
        close_btn.setIconSize(QSize(8, 8))
        close_btn.setFixedSize(QSize(16, 16))
        close_btn.setFlat(True)
        close_btn.setVisible(False)
        
        # Important: Use a lambda that captures the current index
        close_btn.clicked.connect(lambda checked=False, idx=index: self.close_tab(idx))
        
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
        
        self.tabs.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, close_btn)
        self.tabs.setCurrentWidget(editor)
    
    
    
    def update_tab_button_state(self, index, is_hovering):
        if index < 0 or index >= self.tabs.count():
            return
            
        button = self.tabs.tabBar().tabButton(index, QTabBar.ButtonPosition.RightSide)
        if not button:
            return
        
        is_modified = self.tab_modified.get(index, False)
        
        if is_hovering:
            # Show X on hover
            button.setIcon(qta.icon("fa6s.x", color="#858585"))
            button.setIconSize(QSize(10, 10))
            button.setVisible(True)
        elif is_modified:
            # Show white dot when modified
            button.setIcon(qta.icon("fa6s.circle", color="#d4d4d4"))
            button.setIconSize(QSize(8, 8))
            button.setVisible(True)
        else:
            # Hide when clean and not hovering
            button.setVisible(False)

    
    def mark_tab_modified(self, index):
        if index >= 0:
            old_state = self.tab_modified.get(index, False)
            self.tab_modified[index] = True
            # Update button even if already modified (for first text change)
            if not old_state:
                tab_bar = self.tabs.tabBar()
                is_hovering = (index == getattr(tab_bar, 'hovered_tab', -1))
                self.update_tab_button_state(index, is_hovering)


    
    def mark_tab_saved(self, index):
        if index >= 0:
            self.tab_modified[index] = False
            # Update the button state
            tab_bar = self.tabs.tabBar()
            is_hovering = (index == getattr(tab_bar, 'hovered_tab', -1))
            self.update_tab_button_state(index, is_hovering)

    
    def close_tab(self, index):
        if self.tabs.count() > 1:
            # Check if modified and prompt to save
            if self.tab_modified.get(index, False):
                file_name = self.tabs.tabText(index)
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    f"Do you want to save changes to '{file_name}'?",
                    QMessageBox.StandardButton.Save | 
                    QMessageBox.StandardButton.Discard | 
                    QMessageBox.StandardButton.Cancel
                )
                
                if reply == QMessageBox.StandardButton.Save:
                    # Save before closing
                    old_index = self.tabs.currentIndex()
                    self.tabs.setCurrentIndex(index)
                    self.save_file()
                    self.tabs.setCurrentIndex(old_index)
                elif reply == QMessageBox.StandardButton.Cancel:
                    return  # Don't close
            
            self.tabs.removeTab(index)
            
            # Rebuild dicts with updated indices
            new_modified = {}
            new_file_paths = {}
            for i in range(self.tabs.count()):
                old_index = i if i < index else i + 1
                if old_index in self.tab_modified:
                    new_modified[i] = self.tab_modified[old_index]
                if old_index in self.tab_file_paths:
                    new_file_paths[i] = self.tab_file_paths[old_index]
            self.tab_modified = new_modified
            self.tab_file_paths = new_file_paths

            
            
            
            
    # File Functions
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "All Files (*);;Assembly Files (*.asm);;Binary Files (*.bin)"
        )
        
        if file_path:
            for i in range(self.tabs.count()):
                if self.tab_file_paths.get(i) == file_path:
                    self.tabs.setCurrentIndex(i)
                    return
                
            try:
                with open(file_path, 'r', encoding="utf-8") as f:
                    content = f.read()
                    
                file_name = os.path.basename(file_path)
                self.add_new_tab(file_name, file_path, content)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file:\n{str(e)}")
                
                
    def save_file(self):
        index = self.tabs.currentIndex()
        if index < 0:
            return
        
        file_path = self.tab_file_paths.get(index)
        
        if not file_path:
            self.save_file_as()
            return
        
        editor = self.tabs.currentWidget()
        if editor:
            try:
                with open(file_path, 'w', encoding="utf-8") as f:
                    f.write(editor.toPlainText())
                
                self.mark_tab_saved(index) 
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file:\n{str(e)}")
                
    
    def save_file_as(self):
        index = self.tabs.currentIndex()
        if index < 0:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            "",
            "All Files (*);;Assembly Files (*.asm);;Binary Files (*.bin)"
        )
        
        if file_path:
            editor = self.tabs.currentWidget()
            if editor:
                try:
                    with open(file_path, 'w', encoding="utf-8") as f:
                        f.write(editor.toPlainText())
                    
                    file_name = os.path.basename(file_path)
                    self.tabs.setTabText(index, file_name)
                    self.tab_file_paths[index] = file_path
                    self.mark_tab_saved(index)
                    
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not save file:\n{str(e)}")
            
            
            
    # Execution Functions
    def assemble_code(self):
        index = self.tabs.currentIndex()
        if index < 0:
            return
        
        file_path = self.tab_file_paths.get(index)
        
        if not file_path:
            self.save_file_as()
            return
        
        editor = self.tabs.currentWidget()
        if editor:
            try:
                process = subprocess.Popen(
                    "cmd.exe",
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=False
                )
                
                process.stdin.write("cd LC3Assembler\n")
                process.stdin.write(f"py main.py {file_path}\n")
                stdout_data, stderr_data = process.communicate()
                process.stdin.close()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not assemble file:\n{str(e)}")
        
        
            
    
    def stop_code(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    update_assembler()
    app.exec()