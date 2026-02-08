#!/usr/bin/env python3
"""
Generate the NOVA-7 Executive Dashboard NDJSON file compatible with Kibana 9.4.

Produces by-value Lens panels using the formBased datasource format that matches
the built-in [OTel] dashboards shipped with Kibana 9.4, including all required
fields: ignoreGlobalFilters, incompleteColumns, sampling, adHocDataViews,
internalReferences, legend, valueLabels.
"""

import json
import os
import uuid

DATA_VIEW_ID = "logs-*"
DASHBOARD_ID = "nova7-exec-dashboard"


def uid():
    """Generate a random UUID for layer/column IDs."""
    return str(uuid.uuid4())


def make_ref(layer_id):
    """Create a data view reference matching the OTel dashboard pattern."""
    return {
        "id": DATA_VIEW_ID,
        "name": f"indexpattern-datasource-layer-{layer_id}",
        "type": "index-pattern",
    }


def make_layer(layer_id, column_order, columns):
    """Build a formBased layer with all Kibana 9.4 required fields."""
    return {
        layer_id: {
            "columnOrder": column_order,
            "columns": columns,
            "ignoreGlobalFilters": False,
            "incompleteColumns": {},
            "sampling": 1,
        }
    }


def make_state(layers_dict, visualization, query="", filters=None):
    """Build the full state object for a Lens panel."""
    return {
        "adHocDataViews": {},
        "datasourceStates": {
            "formBased": {
                "layers": layers_dict,
            }
        },
        "filters": filters or [],
        "internalReferences": [],
        "query": {"language": "kuery", "query": query},
        "visualization": visualization,
    }


def make_panel(panel_id, grid, title, vis_type, state, references):
    """Build a complete panel object for the dashboard."""
    return {
        "embeddableConfig": {
            "attributes": {
                "references": references,
                "state": state,
                "title": title,
                "type": "lens",
                "visualizationType": vis_type,
            },
            "enhancements": {},
            "syncColors": False,
            "syncCursor": True,
            "syncTooltips": False,
        },
        "gridData": grid,
        "panelIndex": panel_id,
        "title": title,
        "type": "lens",
    }


def col_count(col_id, label="Count", kql_filter=None):
    """Create a count column."""
    col = {
        "customLabel": True,
        "dataType": "number",
        "isBucketed": False,
        "label": label,
        "operationType": "count",
        "params": {"emptyAsNull": True},
        "scale": "ratio",
        "sourceField": "___records___",
    }
    if kql_filter:
        col["filter"] = {"language": "kuery", "query": kql_filter}
    return col


def col_unique_count(col_id, source_field, label="Unique"):
    """Create a unique_count column."""
    return {
        "customLabel": True,
        "dataType": "number",
        "isBucketed": False,
        "label": label,
        "operationType": "unique_count",
        "params": {"emptyAsNull": True},
        "scale": "ratio",
        "sourceField": source_field,
    }


def col_date_histogram(col_id, interval="30s", label="@timestamp"):
    """Create a date_histogram column."""
    return {
        "customLabel": True,
        "dataType": "date",
        "isBucketed": True,
        "label": label,
        "operationType": "date_histogram",
        "params": {"interval": interval},
        "scale": "interval",
        "sourceField": "@timestamp",
    }


def col_terms(col_id, source_field, label, size=10, order_col_id=None):
    """Create a terms column."""
    params = {
        "size": size,
        "orderDirection": "desc",
        "orderBy": {"columnId": order_col_id, "type": "column"} if order_col_id else {"type": "alphabetical"},
        "missingBucket": False,
        "otherBucket": False,
    }
    col = {
        "customLabel": True,
        "dataType": "string",
        "isBucketed": True,
        "label": label,
        "operationType": "terms",
        "params": params,
        "scale": "ordinal",
        "sourceField": source_field,
    }
    return col


# ── Build panels ────────────────────────────────────────────────────────────

panels = []

# ── p1: Error Rate (lnsMetric) ──────────────────────────────────────────────
lid = uid()
cid = uid()
columns = {cid: col_count(cid, label="Error Rate", kql_filter="severity_text: ERROR OR severity_text: FATAL")}
layer = make_layer(lid, [cid], columns)
state = make_state(layer, {
    "layerId": lid,
    "layerType": "data",
    "metricAccessor": cid,
    "color": "#E7664C",
    "subtitle": "Errors / min",
})
panels.append(make_panel("p1",
    {"h": 6, "i": "p1", "w": 12, "x": 0, "y": 0},
    "Error Rate", "lnsMetric", state, [make_ref(lid)]))

# ── p2: Log Volume (lnsMetric) ──────────────────────────────────────────────
lid = uid()
cid = uid()
columns = {cid: col_count(cid, label="Log Volume")}
layer = make_layer(lid, [cid], columns)
state = make_state(layer, {
    "layerId": lid,
    "layerType": "data",
    "metricAccessor": cid,
    "color": "#54B399",
    "subtitle": "Total log volume",
})
panels.append(make_panel("p2",
    {"h": 6, "i": "p2", "w": 12, "x": 12, "y": 0},
    "Log Volume", "lnsMetric", state, [make_ref(lid)]))

# ── p3: Active Services (lnsMetric) ─────────────────────────────────────────
lid = uid()
cid = uid()
columns = {cid: col_unique_count(cid, "resource.attributes.service.name", label="Active Services")}
layer = make_layer(lid, [cid], columns)
state = make_state(layer, {
    "layerId": lid,
    "layerType": "data",
    "metricAccessor": cid,
    "color": "#6DCCB1",
    "subtitle": "Distinct services reporting",
})
panels.append(make_panel("p3",
    {"h": 6, "i": "p3", "w": 12, "x": 24, "y": 0},
    "Active Services", "lnsMetric", state, [make_ref(lid)]))

# ── p4: Active Anomalies (lnsMetric) ────────────────────────────────────────
lid = uid()
cid = uid()
columns = {cid: col_unique_count(cid, "attributes.chaos.channel", label="Active Anomalies")}
layer = make_layer(lid, [cid], columns)
state = make_state(layer, {
    "layerId": lid,
    "layerType": "data",
    "metricAccessor": cid,
    "color": "#DA8B45",
    "subtitle": "Distinct fault channels",
})
panels.append(make_panel("p4",
    {"h": 6, "i": "p4", "w": 12, "x": 36, "y": 0},
    "Active Anomalies", "lnsMetric", state, [make_ref(lid)]))

# ── p5: Log Volume Over Time (lnsXY area_stacked) ──────────────────────────
lid = uid()
cid_x = uid()
cid_y = uid()
columns = {
    cid_x: col_date_histogram(cid_x, "30s"),
    cid_y: col_count(cid_y, label="Log count"),
}
layer = make_layer(lid, [cid_x, cid_y], columns)
state = make_state(layer, {
    "legend": {"isVisible": True, "position": "right"},
    "valueLabels": "hide",
    "preferredSeriesType": "area_stacked",
    "layers": [{
        "layerId": lid,
        "layerType": "data",
        "seriesType": "area_stacked",
        "accessors": [cid_y],
        "xAccessor": cid_x,
    }],
})
panels.append(make_panel("p5",
    {"h": 12, "i": "p5", "w": 24, "x": 0, "y": 6},
    "Log Volume Over Time", "lnsXY", state, [make_ref(lid)]))

# ── p6: Errors by Subsystem (lnsXY bar_horizontal) ─────────────────────────
lid = uid()
cid_x = uid()
cid_y = uid()
columns = {
    cid_x: col_terms(cid_x, "attributes.system.subsystem", "Subsystem", size=10, order_col_id=cid_y),
    cid_y: col_count(cid_y, label="Error Count", kql_filter="severity_text: ERROR"),
}
layer = make_layer(lid, [cid_x, cid_y], columns)
state = make_state(layer, {
    "legend": {"isVisible": True, "position": "right"},
    "valueLabels": "hide",
    "preferredSeriesType": "bar_horizontal",
    "layers": [{
        "layerId": lid,
        "layerType": "data",
        "seriesType": "bar_horizontal",
        "accessors": [cid_y],
        "xAccessor": cid_x,
    }],
})
panels.append(make_panel("p6",
    {"h": 12, "i": "p6", "w": 24, "x": 24, "y": 6},
    "Errors by Subsystem", "lnsXY", state, [make_ref(lid)]))

# ── p7: Cloud Provider Distribution (lnsPie) ───────────────────────────────
lid = uid()
cid_group = uid()
cid_metric = uid()
columns = {
    cid_group: col_terms(cid_group, "resource.attributes.cloud.provider", "Cloud Provider", size=5, order_col_id=cid_metric),
    cid_metric: col_count(cid_metric, label="Count"),
}
layer = make_layer(lid, [cid_group, cid_metric], columns)
state = make_state(layer, {
    "shape": "pie",
    "layers": [{
        "layerId": lid,
        "layerType": "data",
        "primaryGroups": [cid_group],
        "metrics": [cid_metric],
    }],
})
panels.append(make_panel("p7",
    {"h": 12, "i": "p7", "w": 24, "x": 0, "y": 18},
    "Cloud Provider Distribution", "lnsPie", state, [make_ref(lid)]))

# ── p8: Top 10 Error Types (lnsDatatable) ──────────────────────────────────
lid = uid()
cid_terms = uid()
cid_count = uid()
columns = {
    cid_terms: col_terms(cid_terms, "attributes.error.type", "Error Type", size=10, order_col_id=cid_count),
    cid_count: col_count(cid_count, label="Count"),
}
layer = make_layer(lid, [cid_terms, cid_count], columns)
state = make_state(layer, {
    "columns": [
        {"columnId": cid_terms, "isTransposed": False, "isMetric": False},
        {"columnId": cid_count, "isTransposed": False, "isMetric": True},
    ],
    "layerId": lid,
    "layerType": "data",
    "paging": {"enabled": True, "size": 10},
    "sorting": None,
})
panels.append(make_panel("p8",
    {"h": 12, "i": "p8", "w": 24, "x": 24, "y": 18},
    "Top 10 Error Types", "lnsDatatable", state, [make_ref(lid)]))

# ── p9: Service Health Matrix (lnsHeatmap) ──────────────────────────────────
lid = uid()
cid_time = uid()
cid_svc = uid()
cid_val = uid()
columns = {
    cid_time: col_date_histogram(cid_time, "1m"),
    cid_svc: col_terms(cid_svc, "resource.attributes.service.name", "Service", size=10, order_col_id=cid_val),
    cid_val: col_count(cid_val, label="Error Count", kql_filter="severity_text: ERROR"),
}
layer = make_layer(lid, [cid_time, cid_svc, cid_val], columns)
state = make_state(layer, {
    "gridConfig": {"isCellLabelVisible": False},
    "shape": "heatmap",
    "layerId": lid,
    "layerType": "data",
    "xAccessor": cid_time,
    "yAccessor": cid_svc,
    "valueAccessor": cid_val,
    "legend": {"isVisible": True, "position": "right"},
})
panels.append(make_panel("p9",
    {"h": 12, "i": "p9", "w": 48, "x": 0, "y": 30},
    "Service Health Matrix", "lnsHeatmap", state, [make_ref(lid)]))

# ── p10: Nginx Request Rate (lnsXY area_stacked) ───────────────────────────
lid = uid()
cid_x = uid()
cid_y = uid()
columns = {
    cid_x: col_date_histogram(cid_x, "30s"),
    cid_y: col_count(cid_y, label="Requests"),
}
layer = make_layer(lid, [cid_x, cid_y], columns)
state = make_state(layer, {
    "legend": {"isVisible": True, "position": "right"},
    "valueLabels": "hide",
    "preferredSeriesType": "area_stacked",
    "layers": [{
        "layerId": lid,
        "layerType": "data",
        "seriesType": "area_stacked",
        "accessors": [cid_y],
        "xAccessor": cid_x,
    }],
}, query="data_stream.dataset: nginx.access.otel")
panels.append(make_panel("p10",
    {"h": 10, "i": "p10", "w": 24, "x": 0, "y": 42},
    "Nginx Request Rate", "lnsXY", state, [make_ref(lid)]))

# ── p11: MySQL Slow Queries (lnsXY line) ────────────────────────────────────
lid = uid()
cid_x = uid()
cid_y = uid()
columns = {
    cid_x: col_date_histogram(cid_x, "30s"),
    cid_y: col_count(cid_y, label="Slow Queries"),
}
layer = make_layer(lid, [cid_x, cid_y], columns)
state = make_state(layer, {
    "legend": {"isVisible": True, "position": "right"},
    "valueLabels": "hide",
    "preferredSeriesType": "line",
    "layers": [{
        "layerId": lid,
        "layerType": "data",
        "seriesType": "line",
        "accessors": [cid_y],
        "xAccessor": cid_x,
    }],
}, query="data_stream.dataset: mysql.slowlog.otel")
panels.append(make_panel("p11",
    {"h": 10, "i": "p11", "w": 24, "x": 24, "y": 42},
    "MySQL Slow Queries", "lnsXY", state, [make_ref(lid)]))


# ── Collect all references from panels ──────────────────────────────────────
all_refs = []
seen_ref_names = set()
for panel in panels:
    for ref in panel["embeddableConfig"]["attributes"]["references"]:
        if ref["name"] not in seen_ref_names:
            all_refs.append(ref)
            seen_ref_names.add(ref["name"])


# ── Build the dashboard saved object ───────────────────────────────────────
dashboard = {
    "attributes": {
        "description": "Executive overview of NOVA-7 mission telemetry across all subsystems and cloud providers",
        "kibanaSavedObjectMeta": {
            "searchSourceJSON": json.dumps({
                "query": {"language": "kuery", "query": ""},
                "filter": [],
            }),
        },
        "panelsJSON": json.dumps(panels),
        "refreshInterval": {"pause": False, "value": 10000},
        "timeFrom": "now-15m",
        "timeRestore": True,
        "timeTo": "now",
        "title": "NOVA-7 Executive Dashboard",
    },
    "coreMigrationVersion": "8.8.0",
    "id": DASHBOARD_ID,
    "managed": False,
    "references": all_refs,
    "type": "dashboard",
    "typeMigrationVersion": "10.3.0",
}

# ── Write NDJSON ────────────────────────────────────────────────────────────
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exec-dashboard.ndjson")
with open(output_path, "w") as f:
    f.write(json.dumps(dashboard, separators=(",", ":")) + "\n")

print(f"Wrote {output_path}")
print(f"  Panels: {len(panels)}")
print(f"  References: {len(all_refs)}")
