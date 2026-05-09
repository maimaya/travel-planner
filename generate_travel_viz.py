from __future__ import annotations

import argparse
import json
import os
from shutil import copy2
from dataclasses import asdict, dataclass, field
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin


@dataclass
class Location:
    name: str
    category: str
    lat: float
    lng: float
    title: str
    subtitle: str
    emoji: str
    description: str
    link: Optional[str] = None
    link_label: Optional[str] = None
    accent: Optional[str] = None


@dataclass
class RouteSegment:
    from_stop: str
    to_stop: str
    mode: str
    emoji: str
    minutes: int
    tip: str


@dataclass
class DayPlan:
    day: str
    title: str
    theme: str
    date_hint: str
    hotel: str
    summary: str
    stops: List[str] = field(default_factory=list)
    route: List[RouteSegment] = field(default_factory=list)


@dataclass
class MapConfig:
    center_lat: float
    center_lng: float
    zoom: int
    min_zoom: int
    max_zoom: int


@dataclass
class TravelPlan:
    destination: str
    country: str
    tag_line: str
    map_title: str
    hero_note: str
    map_config: MapConfig
    locations: Dict[str, Location]
    day_plans: List[DayPlan]


TRANSPORT_STYLES = {
    "walk": {"color": "#f29f80", "icons": "", "weight": 6},
    "metro": {"color": "#7ea6a2", "icons": "6,10", "weight": 7},
    "taxi": {"color": "#e0b94f", "icons": "2,10", "weight": 7},
    "train": {"color": "#88a6d8", "icons": "14,10", "weight": 7},
    "bike": {"color": "#97b77b", "icons": "6,6", "weight": 6},
    "bus": {"color": "#c794b8", "icons": "12,8", "weight": 6},
    "car": {"color": "#cf8f6d", "icons": "10,8", "weight": 7},
}

DEFAULT_GOOGLE_MAPS_API_KEY = ""


def load_local_env(base_dir: Path) -> None:
    """Load simple KEY=VALUE pairs from .env without requiring extra packages."""
    env_path = base_dir / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def build_barcelona_plan() -> TravelPlan:
    locations = {
        "hotel_passage": Location(
            name="Hotel Casa Sagnier",
            category="hotel",
            lat=41.3921,
            lng=2.1648,
            title="入住酒店",
            subtitle="Passeig de Gracia 周边",
            emoji="🏨",
            description="作为 4 天移动中心很合适，步行和地铁切换都顺手。",
            link="https://www.hotelcasasagnier.com/",
            link_label="酒店官网",
            accent="#d98f70",
        ),
        "casa_batllo": Location(
            name="Casa Batllo",
            category="sight",
            lat=41.3917,
            lng=2.1649,
            title="巴特罗之家",
            subtitle="高迪现代主义代表作",
            emoji="🎨",
            description="建议预约早场，室内光影和语音导览体验都很好。",
            link="https://www.casabatllo.es/en/",
            link_label="官网 / 购票",
            accent="#de8c6d",
        ),
        "el_nacional": Location(
            name="El Nacional",
            category="food",
            lat=41.3913,
            lng=2.1690,
            title="El Nacional",
            subtitle="适合第一顿西班牙餐",
            emoji="🍤",
            description="共享 tapas 很合适，环境漂亮，适合作为开场。",
            link="https://www.elnacionalbcn.com/en/",
            link_label="餐厅官网",
            accent="#e5a766",
        ),
        "sagrada_familia": Location(
            name="Sagrada Familia",
            category="sight",
            lat=41.4036,
            lng=2.1744,
            title="圣家堂",
            subtitle="巴塞罗那必看地标",
            emoji="⛪",
            description="建议提前预订带塔楼时段，傍晚彩窗非常美。",
            link="https://sagradafamilia.org/en/tickets",
            link_label="官网 / 预订",
            accent="#e59a8c",
        ),
        "bunkers": Location(
            name="Bunkers del Carmel",
            category="view",
            lat=41.4187,
            lng=2.1527,
            title="Carmel 山顶观景台",
            subtitle="看日落的经典点位",
            emoji="🌇",
            description="风大时记得带外套，适合把第一天收在城市全景里。",
            accent="#c89381",
        ),
        "park_guell": Location(
            name="Park Guell",
            category="sight",
            lat=41.4145,
            lng=2.1527,
            title="古埃尔公园",
            subtitle="高迪童话感拼贴世界",
            emoji="🦎",
            description="最好预订上午场，人流更温和，适合拍照。",
            link="https://parkguell.barcelona/en",
            link_label="官网 / 门票",
            accent="#92ae7b",
        ),
        "gracia_brunch": Location(
            name="Brunch & Cake",
            category="food",
            lat=41.3990,
            lng=2.1598,
            title="Brunch & Cake",
            subtitle="Gracia 区轻松早午餐",
            emoji="🥞",
            description="清新风格餐厅，适合作为第二天的慢节奏开场。",
            link="https://brunchandcake.com/",
            link_label="餐厅官网",
            accent="#d7b78d",
        ),
        "recinte_modernista": Location(
            name="Sant Pau Recinte Modernista",
            category="sight",
            lat=41.4125,
            lng=2.1744,
            title="圣保罗现代主义建筑群",
            subtitle="被低估的精致建筑群",
            emoji="🏛️",
            description="从这里再去圣家堂或市中心都很顺，适合拍照。",
            link="https://www.santpaubarcelona.org/en/",
            link_label="官网 / 门票",
            accent="#9db7d3",
        ),
        "disfrutar": Location(
            name="Disfrutar",
            category="food",
            lat=41.3888,
            lng=2.1533,
            title="Disfrutar",
            subtitle="想吃一顿仪式感晚餐可以选这里",
            emoji="🍽️",
            description="若要安排 fine dining，需尽早预订。",
            link="https://www.disfrutarbarcelona.com/",
            link_label="餐厅官网",
            accent="#a6877d",
        ),
        "gothic_quarter": Location(
            name="Barri Gotic",
            category="sight",
            lat=41.3830,
            lng=2.1762,
            title="哥特区",
            subtitle="老城步行最有味道的一段",
            emoji="🏰",
            description="适合慢慢逛小巷、教堂、广场和纪念品店。",
            accent="#8f8eaa",
        ),
        "boqueria": Location(
            name="La Boqueria",
            category="food",
            lat=41.3817,
            lng=2.1715,
            title="波盖利亚市场",
            subtitle="适合午间快吃和看当地节奏",
            emoji="🍓",
            description="果汁、火腿和海鲜都值得试，避开最拥挤时段更舒服。",
            link="https://www.boqueria.barcelona/home",
            link_label="市场官网",
            accent="#df876f",
        ),
        "picasso": Location(
            name="Museu Picasso",
            category="sight",
            lat=41.3853,
            lng=2.1800,
            title="毕加索博物馆",
            subtitle="老城区里的艺术停留点",
            emoji="🖼️",
            description="馆藏很系统，适合作为老城日的文化补充。",
            link="https://museupicassobcn.cat/en",
            link_label="官网 / 门票",
            accent="#789bb9",
        ),
        "barceloneta": Location(
            name="Barceloneta Beach",
            category="view",
            lat=41.3789,
            lng=2.1925,
            title="巴塞罗内塔海边",
            subtitle="海风散步与城市切换",
            emoji="🌊",
            description="第三天下午留给海边会很舒服，适合放慢节奏。",
            accent="#72afc8",
        ),
        "can_soles": Location(
            name="Can Sole",
            category="food",
            lat=41.3801,
            lng=2.1897,
            title="Can Sole",
            subtitle="海鲜饭老店",
            emoji="🥘",
            description="想吃经典海鲜饭可以安排在这里，氛围复古。",
            link="https://restaurantcansole.com/",
            link_label="餐厅官网",
            accent="#d3a66a",
        ),
        "montjuic": Location(
            name="Montjuic",
            category="sight",
            lat=41.3630,
            lng=2.1650,
            title="蒙特惠奇山",
            subtitle="山景与城市视角",
            emoji="🚠",
            description="适合第四天把城市再从高处看一遍。",
            accent="#90b08b",
        ),
        "mnac": Location(
            name="MNAC",
            category="sight",
            lat=41.3686,
            lng=2.1516,
            title="加泰罗尼亚国家艺术博物馆",
            subtitle="建筑本体和露台都值得",
            emoji="🏛️",
            description="馆外平台远眺很美，适合作为返程前的收尾。",
            link="https://www.museunacional.cat/en",
            link_label="官网 / 门票",
            accent="#c9a29b",
        ),
        "cable_car": Location(
            name="Montjuic Cable Car",
            category="transport",
            lat=41.3677,
            lng=2.1631,
            title="蒙特惠奇缆车",
            subtitle="轻松上山的小段体验",
            emoji="🚡",
            description="如果不想全程步行，上山这段很适合保留体力。",
            link="https://www.telefericdemontjuic.cat/en",
            link_label="官网 / 购票",
            accent="#7da4a3",
        ),
        "airport": Location(
            name="Barcelona El Prat Airport",
            category="transport",
            lat=41.2974,
            lng=2.0833,
            title="返程交通",
            subtitle="机场方向",
            emoji="✈️",
            description="建议预留充足时间，从市区前往机场约 35 到 50 分钟。",
            accent="#96a9bf",
        ),
    }

    day_plans = [
        DayPlan(
            day="Day 1",
            title="高迪初见",
            theme="经典地标 + 城市日落",
            date_hint="抵达当日",
            hotel="Hotel Casa Sagnier",
            summary="第一天不排太满，以酒店周边、高迪建筑和山顶日落为主。",
            stops=["hotel_passage", "casa_batllo", "el_nacional", "sagrada_familia", "bunkers"],
            route=[
                RouteSegment("hotel_passage", "casa_batllo", "walk", "🚶", 8, "酒店步行过去最舒服"),
                RouteSegment("casa_batllo", "el_nacional", "walk", "🚶", 5, "同一片区慢慢走"),
                RouteSegment("el_nacional", "sagrada_familia", "metro", "🚇", 18, "Passeig de Gracia 转线方便"),
                RouteSegment("sagrada_familia", "bunkers", "taxi", "🚕", 20, "傍晚直接去看日落更省时间"),
            ],
        ),
        DayPlan(
            day="Day 2",
            title="公园建筑",
            theme="公园 + 建筑群 + 精致晚餐",
            date_hint="完整游玩日",
            hotel="Hotel Casa Sagnier",
            summary="第二天用更从容的节奏连接 Gracia、古埃尔公园和现代主义建筑。",
            stops=["hotel_passage", "gracia_brunch", "park_guell", "recinte_modernista", "disfrutar"],
            route=[
                RouteSegment("hotel_passage", "gracia_brunch", "walk", "🚶", 16, "边走边看街区很有趣"),
                RouteSegment("gracia_brunch", "park_guell", "taxi", "🚕", 14, "上坡段打车更轻松"),
                RouteSegment("park_guell", "recinte_modernista", "bus", "🚌", 22, "公交连接更自然"),
                RouteSegment("recinte_modernista", "disfrutar", "metro", "🚇", 24, "回到市中心吃晚餐"),
            ],
        ),
        DayPlan(
            day="Day 3",
            title="老城海风",
            theme="历史街区 + 市场 + 海边晚餐",
            date_hint="完整游玩日",
            hotel="Hotel Casa Sagnier",
            summary="第三天重点是老城质感与海边切换，适合把脚步放慢。",
            stops=["hotel_passage", "gothic_quarter", "boqueria", "picasso", "barceloneta", "can_soles"],
            route=[
                RouteSegment("hotel_passage", "gothic_quarter", "metro", "🚇", 15, "直达老城范围"),
                RouteSegment("gothic_quarter", "boqueria", "walk", "🚶", 10, "小巷里穿过去最有感觉"),
                RouteSegment("boqueria", "picasso", "walk", "🚶", 14, "沿老城区边走边逛"),
                RouteSegment("picasso", "barceloneta", "bike", "🚲", 12, "海边段很适合骑行"),
                RouteSegment("barceloneta", "can_soles", "walk", "🚶", 7, "海边晚餐收尾"),
            ],
        ),
        DayPlan(
            day="Day 4",
            title="山景返程",
            theme="山景 + 博物馆 + 机场衔接",
            date_hint="离开当日",
            hotel="Hotel Casa Sagnier",
            summary="第四天把体力留给轻量但好看的行程，最后顺滑衔接机场。",
            stops=["hotel_passage", "mnac", "cable_car", "montjuic", "airport"],
            route=[
                RouteSegment("hotel_passage", "mnac", "metro", "🚇", 20, "早上先往西边移动"),
                RouteSegment("mnac", "cable_car", "walk", "🚶", 10, "一路拍照上去"),
                RouteSegment("cable_car", "montjuic", "train", "🚠", 8, "缆车本身就是体验的一部分"),
                RouteSegment("montjuic", "airport", "taxi", "🚕", 35, "携带行李时最省心"),
            ],
        ),
    ]

    return TravelPlan(
        destination="Barcelona",
        country="Spain",
        tag_line="奶油感 3D 旅行攻略可视化",
        map_title="Barcelona Dream Route",
        hero_note="Google Maps 底图上叠加 3D 推荐点位和按天切换路线。",
        map_config=MapConfig(
            center_lat=41.3902,
            center_lng=2.1649,
            zoom=13,
            min_zoom=11,
            max_zoom=17,
        ),
        locations=locations,
        day_plans=day_plans,
    )


def serialize_plan(plan: TravelPlan) -> Dict[str, object]:
    return {
        "destination": plan.destination,
        "country": plan.country,
        "tagLine": plan.tag_line,
        "mapTitle": plan.map_title,
        "heroNote": plan.hero_note,
        "mapConfig": asdict(plan.map_config),
        "locations": {key: asdict(value) for key, value in plan.locations.items()},
        "dayPlans": [
            {
                "day": day.day,
                "title": day.title,
                "theme": day.theme,
                "dateHint": day.date_hint,
                "hotel": day.hotel,
                "summary": day.summary,
                "stops": day.stops,
                "route": [asdict(segment) for segment in day.route],
            }
            for day in plan.day_plans
        ],
        "transportStyles": TRANSPORT_STYLES,
    }


def render_html(plan_data: Dict[str, object], google_maps_api_key: str) -> str:
    payload = json.dumps(plan_data, ensure_ascii=False, indent=2)
    api_key = json.dumps(google_maps_api_key)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Travel Planner</title>
  <style>
    :root {{
      --cream: #fff9f1;
      --cream-deep: #f7efe2;
      --butter: #f2debe;
      --peach: #efc7b0;
      --salmon: #d98f70;
      --sage: #a7c1ab;
      --sea: #89b7c7;
      --ink: #5d544f;
      --ink-soft: #7f7670;
      --card: rgba(255, 251, 245, 0.82);
      --card-strong: rgba(255, 250, 244, 0.94);
      --shadow: 0 20px 50px rgba(169, 144, 123, 0.16);
      --radius-xl: 28px;
      --radius-lg: 22px;
      --radius-md: 16px;
      --panel-width: 390px;
      --font-display: "Avenir Next", "PingFang SC", "Hiragino Sans GB", sans-serif;
      --font-body: "SF Pro Text", "PingFang SC", "Microsoft YaHei", sans-serif;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      min-height: 100vh;
      font-family: var(--font-body);
      color: var(--ink);
      background:
        radial-gradient(circle at 15% 20%, rgba(255, 241, 225, 0.95), transparent 30%),
        radial-gradient(circle at 85% 12%, rgba(203, 232, 227, 0.7), transparent 24%),
        linear-gradient(135deg, #fffdf8 0%, #fff6ea 46%, #f9efe7 100%);
      overflow-x: hidden;
      overflow-y: auto;
    }}

    .intro-screen {{
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 28px;
    }}

    .intro-shell {{
      width: min(1120px, 100%);
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 24px;
      align-items: stretch;
    }}

    .intro-hero,
    .intro-form {{
      background: rgba(255, 250, 244, 0.8);
      backdrop-filter: blur(18px);
      border: 1px solid rgba(255,255,255,0.72);
      border-radius: 34px;
      box-shadow: var(--shadow);
    }}

    .intro-hero {{
      padding: 34px;
      display: grid;
      align-content: space-between;
      background:
        radial-gradient(circle at 15% 22%, rgba(255, 234, 214, 0.92), transparent 28%),
        radial-gradient(circle at 82% 14%, rgba(210, 235, 230, 0.75), transparent 22%),
        linear-gradient(150deg, rgba(255,255,255,0.88), rgba(251,241,227,0.82));
    }}

    .intro-kicker {{
      display: inline-flex;
      width: fit-content;
      padding: 8px 14px;
      border-radius: 999px;
      background: rgba(255,255,255,0.76);
      color: var(--salmon);
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}

    .intro-title {{
      margin: 16px 0 10px;
      font-family: var(--font-display);
      font-size: clamp(42px, 6vw, 72px);
      line-height: 0.98;
      letter-spacing: -0.05em;
    }}

    .intro-copy {{
      margin: 0;
      max-width: 620px;
      color: var(--ink-soft);
      font-size: 16px;
      line-height: 1.7;
    }}

    .intro-mock {{
      position: relative;
      min-height: 270px;
      margin-top: 26px;
      border-radius: 28px;
      overflow: hidden;
      background:
        linear-gradient(180deg, rgba(222, 241, 236, 0.72), rgba(255, 248, 240, 0.78)),
        linear-gradient(90deg, rgba(240, 217, 190, 0.4) 0 2px, transparent 2px 70px),
        linear-gradient(0deg, rgba(240, 217, 190, 0.22) 0 2px, transparent 2px 70px);
    }}

    .intro-mock::before {{
      content: "";
      position: absolute;
      inset: 14% 8%;
      border-radius: 34% 28% 30% 40% / 28% 36% 30% 34%;
      background: linear-gradient(145deg, rgba(248, 227, 196, 0.9), rgba(255,251,244,0.96));
      box-shadow: inset 0 -14px 24px rgba(215, 180, 146, 0.18);
    }}

    .mock-route {{
      position: absolute;
      inset: 0;
    }}

    .mock-route span {{
      position: absolute;
      display: grid;
      place-items: center;
      width: 56px;
      height: 56px;
      border-radius: 999px;
      background: rgba(255,255,255,0.94);
      border: 4px solid rgba(223, 158, 136, 0.82);
      box-shadow: 0 12px 18px rgba(186, 143, 113, 0.18);
      font-size: 22px;
    }}

    .mock-route span::after {{
      content: "";
      position: absolute;
      width: 14px;
      height: 14px;
      bottom: -8px;
      left: 50%;
      transform: translateX(-50%) rotate(45deg);
      background: rgba(223, 158, 136, 0.92);
      border-radius: 2px;
    }}

    .mock-route svg {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
    }}

    .intro-form {{
      padding: 28px;
      display: grid;
      gap: 18px;
      align-content: start;
    }}

    .intro-form h2 {{
      margin: 0;
      font-size: 28px;
      line-height: 1.08;
    }}

    .form-heading {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}

    .language-toggle {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px;
      border: none;
      border-radius: 999px;
      background: rgba(247,239,226,0.88);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.74);
      color: var(--ink-soft);
      font: inherit;
      font-size: 12px;
      cursor: pointer;
    }}

    .language-toggle span {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 60px;
      height: 30px;
      padding: 0 10px;
      border-radius: 999px;
      transition: background 160ms ease, color 160ms ease, box-shadow 160ms ease;
    }}

    .language-toggle[data-language="zh"] .lang-zh,
    .language-toggle[data-language="en"] .lang-en {{
      color: var(--ink);
      background: rgba(255,255,255,0.9);
      box-shadow: 0 8px 14px rgba(194, 160, 130, 0.14);
    }}

    .form-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }}

    .field {{
      display: grid;
      gap: 8px;
    }}

    .field.full {{
      grid-column: 1 / -1;
    }}

    .field label {{
      font-size: 12px;
      color: var(--ink-soft);
      letter-spacing: 0.03em;
      text-transform: uppercase;
    }}

    .field input,
    .field select,
    .field textarea {{
      width: 100%;
      border: none;
      outline: none;
      padding: 14px 16px;
      border-radius: 18px;
      background: rgba(247,239,226,0.82);
      color: var(--ink);
      font: inherit;
      resize: vertical;
    }}

    .field textarea {{
      min-height: 108px;
    }}

    .style-multiselect {{
      position: relative;
    }}

    .style-trigger {{
      min-height: 150px;
      display: flex;
      flex-wrap: wrap;
      align-content: flex-start;
      align-items: flex-start;
      gap: 8px;
      padding: 16px 20px 18px;
      border-radius: 32px;
      background: rgba(247,239,226,0.82);
      cursor: text;
      position: relative;
    }}

    .style-placeholder {{
      color: var(--ink-soft);
      display: none;
    }}

    .selected-chip {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      height: 32px;
      padding: 0 10px;
      border-radius: 999px;
      background: linear-gradient(135deg, rgba(239,199,176,0.96), rgba(247,227,200,0.96));
      color: var(--ink);
      font-size: 13px;
      white-space: nowrap;
    }}

    .selected-chip button {{
      border: none;
      background: transparent;
      color: inherit;
      cursor: pointer;
      font-size: 14px;
      padding: 0;
      line-height: 1;
    }}

    .style-search-input {{
      flex: 1 1 100%;
      min-width: 0;
      border: none;
      outline: none;
      background: transparent;
      color: var(--ink);
      font: inherit;
      padding: 0;
      line-height: 1.4;
      caret-color: var(--ink-soft);
    }}

    .style-search-input::placeholder {{
      color: transparent;
    }}

    .style-caret {{
      position: absolute;
      right: 22px;
      bottom: 18px;
      width: 14px;
      height: 14px;
      pointer-events: none;
      border-right: 2px solid var(--ink-soft);
      border-bottom: 2px solid var(--ink-soft);
      transform: rotate(45deg);
      opacity: 0.85;
    }}

    .style-dropdown {{
      position: absolute;
      top: calc(100% + 8px);
      left: 0;
      right: 0;
      z-index: 8;
      padding: 10px;
      border-radius: 20px;
      background: rgba(255,250,244,0.96);
      border: 1px solid rgba(255,255,255,0.84);
      box-shadow: 0 18px 28px rgba(180, 155, 130, 0.16);
      display: none;
      gap: 8px;
      max-height: 240px;
      overflow-y: auto;
    }}

    .style-dropdown.open {{
      display: grid;
    }}

    .style-option {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 12px;
      border-radius: 14px;
      cursor: pointer;
      transition: background 160ms ease;
    }}

    .style-option:hover {{
      background: rgba(247,239,226,0.78);
    }}

    .style-option input {{
      width: 16px;
      height: 16px;
      margin: 0;
      accent-color: #d98f70;
    }}

    .style-option-text {{
      color: var(--ink);
      font-size: 14px;
    }}

    .form-actions {{
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
    }}

    .primary-btn,
    .ghost-btn {{
      border: none;
      border-radius: 16px;
      padding: 14px 18px;
      font: inherit;
      cursor: pointer;
    }}

    .primary-btn {{
      background: linear-gradient(135deg, #efc7b0, #f7e3c8);
      color: var(--ink);
      font-weight: 700;
      box-shadow: 0 12px 22px rgba(211, 176, 145, 0.2);
    }}

    .ghost-btn {{
      background: rgba(255,255,255,0.7);
      color: var(--ink-soft);
    }}

    .intro-note {{
      margin: 0;
      color: var(--ink-soft);
      font-size: 13px;
      line-height: 1.6;
    }}

    .planner-shell {{
      display: none;
      grid-template-columns: minmax(250px, var(--panel-width)) 1fr;
      min-height: 100vh;
      gap: 22px;
      padding: 20px;
    }}

    .planner-shell.active {{
      display: grid;
    }}

    .trip-input-summary {{
      display: grid;
      gap: 10px;
      padding: 14px;
      border-radius: 18px;
      background: rgba(255,255,255,0.58);
    }}

    .trip-summary-title {{
      font-size: 13px;
      color: var(--ink-soft);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}

    .side-panel {{
      backdrop-filter: blur(20px);
      background: var(--card);
      border: 1px solid rgba(255, 255, 255, 0.6);
      border-radius: var(--radius-xl);
      box-shadow: var(--shadow);
      padding: 26px 22px;
      display: flex;
      flex-direction: column;
      gap: 18px;
      z-index: 3;
    }}

    .side-topbar {{
      display: flex;
      align-items: center;
      justify-content: flex-start;
      min-height: 38px;
    }}

    .back-to-form {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: none;
      border-radius: 999px;
      padding: 9px 13px;
      background: rgba(255,255,255,0.72);
      color: var(--ink-soft);
      font: inherit;
      font-size: 13px;
      cursor: pointer;
      box-shadow: 0 10px 18px rgba(190, 160, 132, 0.12);
      transition: transform 160ms ease, color 160ms ease, background 160ms ease;
    }}

    .back-to-form:hover {{
      transform: translateX(-2px);
      color: var(--ink);
      background: rgba(255,255,255,0.92);
    }}

    .hero-tag {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 14px;
      border-radius: 999px;
      background: rgba(255,255,255,0.74);
      color: var(--salmon);
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      width: fit-content;
    }}

    h1 {{
      margin: 0;
      font-family: var(--font-display);
      font-size: 34px;
      line-height: 1.08;
      letter-spacing: -0.03em;
    }}

    .hero-days {{
      margin-top: 8px;
      color: var(--ink-soft);
      font-size: 18px;
      line-height: 1.2;
    }}

    .hero-copy {{
      margin: 0;
      color: var(--ink-soft);
      line-height: 1.65;
      font-size: 14px;
    }}

    .day-switcher {{
      display: grid;
      gap: 10px;
      max-height: 360px;
      overflow-y: auto;
      padding-right: 4px;
    }}

    .day-chip {{
      padding: 14px 14px 14px 16px;
      border-radius: 18px;
      border: 1px solid transparent;
      background: rgba(255,255,255,0.58);
      cursor: pointer;
      transition: transform 180ms ease, background 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
      text-align: left;
    }}

    .day-chip-detail {{
      display: none;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid rgba(126, 111, 101, 0.12);
    }}

    .day-chip.active .day-chip-detail {{
      display: block;
    }}

    .day-chip-detail ul {{
      margin: 0;
      padding-left: 18px;
      display: grid;
      gap: 8px;
      color: var(--ink-soft);
      font-size: 13px;
      line-height: 1.5;
    }}

    .day-chip-detail li::marker {{
      color: var(--salmon);
    }}

    .day-chip:hover,
    .day-chip.active {{
      transform: translateX(4px);
      background: linear-gradient(135deg, rgba(255,247,240,0.95), rgba(255,255,255,0.88));
      border-color: rgba(217,143,112,0.18);
      box-shadow: 0 12px 24px rgba(211, 176, 145, 0.18);
    }}

    .day-chip strong {{
      display: block;
      font-size: 15px;
      margin-bottom: 4px;
    }}

    .day-chip span {{
      color: var(--ink-soft);
      font-size: 12px;
      line-height: 1.5;
    }}

    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      color: var(--ink-soft);
      font-size: 12px;
    }}

    .pill {{
      padding: 6px 10px;
      background: rgba(247, 239, 226, 0.96);
      border-radius: 999px;
    }}

    .legend {{
      display: grid;
      gap: 6px;
      padding-top: 4px;
    }}

    .legend-item {{
      display: grid;
      grid-template-columns: 28px 1fr;
      gap: 8px;
      align-items: center;
      color: var(--ink-soft);
      font-size: 11px;
    }}

    .legend-line {{
      height: 5px;
      border-radius: 999px;
      opacity: 0.95;
    }}

    .map-stage {{
      position: relative;
      border-radius: 38px;
      background: linear-gradient(180deg, rgba(255,255,255,0.5), rgba(250,242,232,0.8));
      box-shadow: var(--shadow);
      overflow: hidden;
      min-height: calc(100vh - 40px);
      isolation: isolate;
    }}

    .map-title {{
      position: absolute;
      top: 28px;
      left: 30px;
      z-index: 5;
      pointer-events: none;
    }}

    .map-title h2 {{
      margin: 0;
      font-size: 22px;
      line-height: 1.1;
      text-shadow: 0 2px 10px rgba(255,255,255,0.55);
    }}

    .map-title p {{
      margin: 8px 0 0;
      color: var(--ink-soft);
      font-size: 14px;
      text-shadow: 0 2px 10px rgba(255,255,255,0.55);
    }}

    #map {{
      position: absolute;
      inset: 0;
    }}

    .map-message {{
      position: absolute;
      inset: 50% auto auto 50%;
      transform: translate(-50%, -50%);
      width: min(640px, calc(100% - 32px));
      z-index: 8;
      padding: 0;
      border-radius: 0;
      background: transparent;
      backdrop-filter: none;
      box-shadow: none;
      display: none;
    }}

    .map-message.visible {{
      display: block;
    }}

    .map-message h3 {{
      margin: 0 0 10px;
      font-size: 18px;
    }}

    .map-message p {{
      margin: 0;
      color: var(--ink-soft);
      line-height: 1.7;
      font-size: 14px;
    }}

    .map-message code {{
      background: rgba(247, 239, 226, 0.95);
      padding: 2px 6px;
      border-radius: 8px;
    }}

    .travel-loader {{
      display: grid;
      justify-items: center;
      gap: 10px;
      padding: 0;
    }}

    .travel-loader-image-wrap {{
      width: min(420px, 72vw);
      aspect-ratio: 1;
      display: grid;
      place-items: center;
      overflow: visible;
      filter: drop-shadow(0 22px 32px rgba(190, 160, 132, 0.2));
    }}

    .travel-loader-image {{
      width: 100%;
      height: 100%;
      object-fit: contain;
    }}

    .travel-loader p {{
      margin: 0;
      color: var(--ink-soft);
      font-size: 16px;
      font-weight: 650;
      letter-spacing: 0.02em;
    }}

    .map-status {{
      position: absolute;
      right: 24px;
      bottom: 24px;
      z-index: 6;
      max-width: 420px;
      padding: 10px 14px;
      border-radius: 14px;
      background: rgba(255,255,255,0.78);
      backdrop-filter: blur(10px);
      box-shadow: 0 10px 24px rgba(180, 155, 130, 0.12);
      color: var(--ink-soft);
      font-size: 12px;
      line-height: 1.5;
    }}

    .marker-layer,
    .route-layer {{
      position: absolute;
      inset: 0;
      pointer-events: none;
    }}

    .route-layer svg {{
      width: 100%;
      height: 100%;
      overflow: visible;
    }}

    .route-layer path {{
      fill: none;
      stroke-linecap: round;
      stroke-linejoin: round;
      filter: drop-shadow(0 8px 14px rgba(140, 117, 93, 0.15));
      stroke-dasharray: 10 10;
    }}

    .route-badge {{
      position: absolute;
      transform: translate(-50%, -50%);
      min-width: 84px;
      padding: 7px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.9);
      box-shadow: 0 10px 20px rgba(192, 167, 143, 0.14);
      font-size: 12px;
      color: var(--ink-soft);
      text-align: center;
      white-space: nowrap;
    }}

    .marker-layer .marker-item {{
      position: absolute;
      width: 54px;
      height: 74px;
      transform: translate(-50%, -62px);
      overflow: visible;
      pointer-events: auto;
    }}

    .marker-layer .marker-item:hover {{
      z-index: 30;
    }}

    .marker-3d {{
      position: relative;
      width: 54px;
      transform-style: preserve-3d;
      transition: transform 180ms ease;
    }}

    .marker-pin {{
      width: 54px;
      height: 54px;
      display: grid;
      place-items: center;
      border-radius: 50%;
      background: rgba(255,255,255,0.96);
      border: 5px solid color-mix(in srgb, var(--stop-accent, var(--salmon)) 72%, white);
      box-shadow: 0 10px 18px rgba(186, 143, 113, 0.22);
      margin: 0;
      position: relative;
      z-index: 2;
      font-size: 22px;
    }}

    .marker-pin::after {{
      content: "";
      position: absolute;
      width: 14px;
      height: 14px;
      background: var(--stop-accent, var(--salmon));
      bottom: -8px;
      left: 50%;
      transform: translateX(-50%) rotate(45deg);
      border-radius: 2px;
      z-index: -1;
    }}

    .marker-card {{
      position: absolute;
      left: 50%;
      top: 66px;
      width: 186px;
      margin-top: 0;
      padding: 12px 14px;
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(255,255,255,0.97), rgba(255,247,240,0.9));
      border: 1px solid rgba(255,255,255,0.8);
      box-shadow:
        0 18px 24px rgba(180, 155, 130, 0.18),
        inset 0 1px 0 rgba(255,255,255,0.7);
      transform: translateX(-50%) perspective(800px) rotateX(12deg);
      transform-origin: center top;
      opacity: 0;
      pointer-events: none;
      transition: opacity 160ms ease, transform 160ms ease;
    }}

    .marker-item:hover .marker-card {{
      opacity: 1;
      pointer-events: auto;
      transform: translateX(-50%) perspective(800px) rotateX(0deg) translateY(2px);
    }}

    .marker-card strong {{
      display: block;
      font-size: 13px;
      margin-bottom: 4px;
      color: var(--ink);
    }}

    .marker-card span {{
      display: block;
      font-size: 11px;
      line-height: 1.5;
      color: var(--ink-soft);
    }}

    .marker-card a {{
      color: var(--salmon);
      text-decoration: none;
    }}

    .marker-flat {{
      position: relative;
      width: 54px;
      height: 54px;
      display: grid;
      place-items: center;
      border-radius: 50%;
      background: rgba(255,255,255,0.96);
      border: 5px solid color-mix(in srgb, var(--stop-accent, var(--salmon)) 72%, white);
      box-shadow: 0 10px 18px rgba(186, 143, 113, 0.22);
      font-size: 20px;
      margin: 0;
    }}

    .marker-flat::after {{
      content: "";
      position: absolute;
      width: 14px;
      height: 14px;
      background: var(--stop-accent, var(--salmon));
      bottom: -8px;
      left: 50%;
      transform: translateX(-50%) rotate(45deg);
      border-radius: 2px;
    }}

    .marker-flat-card {{
      position: absolute;
      left: 50%;
      top: 66px;
      min-width: 138px;
      max-width: 186px;
      margin-top: 0;
      padding: 12px 14px;
      border-radius: 18px;
      background: rgba(255,255,255,0.95);
      box-shadow: 0 12px 20px rgba(180, 155, 130, 0.16);
      transform: translateX(-50%);
      opacity: 0;
      pointer-events: none;
      transition: opacity 160ms ease;
      text-align: center;
    }}

    .marker-flat-card strong {{
      display: block;
      font-size: 12px;
      margin-bottom: 3px;
    }}

    .marker-flat-card span {{
      display: block;
      font-size: 11px;
      line-height: 1.4;
      color: var(--ink-soft);
    }}

    .marker-item:hover .marker-flat-card {{
      opacity: 1;
      pointer-events: auto;
    }}

    .corner-card {{
      position: absolute;
      left: 26px;
      bottom: 24px;
      width: min(360px, calc(100% - 40px));
      z-index: 5;
      padding: 18px;
      border-radius: 24px;
      background: rgba(255,255,255,0.76);
      backdrop-filter: blur(16px);
      box-shadow: var(--shadow);
    }}

    .corner-card h3 {{
      margin: 0 0 10px;
      font-size: 16px;
    }}

    .timeline {{
      display: grid;
      gap: 10px;
    }}

    .timeline-item {{
      display: grid;
      grid-template-columns: 26px 1fr;
      gap: 10px;
      align-items: start;
      font-size: 13px;
      color: var(--ink-soft);
    }}

    .timeline-item strong {{
      display: block;
      color: var(--ink);
      margin-bottom: 2px;
    }}

    @media (max-width: 1080px) {{
      body {{
        overflow: auto;
      }}

      .intro-shell {{
        grid-template-columns: 1fr;
      }}

      .planner-shell {{
        grid-template-columns: 1fr;
      }}

      .map-stage {{
        min-height: 840px;
      }}
    }}

    @media (max-width: 700px) {{
      .intro-screen {{
        padding: 14px;
      }}

      .planner-shell {{
        padding: 14px;
        gap: 14px;
      }}

      .side-panel {{
        padding: 18px;
      }}

      .map-title {{
        top: 20px;
        left: 20px;
      }}

      .map-status {{
        right: 16px;
        left: 16px;
        top: auto;
        bottom: 138px;
        max-width: none;
      }}

      .marker-3d {{
        width: 150px;
      }}

      .corner-card {{
        left: 16px;
        right: 16px;
        bottom: 16px;
        width: auto;
      }}
    }}
  </style>
</head>
<body>
  <section class="intro-screen" id="intro-screen">
    <div class="intro-shell">
      <section class="intro-hero">
        <div>
          <div class="intro-kicker" data-i18n="introKicker">Dream Route Generator</div>
          <h1 class="intro-title" data-i18n-html="introTitle">Plan First,<br>Then Wander Beautifully.</h1>
        </div>
        <div class="intro-mock">
          <div class="mock-route">
            <svg viewBox="0 0 100 100" preserveAspectRatio="none">
              <path d="M18 70 C 34 58, 34 44, 50 38 S 72 30, 84 54" fill="none" stroke="#d99a84" stroke-width="2.6" stroke-dasharray="4 4" stroke-linecap="round"/>
            </svg>
            <span style="left:16%; top:64%;">🏨</span>
            <span style="left:48%; top:34%;">⛪</span>
            <span style="left:82%; top:48%;">🍤</span>
          </div>
        </div>
      </section>
      <form class="intro-form" id="trip-form">
        <div class="form-heading">
          <h2 data-i18n="formTitle">先定义这次旅行</h2>
          <input id="language-input" name="language" type="hidden" value="zh">
          <button class="language-toggle" id="language-toggle" type="button" data-language="zh" aria-label="Switch language">
            <span class="lang-zh">🇨🇳CHN</span>
            <span class="lang-en">🇺🇸EN</span>
          </button>
        </div>
        <div class="form-grid">
          <div class="field full">
            <label for="destination-input" data-i18n="destinationLabel">Destination</label>
            <input id="destination-input" name="destination" placeholder="Barcelona / Kyoto / Istanbul">
          </div>
          <div class="field">
            <label for="days-input" data-i18n="daysLabel">Days</label>
            <input id="days-input" name="days" type="number" min="1" max="14">
          </div>
          <div class="field">
            <label for="budget-input" data-i18n="budgetLabel">Budget</label>
            <select id="budget-input" name="budget">
              <option value="" selected></option>
              <option value="轻奢体验" data-i18n="budgetLuxe">轻奢体验</option>
              <option value="高性价比" data-i18n="budgetValue">高性价比</option>
            </select>
          </div>
          <div class="field">
            <label for="pace-input" data-i18n="paceLabel">Pace</label>
            <select id="pace-input" name="pace">
              <option value="" selected></option>
              <option value="松弛漫游" data-i18n="paceSlow">松弛漫游</option>
              <option value="经典必打卡" data-i18n="paceClassic">经典必打卡</option>
              <option value="节奏紧凑" data-i18n="paceFast">节奏紧凑</option>
            </select>
          </div>
          <div class="field">
            <label for="transport-input" data-i18n="transportLabel">Transport Mode</label>
            <input id="transport-input" name="transport" list="transport-options" placeholder="">
            <datalist id="transport-options">
              <option value="公共交通"></option>
              <option value="租车 / 自驾"></option>
              <option value="步行为主"></option>
              <option value="打车为主"></option>
            </datalist>
          </div>
          <div class="field">
            <label data-i18n="styleLabel">Travel Style</label>
            <div class="style-multiselect" id="style-multiselect">
              <div class="style-trigger" id="style-trigger">
                <span class="style-placeholder" id="style-placeholder"></span>
                <input class="style-search-input" id="style-search-input" type="text" placeholder="">
                <span class="style-caret"></span>
              </div>
              <div class="style-dropdown" id="style-dropdown">
                <label class="style-option" data-style-option="建筑">
                  <input type="checkbox" name="style" value="建筑">
                  <span class="style-option-text" data-i18n="styleArchitecture">建筑</span>
                </label>
                <label class="style-option" data-style-option="博物馆">
                  <input type="checkbox" name="style" value="博物馆">
                  <span class="style-option-text" data-i18n="styleMuseum">博物馆</span>
                </label>
                <label class="style-option" data-style-option="自然风光">
                  <input type="checkbox" name="style" value="自然风光">
                  <span class="style-option-text" data-i18n="styleNature">自然风光</span>
                </label>
                <label class="style-option" data-style-option="美食">
                  <input type="checkbox" name="style" value="美食">
                  <span class="style-option-text" data-i18n="styleFood">美食</span>
                </label>
                <label class="style-option" data-style-option="购物">
                  <input type="checkbox" name="style" value="购物">
                  <span class="style-option-text" data-i18n="styleShopping">购物</span>
                </label>
                <label class="style-option" data-style-option="夜景">
                  <input type="checkbox" name="style" value="夜景">
                  <span class="style-option-text" data-i18n="styleNightView">夜景</span>
                </label>
                <label class="style-option" data-style-option="咖啡店">
                  <input type="checkbox" name="style" value="咖啡店">
                  <span class="style-option-text" data-i18n="styleCafe">咖啡店</span>
                </label>
                <label class="style-option" data-style-option="海边">
                  <input type="checkbox" name="style" value="海边">
                  <span class="style-option-text" data-i18n="styleBeach">海边</span>
                </label>
              </div>
            </div>
          </div>
          <div class="field full">
            <label for="preference-input" data-i18n="preferenceLabel">Preference</label>
            <textarea id="preference-input" name="preference" data-i18n-placeholder="preferencePlaceholder" placeholder="例如：想住在步行友好的区域，白天多看建筑，晚上想吃海鲜饭。"></textarea>
          </div>
        </div>
        <div class="form-actions">
          <button class="primary-btn" type="submit" data-i18n="submitButton">生成地图攻略</button>
          <button class="ghost-btn" type="button" id="use-demo-btn" data-i18n="demoButton">直接看 Barcelona Demo</button>
        </div>
      </form>
    </div>
  </section>

  <div class="planner-shell" id="planner-shell">
    <aside class="side-panel">
      <div class="side-topbar">
        <button class="back-to-form" id="back-to-form" type="button">
          <span aria-hidden="true">←</span>
          <span data-i18n="backButton">返回修改</span>
        </button>
      </div>
      <div>
        <h1 id="hero-title">{plan_data["destination"]}</h1>
        <div class="hero-days" id="hero-days">4 Days</div>
      </div>
      <section class="trip-input-summary" id="trip-input-summary">
        <div class="trip-summary-title" data-i18n="tripBrief">Trip Brief</div>
        <div class="meta">
          <div class="pill" id="summary-destination">Barcelona demo</div>
          <div class="pill" id="summary-days">days</div>
          <div class="pill" id="summary-budget">budget</div>
          <div class="pill" id="summary-style">travel style</div>
          <div class="pill" id="summary-transport">transport</div>
        </div>
        <p class="hero-copy" id="summary-preference" data-i18n="summaryPreferenceEmpty">填写你的旅行偏好后，这里会显示一份简短摘要。</p>
      </section>
      <div class="day-switcher" id="day-switcher"></div>
      <section class="legend" id="legend"></section>
    </aside>

    <main class="map-stage">
      <div class="map-title">
        <h2 id="map-area-name">{plan_data["destination"]}</h2>
      </div>
      <div class="map-status" id="map-status"></div>
      <div id="map"></div>
      <div class="map-message visible" id="map-message">
        <h3 data-i18n="mapPreparingTitle">正在准备地图</h3>
        <p data-i18n="mapPreparingBody">进入行程后会自动加载 Google Maps，并按点击的日期显示当天路线与点位。</p>
      </div>
      <section class="corner-card">
        <h3 data-i18n="todayRoute">当日路线</h3>
        <div class="timeline" id="timeline"></div>
      </section>
    </main>
  </div>

  <script>
    const baseTravelPlan = {payload};
    let travelPlan = JSON.parse(JSON.stringify(baseTravelPlan));
    const embeddedApiKey = {api_key};

    const translations = {{
      zh: {{
        introKicker: "Dream Route Generator",
        introTitle: "Plan First,<br>Then Wander Beautifully.",
        formTitle: "先定义这次旅行",
        destinationLabel: "Destination",
        daysLabel: "Days",
        budgetLabel: "Budget",
        budgetLuxe: "轻奢体验",
        budgetValue: "高性价比",
        paceLabel: "Pace",
        paceSlow: "松弛漫游",
        paceClassic: "经典必打卡",
        paceFast: "节奏紧凑",
        transportLabel: "Transport Mode",
        styleLabel: "Travel Style",
        styleArchitecture: "建筑",
        styleMuseum: "博物馆",
        styleNature: "自然风光",
        styleFood: "美食",
        styleShopping: "购物",
        styleNightView: "夜景",
        styleCafe: "咖啡店",
        styleBeach: "海边",
        preferenceLabel: "Preference",
        preferencePlaceholder: "例如：想住在步行友好的区域，白天多看建筑，晚上想吃海鲜饭。",
        submitButton: "生成地图攻略",
        demoButton: "直接看 Barcelona Demo",
        tripBrief: "Trip Brief",
        summaryPreferenceEmpty: "填写你的旅行偏好后，这里会显示一份简短摘要。",
        mapPreparingTitle: "正在准备地图",
        mapPreparingBody: "进入行程后会自动加载 Google Maps，并按点击的日期显示当天路线与点位。",
        mapLoadingText: "路线规划中...",
        todayRoute: "当日路线",
        backButton: "返回修改",
        legendWalk: "🚶 步行连接小街区",
        legendMetro: "🚇 地铁跨区移动",
        legendTaxi: "🚕 打车节省上坡或返程时间",
        legendTrain: "🚠 缆车 / 特色交通段",
        legendBike: "🚲 海边或平缓路段",
        legendBus: "🚌 公交连接",
        legendCar: "🚗 租车 / 自驾路线",
        statusPrefix: "状态：",
        statusWaiting: "等待加载地图",
        noBudget: "未指定预算",
        noPace: "未指定节奏",
        noStyle: "未指定风格",
        noTransport: "未指定出行方式",
        rentalCar: "租车 / 自驾",
        noPreference: "暂无额外偏好",
        daysUnit: "days",
      }},
      en: {{
        introKicker: "Dream Route Generator",
        introTitle: "Plan First,<br>Then Wander Beautifully.",
        formTitle: "Define Your Trip",
        destinationLabel: "Destination",
        daysLabel: "Days",
        budgetLabel: "Budget",
        budgetLuxe: "Comfort Luxe",
        budgetValue: "Best Value",
        paceLabel: "Pace",
        paceSlow: "Relaxed",
        paceClassic: "Classic Highlights",
        paceFast: "Packed Schedule",
        transportLabel: "Transport Mode",
        styleLabel: "Travel Style",
        styleArchitecture: "Architecture",
        styleMuseum: "Museums",
        styleNature: "Nature",
        styleFood: "Food",
        styleShopping: "Shopping",
        styleNightView: "Night Views",
        styleCafe: "Cafes",
        styleBeach: "Beach",
        preferenceLabel: "Preference",
        preferencePlaceholder: "Example: Stay in a walkable area, see architecture during the day, and have seafood at night.",
        submitButton: "Generate Map Guide",
        demoButton: "View Barcelona Demo",
        tripBrief: "Trip Brief",
        summaryPreferenceEmpty: "Your travel preference summary will appear here.",
        mapPreparingTitle: "Preparing Map",
        mapPreparingBody: "After entering the itinerary, Google Maps will load automatically and show the selected day route.",
        mapLoadingText: "Planning route...",
        todayRoute: "Day Route",
        backButton: "Back to Edit",
        legendWalk: "🚶 Walkable neighborhood links",
        legendMetro: "🚇 Transit across districts",
        legendTaxi: "🚕 Taxi for hills or long transfers",
        legendTrain: "🚠 Cable car / special transit",
        legendBike: "🚲 Bike-friendly or coastal routes",
        legendBus: "🚌 Bus connection",
        legendCar: "🚗 Rental car / self-drive route",
        statusPrefix: "Status: ",
        statusWaiting: "Waiting for map",
        noBudget: "No budget selected",
        noPace: "No pace selected",
        noStyle: "No travel style selected",
        noTransport: "No transport selected",
        rentalCar: "Rental Car / Self-drive",
        noPreference: "No extra preference",
        daysUnit: "days",
      }},
    }};

    const state = {{
      activeDayIndex: null,
      tripProfile: null,
      planSignature: "",
      map: null,
      overlay: null,
      routeOverlay: null,
      overlayClasses: null,
      apiLoaded: false,
      isLoadingMap: false,
      activeApiKey: "",
      language: "zh",
      areaLookupTimer: null,
      markerElements: new Map(),
      activeRoutePolylines: [],
      activeBadgeData: [],
      activeDayBounds: null,
    }};

    const introScreen = document.getElementById("intro-screen");
    const plannerShell = document.getElementById("planner-shell");
    const tripForm = document.getElementById("trip-form");
    const backToFormBtn = document.getElementById("back-to-form");
    const useDemoBtn = document.getElementById("use-demo-btn");
    const daySwitcher = document.getElementById("day-switcher");
    const legend = document.getElementById("legend");
    const timeline = document.getElementById("timeline");
    const messageBox = document.getElementById("map-message");
    const mapContainer = document.getElementById("map");
    const mapStatus = document.getElementById("map-status");
    const heroTitle = document.getElementById("hero-title");
    const heroDays = document.getElementById("hero-days");
    const mapAreaName = document.getElementById("map-area-name");
    const languageInput = document.getElementById("language-input");
    const languageToggle = document.getElementById("language-toggle");
    const styleMultiselect = document.getElementById("style-multiselect");
    const styleTrigger = document.getElementById("style-trigger");
    const styleDropdown = document.getElementById("style-dropdown");
    const styleSearchInput = document.getElementById("style-search-input");
    const stylePlaceholder = document.getElementById("style-placeholder");

    function getLanguage() {{
      return languageInput?.value || languageToggle?.dataset.language || state.language || "zh";
    }}

    function t(key) {{
      const lang = getLanguage();
      return translations[lang]?.[key] || translations.zh[key] || key;
    }}

    function applyLanguage() {{
      state.language = getLanguage();
      if (languageInput) languageInput.value = state.language;
      if (languageToggle) languageToggle.dataset.language = state.language;
      document.documentElement.lang = state.language === "en" ? "en" : "zh-CN";
      document.querySelectorAll("[data-i18n]").forEach((node) => {{
        node.textContent = t(node.dataset.i18n);
      }});
      document.querySelectorAll("[data-i18n-html]").forEach((node) => {{
        node.innerHTML = t(node.dataset.i18nHtml);
      }});
      document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {{
        node.setAttribute("placeholder", t(node.dataset.i18nPlaceholder));
      }});
      if (!state.tripProfile) {{
        document.getElementById("summary-preference").textContent = t("summaryPreferenceEmpty");
      }}
      if (!mapStatus.textContent) {{
        setStatus(t("statusWaiting"));
      }}
      renderSelectedStyleChips();
      createLegend();
    }}

    function showMessage(title, body) {{
      messageBox.classList.add("visible");
      messageBox.innerHTML = `<h3>${{title}}</h3><p>${{body}}</p>`;
    }}

    function showLoadingMapMessage() {{
      messageBox.classList.add("visible");
      messageBox.innerHTML = `
        <div class="travel-loader" role="status" aria-live="polite">
          <div class="travel-loader-image-wrap" aria-hidden="true">
            <img class="travel-loader-image" src="assets/travel-loader-globe.png" alt="" />
          </div>
          <p>${{t("mapLoadingText")}}</p>
        </div>
      `;
    }}

    function setStatus(text) {{
      mapStatus.textContent = `${{t("statusPrefix")}}${{text}}`;
    }}

    function getStyleCheckboxes() {{
      return Array.from(styleDropdown.querySelectorAll('input[name="style"]'));
    }}

    function getSelectedStyleValues() {{
      return getStyleCheckboxes().filter((item) => item.checked).map((item) => item.value);
    }}

    function renderSelectedStyleChips() {{
      styleTrigger.querySelectorAll(".selected-chip").forEach((item) => item.remove());
      const selected = getSelectedStyleValues();
      stylePlaceholder.style.display = selected.length ? "none" : "inline";

      selected.forEach((value) => {{
        const chip = document.createElement("span");
        chip.className = "selected-chip";
        chip.innerHTML = `${{styleLabelForValue(value)}} <button type="button" aria-label="移除 ${{value}}" data-remove-style="${{value}}">×</button>`;
        styleTrigger.insertBefore(chip, styleSearchInput);
      }});
    }}

    function filterStyleOptions(query) {{
      const keyword = String(query || "").trim().toLowerCase();
      styleDropdown.querySelectorAll(".style-option").forEach((option) => {{
        const value = option.dataset.styleOption || "";
        const label = option.textContent || "";
        option.style.display = !keyword || `${{value}} ${{label}}`.toLowerCase().includes(keyword) ? "flex" : "none";
      }});
    }}

    function styleLabelForValue(value) {{
      const keyMap = {{
        "建筑": "styleArchitecture",
        "博物馆": "styleMuseum",
        "自然风光": "styleNature",
        "美食": "styleFood",
        "购物": "styleShopping",
        "夜景": "styleNightView",
        "咖啡店": "styleCafe",
        "海边": "styleBeach",
      }};
      return keyMap[value] ? t(keyMap[value]) : value;
    }}

    function openStyleDropdown() {{
      styleDropdown.classList.add("open");
    }}

    function closeStyleDropdown() {{
      styleDropdown.classList.remove("open");
      styleSearchInput.value = "";
      filterStyleOptions("");
    }}

    function titleCaseWords(value) {{
      return String(value || "")
        .split(/\s+/)
        .filter(Boolean)
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
    }}

    function slugify(value) {{
      return String(value || "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
    }}

    function cloneBasePlan() {{
      return JSON.parse(JSON.stringify(baseTravelPlan));
    }}

    function getDayCountFromProfile(profile) {{
      const count = Number.parseInt(profile.days, 10);
      return Number.isFinite(count) ? Math.max(1, Math.min(count, 7)) : 4;
    }}

    function toSentenceCase(value) {{
      const text = String(value || "").trim();
      if (!text) return "";
      return text.charAt(0).toUpperCase() + text.slice(1);
    }}

    function normalizeTransport(value) {{
      const text = String(value || "").trim();
      const lowered = text.toLowerCase();
      if (!text) return {{
        value: "",
        label: t("noTransport"),
        isRentalCar: false,
      }};
      const isRentalCar = /租车|自驾|开车|驾车|car|drive|driving|rental/.test(lowered);
      return {{
        value: text,
        label: isRentalCar ? t("rentalCar") : text,
        isRentalCar,
      }};
    }}

    function collectTripProfile() {{
      const formData = new FormData(tripForm);
      const styles = formData.getAll("style").map((item) => String(item).trim()).filter(Boolean);
      const styleDisplay = styles.map(styleLabelForValue);
      const transport = normalizeTransport(formData.get("transport"));
      return {{
        language: getLanguage(),
        destination: String(formData.get("destination") || "").trim() || "Barcelona",
        days: String(formData.get("days") || "").trim() || "4",
        budget: String(formData.get("budget") || "").trim() || t("noBudget"),
        pace: String(formData.get("pace") || "").trim() || t("noPace"),
        style: styleDisplay.length ? styleDisplay.join(" / ") : t("noStyle"),
        styleTags: styles,
        transport: transport.label,
        transportRaw: transport.value,
        isRentalCar: transport.isRentalCar,
        preference: String(formData.get("preference") || "").trim() || t("noPreference"),
      }};
    }}

    function applyTripProfile(profile) {{
      state.tripProfile = profile;
      if (profile.language && languageInput.value !== profile.language) {{
        languageInput.value = profile.language;
        if (languageToggle) languageToggle.dataset.language = profile.language;
        applyLanguage();
      }}
      document.title = `Travel Planner -- ${{profile.destination}}`;
      heroTitle.textContent = profile.destination;
      heroDays.textContent = `${{profile.days}} Days`;
      mapAreaName.textContent = profile.destination;
      document.getElementById("summary-destination").textContent = profile.destination;
      document.getElementById("summary-days").textContent = `${{profile.days}} ${{t("daysUnit")}}`;
      document.getElementById("summary-budget").textContent = profile.budget;
      document.getElementById("summary-style").textContent = `${{profile.style}} · ${{profile.pace}}`;
      document.getElementById("summary-transport").textContent = profile.transport;
      document.getElementById("summary-preference").textContent = profile.preference;
    }}

    function updatePlanHeadings() {{
      mapAreaName.textContent = travelPlan.destination || state.tripProfile?.destination || "";
      if (state.tripProfile) {{
        heroTitle.textContent = state.tripProfile.destination;
        heroDays.textContent = `${{getDayCountFromProfile(state.tripProfile)}} Days`;
      }}
    }}

    function enterPlanner(profile) {{
      applyTripProfile(profile);
      introScreen.style.display = "none";
      plannerShell.classList.add("active");
      createPendingDayChips(profile);
      timeline.innerHTML = "";
      if (embeddedApiKey) {{
        initMap();
      }} else {{
        setStatus("缺少 Google Maps API Key");
        showMessage("缺少 Google Maps API Key", "为了安全发布到 GitHub，API Key 已改为从本地 <code>.env</code> 或环境变量 <code>GOOGLE_MAPS_API_KEY</code> 读取，不再写入源码。");
      }}
    }}

    function goBackToIntro() {{
      plannerShell.classList.remove("active");
      introScreen.style.display = "grid";
      document.title = "Travel Planner";
      clearDaySelection();
      window.scrollTo({{ top: 0, behavior: "smooth" }});
    }}

    function setButtonLoading(isLoading) {{
      state.isLoadingMap = isLoading;
      setStatus(isLoading ? "正在请求 Google Maps..." : "地图准备就绪");
    }}

    function escapeHtml(value) {{
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }}

    function formatMapsError(rawMessage) {{
      const text = String(rawMessage || "");
      const knownErrors = [
        "RefererNotAllowedMapError",
        "InvalidKeyMapError",
        "ApiNotActivatedMapError",
        "BillingNotEnabledMapError",
        "ClientBillingNotEnabledMapError",
        "ExpiredKeyMapError",
        "DeletedApiProjectMapError",
        "MissingKeyMapError",
      ];

      const matched = knownErrors.find((item) => text.includes(item));
      if (!matched) {{
        return escapeHtml(text || "未知错误，请检查浏览器控制台。");
      }}

      const hints = {{
        RefererNotAllowedMapError: "当前 key 的网站来源限制不允许这个页面。若你现在是从 file:// 打开，通常会失败。请改用 localhost，并在 Google Cloud Console 把允许来源加上 http://localhost/*。",
        InvalidKeyMapError: "API Key 无效，请确认复制完整、没有多余空格，并且属于正确的 Google Cloud 项目。",
        ApiNotActivatedMapError: "这个项目还没启用 Maps JavaScript API。到 Google Cloud Console 为该项目启用它。",
        BillingNotEnabledMapError: "这个项目没有开启 billing，Maps JavaScript API 无法加载。",
        ClientBillingNotEnabledMapError: "当前前端使用的项目没有可用 billing，请检查 key 归属项目。",
        ExpiredKeyMapError: "这个 key 已失效，请更换有效 key。",
        DeletedApiProjectMapError: "这个 key 所属项目可能已删除或不可用。",
        MissingKeyMapError: "请求里没有有效 key。",
      }};

      return `<strong>${{matched}}</strong><br>${{hints[matched]}}`;
    }}

    function resetGoogleMapsLoader() {{
      const existing = document.querySelector('script[data-google-maps-loader="true"]');
      if (existing) {{
        existing.remove();
      }}
      state.apiLoaded = false;
      if (window.google && window.google.maps && state.map) {{
        state.activeRoutePolylines.forEach((line) => line.setMap(null));
      }}
      state.map = null;
      state.overlay = null;
      state.routeOverlay = null;
      state.markerElements = new Map();
      state.activeRoutePolylines = [];
      state.activeBadgeData = [];
      mapContainer.innerHTML = "";
      window.__initGoogleMapsForTravelGuide = undefined;
      window.gm_authFailure = undefined;
    }}

    function createLegend() {{
      legend.innerHTML = "";
      Object.entries(travelPlan.transportStyles).forEach(([mode, style]) => {{
        const row = document.createElement("div");
        row.className = "legend-item";

        const line = document.createElement("div");
        line.className = "legend-line";
        line.style.background = style.color;
        if (style.icons) {{
          line.style.background = `repeating-linear-gradient(90deg, ${{style.color}} 0 10px, transparent 10px 18px)`;
        }}

        const text = document.createElement("div");
        text.textContent = {{
          walk: t("legendWalk"),
          metro: t("legendMetro"),
          taxi: t("legendTaxi"),
          train: t("legendTrain"),
          bike: t("legendBike"),
          bus: t("legendBus"),
          car: t("legendCar"),
        }}[mode] || mode;

        row.append(line, text);
        legend.appendChild(row);
      }});
    }}

    function createDayChips() {{
      daySwitcher.innerHTML = "";
      travelPlan.dayPlans.forEach((day, index) => {{
        const chip = document.createElement("button");
        chip.className = "day-chip";
        chip.type = "button";
        const detailItems = buildDayNarrative(day)
          .map((item) => `<li>${{item}}</li>`)
          .join("");
        chip.innerHTML = `
          <strong>${{day.day}}</strong>
          <span>${{day.title}}</span>
          <div class="day-chip-detail">
            <ul>${{detailItems}}</ul>
          </div>
        `;
        chip.addEventListener("click", () => toggleActiveDay(index));
        daySwitcher.appendChild(chip);
      }});
    }}

    function createPendingDayChips(profile) {{
      daySwitcher.innerHTML = "";
      const dayCount = getDayCountFromProfile(profile);
      for (let index = 0; index < dayCount; index += 1) {{
        const chip = document.createElement("button");
        chip.className = "day-chip pending";
        chip.type = "button";
        chip.disabled = true;
        chip.innerHTML = `<strong>Day ${{index + 1}}</strong>`;
        daySwitcher.appendChild(chip);
      }}
    }}

    function renderTimeline(dayPlan) {{
      timeline.innerHTML = "";
      dayPlan.route.forEach((segment) => {{
        const toLocation = travelPlan.locations[segment.to_stop];
        const item = document.createElement("div");
        item.className = "timeline-item";
        item.innerHTML = `
          <div>${{segment.emoji}}</div>
          <div>
            <strong>${{toLocation.title}}</strong>
            <span>${{segment.minutes}} 分钟 · ${{segment.tip}}</span>
          </div>
        `;
        timeline.appendChild(item);
      }});
    }}

    function getStopLabel(stopKey) {{
      const stop = travelPlan.locations[stopKey];
      return stop ? stop.title : "下一站";
    }}

    function formatConnection(segment) {{
      if (!segment) return "";
      const fromName = getStopLabel(segment.from_stop);
      const toName = getStopLabel(segment.to_stop);
      const stationText = segment.mode === "metro"
        ? `，起点站：${{segment.start_station || `${{fromName}} 附近站`}}，终点站：${{segment.end_station || `${{toName}} 附近站`}}`
        : "";
      return `【${{fromName}}到${{toName}} ${{segment.emoji}}${{segment.minutes}}min${{stationText}}】`;
    }}

    function requiresReservation(stop) {{
      const label = `${{stop.linkLabel || stop.link_label || ""}}`.toLowerCase();
      return /预订|预约|门票|购票|ticket|book/.test(label);
    }}

    function buildDayNarrative(dayPlan) {{
      const labels = ["上午", "午餐", "下午", "傍晚", "晚上"];
      const items = [];
      dayPlan.route.forEach((segment, index) => {{
        const stop = travelPlan.locations[segment.to_stop];
        if (!stop) return;
        const label = stop.category === "food" ? "午餐" : labels[Math.min(index, labels.length - 1)];
        const duration = stop.category === "food" ? "预计1小时" : "预计2-3小时";
        const reservation = requiresReservation(stop) ? " 需预约" : "";
        items.push(`${{label}}：${{stop.title}}（${{duration}}） ${{formatConnection(segment)}}${{reservation}}`);
      }});
      if (dayPlan.restaurantOptions && dayPlan.restaurantOptions.length) {{
        items.push(`晚餐：${{dayPlan.restaurantOptions.join(" / ")}}`);
      }}
      return items.length ? items : ["点击后将在地图中显示当天路线与点位。"];
    }}

    function clearDaySelection() {{
      state.activeDayIndex = null;
      [...daySwitcher.children].forEach((chip) => chip.classList.remove("active"));
      timeline.innerHTML = "";
      if (state.map && state.routeOverlay) {{
        state.markerElements.forEach((el) => {{
          el.style.display = "none";
        }});
        clearActivePolylines();
        state.routeOverlay.setBadgeData([]);
      }}
    }}

    function isThreeDCategory(category) {{
      return ["sight", "food", "view"].includes(category);
    }}

    function createMarkerHtml(stop) {{
      const reservationLabel = requiresReservation(stop) ? "预约 / 购票" : "";
      const linkMarkup = stop.link
        ? `<span><a href="${{stop.link}}" target="_blank" rel="noreferrer">${{reservationLabel || stop.linkLabel || "查看链接"}}</a></span>`
        : "";

      if (isThreeDCategory(stop.category)) {{
        return `
          <div class="marker-3d" style="--stop-accent:${{stop.accent || "#d98f70"}}">
            <div class="marker-pin">${{stop.emoji}}</div>
            <div class="marker-card">
              <strong>${{stop.title}}</strong>
              <span>${{stop.subtitle}}</span>
              <span>${{stop.description}}</span>
              ${{linkMarkup}}
            </div>
          </div>
        `;
      }}

      return `
        <div class="marker-flat" style="--stop-accent:${{stop.accent || "#d98f70"}}">${{stop.emoji}}</div>
        <div class="marker-flat-card">
          <strong>${{stop.title}}</strong>
          <span>${{stop.subtitle}}</span>
          ${{linkMarkup}}
        </div>
      `;
    }}

    function ensureOverlayClasses() {{
      if (state.overlayClasses) {{
        return state.overlayClasses;
      }}

      class HtmlMarkerOverlay extends google.maps.OverlayView {{
        constructor(map, stops) {{
          super();
          this.map = map;
          this.stops = stops;
          this.container = null;
          this.setMap(map);
        }}

        onAdd() {{
          this.container = document.createElement("div");
          this.container.className = "marker-layer";
          this.getPanes().overlayMouseTarget.appendChild(this.container);

          Object.entries(this.stops).forEach(([key, stop]) => {{
            const el = document.createElement("div");
            el.className = "marker-item";
            el.dataset.stopKey = key;
            el.innerHTML = createMarkerHtml(stop);
            this.container.appendChild(el);
            state.markerElements.set(key, el);
          }});
        }}

        draw() {{
          const projection = this.getProjection();
          if (!projection || !this.container) return;

          Object.entries(this.stops).forEach(([key, stop]) => {{
            const pixel = projection.fromLatLngToDivPixel(
              new google.maps.LatLng(stop.lat, stop.lng)
            );
            const el = state.markerElements.get(key);
            if (!pixel || !el) return;
            el.style.left = `${{pixel.x}}px`;
            el.style.top = `${{pixel.y}}px`;
          }});
        }}

        onRemove() {{
          if (this.container) this.container.remove();
        }}
      }}

      class RouteOverlay extends google.maps.OverlayView {{
        constructor(map) {{
          super();
          this.map = map;
          this.container = null;
          this.svg = null;
          this.segments = [];
          this.setMap(map);
        }}

        onAdd() {{
          this.container = document.createElement("div");
          this.container.className = "route-layer";
          this.svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
          this.container.appendChild(this.svg);
          this.getPanes().overlayLayer.appendChild(this.container);
        }}

        draw() {{
          if (!this.container || !this.svg) return;
          const div = this.getMap().getDiv();
          this.container.style.width = `${{div.offsetWidth}}px`;
          this.container.style.height = `${{div.offsetHeight}}px`;
          this.svg.setAttribute("viewBox", `0 0 ${{div.offsetWidth}} ${{div.offsetHeight}}`);
          this.redraw();
        }}

        setSegments(segments) {{
          this.segments = segments;
          this.redraw();
        }}

        setBadgeData(badges) {{
          state.activeBadgeData = badges;
          this.redrawBadges();
        }}

        redraw() {{
          if (!this.svg || !this.getProjection()) return;
          this.svg.innerHTML = "";
          this.segments.forEach((segment) => {{
            const pathD = buildCurvedPath(this.getProjection(), segment.startLatLng, segment.endLatLng);
            if (pathD) this.addPath(pathD, segment.style);
          }});
          this.redrawBadges();
        }}

        redrawBadges() {{
          if (!this.container || !this.getProjection()) return;
          this.container.querySelectorAll(".route-badge").forEach((el) => el.remove());

          state.activeBadgeData.forEach((badge) => {{
            const startPx = this.getProjection().fromLatLngToDivPixel(badge.startLatLng);
            const endPx = this.getProjection().fromLatLngToDivPixel(badge.endLatLng);
            if (!startPx || !endPx) return;

            const el = document.createElement("div");
            el.className = "route-badge";
            el.innerHTML = `${{badge.emoji}} ${{badge.minutes}} min`;
            el.style.left = `${{(startPx.x + endPx.x) / 2}}px`;
            el.style.top = `${{(startPx.y + endPx.y) / 2}}px`;
            this.container.appendChild(el);
          }});
        }}

        clearPaths() {{
          if (this.svg) this.svg.innerHTML = "";
        }}

        addPath(pathD, style) {{
          if (!this.svg) return;
          const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
          path.setAttribute("d", pathD);
          path.setAttribute("stroke", style.color);
          path.setAttribute("stroke-width", style.weight);
          if (style.icons) {{
            path.setAttribute("stroke-dasharray", style.icons);
          }}
          this.svg.appendChild(path);
        }}

        onRemove() {{
          if (this.container) this.container.remove();
        }}
      }}

      state.overlayClasses = {{ HtmlMarkerOverlay, RouteOverlay }};
      return state.overlayClasses;
    }}

    function haversineKm(a, b) {{
      const toRad = (value) => (value * Math.PI) / 180;
      const earth = 6371;
      const dLat = toRad(b.lat - a.lat);
      const dLng = toRad(b.lng - a.lng);
      const s1 = Math.sin(dLat / 2) ** 2;
      const s2 =
        Math.cos(toRad(a.lat)) *
        Math.cos(toRad(b.lat)) *
        Math.sin(dLng / 2) ** 2;
      const c = 2 * Math.atan2(Math.sqrt(s1 + s2), Math.sqrt(1 - s1 - s2));
      return earth * c;
    }}

    function estimateSegment(start, end) {{
      const distanceKm = haversineKm(start, end);
      if (distanceKm < 1.1) {{
        return {{
          mode: "walk",
          emoji: "🚶",
          minutes: Math.max(8, Math.round((distanceKm / 4.6) * 60)),
          tip: "适合步行慢逛过去",
        }};
      }}
      if (distanceKm < 3.5) {{
        return {{
          mode: "metro",
          emoji: "🚇",
          minutes: Math.max(12, Math.round((distanceKm / 24) * 60) + 6),
          tip: "地铁跨区移动更省力",
        }};
      }}
      if (distanceKm < 7) {{
        return {{
          mode: "taxi",
          emoji: "🚕",
          minutes: Math.max(16, Math.round((distanceKm / 26) * 60) + 8),
          tip: "打车更顺滑，适合衔接下一个点",
        }};
      }}
      return {{
        mode: "train",
        emoji: "🚆",
        minutes: Math.max(24, Math.round((distanceKm / 32) * 60) + 10),
        tip: "较远距离建议公共交通或城市快线",
      }};
    }}

    function estimateCarSegment(start, end) {{
      const distanceKm = haversineKm(start, end);
      return {{
        mode: "car",
        emoji: "🚗",
        minutes: Math.max(8, Math.round((distanceKm / 28) * 60) + 7),
        tip: "自驾前往，时间已按城市道路粗略估算",
      }};
    }}

    function applyTransportPreferenceToPlan(plan, profile) {{
      if (!profile?.isRentalCar) return plan;
      plan.dayPlans.forEach((dayPlan) => {{
        dayPlan.route = dayPlan.route.map((segment) => {{
          const start = plan.locations[segment.from_stop];
          const end = plan.locations[segment.to_stop];
          const carSegment = start && end ? estimateCarSegment(start, end) : {{
            mode: "car",
            emoji: "🚗",
            minutes: segment.minutes,
            tip: "自驾前往",
          }};
          return {{
            ...segment,
            mode: carSegment.mode,
            emoji: carSegment.emoji,
            minutes: carSegment.minutes,
            tip: carSegment.tip,
            start_station: null,
            end_station: null,
          }};
        }});
      }});
      return plan;
    }}

    function textSearchPromise(service, request) {{
      return new Promise((resolve, reject) => {{
        service.textSearch(request, (results, status) => {{
          if (status === google.maps.places.PlacesServiceStatus.OK && results) {{
            resolve(results);
            return;
          }}
          if (status === google.maps.places.PlacesServiceStatus.ZERO_RESULTS) {{
            resolve([]);
            return;
          }}
          reject(new Error(`Places text search failed: ${{status}}`));
        }});
      }});
    }}

    function nearbySearchPromise(service, request) {{
      return new Promise((resolve) => {{
        service.nearbySearch(request, (results, status) => {{
          if (status === google.maps.places.PlacesServiceStatus.OK && results && results.length) {{
            resolve(results);
            return;
          }}
          resolve([]);
        }});
      }});
    }}

    async function findNearbyTransitStation(service, location) {{
      const results = await nearbySearchPromise(service, {{
        location: {{ lat: location.lat, lng: location.lng }},
        radius: 900,
        type: "subway_station",
      }});
      return results[0] ? results[0].name : `${{location.title}} 附近站`;
    }}

    async function geocodeDestination(destination) {{
      const geocoder = new google.maps.Geocoder();
      const response = await geocoder.geocode({{ address: destination }});
      if (!response.results || !response.results.length) {{
        throw new Error("No geocoding results for this destination.");
      }}
      return response.results[0];
    }}

    function extractAddressPart(result, type) {{
      const part = (result.address_components || []).find((item) => item.types.includes(type));
      return part ? part.long_name : "";
    }}

    function dedupePlaces(list) {{
      const seen = new Set();
      return list.filter((item) => {{
        const key = item.place_id || `${{item.name}}-${{item.formatted_address || ""}}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      }});
    }}

    function hasPlaceGeometry(place) {{
      return Boolean(place && place.geometry && place.geometry.location);
    }}

    function normalizePreferenceText(value) {{
      const text = String(value || "").trim();
      return text === "暂无额外偏好" ? "" : text;
    }}

    function inferPreferenceCategory(value) {{
      const text = normalizePreferenceText(value).toLowerCase();
      if (!text) return "";
      if (/dinner|lunch|breakfast|brunch|restaurant|food|eat|meal|cafe|coffee|bar|sushi|ramen|burger|steak|bbq|pizza|seafood|taco|thai|korean|japanese|chinese|mexican|italian|french|fine dining|餐厅|晚餐|午餐|早餐|早午餐|美食|吃|咖啡|酒吧|寿司|拉面|汉堡|牛排|海鲜|火锅|烧烤|甜品/.test(text)) return "food";
      if (/\b(hotel|hostel|inn|resort|stay)\b|住宿|酒店|入住/.test(text)) return "hotel";
      return "sight";
    }}

    function placeMatchesCategory(place, category) {{
      const types = place.types || [];
      if (category === "hotel") return types.includes("lodging");
      if (category === "food") {{
        return types.some((type) => ["restaurant", "food", "cafe", "bakery", "bar", "meal_takeaway"].includes(type));
      }}
      return !types.includes("lodging") && !types.includes("restaurant") && !types.includes("food");
    }}

    function prioritizePlace(list, preferredPlace) {{
      if (!preferredPlace) return dedupePlaces(list);
      return dedupePlaces([preferredPlace, ...list]);
    }}

    function describePlace(place, category) {{
      const types = place.types || [];
      if (category === "food") {{
        return place.rating
          ? `评分约 ${{place.rating}}，适合作为当天用餐停留。`
          : "适合作为当天用餐停留，方便衔接后续路线。";
      }}
      if (category === "hotel") {{
        return "适合作为行程起点，方便连接当天路线。";
      }}
      if (types.includes("museum") || types.includes("art_gallery")) {{
        return "适合安排文化与艺术主题停留。";
      }}
      if (types.includes("park") || types.includes("natural_feature")) {{
        return "适合散步、看景和放慢节奏。";
      }}
      if (types.includes("church") || types.includes("place_of_worship")) {{
        return "以建筑与历史氛围见长，适合细看细逛。";
      }}
      if (types.includes("tourist_attraction")) {{
        return "城市代表性景点，适合安排为当天核心停留。";
      }}
      return "适合作为城市探索中的特色停留点。";
    }}

    function inferPlaceEmoji(place, category) {{
      const name = String(place.name || "").toLowerCase();
      const types = place.types || [];
      if (category === "hotel") return "🏨";
      if (category === "food") {{
        if (/sushi|omakase|ramen|izakaya|japanese/.test(name)) return "🍣";
        if (/burger|shake shack|hamburger/.test(name)) return "🍔";
        if (/steak|grill|bbq|barbecue/.test(name)) return "🥩";
        if (/bar|cocktail|wine|pub|lounge/.test(name) || types.includes("bar")) return "🍹";
        if (/pizza|pizzeria/.test(name)) return "🍕";
        if (/cafe|coffee|bakery|patisserie/.test(name) || types.includes("cafe") || types.includes("bakery")) return "☕";
        if (/fine|tasting|michelin|chef|restaurant/.test(name)) return "🍴";
        return "🍽️";
      }}
      if (types.includes("park") || /park|garden|jardin|botanic/.test(name)) return "⛲️";
      if (/beach|seaside|coast|bay|island|plage/.test(name) || types.includes("natural_feature")) return "🏝️";
      if (types.includes("museum") || /museum|gallery|musee|museo/.test(name)) return "🏛️";
      if (types.includes("church") || types.includes("place_of_worship") || /cathedral|church|basilica|temple|mosque|synagogue/.test(name)) return "⛪";
      if (/tower|observatory|view|summit|lookout|skyline/.test(name)) return "🗼";
      if (/palace|castle|fort|chateau/.test(name)) return "🏰";
      if (/market|bazaar|mercado/.test(name)) return "🛍️";
      return "🏰";
    }}

    function inferLinkLabel(place, category) {{
      const name = String(place.name || "").toLowerCase();
      const types = place.types || [];
      if (
        category === "sight" &&
        (types.includes("museum") ||
          types.includes("art_gallery") ||
          /museum|gallery|observatory|tower|palace|castle|aquarium|zoo|theme park|ticket/.test(name))
      ) {{
        return "预约 / 购票";
      }}
      return "Google Maps";
    }}

    function placeToLocation(place, category, index) {{
      const geometry = place.geometry && place.geometry.location;
      const lat = typeof geometry.lat === "function" ? geometry.lat() : geometry.lat;
      const lng = typeof geometry.lng === "function" ? geometry.lng() : geometry.lng;
      const accentMap = {{
        sight: "#de8c6d",
        food: "#d7b78d",
        hotel: "#d98f70",
        view: "#89b7c7",
      }};
      return {{
        name: place.name,
        category,
        lat,
        lng,
        title: place.name,
        subtitle: place.formatted_address || place.vicinity || place.name,
        emoji: inferPlaceEmoji(place, category),
        description: describePlace(place, category),
        link: place.place_id ? `https://www.google.com/maps/place/?q=place_id:${{place.place_id}}` : null,
        linkLabel: place.place_id ? inferLinkLabel(place, category) : null,
        accent: accentMap[category] || "#d98f70",
      }};
    }}

    function buildShortDaySummary(dayStops, dayIndex = 0) {{
      const typeSet = new Set(dayStops.flatMap((place) => place.types || []));
      const names = dayStops.map((place) => String(place.name || "").toLowerCase()).join(" ");
      const hasFood = dayStops.some((place) => {{
        const types = place.types || [];
        return types.some((type) => ["restaurant", "food", "cafe", "bakery", "bar"].includes(type));
      }});
      const hasMuseum = typeSet.has("museum") || typeSet.has("art_gallery") || /museum|gallery|louvre|musee|museo|art/.test(names);
      const hasPark = typeSet.has("park") || typeSet.has("natural_feature") || /park|garden|jardin|tuileries|forest|botanic/.test(names);
      const hasChurch = typeSet.has("church") || typeSet.has("place_of_worship") || /cathedral|basilica|church|temple|sainte|notre/.test(names);
      const hasView = /tower|observatory|view|summit|lookout|hill|mont|arc /.test(names);
      const hasMarket = /market|bazaar|shopping|mall|street/.test(names);

      const candidates = [];
      if (hasMuseum) candidates.push("艺术经典");
      if (hasChurch) candidates.push("建筑巡礼");
      if (hasPark) candidates.push("花园漫游");
      if (hasView) candidates.push("城市眺望");
      if (hasMarket) candidates.push("街区闲逛");
      if (hasFood) candidates.push("美食探索");

      if (candidates.length >= 2) return `${{candidates[0]}}·${{candidates[1]}}`;
      if (candidates.length === 1) return candidates[0];

      return ["城市初见", "街区漫游", "经典地标", "慢游收尾"][dayIndex % 4];
    }}

    function rebuildPlannerUI() {{
      updatePlanHeadings();
      createLegend();
      createDayChips();
      clearDaySelection();
    }}

    async function searchPreferencePlace(service, profile, locality, center) {{
      const preferenceText = normalizePreferenceText(profile.preference);
      if (!preferenceText) return null;

      const category = inferPreferenceCategory(preferenceText);
      const categoryQuery = {{
        food: `${{preferenceText}} restaurant in ${{locality}}`,
        hotel: `${{preferenceText}} hotel in ${{locality}}`,
        sight: `${{preferenceText}} in ${{locality}}`,
      }}[category] || `${{preferenceText}} in ${{locality}}`;
      const queries = [...new Set([categoryQuery, `${{preferenceText}} ${{locality}}`])];

      for (const query of queries) {{
        const results = await textSearchPromise(service, {{
          query,
          location: center,
          radius: 18000,
        }});
        const match = dedupePlaces(results)
          .filter(hasPlaceGeometry)
          .find((place) => placeMatchesCategory(place, category)) || dedupePlaces(results).find(hasPlaceGeometry);
        if (match) {{
          match.__preferredCategory = category;
          return match;
        }}
      }}
      return null;
    }}

    async function buildDynamicTravelPlan(profile) {{
      const signature = `${{profile.destination}}::${{getDayCountFromProfile(profile)}}::${{profile.style}}::${{profile.budget}}::${{profile.pace}}::${{profile.transport}}::${{profile.preference}}`;
      if (state.planSignature === signature && travelPlan.dayPlans.length) {{
        return;
      }}

      if (
        profile.destination.trim().toLowerCase() === "barcelona" &&
        getDayCountFromProfile(profile) === 4 &&
        !normalizePreferenceText(profile.preference)
      ) {{
        travelPlan = cloneBasePlan();
        applyTransportPreferenceToPlan(travelPlan, profile);
        state.planSignature = signature;
        rebuildPlannerUI();
        return;
      }}

      setStatus(`正在检索 ${{profile.destination}} 的城市坐标...`);
      const geocodeResult = await geocodeDestination(profile.destination);
      const country = extractAddressPart(geocodeResult, "country") || "Dynamic Route";
      const locality =
        extractAddressPart(geocodeResult, "locality") ||
        extractAddressPart(geocodeResult, "administrative_area_level_1") ||
        toSentenceCase(profile.destination);
      const location = geocodeResult.geometry.location;
      const center = {{
        lat: typeof location.lat === "function" ? location.lat() : location.lat,
        lng: typeof location.lng === "function" ? location.lng() : location.lng,
      }};

      const service = new google.maps.places.PlacesService(document.createElement("div"));
      setStatus(`正在搜索 ${{locality}} 的景点、餐厅和酒店...`);

      const dayCount = getDayCountFromProfile(profile);
      const styleKeywords = (profile.styleTags && profile.styleTags.length ? profile.styleTags : ["景点", "美食"]).join(" ");
      const [sightResults, foodResults, hotelResults, preferredPlace] = await Promise.all([
        textSearchPromise(service, {{
          query: `${{styleKeywords}} attractions in ${{locality}}`,
          location: center,
          radius: 12000,
        }}),
        textSearchPromise(service, {{
          query: `best local restaurants in ${{locality}}`,
          location: center,
          radius: 10000,
        }}),
        textSearchPromise(service, {{
          query: `boutique hotel in ${{locality}} city center`,
          location: center,
          radius: 8000,
        }}),
        searchPreferencePlace(service, profile, locality, center),
      ]);

      const preferredCategory = preferredPlace?.__preferredCategory || "";
      const sights = prioritizePlace(sightResults, preferredCategory === "sight" ? preferredPlace : null)
        .slice(0, Math.max(dayCount * 2, 6));
      const foods = prioritizePlace(foodResults, preferredCategory === "food" ? preferredPlace : null)
        .slice(0, Math.max(dayCount * 3, 6));
      const hotels = prioritizePlace(hotelResults, preferredCategory === "hotel" ? preferredPlace : null)
        .slice(0, 1);

      if (!sights.length) {{
        throw new Error(`No attractions found for ${{profile.destination}}.`);
      }}

      const dynamicPlan = {{
        destination: locality,
        country,
        tagLine: "Dynamic City Route",
        mapTitle: `${{titleCaseWords(locality)}} Dream Route`,
        heroNote: `为 ${{locality}} 动态生成的 ${{dayCount}} 天地图路线，偏好：${{profile.style}} / ${{profile.pace}}。`,
        mapConfig: {{
          center_lat: center.lat,
          center_lng: center.lng,
          zoom: 13,
          min_zoom: 11,
          max_zoom: 17,
        }},
        locations: {{}},
        dayPlans: [],
        transportStyles: baseTravelPlan.transportStyles,
      }};

      const hotelPlace = preferredCategory === "hotel" && preferredPlace ? preferredPlace : hotels[0] || sights[0];
      const hotelKey = `hotel-${{slugify(hotelPlace.name)}}`;
      dynamicPlan.locations[hotelKey] = placeToLocation(hotelPlace, "hotel", 0);

      for (let dayIndex = 0; dayIndex < dayCount; dayIndex += 1) {{
        const daySights = sights.slice(dayIndex * 2, dayIndex * 2 + 2);
        const dayFood = dayIndex === 0 && preferredCategory === "food" && preferredPlace
          ? preferredPlace
          : foods[dayIndex] || foods[dayIndex % Math.max(foods.length, 1)] || sights[dayIndex];
        const restaurantOptions = foods
          .slice(dayIndex * 3, dayIndex * 3 + 3)
          .map((place) => place.name);
        if (dayIndex === 0 && preferredCategory === "food" && preferredPlace && !restaurantOptions.includes(preferredPlace.name)) {{
          restaurantOptions.unshift(preferredPlace.name);
        }}
        if (!restaurantOptions.length && dayFood) {{
          restaurantOptions.push(dayFood.name);
        }}
        const dayStops = [hotelPlace, ...daySights];
        if (dayFood) {{
          dayStops.splice(Math.min(2, dayStops.length), 0, dayFood);
        }}

        const stopKeys = dayStops.map((place, index) => {{
          const category =
            place.name === hotelPlace.name && index === 0
              ? "hotel"
              : place.name === dayFood.name
                ? "food"
                : "sight";
          const key = `${{category}}-${{slugify(place.name)}}-${{dayIndex}}-${{index}}`;
          if (!dynamicPlan.locations[key]) {{
            dynamicPlan.locations[key] = placeToLocation(place, category, index);
          }}
          return key;
        }});

        const route = [];
        for (let i = 0; i < stopKeys.length - 1; i += 1) {{
          const start = dynamicPlan.locations[stopKeys[i]];
          const end = dynamicPlan.locations[stopKeys[i + 1]];
          const segment = profile.isRentalCar ? estimateCarSegment(start, end) : estimateSegment(start, end);
          if (segment.mode === "metro") {{
            const [startStation, endStation] = await Promise.all([
              findNearbyTransitStation(service, start),
              findNearbyTransitStation(service, end),
            ]);
            segment.startStation = startStation;
            segment.endStation = endStation;
          }}
          route.push({{
            from_stop: stopKeys[i],
            to_stop: stopKeys[i + 1],
            mode: segment.mode,
            emoji: segment.emoji,
            minutes: segment.minutes,
            tip: segment.tip,
            start_station: segment.startStation || null,
            end_station: segment.endStation || null,
          }});
        }}

        dynamicPlan.dayPlans.push({{
          day: `Day ${{dayIndex + 1}}`,
          title: buildShortDaySummary(dayStops, dayIndex),
          theme: `${{profile.style}} · ${{profile.pace}}`,
          dateHint: `${{dayCount}} 天行程中的第 ${{dayIndex + 1}} 天`,
          hotel: hotelPlace.name,
          summary: `围绕 ${{locality}} 动态检索出的景点与餐厅，按 ${{profile.budget}} 预算风格进行组合。`,
          restaurantOptions,
          stops: stopKeys,
          route,
        }});
      }}

      travelPlan = dynamicPlan;
      applyTransportPreferenceToPlan(travelPlan, profile);
      state.planSignature = signature;
      rebuildPlannerUI();
    }}

    function buildCurvedPath(projection, start, end) {{
      const p1 = projection.fromLatLngToDivPixel(start);
      const p2 = projection.fromLatLngToDivPixel(end);
      if (!p1 || !p2) return "";

      const mx = (p1.x + p2.x) / 2;
      const my = (p1.y + p2.y) / 2 - Math.max(24, Math.abs(p2.x - p1.x) * 0.12);
      return `M ${{p1.x}} ${{p1.y}} C ${{mx}} ${{p1.y - 12}}, ${{mx}} ${{p2.y + 12}}, ${{p2.x}} ${{p2.y}}`;
    }}

    function clearActivePolylines() {{
      state.activeRoutePolylines.forEach((line) => line.setMap(null));
      state.activeRoutePolylines = [];
      if (state.routeOverlay) state.routeOverlay.clearPaths();
    }}

    function updateVisibleMarkers(dayPlan) {{
      const activeStops = new Set(dayPlan.stops);
      state.markerElements.forEach((el, key) => {{
        el.style.display = activeStops.has(key) ? "block" : "none";
      }});
    }}

    function updateMapForDay(dayPlan, fitToDay = false) {{
      if (!state.map || !state.overlay || !state.routeOverlay) return;

      updateVisibleMarkers(dayPlan);
      clearActivePolylines();

      const bounds = new google.maps.LatLngBounds();
      const badgeData = [];
      const routeSegments = [];

      dayPlan.stops.forEach((stopKey) => {{
        const stop = travelPlan.locations[stopKey];
        bounds.extend(new google.maps.LatLng(stop.lat, stop.lng));
      }});
      state.activeDayBounds = bounds;

      dayPlan.route.forEach((segment) => {{
        const startStop = travelPlan.locations[segment.from_stop];
        const endStop = travelPlan.locations[segment.to_stop];
        const startLatLng = new google.maps.LatLng(startStop.lat, startStop.lng);
        const endLatLng = new google.maps.LatLng(endStop.lat, endStop.lng);
        const style = travelPlan.transportStyles[segment.mode] || {{
          color: "#9aa7b8",
          icons: "8,10",
          weight: 6,
        }};

        const line = new google.maps.Polyline({{
          map: state.map,
          path: [startLatLng, endLatLng],
          geodesic: false,
          strokeColor: style.color,
          strokeOpacity: 0.01,
          strokeWeight: style.weight,
          clickable: false,
        }});
        state.activeRoutePolylines.push(line);

        routeSegments.push({{
          startLatLng,
          endLatLng,
          style,
        }});

        badgeData.push({{
          emoji: segment.emoji,
          minutes: segment.minutes,
          startLatLng,
          endLatLng,
        }});
      }});

      state.routeOverlay.setBadgeData(badgeData);
      state.routeOverlay.setSegments(routeSegments);
      if (fitToDay) {{
        state.map.fitBounds(bounds, 90);
      }}
    }}

    function setActiveDay(index) {{
      state.activeDayIndex = index;
      const dayPlan = travelPlan.dayPlans[index];
      [...daySwitcher.children].forEach((chip, chipIndex) => {{
        chip.classList.toggle("active", chipIndex === index);
      }});
      renderTimeline(dayPlan);
      updateMapForDay(dayPlan, true);
    }}

    function toggleActiveDay(index) {{
      if (state.activeDayIndex === index) {{
        clearDaySelection();
        return;
      }}
      setActiveDay(index);
    }}

    function extractAreaLabelFromGeocode(result) {{
      const components = result.address_components || [];
      const preferredTypes = [
        "locality",
        "sublocality",
        "administrative_area_level_2",
        "administrative_area_level_1",
        "country",
      ];
      for (const type of preferredTypes) {{
        const match = components.find((component) => component.types.includes(type));
        if (match) return match.long_name;
      }}
      return result.formatted_address || "";
    }}

    function updateCurrentMapAreaName() {{
      if (!state.map || !window.google || !google.maps) return;
      window.clearTimeout(state.areaLookupTimer);
      state.areaLookupTimer = window.setTimeout(() => {{
        const center = state.map.getCenter();
        if (!center) return;
        const geocoder = new google.maps.Geocoder();
        geocoder.geocode({{ location: center }}, (results, status) => {{
          if (status === "OK" && results && results.length) {{
            const label = extractAreaLabelFromGeocode(results[0]);
            if (label) mapAreaName.textContent = label;
          }}
        }});
      }}, 450);
    }}

    async function loadGoogleMapsApi(apiKey) {{
      if (state.apiLoaded && state.activeApiKey === apiKey && window.google && window.google.maps) {{
        return;
      }}

      if (state.activeApiKey && state.activeApiKey !== apiKey) {{
        resetGoogleMapsLoader();
      }}

      await new Promise((resolve, reject) => {{
        const existing = document.querySelector('script[data-google-maps-loader="true"]');
        if (existing) {{
          if (state.apiLoaded && window.google && window.google.maps) {{
            resolve();
            return;
          }}
          existing.remove();
        }}

        state.activeApiKey = apiKey;

        let settled = false;
        let loadTimeoutId = null;
        const clearLoadTimeout = () => {{
          if (loadTimeoutId) {{
            window.clearTimeout(loadTimeoutId);
            loadTimeoutId = null;
          }}
        }};
        const cleanupFailedLoader = () => {{
          const failedScript = document.querySelector('script[data-google-maps-loader="true"]');
          if (failedScript) failedScript.remove();
          state.apiLoaded = false;
          state.activeApiKey = "";
          state.isLoadingMap = false;
        }};
        const finishResolve = () => {{
          if (settled) return;
          settled = true;
          clearLoadTimeout();
          state.apiLoaded = true;
          resolve();
        }};
        const finishReject = (error) => {{
          if (settled) return;
          settled = true;
          clearLoadTimeout();
          cleanupFailedLoader();
          reject(error);
        }};

        window.__initGoogleMapsForTravelGuide = () => {{
          setStatus("Google Maps 脚本已返回，正在初始化地图...");
          finishResolve();
        }};

        window.gm_authFailure = () => {{
          const error = new Error("InvalidKeyMapError: Google Maps authentication failed.");
          setStatus("Google Maps 鉴权失败");
          showMessage("Google Maps 加载失败", formatMapsError(error.message));
          cleanupFailedLoader();
          finishReject(error);
        }};

        const script = document.createElement("script");
        script.dataset.googleMapsLoader = "true";
        script.src = `https://maps.googleapis.com/maps/api/js?key=${{encodeURIComponent(apiKey)}}&libraries=places&v=weekly&loading=async&callback=__initGoogleMapsForTravelGuide`;
        script.async = true;
        script.defer = true;
        script.onerror = () => {{
          setStatus("Google Maps 脚本请求失败");
          finishReject(new Error("Google Maps script request failed."));
        }};
        document.head.appendChild(script);
        setStatus("已发出脚本请求，等待 Google 响应...");

        loadTimeoutId = window.setTimeout(() => {{
          if (!state.apiLoaded) {{
            setStatus("等待超时");
            finishReject(new Error("Google Maps load timed out. This often means the API key was rejected, the page origin is not allowed, or Maps JavaScript API/billing is not enabled."));
          }}
        }}, 12000);
      }});
    }}

    async function initMap() {{
      if (state.isLoadingMap) {{
        setStatus("正在加载中，请稍等...");
        return;
      }}

      const apiKey = embeddedApiKey.trim();
      if (!apiKey) {{
        setStatus("没有检测到 API Key");
        showMessage("还没有 API Key", "请在运行脚本前设置环境变量 <code>GOOGLE_MAPS_API_KEY</code>，再重新运行脚本生成页面。");
        return;
      }}

      if (window.location.protocol === "file:") {{
        showMessage("当前仍是 file:// 预览", "你现在仍然是从本地文件打开。即使 key 正确，Google Maps 也常因来源限制而拒绝加载。请改用 localhost 预览，再点一次“加载底图”。");
      }}

      showLoadingMapMessage();
      setButtonLoading(true);

      try {{
        await loadGoogleMapsApi(apiKey);
        if (state.tripProfile) {{
          await buildDynamicTravelPlan(state.tripProfile);
        }}
      }} catch (error) {{
        const body = formatMapsError(error && error.message ? error.message : "");
        showMessage("Google Maps 加载失败", body);
        setButtonLoading(false);
        return;
      }}

      if (!state.map) {{
        const overlayClasses = ensureOverlayClasses();
        state.map = new google.maps.Map(document.getElementById("map"), {{
          center: {{
            lat: travelPlan.mapConfig.center_lat,
            lng: travelPlan.mapConfig.center_lng,
          }},
          zoom: travelPlan.mapConfig.zoom,
          minZoom: travelPlan.mapConfig.min_zoom,
          maxZoom: travelPlan.mapConfig.max_zoom,
          mapTypeControl: false,
          streetViewControl: false,
          fullscreenControl: false,
          clickableIcons: false,
          gestureHandling: "greedy",
          styles: [
            {{ elementType: "geometry", stylers: [{{ color: "#f6ecdc" }}] }},
            {{ elementType: "labels.text.fill", stylers: [{{ color: "#7a6d63" }}] }},
            {{ elementType: "labels.text.stroke", stylers: [{{ color: "#fffaf4" }}] }},
            {{ featureType: "water", elementType: "geometry", stylers: [{{ color: "#cfe6ea" }}] }},
            {{ featureType: "poi.park", elementType: "geometry", stylers: [{{ color: "#dbead5" }}] }},
            {{ featureType: "road", elementType: "geometry", stylers: [{{ color: "#fff7ec" }}] }},
            {{ featureType: "road.highway", elementType: "geometry", stylers: [{{ color: "#efd7bf" }}] }},
          ],
        }});

        state.overlay = new overlayClasses.HtmlMarkerOverlay(state.map, travelPlan.locations);
        state.routeOverlay = new overlayClasses.RouteOverlay(state.map);

        state.map.addListener("zoom_changed", () => {{
          if (state.activeDayIndex !== null) updateMapForDay(travelPlan.dayPlans[state.activeDayIndex], false);
        }});
        state.map.addListener("dragend", () => {{
          if (state.activeDayIndex !== null) updateMapForDay(travelPlan.dayPlans[state.activeDayIndex], false);
          updateCurrentMapAreaName();
        }});
        state.map.addListener("idle", () => {{
          if (state.activeDayIndex !== null) updateMapForDay(travelPlan.dayPlans[state.activeDayIndex], false);
          updateCurrentMapAreaName();
        }});
      }}

      messageBox.classList.remove("visible");
      mapContainer.style.visibility = "visible";
      if (state.activeDayIndex !== null) {{
        setActiveDay(state.activeDayIndex);
      }} else {{
        clearDaySelection();
      }}
      setButtonLoading(false);
      setStatus("地图已加载完成");
      updateCurrentMapAreaName();
    }}

    tripForm.addEventListener("submit", (event) => {{
      event.preventDefault();
      enterPlanner(collectTripProfile());
    }});
    backToFormBtn.addEventListener("click", goBackToIntro);
    useDemoBtn.addEventListener("click", () => {{
      enterPlanner(collectTripProfile());
    }});
    languageToggle.addEventListener("click", () => {{
      languageInput.value = getLanguage() === "zh" ? "en" : "zh";
      applyLanguage();
      if (state.tripProfile) {{
        state.tripProfile.language = getLanguage();
        applyTripProfile(state.tripProfile);
      }}
    }});
    styleTrigger.addEventListener("click", (event) => {{
      if (event.target instanceof HTMLElement && event.target.dataset.removeStyle) {{
        const checkbox = getStyleCheckboxes().find((item) => item.value === event.target.dataset.removeStyle);
        if (checkbox) checkbox.checked = false;
        renderSelectedStyleChips();
        openStyleDropdown();
        return;
      }}
      openStyleDropdown();
      styleSearchInput.focus();
    }});
    styleSearchInput.addEventListener("input", (event) => {{
      filterStyleOptions(event.target.value);
      openStyleDropdown();
    }});
    styleDropdown.addEventListener("change", () => {{
      renderSelectedStyleChips();
      openStyleDropdown();
      styleSearchInput.focus();
    }});
    document.addEventListener("click", (event) => {{
      if (!styleMultiselect.contains(event.target)) {{
        closeStyleDropdown();
      }}
    }});

    createLegend();
    createDayChips();
    clearDaySelection();
    renderSelectedStyleChips();
    applyLanguage();
  </script>
</body>
</html>
"""


def write_outputs(base_dir: Path, plan: TravelPlan) -> None:
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)
    source_assets_dir = base_dir / "assets"
    output_assets_dir = output_dir / "assets"
    for loader_asset in (
        source_assets_dir / "travel-loader-globe.png",
        source_assets_dir / "travel-loader-globe.svg",
    ):
        if loader_asset.exists():
            output_assets_dir.mkdir(exist_ok=True)
            copy2(loader_asset, output_assets_dir / loader_asset.name)
    load_local_env(base_dir)
    plan_data = serialize_plan(plan)
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", DEFAULT_GOOGLE_MAPS_API_KEY).strip()
    html = render_html(plan_data, api_key)
    (output_dir / "index.html").write_text(html, encoding="utf-8")
    (output_dir / "barcelona_4day_visual_guide.html").write_text(html, encoding="utf-8")
    (output_dir / "barcelona_4day_visual_guide_v2.html").write_text(html, encoding="utf-8")
    (output_dir / "barcelona_4day_visual_guide_v3.html").write_text(html, encoding="utf-8")
    (output_dir / "barcelona_4day_data.json").write_text(
        json.dumps(plan_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


class QuietHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


def serve_preview(base_dir: Path, port: int = 8000) -> None:
    os.chdir(base_dir)
    server = ThreadingHTTPServer(("127.0.0.1", port), QuietHandler)
    html_path = "output/index.html"
    url = urljoin(f"http://127.0.0.1:{port}/", html_path)
    print(f"Preview server running at {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nPreview server stopped.")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate or preview the Barcelona travel guide.")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["generate", "serve"],
        default="generate",
        help="Use 'generate' to build output files or 'serve' to start a localhost preview.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the localhost preview server when using the 'serve' command.",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    plan = build_barcelona_plan()
    write_outputs(base_dir, plan)
    print("Generated output/index.html")
    if args.command == "serve":
        serve_preview(base_dir, args.port)


if __name__ == "__main__":
    main()
