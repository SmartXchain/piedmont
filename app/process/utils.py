# process/utils.py
import os
import base64
import re

from django.utils import timezone
from django.conf import settings
from graphviz import Digraph

from .models import Process


def _estimate_duration(min_val, max_val):
    """
    Estimate a single duration value (minutes) from min/max.
    Uses average if both present, or whichever is present.
    Returns int minutes.
    """
    if min_val is not None and max_val is not None:
        return int(round((min_val + max_val) / 2))
    if min_val is not None:
        return int(min_val)
    if max_val is not None:
        return int(max_val)
    return 0


def _embed_logo_in_svg(svg: str, image_path: str) -> str:
    """
    Replace the xlink:href reference to the logo file in the SVG
    with a data:image/png;base64,... URI so the logo is embedded.

    This assumes the logo appears as an <image xlink:href="...basename...">.
    """
    if not os.path.exists(image_path):
        return svg

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    basename = os.path.basename(image_path)

    # Replace any xlink:href="...basename..." with data URI
    pattern = rf'xlink:href="[^"]*{re.escape(basename)}[^"]*"'
    replacement = f'xlink:href="data:image/png;base64,{b64}"'

    svg_embedded = re.sub(pattern, replacement, svg)
    return svg_embedded


def build_process_flowchart_svg(process: Process) -> str:
    """
    Build an SVG flowchart for a Process using Graphviz.

    Features:
      - Top-down layout
      - Header with:
          * Standard name
          * Classification
          * Standard process name
          * Revision
          * Generated date
          * Process number
          * Total touch time (min)
          * Total run time (min)
      - Optional logo (settings.GRAPHVIZ_LOGO_PATH) embedded as base64
      - Rectified steps highlighted with a different fill color
      - Per-step labels include touch/run times if present
    """
    dot = Digraph(
        name=f"process_{process.id}",
        comment=f"Flowchart for Process {process.id}",
        format="svg",
    )

    # ---------------------------------------------------------------------
    # Header info (we'll compute total times after we scan steps)
    # ---------------------------------------------------------------------
    standard_name = process.standard.name if process.standard else "Process"
    classification_name = getattr(process.classification, "class_name", None)
    subtitle = getattr(process.standard_process, "name", "") or ""
    revision = getattr(process.standard, "revision", None) if process.standard else None
    generated_date = timezone.now().strftime("%Y-%m-%d")

    classification_color = "#007bff" if classification_name else "black"

    # ---------------------------------------------------------------------
    # Steps (we need to scan them to compute totals)
    # ---------------------------------------------------------------------
    steps = process.steps.select_related("method").order_by("step_number")

    if not steps.exists():
        # No steps: handle simple case (logo + header only)
        logo_rel_path = getattr(settings, "GRAPHVIZ_LOGO_PATH", None)
        logo_abs_path = None
        has_logo = False

        if logo_rel_path:
            logo_abs_path = os.path.join(settings.BASE_DIR, logo_rel_path)
            if os.path.exists(logo_abs_path):
                has_logo = True
                logo_basename = os.path.basename(logo_abs_path)
                dot.node(
                    "logo",
                    image=logo_basename,
                    label="",
                    shape="none",
                    fixedsize="true",
                    width="1.0",
                )

        header_lines = [standard_name]
        if classification_name:
            header_lines.append(f"Classification: {classification_name}")
        if subtitle:
            header_lines.append(subtitle)
        if revision:
            header_lines.append(f"Rev: {revision}")
        header_lines.append(f"Generated {generated_date} — Process #{process.id}")

        header_label = "\n".join(header_lines)

        dot.node(
            "header",
            label=header_label,
            shape="none",
            fontcolor=classification_color,
        )

        if has_logo:
            dot.body.append("{ rank=min; logo; header; }")
            dot.attr(imagepath=os.path.dirname(logo_abs_path))
            dot.edge("logo", "header", style="invis")
        else:
            dot.body.append("{ rank=min; header; }")

        dot.attr(rankdir="TB", nodesep="0.5", ranksep="0.75")

        svg = dot.pipe(format="svg").decode("utf-8")
        if has_logo and logo_abs_path:
            svg = _embed_logo_in_svg(svg, logo_abs_path)
        return svg

    # If we have steps, compute total touch/run time across methods
    total_touch = 0
    total_run = 0
    for step in steps:
        m = step.method
        if not m:
            continue
        total_touch += _estimate_duration(m.touch_time_min, m.touch_time_max)
        total_run += _estimate_duration(m.run_time_min, m.run_time_max)

    # ---------------------------------------------------------------------
    # Optional logo node
    # ---------------------------------------------------------------------
    logo_rel_path = getattr(settings, "GRAPHVIZ_LOGO_PATH", None)
    logo_abs_path = None
    has_logo = False

    if logo_rel_path:
        logo_abs_path = os.path.join(settings.BASE_DIR, logo_rel_path)
        if os.path.exists(logo_abs_path):
            has_logo = True
            logo_basename = os.path.basename(logo_abs_path)
            dot.node(
                "logo",
                image=logo_basename,
                label="",
                shape="none",
                fixedsize="true",
                width="1.0",
            )

    # ---------------------------------------------------------------------
    # Header node (with total times)
    # ---------------------------------------------------------------------
    header_lines = [standard_name]

    if classification_name:
        header_lines.append(f"Classification: {classification_name}")
    if subtitle:
        header_lines.append(subtitle)
    if revision:
        header_lines.append(f"Rev: {revision}")

    # Add totals if any non-zero
    if total_touch > 0 or total_run > 0:
        header_lines.append(
            f"Est. Touch Time: {total_touch} min  |  Est. Run Time: {total_run} min"
        )

    header_lines.append(f"Generated {generated_date} — Process #{process.id}")

    header_label = "\n".join(header_lines)

    dot.node(
        "header",
        label=header_label,
        shape="none",
        fontcolor=classification_color,
    )

    if has_logo:
        dot.body.append("{ rank=min; logo; header; }")
        dot.edge("logo", "header", style="invis")
    else:
        dot.body.append("{ rank=min; header; }")

    # Graph attributes
    dot.attr(
        rankdir="TB",
        nodesep="0.5",
        ranksep="0.75",
    )
    dot.attr("node", shape="box", style="rounded,filled", fillcolor="lightgrey")

    if has_logo and logo_abs_path:
        dot.attr(imagepath=os.path.dirname(logo_abs_path))

    # ---------------------------------------------------------------------
    # Step nodes (with per-step touch/run times)
    # ---------------------------------------------------------------------
    node_ids = []
    for step in steps:
        node_id = f"step_{step.id}"
        node_ids.append(node_id)

        method = step.method
        method_title = method.title if method else "No Method"
        method_type = getattr(method, "method_type", "") or ""
        chemical = getattr(method, "chemical", "") or ""

        label_lines = [
            f"Step {step.step_number}",
            method_title,
        ]
        if method_type:
            label_lines.append(f"Type: {method_type}")
        if chemical:
            label_lines.append(f"Chem: {chemical}")

        # Touch time
        if method and (method.touch_time_min is not None or method.touch_time_max is not None):
            if method.touch_time_min is not None and method.touch_time_max is not None:
                label_lines.append(
                    f"Touch: {method.touch_time_min}-{method.touch_time_max} min"
                )
            else:
                single = method.touch_time_min or method.touch_time_max
                label_lines.append(f"Touch: {single} min")

        # Run time
        if method and (method.run_time_min is not None or method.run_time_max is not None):
            if method.run_time_min is not None and method.run_time_max is not None:
                label_lines.append(
                    f"Run: {method.run_time_min}-{method.run_time_max} min"
                )
            else:
                single = method.run_time_min or method.run_time_max
                label_lines.append(f"Run: {single} min")

        label = "\n".join(label_lines)

        is_rectified = getattr(method, "is_rectified", False)
        fillcolor = "#ffd9d9" if is_rectified else "lightgrey"

        dot.node(
            node_id,
            label=label,
            tooltip=method_title,
            fillcolor=fillcolor,
        )

    # Edges: header -> first step, then chain
    if node_ids:
        dot.edge("header", node_ids[0])
        for i in range(len(node_ids) - 1):
            dot.edge(node_ids[i], node_ids[i + 1])

    svg = dot.pipe(format="svg").decode("utf-8")

    if has_logo and logo_abs_path:
        svg = _embed_logo_in_svg(svg, logo_abs_path)

    return svg
