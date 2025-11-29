import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

df = pd.read_csv("final_footprint_dataset.csv")

for col in ["water_footprint", "carbon_footprint", "total_mwh",
            "scarcity_factor", "carbon_intensity_tons_per_mwh"]:
    if col in df.columns:
        df[col] = df[col].fillna(0)

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


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    suppress_callback_exceptions=True
)

app.title = "US Data Center Environmental Explorer"


app.validation_layout = html.Div([
    html.Div(id="tabs-content"),

    # Water tab
    dcc.Dropdown(id="pca_filter"),
    dcc.Dropdown(id="state_filter"),
    dcc.Dropdown(id="fuel_filter"),
    dcc.Graph(id="water_map"),
    html.Div(id="water_details"),

    # Carbon tab
    dcc.Graph(id="carbon_map"),

    # Tradeoff tab
    dcc.Graph(id="tradeoff_scatter"),

    # State tab
    dcc.RadioItems(id="state_metric"),
    dcc.Graph(id="state_map"),
])



def layout():
    return dbc.Container(
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
                        "Interactive exploration of electricity use, water stress, "
                        "and carbon emissions associated with U.S. data centers.",
                        className="text-center text-muted mb-3",
                    )
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
                    dcc.Tab(label="Future Scenarios (Coming Soon)", value="tab-future"),
                ],
            ),

            html.Div(id="tabs-content", className="mt-3"),
        ],
    )


app.layout = layout


def water_tab_layout():
    return dbc.Row([
        dbc.Col([
            html.H5("Filters", className="text-info mb-2"),

            html.Label("PCA"),
            dcc.Dropdown(
                id="pca_filter",
                options=[{"label": p, "value": p} for p in sorted(df_map["pca_name"].dropna().unique())],
                multi=True,
                placeholder="Select PCA(s)",
            ),
            html.Br(),

            html.Label("State"),
            dcc.Dropdown(
                id="state_filter",
                options=[{"label": s, "value": s} for s in sorted(df_map["plant_state"].dropna().unique())],
                multi=True,
                placeholder="Select state(s)",
            ),
            html.Br(),

            html.Label("Fuel Type"),
            dcc.Dropdown(
                id="fuel_filter",
                options=[{"label": f, "value": f} for f in sorted(df_map["primary_fuel"].dropna().unique())],
                multi=True,
                placeholder="Select fuel type(s)",
            ),
        ], width=3),

        dbc.Col([
            dcc.Graph(id="water_map", style={"height": "70vh"}),
            html.Div(id="water_details", className="mt-3"),
        ], width=9)
    ])


def carbon_tab_layout():
    return dbc.Col(
        dcc.Graph(id="carbon_map", style={"height": "80vh"}),
        width=12
    )


def tradeoff_tab_layout():
    return dbc.Col(
        dcc.Graph(id="tradeoff_scatter", style={"height": "80vh"}),
        width=12
    )


def state_tab_layout():
    return dbc.Row([
        dbc.Col([
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
            )
        ], width=2),

        dbc.Col(
            dcc.Graph(id="state_map", style={"height": "80vh"}),
            width=10
        ),
    ])


def future_tab_layout():
    return html.Div([
        html.H4("Future Projections (placeholder)", className="text-info"),
        html.P(
            "Your teammates will plug in Aqueduct 4.0 and the US-AI-Server-Analysis "
            "dataset here to extend water & carbon projections to 2030/2050.",
            className="text-muted"
        ),
    ], className="p-3")


@app.callback(Output("tabs-content", "children"), Input("tabs", "value"))
def render_tab(tab):
    if tab == "tab-water":
        return water_tab_layout()
    if tab == "tab-carbon":
        return carbon_tab_layout()
    if tab == "tab-tradeoff":
        return tradeoff_tab_layout()
    if tab == "tab-state":
        return state_tab_layout()
    return future_tab_layout()


@app.callback(
    [Output("water_map", "figure"), Output("water_details", "children")],
    [
        Input("pca_filter", "value"),
        Input("state_filter", "value"),
        Input("fuel_filter", "value"),
        Input("water_map", "clickData")
    ]
)
def update_water_map(pca_vals, state_vals, fuel_vals, click_data):

    dff = df_map.copy()

    if pca_vals:
        dff = dff[dff["pca_name"].isin(pca_vals)]
    if state_vals:
        dff = dff[dff["plant_state"].isin(state_vals)]
    if fuel_vals:
        dff = dff[dff["primary_fuel"].isin(fuel_vals)]

    # build map
    fig = px.scatter_mapbox(
        dff,
        lat="lat", lon="lon",
        size="total_mwh",
        color="water_footprint",
        color_continuous_scale="Viridis",
        mapbox_style="carto-darkmatter",
        zoom=3,
        hover_data=["pca_name", "subbasin", "total_mwh", "water_footprint"],
        title="Water-scarcity-weighted footprint of data center electricity",
    )

    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))

    # drilldown
    if click_data:
        row = dff.iloc[click_data["points"][0]["pointIndex"]]
        return fig, dbc.Card(
            [
                dbc.CardHeader("Selected Subbasin / PCA", className="bg-dark"),
                dbc.CardBody([
                    html.H5(row.get("pca_name", "N/A")),
                    html.P(f"Subbasin: {row.get('subbasin', 'N/A')}"),
                    html.P(f"State: {row.get('plant_state', 'N/A')}"),
                    html.P(f"Fuel: {row.get('primary_fuel', 'N/A')}"),
                    html.Hr(),
                    html.P(f"Electricity: {row.get('total_mwh', 0):,.0f} MWh"),
                    html.P(f"Water footprint: {row.get('water_footprint', 0):,.0f} m³-eq"),
                    html.P(f"Scarcity factor: {row.get('scarcity_factor', 0):.2f}"),
                    html.P(f"Carbon intensity: {row.get('carbon_intensity_tons_per_mwh', 0):.3f} tons/MWh"),
                ])
            ],
            color="dark", inverse=True
        )

    return fig, html.Div("Click a point for details.", className="text-muted")




@app.callback(Output("carbon_map", "figure"), Input("tabs", "value"))
def update_carbon_map(_):
    fig = px.scatter_mapbox(
        df_map,
        lat="lat", lon="lon",
        size="total_mwh",
        color="carbon_footprint",
        # LIGHTER, NOT BLACKISH
        color_continuous_scale="Inferno",
        mapbox_style="carto-darkmatter",
        zoom=3,
        hover_data=["pca_name", "subbasin", "carbon_footprint", "total_mwh"],
        title="Carbon footprint of data center electricity",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    return fig

@app.callback(Output("tradeoff_scatter", "figure"), Input("tabs", "value"))
def update_tradeoff(_):
    fig = px.scatter(
        df_map,
        x="total_mwh",
        y="scarcity_factor",
        size="water_footprint",
        color="carbon_intensity_tons_per_mwh",
        color_continuous_scale="Turbo",
        hover_data=["pca_name", "subbasin", "plant_state"],
        labels={
            "total_mwh": "Electricity used by data centers (MWh)",
            "scarcity_factor": "Water scarcity factor",
            "carbon_intensity_tons_per_mwh": "Carbon intensity (tons/MWh)",
        },
        title="Energy vs Water Scarcity",
    )
    fig.update_layout(template="plotly_dark")
    return fig


@app.callback(Output("state_map", "figure"), Input("state_metric", "value"))
def update_state_map(metric):
    label = {
        "water_footprint": "Water footprint (m³-eq)",
        "carbon_footprint": "Carbon footprint (tons CO₂-eq)",
        "total_mwh": "Electricity (MWh)",
    }[metric]

    fig = px.choropleth(
        state_df,
        locations="plant_state",
        locationmode="USA-states",
        color=metric,
        color_continuous_scale="Plasma",
        scope="usa",
        labels={metric: label},
        title=f"State-level {label}",
    )
    fig.update_layout(template="plotly_dark")
    return fig


if __name__ == "__main__":
    app.run(debug=True)
