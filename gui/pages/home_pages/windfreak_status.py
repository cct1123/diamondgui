"""
Windfreak SynthHD – Status Only Page

last update: 2025/06/20
"""

import time

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html, no_update

from hardware.hardwaremanager import HardwareManager

# Component ID prefix
ID = "windfreak-status-"
hw = HardwareManager()

# ---------- Layout ---------- #

layout_windfreak_status = dbc.Container(
    [
        dbc.Card(
            [
                dbc.CardHeader("Windfreak SynthHD – Channel Monitor"),
                dbc.CardBody(
                    [
                        dcc.Interval(id=ID + "interval", interval=1000, n_intervals=0),
                        dbc.Table(
                            id=ID + "status-table",
                            bordered=True,
                            striped=True,
                            hover=True,
                        ),
                        html.Div(id=ID + "last-updated", className="text-muted mt-2"),
                        dcc.Store(id=ID + "status-store", storage_type="memory"),
                    ]
                ),
            ],
            className="mt-4 mb-4",
        )
    ],
    fluid=True,
)

# ---------- Callback ---------- #


@callback(
    Output(ID + "status-table", "children"),
    Output(ID + "status-store", "data"),
    Output(ID + "last-updated", "children"),
    Input(ID + "interval", "n_intervals"),
    State(ID + "status-store", "data"),
)
def update_status_table(_, stored_data):
    try:

        def read(ch, param):
            return hw.windfreak.synth[ch].read(param)

        now = time.time()
        channels = []
        for ch in [0, 1]:
            freq = round(read(ch, "frequency") / 1e6, 3)
            power = round(read(ch, "power"), 2)
            enabled = "Yes" if read(ch, "rf_enable") else "No"
            channels.append(
                {"channel": ch, "freq": freq, "power": power, "enabled": enabled}
            )

        table_body = html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(f"Channel {c['channel']}"),
                        html.Td(c["freq"]),
                        html.Td(c["power"]),
                        html.Td(c["enabled"]),
                    ]
                )
                for c in channels
            ]
        )

        table = [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Channel"),
                        html.Th("Frequency (MHz)"),
                        html.Th("Power (dBm)"),
                        html.Th("Enabled"),
                    ]
                )
            ),
            table_body,
        ]

        return table, {"timestamp": now, "channels": channels}, "Last updated just now"

    except Exception:
        if not stored_data:
            return no_update, no_update, "No valid data available"

        age_sec = int(time.time() - stored_data["timestamp"])
        age_msg = (
            f"Last update {age_sec} sec ago"
            if age_sec < 60
            else f"Last update {age_sec // 60} min ago"
        )

        table_body = html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(f"Channel {c['channel']}"),
                        html.Td(c["freq"]),
                        html.Td(c["power"]),
                        html.Td(c["enabled"]),
                    ]
                )
                for c in stored_data.get("channels", [])
            ]
        )

        table = [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Channel"),
                        html.Th("Frequency (MHz)"),
                        html.Th("Power (dBm)"),
                        html.Th("Enabled"),
                    ]
                )
            ),
            table_body,
        ]

        return table, no_update, age_msg
