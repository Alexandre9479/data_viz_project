from dash import Dash, html, dcc, Input, Output, State
import pandas as pd
import base64
import io
import plotly.express as px

# Initialize the Dash app
app = Dash(__name__)
server = app.server # NEW LINE: This line is essential for Gunicorn deployment

# --- App Layout ---
app.layout = html.Div(children=[
    html.H1(children='Data Visualization Project'),
    html.Div(children='''
        Upload your CSV or Excel file to get started with visualizations.
    '''),

    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    ),

    html.Div(id='output-data-upload'),

    html.Hr(), # Horizontal rule for separation

    html.Div([
        html.Div("Select X-Axis:", style={'width': '20%', 'display': 'inline-block'}),
        dcc.Dropdown(
            id='xaxis-column',
            options=[],
            value=None,
            placeholder="Select a column for X-axis",
            style={'width': '70%', 'display': 'inline-block', 'verticalAlign': 'middle'}
        )
    ]),
    html.Div([
        html.Div("Select Y-Axis:", style={'width': '20%', 'display': 'inline-block'}),
        dcc.Dropdown(
            id='yaxis-column',
            options=[],
            value=None,
            placeholder="Select a column for Y-axis",
            style={'width': '70%', 'display': 'inline-block', 'verticalAlign': 'middle'}
        )
    ]),
    html.Div([
        html.Div("Select Plot Type:", style={'width': '20%', 'display': 'inline-block'}),
        dcc.Dropdown(
            id='plot-type',
            options=[
                {'label': 'Scatter Plot', 'value': 'scatter'},
                {'label': 'Bar Chart', 'value': 'bar'},
                {'label': 'Line Plot', 'value': 'line'},
            ],
            value='scatter',
            style={'width': '70%', 'display': 'inline-block', 'verticalAlign': 'middle'}
        )
    ]),
    html.Div([
        html.Div("Color By:", style={'width': '20%', 'display': 'inline-block'}),
        dcc.Dropdown(
            id='color-column',
            options=[],
            value=None,
            placeholder="Select a column to color by (optional)",
            style={'width': '70%', 'display': 'inline-block', 'verticalAlign': 'middle'}
        )
    ]),


    dcc.Graph(id='dynamic-graph'),

    dcc.Store(id='stored-data', data={})
])

# --- Callbacks ---

@app.callback(
    Output('output-data-upload', 'children'),
    Output('stored-data', 'data'),
    Output('xaxis-column', 'options'),
    Output('yaxis-column', 'options'),
    Output('color-column', 'options'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified')
)
def parse_contents(contents, filename, date):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            if 'csv' in filename:
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            elif 'xls' in filename:
                df = pd.read_excel(io.BytesIO(decoded))
            else:
                return html.Div(['Please upload a CSV or Excel (.xlsx) file.']), {}, [], [], []
        except Exception as e:
            print(f"Error processing file: {e}")
            return html.Div(['There was an error processing this file. Please check file format.']), {}, [], [], []

        df_json = df.to_json(date_format='iso', orient='split')

        column_options = [{'label': col, 'value': col} for col in df.columns]

        return html.Div([
            html.H5(filename),
            html.H6(f"Last modified: {pd.to_datetime(date, unit='ms')}"),
            html.Hr(),
            html.Div('Raw Data Preview:'),
            html.Table(
                [html.Tr([html.Th(col) for col in df.columns])] +
                [html.Tr([
                    html.Td(df.iloc[i][col]) for col in df.columns
                ]) for i in range(min(len(df), 10))]
            ),
            html.Hr(),
            html.Div('Number of rows: ' + str(len(df))),
            html.Div('Number of columns: ' + str(len(df.columns))),
        ]), df_json, column_options, column_options, column_options
    
    return html.Div('Please upload a file to visualize.'), {}, [], [], []


@app.callback(
    Output('dynamic-graph', 'figure'),
    Input('xaxis-column', 'value'),
    Input('yaxis-column', 'value'),
    Input('plot-type', 'value'),
    Input('color-column', 'value'),
    State('stored-data', 'data')
)
def update_graph(xaxis_col_name, yaxis_col_name, plot_type, color_col_name, stored_data):
    if stored_data and xaxis_col_name and yaxis_col_name:
        df = pd.read_json(stored_data, orient='split')

        title = f'{plot_type.capitalize()} of {yaxis_col_name} vs. {xaxis_col_name}'
        if color_col_name:
            title += f' (Colored by {color_col_name})'

        if plot_type == 'scatter':
            fig = px.scatter(df, x=xaxis_col_name, y=yaxis_col_name, color=color_col_name, title=title)
        elif plot_type == 'bar':
            fig = px.bar(df, x=xaxis_col_name, y=yaxis_col_name, color=color_col_name, title=title)
        elif plot_type == 'line':
            fig = px.line(df, x=xaxis_col_name, y=yaxis_col_name, color=color_col_name, title=title)
        else:
            fig = {}

        return fig
    else:
        return {
            'layout': {
                'title': 'Upload data and select columns to see the graph'
            }
        }


# --- Run the app ---
if __name__ == '__main__':
    app.run(debug=False) # CHANGED THIS LINE