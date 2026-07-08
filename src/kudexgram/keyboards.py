from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class InlineKeyboardButton:
    text: str
    callback_data: str

    def to_dict(self) -> dict[str, str]:
        return {
            "text": self.text,
            "callback_data": self.callback_data,
        }


@dataclass
class InlineKeyboard:
    _rows: list[list[InlineKeyboardButton]] = field(default_factory=lambda: [[]])

    def button(self, text: str, *, callback: str) -> InlineKeyboard:
        if not self._rows:
            self._rows.append([])
        self._rows[-1].append(InlineKeyboardButton(text=text, callback_data=callback))
        return self

    def row(self) -> InlineKeyboard:
        if self._rows and not self._rows[-1]:
            return self
        self._rows.append([])
        return self

    def to_dict(self) -> dict[str, list[list[dict[str, str]]]]:
        return {
            "inline_keyboard": [
                [button.to_dict() for button in row]
                for row in self._rows
                if row
            ]
        }
