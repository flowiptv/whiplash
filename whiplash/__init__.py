import json
import os
from copy import deepcopy

import pygame as pg

pg.init()
pg.font.init()
# initialize the joystick subsystem
pg.joystick.init()

# look for available gamepads/remotes and open them
joysticks = []
for i in range(pg.joystick.get_count()):
    j = pg.joystick.Joystick(i)
    j.init()  # this activates the gamepad!
    joysticks.append(j)
    print(f"gamepad/remote connected: {j.get_name()}")

# =========================================================
# CONFIG
# =========================================================
CONFIG_PATH = "/opt/flowtv/whiplash.json"

DEFAULT_CONFIG = {
    "theme": {
        "accent_color": [149, 66, 245],
        "background_color": [10, 10, 12],
        "panel_color": [25, 25, 28],
        "panel_alt_color": [35, 35, 38],
        "button_color": [45, 45, 50],
        "button_border": [100, 100, 105],
        "border_color": [60, 60, 65],
        "text_color": [240, 240, 240],
        "text_soft_color": [230, 230, 235],
        "muted_color": [140, 140, 150],
        "corner_roundness": 8,
        "focus_outline_width": 3,
        "animation_type": "ease_out",
        "animation_speed": 0.15,
        "sidebar_animation_speed": 0.12,
        "sidebar_width": 13,
    }
}

def deep_merge(base, override):
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base

def load_config(path=CONFIG_PATH):
    cfg = deepcopy(DEFAULT_CONFIG)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                deep_merge(cfg, loaded)
        except Exception as exc:
            print(f"config load failed: {exc}")
    else:
        save_config(cfg, path)
    return cfg

def save_config(cfg, path=CONFIG_PATH):
    try:
        dirpath = os.path.dirname(path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as exc:
        print(f"config save failed: {exc}")

def get_element_pointer(path):
    if not path:
        return None
        
    parts = path.split(":")
    layout_id = parts[0]
    
    # grab the root layout
    if layout_id not in layouts:
        return None
        
    current = layouts[layout_id]
    
    # traverse down the elements tree
    for part in parts[1:]:
        if not isinstance(current, dict) or "elements" not in current:
            return None
            
        found = None
        for child in current["elements"]:
            if child.get("id") == part:
                found = child
                break
                
        if found is None:
            return None
        current = found
        
    return current


# =========================================================
# CACHING SYSTEMS
# =========================================================
text_cache = {}
gradient_cache = {}
surface_cache = {}

def clear_caches():
    text_cache.clear()
    gradient_cache.clear()
    surface_cache.clear()

def render_text(font_obj, text, color):
    """caches rendered text surfaces to save massive cpu cycles!"""
    c_tuple = tuple(color) if isinstance(color, list) else color
    key = (id(font_obj), text, c_tuple)
    if key not in text_cache:
        text_cache[key] = font_obj.render(text, True, c_tuple)
    return text_cache[key]

def get_cached_surface(w, h, fill_color=None):
    """call this to reuse surface sheets instead of creating new frames!"""
    key = (w, h)
    if key not in surface_cache:
        surface_cache[key] = pg.Surface((w, h))
    surf = surface_cache[key]
    if fill_color:
        surf.fill(tuple(fill_color) if isinstance(fill_color, list) else fill_color)
    return surf

def draw_linear_gradient(surface, color1, color2, rect, orientation='vertical'):
    """draws a smooth linear gradient using caching for maximum speed!"""
    c1 = tuple(color1) if isinstance(color1, list) else color1
    c2 = tuple(color2) if isinstance(color2, list) else color2
    key = (c1, c2, rect.width, rect.height, orientation)
    
    if key not in gradient_cache:
        if orientation == 'vertical':
            grad_surf = pg.Surface((1, 2), pg.SRCALPHA)
        else:
            grad_surf = pg.Surface((2, 1), pg.SRCALPHA)
            
        grad_surf.set_at((0, 0), c1)
        if orientation == 'vertical':
            grad_surf.set_at((0, 1), c2)
        else:
            grad_surf.set_at((1, 0), c2)
            
        gradient_cache[key] = pg.transform.smoothscale(grad_surf, (rect.width, rect.height))
        
    surface.blit(gradient_cache[key], rect)


config = load_config()
theme = config["theme"]

def t(key, default=None):
    return theme.get(key, default)

# =========================================================
# ACTION CALLBACKS
# =========================================================
def play_movie(el): print(f"playing movie from button: {el.get('label')}! :3")
def open_settings(el):
    global activelayout,focus
    activelayout = "2"
    focus = "2:takeback"
def custom_card_action(el): print("clicked a whole focusable container card!")
def open_home(el):
    global activelayout,focus
    activelayout = "main"
    focus = "main"
def open_movies(el): sidebar_open()
def open_about(el): print("opening about page!")

def handle_search_submit(el):
    print(f"text input committed! current search query value is now: '{el.get('value')}'")

def handle_checkbox_toggle(el):
    print(f"checkbox element '{el.get('id')}' updated state to: {el.get('checked')}")


def sidebar_open():
    global focus
    open_sidebar()
    sidebar_focus = first_sidebar_focus()
    if sidebar_focus:
        focus = sidebar_focus

def set_layout(id):
    global activelayout,focus
    activelayout = id
    focus = id

action_map = {
    "play_media": play_movie,
    "open_settings": open_settings,
    "card_clicked": custom_card_action,
    "open_home": open_home,
    "open_movies": open_movies,
    "open_about": open_about,
}

# =========================================================
# LAYOUT
# =========================================================
layouts = {
    "main": {
        "id": "main",
        "type": "list",
        "direction": "horizontal",
        "height": 27,
        "width": 48,
        "stretch": False,
        "elements": [
            {
                "id": "content",
                "type": "list",
                "direction": "vertical",
                "height": 27,
                "width": 48,
                "stretch": False,
                "elements": [
                    {
                        "id": "top_bar",
                        "type": "list",
                        "direction": "horizontal",
                        "height": 4,
                        "width": 48,
                        "stretch": True,
                        "elements": [
                            {"id": "home_top", "type": "button", "label": "Home", "margin": 1, "action": open_home},
                            {"id": "enablesidebar", "type": "button", "label": "Sidebar", "margin": 1, "action": open_movies},
                            {"id": "changelayout", "type": "button", "label": "Change layout", "margin": 1, "action": open_settings},
                        ]
                    },
                    {
                        "id": "interactive_inputs",
                        "type": "list",
                        "direction": "horizontal",
                        "height": 5,
                        "width": 48,
                        "stretch": True,
                        "elements": [
                            {"id": "search_input", "type": "textinput", "label": "Search Media", "value": "", "placeholder": "Press Enter to type...", "margin": 1, "action": handle_search_submit},
                            {"id": "autoplay_toggle", "type": "checkbox", "label": "Autoplay Trailer Videos", "checked": True, "margin": 1, "action": handle_checkbox_toggle},
                        ]
                    },
                    {
                        "id": "scroll_box",
                        "type": "list",
                        "direction": "vertical",
                        "height": 13,
                        "width": 48,
                        "scroll": True,
                        "anim_speed": 0.15,
                        "elements": [
                            {"id": "img_item", "type": "button", "label": "Image Card fallback", "image": "assets/poster.png", "height": 5, "margin": 0.5, "action": play_movie},
                            {"id": "item1", "type": "button", "label": "Media Item #1", "height": 5, "margin": 0.5, "action": play_movie},
                            {"id": "item2", "type": "button", "label": "Media Item #2", "height": 5, "margin": 0.5, "action": play_movie}
                        ]
                    }
                ]
            }
        ]
    },
    "2": {
        "id": "2",
        "type": "list",
        "direction": "vertical",
        "height": 27,
        "width": 48,
        "stretch": False,
        "elements": [{"id": "label1", "type": "label", "label": "Hello, World! Layout 2!", "height": 4}, {"id": "takeback","type":"button","height": 4,"label": "take me back!","action":"open_home"}]
    }
}

# =========================================================
# SIDEBAR
# =========================================================
sidebar_items = [
    {"id": "home", "type": "button", "label": "home", "height": 3, "action": open_home},
    {"id": "movies", "type": "button", "label": "movies", "height": 3, "action": open_movies},
    {"id": "settings", "type": "button", "label": "settings", "height": 3, "action": open_settings},
    {"id": "about", "type": "button", "label": "about", "height": 3, "action": open_about},
]

# =========================================================
# RUNTIME STATE
# =========================================================
activelayout = "main"
focus = "main"
last_content_focus = focus
appName = "Whiplash Demo App"

screen = pg.display.set_mode((int(1920 / 2), int(1080 / 2)), pg.RESIZABLE)
clock = pg.time.Clock()
cell_w = screen.get_width() / 48
cell_h = screen.get_height() / 27

def get_font(size):
    try:
        try:
            return pg.font.Font("whiplash/font.ttf", int(size))
        except:
            return pg.font.Font("/opt/flowtv/font.ttf", int(size))
    except IOError:
        return pg.font.SysFont("Arial", int(size))

font = get_font(cell_h)
fontsm = get_font(cell_h / 2)
fontmed = get_font(cell_h / 1.25)
font_osk = get_font(cell_h)
font_osk_big = get_font(cell_h * 1.5)

layout_registry = {}
sidebar_registry = {}
scroll_states = {}
image_cache = {}

sidebar_state = {
    "open": False,
    "x": -float(t("sidebar_width", 10)),
    "tx": -float(t("sidebar_width", 10)),
}

focus_anim = {"x": 0, "y": 0, "w": 0, "h": 0, "tx": 0, "ty": 0, "tw": 0, "th": 0, "active": False}

# On-Screen Keyboard Configuration State
osk_state = {
    "target_active": False,
    "anim": 0.0,
    "target_el": None,
    "buffer": "",
    "cursor_pos": 0,
    "layer": "abc",
    "row": 0,
    "col": 0
}

OSK_LAYERS = {
    "abc": [
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
        ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
        ["a", "s", "d", "f", "g", "h", "j", "k", "l", "'"],
        ["z", "x", "c", "v", "b", "n", "m", ",", ".", "?"],
        ["ABC", "!@#", "<-", "__________", "__________", "__________", "->", "<--", "×", "✓"]
    ],
    "ABC": [
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
        ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", "'"],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "?"],
        ["abc", "!@#", "<-", "__________", "__________", "__________", "->", "<--", "×", "✓"]
    ],
    "!@#": [
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
        ["-", "_", "=", "+", "[", "]", "{", "}", ";", ":"],
        [".", ",", "/", "?", "\\", "|", "@", "#", "$", "%"],
        ["^", "&", "*", "(", ")", "!", "<", ">", "'", '"'],
        ["abc", "123", "<-", "__________", "__________", "__________", "->", "<--", "×", "✓"]
    ],
    "123": [
        ["1", "2", "3"],
        ["4", "5", "6"],
        ["7", "8", "9"],
        ["", "0", ""],
        ["abc", "!@#", "<-", "__________", "__________", "__________", "->", "<--", "×", "✓"]
    ],
}

# Image Asset Caching Handler Function
def get_cached_image(path, size):
    cache_key = (path, size)
    if cache_key in image_cache:
        return image_cache[cache_key]
    
    if os.path.exists(path):
        try:
            surface = pg.image.load(path).convert_alpha()
            scaled_surface = pg.transform.smoothscale(surface, size)
            image_cache[cache_key] = scaled_surface
            return scaled_surface
        except Exception as e:
            print(f"image loading failure: {e}")
    return None

# =========================================================
# ANIMATION
# =========================================================
def advance_anim(current, target, speed, anim_type="ease_out", steps=0):
    if abs(target - current) < 0.01:
        return target
    if anim_type == "ease_out":
        return current + (target - current) * speed
    if anim_type == "linear":
        step_amt = speed if steps == 0 else (target - current) / steps
        if target > current: return min(current + step_amt, target)
        return max(current - step_amt, target)
    return target

# =========================================================
# THEME DRAW HELPERS
# =========================================================
def clamp_radius(value, rect):
    if value <= 0: return 0
    return int(min(value, rect.width // 2, rect.height // 2))

def draw_rect(surface, color, rect, border=0, radius=None):
    r = clamp_radius(t("corner_roundness", 0), rect) if radius is None else radius
    pg.draw.rect(surface, color, rect, border, border_radius=r)

# =========================================================
# ACTIONS
# =========================================================
def run_action(el):
    if el.get("type") == "checkbox":
        el["checked"] = not el.get("checked", False)
        action = el.get("action")
        if callable(action): action(el)
        return
    elif el.get("type") == "textinput":
        open_osk(el)
        return

    action = el.get("action")
    if callable(action):
        action(el)
        return
    if isinstance(action, str) and action in action_map:
        action_map[action](el)
        return
    print(f"no action bound to {el.get('id', '<unknown>')}")

# =========================================================
# PATH RESOLUTION
# =========================================================
def get_element_by_path(path):
    parts = path.split(":")
    if not parts or parts[0] != activelayout:
        return None

    current = layouts.get(activelayout)
    for part in parts[1:]:
        if not current or "elements" not in current:
            return None
        found = None
        for child in current["elements"]:
            if child.get("id") == part:
                found = child
                break
        if found is None:
            return None
        current = found
    return current

def is_sidebar_path(path):
    return path.startswith("sidebar:")

# =========================================================
# SIDEBAR CONTROL
# =========================================================
def open_sidebar():
    sidebar_state["open"] = True
    sidebar_state["tx"] = 0.0

def close_sidebar():
    sidebar_state["open"] = False
    sidebar_state["tx"] = -float(t("sidebar_width", 10))

def first_sidebar_focus():
    for item in sidebar_items:
        if item.get("type") in ("button", "toggle", "slider", "checkbox", "textinput"):
            return f"sidebar:{item['id']}"
    return None

def content_items_from_registry(): return layout_registry
def sidebar_items_from_registry(): return sidebar_registry

# =========================================================
# FOCUS CONVERGENCE HELPERS
# =========================================================
def is_focusable_leaf(el):
    return el.get("type") in ("button", "toggle", "slider", "checkbox", "textinput") or el.get("focus")

def find_deepest_focusable(el, current_path):
    el_id = el.get("id", "")
    path = f"{current_path}:{el_id}" if current_path else el_id
    if is_focusable_leaf(el): return path
    for child in el.get("elements", []):
        leaf_path = find_deepest_focusable(child, path)
        if leaf_path: return leaf_path
    return None

# =========================================================
# FOCUS / NAVIGATION
# =========================================================
def handle_layout_input(direction):
    global focus, last_content_focus

    if is_sidebar_path(focus):
        reg = sidebar_items_from_registry()
        if direction in ("left", "right"):
            focus = last_content_focus if last_content_focus in layout_registry else next(iter(layout_registry), last_content_focus)
            close_sidebar()
            return
        if not reg or focus not in reg: return

        curr_x, curr_y, curr_w, curr_h = reg[focus]
        best_target, min_dist = None, float("inf")
        for path, (tx, ty, tw, th) in reg.items():
            if path == focus: continue
            dx = (tx + tw / 2) - (curr_x + curr_w / 2)
            node_dy = (ty + th / 2) - (curr_y + curr_h / 2)
            if direction == "up" and node_dy >= -0.01: continue
            if direction == "down" and node_dy <= 0.01: continue
            dist = dx**2 + (node_dy**2 * 500) if direction in ("left", "right") else (dx**2 * 500) + node_dy**2
            if dist < min_dist:
                min_dist = dist
                best_target = path
        if best_target: focus = best_target
        return

    reg = content_items_from_registry()
    if not reg or focus not in reg:
        if reg:
            focus = next(iter(reg))
            last_content_focus = focus
        return

    curr_x, curr_y, curr_w, curr_h = reg[focus]
    best_target, min_dist = None, float("inf")

    for path, (tx, ty, tw, th) in reg.items():
        if path == focus: continue
        dx = (tx + tw / 2) - (curr_x + curr_w / 2)
        node_dy = (ty + th / 2) - (curr_y + curr_h / 2)

        if direction == "up" and node_dy >= -0.01: continue
        if direction == "down" and node_dy <= 0.01: continue
        if direction == "left" and dx >= -0.01: continue
        if direction == "right" and dx <= 0.01: continue

        dist = dx**2 + (node_dy**2 * 500) if direction in ("left", "right") else (dx**2 * 500) + node_dy**2
        if dist < min_dist:
            min_dist = dist
            best_target = path

    if best_target:
        focus = best_target
        last_content_focus = focus
        return

    if direction == "left" and not sidebar_state["open"]:
        open_sidebar()
        sidebar_focus = first_sidebar_focus()
        if sidebar_focus: focus = sidebar_focus
        return

def handle_focus_memory():
    global last_content_focus, focus
    if not is_sidebar_path(focus):
        if focus in layout_registry:
            last_content_focus = focus
        elif layout_registry:
            el = get_element_by_path(focus)
            if el:
                deep_leaf = find_deepest_focusable(el, ":".join(focus.split(":")[:-1]))
                if deep_leaf and deep_leaf in layout_registry:
                    focus = deep_leaf
                    last_content_focus = focus
        if sidebar_state["open"]: close_sidebar()

# =========================================================
# TV ON-SCREEN KEYBOARD LOGIC
# =========================================================
def open_osk(element):
    osk_state["target_active"] = True
    osk_state["target_el"] = element
    osk_state["buffer"] = element.get("value", "")
    osk_state["cursor_pos"] = len(osk_state["buffer"])
    osk_state["layer"] = "abc"
    osk_state["row"] = 0
    osk_state["col"] = 0

def handle_osk_input(direction):
    grid = OSK_LAYERS[osk_state["layer"]]
    r, c = osk_state["row"], osk_state["col"]
    orig_r, orig_c = r, c

    if direction == "right":
        current_key = grid[r][c]
        while True:
            c = (c + 1) % len(grid[r])
            if grid[r][c] != current_key and grid[r][c] != "":
                while c > 0 and grid[r][c] == grid[r][c - 1]:
                    c -= 1
                break
            if c == orig_c:
                break
    elif direction == "left":
        while c > 0 and grid[r][c] == grid[r][c - 1]:
            c -= 1
        current_key = grid[r][c]
        while True:
            c = (c - 1) % len(grid[r])
            if grid[r][c] != current_key and grid[r][c] != "":
                while c > 0 and grid[r][c] == grid[r][c - 1]:
                    c -= 1
                break
            if c == orig_c:
                break
    elif direction in ("up", "down"):
        if direction == "up": r = (r - 1) % len(grid)
        else: r = (r + 1) % len(grid)
        
        if c >= len(grid[r]): c = len(grid[r]) - 1
        if grid[r][c] == "":
            while c > 0 and grid[r][c] == "":
                c -= 1
        while c > 0 and grid[r][c] == grid[r][c - 1]:
            c -= 1

    osk_state["row"], osk_state["col"] = r, c

def select_osk_key():
    grid = OSK_LAYERS[osk_state["layer"]]
    key = grid[osk_state["row"]][osk_state["col"]]

    if key in ("abc", "ABC", "!@#", "123"):
        osk_state["layer"] = key
        if osk_state["row"] >= len(OSK_LAYERS[key]):
            osk_state["row"] = len(OSK_LAYERS[key]) - 1
        return

    if key == "✓":
        osk_state["target_el"]["value"] = osk_state["buffer"]
        osk_state["target_active"] = False
        action = osk_state["target_el"].get("action")
        if callable(action): action(osk_state["target_el"])
    elif key == "×":
        osk_state["target_active"] = False
    elif key == "<-":
        osk_state["cursor_pos"] = max(0, osk_state["cursor_pos"] - 1)
    elif key == "->":
        osk_state["cursor_pos"] = min(len(osk_state["buffer"]), osk_state["cursor_pos"] + 1)
    elif key == "<--":
        pos = osk_state["cursor_pos"]
        if pos > 0:
            osk_state["buffer"] = osk_state["buffer"][:pos - 1] + osk_state["buffer"][pos:]
            osk_state["cursor_pos"] -= 1
    elif key == "__________":
        pos = osk_state["cursor_pos"]
        osk_state["buffer"] = osk_state["buffer"][:pos] + " " + osk_state["buffer"][pos:]
        osk_state["cursor_pos"] += 1
    elif key == "":
        pass
    else:
        pos = osk_state["cursor_pos"]
        osk_state["buffer"] = osk_state["buffer"][:pos] + key + osk_state["buffer"][pos:]
        osk_state["cursor_pos"] += 1

def render_osk():
    if osk_state["anim"] <= 0.001:
        return

    overlay = pg.Surface((screen.get_width(), screen.get_height()), pg.SRCALPHA)
    overlay.fill((10, 10, 12, int(220 * osk_state["anim"])))
    screen.blit(overlay, (0, 0))

    grid = OSK_LAYERS[osk_state["layer"]]
    box_w, box_h = int(32 * cell_w), int(16 * cell_h)
    box_x = (screen.get_width() - box_w) // 2
    
    target_center_y = (screen.get_height() - box_h) // 2
    hidden_y = screen.get_height()
    box_y = int(hidden_y + (target_center_y - hidden_y) * osk_state["anim"])

    box_rect = pg.Rect(box_x, box_y, box_w, box_h)
    draw_rect(screen, t("panel_color"), box_rect, 0)
    draw_rect(screen, t("border_color"), box_rect, 2)

    title_surf = render_text(fontsm, f"Input: {osk_state['target_el'].get('label', 'Text Field')}", t("muted_color"))
    screen.blit(title_surf, (box_x + 20, box_y + 12))

    input_bar_h = int(1.8 * cell_h)
    input_bar_rect = pg.Rect(box_x + 20, box_y + int(1.2 * cell_h), box_w - 40, input_bar_h)
    draw_rect(screen, t("button_color"), input_bar_rect, 0)
    draw_rect(screen, t("button_border"), input_bar_rect, 1)

    text_clip_w = input_bar_rect.width - 20
    text_clip_h = input_bar_rect.height
    text_surface = get_cached_surface(text_clip_w, text_clip_h)
    text_surface.fill((0,0,0,0)) # transparent fill for osk buffer block
    text_surface.set_colorkey((0,0,0)) # quick chroma clear

    text_val_surf = render_text(font, osk_state["buffer"], t("text_color"))
    prefix_string = osk_state["buffer"][:osk_state["cursor_pos"]]
    prefix_w = font.size(prefix_string)[0]

    text_offset_x = 0
    if prefix_w > text_clip_w - 30:
        text_offset_x = (text_clip_w - 30) - prefix_w

    text_y_pos = text_clip_h // 2 - text_val_surf.get_height() // 2
    text_surface.blit(text_val_surf, (text_offset_x, text_y_pos))

    cursor_x = text_offset_x + prefix_w
    cursor_rect = pg.Rect(cursor_x, text_clip_h // 2 - font.get_height() // 2, 2, font.get_height())
    
    if (pg.time.get_ticks() // 400) % 2 == 0:
        pg.draw.rect(text_surface, t("text_color"), cursor_rect)
    else:
        pg.draw.rect(text_surface, t("muted_color"), cursor_rect)

    screen.blit(text_surface, (input_bar_rect.left + 10, input_bar_rect.top))

    start_keys_y = input_bar_rect.bottom + int(0.5 * cell_h)
    row_h = int(2.2 * cell_h)

    for r_idx, row in enumerate(grid):
        total_keys = len(row)
        avail_w = box_w - 40
        key_w_float = avail_w / total_keys

        visited_cols = set()
        for c_idx, key in enumerate(row):
            if c_idx in visited_cols: continue

            span = 1
            while c_idx + span < total_keys and row[c_idx + span] == key:
                span += 1

            for s in range(span): visited_cols.add(c_idx + s)

            kx = box_x + 20 + int(c_idx * key_w_float)
            kx_next = box_x + 20 + int((c_idx + span) * key_w_float)
            ky = start_keys_y + (r_idx * row_h)
            
            k_rect = pg.Rect(kx, ky, (kx_next - kx) - 4, row_h - 4)

            is_key_focused = False
            if osk_state["row"] == r_idx:
                for s in range(span):
                    if osk_state["col"] == c_idx + s:
                        is_key_focused = True
                        break
                        
            if key != "": 
                bg_col = t("accent_color") if is_key_focused else t("button_color")
                draw_rect(screen, bg_col, k_rect, 0)
                if not is_key_focused:
                    draw_rect(screen, t("button_border"), k_rect, 1)
                    
            if key != "×":
                key_surf = render_text(font_osk, key, t("text_color"))
                screen.blit(key_surf, key_surf.get_rect(center=k_rect.center))
            else:
                key_surf = render_text(font_osk_big, key, t("text_color"))
                screen.blit(key_surf, key_surf.get_rect(center=k_rect.center))

# =========================================================
# RENDERING (UPDATED WITH FRUSTUM VIEWPORT CULLING!)
# =========================================================
def render_gui(element, x=0, y=0, parent_w=48, parent_h=27, current_path="", target_surf=None, gx=0, gy=0, selectable=True):
    global layout_registry, scroll_states, focus_anim
    if target_surf is None: target_surf = screen

    el_id = element.get("id", "")
    current_path = f"{current_path}:{el_id}" if current_path else el_id

    margin = element.get("margin", 0)
    local_x = x + margin
    local_y = y + margin
    w = element.get("width", parent_w) - (margin * 2)
    h = element.get("height", parent_h) - (margin * 2)

    rect = pg.Rect(int(local_x * cell_w), int(local_y * cell_h), int(w * cell_w), int(h * cell_h))
    el_type = element.get("type", "list")
    is_focused = (focus == current_path)

    # clipping check: is the container bounding box actually visible inside its current surface frame?
    surf_w, surf_h = target_surf.get_size()
    is_visible = rect.right > 0 and rect.left < surf_w and rect.bottom > 0 and rect.top < surf_h

    if is_focused and selectable and not osk_state["target_active"]:
        focus_anim["active"] = True
        focus_anim["tx"] = int((gx + local_x) * cell_w)
        focus_anim["ty"] = int((gy + local_y) * cell_h)
        focus_anim["tw"] = int(w * cell_w)
        focus_anim["th"] = int(h * cell_h)

    if is_focusable_leaf(element):
        if selectable: layout_registry[current_path] = (gx + local_x, gy + local_y, w, h)
        
        # cull draw calls if the item is outside the viewport clip box!
        if is_visible:
            draw_rect(target_surf, t("button_color"), rect, 0)
            draw_rect(target_surf, t("button_border"), rect, 1)

            if el_type == "button":
                image_drawn = False
                if "image" in element:
                    img_size = (int(rect.width - 12), int(rect.height - 12))
                    if img_size[0] > 0 and img_size[1] > 0:
                        img_surf = get_cached_image(element["image"], img_size)
                        if img_surf:
                            target_surf.blit(img_surf, img_surf.get_rect(center=rect.center))
                            image_drawn = True

                if not image_drawn and "label" in element:
                    text_surf = render_text(font, element["label"], t("text_color"))
                    target_surf.blit(text_surf, text_surf.get_rect(center=rect.center))
                
            elif el_type == "checkbox":
                text_surf = render_text(font, element.get("label", ""), t("text_color"))
                target_surf.blit(text_surf, text_surf.get_rect(left=rect.left + 15, centery=rect.centery))
                
                box_sz = int(rect.height * 0.45)
                box_rect = pg.Rect(rect.right - box_sz - 15, rect.centery - box_sz // 2, box_sz, box_sz)
                draw_rect(target_surf, t("panel_color"), box_rect, 0, radius=4)
                draw_rect(target_surf, t("border_color"), box_rect, 1, radius=4)
                
                if element.get("checked", False):
                    inner_sz = box_sz - 6
                    draw_rect(target_surf, t("accent_color"), pg.Rect(box_rect.left + 3, box_rect.top + 3, inner_sz, inner_sz), 0, radius=2)

            elif el_type == "textinput":
                lbl_surf = render_text(fontmed, element.get("label", ""), t("muted_color"))
                target_surf.blit(lbl_surf, (rect.left + 12, rect.top + 4))
                
                val_string = element.get("value", "")
                display_color = t("text_color") if val_string else t("muted_color")
                if not val_string: 
                    val_string = element.get("placeholder", "")
                    
                clip_w = rect.width - 24
                clip_h = font.get_height() + 4
                input_text_surface = get_cached_surface(clip_w, clip_h)
                input_text_surface.fill((0,0,0,0))
                input_text_surface.set_colorkey((0,0,0))
                
                val_surf = render_text(font, val_string, display_color)
                
                if osk_state["target_active"] and osk_state["target_el"] == element:
                    prefix_string = osk_state["buffer"][:osk_state["cursor_pos"]]
                    prefix_w = font.size(prefix_string)[0]
                else:
                    prefix_w = val_surf.get_width()

                text_offset_x = 0
                if prefix_w > clip_w - 10:
                    text_offset_x = (clip_w - 10) - prefix_w
                    
                input_text_surface.blit(val_surf, (text_offset_x, 0))
                target_surf.blit(input_text_surface, (rect.left + 12, rect.bottom - clip_h - 12))
        return

    if el_type in ("image", "label", "progress"):
        if is_visible:
            if el_type == "label" and "label" in element:
                f = fontsm if "small" in element else font
                text_surf = render_text(f, element["label"], t("text_soft_color"))
                target_surf.blit(text_surf, text_surf.get_rect(left=rect.left + 6, centery=rect.centery))
            elif el_type == "progress":
                draw_rect(target_surf, t("panel_color"), rect, 0)
                draw_rect(target_surf, t("border_color"), rect, 1)
                value = float(element.get("value", 0))
                maximum = float(element.get("max", 100))
                fraction = max(0.0, min(1.0, value / maximum if maximum else 0.0))
                
                pad = int(element.get("padding", 2))
                inner = rect.inflate(-pad * 2, -pad * 2)
                fill_w = int(inner.width * fraction)
                if fill_w > 0 and inner.height > 0:
                    draw_rect(target_surf, t("accent_color"), pg.Rect(inner.left, inner.top, fill_w, inner.height), 0)
        return

    if is_visible:
        if not (el_id == activelayout or (rect.topleft == (0,0) and rect.bottomright == (screen.get_width(),screen.get_height()))):
            draw_rect(target_surf, t("panel_color"), rect, 0)
            draw_rect(target_surf, t("border_color"), rect, 1)
        else:
            draw_rect(target_surf, t("panel_color"), rect, 0, 0)

    padding = element.get("padding", 0)
    content_x, content_y = local_x + padding, local_y + padding
    content_w, content_h = w - (padding * 2), h - (padding * 2)
    child_list = element.get("elements", [])

    if child_list:
        is_vertical = element.get("direction") == "vertical"

        if el_type == "scatter":
            for child in child_list:
                render_gui(child, content_x + child.get("x", 0), content_y + child.get("y", 0), child.get("width", 5), child.get("height", 5), current_path, target_surf, gx, gy, selectable)

        elif element.get("scroll", False):
            if el_id not in scroll_states: scroll_states[el_id] = {"current": 0.0, "target": 0.0}
            running_y = 0
            focused_child_y, focused_child_h = None, None
            child_layouts = []

            for child in child_list:
                c_w = content_w if is_vertical else content_w / len(child_list)
                c_h = child.get("height", content_h) if is_vertical else content_h
                if focus.startswith(f"{current_path}:{child.get('id')}"):
                    focused_child_y, focused_child_h = running_y, c_h
                child_layouts.append((child, c_w, c_h, running_y))
                if is_vertical: running_y += c_h

            if focused_child_y is not None:
                t_scroll = scroll_states[el_id]["target"]
                if focused_child_y < t_scroll: scroll_states[el_id]["target"] = focused_child_y
                elif focused_child_y + focused_child_h > t_scroll + content_h:
                    scroll_states[el_id]["target"] = (focused_child_y + focused_child_h) - content_h

            scroll_states[el_id]["current"] = advance_anim(scroll_states[el_id]["current"], scroll_states[el_id]["target"], element.get("anim_speed", t("animation_speed", 0.25)), element.get("anim_type", t("animation_type", "ease_out")), 0)
            
            cw, ch = max(1, int(content_w * cell_w)), max(1, int(content_h * cell_h))
            clip_surface = get_cached_surface(cw, ch, t("panel_color"))

            for child, child_w, child_h, relative_y in child_layouts:
                # children calculate positions relative to the scroll clip sheet surface
                render_gui(child, 0, relative_y - scroll_states[el_id]["current"], child_w, child_h, current_path, clip_surface, gx + content_x, gy + content_y, selectable)
            
            if is_visible:
                target_surf.blit(clip_surface, (int(content_x * cell_w), int(content_y * cell_h)))

        else:
            cursor_x, cursor_y = content_x, content_y
            is_stretched = element.get("stretch", False)
            for child in child_list:
                c_w = content_w if is_vertical else (content_w / len(child_list) if is_stretched else child.get("width", content_w))
                c_h = content_h if not is_vertical else (content_h / len(child_list) if is_stretched else child.get("height", content_h))
                render_gui(child, cursor_x, cursor_y, c_w, c_h, current_path, target_surf, gx, gy, selectable)
                if is_vertical: cursor_y += c_h
                else: cursor_x += c_w

def render_sidebar():
    global sidebar_registry, focus_anim

    sidebar_w = float(t("sidebar_width", 10))
    sidebar_state["x"] = advance_anim(sidebar_state["x"], sidebar_state["tx"], float(t("sidebar_animation_speed", 0.22)), t("animation_type", "ease_out"), 0)

    x_cell = sidebar_state["x"]
    if x_cell <= -sidebar_w + 0.05 and not sidebar_state["open"]: return

    sidebar_registry = {}
    sidebar_rect = pg.Rect(int(x_cell * cell_w), 0, int(sidebar_w * cell_w), screen.get_height())
    draw_rect(screen, t("panel_color"), sidebar_rect, 0)
    draw_rect(screen, t("border_color"), sidebar_rect, 1)

    header_rect = pg.Rect(sidebar_rect.left, sidebar_rect.top, sidebar_rect.width, int(3 * cell_h))
    header_text = render_text(font, appName, t("accent_color"))
    screen.blit(header_text, header_text.get_rect(center=header_rect.center))

    item_start_y, item_h, item_gap = 4.0, 3.0, 0.5
    for idx, item in enumerate(sidebar_items):
        item_y = item_start_y + idx * (item_h + item_gap)
        item_rect = pg.Rect(int((x_cell + 0.5) * cell_w), int(item_y * cell_h), int((sidebar_w - 1.0) * cell_w), int(item_h * cell_h))

        path = f"sidebar:{item['id']}"
        sidebar_registry[path] = (x_cell + 0.5, item_y, sidebar_w - 1.0, item_h)

        is_focused = (focus == path)
        fill = t("panel_alt_color") if is_focused else t("button_color")
        border = t("accent_color") if is_focused else t("button_border")

        if is_focused and not osk_state["target_active"]:
            focus_anim["active"] = True
            focus_anim["tx"] = item_rect.left
            focus_anim["ty"] = item_rect.top
            focus_anim["tw"] = item_rect.width
            focus_anim["th"] = item_rect.height

        draw_rect(screen, fill, item_rect, 0)
        draw_rect(screen, border, item_rect, 1)
        label = render_text(font, item["label"], t("text_color"))
        screen.blit(label, label.get_rect(center=item_rect.center))

def set_layouts(setlayouts):
    global layouts
    layouts = setlayouts

def set_sidebar_items(items):
    global sidebar_items
    sidebar_items = items

def set_appname(name):
    global appName
    appName = name

def check_mouse_hover_and_click(click_event=False):
    global focus, last_content_focus
    mx, my = pg.mouse.get_pos()

    if sidebar_state["open"]:
        sidebar_w = float(t("sidebar_width", 10))
        if mx <= int(sidebar_w * cell_w):
            for path, (bx, by, bw, bh) in sidebar_registry.items():
                rect = pg.Rect(int(bx * cell_w), int(by * cell_h), int(bw * cell_w), int(bh * cell_h))
                if rect.collidepoint(mx, my):
                    focus = path
                    if click_event:
                        for item in sidebar_items:
                            if focus == f"sidebar:{item['id']}":
                                run_action(item)
                                return True
                    return True
            return False

    for path, (bx, by, bw, bh) in layout_registry.items():
        rect = pg.Rect(int(bx * cell_w), int(by * cell_h), int(bw * cell_w), int(bh * cell_h))
        if rect.collidepoint(mx, my):
            focus = path
            last_content_focus = focus
            if click_event:
                el = get_element_by_path(focus)
                if el:
                    run_action(el)
                    return True
            return True
            
    return False

def check_osk_mouse(click_event=False):
    if not osk_state["target_active"] or osk_state["anim"] < 0.95:
        return False

    mx, my = pg.mouse.get_pos()
    grid = OSK_LAYERS[osk_state["layer"]]
    box_w, box_h = int(32 * cell_w), int(16 * cell_h)
    box_x = (screen.get_width() - box_w) // 2
    target_center_y = (screen.get_height() - box_h) // 2
    box_y = target_center_y

    input_bar_h = int(1.8 * cell_h)
    start_keys_y = box_y + int(1.2 * cell_h) + input_bar_h + int(0.5 * cell_h)
    row_h = int(2.2 * cell_h)

    for r_idx, row in enumerate(grid):
        total_keys = len(row)
        avail_w = box_w - 40

        for c_idx, key in enumerate(row):
            key_w_float = avail_w / total_keys
            kx = box_x + 20 + int(c_idx * key_w_float)
            kx_next = box_x + 20 + int((c_idx + 1) * key_w_float)
            ky = start_keys_y + (r_idx * row_h)
            k_rect = pg.Rect(kx, ky, (kx_next - kx) - 4, row_h - 4)

            if k_rect.collidepoint(mx, my) and key != "":
                osk_state["row"], osk_state["col"] = r_idx, c_idx
                if click_event:
                    select_osk_key()
                return True
    return False

# =========================================================
# MAIN LOOP
# =========================================================
mposx = 40000
def lerptuple(a, b, t):
    return tuple(start + t * (end - start) for start, end in zip(a, b))

def mainloop():
    global focus, focus_anim, cell_w, cell_h, mposx
    grad_fade = 0
    prev_pos = (4000,4000)
    ti = 400
    running = True
    focus_anim = {"x": 0, "y": 0, "w": 0, "h": 0, "tx": 0, "ty": 0, "tw": 0, "th": 0, "active": False}
    
    try:
        cursor_surface = pg.image.load("whiplash/pointer.png").convert_alpha()
    except:
        cursor_surface = pg.image.load("/opt/flowtv/pointer.png").convert_alpha()
        
    pg.mouse.set_visible(False)
    
    while running:
        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                running = False
                
            action = None
            is_back_action = False

            if ev.type == pg.KEYDOWN:
                if ev.key == pg.K_ESCAPE:    is_back_action = True
                elif ev.key == pg.K_UP:      action = "up"
                elif ev.key == pg.K_DOWN:    action = "down"
                elif ev.key == pg.K_LEFT:    action = "left"
                elif ev.key == pg.K_RIGHT:   action = "right"
                elif ev.key == pg.K_RETURN:  action = "select"

            elif ev.type == pg.JOYBUTTONDOWN:
                if ev.button == 0:    action = "select"
                elif ev.button == 1:  is_back_action = True

            elif ev.type == pg.JOYHATMOTION:
                if ev.value == (0, 1):    action = "up"
                elif ev.value == (0, -1): action = "down"
                elif ev.value == (-1, 0): action = "left"
                elif ev.value == (1, 0):  action = "right"

            if is_back_action:
                if osk_state["target_active"]: 
                    osk_state["target_active"] = False
                else: 
                    if sidebar_state["open"] == True:
                        close_sidebar()
                        focus = activelayout
                    else:
                        if appName != "FlowTV": 
                            running = False

            elif action:
                if osk_state["target_active"]:
                    if action == "select": 
                        select_osk_key()
                    else: 
                        handle_osk_input(action)
                else:
                    if action == "select":
                        if is_sidebar_path(focus):
                            for item in sidebar_items:
                                if focus == f"sidebar:{item['id']}":
                                    run_action(item)
                                    break
                        else:
                            el = get_element_by_path(focus)
                            if el: run_action(el)
                    else:
                        handle_layout_input(action)

            elif ev.type == pg.VIDEORESIZE:
                global font, fontsm, font_osk, font_osk_big, fontmed
                print("Recompiling fonts and clearing caches.")
                cell_w = screen.get_width() / 48
                cell_h = screen.get_height() / 27
                font = get_font(cell_h)
                fontsm = get_font(cell_h / 2)
                font_osk = get_font(cell_h)
                font_osk_big = get_font(cell_h * 1.5)
                fontmed = get_font(cell_h / 1.5)
                clear_caches()

            elif ev.type == pg.MOUSEMOTION:
                mposx = pg.mouse.get_pos()[0]
                if osk_state["target_active"]:
                    check_osk_mouse(click_event=False)
                else:
                    check_mouse_hover_and_click(click_event=False)
                ti = 0

            elif ev.type == pg.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    if osk_state["target_active"]:
                        check_osk_mouse(click_event=True)
                    else:
                        check_mouse_hover_and_click(click_event=True)
                        
        if not osk_state["target_active"]:
            handle_focus_memory()

        osk_state["anim"] = advance_anim(osk_state["anim"], 1.0 if osk_state["target_active"] else 0.0, 0.18)

        screen.fill(tuple(t("background_color")))
        layout_registry.clear()
        focus_anim["active"] = False

        render_gui(layouts[activelayout])
        render_sidebar()
        render_osk()
        
        if mposx < cell_w*3 and not sidebar_state["open"]:
            grad_fade = grad_fade + (255 - grad_fade) * 0.1
            if mposx < cell_w:
                sidebar_open()
        else:
            grad_fade = grad_fade + (- grad_fade) * 0.1
            
        draw_linear_gradient(screen, tuple(t("accent_color")) + (int(grad_fade),), tuple(t("accent_color")) + (0,), pg.Rect(0,0,cell_w*4,screen.get_height()), 'horizontal')

        if focus_anim["active"] and not osk_state["target_active"]:
            focus_anim["x"] = advance_anim(focus_anim["x"], focus_anim["tx"], float(t("animation_speed", 0.25)), t("animation_type", "ease_out"))
            focus_anim["y"] = advance_anim(focus_anim["y"], focus_anim["ty"], float(t("animation_speed", 0.25)), t("animation_type", "ease_out"))
            focus_anim["w"] = advance_anim(focus_anim["w"], focus_anim["tw"], float(t("animation_speed", 0.25)), t("animation_type", "ease_out"))
            focus_anim["h"] = advance_anim(focus_anim["h"], focus_anim["th"], float(t("animation_speed", 0.25)), t("animation_type", "ease_out"))

            highlight_rect = pg.Rect(int(focus_anim["x"]), int(focus_anim["y"]), int(focus_anim["w"]), int(focus_anim["h"]))
            pg.draw.rect(
                screen,
                tuple(t("accent_color")),
                highlight_rect,
                int(t("focus_outline_width", 3)),
                border_radius=clamp_radius(t("corner_roundness", 8), highlight_rect),
            )
            
        prev_pos = lerptuple(prev_pos, pg.mouse.get_pos(), .5)
        if ti < 5:
            screen.blit(cursor_surface, prev_pos)
        ti = ti + (clock.get_time() / 1000.0)
        
        pg.display.update()
        clock.tick(60)
        pg.display.set_caption("Whiplash | FPS: "+str(clock.get_fps()))
        
    save_config(config, CONFIG_PATH)
    pg.quit()

if __name__ == "__main__":
    mainloop()