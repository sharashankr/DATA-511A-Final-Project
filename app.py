
# app.py
# US Data Center Environmental Explorer
# Uses final_footprint_dataset.csv (built from the Virginia Tech "Input data.xlsx")

import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc



df = pd.read_csv("final_footprint_dataset.csv")


numeric_cols = [
    "water_footprint",
    "carbon_footprint",
    "total_mwh",
    "scarcity_factor",
    "carbon_intensity_tons_per_mwh",
]
for col in numeric_cols:
    if col in df.columns:
        df[col] = df[col].fillna(0)
    else:
        df[col] = 0.0


df_map = df.dropna(subset=["lat", "lon"]).copy()


state_df = (
    df_map.groupby("plant_state")
    .agg(
        total_mwh=("total_mwh", "sum"),
        water_footprint=("water_footprint", "sum"),
        carbon_footprint=("carbon_footprint", "sum"),
    )
    .reset_index()
)


subbasin_df = (
    df_map.groupby(["subbasin", "plant_state", "pca_name", "fuel_code"])
    .agg(
        total_mwh=("total_mwh", "sum"),
        water_footprint=("water_footprint", "sum"),
        carbon_footprint=("carbon_footprint", "sum"),
        scarcity_factor=("scarcity_factor", "mean"),
        carbon_intensity_tons_per_mwh=("carbon_intensity_tons_per_mwh", "mean"),
    )
    .reset_index()
)


pca_df = (
    df_map.groupby("pca_name")
    .agg(
        total_mwh=("total_mwh", "sum"),
        water_footprint=("water_footprint", "sum"),
        carbon_footprint=("carbon_footprint", "sum"),
        scarcity_factor=("scarcity_factor", "mean"),
        carbon_intensity_tons_per_mwh=("carbon_intensity_tons_per_mwh", "mean"),
    )
    .reset_index()
)


hier_df = (
    df_map.groupby(["plant_state", "pca_name", "subbasin"])
    .agg(
        total_mwh=("total_mwh", "sum"),
        water_footprint=("water_footprint", "sum"),
        carbon_footprint=("carbon_footprint", "sum"),
    )
    .reset_index()
)


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    suppress_callback_exceptions=True,
)
server = app.server  
app.title = "US Data Center Environmental Impact"



def water_tab_layout():
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.H5("Filters", className="text-info mb-2"),

                    html.Label("PCA"),
                    dcc.Dropdown(
                        id="pca_filter",
                        options=[
                            {"label": p, "value": p}
                            for p in sorted(df_map["pca_name"].dropna().unique())
                        ],
                        multi=True,
                        placeholder="Select PCA(s)",
                    ),
                    html.Br(),

                    html.Label("State"),
                    dcc.Dropdown(
                        id="state_filter",
                        options=[
                            {"label": s, "value": s}
                            for s in sorted(df_map["plant_state"].dropna().unique())
                        ],
                        multi=True,
                        placeholder="Select state(s)",
                    ),
                    html.Br(),

                    html.Label("Fuel type"),
                    dcc.Dropdown(
                        id="fuel_filter",
                        options=[
                            {"label": f, "value": f}
                            for f in sorted(df_map["fuel_code"].dropna().unique())
                        ],
                        multi=True,
                        placeholder="Select fuel type(s)",
                    ),
                ],
                width=3,
            ),

            dbc.Col(
                [
                    dcc.Graph(id="water_map", style={"height": "70vh"}),
                    html.Div(id="water_details", className="mt-3"),
                ],
                width=9,
            ),
        ]
    )


def carbon_tab_layout():
    return dbc.Row(
        dbc.Col(
            dcc.Graph(id="carbon_map", style={"height": "80vh"}),
            width=12,
        )
    )


def tradeoff_tab_layout():
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.Label("Color by"),
                    dcc.Dropdown(
                        id="tradeoff_color_metric",
                        options=[
                            {"label": "Carbon intensity (tons/MWh)", "value": "carbon_intensity_tons_per_mwh"},
                            {"label": "Water footprint (m³-eq)", "value": "water_footprint"},
                            {"label": "Carbon footprint (tons CO₂-eq)", "value": "carbon_footprint"},
                        ],
                        value="carbon_intensity_tons_per_mwh",
                        clearable=False,
                    ),
                    html.Br(),
                    dcc.Checklist(
                        id="tradeoff_logx",
                        options=[{"label": "Log-scale x-axis", "value": "logx"}],
                        value=["logx"],
                        labelStyle={"color": "white"},
                    ),
                    html.P(
                        "Each bubble is a subbasin–PCA combination. "
                        "Big, bright points in the upper-right are places where "
                        "data centers use a lot of electricity in already water-stressed areas.",
                        className="text-muted mt-3",
                    ),
                ],
                width=3,
            ),
            dbc.Col(
                dcc.Graph(id="tradeoff_scatter", style={"height": "80vh"}),
                width=9,
            ),
        ]
    )


def state_tab_layout():
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.Label("Metric"),
                    dcc.RadioItems(
                        id="state_metric",
                        options=[
                            {"label": "Water footprint", "value": "water_footprint"},
                            {"label": "Carbon footprint", "value": "carbon_footprint"},
                            {"label": "Total electricity (MWh)", "value": "total_mwh"},
                        ],
                        value="water_footprint",
                        labelStyle={"display": "block"},
                    ),
                    html.P(
                        "Hover on a state to see totals. "
                        "This is a high-level snapshot: it hides within-state hotspots "
                        "that you can find on the map tabs.",
                        className="text-muted mt-3",
                    ),
                ],
                width=3,
            ),
            dbc.Col(
                dcc.Graph(id="state_map", style={"height": "80vh"}),
                width=9,
            ),
        ]
    )


def multivariate_tab_layout():
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.Label("Color lines by"),
                    dcc.Dropdown(
                        id="parallel_color_metric",
                        options=[
                            {"label": "Water footprint", "value": "water_footprint"},
                            {"label": "Carbon footprint", "value": "carbon_footprint"},
                            {"label": "Total electricity (MWh)", "value": "total_mwh"},
                            {"label": "Water scarcity factor", "value": "scarcity_factor"},
                            {
                                "label": "Carbon intensity (tons/MWh)",
                                "value": "carbon_intensity_tons_per_mwh",
                            },
                        ],
                        value="water_footprint",
                        clearable=False,
                    ),
                    html.P(
                        "Each line is a subbasin. Parallel axes let you see whether high "
                        "electricity, high water footprint, and high carbon footprint tend "
                        "to co-occur in the same places.",
                        className="text-muted mt-3",
                    ),
                ],
                width=3,
            ),
            dbc.Col(
                dcc.Graph(id="parallel_plot", style={"height": "80vh"}),
                width=9,
            ),
        ]
    )


def hierarchy_tab_layout():
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.Label("Value to visualize"),
                    dcc.Dropdown(
                        id="hierarchy_metric",
                        options=[
                            {"label": "Electricity (MWh)", "value": "total_mwh"},
                            {"label": "Water footprint (m³-eq)", "value": "water_footprint"},
                            {"label": "Carbon footprint (tons CO₂-eq)", "value": "carbon_footprint"},
                        ],
                        value="total_mwh",
                        clearable=False,
                    ),
                    html.P(
                        "Sunburst shows how each state, PCA, and subbasin contribute to the "
                        "overall footprint. Click to zoom into a specific state or provider.",
                        className="text-muted mt-3",
                    ),
                ],
                width=3,
            ),
            dbc.Col(
                dcc.Graph(id="hierarchy_sunburst", style={"height": "80vh"}),
                width=9,
            ),
        ]
    )


def correlation_tab_layout():
    return dbc.Row(
        dbc.Col(
            dcc.Graph(id="corr_heatmap", style={"height": "80vh"}),
            width=12,
        )
    )


def future_tab_layout():
    return html.Div(
        [
            html.H4("Future Projections (coming soon)", className="text-info"),
            html.P(
                "This tab is reserved for integrating the US-AI-Server-Analysis dataset "
                "and Aqueduct 4.0 future water stress projections (2030 / 2050 / 2080). "
                "The idea is to extend this snapshot into \"what if\" scenarios.",
                className="text-muted",
            ),
        ],
        className="p-3",
    )



app.layout = dbc.Container(
    fluid=True,
    children=[
        dbc.Row(
            dbc.Col(
                html.H2(
                    "US Data Center Environmental Explorer",
                    className="text-center text-info mt-3 mb-1",
                ),
                width=12,
            )
        ),
        dbc.Row(
            dbc.Col(
                html.P(
                    "Interactive exploration of how US data centers' electricity demand "
                    "translates into water stress and carbon emissions, at the watershed level.",
                    className="text-center text-muted mb-3",
                ),
                width=12,
            )
        ),
        dcc.Tabs(
            id="tabs",
            value="tab-water",
            children=[
                dcc.Tab(label="Water Footprint Map", value="tab-water"),
                dcc.Tab(label="Carbon Footprint Map", value="tab-carbon"),
                dcc.Tab(label="Energy–Water Tradeoff", value="tab-tradeoff"),
                dcc.Tab(label="State Summary", value="tab-state"),
                dcc.Tab(label="Multivariate Patterns", value="tab-multi"),
                dcc.Tab(label="PCA / Subbasin Hierarchy", value="tab-hierarchy"),
                dcc.Tab(label="Correlation Explorer", value="tab-corr"),
                dcc.Tab(label="Future Scenarios", value="tab-future"),
            ],
        ),

        
        html.Div(
            id="tab-panels",
            children=[
                html.Div(id="panel-water", children=water_tab_layout()),
                html.Div(id="panel-carbon", children=carbon_tab_layout()),
                html.Div(id="panel-tradeoff", children=tradeoff_tab_layout()),
                html.Div(id="panel-state", children=state_tab_layout()),
                html.Div(id="panel-multi", children=multivariate_tab_layout()),
                html.Div(id="panel-hierarchy", children=hierarchy_tab_layout()),
                html.Div(id="panel-corr", children=correlation_tab_layout()),
                html.Div(id="panel-future", children=future_tab_layout()),
            ],
        ),
    ],
)




@app.callback(
    [
        Output("panel-water", "style"),
        Output("panel-carbon", "style"),
        Output("panel-tradeoff", "style"),
        Output("panel-state", "style"),
        Output("panel-multi", "style"),
        Output("panel-hierarchy", "style"),
        Output("panel-corr", "style"),
        Output("panel-future", "style"),
    ],
    Input("tabs", "value"),
)
def switch_tabs(tab):
    def style(show):
        return {"display": "block"} if show else {"display": "none"}

    return (
        style(tab == "tab-water"),
        style(tab == "tab-carbon"),
        style(tab == "tab-tradeoff"),
        style(tab == "tab-state"),
        style(tab == "tab-multi"),
        style(tab == "tab-hierarchy"),
        style(tab == "tab-corr"),
        style(tab == "tab-future"),
    )



@app.callback(
    [Output("water_map", "figure"), Output("water_details", "children")],
    [
        Input("pca_filter", "value"),
        Input("state_filter", "value"),
        Input("fuel_filter", "value"),
        Input("water_map", "clickData"),
    ],
)
def update_water_map(pca_vals, state_vals, fuel_vals, click_data):
    dff = df_map.copy()

    if pca_vals:
        dff = dff[dff["pca_name"].isin(pca_vals)]
    if state_vals:
        dff = dff[dff["plant_state"].isin(state_vals)]
    if fuel_vals:
        dff = dff[dff["fuel_code"].isin(fuel_vals)]

    fig = px.scatter_mapbox(
        dff,
        lat="lat",
        lon="lon",
        size="total_mwh",
        color="water_footprint",
        color_continuous_scale="Viridis",
        mapbox_style="carto-darkmatter",
        zoom=3,
        hover_data=["pca_name", "subbasin", "total_mwh", "water_footprint"],
        title="Water-scarcity-weighted footprint of data center electricity",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))


    if click_data and len(dff) > 0:
        idx = click_data["points"][0]["pointIndex"]
        if 0 <= idx < len(dff):
            row = dff.iloc[idx]
            card = dbc.Card(
                [
                    dbc.CardHeader("Selected subbasin / PCA", className="bg-dark"),
                    dbc.CardBody(
                        [
                            html.H5(row.get("pca_name", "N/A")),
                            html.P(f"Subbasin: {row.get('subbasin', 'N/A')}"),
                            html.P(f"State: {row.get('plant_state', 'N/A')}"),
                            html.P(f"Fuel: {row.get('fuel_code', 'N/A')}"),
                            html.Hr(),
                            html.P(
                                f"Electricity used by data centers: "
                                f"{row.get('total_mwh', 0):,.0f} MWh"
                            ),
                            html.P(
                                f"Water footprint (scarcity-weighted): "
                                f"{row.get('water_footprint', 0):,.0f} m³-eq"
                            ),
                            html.P(
                                f"Scarcity factor: "
                                f"{row.get('scarcity_factor', 0):.2f}"
                            ),
                            html.P(
                                f"Carbon intensity: "
                                f"{row.get('carbon_intensity_tons_per_mwh', 0):.3f} tons/MWh"
                            ),
                        ]
                    ),
                ],
                color="dark",
                inverse=True,
            )
            return fig, card

    return fig, html.Div(
        "Click on a point to see local PCA, subbasin, and footprint details.",
        className="text-muted",
    )




@app.callback(Output("carbon_map", "figure"), Input("tabs", "value"))
def update_carbon_map(_):
    fig = px.scatter_mapbox(
        df_map,
        lat="lat",
        lon="lon",
        size="total_mwh",
        color="carbon_footprint",
        color_continuous_scale="Inferno",  # lighter than Magma at the low end
        mapbox_style="carto-darkmatter",
        zoom=3,
        hover_data=["pca_name", "subbasin", "carbon_footprint", "total_mwh"],
        title="Carbon footprint of data center electricity (per subbasin)",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    return fig




@app.callback(
    Output("tradeoff_scatter", "figure"),
    [Input("tradeoff_color_metric", "value"), Input("tradeoff_logx", "value")],
)
def update_tradeoff(color_metric, log_opts):
    dff = subbasin_df[subbasin_df["total_mwh"] > 0].copy()

    fig = px.scatter(
        dff,
        x="total_mwh",
        y="scarcity_factor",
        size="water_footprint",
        color=color_metric,
        color_continuous_scale="Turbo",
        hover_data=["pca_name", "subbasin", "plant_state"],
        labels={
            "total_mwh": "Electricity used by data centers (MWh)",
            "scarcity_factor": "Water scarcity factor",
            "water_footprint": "Water footprint (m³-eq)",
            "carbon_intensity_tons_per_mwh": "Carbon intensity (tons/MWh)",
            "carbon_footprint": "Carbon footprint (tons CO₂-eq)",
        },
        title="Energy vs Water Scarcity — highlighting risky regions",
    )

    fig.update_traces(
        marker=dict(
            opacity=0.7,
            line=dict(width=0.4, color="white"),
        )
    )
    fig.update_layout(template="plotly_dark")

    if "logx" in (log_opts or []):
        fig.update_xaxes(type="log")

    return fig




@app.callback(Output("state_map", "figure"), Input("state_metric", "value"))
def update_state_map(metric):
    metric_label = {
        "water_footprint": "Water footprint (m³-eq)",
        "carbon_footprint": "Carbon footprint (tons CO₂-eq)",
        "total_mwh": "Total electricity (MWh)",
    }[metric]

    fig = px.choropleth(
        state_df,
        locations="plant_state",
        locationmode="USA-states",
        color=metric,
        color_continuous_scale="Plasma",
        scope="usa",
        labels={metric: metric_label},
        title=f"State-level {metric_label} from data center electricity",
    )
    fig.update_layout(template="plotly_dark")
    return fig




@app.callback(Output("parallel_plot", "figure"), Input("parallel_color_metric", "value"))
def update_parallel(color_metric):
    dims = [
        "total_mwh",
        "water_footprint",
        "carbon_footprint",
        "scarcity_factor",
        "carbon_intensity_tons_per_mwh",
    ]

    fig = px.parallel_coordinates(
        subbasin_df,
        dimensions=dims,
        color=color_metric,
        color_continuous_scale=px.colors.sequential.Viridis,
        labels={
            "total_mwh": "Electricity (MWh)",
            "water_footprint": "Water (m³-eq)",
            "carbon_footprint": "Carbon (tons CO₂-eq)",
            "scarcity_factor": "Scarcity factor",
            "carbon_intensity_tons_per_mwh": "Carbon intensity",
        },
        title="Multivariate patterns across subbasins",
    )
    fig.update_layout(template="plotly_dark")
    return fig




@app.callback(Output("hierarchy_sunburst", "figure"), Input("hierarchy_metric", "value"))
def update_sunburst(metric):
    label = {
        "total_mwh": "Electricity (MWh)",
        "water_footprint": "Water footprint (m³-eq)",
        "carbon_footprint": "Carbon footprint (tons CO₂-eq)",
    }[metric]

    fig = px.sunburst(
        hier_df,
        path=["plant_state", "pca_name", "subbasin"],
        values=metric,
        color=metric,
        color_continuous_scale="Viridis",
        title=f"Hierarchy of {label}: state → PCA → subbasin",
    )
    fig.update_layout(template="plotly_dark")
    return fig




@app.callback(Output("corr_heatmap", "figure"), Input("tabs", "value"))
def update_corr(_):
    metrics = [
        "total_mwh",
        "water_footprint",
        "carbon_footprint",
        "scarcity_factor",
        "carbon_intensity_tons_per_mwh",
    ]
    corr = pca_df[metrics].corr()

    fig = px.imshow(
        corr,
        x=metrics,
        y=metrics,
        color_continuous_scale="RdBu",
        zmin=-1,
        zmax=1,
        title="Correlation between electricity use, water, carbon, and scarcity (PCA level)",
    )
    fig.update_layout(template="plotly_dark")
    return fig



if __name__ == "__main__":
    app.run(debug=True)
