import json
import os
from copy import deepcopy

import pygame as pg

pg.init()
pg.font.init()


# =========================================================
# CONFIG
# =========================================================
CONFIG_PATH = "whiplash.json"

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
        "animation_speed": 0.25,
        "sidebar_animation_speed": 0.22,
        "sidebar_width": 10,
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
# legacy fallback for older layouts that still use string actions
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
                        "id": "absolute_zone",
                        "type": "scatter",
                        "height": 8,
                        "width": 48,
                        "margin": 1,
                        "focus": True,
                        "elements": [
                            {"id": "float1", "type": "progress", "x": 1, "y": 1, "width": 10, "height": 2, "value": 50, "max": 100},
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
                            {"id": "item1", "type": "button", "label": "Media Item #1", "height": 5, "margin": 0.5, "action": play_movie},
                            {"id": "item2", "type": "button", "label": "Media Item #2", "height": 5, "margin": 0.5, "action": play_movie},
                            {"id": "item3", "type": "button", "label": "Media Item #3", "height": 5, "margin": 0.5, "action": play_movie}
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
# SIDEBAR (NOT PART OF LAYOUT)
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
focus = "main"  # started on a leaf element instead of a container
last_content_focus = focus

screen = pg.display.set_mode((int(1920 / 2), int(1080 / 2)))
clock = pg.time.Clock()
cell_w = screen.get_width() / 48
cell_h = screen.get_height() / 27
font = pg.font.Font("whiplash/font.ttf", int(cell_h))
fontsm = pg.font.Font("whiplash/font.ttf", int(cell_h/2))

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
        if target > current:
            return min(current + step_amt, target)
        return max(current - step_amt, target)
    return target

# =========================================================
# THEME DRAW HELPERS
# =========================================================
def clamp_radius(value, rect):
    if value <= 0:
        return 0
    return int(min(value, rect.width // 2, rect.height // 2))

def draw_rect(surface, color, rect, border=0, radius=None):
    r = clamp_radius(t("corner_roundness", 0), rect) if radius is None else radius
    pg.draw.rect(surface, color, rect, border, border_radius=r)

# =========================================================
# ACTIONS
# =========================================================
def run_action(el):
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
        if item.get("type") in ("button", "toggle", "slider"):
            return f"sidebar:{item['id']}"
    return None

def content_items_from_registry():
    return layout_registry

def sidebar_items_from_registry():
    return sidebar_registry

# =========================================================
# FOCUS CONVERGENCE HELPERS
# =========================================================
def is_focusable_leaf(el):
    """checks if an element type is inherently interactive and selectable."""
    return el.get("type") in ("button", "toggle", "slider") or el.get("focus")

def find_deepest_focusable(el, current_path):
    """recursively finds the first focusable interactive element inside a container."""
    el_id = el.get("id", "")
    path = f"{current_path}:{el_id}" if current_path else el_id
    
    if is_focusable_leaf(el):
        return path
        
    for child in el.get("elements", []):
        leaf_path = find_deepest_focusable(child, path)
        if leaf_path:
            return leaf_path
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

        if not reg or focus not in reg:
            return

        curr_x, curr_y, curr_w, curr_h = reg[focus]
        best_target, min_dist = None, float("inf")

        for path, (tx, ty, tw, th) in reg.items():
            if path == focus:
                continue

            dx = (tx + tw / 2) - (curr_x + curr_w / 2)
            node_dy = (ty + th / 2) - (curr_y + curr_h / 2)

            if direction == "up" and node_dy >= -0.01:
                continue
            if direction == "down" and node_dy <= 0.01:
                continue
            if direction == "left" and dx >= -0.01:
                continue
            if direction == "right" and dx <= 0.01:
                continue

            dist = dx**2 + (node_dy**2 * 500) if direction in ("left", "right") else (dx**2 * 500) + node_dy**2
            if dist < min_dist:
                min_dist = dist
                best_target = path

        if best_target:
            focus = best_target
        return

    reg = content_items_from_registry()
    
    # fallback convergence: if current focus somehow became a container or got orphaned, lock to closest element
    if not reg or focus not in reg:
        if reg:
            focus = next(iter(reg))
            last_content_focus = focus
        return

    curr_x, curr_y, curr_w, curr_h = reg[focus]
    best_target, min_dist = None, float("inf")

    for path, (tx, ty, tw, th) in reg.items():
        if path == focus:
            continue

        dx = (tx + tw / 2) - (curr_x + curr_w / 2)
        node_dy = (ty + th / 2) - (curr_y + curr_h / 2)

        if direction == "up" and node_dy >= -0.01:
            continue
        if direction == "down" and node_dy <= 0.01:
            continue
        if direction == "left" and dx >= -0.01:
            continue
        if direction == "right" and dx <= 0.01:
            continue

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
        if sidebar_focus:
            focus = sidebar_focus
        return

def handle_focus_memory():
    global last_content_focus, focus
    if not is_sidebar_path(focus):
        if focus in layout_registry:
            last_content_focus = focus
        elif layout_registry:
            # if focus lands on a container structural path, break down until a valid leaf is found
            el = get_element_by_path(focus)
            if el:
                deep_leaf = find_deepest_focusable(el, ":".join(focus.split(":")[:-1]))
                if deep_leaf and deep_leaf in layout_registry:
                    focus = deep_leaf
                    last_content_focus = focus

        if sidebar_state["open"]:
            close_sidebar()

# =========================================================
# RENDERING
# =========================================================
def render_gui(element, x=0, y=0, parent_w=48, parent_h=27, current_path="", target_surf=None, gx=0, gy=0, selectable=True):
    global layout_registry, scroll_states, focus_anim
    if target_surf is None:
        target_surf = screen

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

    if is_focused and selectable:
        focus_anim["active"] = True
        focus_anim["tx"] = int((gx + local_x) * cell_w)
        focus_anim["ty"] = int((gy + local_y) * cell_h)
        focus_anim["tw"] = int(w * cell_w)
        focus_anim["th"] = int(h * cell_h)

    # only register actual interactable components into the navigation tree
    if is_focusable_leaf(element):
        if selectable:
            layout_registry[current_path] = (gx + local_x, gy + local_y, w, h)

        draw_rect(target_surf, t("button_color"), rect, 0)
        draw_rect(target_surf, t("button_border"), rect, 1)

        if "label" in element:
            text_surf = font.render(element["label"], True, t("text_color"))
            target_surf.blit(text_surf, text_surf.get_rect(center=rect.center))
        if el_type != "scatter":
            return

    if el_type in ("image", "label", "progress"):
        if el_type == "image":
            draw_rect(target_surf, t("panel_alt_color"), rect, 0)

            image_obj = element.get("surface", element.get("image_surface"))
            image_path = element.get("image_path", element.get("path"))

            if isinstance(image_obj, pg.Surface):
                image_surf = image_obj
            elif isinstance(image_path, str) and image_path:
                if image_path not in image_cache:
                    try:
                        image_cache[image_path] = pg.image.load(image_path).convert_alpha()
                    except Exception as exc:
                        print(f"image load failed for {image_path}: {exc}")
                        image_cache[image_path] = None
                image_surf = image_cache.get(image_path)
            else:
                image_surf = None

            if image_surf is not None:
                fit_mode = element.get("fit", "contain")
                if fit_mode == "stretch":
                    scaled = pg.transform.smoothscale(image_surf, (rect.width, rect.height))
                    target_surf.blit(scaled, rect)
                else:
                    iw, ih = image_surf.get_size()
                    if iw > 0 and ih > 0:
                        scale = min(rect.width / iw, rect.height / ih)
                        new_size = (max(1, int(iw * scale)), max(1, int(ih * scale)))
                        scaled = pg.transform.smoothscale(image_surf, new_size)
                        dest = scaled.get_rect(center=rect.center)
                        target_surf.blit(scaled, dest)
            else:
                pg.draw.line(target_surf, t("border_color"), rect.topleft, rect.bottomright, 1)
                pg.draw.line(target_surf, t("border_color"), rect.topright, rect.bottomleft, 1)

        elif el_type == "label" and "label" in element:
            if "small" in element:
                text_surf = fontsm.render(element["label"], True, t("text_soft_color"))
            else:
                text_surf = font.render(element["label"], True, t("text_soft_color"))
            target_surf.blit(text_surf, text_surf.get_rect(left=rect.left + 6, centery=rect.centery))

        elif el_type == "progress":
            draw_rect(target_surf, t("panel_color"), rect, 0)
            draw_rect(target_surf, t("border_color"), rect, 1)

            value = element.get("value", element.get("current", 0))
            maximum = element.get("max", element.get("maximum", 100))

            try:
                value = float(value)
            except Exception:
                value = 0.0

            try:
                maximum = float(maximum)
            except Exception:
                maximum = 100.0

            if element.get("normalized", False) or maximum <= 1.0:
                fraction = value
            else:
                fraction = value / maximum if maximum else 0.0

            fraction = max(0.0, min(1.0, fraction))

            pad = int(element.get("padding", 2))
            inner = rect.inflate(-pad * 2, -pad * 2)
            inner.width = max(0, inner.width)
            inner.height = max(0, inner.height)

            fill_w = int(inner.width * fraction)
            if fill_w > 0 and inner.height > 0:
                fill_rect = pg.Rect(inner.left, inner.top, fill_w, inner.height)
                draw_rect(target_surf, t("accent_color"), fill_rect, 0)

            text = element.get("label")
            if text is None and element.get("show_percent", True):
                text = f"{int(round(fraction * 100))}%"
            if text:
                text_surf = font.render(str(text), True, t("text_color"))
                target_surf.blit(text_surf, text_surf.get_rect(center=rect.center))
        return

    # containers are structural only now, we don't store them in layout_registry
    if not is_focusable_leaf(element): # Its just a big button with elements.
        if not (el_id == activelayout or (rect.topleft == (0,0) and rect.bottomright == (screen.get_width(),screen.get_height()))):
            draw_rect(target_surf, t("panel_color"), rect, 0)
            draw_rect(target_surf, t("border_color"), rect, 1)
        else:
            draw_rect(target_surf, t("panel_color"), rect, 0, 0) # might be a good idea to draw a square with no rounding

    padding = element.get("padding", 0)
    content_x, content_y = local_x + padding, local_y + padding
    content_w, content_h = w - (padding * 2), h - (padding * 2)
    child_list = element.get("elements", [])

    if child_list:
        is_vertical = element.get("direction") == "vertical"

        if el_type == "scatter":
            for child in child_list:
                c_x = child.get("x", 0)
                c_y = child.get("y", 0)
                c_w = child.get("width", 5)
                c_h = child.get("height", 5)
                render_gui(child, content_x + c_x, content_y + c_y, c_w, c_h, current_path, target_surf, gx, gy, selectable)

        elif element.get("scroll", False):
            if el_id not in scroll_states:
                scroll_states[el_id] = {"current": 0.0, "target": 0.0}

            running_y = 0
            focused_child_y, focused_child_h = None, None
            child_layouts = []

            for child in child_list:
                c_w = content_w if is_vertical else content_w / len(child_list)
                c_h = child.get("height", content_h) if is_vertical else content_h

                if focus.startswith(f"{current_path}:{child.get('id')}"):
                    focused_child_y, focused_child_h = running_y, c_h

                child_layouts.append((child, c_w, c_h, running_y))
                if is_vertical:
                    running_y += c_h

            if focused_child_y is not None:
                t_scroll = scroll_states[el_id]["target"]
                if focused_child_y < t_scroll:
                    scroll_states[el_id]["target"] = focused_child_y
                elif focused_child_y + focused_child_h > t_scroll + content_h:
                    scroll_states[el_id]["target"] = (focused_child_y + focused_child_h) - content_h

            anim_speed = element.get("anim_speed", t("animation_speed", 0.25))
            anim_type = element.get("anim_type", t("animation_type", "ease_out"))
            anim_steps = element.get("anim_steps", 0)

            scroll_states[el_id]["current"] = advance_anim(
                scroll_states[el_id]["current"],
                scroll_states[el_id]["target"],
                anim_speed,
                anim_type,
                anim_steps
            )

            clip_surface = pg.Surface((max(1, int(content_w * cell_w)), max(1, int(content_h * cell_h))))
            clip_surface.fill(tuple(t("panel_color")))

            for child, child_w, child_h, relative_y in child_layouts:
                render_gui(
                    child,
                    0,
                    relative_y - scroll_states[el_id]["current"],
                    child_w,
                    child_h,
                    current_path,
                    clip_surface,
                    gx + content_x,
                    gy + content_y,
                    selectable
                )

            target_surf.blit(clip_surface, (int(content_x * cell_w), int(content_y * cell_h)))

        else:
            cursor_x, cursor_y = content_x, content_y
            is_stretched = element.get("stretch", False)

            for child in child_list:
                c_w = content_w if is_vertical else (content_w / len(child_list) if is_stretched else child.get("width", content_w))
                c_h = content_h if not is_vertical else (content_h / len(child_list) if is_stretched else child.get("height", content_h))
                render_gui(child, cursor_x, cursor_y, c_w, c_h, current_path, target_surf, gx, gy, selectable)
                if is_vertical:
                    cursor_y += c_h
                else:
                    cursor_x += c_w

def render_sidebar():
    global sidebar_registry, focus_anim

    sidebar_w = float(t("sidebar_width", 10))
    sidebar_state["x"] = advance_anim(
        sidebar_state["x"],
        sidebar_state["tx"],
        float(t("sidebar_animation_speed", 0.22)),
        t("animation_type", "ease_out"),
        0
    )

    x_cell = sidebar_state["x"]
    if x_cell <= -sidebar_w + 0.05 and not sidebar_state["open"]:
        return

    sidebar_registry = {}

    sidebar_rect = pg.Rect(int(x_cell * cell_w), 0, int(sidebar_w * cell_w), screen.get_height())
    draw_rect(screen, t("panel_color"), sidebar_rect, 0)
    draw_rect(screen, t("border_color"), sidebar_rect, 1)

    header_rect = pg.Rect(sidebar_rect.left, sidebar_rect.top, sidebar_rect.width, int(3 * cell_h))
    header_text = font.render("sidebar", True, t("accent_color"))
    screen.blit(header_text, header_text.get_rect(center=header_rect.center))

    item_start_y = 4.0
    item_h = 3.0
    item_gap = 0.5

    for idx, item in enumerate(sidebar_items):
        item_y = item_start_y + idx * (item_h + item_gap)
        item_rect = pg.Rect(
            int((x_cell + 0.5) * cell_w),
            int(item_y * cell_h),
            int((sidebar_w - 1.0) * cell_w),
            int(item_h * cell_h),
        )

        path = f"sidebar:{item['id']}"
        sidebar_registry[path] = (x_cell + 0.5, item_y, sidebar_w - 1.0, item_h)

        is_focused = (focus == path)
        fill = t("button_color")
        border = t("button_border")
        if is_focused:
            fill = t("panel_alt_color")
            border = t("accent_color")

            focus_anim["active"] = True
            focus_anim["tx"] = item_rect.left
            focus_anim["ty"] = item_rect.top
            focus_anim["tw"] = item_rect.width
            focus_anim["th"] = item_rect.height

        draw_rect(screen, fill, item_rect, 0)
        draw_rect(screen, border, item_rect, 1)

        label = font.render(item["label"], True, t("text_color"))
        screen.blit(label, label.get_rect(center=item_rect.center))

# =========================================================
# MAIN LOOP
# =========================================================
def mainloop():
    global focus, focus_anim

    running = True
    focus_anim = {"x": 0, "y": 0, "w": 0, "h": 0, "tx": 0, "ty": 0, "tw": 0, "th": 0, "active": False}

    while running:
        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                running = False
            elif ev.type == pg.KEYDOWN:
                if ev.key == pg.K_ESCAPE:
                    running = False
                elif ev.key == pg.K_UP:
                    handle_layout_input("up")
                elif ev.key == pg.K_DOWN:
                    handle_layout_input("down")
                elif ev.key == pg.K_LEFT:
                    handle_layout_input("left")
                elif ev.key == pg.K_RIGHT:
                    handle_layout_input("right")
                elif ev.key == pg.K_RETURN:
                    if is_sidebar_path(focus):
                        for item in sidebar_items:
                            if focus == f"sidebar:{item['id']}":
                                run_action(item)
                                break
                    else:
                        el = get_element_by_path(focus)
                        if el:
                            run_action(el)

        handle_focus_memory()

        screen.fill(tuple(t("background_color")))
        layout_registry.clear()
        focus_anim["active"] = False

        render_gui(layouts[activelayout])
        render_sidebar()

        if focus_anim["active"]:
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

        pg.display.update()
        clock.tick(60)

    save_config(config, CONFIG_PATH)
    pg.quit()
