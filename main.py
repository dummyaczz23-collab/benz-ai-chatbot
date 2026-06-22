"""
AI Chatbot -- Kivy app
-----------------------
Modern chat UI powered by the free Google Gemini API.
On first launch, it asks for your Gemini API key and saves it locally
on the device (it is never stored in this source code or repo).
"""

import os
import json
import threading

import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup

import requests

MODEL = "gemini-2.5-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

BG_COLOR = (0.07, 0.07, 0.10, 1)
HEADER_COLOR = (0.12, 0.12, 0.16, 1)
USER_BUBBLE = (0.18, 0.42, 0.93, 1)
BOT_BUBBLE = (0.20, 0.20, 0.24, 1)
TEXT_COLOR = (1, 1, 1, 1)
INPUT_BG = (0.15, 0.15, 0.18, 1)


class Bubble(BoxLayout):
    """A single rounded chat bubble, aligned left (bot) or right (user)."""

    def __init__(self, text, color, align_right, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(10),
            padding=(dp(10), dp(2)),
            **kwargs,
        )
        self.label = Label(
            text=text,
            color=TEXT_COLOR,
            size_hint=(None, None),
            text_size=(Window.width * 0.72, None),
            halign="left",
            valign="middle",
            padding=(dp(12), dp(10)),
        )
        self.label.bind(texture_size=self._update_label_size)

        with self.label.canvas.before:
            Color(*color)
            self._rect = RoundedRectangle(radius=[dp(16)])
        self.label.bind(pos=self._update_rect, size=self._update_rect)

        spacer = BoxLayout()
        if align_right:
            self.add_widget(spacer)
            self.add_widget(self.label)
        else:
            self.add_widget(self.label)
            self.add_widget(spacer)

    def _update_label_size(self, instance, size):
        instance.size = size
        self.height = size[1] + dp(8)

    def _update_rect(self, instance, value):
        self._rect.pos = instance.pos
        self._rect.size = instance.size


class Header(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(size_hint=(1, None), height=dp(52), **kwargs)
        with self.canvas.before:
            Color(*HEADER_COLOR)
            self._rect = RoundedRectangle(radius=[0])
        self.bind(pos=self._update_rect, size=self._update_rect)
        title = Label(text="AI Chatbot", color=TEXT_COLOR, bold=True, font_size=dp(18))
        self.add_widget(title)

    def _update_rect(self, instance, value):
        self._rect.pos = instance.pos
        self._rect.size = instance.size


class ChatApp(App):
    def build(self):
        Window.clearcolor = BG_COLOR
        self.title = "AI Chat"
        self.api_key = self._load_api_key()
        self._typing_bubble = None

        root = BoxLayout(orientation="vertical")
        root.add_widget(Header())

        self.scroll = ScrollView(size_hint=(1, 1), bar_width=dp(4))
        self.messages = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(6), padding=dp(10)
        )
        self.messages.bind(minimum_height=self.messages.setter("height"))
        self.scroll.add_widget(self.messages)
        root.add_widget(self.scroll)

        input_row = BoxLayout(size_hint=(1, None), height=dp(56), padding=dp(6), spacing=dp(6))
        self.text_input = TextInput(
            hint_text="Type a message...",
            multiline=False,
            background_color=INPUT_BG,
            foreground_color=TEXT_COLOR,
            hint_text_color=(0.6, 0.6, 0.6, 1),
            cursor_color=TEXT_COLOR,
            padding=(dp(12), dp(14)),
        )
        self.text_input.bind(on_text_validate=self.on_send)

        send_btn = Button(
            text="Send", size_hint=(None, 1), width=dp(80),
            background_normal="", background_color=USER_BUBBLE, color=TEXT_COLOR,
        )
        send_btn.bind(on_release=self.on_send)

        input_row.add_widget(self.text_input)
        input_row.add_widget(send_btn)
        root.add_widget(input_row)

        self.conversation = []
        self._add_bubble("Hi! Ask me anything.", BOT_BUBBLE, align_right=False)

        if not self.api_key:
            Clock.schedule_once(lambda dt: self._prompt_for_api_key(), 0.2)

        return root

    # ---------- API key storage (local to this device, never in source) ----------
    def _config_path(self):
        return os.path.join(self.user_data_dir, "config.json")

    def _load_api_key(self):
        path = self._config_path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f).get("api_key", "")
            except Exception:
                return ""
        return ""

    def _save_api_key(self, key):
        os.makedirs(self.user_data_dir, exist_ok=True)
        with open(self._config_path(), "w") as f:
            json.dump({"api_key": key}, f)

    def _prompt_for_api_key(self):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))
        info = Label(
            text="Paste your free Gemini API key.\nGet one at aistudio.google.com/app/apikey",
            color=TEXT_COLOR, size_hint_y=None, height=dp(60), halign="center",
        )
        info.bind(size=lambda i, v: setattr(i, "text_size", v))
        key_input = TextInput(hint_text="API key", multiline=False, size_hint_y=None, height=dp(48))
        save_btn = Button(text="Save", size_hint_y=None, height=dp(48),
                           background_normal="", background_color=USER_BUBBLE)

        content.add_widget(info)
        content.add_widget(key_input)
        content.add_widget(save_btn)

        popup = Popup(title="One-time setup", content=content,
                       size_hint=(0.85, 0.5), auto_dismiss=False)

        def on_save(instance):
            key = key_input.text.strip()
            if key:
                self.api_key = key
                self._save_api_key(key)
                popup.dismiss()

        save_btn.bind(on_release=on_save)
        popup.open()

    # ---------- Chat logic ----------
    def _add_bubble(self, text, color, align_right):
        bubble = Bubble(text, color, align_right)
        self.messages.add_widget(bubble)
        Clock.schedule_once(lambda dt: setattr(self.scroll, "scroll_y", 0), 0.05)
        return bubble

    def on_send(self, *args):
        if not self.api_key:
            self._prompt_for_api_key()
            return
        text = self.text_input.text.strip()
        if not text:
            return
        self.text_input.text = ""
        self._add_bubble(text, USER_BUBBLE, align_right=True)
        self.conversation.append({"role": "user", "parts": [{"text": text}]})
        self._typing_bubble = self._add_bubble("...", BOT_BUBBLE, align_right=False)
        threading.Thread(target=self._fetch_reply, daemon=True).start()

    def _fetch_reply(self):
        reply = ask_gemini(self.conversation, self.api_key)
        Clock.schedule_once(lambda dt: self._show_reply(reply))

    def _show_reply(self, reply):
        if self._typing_bubble in self.messages.children:
            self.messages.remove_widget(self._typing_bubble)
        self._add_bubble(reply, BOT_BUBBLE, align_right=False)
        self.conversation.append({"role": "model", "parts": [{"text": reply}]})


def ask_gemini(conversation, api_key):
    headers = {"content-type": "application/json"}
    payload = {"contents": conversation}
    params = {"key": api_key}

    try:
        response = requests.post(
            API_URL, headers=headers, params=params,
            data=json.dumps(payload), timeout=30,
        )
    except requests.exceptions.RequestException as e:
        return f"[Network error: {e}]"

    if response.status_code != 200:
        return f"[API error {response.status_code}: {response.text[:200]}]"

    data = response.json()
    candidates = data.get("candidates")
    if not candidates:
        return f"[Blocked or empty response: {data.get('promptFeedback', {})}]"

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        return "[Empty reply]"

    return parts[0].get("text", "[Empty text]")


if __name__ == "__main__":
    ChatApp().run()
