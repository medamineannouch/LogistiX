import pathlib
import statistics

import dash
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import dash_daq as daq
import json
from dash.exceptions import PreventUpdate
from dash import html
from dash import dcc
from instance import mk_instance, read_data
from pre_clusterer import preclustering
from model import mk_costs, multiple_src, single_src


external_stylesheets = ['styles.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

def mk_data(n_plants=2, n_dcs=20, n_custs=100, n_prods=2, seed=42):
    df = read_data()
    (prods, weight, cust, plnt, dc, dc_ub, demand, plnt_ub, name) = \
        mk_instance(df, n_plants, n_dcs, n_custs, n_prods, seed)
    (tp_cost, del_cost, dc_fc, dc_vc) = mk_costs(plnt, dc, cust)

    data = (weight, cust, plnt, dc, dc_ub, demand, plnt_ub, name, tp_cost, del_cost, dc_fc, dc_vc)
    return data


def jsonize(data):
    (weight, cust, plnt, dc, dc_lb, dc_ub, demand, plnt_ub, name, tp_cost, del_cost, dc_fc, dc_vc) = data
    serialized_data = {
        "weight": weight,
        "cust": cust,
        "plnt": plnt,
        "dc": dc,
        "dc_lb": dc_lb,
        "dc_ub": dc_ub,
        "demand": {str(k): v for k, v in demand.items()},
        "plnt_ub": {str(k): v for k, v in plnt_ub.items()},
        "name": name,
        "tp_cost": {str(k): v for k, v in tp_cost.items()},
        "del_cost": {str(k): v for k, v in del_cost.items()},
        "dc_fc": dc_fc,
        "dc_vc": dc_vc
    }
    return json.dumps(serialized_data)

def unjsonize(data):
    try:
        deserialized_data = json.loads(data)
        demand = {tuple(map(eval, k.split(','))): v for k, v in deserialized_data["demand"].items()}
        plnt_ub = {tuple(map(eval, k.split(','))): v for k, v in deserialized_data["plnt_ub"].items()}
        tp_cost = {tuple(map(eval, k.split(','))): v for k, v in deserialized_data["tp_cost"].items()}
        del_cost = {tuple(map(eval, k.split(','))): v for k, v in deserialized_data["del_cost"].items()}

        return (
            deserialized_data["weight"],
            deserialized_data["cust"],
            deserialized_data["plnt"],
            deserialized_data["dc"],
            deserialized_data["dc_lb"],
            deserialized_data["dc_ub"],
            demand,
            plnt_ub,
            deserialized_data["name"],
            tp_cost,
            del_cost,
            deserialized_data["dc_fc"],
            deserialized_data["dc_vc"]
        )
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format for data")

def solve(data, num_clusters, num_dcs_open, model="multiple source"):
    (weight, cust, plnt, dc, dc_lb, dc_ub, demand, plnt_ub, name, tp_cost, del_cost, dc_fc, dc_vc) = data

    models = {
        "multiple source": multiple_src,
        "single source": single_src
    }
    k = list(models.keys())[0]
    TIME_LIM = 300  # allow gurobi to use 5 minutes
    print(f"*** new instance, {len(plnt)} plants + {len(dc)} dc's + {len(cust)} customers ***")
    print(f"***** dc's clustered into {len(num_clusters)} groups, for choosing {num_dcs_open} dc's")
    print(f"* using {k} model *")
    model = models[k](weight, cust, num_clusters, dc_ub, plnt, plnt_ub,
                      demand, tp_cost, del_cost, dc_fc, dc_vc, num_dcs_open)
    model.setParam('TimeLimit', TIME_LIM)
    model.optimize()
    x,y = model.__data

    dcs = [i for i in num_clusters if y[i].X > .5]
    print("solution:", dcs)
    return dcs


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([

    html.Div([
              html.H1(children='Optimization of Logistics Network', style={'textAlign': 'center'}),
              html.P("Welcome to the optimization application web page.", style={'textAlign': 'center'}),

              html.Label('Number of Plants:'),
              dcc.Input(type='number', id='num-plants', value=5, style={'marginBottom': '10px'}),

              html.Label('Number of Distribution Centers:'),
              dcc.Input(type='number', id='num-dc', value=3, style={'marginBottom': '10px'}),

              html.Label('Number of Customers:'),
              dcc.Input(type='number', id='num-customers', value=10, style={'marginBottom': '10px'}),

              html.Label('Number of Products:'),
              dcc.Input(type='number', id='num-products', value=5, style={'marginBottom': '10px'}),

              html.Label('Seed:'),
              dcc.Input(type='number', id='seed', value='42', style={'marginBottom': '10px'}),

              html.Label('Number of Clusters:'),
              dcc.Input(type='number', id='num-clusters', value=2, style={'marginBottom': '10px'}),

              html.Label('Number of DCs to Open:'),
              dcc.Input(type='number', id='num-dcs-open', value=1, style={'marginBottom': '10px'}),

              html.Button('Submit', id='submit-button', n_clicks=0, style={'marginBottom': '10px','marginLeft': '30px'}),

              html.Div(id='output')], style={'width': '48%', 'float': 'left', 'display': 'inline-block'}),
    html.Div([
            dcc.Graph(id='example-map')
        ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
    ]
                        )

# Callback to retrieve the form data on button click
@app.callback(Output('output', 'children'),
              [Input('submit-button', 'n_clicks')],
              [Input('num-plants', 'value'),
               Input('num-dc', 'value'),
               Input('num-customers', 'value'),
               Input('num-products', 'value'),
               Input('seed', 'value'),
               Input('num-clusters', 'value'),
               Input('num-dcs-open', 'value')])



def init_data(n_clicks, n_plants, n_dcs, n_custs, n_prods, seed, num_clusters, num_dcs_open):
    if n_clicks is None:
        raise PreventUpdate

    if any(v is None for v in [n_plants, n_dcs, n_custs, n_prods, seed, num_clusters, num_dcs_open]):
        return "Incomplete form, please fill in all values", None

    try:
        data = mk_data(n_plants, n_dcs, n_custs, n_prods, seed)
        jdata = jsonize(data)
        return f'Data created from the form inputs', jdata
    except Exception as e:
        return f'Error: {str(e)}', None


def update_map(n_clicks, data, num_clusters, num_dcs_open):


    if n_clicks is None or data is None:
        raise PreventUpdate

    data = unjsonize(data)
    (weight, cust, plnt, dc, dc_ub, demand, plnt_ub, name, tp_cost, del_cost, dc_fc, dc_vc) = data

    lats, lons = zip(*[cust[i] for i in cust])
    lat_center = statistics.mean(lats)
    lon_center = statistics.mean(lons)
    dc_lats, dc_lons = zip(*[dc[i] for i in dc])
    p_lats, p_lons = zip(*[plnt[i] for i in plnt])


    # clustering part
    print(f'clustering {num_clusters}...')
    prods = weight.keys()
    cluster_dc = preclustering(cust, dc, prods, demand, num_clusters)
    cdc_lats, cdc_lons = zip(*[dc[i] for i in cluster_dc])
    print("cluster_dc:", cluster_dc)
    print("done.")

    # optimization part
    print(f'optimizing {num_dcs_open}...')
    opt_dc = solve(data, cluster_dc, num_dcs_open)
    odc_lats, odc_lons = zip(*[dc[i] for i in opt_dc])
    print("opt_dc:", opt_dc)
    print("done.")
    # Dummy map with markers based on form input (replace with actual logic)
    trace = [
        go.Scattermapbox(
            lat=p_lats,
            lon=p_lons,
            text=[i for i in plnt],
            mode="markers",
            marker={"color": "black", "size": 11, "opacity": .9},
            name="Plant",

        ),
        go.Scattermapbox(
            lat=lats,
            lon=lons,
            text=[i for i in cust],
            mode="markers",
            marker={"color": "white", "size": 6, "opacity": 1.},
            name="Customer",
            # selectedpoints=selected_index,
            # customdata=text,
        ),
        go.Scattermapbox(
            lat=dc_lats,
            lon=dc_lons,
            text=[i for i in dc],
            mode="markers",
            marker={"color": "green", "size": 8, "opacity": 0.9},
            name="DC",
        ),
        go.Scattermapbox(
            lat=cdc_lats,
            lon=cdc_lons,
            text=[i for i in cluster_dc],
            mode="markers",
            marker={"color": "red", "size": 9, "opacity": 0.9},
            name="DC-clustered",
        ),
        go.Scattermapbox(
            lat=odc_lats,
            lon=odc_lons,
            text=[i for i in opt_dc],
            mode="markers",
            marker={"color": "yellow", "size": 10, "opacity": 0.9},
            name="Optimum DCs",
        ),
    ]
    layout = go.Layout(
        title='Example Map',
        autosize=True,
        hovermode='closest',
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=0, lon=0),  # Center of the map
            zoom=2,  # Initial zoom level
        ),
    )

    return {'data': [trace], 'layout': layout}


if __name__ == "__main__":
    app.run_server(debug=True)

