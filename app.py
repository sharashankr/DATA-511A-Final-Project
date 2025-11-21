import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output


df = pd.read_csv("dc_with_air_quality.csv")


df.columns = df.columns.str.lower()


app = Dash(__name__)


app.layout = html.Div([
    
    html.H1("Environmental Impact of U.S. Data Centers", style={'textAlign': 'center'}),
    
    html.Div([
        #Sidebar filters
        html.Div([
            html.H3("Filters"),
            
            #State filter
            dcc.Dropdown(
                id='state_filter',
                options=[{'label': s, 'value': s} for s in sorted(df['state'].unique())],
                multi=True,
                placeholder="Select State(s)"
            ),
            
            #Operator filter
            dcc.Dropdown(
                id='operator_filter',
                options=[{'label': o, 'value': o} for o in sorted(df['operator'].dropna().unique())],
                multi=True,
                placeholder="Select Operator(s)"
            ),

            #Status filter
            dcc.Dropdown(
                id='status_filter',
                options=[{'label': s, 'value': s} for s in sorted(df['status'].dropna().unique())],
                multi=True,
                placeholder="Select Status"
            ),
            
            #Pollution filter
            dcc.Dropdown(
                id='pollutant_filter',
                options=[
                    {'label': 'PM2.5', 'value': 'pm2.5__local_conditions'},
                    {'label': 'Ozone', 'value': 'ozone'},
                    {'label': 'NO2', 'value': 'nitrogen_dioxide_no2'},
                ],
                value='pm2.5__local_conditions',
                placeholder="Select Pollutant"
            ),
        ], style={'width': '25%', 'display': 'inline-block', 'verticalAlign': 'top', 
                  'padding': '20px', 'backgroundColor': '#f8f8f8'}),
        
      
        html.Div([
            dcc.Graph(id='map'),
            dcc.Graph(id='scatter'),
            dcc.Graph(id='bar_chart'),
        ], style={'width': '73%', 'display': 'inline-block'})
    ]),
])


@app.callback(
    Output('map', 'figure'),
    Output('scatter', 'figure'),
    Output('bar_chart', 'figure'),
    Input('state_filter', 'value'),
    Input('operator_filter', 'value'),
    Input('status_filter', 'value'),
    Input('pollutant_filter', 'value')
)
def update_dashboard(state, operator, status, pollutant_col):

    filtered = df.copy()

   
    if state:
        filtered = filtered[filtered['state'].isin(state)]
    if operator:
        filtered = filtered[filtered['operator'].isin(operator)]
    if status:
        filtered = filtered[filtered['status'].isin(status)]


    map_fig = px.scatter_mapbox(
        filtered,
        lat="lat", lon="long",
        color=pollutant_col,
        size="facility_size_sq_ft" if "facility_size_sq_ft" in filtered.columns else None,
        hover_name="operator",
        hover_data=["state", "county", pollutant_col, "status"],
        zoom=3,
        mapbox_style="carto-positron",
        color_continuous_scale="Viridis",
        title="Data Centers Across the U.S."
    )


    scatter_fig = px.scatter(
        filtered,
        x="facility_size_sq_ft" if "facility_size_sq_ft" in filtered.columns else filtered.index,
        y=pollutant_col,
        color="operator",
        hover_data=["state", "county", "status"],
        title="Pollution vs Facility Size"
    )

    # ----------------- BAR CHART -----------------
    bar_df = filtered.groupby("state").size().reset_index(name="count")
    bar_fig = px.bar(
        bar_df,
        x="state", y="count",
        title="Number of Data Centers per State",
        color="state"
    )

    return map_fig, scatter_fig, bar_fig


if __name__ == "__main__":
    app.run(debug=True)
