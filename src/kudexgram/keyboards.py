from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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


@dataclass(frozen=True)
class KeyboardButton:
    text: str

    def to_dict(self) -> dict[str, str]:
        return {"text": self.text}


@dataclass
class ReplyKeyboard:
    _rows: list[list[KeyboardButton]] = field(default_factory=lambda: [[]])
    resize_keyboard: bool = True
    one_time_keyboard: bool = False
    selective: bool = False

    def button(self, text: str) -> ReplyKeyboard:
        if not self._rows:
            self._rows.append([])
        self._rows[-1].append(KeyboardButton(text=text))
        return self

    def row(self) -> ReplyKeyboard:
        if self._rows and not self._rows[-1]:
            return self
        self._rows.append([])
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "keyboard": [
                [button.text for button in row]
                for row in self._rows
                if row
            ],
            "resize_keyboard": self.resize_keyboard,
            "one_time_keyboard": self.one_time_keyboard,
            "selective": self.selective,
        }


@dataclass
class ReplyKeyboardRemove:
    selective: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "remove_keyboard": True,
            "selective": self.selective,
        }
