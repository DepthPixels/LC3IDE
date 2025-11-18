import sys, os, subprocess, platform
import qtawesome as qta

from PySide6.QtCore import QSize, Qt, QVariantAnimation, QEasingCurve, QSequentialAnimationGroup, QEvent
from PySide6.QtWidgets import (QApplication, QWidget, QMainWindow, QPushButton, 
                               QPlainTextEdit, QDockWidget, QVBoxLayout, QHBoxLayout,
                               QTabWidget, QTabBar, QTextEdit, QFileDialog, QMessageBox)
from PySide6.QtGui import QColor, QPainter, QTextFormat, QAction


def update_assembler():
    """
    Clones or updates the LC3Assembler repository.
    """
    assembler_path = os.path.join(os.getcwd(), 'LC3Assembler')    # Get the path to the assembler subdirectory.
    process = subprocess.Popen(    # Opens a persistent terminal to execute consecutive commands to clone/update repository.
            "cmd.exe",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False
        )
    if os.path.isdir(assembler_path):
        process.stdin.write("cd LC3Assembler\n")    # Navigate to the assembler directory if it exists.
        process.stdin.write("git pull\n")    # Git Pull to update the local repository.
    else:
        process.stdin.write("git clone https://github.com/DepthPixels/LC3Assembler.git\n")    # Clone the repository if it doesn't exist.
    stdout_data, stderr_data = process.communicate()    # Wait for the terminal process to finish.
    process.stdin.close()    # Close the terminal process.


class DockButton(QPushButton):
    def __init__(self, icon_string, original_color, hover_color):
        super().__init__()
        
        # Variables
        self.icon_string = icon_string
        self.original_color = original_color
        self.hover_color = hover_color
        
        self.setIcon(qta.icon(self.icon_string, color=self.original_color))
        
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
        
        
    def event(self, event):
        if event.type() == QEvent.HoverEnter:
            self.enterDockIcon()
        if event.type() == QEvent.HoverLeave:
            self.leaveDockIcon()
            
        return super().event(event)
    
    def update_icon_size(self, value):
        self.setIconSize(value)
    
    def enterDockIcon(self):
        self.setIcon(qta.icon(self.icon_string, color=self.hover_color))
        self.bounce_group.stop()
        
        current_size = self.iconSize()
        
        # Expand to bigger size
        self.expand_anim.setStartValue(current_size)
        self.expand_anim.setEndValue(QSize(22, 22))
        
        # Contract back to normal hover size
        self.contract_anim.setStartValue(QSize(24, 24))
        self.contract_anim.setEndValue(QSize(20, 20))
        
        self.bounce_group.start()
    
    def leaveDockIcon(self):
        self.setIcon(qta.icon(self.icon_string, color=self.original_color))
        self.bounce_group.stop()
        
        # Simple shrink back
        self.expand_anim.setStartValue(self.iconSize())
        self.expand_anim.setEndValue(QSize(20, 20))
        self.expand_anim.start()



class LineNumberArea(QWidget):
    """
    Custom widget that inherits from QWidget for displaying line numbers in the CodeEditor class.
    """
    def __init__(self, editor):    # Requires a parent CodeEditor
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self) -> QSize:
        """
        Sets this Widget's Size by using the QWidget.sizeHint() method which takens in a QSize() object.
        """
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        """
        QWidget.paintEvent() is called whenever the widget is drawn to the screen, tells it to use the line_number_area_paint_event() method in the parent CodeEditor.
        """
        self.code_editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    """
    Custom Extension of the QPlainTextEdit class to show line numbers and highlight lines if wanted.
    """
    def __init__(self):
        super().__init__()
        self.line_number_area = LineNumberArea(self)    # Create a LineNumberArea Widget and assign this CodeEditor as parent.
        
        # Signals
        self.blockCountChanged.connect(self.update_line_number_area_width)    # QPlainTextEdit().blockCountChanged triggers when the number of lines (blocks) changes.
        self.updateRequest.connect(self.update_line_number_area)    # QPlainTextEdit.updateRequest() is triggered when the text rect has to be redrawn, eg scrolling, connect it to other things that change along with this.
        self.cursorPositionChanged.connect(self.highlight_current_line)    # Connect cursor position change to highlighting to remove previous line highlight and enable current.
        
        # Initial Update
        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def line_number_area_width(self) -> int:
        """
        Calculates the required width for the line count.
        """
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _) -> None:
        """
        Updates the Viewport width depending on the line number area width. Unused parameter is there since the QPlainTextEdit().blockCountChanged() sends the new block count.
        """
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy) -> None:
        """
        Updates the Child Widget that displays the line numbers.
        rect: Area redrawn, QRect()
        dy: Number of pixels scrolled.
        """
        if dy:
            self.line_number_area.scroll(0, dy)    # If the viewport was scrolled, scroll LineNumberArea by the same number of pixels.
        else:
            self.line_number_area.update(0, rect.y(),    # Otherwise just update the child LineNumberArea with the changed area QRect()'s properties.
                                        self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):    # If the entire viewport changes then update the width of the LineNumberArea object.
            self.update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)    # Inherit from the QPlainTextEdit resizeEvent() method.
        cr = self.contentsRect()
        self.line_number_area.setGeometry(cr.left(), cr.top(),    # Set the size of the LineNumberArea to the new dimensions of the CodeEditor.
                                         self.line_number_area_width(), cr.height())

    def line_number_area_paint_event(self, event) -> None:
        """
        Paints the actual line numbers onto the window.
        """
        painter = QPainter(self.line_number_area)    # QPainter is a general purpose utility that allows us to draw stuff, here we're drawing onto the LineNumberArea.
        painter.fillRect(event.rect(), QColor(14, 14, 14))   # Fill the updated rect (the LineNumberArea) with the background color in decimal.

        block = self.firstVisibleBlock()    # Returns the first visible block which is the the block at the top of the screen.
        block_number = block.blockNumber()    # Finds the block number of the block at the top of the screen.
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()    # Gets the bounding box of the block in block coordinates then translates it by the position of the CodeEditor in origin coordinates vertically to find the top of the line number area in origin coordinates.
        bottom = top + self.blockBoundingRect(block).height()
        
        while block.isValid() and top <= event.rect().bottom():   # While the block exists and
            if block.isVisible() and bottom >= event.rect().top():    # While the block is visible and
                number = str(block_number + 1)
                painter.setPen(QColor(133, 133, 133))    # Color of the line number
                painter.drawText(0, int(top), self.line_number_area.width() - 3, 
                               self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, number)    # Draw a right-aligned line number, considering the 3px spacing.

            # Go to the next block
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlight_current_line(self) -> None:
        """
        Adds a highlight to the line the cursor is currently on.
        """
        extra_selections = []
        if not self.isReadOnly():    # Check if the content is read-only first.
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(26, 26, 26)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)    # This method allows us to set the color of extra selections separate from the cursor selection.



class CustomTabBar(QTabBar):
    """
    Extension of the QTabBar class to implement the special hovering functions.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.hovered_tab = -1
    
    
    def mouseMoveEvent(self, event):
        # This code happens before the code of the inherited mouseMoveEvent()
        
        # Find the tab the user is hovering at and store that in self.hovered_tab if it isn't the current one.
        new_hovered = self.tabAt(event.pos())
        if new_hovered != self.hovered_tab:
            old_hovered = self.hovered_tab
            self.hovered_tab = new_hovered
            
            # Update both old and new hovered tabs
            main_window = self.window()
            if hasattr(main_window, 'update_tab_button_state'):
                if old_hovered >= 0:
                    # Set the previously hovered tab to not hover.
                    main_window.update_tab_button_state(old_hovered, False)
                if new_hovered >= 0:
                    # Set the newly hovering tab to hovered.
                    main_window.update_tab_button_state(new_hovered, True)
        # Execute code from inherited mouseMoveEvent().
        super().mouseMoveEvent(event)
    
    def leaveEvent(self, event):
        # Removes hovering effect when the mouse leaves the tab bar.
        if self.hovered_tab >= 0:
            old_hovered = self.hovered_tab
            self.hovered_tab = -1    # Reset to none.
            main_window = self.window()
            # Set the tab to not hovered.
            if hasattr(main_window, 'update_tab_button_state'):
                main_window.update_tab_button_state(old_hovered, False)
        super().leaveEvent(event)


class MainWindow(QMainWindow):
    """
    Main Window of the IDE.
    """
    def __init__(self):
        super().__init__()
        
        # Styling and Sizing        
        self.setWindowTitle("LC3IDE")
        self.setMinimumSize(QSize(1200, 780))
        self.setStyleSheet("background-color: #0e0e0e")
        
        # Variables
        self.tab_modified = {}    # Holds unsaved tabs.
        self.tab_file_paths = {}    # Holds the file paths of the files in the tabs.
        
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
        
        #
        # Tab Bar Code
        #
        
        # Create tab widget with custom tab bar
        self.tabs = QTabWidget()    # The tabs widget will just be the default widget.
        custom_tab_bar = CustomTabBar(self.tabs)
        self.tabs.setTabBar(custom_tab_bar)    # But the bar will be replaced by the CustomTabBar.
        self.tabs.setTabsClosable(False)  # Tab Closing is handled manually with close_tab()
        
        # Tab Styling
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

        # Create the widget that holds in the actions.
        corner_widget = QWidget()
        corner_layout = QHBoxLayout()
        corner_layout.setContentsMargins(4, 0, 4, 0)
        corner_layout.setSpacing(4)

        # Add tab button
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

        # Assemble button
        self.assemble_button = QPushButton()
        self.assemble_button.setIcon(qta.icon("fa6s.gears", color="#858585"))
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

        # Add empty tab
        self.add_new_tab("Untitled-1")

        #
        # Dock Code
        #
        
        # Open File Button
        self.open_button = DockButton("fa6.folder", "#858585", "white")
        self.open_button.setIconSize(QSize(20, 20))
        self.open_button.setFixedSize(QSize(40, 40))
        self.open_button.setFlat(True)
        self.open_button.clicked.connect(self.open_file)
        self.open_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
        """)
        
        # Save File Button
        self.save_button = DockButton("fa6.floppy-disk", "#858585", "white")
        self.save_button.setIconSize(QSize(20, 20))
        self.save_button.setFixedSize(QSize(40, 40))
        self.save_button.setFlat(True)
        self.save_button.clicked.connect(self.save_file)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
        """)
        
        # Save File As Button
        self.save_as_button = DockButton("fa6.hard-drive", "#858585", "white")
        self.save_as_button.setIconSize(QSize(20, 20))
        self.save_as_button.setFixedSize(QSize(40, 40))
        self.save_as_button.setFlat(True)
        self.save_as_button.clicked.connect(self.save_file_as)
        self.save_as_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
        """)
            
        
        # Dock Code
        dock = QDockWidget("Dock", self)
        dock.setTitleBarWidget(QWidget())
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                            Qt.DockWidgetArea.RightDockWidgetArea)
        
        dock_content = QWidget()
        dock_content.setStyleSheet("background-color: #0e0e0e;")
        dock_layout = QVBoxLayout()
        
        # Add Dock Buttons
        dock_layout.addWidget(self.open_button)
        dock_layout.addWidget(self.save_button)
        dock_layout.addWidget(self.save_as_button)
        dock_layout.addStretch()
        dock_content.setLayout(dock_layout)
        dock.setWidget(dock_content)
        
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
               
        
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
    def open_file(self, file_path=""):
        if file_path == False:
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
                if platform.system() == "Windows":
                    process.stdin.write(f"py main.py {file_path}\n")
                else:
                    process.stdin.write(f"python3 main.py {file_path}\n")
                stdout_data, stderr_data = process.communicate()
                process.stdin.close()
                self.open_file(file_path[:-3] + "bin")
                
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