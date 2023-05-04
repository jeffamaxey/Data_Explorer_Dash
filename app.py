import re

import dash
from dash import dcc, html, dash_table
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px

import utils.dash_reusable_components as drc
import utils.mathutils as mu

import os
import sys
import pandas as pd
import copy
import webbrowser
from datetime import datetime
from warnings import warn
from threading import Timer


app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)
app.config['suppress_callback_exceptions'] = True
app.title = "Data Exploration Viewer"
server = app.server


title_text = "Data Exploration Viewer"
default_page_size = 25 # Default number of table rows to display
max_num_bars = 50 # The maximum number of bars to display on the bar plots

# Use these to track current application state
full_data_path = None
full_data_prefix = None
global_page_current = None
global_page_size_table = None
global_sort_by = None
global_filter_query = None
global_page_size = None

# If Using Data Files with Known Structure, Can Define the Structure Like This
# This will help the application use the proper dtypes for the given columns, and
# help with column ordering in the displayed table
# (These will be passed to the read_df() function when used)
# selected_earning_data_usable_cols = [
#     'Category',
#     'Name',
#     'ASIN',
#     'Seller',
#     'Date Shipped',
#     'Price($)',
#     'Items Shipped',
#     'Returns',
#     'Revenue($)',
#     'Ad Fees($)'
# ]
#
# selected_earning_data_usable_cols_to_dtype = {
#     'Category': 'string',
#     'Name': 'string',
#     'ASIN': 'string',
#     'Seller': 'string',
#     'Date Shipped': 'datetime64',
#     'Price($)': 'float64',
#     'Items Shipped': 'int64',
#     'Returns': 'int64',
#     'Revenue($)': 'float64',
#     'Ad Fees($)': 'float64'
# }
#
#
#
# selected_orders_data_usable_cols = [
#     'id',
#     'Category',
#     'Name',
#     'ASIN',
#     'Qty',
#     'Price',
#     'Date',
#     'Link_Type',
#     'Indirect_Sales',
#     'Device_Type_Group'
# ]
#
# selected_orders_data_usable_cols_to_dtype = {
#     'id': 'string',
#     'Category': 'string',
#     'Name': 'string',
#     'ASIN': 'string',
#     'Qty': 'int64',
#     'Price': 'int64',
#     'Date': 'datetime64',
#     'Link_Type': 'string',
#     'Indirect_Sales': 'string',
#     'Device_Type_Group': 'string'
# }



#########################################################################################################################
#########################################################################################################################
#########################################################################################################################
# DATA LOADING



def table_type(df_column, col_name=None):
    # Note - this only works with Pandas >= 1.0.0
    t = 'any'

    if sys.version_info < (3, 0):  # Pandas 1.0.0 does not support Python 2
        return 'any'
    elif (str(df_column.dtype).startswith('date')):
        return 'datetime'
    elif (str(df_column.dtype).startswith('object') or
                str(df_column.dtype).startswith('str')):
        return 'text'
    elif (str(df_column.dtype).startswith('int') or
                str(df_column.dtype).startswith('float')):
        return 'numeric'
    else:
        return 'any'




def read_df(path, dtype_dict=None, col_order=None):

    if(path.endswith('.csv')):
        df = pd.read_csv(path, sep=",", encoding='Latin-1')
    elif(path.endswith('.xls') or path.endswith('.xlsm') or path.endswith('.xlsx')):
        df = pd.read_excel(path)

    # REMOVE UNNAMED COLUMNS
    df = df[[c for c in df.columns if not c.lower().startswith("unnamed")]]


    if dtype_dict is None:
        warn(f"READING WITHOUT DTYPES ---{str(path)}")
        # One last try to convert date strings to datetime
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_datetime(df[col])
                except ValueError:
                    pass


    else:
        for k, v in dtype_dict.items():
            try:
                if (v == 'string'):
                    df[k] = df[k].astype('string')
                elif(v in ['int64', 'float64', 'int32', 'float32', 'double']):
                    df[k] = pd.to_numeric(df[k], errors='coerce')
                elif('date' in v):
                    df[k] = pd.to_datetime(df[k], errors='coerce')
                else:
                    raise Exception(f"INVALID DTYPE GIVEN FOR COLUMN --- {str(k)}")
            except Exception as e:
                warn(str(e))


    if (col_order is None):
        warn(f"READING WITHOUT COLUMN ORDERING --- {str(path)}")
    else:
        try:
            df = df[col_order]
        except:
            warn(f"COULDN'T APPLY COLUMN ORDERING --- {str(path)}")

    return df


def get_file_path_options(path):
    return [{"label": x, "value": x} for x in [file for file in os.listdir(path) if
                                                   file.endswith('.csv') or
                                                   file.endswith('.xls') or
                                                   file.endswith('.xlsm') or
                                                   file.endswith('.xlsx')]]

# END DATA LOADING
#########################################################################################################################
#########################################################################################################################
#########################################################################################################################


df = pd.DataFrame.from_dict({})
df_path = None
global_group_by = None
global_agg = None

app.layout = html.Div(
    children=[
        # .container class is fixed, .container.scalable is scalable
        html.Div(
            className="banner",
            children=[
                # Change App Name here
                html.Div(
                    className="container scalable",
                    children=[
                        # Change App Name here
                        html.H2(
                            id="banner-title",
                            children=[
                                html.A(
                                    title_text,
                                    # href="",
                                    style={
                                        "text-decoration": "none",
                                        "color": "inherit",
                                    },
                                )
                            ],
                        ),
                        html.A(
                            id="banner-logo",
                            children=[
                                html.Img(src=app.get_asset_url("dash-logo-new.png"))
                            ],
                            href="https://plot.ly/products/dash/",
                        ),
                    ],
                )
            ],
        ),
        html.Div(
            id="body",
            className="container scalable",
            children=[
                html.Div(
                    id="app-container",
                    # className="row",
                    children=[
                        html.Div(
                            # className="three columns",
                            id="left-column",
                            style={"min-width": "25%", "max-width": "35%"},
                            children=[
                                drc.Card(
                                    id="first-card",
                                    children=[
                                        drc.NamedInput(
                                            name="Data Path",
                                            id="data-path",
                                            type="url",
                                            placeholder=os.getcwd(),
                                            debounce=True
                                        ),
                                        drc.NamedDropdown(
                                            name="Select Dataset",
                                            id="dropdown-select-dataset",
                                            options=get_file_path_options(os.getcwd()),
                                            clearable=False,
                                            searchable=True,
                                            value="",
                                        ),
                                        drc.NamedDropdown(
                                            name="Group By",
                                            id="group-by",
                                            options=[],
                                            value=None,
                                            clearable=False,
                                            searchable=False,
                                            multi=True
                                        ),
                                        drc.NamedDropdown(
                                            name="Aggregation Method",
                                            id="aggregate",
                                            options=["Count", "Sum", "Mean", "Standard Deviation", "Variance", "Min", "Max"],
                                            value="Count",
                                            clearable=False,
                                            searchable=False,
                                            multi=False,

                                        ),
                                        drc.NamedInput(
                                            name="Page Size",
                                            id="page-size-selection",
                                            type="number",
                                            placeholder=10,
                                            value=10,
                                            debounce=True,
                                            min=1,
                                            max=500
                                        ),
                                    ],
                                ),
                                drc.Card(
                                    id="button-card",
                                    children=[
                                        drc.NamedSlider(
                                            name="Max Number Plot Bars",
                                            id="max-plot-bars",
                                            min=0,
                                            max=max_num_bars,
                                            value=10,
                                            step=1,
                                            marks={
                                                0: '0',
                                                10: '10',
                                                20: '20',
                                                30: '30',
                                                40: '40',
                                                50: '50'
                                            },
                                            tooltip={"placement": "bottom", "always_visible": False}
                                        ),
                                    ],
                                )
                            ],
                        ),
                        html.Div([
                            html.H3(
                                "Select a Dataset",
                                id="data-title",
                                # href="",
                                style={
                                    "text-decoration": "none",
                                    "color": "inherit",
                                }
                            ),
                            html.Button(
                                "Download Filtered Data",
                                id="download-filtered-data-button",
                                disabled=True,
                                # style={"padding": "0px 10px 25px 25px"}
                                style={"margin-right": "10px", "margin-bottom": "10px"}
                            ),
                            html.Div(
                                html.A(
                                    "",
                                    id="data-filter-query",
                                    # href="",
                                    style={
                                        "text-decoration": "none",
                                        "color": "inherit",
                                    }
                                )
                            ),
                            html.Div(
                                html.A(
                                    "Filtering Documentation",
                                    id="data-filter-link",
                                    href="https://dash.plotly.com/datatable/filtering",
                                    style={
                                        "text-decoration": "none",
                                        "color": "blue",
                                        "text-decoration": "underline",
                                        "font-size": 12
                                    }
                                )
                            ),
                            dash_table.DataTable(
                                id='datatable-interactivity',
                                columns=[
                                    {'name': i, 'id': i, 'deletable': False} for i in df.columns
                                    # omit the id column
                                    # if i != 'id'
                                ],
                                data=df.to_dict('records'),
                                editable=True,
                                filter_action="native",
                                sort_action="native",
                                sort_mode='multi',
                                row_selectable=False,
                                row_deletable=False,
                                selected_rows=[],
                                page_action='native',
                                page_current=0,
                                page_size=default_page_size,
                                style_data={
                                    'whiteSpace': 'normal',
                                    'height': 'auto',
                                    # 'color': 'white',
                                    'backgroundColor': '#2A2E3C'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': '#3B4052',
                                    }
                                ],
                                style_header={
                                    'backgroundColor': '#2A2E3C',
                                    # 'color': 'black',
                                    'fontWeight': 'bold'
                                }
                            ),
                            html.Div(id='datatable-interactivity-container'),
                            dcc.Download(id="download"),
                            dcc.Download(id="download-selected")
                        ])
                    ],
                ),
            ]
        )])



@app.callback(
    Output("download", "data"),
    Input("download-filtered-data-button", "n_clicks"),
    State("data-path", "value"),
    State("dropdown-select-dataset", "value"),
    State("group-by", "value"),
    State("aggregate", "value"),
    State("datatable-interactivity", "data"),
    State("datatable-interactivity", "derived_virtual_indices")
)
def on_download_filter_data_button_pressed(n_clicks, path, file, group_by, aggregation_method, data, virtual_row_ids):

    if(virtual_row_ids is not None):
        virtual_row_ids = [int(id) for id in virtual_row_ids]
    else:
        raise PreventUpdate


    if(data is None or len(data) == 0):
        raise PreventUpdate


    df_tmp = pd.DataFrame.from_dict(data).iloc[virtual_row_ids]

    # def extract_hyperlink(s):
    #     hyperlinked_text_re = re.compile(r'\[(?P<HyperlinkedText>.+)\]\(https://www.amazon.com/dp/.*\)')
    #     m = hyperlinked_text_re.match(str(s))
    #     if (m is not None):
    #         s = m.group("HyperlinkedText")
    #     return s

    #df_tmp = df_tmp.applymap(extract_hyperlink)

    filename = file[:-4] + '___' + datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + file[4:]
    return dcc.send_data_frame(df_tmp.to_csv, filename)



# Update Options Each Time a New Value is Selected
@app.callback(
    Output("dropdown-select-dataset", "options"),
    [Input("data-path", "value"),
     Input("dropdown-select-dataset", "value")]
)
def on_change_data_path(path, _):
    return get_file_path_options(path)




@app.callback(
    Output("datatable-interactivity", "columns"),
    Output("datatable-interactivity", "data"),
    Output("datatable-interactivity", "derived_virtual_selected_rows"),
    Output("datatable-interactivity", "page_current"),
    Output("datatable-interactivity", "page_size"),
    Output("data-title", "children"),
    Output("group-by", "options"),
    Output("group-by", "value"),
    Output("aggregate", "options"),
    Output("aggregate", "value"),
    Output("download-filtered-data-button", "disabled"),
    Output("data-filter-query", "children"),
    Output("datatable-interactivity", "filter_query"),
    Input("data-path", "value"),
    Input("dropdown-select-dataset", "value"),
    Input("group-by", "value"),
    Input("aggregate", "value"),
    Input('datatable-interactivity', "derived_virtual_data"),
    Input('datatable-interactivity', "derived_virtual_selected_rows"),
    Input("page-size-selection", "value"),
    Input("datatable-interactivity", "page_size"),
    Input("datatable-interactivity", "filter_query")
)
def on_select_data(path, file, group_by, aggregation_method, rows, derived_virtual_selected_rows, selected_page_size, table_page_size, filter_query):
    global global_group_by
    global global_agg

    if(str(global_group_by) != str(group_by) or str(global_agg) != str(aggregation_method)):
        derived_virtual_selected_rows = []

    global_group_by = group_by
    global_agg = aggregation_method


    df_tmp, new_df = get_filtered_df(path, file, group_by, aggregation_method)

    data_title = f"Examining: {str(file)}"

    if(new_df):
        filter_query = ""


    if (filter_query is not None and len(filter_query) > 0):
        data_filter_query_text = f"Current Filter Query: {str(filter_query)}"
    else:
        data_filter_query_text = ""


    return (
        reset_table(df_tmp, table_page_size, selected_page_size, [])
        + [data_title]
        + reset_chart_x_dropdown(df)
        + reset_aggregate()
        + [False]
        + [data_filter_query_text]
        + [filter_query]
        if new_df
        else reset_table(
            df_tmp,
            table_page_size,
            selected_page_size,
            selected_rows=derived_virtual_selected_rows,
        )
        + [data_title]
        + reset_chart_x_dropdown(df, group_by)
        + reset_aggregate(aggregation_method)
        + [False]
        + [data_filter_query_text]
        + [filter_query]
    )



# Output("datatable-interactivity", "columns"),
# Output("datatable-interactivity", "data"),
# Output("datatable-interactivity", "derived_virtual_selected_rows"),
# Output("datatable-interactivity", "page_current"),
# Output("datatable-interactivity", "page_size"),
def reset_table(df, table_page_size, selected_page_size, selected_rows=[]):

    page_size = selected_page_size


    columns=[
                  {'name': i, 'id': i, 'deletable': False, 'type': table_type(df[i], i), 'presentation': 'markdown'} for i in df.columns
                  # omit the id column
                  # if i != 'id'
              ]
    data = df.to_dict('records')
    selected_rows = selected_rows
    page_current = 0
    return [columns, data, selected_rows, page_current, page_size]


    # Output("group-by", "options"),
    # Output("group-by", "value")
def reset_chart_x_dropdown(df=None, pass_through=[]):
    #options = [c for c in df.columns if table_type(df[c]) == 'text'] # If we only want to be able to group on categorical vars
    options = list(df.columns)
    return [options, pass_through]



def reset_chart_y_dropdown(df=None):
    options = [c for c in df.columns if table_type(df[c]) in ['numeric', 'any'] and 'date' not in str(df.dtypes[c])]
    return [options, []]



def reset_aggregate(value="Count"):
    options = ["Count", "Sum", "Mean", "Standard Deviation", "Variance", "Min", "Max"]
    return [options, value]




def get_filtered_df(path, file, group_by, aggregation_method, add_hyperlinks=True):
    global df
    global df_path

    try:
        new_df = df_path != os.path.join(path, file)
        df_path = os.path.join(path, file)
    except:
        new_df = False

    if (path is None or file is None):
        raise PreventUpdate

    full_data_path = os.path.join(path, file)

    if (not os.path.exists(full_data_path) or
            os.path.isdir(full_data_path)):
        raise PreventUpdate

    try:
        # If you know the data structure, do this
        # if ('order' in file):
        #     df = read_df(full_data_path,
        #                  dtype_dict=selected_orders_data_usable_cols_to_dtype,
        #                  col_order=selected_orders_data_usable_cols)
        # elif ('earning' in file):
        #     df = read_df(full_data_path,
        #                  dtype_dict=selected_earning_data_usable_cols_to_dtype,
        #                  col_order=selected_earning_data_usable_cols)
        # else:
        #     df = read_df(full_data_path)
        df = read_df(full_data_path)
    except:
        raise Exception("Cannot Load CSV File at: ", full_data_path)



    # ADD HYPERLINKS TO NAME COLUMN
    # if(add_hyperlinks and 'Name' in df.columns and 'ASIN' in df.columns):
    #     df['Name'] = (['[']*len(df)) + df['Name'].astype(str) + (['](https://www.amazon.com/dp/']*len(df)) + df['ASIN'].astype(str) + ([')']*len(df))


    if (new_df):
        group_by = []

    if (
        group_by is None
        or len(group_by) == 0
        or aggregation_method is None
        or len(aggregation_method) == 0
    ):
        df_tmp = df


    elif (aggregation_method == "Count"):
        df_tmp = df.groupby(by=group_by, as_index=False).size()
    elif (aggregation_method == "Mean"):
        df_tmp = df.groupby(by=group_by, as_index=False).mean()
    elif (aggregation_method == "Standard Deviation"):
        df_tmp = df.groupby(by=group_by, as_index=False).std()
    elif (aggregation_method == "Min"):
        df_tmp = df.groupby(by=group_by, as_index=False).min()
    elif (aggregation_method == "Max"):
        df_tmp = df.groupby(by=group_by, as_index=False).max()
    elif (aggregation_method == "Variance"):
        df_tmp = df.groupby(by=group_by, as_index=False).var()
    elif (aggregation_method == "Sum"):
        df_tmp = df.groupby(by=group_by, as_index=False).sum()
    return df_tmp, new_df





@app.callback(
    Output('datatable-interactivity-container', "children"),
    Input('datatable-interactivity', "derived_virtual_data"),
    Input('datatable-interactivity', "derived_virtual_selected_rows"),


    Input("data-path", "value"),
    Input("dropdown-select-dataset", "value"),
    Input("group-by", "value"),
    Input("aggregate", "value"),
    Input("max-plot-bars", "value")
)
def update_graphs(rows, derived_virtual_selected_rows, path, file, group_by, aggregation_method, max_plot_bars):
    # When the table is first rendered, `derived_virtual_data` and
    # `derived_virtual_selected_rows` will be `None`. This is due to an
    # idiosyncrasy in Dash (unsupplied properties are always None and Dash
    # calls the dependent callbacks when the component is first rendered).
    # So, if `rows` is `None`, then the component was just rendered
    # and its value will be the same as the component's dataframe.
    # Instead of setting `None` in here, you could also set
    # `derived_virtual_data=df.to_rows('dict')` when you initialize
    # the component.
    try:
        if(max_plot_bars == 0):
            return []

        if(group_by is None or len(group_by)==9 or
           aggregation_method is None or len(group_by)==0):
            # NO CHILDREN
            return []

        global df

        df_tmp, new_df = get_filtered_df(path, file, group_by, aggregation_method)

        if derived_virtual_selected_rows is None:
            derived_virtual_selected_rows = []

        dff = df_tmp if rows is None else pd.DataFrame(rows)

        if(len(group_by) > 1):
            chart_x_column = "___".join(group_by)
            dff[chart_x_column] = dff[group_by].agg('--'.join, axis=1)
            dff = dff[[c for c in dff.columns if c not in group_by]]

        else:
            chart_x_column = group_by[0]


        colors = ['#7FDBFF' if i in derived_virtual_selected_rows else '#0074D9'
                  for i in range(len(dff))]

        figs = []

        graphs = [
            html.Div(
                dcc.Graph(
                    id=column,
                    # figure={
                    #     "data": [
                    #         {
                    #             "x": dff[chart_x_column][:max_plot_bars],
                    #             "y": dff[column][:max_plot_bars],
                    #             "type": "bar",
                    #             "marker": {"color": colors},
                    #         }
                    #     ],
                    #     "layout": {
                    #         "xaxis": {"automargin": True},
                    #         "yaxis": {
                    #             "automargin": True,
                    #             "title": {"text": column}
                    #         },
                    #         "height": 250,
                    #         "margin": {"t": 100, "l": 10, "r": 10},
                    #     },
                    # },
                    figure=go.Figure(
                        data=px.bar(
                            pd.DataFrame.from_dict(
                                                        {
                                                            chart_x_column: dff[chart_x_column][:max_plot_bars],
                                                            column: dff[column][:max_plot_bars]
                                                        }
                                                   ),
                            x=chart_x_column,
                            y=column,
                            #x=dff[chart_x_column][:max_plot_bars],
                            #y=dff[column][:max_plot_bars],
                            #width=[0.8, 0.8, 0.8, 3.5, 4] # customize width here,
                            color_discrete_sequence=colors[:max_plot_bars],
                            title=column
                        )
                    )
                ),
                style={'marginBottom': 50, 'marginTop': 25}
            )
            # check if column exists - user may have deleted it
            # If `column.deletable=False`, then you don't
            # need to do this check.

            for column in list(dict.fromkeys(list(df.columns) + ['size', 'count'])) if
            ((column in dff.columns and table_type(dff[column]) in ['numeric', 'any']) or
            (column in dff.columns and column == ['size', 'count'])) and
            column not in group_by
        ]

        for fig in [g.children.figure for g in graphs]:
            #print(type(fig))
            fig.update_layout({
                'plot_bgcolor': 'rgba(0, 0, 0, 0)',
                'paper_bgcolor': 'rgba(0, 0, 0, 0)',
                'font_family': "Arial",
                'font_color': "#a5b1cd",
                'font_size': 20,
                'title_font_color': "#a5b1cd",
                'legend_title_font_color': "#a5b1cd"
            },
            xaxis={'tickfont': {'size': mu.lerp(16, 12, min(len(dff), max_plot_bars)/max_num_bars)}},
            title={'x': 0.5, 'xanchor': 'center'}
            )

    except Exception as e:
        print("\n\n\n")
        warn(str(e))
        raise e
    return graphs





#     Output('datatable-interactivity', "page_current"),
#     Output('datatable-interactivity', 'page_size'),
#     Input("page-size-selection", "value"),
#     Input('datatable-interactivity', 'page_size')
def set_page_size(new_page_size, old_page_size):
    if (new_page_size == old_page_size):
        raise PreventUpdate
    return 0, new_page_size


def open_browser():
    try:
        webbrowser.open("http://localhost:8050", new=0, autoraise=True)
    except:
        warn("Couldn't automatically open browser window --- Please open a browser window and navigate to" + \
             " http://localhost:8050 in order to use the application")

# Running the server
if __name__ == "__main__":
    Timer(1, open_browser).start()
    app.run_server(debug=False)


