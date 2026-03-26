COLORS = {
    "bg_darkest": "#0f0f17",
    "bg_dark": "#151520",
    "bg_medium": "#1a1a28",
    "bg_light": "#242438",
    "bg_lighter": "#2e2e48",
    "bg_card": "#1e1e32",
    "bg_hover": "#2a2a44",
    "text_primary": "#e2e4f0",
    "text_secondary": "#a8aec0",
    "text_muted": "#5c6280",
    "accent": "#6c8cff",
    "accent_hover": "#8aa4ff",
    "accent_soft": "#6c8cff22",
    "green": "#5ce0a8",
    "green_soft": "#5ce0a822",
    "yellow": "#ffd06a",
    "yellow_soft": "#ffd06a22",
    "red": "#ff6b8a",
    "red_soft": "#ff6b8a22",
    "peach": "#ffab76",
    "purple": "#b18cff",
    "purple_soft": "#b18cff22",
    "cyan": "#56d4e0",
    "border": "#2a2a42",
    "border_light": "#363658",
    "selection": "#6c8cff33",
    "shadow": "#00000040",
}

# Sidebar icon mappings using Unicode symbols
NAV_ICONS = {
    "Dashboard":        "\u2302",   # House
    "Phones":           "\u260E",   # Phone
    "Glass Protectors": "\u25CE",   # Bullseye
    "Ronin":            "\u2726",   # Star
    "Space":            "\u2726",
    "Login":            "\u2726",
    "Audionic":         "\u2726",
    "Cherry":           "\u2726",
    "Faster":           "\u2726",
    "Orimo":            "\u2726",
    "Taar":             "\u2726",
    "Camera Lens":      "\u25C9",   # Circle
    "Accessories":      "\u2699",   # Gear
    "Phone Cases":      "\u25A3",   # Square
    "Tablets":          "\u25AD",   # Rectangle
    "Transactions":     "\u2263",   # Lines
}


def get_stylesheet() -> str:
    c = COLORS
    return f"""
    /* ── Global ─────────────────────────────────────── */
    * {{
        outline: none;
    }}
    QMainWindow, QWidget {{
        background-color: {c['bg_medium']};
        color: {c['text_primary']};
        font-family: "Segoe UI", "Inter", "Noto Sans", "Ubuntu", "SF Pro Display", sans-serif;
        font-size: 13px;
    }}

    /* ── Top Bar ────────────────────────────────────── */
    #topBar {{
        background-color: {c['bg_darkest']};
        border-bottom: 1px solid {c['border']};
    }}

    /* ── Sidebar ────────────────────────────────────── */
    #sidebar {{
        background-color: {c['bg_dark']};
        border-right: 1px solid {c['border']};
    }}
    #sidebar QPushButton {{
        background-color: transparent;
        color: {c['text_secondary']};
        border: none;
        border-radius: 8px;
        padding: 9px 14px;
        text-align: left;
        font-size: 13px;
        margin: 1px 0px;
    }}
    #sidebar QPushButton:hover {{
        background-color: {c['bg_hover']};
        color: {c['text_primary']};
    }}
    #sidebar QPushButton:checked {{
        background-color: {c['accent_soft']};
        color: {c['accent']};
        font-weight: 600;
        border-left: 3px solid {c['accent']};
        border-radius: 0px 8px 8px 0px;
    }}

    /* ── Search Bar ─────────────────────────────────── */
    #searchBar {{
        background-color: {c['bg_light']};
        border: 1px solid {c['border']};
        border-radius: 10px;
        padding: 9px 16px 9px 36px;
        color: {c['text_primary']};
        font-size: 13px;
    }}
    #searchBar:focus {{
        border-color: {c['accent']};
        background-color: {c['bg_lighter']};
    }}

    /* ── Tables ─────────────────────────────────────── */
    QTableWidget {{
        background-color: {c['bg_dark']};
        alternate-background-color: {c['bg_medium']};
        gridline-color: {c['border']};
        border: 1px solid {c['border']};
        border-radius: 10px;
        color: {c['text_primary']};
        selection-background-color: {c['selection']};
        selection-color: {c['text_primary']};
        font-size: 13px;
    }}
    QTableWidget::item {{
        padding: 8px 12px;
        border-bottom: 1px solid {c['border']};
    }}
    QTableWidget::item:hover {{
        background-color: {c['bg_hover']};
    }}
    QHeaderView::section {{
        background-color: {c['bg_darkest']};
        color: {c['text_muted']};
        border: none;
        border-bottom: 2px solid {c['border']};
        padding: 10px 12px;
        font-weight: 700;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    QHeaderView::section:first {{
        border-top-left-radius: 10px;
    }}
    QHeaderView::section:last {{
        border-top-right-radius: 10px;
    }}

    /* ── Buttons ────────────────────────────────────── */
    QPushButton {{
        background-color: {c['bg_lighter']};
        color: {c['text_primary']};
        border: 1px solid {c['border_light']};
        border-radius: 8px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {c['bg_hover']};
        border-color: {c['text_muted']};
    }}
    QPushButton:pressed {{
        background-color: {c['bg_light']};
    }}
    QPushButton#primaryBtn {{
        background-color: {c['accent']};
        color: #ffffff;
        border: none;
        font-weight: 600;
    }}
    QPushButton#primaryBtn:hover {{
        background-color: {c['accent_hover']};
    }}
    QPushButton#primaryBtn:pressed {{
        background-color: {c['accent']};
    }}
    /* ── Table Action Buttons ──────────────────────── */
    QPushButton#tblEdit {{
        background-color: {c['accent']};
        color: #ffffff;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
        padding: 0;
    }}
    QPushButton#tblEdit:hover {{
        background-color: {c['accent_hover']};
    }}
    QPushButton#tblStockIn {{
        background-color: transparent;
        color: {c['green']};
        border: 1px solid {c['green']};
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
        padding: 0;
    }}
    QPushButton#tblStockIn:hover {{
        background-color: {c['green']};
        color: {c['bg_darkest']};
    }}
    QPushButton#tblSell {{
        background-color: transparent;
        color: {c['cyan']};
        border: 1px solid {c['cyan']};
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
        padding: 0;
    }}
    QPushButton#tblSell:hover {{
        background-color: {c['cyan']};
        color: {c['bg_darkest']};
    }}
    QPushButton#tblDelete {{
        background-color: transparent;
        color: {c['red']};
        border: 1px solid {c['red']};
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
        padding: 0;
    }}
    QPushButton#tblDelete:hover {{
        background-color: {c['red']};
        color: #ffffff;
    }}
    QPushButton#tblReturn {{
        background-color: transparent;
        color: {c['yellow']};
        border: 1px solid {c['yellow']};
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
        padding: 0;
    }}
    QPushButton#tblReturn:hover {{
        background-color: {c['yellow']};
        color: {c['bg_darkest']};
    }}
    QPushButton#tblClaim {{
        background-color: transparent;
        color: {c['purple']};
        border: 1px solid {c['purple']};
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
        padding: 0;
    }}
    QPushButton#tblClaim:hover {{
        background-color: {c['purple']};
        color: #ffffff;
    }}
    QPushButton#tblResolve {{
        background-color: transparent;
        color: {c['peach']};
        border: 1px solid {c['peach']};
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
        padding: 0;
    }}
    QPushButton#tblResolve:hover {{
        background-color: {c['peach']};
        color: {c['bg_darkest']};
    }}

    QPushButton#dangerBtn {{
        background-color: {c['red']};
        color: #ffffff;
        border: none;
        font-weight: 600;
    }}
    QPushButton#dangerBtn:hover {{
        background-color: #ff85a0;
    }}
    QPushButton#successBtn {{
        background-color: {c['green']};
        color: {c['bg_darkest']};
        border: none;
        font-weight: 600;
    }}
    QPushButton#successBtn:hover {{
        background-color: #7aecbe;
    }}

    /* ── Inputs ─────────────────────────────────────── */
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {{
        background-color: {c['bg_light']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 8px 12px;
        color: {c['text_primary']};
        font-size: 13px;
        min-height: 20px;
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus {{
        border-color: {c['accent']};
        background-color: {c['bg_lighter']};
    }}

    /* ── SpinBox ── hide increment/decrement buttons ── */
    QSpinBox::up-button, QDoubleSpinBox::up-button,
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        width: 0;
        height: 0;
        border: none;
    }}

    QComboBox::drop-down {{
        border: none;
        width: 28px;
        subcontrol-position: right center;
    }}
    QComboBox::down-arrow {{
        width: 12px;
        height: 12px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c['bg_light']};
        color: {c['text_primary']};
        selection-background-color: {c['accent']};
        selection-color: #ffffff;
        border: 1px solid {c['border_light']};
        border-radius: 8px;
        padding: 4px;
    }}
    QComboBox QAbstractItemView::item {{
        padding: 6px 12px;
        border-radius: 4px;
    }}
    QComboBox QAbstractItemView::item:hover {{
        background-color: {c['bg_hover']};
    }}

    /* ── Checkbox ───────────────────────────────────── */
    QCheckBox {{
        color: {c['text_primary']};
        spacing: 10px;
        font-size: 13px;
    }}
    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border-radius: 5px;
        border: 2px solid {c['border_light']};
        background-color: {c['bg_light']};
    }}
    QCheckBox::indicator:hover {{
        border-color: {c['accent']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {c['accent']};
        border-color: {c['accent']};
    }}

    /* ── Scrollbar ──────────────────────────────────── */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 8px;
        margin: 4px 2px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {c['border']};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {c['text_muted']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        height: 0;
        background: transparent;
    }}
    QScrollBar:horizontal {{
        background-color: transparent;
        height: 8px;
        margin: 2px 4px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {c['border']};
        border-radius: 4px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {c['text_muted']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        width: 0;
        background: transparent;
    }}

    /* ── Dialog ─────────────────────────────────────── */
    QDialog {{
        background-color: {c['bg_medium']};
        border-radius: 12px;
    }}
    QLabel {{
        color: {c['text_primary']};
    }}
    QGroupBox {{
        color: {c['accent']};
        border: 1px solid {c['border']};
        border-radius: 10px;
        margin-top: 12px;
        padding: 20px 16px 16px 16px;
        font-weight: 600;
        font-size: 13px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 14px;
        padding: 2px 8px;
        color: {c['accent']};
    }}

    /* ── Tab Widget ─────────────────────────────────── */
    QTabWidget::pane {{
        border: 1px solid {c['border']};
        border-radius: 10px;
        background-color: {c['bg_medium']};
    }}
    QTabBar::tab {{
        background-color: {c['bg_dark']};
        color: {c['text_muted']};
        border: none;
        padding: 10px 24px;
        margin-right: 2px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-size: 12px;
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        background-color: {c['bg_medium']};
        color: {c['accent']};
    }}
    QTabBar::tab:hover {{
        background-color: {c['bg_light']};
        color: {c['text_primary']};
    }}

    /* ── Message Box ────────────────────────────────── */
    QMessageBox {{
        background-color: {c['bg_medium']};
    }}
    QMessageBox QLabel {{
        color: {c['text_primary']};
        font-size: 13px;
    }}
    QMessageBox QPushButton {{
        min-width: 80px;
        padding: 8px 20px;
    }}

    /* ── Tooltip ────────────────────────────────────── */
    QToolTip {{
        background-color: {c['bg_lighter']};
        color: {c['text_primary']};
        border: 1px solid {c['border_light']};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }}
    """
