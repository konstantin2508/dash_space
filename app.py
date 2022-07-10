from distutils.log import debug
import genericpath
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

import numpy as np

import requests
import pandas as pd
import plotly.express as px
# import plotly.io as poi
# poi.renderers.default = 'browser'

response = requests.get('http://asterank.com/api/kepler?query={}&limit=2000')
df = pd.json_normalize(response.json())
df = df[df['PER'] > 0]      # отфильтруем экстремальное значение

# print(df.head())

# Создадим дополнительную категориальную переменную (радиус звезды)
bins = [0, 0.8, 1.2, 100]
names = ['small', 'similar', 'bigger']
df['StarSize'] = pd.cut(df['RSTAR'], bins, labels=names)

# Создадим дополнительную категориальную переменную (температура звезды)
tp_bins = [0, 200, 400, 500, 5000]
tp_labels = ['low', 'optimal', 'high', 'extreme']
df['temp'] = pd.cut(df['TPLANET'], tp_bins, labels=tp_labels)

# Создадим дополнительную категориальную переменную (радиус планеты)
rp_bins = [0, 0.5, 2, 4, 100]
rp_labels = ['low', 'optimal', 'high', 'extreme']
df['gravity'] = pd.cut(df['RPLANET'], rp_bins, labels=rp_labels)

# Создаем признак статуса объекта на основании ранее созданных параметров
df['status'] = np.where((df['temp'] == 'optimal') & (df['gravity'] == 'optimal'),
                'promising', None)
df.loc[:, 'status'] = np.where((df['temp'] == 'optimal') & (df['gravity'].isin(['low', 'high'])),
                'chalenging', df['status'])
df.loc[:, 'status'] = np.where((df['gravity'] == 'optimal') & (df['temp'].isin(['low', 'high'])),
                'chalenging', df['status'])
df['status'] = df.status.fillna('extreme')

options = []
for k in names:
    options.append({'label': k, 'value': k})

# Создадим выпадающее меню
star_size_selector = dcc.Dropdown(
    id='star-selector',
    options=options,
    value=['small', 'similar', 'bigger'],   # значения по умолчанию
    multi=True
)



# Строим График, если статический без колбэка
# fig = px.scatter(df, x='RPLANET', y='TPLANET')    # Уже не надо, т.к. есть в колбэке
# fig.show()

# Создаем ползунок
rplanet_selector = dcc.RangeSlider(
    id='range-slider',
    min=min(df['RPLANET']),
    max=max(df['RPLANET']),
    marks={5: '5', 10: '10', 20: '20'},
    step=1,
    value=[min(df['RPLANET']), max(df['RPLANET'])]  # значения по умолчанию
)

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP])


app.layout = html.Div(
    [
        dbc.Row(html.H1('Hello Dash!'),
        style={'margin-bottom': 40}),
        dbc.Row([
            dbc.Col([
                html.Div('Select planet main semi-axis range'),     # Добавляем первый фильтр
                html.Div(rplanet_selector) 
            ],
            width={'size': 2}),
            dbc.Col([
                html.Div('Choise Star Size'),       # Добавляем второй фильтр
                html.Div(star_size_selector)
            ],
            width={'size': 3, 'offset': 1}),
            dbc.Col(
                dbc.Button('Apply', id='submit-val', n_clicks=0, className='mr-2')      # Добавляем кнопку "Применить"
            )
            ],
            style={'margin-bottom': 40}),
        dbc.Row([
            dbc.Col([
                html.Div('Planet Temperature-Distance from the Star'),      # Добавляем первый график
                dcc.Graph(id='dist-temp-chart')  
            ],
            width={'size': 6}),
            dbc.Col([
                html.Div('Position on the Celestial Sphere'),       # Добавляем второй график
                dcc.Graph(id='celestial-chart')
            ])
        ],
        style={'margin-bottom': 40})
    ],
    style={'margin-left': '80px',
    'margin-right': '80px'})



# # Наполнение страницы без бутстрапа
# app.layout = html.Div([
#     html.H1('Hello Dash!'),
#     html.Div(rplanet_selector, style={'width': '400px', 'margin-bottom': '40px'}),
#     html.Div('Choise Star Size'),
#     html.Div(star_size_selector, style={'width': '400px', 'margin-bottom': '40px'}),
#     html.Div('Planets Chart'),
#     dcc.Graph(id='dist-temp-chart'#, figure=fig     # уже не надо
#     )
#     ],
#     style={'margin-left': '80px',
#     'margin-right': '80px'})


# Изменяем график по ползунку
@app.callback(
    Output(component_id='dist-temp-chart', component_property='figure'),
    [Input(component_id='submit-val', component_property='n_clicks')],      # создаем колбэк для кнопки обновления
    [State(component_id='range-slider', component_property='value'),
    State(component_id='star-selector', component_property='value')]    
    # [Input(component_id='range-slider', component_property='value'),      # если без кнопки, то обновляет графики автоматически при изменении фильтров
    # Input(component_id='star-selector', component_property='value')]
)
def update_dist_temp_chart(n, radius_range, star_size):
    chart_data = df[(df['RPLANET'] > radius_range[0]) & (df['RPLANET'] < radius_range[1]) & (df['StarSize'].isin(star_size))]
    fig = px.scatter(chart_data, x='TPLANET', y='A', color='StarSize')
    return fig


@app.callback(
    Output(component_id='celestial-chart', component_property='figure'),
    [Input(component_id='range-slider', component_property='value'),
    Input(component_id='star-selector', component_property='value')]
)
def update_celestial_chart(radius_range, star_size):
    chart_data = df[(df['RPLANET'] > radius_range[0]) & (df['RPLANET'] < radius_range[1]) & (df['StarSize'].isin(star_size))]
    fig = px.scatter(chart_data, x='RA', y='DEC', size='RPLANET', color='status')
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)

