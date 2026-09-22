# MenuBelt v1.0.1

**Build your own multi-list action menus in Krita, reachable from a cursor popup and
a Tools → MenuBelt submenu. Each list opens as a linear menu or a
Blender-style radial pie.**

## New in 1.0.1

- **Script library** — the editor now manages your own Python scripts: **Scripts** is
  an *Add items* source, and *New… / Edit… / Rename… / Delete / Folder* manage the
  files (the editor has a **Save & Run** button). A script runs with `krita`/`app`,
  `document`/`doc`, `window`, `view` and `layer`/`node` pre-injected, so a new menu
  command is a new *file* instead of a plugin change. Ships with
  `scripts/luminosity_view.py`: a non-destructive **Luminosity (ITU-R BT.709)** view
  (a filter layer on top of the stack — your pixels are never touched, click the item
  again to drop it).
- **Shortcut takeover** — when a list shortcut is already taken, MenuBelt can
  **override** it and unbinds the other binding for you. For a Krita action that is
  written to `kritashortcutsrc`, so it stays unbound after a restart; *Restore* in
  Menu Settings gives it back and clears this menu's key in return.
- **MenuBelt in Krita's Keyboard Shortcuts dialog** — `actions/menubelt.action` is
  part of the release, so the plugin's own actions can be bound in
  **Settings → Configure Krita → Keyboard Shortcuts**.
- `manual.html` and the README updated for all of the above.

## Install

> Requires **Krita 5.x** (developed against 5.3).

1. Download `menubelt_v1.0.1.zip`.
2. Unzip it and copy the `pykrita/` and `actions/` folders into your Krita resource
   directory (Windows: `%APPDATA%/krita/`; Linux: `~/.config/krita/`).
3. Restart Krita.
4. **Settings → Configure Krita → Python Plugin Manager →** tick **MenuBelt**,
   then restart again.

Then open the editor from **Tools → MenuBelt → Configure MenuBelt**.

## License

GPL-3.0 · [Full license](LICENSE)

---

# MenuBelt v1.0.0

**Build your own multi-list action menus in Krita, reachable from a cursor popup and
a Tools → MenuBelt submenu. Each list opens as a linear menu or a
Blender-style radial pie.**

This is the first public release of **MenuBelt**.

## Highlights

- **Native Krita actions** — each command is a *real* Krita action (icons, enable/disable
  state and shortcut hints inherited automatically).
- **Six "Add" sources** — Krita Actions, Layer Blend Mode, Brush Blend Mode, Brush
  Value (Opacity/Flow/Size), Krita Palettes (colour swatches), and Brushes (presets).
- **List or Pie** — linear menus, or Blender-style radial pies (up to 8 items).
- **Submenus, Headers, Separators, checkable Toggles** — organise any list.
- **Per-list shortcuts** plus a whole-menu popup trigger, set from inside the editor.
- **Live preview** of the whole menu tree while editing.
- **Export / Import** config to share or back up your setup.

## Install

> Requires **Krita 5.x** (developed against 5.3).

1. Download this `menubelt_v1.0.0.zip`.
2. Unzip it and copy the `pykrita/` and `actions/` folders into your Krita resource
   directory (Windows: `%APPDATA%/krita/`; Linux: `~/.config/krita/`).
3. Restart Krita.
4. **Settings → Configure Krita → Python Plugin Manager →** tick **MenuBelt**,
   then restart again.

Then open the editor from **Tools → MenuBelt → Configure MenuBelt**.

## License

GPL-3.0 · [Full license](LICENSE)
