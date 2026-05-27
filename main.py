import json
import os
import datetime
import math
import requests
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp

# 配色常量 - 蓝白运动风
PRIMARY = (0.11, 0.40, 0.75, 1)       # #1C66BF 蓝
PRIMARY_DARK = (0.08, 0.28, 0.55, 1)  # #14478C 深蓝
ACCENT = (0.00, 0.71, 0.85, 1)        # #00B5D9 青蓝
WHITE = (1, 1, 1, 1)
LIGHT_BG = (0.95, 0.97, 1.0, 1)      # 淡蓝白
DARK_TEXT = (0.15, 0.15, 0.20, 1)
GRAY_TEXT = (0.5, 0.5, 0.55, 1)
RED = (0.90, 0.25, 0.25, 1)
GREEN = (0.20, 0.75, 0.40, 1)
ORANGE = (1.0, 0.60, 0.10, 1)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DATA_FILE = os.path.join(DATA_DIR, "felixsport.json")


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "username": "Felix",
        "avatar": "",
        "records": [],
        "preferences": {},
    }


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def feels_like_temp(temp, humidity, wind_speed):
    """体感温度计算"""
    if temp >= 27:
        # 高温用Heat Index简化
        hi = temp + 0.33 * (humidity / 100 * 6.105 * math.exp(17.27 * temp / (237.7 + temp))) - 0.7 * wind_speed - 4.0
        return round(hi, 1)
    elif temp <= 10:
        # 低温用Wind Chill
        if wind_speed > 1.3:
            wc = 13.12 + 0.6215 * temp - 11.37 * wind_speed ** 0.16 + 0.3965 * temp * wind_speed ** 0.16
            return round(wc, 1)
    return temp


def sport_advice(temp, humidity, wind_speed, weather):
    """天气是否适合跑步判断"""
    fl = feels_like_temp(temp, humidity, wind_speed)
    if "雨" in weather or "雪" in weather:
        return "不建议户外运动", "天气恶劣，建议室内运动", RED
    if "雾" in weather or "霾" in weather:
        return "适合室内运动", "空气质量较差，避免户外跑步", ORANGE
    if wind_speed > 8:
        return "适合室内运动", "风力较大，注意安全", ORANGE
    if fl > 38:
        return "不建议户外运动", "体感过热，易中暑", RED
    if fl > 32:
        return "适合慢跑", "体感较热，注意补水和降温", ORANGE
    if fl < -10:
        return "不建议户外运动", "体感过冷，易冻伤", RED
    if fl < 0:
        return "适合慢跑", "体感较冷，充分热身", ORANGE
    if 15 <= fl <= 25 and humidity < 80:
        return "适合快跑", "天气舒适，适合全力奔跑", GREEN
    return "适合慢跑", "天气尚可，适合轻松慢跑", ACCENT


def hr_zone(hr, age=18):
    """心率健康区间判断"""
    max_hr = 220 - age
    pct = hr / max_hr * 100
    if pct < 50:
        return "热身区", GRAY_TEXT
    if pct < 60:
        return "燃脂区", GREEN
    if pct < 70:
        return "有氧区", ACCENT
    if pct < 80:
        return "无氧区", ORANGE
    return "极限区", RED


class BgLabel(Label):
    """带背景的Label"""
    pass


class NavButton(Button):
    """底部导航按钮"""
    pass


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_data = load_data()
        self.weather_data = None
        self.build_ui()
        Clock.schedule_once(lambda dt: self.fetch_weather(), 2)

    def build_ui(self):
        layout = BoxLayout(orientation="vertical", padding=0, spacing=0)

        # 顶部栏
        top = BoxLayout(size_hint_y=0.12, padding=[15, 10])
        with top.canvas.before:
            Color(*PRIMARY)
            Rectangle(pos=top.pos, size=top.size)
        top.bind(pos=lambda i, v: setattr(top.canvas.before.children[0], "pos", v),
                 size=lambda i, v: setattr(top.canvas.before.children[0], "size", v))

        # 头像 + 用户名
        avatar_box = BoxLayout(orientation="horizontal", spacing=10)
        avatar_label = Label(
            text="[size=40]🏃[/size]", markup=True,
            size_hint_x=0.2, color=WHITE
        )
        avatar_box.add_widget(avatar_label)

        username_label = Label(
            text=self.app_data.get("username", "Felix"),
            font_size=sp(22), bold=True,
            size_hint_x=0.5, halign="left", valign="middle",
            color=WHITE
        )
        username_label.bind(size=username_label.setter("text_size"))
        avatar_box.add_widget(username_label)

        date_label = Label(
            text=datetime.date.today().strftime("%m月%d日"),
            font_size=sp(14),
            size_hint_x=0.3, halign="right", valign="middle",
            color=(0.8, 0.9, 1.0, 1)
        )
        date_label.bind(size=date_label.setter("text_size"))
        avatar_box.add_widget(date_label)

        top.add_widget(avatar_box)
        layout.add_widget(top)

        # 天气卡片
        weather_card = BoxLayout(orientation="vertical", size_hint_y=0.35,
                                  padding=[20, 15], spacing=8)
        with weather_card.canvas.before:
            Color(*LIGHT_BG)
            Rectangle(pos=weather_card.pos, size=weather_card.size)
        weather_card.bind(
            pos=lambda i, v: setattr(weather_card.canvas.before.children[0], "pos", v),
            size=lambda i, v: setattr(weather_card.canvas.before.children[0], "size", v)
        )

        self.weather_title = Label(text="天气加载中...", font_size=sp(16),
                                    color=DARK_TEXT, halign="left", size_hint_y=0.25)
        self.weather_title.bind(size=self.weather_title.setter("text_size"))
        weather_card.add_widget(self.weather_title)

        self.weather_detail = Label(text="", font_size=sp(14),
                                     color=GRAY_TEXT, halign="left", size_hint_y=0.35)
        self.weather_detail.bind(size=self.weather_detail.setter("text_size"))
        weather_card.add_widget(self.weather_detail)

        self.advice_label = Label(text="", font_size=sp(16), bold=True,
                                   halign="left", size_hint_y=0.25)
        self.advice_label.bind(size=self.advice_label.setter("text_size"))
        weather_card.add_widget(self.advice_label)

        self.advice_detail = Label(text="", font_size=sp(13),
                                    color=GRAY_TEXT, halign="left", size_hint_y=0.25)
        self.advice_detail.bind(size=self.advice_detail.setter("text_size"))
        weather_card.add_widget(self.advice_detail)

        layout.add_widget(weather_card)

        # 快捷记录按钮
        btn_area = BoxLayout(size_hint_y=0.15, padding=[30, 10])
        add_btn = Button(
            text="＋  记录运动", font_size=sp(18), bold=True,
            background_color=PRIMARY, color=WHITE,
            background_normal=""
        )
        add_btn.bind(on_press=self.go_add_record)
        btn_area.add_widget(add_btn)
        layout.add_widget(btn_area)

        # 最近记录
        recent_box = BoxLayout(orientation="vertical", size_hint_y=0.38,
                                padding=[15, 5], spacing=5)
        recent_title = Label(text="最近运动", font_size=sp(16), bold=True,
                              color=DARK_TEXT, halign="left", size_hint_y=0.15)
        recent_title.bind(size=recent_title.setter("text_size"))
        recent_box.add_widget(recent_title)

        scroll = ScrollView(size_hint_y=0.85)
        self.recent_list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=5)
        self.recent_list.bind(minimum_height=self.recent_list.setter("height"))
        scroll.add_widget(self.recent_list)
        recent_box.add_widget(scroll)
        layout.add_widget(recent_box)

        self.add_widget(layout)
        self.refresh_recent()

    def refresh_recent(self):
        self.recent_list.clear_widgets()
        records = self.app_data.get("records", [])[-5:]
        records.reverse()
        if not records:
            self.recent_list.add_widget(Label(text="暂无记录，点击上方按钮添加",
                                               color=GRAY_TEXT, font_size=sp(13),
                                               size_hint_y=None, height=dp(40)))
        for r in records:
            item = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(45),
                              spacing=8)
            date_l = Label(text=r.get("date", ""), font_size=sp(12),
                           color=GRAY_TEXT, size_hint_x=0.25)
            dist_l = Label(text=f"{r.get('distance', 0)}km", font_size=sp(14),
                           bold=True, color=DARK_TEXT, size_hint_x=0.2)
            time_l = Label(text=f"{r.get('duration', 0)}min", font_size=sp(12),
                           color=GRAY_TEXT, size_hint_x=0.2)
            pace_l = Label(text=r.get("pace", ""), font_size=sp(12),
                           color=ACCENT, size_hint_x=0.2)
            hr_l = Label(text=f"{r.get('heartrate', '')}bpm" if r.get("heartrate") else "",
                         font_size=sp(12), color=ORANGE, size_hint_x=0.15)
            for w in [date_l, dist_l, time_l, pace_l, hr_l]:
                item.add_widget(w)
            self.recent_list.add_widget(item)

    def fetch_weather(self):
        try:
            # 使用 wttr.in 免费 API，无需key
            resp = requests.get("https://wttr.in/?format=j1", timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                cur = data.get("current_condition", [{}])[0]
                temp = float(cur.get("temp_C", 20))
                humidity = float(cur.get("humidity", 50))
                wind_speed = float(cur.get("windspeedKmph", 5)) / 3.6
                desc = cur.get("lang_zh", [{}])[0].get("value", cur.get("weatherDesc", [{}])[0].get("value", ""))
                fl = feels_like_temp(temp, humidity, wind_speed)
                self.weather_data = {
                    "temp": temp, "humidity": humidity,
                    "wind_speed": wind_speed, "desc": desc, "feels_like": fl,
                }
                self.weather_title.text = f"🌡 {temp}°C  {desc}  体感 {fl}°C"
                self.weather_detail.text = f"湿度 {humidity}%  风速 {wind_speed:.1f}m/s"
                adv, detail, color = sport_advice(temp, humidity, wind_speed, desc)
                self.advice_label.text = f"💪 {adv}"
                self.advice_label.color = color
                self.advice_detail.text = detail
            else:
                self.weather_title.text = "天气获取失败，请检查网络"
        except Exception:
            self.weather_title.text = "天气获取失败，请检查网络"

    def go_add_record(self, instance):
        self.manager.current = "record"


class RecordScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_data = load_data()
        self.edit_index = None
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation="vertical", padding=0, spacing=0)

        # 顶部
        top = BoxLayout(size_hint_y=0.10, padding=[15, 8])
        with top.canvas.before:
            Color(*PRIMARY)
            Rectangle(pos=top.pos, size=top.size)
        top.bind(pos=lambda i, v: setattr(top.canvas.before.children[0], "pos", v),
                 size=lambda i, v: setattr(top.canvas.before.children[0], "size", v))
        title = Label(text="运动记录", font_size=sp(20), bold=True, color=WHITE)
        top.add_widget(title)
        layout.add_widget(top)

        # 表单
        form = BoxLayout(orientation="vertical", size_hint_y=0.45,
                          padding=[25, 15], spacing=12)

        self.date_input = self._make_field("日期", datetime.date.today().strftime("%Y-%m-%d"))
        self.dist_input = self._make_field("距离(km)", "")
        self.dur_input = self._make_field("时长(分钟)", "")
        self.pace_input = self._make_field("配速(如5'30\")", "")
        self.hr_input = self._make_field("心率(bpm)", "")

        for w in [self.date_input, self.dist_input, self.dur_input,
                   self.pace_input, self.hr_input]:
            form.add_widget(w)
        layout.add_widget(form)

        # 按钮
        btn_area = BoxLayout(size_hint_y=0.12, padding=[25, 5], spacing=15)
        save_btn = Button(text="保存", font_size=sp(16), bold=True,
                          background_color=PRIMARY, color=WHITE, background_normal="")
        save_btn.bind(on_press=self.save_record)
        btn_area.add_widget(save_btn)
        layout.add_widget(btn_area)

        # 历史列表
        hist_box = BoxLayout(orientation="vertical", size_hint_y=0.33, padding=[15, 5])
        hist_title = Label(text="历史记录", font_size=sp(14), bold=True,
                           color=DARK_TEXT, halign="left", size_hint_y=0.12)
        hist_title.bind(size=hist_title.setter("text_size"))
        hist_box.add_widget(hist_title)

        scroll = ScrollView(size_hint_y=0.88)
        self.hist_list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=4)
        self.hist_list.bind(minimum_height=self.hist_list.setter("height"))
        scroll.add_widget(self.hist_list)
        hist_box.add_widget(scroll)
        layout.add_widget(hist_box)

        self.add_widget(layout)
        self.refresh_history()

    def _make_field(self, label_text, default):
        box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(42), spacing=8)
        lbl = Label(text=label_text, font_size=sp(14), color=GRAY_TEXT,
                    size_hint_x=0.35, halign="right")
        lbl.bind(size=lbl.setter("text_size"))
        inp = TextInput(text=default, font_size=sp(14),
                        size_hint_x=0.65, multiline=False,
                        background_color=LIGHT_BG, foreground_color=DARK_TEXT)
        box.add_widget(lbl)
        box.add_widget(inp)
        return box

    def save_record(self, instance):
        try:
            record = {
                "date": self.date_input.children[0].text.strip(),
                "distance": float(self.dist_input.children[0].text.strip() or "0"),
                "duration": int(self.dur_input.children[0].text.strip() or "0"),
                "pace": self.pace_input.children[0].text.strip(),
                "heartrate": int(self.hr_input.children[0].text.strip() or "0") if self.hr_input.children[0].text.strip() else None,
            }
        except ValueError:
            return

        if self.edit_index is not None:
            self.app_data["records"][self.edit_index] = record
            self.edit_index = None
        else:
            self.app_data["records"].append(record)
        save_data(self.app_data)
        self._clear_inputs()
        self.refresh_history()

    def _clear_inputs(self):
        self.date_input.children[0].text = datetime.date.today().strftime("%Y-%m-%d")
        for w in [self.dist_input, self.dur_input, self.pace_input, self.hr_input]:
            w.children[0].text = ""

    def refresh_history(self):
        self.hist_list.clear_widgets()
        records = self.app_data.get("records", [])
        records.reverse()
        for i, r in enumerate(records):
            idx = len(records) - 1 - i
            item = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=5)
            info = f"{r.get('date','')}  {r.get('distance',0)}km  {r.get('duration',0)}min"
            lbl = Label(text=info, font_size=sp(12), color=DARK_TEXT,
                        halign="left", size_hint_x=0.7)
            lbl.bind(size=lbl.setter("text_size"))
            item.add_widget(lbl)

            del_btn = Button(text="删除", font_size=sp(11),
                             background_color=RED, color=WHITE,
                             background_normal="", size_hint_x=0.15)
            del_btn.bind(on_press=lambda x, ii=idx: self.delete_record(ii))
            item.add_widget(del_btn)
            self.hist_list.add_widget(item)

    def delete_record(self, idx):
        if 0 <= idx < len(self.app_data["records"]):
            self.app_data["records"].pop(idx)
            save_data(self.app_data)
            self.refresh_history()


class StatsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_data = load_data()
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation="vertical", padding=0, spacing=0)

        top = BoxLayout(size_hint_y=0.10, padding=[15, 8])
        with top.canvas.before:
            Color(*PRIMARY)
            Rectangle(pos=top.pos, size=top.size)
        top.bind(pos=lambda i, v: setattr(top.canvas.before.children[0], "pos", v),
                 size=lambda i, v: setattr(top.canvas.before.children[0], "size", v))
        title = Label(text="数据统计", font_size=sp(20), bold=True, color=WHITE)
        top.add_widget(title)
        layout.add_widget(top)

        # 统计图表区
        chart_area = BoxLayout(orientation="vertical", size_hint_y=0.9, padding=[15, 10], spacing=10)

        # 月跑量柱状图
        bar_title = Label(text="月累计跑量 (km)", font_size=sp(14), bold=True,
                          color=DARK_TEXT, halign="left", size_hint_y=0.08)
        bar_title.bind(size=bar_title.setter("text_text"))
        chart_area.add_widget(bar_title)

        self.bar_chart = BarChart(size_hint_y=0.42)
        chart_area.add_widget(self.bar_chart)

        # 心率曲线图
        hr_title = Label(text="心率变化趋势", font_size=sp(14), bold=True,
                         color=DARK_TEXT, halign="left", size_hint_y=0.08)
        hr_title.bind(size=hr_title.setter("text_text"))
        chart_area.add_widget(hr_title)

        self.hr_chart = LineChart(size_hint_y=0.42)
        chart_area.add_widget(self.hr_chart)

        layout.add_widget(chart_area)
        self.add_widget(layout)

    def on_enter(self, *args):
        self.app_data = load_data()
        self.bar_chart.data = self._monthly_data()
        self.hr_chart.data = self._hr_data()
        self.bar_chart.draw()
        self.hr_chart.draw()

    def _monthly_data(self):
        records = self.app_data.get("records", [])
        monthly = {}
        for r in records:
            d = r.get("date", "")[:7]  # YYYY-MM
            if d:
                monthly[d] = monthly.get(d, 0) + r.get("distance", 0)
        sorted_months = sorted(monthly.items())[-6:]
        return sorted_months

    def _hr_data(self):
        records = self.app_data.get("records", [])
        hr_list = []
        for r in records:
            hr = r.get("heartrate")
            if hr:
                hr_list.append((r.get("date", ""), hr))
        return hr_list[-20:]


class BarChart(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []
        self.bind(size=self._redraw, pos=self._redraw)

    def _redraw(self, *args):
        Clock.schedule_once(lambda dt: self.draw())

    def draw(self):
        self.canvas.clear()
        if not self.data:
            with self.canvas:
                Color(*GRAY_TEXT)
                Label(text="暂无数据")
            return

        w, h = self.size
        x0, y0 = self.pos
        x0 += dp(40)
        y0 += dp(20)
        chart_w = w - dp(60)
        chart_h = h - dp(40)

        n = len(self.data)
        if n == 0:
            return
        max_val = max(v for _, v in self.data) or 1
        bar_w = chart_w / n * 0.7
        gap = chart_w / n * 0.3

        with self.canvas:
            # Y轴
            Color(*GRAY_TEXT)
            Line(points=[x0, y0, x0, y0 + chart_h], width=1)
            # X轴
            Line(points=[x0, y0, x0 + chart_w, y0], width=1)

            for i, (label, val) in enumerate(self.data):
                bar_h = (val / max_val) * chart_h * 0.9
                bx = x0 + i * (bar_w + gap) + gap / 2
                by = y0

                Color(*ACCENT)
                Rectangle(pos=(bx, by), size=(bar_w, bar_h))

                # 标签
                Color(*DARK_TEXT)
                # 值
                # 用简化方式绘制


class LineChart(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []
        self.bind(size=self._redraw, pos=self._redraw)

    def _redraw(self, *args):
        Clock.schedule_once(lambda dt: self.draw())

    def draw(self):
        self.canvas.clear()
        if not self.data:
            return

        w, h = self.size
        x0, y0 = self.pos
        x0 += dp(40)
        y0 += dp(20)
        chart_w = w - dp(60)
        chart_h = h - dp(40)

        n = len(self.data)
        if n < 2:
            return
        hrs = [hr for _, hr in self.data]
        min_hr = min(hrs) - 5
        max_hr = max(hrs) + 5
        hr_range = max_hr - min_hr or 1

        with self.canvas:
            Color(*GRAY_TEXT)
            Line(points=[x0, y0, x0, y0 + chart_h], width=1)
            Line(points=[x0, y0, x0 + chart_w, y0], width=1)

            Color(*ORANGE)
            points = []
            for i, (_, hr) in enumerate(self.data):
                px = x0 + (i / (n - 1)) * chart_w
                py = y0 + ((hr - min_hr) / hr_range) * chart_h * 0.9
                points.extend([px, py])
            if len(points) >= 4:
                Line(points=points, width=2)


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_data = load_data()
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation="vertical", padding=0, spacing=0)

        top = BoxLayout(size_hint_y=0.10, padding=[15, 8])
        with top.canvas.before:
            Color(*PRIMARY)
            Rectangle(pos=top.pos, size=top.size)
        top.bind(pos=lambda i, v: setattr(top.canvas.before.children[0], "pos", v),
                 size=lambda i, v: setattr(top.canvas.before.children[0], "size", v))
        title = Label(text="个人设置", font_size=sp(20), bold=True, color=WHITE)
        top.add_widget(title)
        layout.add_widget(top)

        form = BoxLayout(orientation="vertical", size_hint_y=0.5,
                          padding=[25, 20], spacing=15)

        # 头像
        avatar_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(80), spacing=10)
        self.avatar_display = Label(text="[size=60]🏃[/size]", markup=True,
                                    size_hint_x=0.3, color=PRIMARY)
        avatar_box.add_widget(self.avatar_display)
        avatar_hint = Label(text="点击更换头像（暂不支持）\n将在后续版本中添加",
                            font_size=sp(12), color=GRAY_TEXT, size_hint_x=0.7,
                            halign="left")
        avatar_hint.bind(size=avatar_hint.setter("text_size"))
        avatar_box.add_widget(avatar_hint)
        form.add_widget(avatar_box)

        # 用户名
        name_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(45), spacing=8)
        name_lbl = Label(text="用户名", font_size=sp(14), color=GRAY_TEXT, size_hint_x=0.3)
        self.name_input = TextInput(text=self.app_data.get("username", "Felix"),
                                     font_size=sp(14), size_hint_x=0.5,
                                     multiline=False, background_color=LIGHT_BG,
                                     foreground_color=DARK_TEXT)
        save_name_btn = Button(text="保存", font_size=sp(12),
                                background_color=PRIMARY, color=WHITE,
                                background_normal="", size_hint_x=0.2)
        save_name_btn.bind(on_press=self.save_username)
        name_box.add_widget(name_lbl)
        name_box.add_widget(self.name_input)
        name_box.add_widget(save_name_btn)
        form.add_widget(name_box)

        # 数据统计
        records = self.app_data.get("records", [])
        total_km = sum(r.get("distance", 0) for r in records)
        total_min = sum(r.get("duration", 0) for r in records)
        stats_text = f"总跑量: {total_km:.1f} km\n总时长: {total_min} 分钟\n记录数: {len(records)} 次"
        stats_lbl = Label(text=stats_text, font_size=sp(14), color=DARK_TEXT,
                          halign="left", size_hint_y=0.3)
        stats_lbl.bind(size=stats_lbl.setter("text_size"))
        form.add_widget(stats_lbl)

        layout.add_widget(form)

        # 关于
        about_box = BoxLayout(orientation="vertical", size_hint_y=0.4,
                               padding=[25, 10], spacing=10)
        about_lbl = Label(
            text="FelixSport v1.0\n个人跑步运动健康助手\n蓝白运动风 · 本地存储 · 隐私安全",
            font_size=sp(13), color=GRAY_TEXT, halign="center"
        )
        about_lbl.bind(size=about_lbl.setter("text_text"))
        about_box.add_widget(about_lbl)

        # 清空数据按钮
        clear_btn = Button(text="清空所有数据", font_size=sp(13),
                           background_color=RED, color=WHITE,
                           background_normal="", size_hint_y=None, height=dp(40))
        clear_btn.bind(on_press=self.clear_data)
        about_box.add_widget(clear_btn)

        layout.add_widget(about_box)
        self.add_widget(layout)

    def save_username(self, instance):
        name = self.name_input.text.strip()
        if name:
            self.app_data["username"] = name
            save_data(self.app_data)

    def clear_data(self, instance):
        content = BoxLayout(orientation="vertical", padding=20, spacing=15)
        content.add_widget(Label(text="确定要清空所有数据吗？\n此操作不可恢复",
                                  font_size=sp(14), color=RED))
        btns = BoxLayout(spacing=15, size_hint_y=0.3)
        yes_btn = Button(text="确定清空", background_color=RED, color=WHITE, background_normal="")
        no_btn = Button(text="取消", background_color=GRAY_TEXT, color=WHITE, background_normal="")
        btns.add_widget(yes_btn)
        btns.add_widget(no_btn)
        content.add_widget(btns)

        popup = Popup(title="确认", content=content, size_hint=(0.7, 0.4))
        yes_btn.bind(on_press=lambda x: self._do_clear(popup))
        no_btn.bind(on_press=popup.dismiss)
        popup.open()

    def _do_clear(self, popup):
        self.app_data = {"username": "Felix", "avatar": "", "records": [], "preferences": {}}
        save_data(self.app_data)
        popup.dismiss()


class FelixSportApp(App):
    def build(self):
        self.title = "FelixSport"
        Window.clearcolor = LIGHT_BG

        sm = ScreenManager()

        home = HomeScreen(name="home")
        record = RecordScreen(name="record")
        stats = StatsScreen(name="stats")
        settings = SettingsScreen(name="settings")

        sm.add_widget(home)
        sm.add_widget(record)
        sm.add_widget(stats)
        sm.add_widget(settings)

        # 主布局：内容 + 底部导航
        root = BoxLayout(orientation="vertical")

        # ScreenManager 区域
        sm.size_hint_y = 0.92
        root.add_widget(sm)

        # 底部导航
        nav = BoxLayout(size_hint_y=0.08, spacing=0)
        with nav.canvas.before:
            Color(*WHITE)
            Rectangle(pos=nav.pos, size=nav.size)
        nav.bind(pos=lambda i, v: setattr(nav.canvas.before.children[0], "pos", v),
                 size=lambda i, v: setattr(nav.canvas.before.children[0], "size", v))

        tabs = [
            ("🏠 首页", "home"),
            ("📋 记录", "record"),
            ("📊 统计", "stats"),
            ("⚙ 设置", "settings"),
        ]
        for text, screen_name in tabs:
            btn = Button(text=text, font_size=sp(13),
                         background_color=WHITE, color=PRIMARY,
                         background_normal="")
            btn.bind(on_press=lambda x, s=screen_name: setattr(sm, "current", s))
            nav.add_widget(btn)

        root.add_widget(nav)
        return root


if __name__ == "__main__":
    FelixSportApp().run()
