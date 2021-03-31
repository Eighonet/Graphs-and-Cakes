import pandas as pd
import json
from tqdm import tqdm
import plotly.express as px
from pathlib import Path  
import seaborn as sns

def get_color(number):
    color = sns.color_palette("deep")[number]
    actual_rgb = tuple(int(255*x) for x in color)
    actual_hex = '#%02x%02x%02x' % actual_rgb
    return actual_hex

def cast_to_string(routes_property):
    return [str(int).replace("[", "").replace("]", "") for int in routes_property]

class GIS_processing():
    
    df = pd.DataFrame()
    df_clear = pd.DataFrame()
    dfs = pd.DataFrame()
    
    def __init__(self) -> None:
        pass
    
    def add_additionals(self, filepath) -> None:
        self.df = pd.read_csv(filepath)
        route_type = []
        start_point_meters = []
        finish_point_meters = []
        start_point_part = []
        finish_point_part = []
        instruction_type = []
        
        for i in tqdm(range(len(self.df["drivingDirection_json"]))):
            route_type.append(json.loads(self.df["drivingDirection_json"][i])["type"])
            start_point_meters.append(json.loads(self.df["drivingDirection_json"][i])['start_point']['meters'])
            finish_point_meters.append(json.loads(self.df["drivingDirection_json"][i])['finish_point']['meters'])
            start_point_part.append(json.loads(self.df["drivingDirection_json"][i])['start_point']['part'])
            finish_point_part.append(json.loads(self.df["drivingDirection_json"][i])['finish_point']['part'])
            if ('instruction' in json.loads(self.df["drivingDirection_json"][i])):
                instruction_type.append(json.loads(self.df["drivingDirection_json"][i])['instruction']['type'])
            else:
                 instruction_type.append(-1)
        route_type = pd.DataFrame(cast_to_string(route_type), columns=['route_type'])
        start_point_meters = pd.DataFrame(cast_to_string( start_point_meters), columns=['start_point_meters'])
        finish_point_meters = pd.DataFrame(cast_to_string(finish_point_meters), columns=['finish_point_meters'])
        start_point_part = pd.DataFrame(cast_to_string(start_point_part), columns=[' start_point_part'])
        finish_point_part = pd.DataFrame(cast_to_string(finish_point_part), columns=['finish_point_part'])
        instruction_type = pd.DataFrame(cast_to_string(instruction_type), columns=['instruction_type'])
        
        self.df = self.df.join(route_type.join(start_point_meters.join(finish_point_meters.join(start_point_part.join(finish_point_part.join(instruction_type))))))
        self.df.to_csv('add_' + Path(filepath).name)
        
    def flatternize(self, filepath, items_column) -> None:
    
        self.df = pd.read_csv(filepath)
        routes_edges = []
        routes_time = []
        routes_speed = []
        routes_length = []
#        routes_traffic_type = []

        for i in tqdm(range(len(self.df))):
            routes_edges.append([])
            routes_time.append([])
            routes_speed.append([])
            routes_length.append([])
#            routes_traffic_type.append([])
            for j in range(len(json.loads(self.df.iloc[i, items_column])['items'])):
                 for k in range(len(json.loads(self.df.iloc[i, items_column])['items'][j]['edges'])):
                        routes_edges[i].append(json.loads(self.df.iloc[i, items_column])['items'][j]['edges'][k]['edge_id'])
                        routes_time[i].append(json.loads(self.df.iloc[i, items_column])['items'][j]['edges'][k]['time'])
                        routes_speed[i].append(json.loads(self.df.iloc[i, items_column])['items'][j]['edges'][k]['speed'])
                        routes_length[i].append(json.loads(self.df.iloc[i, items_column])['items'][j]['edges'][k]['length'])
#                if ('traffic_type' in json.loads(df.iloc[i, items_column])['items'][j]['edges'][k]):
#                            routes_traffic_type[i].append(json.loads(self.df.iloc[i, items_column])['items'][j]['edges'][k]['traffic_type'])
#                        else:
#                            routes_traffic_type[i].append(-1)
                            
        edges_pd = pd.DataFrame(cast_to_string(routes_edges), columns=['edges'])
        time_pd = pd.DataFrame(cast_to_string(routes_time), columns=['time'])
        speed_pd = pd.DataFrame(cast_to_string(routes_speed), columns=['speed'])
        routes_length_pd = pd.DataFrame(cast_to_string(routes_length), columns=['length'])
#        routes_traffic_type_pd = pd.DataFrame(cast_to_string(routes_traffic_type), columns=['directionality'])
        
        
        self.df = self.df.join(edges_pd.join(time_pd.join(speed_pd.join(routes_length_pd)))).drop(['start_json', 'end_json', 'navigationId', "start_utc", "end_utc", "ETA", "build_utc", "build_timestamp"], axis=1)
        self.df.to_csv('processed_' + Path(filepath).name)
        
    def plot_time_freq(self, routes_1, routes_2):
        
        def freq_counter(routes):
            freq = []
            time = []
            index = pd.DatetimeIndex(routes['start_timestamp'])
            for i in range(0, 23):
                freq.append(len(routes.iloc[index.indexer_between_time(str(0+i) + ':00', str(1+i) + ':00')]))
                time.append(str(0+i) + ':00 - ' +  str(1+i) + ':00');
            freq.append(len(routes.iloc[index.indexer_between_time('23:00','00:00')]))
            time.append('23:00 - 00:00')
            df = pd.DataFrame(freq, index = time, columns = ['frequencies'])
            return(df)

        def draw_freq_hist(freq_df):
            fig = px.bar(freq_df, x=freq_df.index, y='frequencies')
            fig.show()

        def draw_freq_line(freq_1, freq_2):
            fig = px.line(freq_1, x=freq_1.index, y='frequencies')
            fig.add_scatter(x=freq_2.index, y=freq_2['frequencies'], mode='lines')
            fig.show()
            
        freq_city_1 = freq_counter(routes_1)
        freq_city_2 = freq_counter(routes_2)
        
        draw_freq_line(freq_city_1, freq_city_2)
        
    def plot_time_freq(self, routes_1, routes_2):
        
        def flat_list(data):
            return [int(item.replace("'", "")) for sublist in data for item in sublist]
        
        def get_use_data(routes_omsk):
            day_edges = [] 
            for i in range(0, 2):
                tmp = routes_omsk[(routes_omsk['start_timestamp'] >= '2020-12-0' + str(7+i)) & (routes_omsk['start_timestamp'] < '2020-12-0' + str(7+i+1))]['new_edges'].to_list()
                tmp_cl = [x for x in tmp if str(x) != 'nan']
                for j in range(len(tmp_cl)):
                    tmp_cl[j] = tmp_cl[j].split(',')
                day_edges.append(flat_list(tmp_cl))

            tmp = routes_omsk[(routes_omsk['start_timestamp'] >= '2020-12-09') & (routes_omsk['start_timestamp'] < '2020-12-10')]['new_edges'].to_list()
            tmp_cl = [x for x in tmp if str(x) != 'nan']
            for j in range(len(tmp_cl)):
                tmp_cl[j] = tmp_cl[j].split(',')
            day_edges.append(flat_list(tmp_cl))

            for i in range(0, 4):
                tmp = routes_omsk[(routes_omsk['start_timestamp'] >= '2020-12-1' + str(i)) & (routes_omsk['start_timestamp'] < '2020-12-1' + str(i+1))]['new_edges'].to_list()
                tmp_cl = [x for x in tmp if str(x) != 'nan']
                tmp_cl = [x for x in tmp_cl if str(x) != '']
                for j in range(len(tmp_cl)):
                    tmp_cl[j] = tmp_cl[j].split(',')
                day_edges.append(flat_list(tmp_cl))
                return day_edges
        
        def usage_to_dict(usage):
            counts = dict()
            for i in usage:
                counts[i] = counts.get(i, 0) + 1
            return counts

        def overall_to_dict(overall):
            counts = dict()
            for i in overall:
                counts[i] = 0
            return counts
        
        def draw_freq_line_inter(freq_1, freq_2, freq_3):
            fig = px.line(freq_1, x=freq_1.index, y='frequencies')
            fig.add_scatter(x=freq_2.index, y=freq_2['frequencies'], mode='lines', line = {'color': get_color(3), 'dash': 'solid'})
            fig.add_scatter(x=freq_3.index, y=freq_3['frequencies'], mode='lines', line = {'color': get_color(8), 'dash': 'solid'})
            fig.update_layout(showlegend=False)
            fig.show()
        
        overall = flat_list(dfs[1])
        usage_monday = usage_to_dict(get_use_data(routes_omsk_clear)[0])
        usage_wednesday = usage_to_dict(get_use_data(routes_omsk_clear)[1])

        usage_saturday = usage_to_dict(get_use_data(routes_omsk_clear)[5])
        usage_sunday = usage_to_dict(get_use_data(routes_omsk_clear)[6])
        overall = overall_to_dict(overall)
        
        weekdays = {k: overall.get(k, 0) + usage_monday.get(k, 0) + usage_wednesday.get(k, 0) 
            for k in set(overall) | set(usage_monday) | set(usage_wednesday)}
        weekend = {k: overall.get(k, 0) + usage_saturday.get(k, 0) + usage_sunday.get(k, 0) 
            for k in set(overall) | set(usage_saturday) | set(usage_sunday)}
        intersection = {x:min(weekdays[x], weekend[x]) for x in weekdays if x in weekend}
        
        weekdays = pd.DataFrame.from_dict(weekdays, orient = 'index', columns = ['frequencies']).reset_index()
        weekend = pd.DataFrame.from_dict(weekend, orient = 'index', columns = ['frequencies']).reset_index()
        intersection = pd.DataFrame.from_dict(intersection, orient = 'index', columns = ['frequencies']).reset_index()
        
        draw_freq_line_inter(intersection, weekdays, weekend)
        
        
    def clear_flatternized(self, filepath = None) -> None:

        def del_heads_n_tails(route):
            counter_d = 0
            edge_arr = route['edges'].split(',')
            time_arr = route['time'].split(',')
            speed_arr = route['speed'].split(',')
            len_arr = route['length'].split(',')
#            dir_arr = route['directionality'].split(',')
            
            indexes = []
            for j in range(len(edge_arr)):
                if (int(edge_arr[j]) == 0 or int(time_arr[j]) == 0):
                    indexes.append(j)

            for j in range(len(edge_arr) - 1):
                if (int(edge_arr[j]) == int(edge_arr[j+1])):
                    indexes.append(j)

            indexes = set(indexes)
            counter_d = len(indexes)
            for index in sorted(indexes, reverse=True):
                del edge_arr[index]
                del time_arr[index]
                del speed_arr[index]
                del len_arr[index]
#                del dir_arr[index]                                                             
            
            return [edge_arr, time_arr, speed_arr, len_arr, counter_d]

        def clear_routes_data(routes):
            edges_clear = []
            time_clear = []
            speed_clear = []
            len_clear = []
 #           dir_clear = []
                                                                                     
            counter_do = 0
            for i in tqdm(range(len(routes))):
                route_data = del_heads_n_tails(routes.iloc[i, :])
                edges_clear.append(route_data[0])
                time_clear.append(route_data[1])
                speed_clear.append(route_data[2])
                len_clear.append(route_data[3])
#                dir_clear.append(route_data[4])
                counter_do += route_data[4] 
            routes_properties = [[edges_clear, 'edges'], [time_clear, 'time'], [speed_clear, 'speed'], [len_clear, 'length']]
            for i in range(len(routes_properties)):
                routes_properties[i] = pd.DataFrame(cast_to_string(routes_properties[i][0]), columns = [routes_properties[i][1]])
            return [routes_properties, edges_clear, counter_do]
        
        if (filepath != None):
            self.dfs = clear_routes_data(pd.read_csv(filepath))
            self.df = pd.read_csv(filepath)
        else:          
            self.dfs = clear_routes_data(self.df)
#        self.df_clear = self.df.drop(['edges', 'time', 'speed', 'length', 'directionality'], axis=1).join(self.dfs[0][0].join(self.dfs[0][1].join(self.dfs[0][2].join(self.dfs[0][3].join(self.dfs[0][4])))))
        self.df_clear = self.df.drop(['edges', 'time', 'speed', 'length'], axis=1).join(self.dfs[0][0].join(self.dfs[0][1].join(self.dfs[0][2].join(self.dfs[0][3]))))
        self.df_clear.to_csv('clear_' + Path(filepath).name)
        

        
processing =  GIS_processing()
processing.flatternize('abakan.csv', 15)
processing.clear_flatternized("add_processed_abakan.csv")
