import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QComboBox, QPushButton
)
from PyQt5.QtCore import Qt, QEvent

API_KEY = "60673bf6534faf5107032818a95486d0"
API_URL = f"http://api.currencylayer.com/live?access_key={API_KEY}"

CURRENCY_NAMES_RU = {
    "USD": "Доллар США",
    "EUR": "Евро",
    "RUB": "Российский рубль",
    "KZT": "Казахстанский тенге",
    "GBP": "Фунт стерлингов",
    "JPY": "Японская иена",
    "CNY": "Китайский юань",
    "CHF": "Швейцарский франк",
    "AUD": "Австралийский доллар",
    "CAD": "Канадский доллар",
    "UAH": "Украинская гривна",
    "BYN": "Белорусский рубль",
    "INR": "Индийская рупия",
    "BRL": "Бразильский реал",
    "ZAR": "Южноафриканский ранд",
    "SEK": "Шведская крона",
    "NOK": "Норвежская крона",
    "PLN": "Польский злотый",
    "TRY": "Турецкая лира",
    "MXN": "Мексиканское песо",
}


class CurrencyCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Финансовый калькулятор")
        self.setGeometry(300, 200, 520, 600)

        self.last_focused_edit = None
        self._initializing = True
        self.rates = self.get_rates()

        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)

        self.currency_rows = []
        default_currencies = ["RUB", "KZT", "EUR"]

        for cur in default_currencies:
            row = QHBoxLayout()
            row.setSpacing(5)

            combo = QComboBox()
            for code in sorted(self.rates.keys()):
                display = f"{CURRENCY_NAMES_RU.get(code, code)} ({code})"
                combo.addItem(display, code)

            combo.blockSignals(True)
            idx = combo.findData(cur)
            if idx != -1:
                combo.setCurrentIndex(idx)
            combo.blockSignals(False)
            combo.setFixedHeight(60)
            combo.setStyleSheet("font-size: 11pt; padding: 2px;")

            edit = QLineEdit("0")
            edit.setAlignment(Qt.AlignRight)
            edit.setFixedHeight(60)
            edit.setStyleSheet("font-size: 14pt;")
            edit.setFocusPolicy(Qt.ClickFocus)
            edit.installEventFilter(self)

            edit.textChanged.connect(lambda _, e=edit: self.on_value_change(e))
            combo.currentIndexChanged.connect(lambda _, e=edit, c=combo: self.on_currency_change(c, e))

            row.addWidget(combo)
            row.addWidget(edit)
            row.setStretchFactor(combo, 4)
            row.setStretchFactor(edit, 6)

            self.layout.addLayout(row)
            self.currency_rows.append((combo, edit))

        buttons = [
            ["C", "⌫", "%", "/"],
            ["7", "8", "9", "*"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            ["00", "0", ".", "="]
        ]

        for row in buttons:
            hbox = QHBoxLayout()
            for btn_text in row:
                btn = QPushButton(btn_text)
                btn.setFixedSize(80, 60)
                btn.setStyleSheet("font-size: 12pt;")
                btn.setFocusPolicy(Qt.NoFocus)
                btn.clicked.connect(lambda _, t=btn_text: self.on_button_click(t))
                hbox.addWidget(btn)
            self.layout.addLayout(hbox)

        self.setLayout(self.layout)
        self._initializing = False

        if self.currency_rows:
            first_edit = self.currency_rows[0][1]
            first_edit.setFocus()
            self.last_focused_edit = first_edit
            first_edit.setCursorPosition(len(first_edit.text()))

    def get_rates(self):
        try:
            response = requests.get(API_URL, timeout=5)
            data = response.json()
            if not data.get("success"):
                raise Exception(data.get("error", {}).get("info", "Ошибка API"))
            rates = data["quotes"]
            result = {"USD": 1.0}
            for k, v in rates.items():
                result[k[3:]] = v
            return result
        except Exception as e:
            print("Ошибка загрузки курсов:", e)
            return {"USD": 1.0, "RUB": 90.0, "KZT": 500.0, "EUR": 0.92}

    def format_number(self, num: float) -> str:
        return ("{:.3f}".format(num)).rstrip("0").rstrip(".")

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn and isinstance(obj, QLineEdit):
            self.last_focused_edit = obj
            self.on_value_change(obj)
        return super().eventFilter(obj, event)

    def on_value_change(self, edited_field):
        if self._initializing:
            return

        text = edited_field.text().strip()
        if text == "":
            edited_field.setText("0")
            return

        try:
            value = float(edited_field.text())
        except Exception:
            return

        from_code = None
        for combo, edit in self.currency_rows:
            if edit is edited_field:
                from_code = combo.currentData()
                break
        if from_code is None:
            return

        if self.rates.get(from_code, 0) == 0:
            amount_in_usd = 0.0
        else:
            amount_in_usd = value / self.rates[from_code]

        for combo, edit in self.currency_rows:
            if edit is not edited_field:
                cur_code = combo.currentData()
                converted = amount_in_usd * self.rates.get(cur_code, 0.0)
                edit.blockSignals(True)
                edit.setText(self.format_number(converted))
                edit.blockSignals(False)

    def on_currency_change(self, combo, edit):
        if self._initializing:
            return

        source_field = self.last_focused_edit or edit
        self.on_value_change(source_field)

        if self.last_focused_edit:
            self.last_focused_edit.setFocus()
            self.last_focused_edit.setCursorPosition(len(self.last_focused_edit.text()))

    def on_button_click(self, text):
        focused_edit = None
        for _, edit in self.currency_rows:
            if edit.hasFocus():
                focused_edit = edit
                break
        if focused_edit is None:
            focused_edit = self.last_focused_edit
        if not focused_edit:
            return

        current = focused_edit.text()

        if text == "C":
            focused_edit.setText("0")
        elif text == "⌫":
            new_val = current[:-1] if current else ""
            focused_edit.setText(new_val if new_val else "0")
        elif text == "=":
            try:
                result = str(eval(current))
                focused_edit.setText(self.format_number(float(result)))
                self.on_value_change(focused_edit)
            except Exception:
                focused_edit.setText("Ошибка")
        else:
            if current == "0" and text.isdigit():
                focused_edit.setText(text)
            else:
                focused_edit.setText(current + text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CurrencyCalculator()
    window.show()
    sys.exit(app.exec_())
