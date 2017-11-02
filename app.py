from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, Select, RadioButtonGroup
from bokeh.plotting import figure
from bokeh.layouts import column, widgetbox
from collections import OrderedDict
import pandas as pd
import requests


BASE_URL = 'http://minikep-db.herokuapp.com/api'

    
class Frequency:
    """Frequencies for radio buttons."""
        
    pairs = OrderedDict([
                ('Annual', 'a'),
                ('Quarterly', 'q'),
                ('Monthly', 'm'),
                ('Daily', 'd')])
    
    letters = list(pairs.values())
    desc = list(pairs.keys())
    
    def get_index(freq):
        """Return *freq* index."""
        return Frequency.letters.index(freq)        
   
    def descriptions():
        """Return list like ['Annual', 'Quarterly', 'Monthly', 'Daily']."""
        return Frequency.desc

    def on_choice(choice: int):
        """Get one letter frequency for *choice* index.        
        
        Args:
            choice (int): integers from 0 to 3 corresponding to radio button
        """
        return Frequency.letters[choice]

#TODO: move this to tests
assert Frequency.descriptions() == ['Annual', 'Quarterly', 'Monthly', 'Daily']
assert [Frequency.on_choice(x) for x in range(4)] == list("aqmd") 
assert Frequency.get_index('q') == 1      
           

def names(freq: str):
    """Get all time series names for a given frequency *freq*."""
    url = f'{BASE_URL}/names/{freq}'
    return requests.get(url).json()


def get_from_api_datapoints(freq, name):
    """Return data for variable *name* and frequency *freq*.
 
    Args:
        freq (str): single letter representing a frequency, ex: 'a'
        name (str): time series name, ex: 'GDP_yoy'

    Returns:
        list of dictionaries like 
        [{'date': '1999-12-31', 'freq': 'a', 'name': 'GDP_yoy', 'value': 106.4},
          ...
          ]
    """
    url = f'{BASE_URL}/datapoints'
    params = dict(freq=freq, name=name, format='json')
    data = requests.get(url, params).json()
    # if parameters are invalid, response is not a jsoned list
    if not isinstance(data, list):
        return []
    return data


def get_time_series(freq, name):
    """Get data as dictionary with 'x' and 'y' keys."""
    data = get_from_api_datapoints(freq, name)
    return dict(x=pd.to_datetime([d['date'] for d in data]),
                y=[d['value'] for d in data])


def get_data_frame(freq, name1, name2):
    """Make pandas Dataframe based on parameters.
    column names will be 
    """
    data1 = get_from_api_datapoints(freq, name1) 
    data2 = get_from_api_datapoints(freq, name2) 
    data1.extend(data2)
    df = pd.DataFrame(data1)
    df.date = pd.to_datetime(df.date)
    df = df.pivot(columns='name', values='value', index='date')
    df.index.name = df.columns.name = None
    return df[[name1, name2]]


def get_column_data_source(freq, name1, name2):
    df = get_data_frame(freq, name1, name2)
    df.columns = ['line1', 'line2']
    return ColumnDataSource(df)

    
def create_radio_buttons(start_freq):
    desc_list = Frequency.descriptions()
    n = Frequency.get_index(start_freq)
    return RadioButtonGroup(labels=desc_list, active=n)

 
def create_selectors(freq, name1, name2):
    freq_names = names(freq)
    sel1 = Select(options=freq_names,
                  value=name1)
    sel2 = Select(options=freq_names,
                  value=name2)
    return (sel1, sel2)


def create_plot(freq, name1, name2):
    src = get_column_data_source(freq, name1, name2)
    plot = figure(plot_width=600, 
                  plot_height=400, 
                  x_axis_type="datetime")
    plot.line(source=src, x='index', y='line1', color='navy')
    plot.line(source=src, x='index', y='line2', color='red')    
    plot.title.text = f'{name1}, {name2}'
    return plot, src


def update_plot(attr, old, new):
    """Bokeh callback function"""
    # step 1. update names selector based on frequency
    selected_freq = Frequency.on_choice(frequency_selector.active) 
    new_names = names(selected_freq)
    name_selector1.options = new_names
    name_selector2.options = new_names
    # step 2. update plot
    selected_indicator1 = name_selector1.value
    selected_indicator2 = name_selector2.value    
    new_src = get_column_data_source(selected_freq, 
                                     selected_indicator1, 
                                     selected_indicator2)
    source.data = new_src.data
    plot.title.text = f'{selected_indicator1}, {selected_indicator2}'


initial_freq = 'q'
initial_names = 'GDP_yoy', 'CPI_rog'  
frequency_selector = create_radio_buttons(initial_freq)
name_selector1, name_selector2 = create_selectors(initial_freq, *initial_names)
plot, source = create_plot(initial_freq, *initial_names)

# core behavior with callbacks        
frequency_selector.on_change('active', update_plot)
name_selector1.on_change('value', update_plot)
name_selector2.on_change('value', update_plot)


# layout
layout = column(widgetbox(frequency_selector, 
                          name_selector1,
                          name_selector2), 
                plot)
curdoc().add_root(layout)
