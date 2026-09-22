"""View mode: Luminosity (ITU-R BT.709).

Toggles a *non-destructive* display mode: click the menu item once to add a
desaturate filter layer (method = Luminosity, ITU-R BT.709) on top of the
current document, click it again to remove that layer. Nothing is painted into
your layers, so the effect can be dropped at any time by deleting the layer.

Injected by MenuBelt: krita / app, document / doc, window, view, layer / node.
Copy this file before editing if you want to keep the original around.
"""
from krita import Selection

LAYER_NAME = "View \u00b7 Luminosity (ITU-R BT.709)"
# Desaturate filter parameters: type 1 = Luminosity (ITU-R BT.709)
# (0 Lightness, 1 Luminosity BT.709, 2 Luminosity BT.601, 3 Average, 4 Min, 5 Max).
LUMINOSITY_BT709 = 1


def _walk(node):
    """Yield a node and all of its descendants."""
    stack = [node]
    while stack:
        current = stack.pop()
        if current is None:
            continue
        yield current
        try:
            stack.extend(current.childNodes())
        except Exception:
            continue


def _find_layer(doc):
    for node in _walk(doc.rootNode()):
        try:
            if node.name() == LAYER_NAME:
                return node
        except Exception:
            continue
    return None


def _add_layer(doc):
    filt = krita.filter("desaturate")
    if filt is None:
        raise RuntimeError("the 'desaturate' filter is unavailable in this Krita build")
    selection = Selection()
    selection.selectAll(doc.rootNode(), 255)
    layer = doc.createFilterLayer(LAYER_NAME, filt, selection)
    if layer is None:
        raise RuntimeError("Krita refused to create the filter layer")
    doc.rootNode().addChildNode(layer, None)      # top of the stack
    # The layer owns its own filter configuration - configuring the object
    # returned by krita.filter() above would have no effect on the layer.
    live = layer.filter()
    config = live.configuration()
    config.setProperty("type", LUMINOSITY_BT709)
    live.setConfiguration(config)
    return layer


def toggle(doc):
    """Add the view layer, or remove it when it is already there."""
    if doc is None:
        raise RuntimeError("no active document")
    existing = _find_layer(doc)
    if existing is not None:
        existing.remove()
        doc.refreshProjection()
        return "removed"
    _add_layer(doc)
    doc.refreshProjection()
    return "added"


state = toggle(document)
print("MenuBelt: %s \"%s\"" % (state, LAYER_NAME))
