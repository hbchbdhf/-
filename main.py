# -*- coding: utf-8 -*-
"""
弹窗视觉小说 · 手机版（Kivy）
============================
同一份剧情（game_data.py，从 youxi.py 抽取），界面改用 Kivy，
因为安卓上没有 tkinter。玩法与桌面版一致：

  剧情页：点正文/按空格跳过打字动画；选项按钮；数字键 1-9 也可选
  战斗页：先选特殊能力（防御/护盾/治疗，数值随机），再回合制对打

桌面试玩：  python main.py
打包 APK：  见 README.md（云端 buildozer 构建）
"""

import os
import random
import sys
import time
import traceback

os.environ.setdefault("KIVY_NO_ARGS", "1")


# ============================================================
#  崩溃诊断
#  手机上没法看 logcat，所以把启动阶段和异常写进应用私有目录，
#  下次启动时直接把日志贴在屏幕上（可以截图发出来）。
# ============================================================
def _diag_dir():
    for key in ("ANDROID_PRIVATE", "ANDROID_APP_PATH"):
        p = os.environ.get(key)
        if p and os.path.isdir(p):
            return p
    return os.path.dirname(os.path.abspath(__file__))


_LOG_DIR = _diag_dir()
_BOOT_LOG = os.path.join(_LOG_DIR, "boot.log")
_CRASH_LOG = os.path.join(_LOG_DIR, "crash.log")


def _diag(msg, reset=False):
    try:
        with open(_BOOT_LOG, "w" if reset else "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), msg))
    except Exception:
        pass


def _read_text(path, limit=6000):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()[:limit]
    except Exception:
        return ""


def _install_crash_hook():
    def hook(exc_type, exc, tb):
        text = "".join(traceback.format_exception(exc_type, exc, tb))
        try:
            with open(_CRASH_LOG, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass
        tail = text.strip().splitlines()[-1] if text.strip() else "?"
        _diag("CRASH: " + tail)

    sys.excepthook = hook


_install_crash_hook()
_diag("boot: 进程启动 (py %s)" % sys.version.split()[0], reset=True)

from kivy.config import Config

_diag("boot: kivy.config 加载完成")

# 桌面调试时的窗口大小，手机上一律全屏，这几个值不起作用。
# 高分屏（150%/200% 缩放）下 Kivy 逻辑坐标 = 像素 x 缩放倍数，
# 所以窗口要按系统 DPI 放大，否则右半边内容会被裁掉。
_scale = 1.0
# 注意：p4a 里 sys.platform 是 'linux'，要用它注入的环境变量判断
_IS_ANDROID = bool(os.environ.get("ANDROID_ARGUMENT")
                   or os.environ.get("ANDROID_PRIVATE"))
if sys.platform == "win32":
    try:
        import ctypes as _ctypes
        _ctypes.windll.shcore.SetProcessDpiAwareness(1)
        _scale = _ctypes.windll.user32.GetDpiForSystem() / 96.0
    except Exception:
        pass
if not _IS_ANDROID:
    Config.set("graphics", "width", str(int(430 * _scale)))
    Config.set("graphics", "height", str(int(780 * _scale)))
    Config.set("graphics", "resizable", "1")

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, RoundedRectangle

_diag("boot: kivy 控件导入完成")

from game_data import SCENES

_diag("boot: 剧情数据载入，共 %d 个场景" % len(SCENES))

# ============================================================
#  中文字体：不注册的话安卓上全是方框
# ============================================================
_HERE = os.path.dirname(os.path.abspath(__file__))


def _find_font():
    """按优先级找一个能显示中文的字体"""
    candidates = [
        os.path.join(_HERE, "NotoSansSC.ttf"),
        os.path.join(_HERE, "assets", "NotoSansSC.ttf"),
        "/system/fonts/NotoSansCJK-Regular.ttc",
        "/system/fonts/NotoSansSC-Regular.otf",
        "/system/fonts/NotoSansHans-Regular.otf",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyh.ttf",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


_FONT = _find_font()
if _FONT:
    # 覆盖默认的 Roboto，所有控件（含 kv 默认样式）都会用这套中文字体
    try:
        LabelBase.register(
            name="Roboto",
            fn_regular=_FONT,
            fn_bold=_FONT,
            fn_italic=_FONT,
            fn_bolditalic=_FONT,
        )
        _diag("boot: 注册中文字体 %s" % _FONT)
    except Exception:
        _diag("boot: 字体注册失败 %s" % traceback.format_exc().strip().splitlines()[-1])
else:
    _diag("boot: 没找到中文字体，可能显示方框")

# ============================================================
#  配色（与桌面版一致）
# ============================================================
BG = "#15151a"
PANEL = "#1e1e26"
LINE = "#2c2c36"
TEXT = "#e9e7e2"
MUTED = "#77757f"
ACCENT = "#e3b567"
ACCENT_HOVER = "#f0c67e"
GOLD = "#d3ab61"
BADGE_BG = "#2b2519"
BTN_BG = "#272730"
BTN_HOVER = "#343441"
BTN_TEXT = "#1a1a1e"

# 战斗页配色（与 play.py 一致）
B_BG = "#eef1f6"
B_CARD = "#ffffff"
B_BORDER = "#dfe4ea"
B_TEXT = "#2d3436"
B_SUBTEXT = "#7f8c8d"
B_PLAYER = "#2e9e5b"
B_ENEMY = "#d9534f"
B_BAR_BG = "#e4e7ec"
B_HEAL = "#2e86de"


def rgba(hex_color, alpha=1.0):
    h = hex_color.lstrip("#")
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)] + [alpha]


# ============================================================
#  战斗数值（与 play.py 一致）
# ============================================================
PLAYER_MAX_HP = 100
ENEMY_MAX_HP = 100
PLAYER_ATK = 15
ENEMY_ATK = 15
PLAYER_CRIT_RATE = 0.5
ENEMY_CRIT_RATE = 0.5
ENEMY_NAME = "赵某某"

SKILL_NAMES = {"defense": "随机防御", "shield": "护盾", "heal": "治疗"}
SKILL_COLORS = {"defense": "#8e44ad", "shield": "#2e86de", "heal": "#2e9e5b"}


def roll_skill(kind=None):
    if kind is None:
        kind = random.choice(["defense", "shield", "heal"])
    if kind == "defense":
        lo = random.randint(2, 5)
        hi = lo + random.randint(4, 9)
        return {"kind": kind, "lo": lo, "hi": hi}
    if kind == "shield":
        total = random.randint(40, 70)
        return {"kind": kind, "shield": total, "max_shield": total}
    mode = random.choice(["passive", "full"])
    if mode == "passive":
        return {"kind": kind, "mode": mode, "heal": random.randint(4, 8)}
    return {"kind": kind, "mode": mode,
            "threshold": random.randint(25, 40), "used": False}


def skill_title(s):
    return SKILL_NAMES[s["kind"]]


def skill_detail(s):
    if s["kind"] == "defense":
        return f"每次受击随机减免 {s['lo']}~{s['hi']} 点伤害"
    if s["kind"] == "shield":
        return f"吸收伤害（剩余 {max(s['shield'], 0)} / {s['max_shield']}）"
    if s["mode"] == "passive":
        return f"攻击时后台回复 {s['heal']} 点生命"
    used = "已触发" if s["used"] else "每场一次"
    return f"生命低于 {s['threshold']} 时回满血，该回合无法攻击（{used}）"


def skill_intro(kind):
    return {
        "defense": "每次受击随机减免一部分伤害\n（减免范围随机）",
        "shield": "获得 40~70 点护盾\n先于生命值承受伤害",
        "heal": "随机获得「边打边回」\n或「低血量回满、当回合不能攻击」",
    }[kind]


def roll_damage(atk, crit_rate, crit_dmg):
    if random.random() < crit_rate:
        return round(atk * (1 + crit_dmg)), True
    return atk, False


def mitigate(skill, dmg):
    notes = []
    if skill["kind"] == "defense":
        blocked = min(random.randint(skill["lo"], skill["hi"]), dmg)
        dmg -= blocked
        notes.append(f"随机防御挡下 {blocked} 点伤害")
    elif skill["kind"] == "shield" and skill["shield"] > 0:
        absorbed = min(skill["shield"], dmg)
        skill["shield"] -= absorbed
        dmg -= absorbed
        notes.append(f"护盾吸收 {absorbed} 点伤害")
        if skill["shield"] <= 0:
            notes.append("护盾被击碎")
    return max(dmg, 0), notes


# ============================================================
#  基础控件
# ============================================================
class FlatButton(Button):
    """圆角扁按钮：Kivy 默认按钮太有年代感，这里全部自绘"""

    bg_color = ListProperty(rgba(BTN_BG))
    press_color = ListProperty(rgba(BTN_HOVER))
    radius = NumericProperty(dp(10))

    def __init__(self, **kw):
        kw.setdefault("background_normal", "")
        kw.setdefault("background_down", "")
        kw.setdefault("background_color", (0, 0, 0, 0))
        super().__init__(**kw)
        self._base_color = list(self.bg_color)
        with self.canvas.before:
            self._color = Color(*self.bg_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size,
                                          radius=[self.radius])
        self.bind(pos=self._sync, size=self._sync,
                  bg_color=self._sync_color)

    def _sync(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size
        self._rect.radius = [self.radius]

    def _sync_color(self, *_):
        self._color.rgba = self.bg_color

    def on_press(self):
        self.bg_color = list(self.press_color)

    def on_release(self):
        self.bg_color = list(self._base_color)


class TextButton(FlatButton):
    """自动换行的按钮文字：手机屏窄，长选项要能折行"""

    def __init__(self, **kw):
        kw.setdefault("halign", "left")
        kw.setdefault("valign", "middle")
        kw.setdefault("font_size", sp(14))
        super().__init__(**kw)
        self.text_size = (self.width - dp(30), None)
        self.bind(size=self._fit)

    def _fit(self, *_):
        self.text_size = (max(dp(40), self.width - dp(30)), None)


class HPBar(Widget):
    hp = NumericProperty(0)
    max_hp = NumericProperty(100)
    fill_color = ListProperty([0.18, 0.62, 0.36, 1])

    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas:
            self._bg = Color(*rgba(B_BAR_BG))
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size,
                                             radius=[self.height / 2])
            self._fg = Color(*self.fill_color)
            self._fg_rect = RoundedRectangle(pos=self.pos, size=self.size,
                                             radius=[self.height / 2])
        self.bind(pos=self._redraw, size=self._redraw, hp=self._redraw,
                  max_hp=self._redraw, fill_color=self._redraw)
        self._redraw()

    def _redraw(self, *_):
        r = max(self.height / 2.0, 1)
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self._bg_rect.radius = [r]
        ratio = 0.0 if self.max_hp <= 0 else max(0.0, min(1.0, self.hp / self.max_hp))
        w = max(self.width * ratio, 0)
        self._fg.rgba = self.fill_color
        self._fg_rect.pos = self.pos
        self._fg_rect.size = (w, self.height)
        self._fg_rect.radius = [r]


class HLine(Widget):
    """1px 分隔线"""

    def __init__(self, color=LINE, **kw):
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", dp(1))
        super().__init__(**kw)
        with self.canvas:
            self._c = Color(*rgba(color))
            self._r = RoundedRectangle(pos=self.pos, size=self.size, radius=[0])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._r.pos = self.pos
        self._r.size = self.size


def make_label(text="", size=14, color=TEXT, bold=False, halign="left",
               valign="middle", **kw):
    lbl = Label(text=text, font_size=sp(size), color=rgba(color),
                bold=bold, halign=halign, valign=valign, markup=kw.pop("markup", False),
                **kw)
    lbl.bind(width=lambda *_: setattr(lbl, "text_size", (lbl.width, None)))
    return lbl


# ============================================================
#  剧情页
# ============================================================
class NovelScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        self.scenes = SCENES
        self.current = None
        self.current_key = None
        self.choices_visible = False

        self.full_text = ""
        self.type_pos = 0
        self.typing = False
        self.tick_event = None
        self._touch_start = None

        root = BoxLayout(orientation="vertical",
                         padding=[dp(16), dp(12), dp(16), dp(10)],
                         spacing=dp(6))

        # ---- 顶栏：标题 / 结局徽章 / 重来 ----
        header = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
        self.title_label = make_label("", size=15, color=ACCENT, bold=True)
        header.add_widget(self.title_label)

        self.badge = FlatButton(text="", font_size=sp(11),
                                size_hint=(None, 1), width=dp(0), opacity=0,
                                bg_color=rgba(BADGE_BG))
        self.badge.width = dp(84)
        header.add_widget(self.badge)

        restart = FlatButton(text="重来", font_size=sp(12),
                             size_hint=(None, 1), width=dp(54),
                             color=rgba(TEXT))
        restart.bind(on_release=lambda *_: self.restart())
        header.add_widget(restart)
        root.add_widget(header)

        root.add_widget(HLine())

        # ---- 正文 ----
        self.sv = ScrollView(do_scroll_x=False, bar_width=dp(3),
                             bar_color=rgba("#454555"),
                             bar_inactive_color=rgba("#31313c"))
        self.body = make_label("", size=15.5, color=TEXT, halign="left",
                               valign="top")
        self.body.text_size = (dp(300), None)
        self.body.size_hint_y = None
        self.body.height = dp(60)
        self.body.bind(texture_size=lambda *_: self._body_resize())
        self.inner = BoxLayout(orientation="vertical", size_hint_y=None,
                               padding=[dp(14), dp(12)])
        self.inner.bind(minimum_height=self.inner.setter("height"))
        self.inner.add_widget(self.body)
        self.sv.add_widget(self.inner)
        self.inner.bind(width=lambda *_: self._body_resize())
        root.add_widget(self.sv)

        # ---- 提示 ----
        self.hint = make_label("", size=11, color=MUTED)
        self.hint.size_hint_y = None
        self.hint.height = dp(18)
        root.add_widget(self.hint)

        # ---- 选项区 ----
        self.choices = BoxLayout(orientation="vertical", spacing=dp(7),
                                 size_hint_y=None, padding=[0, 0, 0, dp(4)])
        self.choices.bind(minimum_height=self.choices.setter("height"))
        root.add_widget(self.choices)

        self.add_widget(root)
        self.go_to("start")

    # ---------- 排版 ----------
    def _body_resize(self, *_):
        width = max(self.inner.width - dp(28), dp(120))
        self.body.text_size = (width, None)
        self.body.height = self.body.texture_size[1]

    # ---------- 场景切换 ----------
    def go_to(self, key):
        scene = self.scenes.get(key)
        if scene is None:
            scene = {
                "title": "脚本错误",
                "ending": "出错了",
                "text": (f"找不到名为「{key}」的场景。\n\n"
                         "请检查 SCENES 里是否写了这个键，"
                         "以及选项的 next 有没有拼错。"),
            }
        self.current = scene
        self.current_key = key
        self._clear_choices()
        self.title_label.text = scene.get("title", "")

        ending = scene.get("ending")
        if ending:
            label = ending if isinstance(ending, str) else "结局"
            self.badge.text = label
            self.badge.opacity = 1
            self.badge.width = dp(84)
        else:
            self.badge.text = ""
            self.badge.opacity = 0
            self.badge.width = dp(0)

        self.hint.text = "点正文跳过文字动画"
        self._start_typing(scene.get("text", ""))

    def restart(self):
        self.go_to("start")

    def _clear_choices(self):
        self.choices_visible = False
        self.choices.clear_widgets()

    # ---------- 打字机 ----------
    def _start_typing(self, text):
        self._cancel_typing()
        self.full_text = text or ""
        self.type_pos = 0
        self.typing = True
        self.body.text = ""
        self.sv.scroll_y = 1
        self._need_scroll = False
        self.tick_event = Clock.schedule_interval(self._tick, 0.024)

    def _tick(self, _dt):
        if not self.typing:
            return False
        if self.type_pos >= len(self.full_text):
            self._finish_typing()
            return False
        end = min(self.type_pos + 2, len(self.full_text))
        self.body.text = self.full_text[:end]
        self.type_pos = end
        Clock.schedule_once(self._scroll_follow, 0)
        return True

    def _cancel_typing(self):
        if self.tick_event is not None:
            self.tick_event.cancel()
            self.tick_event = None

    def _skip_typing(self):
        if not self.typing:
            return
        self._cancel_typing()
        self._finish_typing()
        self.sv.scroll_y = 1

    def _finish_typing(self):
        if self.type_pos < len(self.full_text):
            self.body.text = self.full_text
            self.type_pos = len(self.full_text)
        self.typing = False
        self.tick_event = None
        self._scroll_bottom()
        if not self.choices_visible:
            self._show_choices()

    def _scroll_follow(self, *_):
        """内容超过视口才跟着滚到底，否则保持顶部"""
        if self.body.height > self.sv.height:
            self.sv.scroll_y = 0

    def _scroll_bottom(self):
        self.sv.scroll_y = 0 if self.body.height > self.sv.height else 1

    # ---------- 选项 ----------
    def _show_choices(self):
        if self.choices_visible:
            return
        self.choices_visible = True

        scene = self.current or {}
        if scene.get("ending"):
            self.hint.text = "已抵达结局"
            self._add_button("重新开始", self.restart, accent=True)
            self._add_button("退出游戏", self.app.stop)
        elif scene.get("choices"):
            self.hint.text = "选一个（数字键也行）"
            for index, choice in enumerate(scene["choices"][:9], start=1):
                label = choice.get("label", f"选项 {index}")
                self._add_button(f"{index}   {label}",
                                 lambda c=choice: self._choose(c))
        elif scene.get("next"):
            self.hint.text = "点正文或按下面继续"
            self._add_button("继续  →",
                             lambda: self.go_to(scene["next"]), accent=True)
        else:
            self.hint.text = "这个场景既没有选项，也没有结局标记"
            self._add_button("重新开始", self.restart)

    def _add_button(self, text, command, accent=False):
        btn = TextButton(text=text, size_hint_y=None, height=dp(46),
                         color=rgba(BTN_TEXT if accent else TEXT),
                         bg_color=rgba(ACCENT if accent else BTN_BG),
                         press_color=rgba(ACCENT_HOVER if accent else BTN_HOVER))
        btn.bind(on_release=lambda *_: command())
        self.choices.add_widget(btn)

    def _choose(self, choice):
        if not isinstance(choice, dict):
            return
        if choice.get("pvp"):
            self.hint.text = "战斗中……打完剧情会自己接下去"
            self.app.start_battle(
                win_key=choice.get("win", "win"),
                lose_key=choice.get("lose", "lose"),
                abort_key=choice.get("abort", self.current_key),
            )
            return
        if choice.get("next"):
            self.go_to(choice["next"])

    # ---------- 触摸：点正文跳过 / 继续 ----------
    def on_touch_down(self, touch):
        if self.sv.collide_point(touch.x, touch.y) and self.body.collide_point(touch.x, touch.y):
            self._touch_start = (touch.x, touch.y)
        else:
            self._touch_start = None
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._touch_start:
            dx = abs(touch.x - self._touch_start[0])
            dy = abs(touch.y - self._touch_start[1])
            self._touch_start = None
            if dx < dp(12) and dy < dp(12):
                self.tap_advance()
        return super().on_touch_up(touch)

    def tap_advance(self):
        if self.typing:
            self._skip_typing()
            return
        cur = self.current or {}
        if not cur.get("ending") and not cur.get("choices") and cur.get("next"):
            self.go_to(cur["next"])

    def key_choice(self, n):
        if self.typing or not self.choices_visible or not self.current:
            return
        choices = self.current.get("choices") or []
        if 1 <= n <= len(choices):
            self._choose(choices[n - 1])


# ============================================================
#  战斗页
# ============================================================
class BattleScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        self.on_finish = None
        self.player_skill = None
        self.enemy_skill = None
        self.player_hp = PLAYER_MAX_HP
        self.enemy_hp = ENEMY_MAX_HP
        self.player_crit_dmg = 0.5
        self.enemy_crit_dmg = 0.5
        self.log_lines = []
        self.finished = False

        self.box = BoxLayout(orientation="vertical",
                              padding=[dp(14), dp(14), dp(14), dp(14)],
                              spacing=dp(8))
        with self.box.canvas.before:
            self._bg = Color(*rgba(B_BG))
            self._bg_rect = RoundedRectangle(pos=self.box.pos,
                                             size=self.box.size, radius=[0])
        self.box.bind(pos=self._sync_bg, size=self._sync_bg)
        self.add_widget(self.box)
        self.show_select()

    def _sync_bg(self, *_):
        self._bg_rect.pos = self.box.pos
        self._bg_rect.size = self.box.size

    # ---------- 选择能力 ----------
    def show_select(self):
        self.box.clear_widgets()
        title = make_label("战斗游戏", size=22, color=B_TEXT, bold=True,
                           halign="center")
        title.size_hint_y = None
        title.height = dp(52)
        self.box.add_widget(title)

        sub = make_label(f"{ENEMY_NAME} 向你发起挑战！", size=13, color=B_SUBTEXT,
                         halign="center")
        sub.size_hint_y = None
        sub.height = dp(24)
        self.box.add_widget(sub)

        ask = make_label("选择你的特殊能力", size=15, color=B_TEXT, bold=True,
                         halign="center")
        ask.size_hint_y = None
        ask.height = dp(46)
        self.box.add_widget(ask)

        for kind in ("defense", "shield", "heal"):
            card = BoxLayout(orientation="vertical", size_hint_y=None,
                             height=dp(96), padding=[dp(12), dp(8)],
                             spacing=dp(2))
            with card.canvas.before:
                Color(*rgba(B_CARD))
                card._rect = RoundedRectangle(pos=card.pos, size=card.size,
                                              radius=[dp(12)])
                card._line = Color(*rgba(B_BORDER))
                card._stroke = Line(rounded_rectangle=(card.x, card.y,
                                                       card.width, card.height,
                                                       dp(12)), width=1)
            card.bind(pos=lambda w, *_: (
                setattr(w._rect, "pos", w.pos), setattr(w._rect, "size", w.size),
                setattr(w._stroke, "rounded_rectangle", (w.x, w.y, w.width,
                                                          w.height, dp(12)))))
            card.bind(size=lambda w, *_: (
                setattr(w._rect, "size", w.size),
                setattr(w._stroke, "rounded_rectangle", (w.x, w.y, w.width,
                                                          w.height, dp(12)))))
            name = make_label(SKILL_NAMES[kind], size=15, color=SKILL_COLORS[kind],
                              bold=True, halign="center")
            name.size_hint_y = None
            name.height = dp(28)
            detail = make_label(skill_intro(kind), size=12, color=B_TEXT,
                                halign="center")
            card.add_widget(name)
            card.add_widget(detail)

            wrapper = BoxLayout(orientation="vertical", size_hint_y=None,
                                height=dp(96))
            wrapper.add_widget(card)
            card.bind(on_touch_down=self._make_tap(kind))
            self.box.add_widget(wrapper)

        self.box.add_widget(Widget())
        tip = make_label(f"对手 {ENEMY_NAME} 的特殊能力随机生成", size=11,
                         color=B_SUBTEXT, halign="center")
        tip.size_hint_y = None
        tip.height = dp(30)
        self.box.add_widget(tip)

        back = FlatButton(text="返回剧情", font_size=sp(14),
                          size_hint_y=None, height=dp(44),
                          color=rgba("#ffffff"), bg_color=rgba("#8e8e99"),
                          press_color=rgba("#7c7c88"))
        back.bind(on_release=lambda *_: self.app.back_to_novel())
        self.box.add_widget(back)

    def _make_tap(self, kind):
        def handler(_, touch):
            if self.collide_point(*touch.pos):
                self.start_battle(roll_skill(kind))
                return True
            return False
        return handler

    # ---------- 战斗界面 ----------
    def start_battle(self, player_skill):
        self.player_skill = player_skill
        self.enemy_skill = roll_skill()
        self.player_hp = PLAYER_MAX_HP
        self.enemy_hp = ENEMY_MAX_HP
        self.player_crit_dmg = round(random.uniform(0.2, 0.8), 2)
        self.enemy_crit_dmg = round(random.uniform(0.2, 0.8), 2)
        self.finished = False
        self.log_lines = []

        self.box.clear_widgets()

        title = make_label("战斗游戏", size=20, color=B_TEXT, bold=True,
                           halign="center")
        title.size_hint_y = None
        title.height = dp(40)
        self.box.add_widget(title)

        self.player_card = self._build_card("你", B_PLAYER, PLAYER_ATK,
                                            PLAYER_CRIT_RATE,
                                            self.player_crit_dmg, player_skill)
        self.box.add_widget(self.player_card["root"])

        vs = make_label("VS", size=12, color=B_SUBTEXT, bold=True, halign="center")
        vs.size_hint_y = None
        vs.height = dp(20)
        self.box.add_widget(vs)

        self.enemy_card = self._build_card(ENEMY_NAME, B_ENEMY, ENEMY_ATK,
                                           ENEMY_CRIT_RATE,
                                           self.enemy_crit_dmg, self.enemy_skill)
        self.box.add_widget(self.enemy_card["root"])

        # ---- 日志 ----
        self.log_sv = ScrollView(do_scroll_x=False, bar_width=dp(2),
                                 bar_color=rgba("#c9ced6"),
                                 bar_inactive_color=rgba("#e4e7ec"))
        log_box = BoxLayout(orientation="vertical", size_hint_y=None,
                            padding=[dp(10), dp(8)], spacing=dp(2))
        with log_box.canvas.before:
            Color(*rgba(B_CARD))
            self._log_bg = RoundedRectangle(pos=log_box.pos, size=log_box.size,
                                            radius=[dp(10)])
        log_box.bind(pos=lambda w, *_: (setattr(self._log_bg, "pos", w.pos),
                                        setattr(self._log_bg, "size", w.size)))
        log_box.bind(size=lambda w, *_: setattr(self._log_bg, "size", w.size))

        self.log_label = Label(text="", font_size=sp(13), color=rgba(B_TEXT),
                               halign="left", valign="top", markup=True,
                               size_hint_y=None, padding=(dp(10), dp(8)))
        self.log_label.bind(width=lambda *_: setattr(
            self.log_label, "text_size", (self.log_label.width, None)))
        self.log_label.bind(texture_size=lambda *_: setattr(
            self.log_label, "height", self.log_label.texture_size[1]))
        log_box.add_widget(self.log_label)
        log_box.bind(minimum_height=lambda w, v: setattr(w, "height", v))
        self.log_sv.add_widget(log_box)
        self.log_box = log_box
        self.box.add_widget(self.log_sv)

        # ---- 按钮 ----
        self.btn_area = BoxLayout(size_hint_y=None, height=dp(56))
        self.btn_attack = FlatButton(text="攻击！", font_size=sp(16), bold=True,
                                     color=rgba("#ffffff"),
                                     bg_color=rgba(B_PLAYER),
                                     press_color=rgba("#268a4e"))
        self.btn_attack.bind(on_release=lambda *_: self.attack())
        self.btn_area.add_widget(self.btn_attack)
        self.box.add_widget(self.btn_area)

        self.log(f"战斗开始！{ENEMY_NAME}向你发起挑战。")
        self.log(f"你的特殊能力：{skill_title(player_skill)}——{skill_detail(player_skill)}")
        self.log(f"{ENEMY_NAME}的特殊能力：{skill_title(self.enemy_skill)}——{skill_detail(self.enemy_skill)}")
        self._refresh()

    def _build_card(self, name, color, atk, crit_rate, crit_dmg, skill):
        card = BoxLayout(orientation="vertical", size_hint_y=None,
                         height=dp(112), padding=[0, 0, 0, dp(6)], spacing=dp(2))
        with card.canvas.before:
            Color(*rgba(B_CARD))
            card._bg = RoundedRectangle(pos=card.pos, size=card.size,
                                        radius=[dp(12)])
        card.bind(pos=lambda w, *_: setattr(w._bg, "pos", w.pos))
        card.bind(size=lambda w, *_: setattr(w._bg, "size", w.size))

        # 名字条
        bar = BoxLayout(size_hint_y=None, height=dp(30), padding=[dp(12), 0])
        with bar.canvas.before:
            Color(*rgba(color))
            bar._rect = RoundedRectangle(pos=bar.pos, size=bar.size,
                                         radius=[dp(12), dp(12), 0, 0])
        bar.bind(pos=lambda w, *_: setattr(w._rect, "pos", w.pos))
        bar.bind(size=lambda w, *_: setattr(w._rect, "size", w.size))
        name_lbl = make_label(name, size=14, color="#ffffff", bold=True)
        bar.add_widget(name_lbl)
        card.add_widget(bar)

        body = BoxLayout(orientation="vertical", padding=[dp(12), dp(4)],
                         spacing=dp(3))
        hp_lbl = make_label(f"生命值 {PLAYER_MAX_HP} / {PLAYER_MAX_HP}", size=12,
                            color=B_TEXT, bold=True)
        hp_lbl.size_hint_y = None
        hp_lbl.height = dp(18)
        body.add_widget(hp_lbl)

        hp_bar = HPBar(size_hint_y=None, height=dp(9), max_hp=PLAYER_MAX_HP,
                       hp=PLAYER_MAX_HP, fill_color=rgba(color))
        body.add_widget(hp_bar)

        stat = make_label(f"攻击 {atk}   ·   暴击率 {crit_rate:.0%}   ·   暴击伤害 +{crit_dmg:.0%}",
                          size=11, color=B_SUBTEXT)
        stat.size_hint_y = None
        stat.height = dp(18)
        body.add_widget(stat)

        skill_lbl = make_label(f"{skill_title(skill)}：{skill_detail(skill)}",
                               size=11, color=color)
        skill_lbl.size_hint_y = None
        skill_lbl.height = dp(18)
        body.add_widget(skill_lbl)

        card.add_widget(body)
        return {"root": card, "hp": hp_lbl, "bar": hp_bar, "skill": skill_lbl}

    def _refresh(self):
        for view, hp, max_hp, skill in (
            (self.player_card, self.player_hp, PLAYER_MAX_HP, self.player_skill),
            (self.enemy_card, self.enemy_hp, ENEMY_MAX_HP, self.enemy_skill),
        ):
            now = max(hp, 0)
            view["hp"].text = f"生命值 {now} / {max_hp}"
            view["bar"].hp = now
            view["bar"].max_hp = max_hp
            view["skill"].text = f"{skill_title(skill)}：{skill_detail(skill)}"

    # ---------- 日志 ----------
    def log(self, msg, tag=None):
        color = {"crit": "#e67e22", "win": B_PLAYER,
                 "lose": B_ENEMY, "heal": B_HEAL}.get(tag)
        text = f"[color={color}]{msg}[/color]" if color else msg
        self.log_lines.append(text)
        if len(self.log_lines) > 200:
            self.log_lines = self.log_lines[-200:]
        self.log_label.text = "\n".join(self.log_lines)
        Clock.schedule_once(lambda *_: setattr(self.log_sv, "scroll_y", 0), 0.02)

    # ---------- 回合 ----------
    def attack(self):
        if self.finished:
            return

        if (self.player_skill["kind"] == "heal"
                and self.player_skill["mode"] == "full"
                and not self.player_skill["used"]
                and self.player_hp <= self.player_skill["threshold"]):
            self.player_skill["used"] = True
            self.player_hp = PLAYER_MAX_HP
            self.log("你触发治疗，生命值回满，但本回合无法攻击！", "heal")
        else:
            raw, crit = roll_damage(PLAYER_ATK, PLAYER_CRIT_RATE,
                                    self.player_crit_dmg)
            dmg, notes = mitigate(self.enemy_skill, raw)
            self.enemy_hp -= dmg
            msg = f"你发动攻击，造成 {dmg} 点伤害！"
            if crit:
                msg += "暴击！"
            self.log(msg, "crit" if crit else None)
            for n in notes:
                self.log(f"　· {ENEMY_NAME}{n}")

            if self.enemy_hp <= 0:
                self.log(f"{ENEMY_NAME}被打败啦！游戏胜利", "win")
                self._refresh()
                self.finish("win")
                return

            if (self.player_skill["kind"] == "heal"
                    and self.player_skill["mode"] == "passive"):
                healed = min(PLAYER_MAX_HP - self.player_hp,
                             self.player_skill["heal"])
                if healed > 0:
                    self.player_hp += healed
                    self.log(f"你后台治疗，回复 {healed} 点生命值", "heal")

        # ---- 敌方回合 ----
        if (self.enemy_skill["kind"] == "heal"
                and self.enemy_skill["mode"] == "full"
                and not self.enemy_skill["used"]
                and self.enemy_hp <= self.enemy_skill["threshold"]):
            self.enemy_skill["used"] = True
            self.enemy_hp = ENEMY_MAX_HP
            self.log(f"{ENEMY_NAME}触发治疗，生命值回满，但本回合无法攻击！", "lose")
            self._refresh()
            return

        raw2, crit2 = roll_damage(ENEMY_ATK, ENEMY_CRIT_RATE,
                                  self.enemy_crit_dmg)
        dmg2, notes2 = mitigate(self.player_skill, raw2)
        self.player_hp -= dmg2
        msg2 = f"{ENEMY_NAME}反击，对你造成 {dmg2} 点伤害！"
        if crit2:
            msg2 += "暴击！"
        self.log(msg2, "crit" if crit2 else None)
        for n in notes2:
            self.log(f"　· 你{n}")

        if self.player_hp <= 0:
            self.log("你被击败了，游戏结束", "lose")
            self._refresh()
            self.finish("lose")
            return

        if (self.enemy_skill["kind"] == "heal"
                and self.enemy_skill["mode"] == "passive"):
            healed2 = min(ENEMY_MAX_HP - self.enemy_hp, self.enemy_skill["heal"])
            if healed2 > 0:
                self.enemy_hp += healed2
                self.log(f"{ENEMY_NAME}后台治疗，回复 {healed2} 点生命值", "heal")

        self._refresh()

    def finish(self, result):
        """记录战果，把攻击按钮换成返回按钮"""
        self.finished = True
        self.result = result
        self.btn_area.clear_widgets()
        back = FlatButton(text="返回剧情", font_size=sp(16), bold=True,
                          color=rgba("#ffffff"), bg_color=rgba(B_ENEMY),
                          press_color=rgba("#b8443f"))
        back.bind(on_release=lambda *_: self.app.finish_battle(result))
        self.btn_area.add_widget(back)


# ============================================================
#  应用
# ============================================================
class DiagView(BoxLayout):
    """把上次崩溃的日志直接贴在屏幕上，方便截图反馈"""

    def __init__(self, crash, boot, on_close, **kw):
        super().__init__(orientation="vertical", padding=dp(14),
                         spacing=dp(10), **kw)
        self.add_widget(make_label("检测到上次启动崩溃", size=17, color=ACCENT,
                                   bold=True, size_hint_y=None, height=dp(34)))
        sv = ScrollView(do_scroll_x=False)
        body = make_label((crash.strip() or "（没有异常记录）")
                          + "\n\n———————— 启动阶段 ————————\n" + (boot or ""),
                          size=11, color=TEXT, halign="left", valign="top",
                          size_hint_y=None)
        body.bind(texture_size=lambda w, v: setattr(w, "height", v[1]))
        sv.add_widget(body)
        self.add_widget(sv)

        btn = FlatButton(text="清除日志，进入游戏", font_size=sp(15), bold=True,
                         color=rgba(BTN_TEXT), bg_color=rgba(ACCENT),
                         size_hint_y=None, height=dp(46))
        btn.bind(on_release=lambda *_: on_close())
        self.add_widget(btn)


class VNApp(App):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.battle_keys = {"win": "win", "lose": "lose", "abort": "pvp"}

    def build(self):
        self.title = "赵の爱恋"
        Window.clearcolor = rgba(BG)
        _diag("boot: App.build 开始")

        self.sm = None
        self.root_box = BoxLayout(orientation="vertical")
        Window.bind(on_keyboard=self.on_key)

        crash = _read_text(_CRASH_LOG)
        if crash.strip():
            _diag("boot: 发现上次崩溃日志，先显示诊断页")
            self.root_box.add_widget(
                DiagView(crash, _read_text(_BOOT_LOG), on_close=self._enter_game))
            return self.root_box

        self._enter_game()
        return self.root_box

    def _enter_game(self):
        try:
            if os.path.exists(_CRASH_LOG):
                os.remove(_CRASH_LOG)
        except Exception:
            pass
        self.root_box.clear_widgets()

        self.sm = ScreenManager(transition=FadeTransition(duration=0.12))
        self.novel = NovelScreen(app=self, name="novel")
        self.battle = BattleScreen(app=self, name="battle")
        self.sm.add_widget(self.novel)
        self.sm.add_widget(self.battle)
        self.root_box.add_widget(self.sm)
        _diag("boot: 主界面构建完成")

    # ---------- 剧情 <-> 战斗 ----------
    def start_battle(self, win_key="win", lose_key="lose", abort_key="pvp"):
        self.battle_keys = {"win": win_key, "lose": lose_key, "abort": abort_key}
        self.battle.show_select()
        self.sm.current = "battle"

    def finish_battle(self, result):
        key = self.battle_keys.get(result, self.battle_keys.get("abort"))
        self.sm.current = "novel"
        self.novel.go_to(key)

    def back_to_novel(self):
        """战斗中直接返回 = 中途放弃，回到原场景重选"""
        self.sm.current = "novel"
        self.novel.go_to(self.battle_keys.get("abort", "pvp"))

    # ---------- 键盘 / 安卓返回键 ----------
    def on_key(self, _window, key, *_args):
        if key == 27:  # Esc / 安卓返回键
            if self.sm.current == "battle":
                self.back_to_novel()
            else:
                cur = self.novel.current or {}
                if cur.get("ending"):
                    self.novel.restart()
                else:
                    self.stop()
            return True
        if self.sm.current == "novel":
            if key in (13, 32):  # 回车 / 空格
                self.novel.tap_advance()
                return True
            if 49 <= key <= 57:  # 1-9
                self.novel.key_choice(key - 48)
                return True
            if key in (114, 82):  # r / R
                cur = self.novel.current or {}
                if cur.get("ending"):
                    self.novel.restart()
                    return True
        return False


if __name__ == "__main__":
    try:
        VNApp().run()
        _diag("exit: 正常退出")
    except BaseException:
        _text = traceback.format_exc()
        try:
            with open(_CRASH_LOG, "w", encoding="utf-8") as f:
                f.write(_text)
        except Exception:
            pass
        _diag("CRASH(main): " + _text.strip().splitlines()[-1])
        raise
