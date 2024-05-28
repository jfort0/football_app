
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty, NumericProperty
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.utils import get_color_from_hex

import sqlite3
import os
import datetime as dt
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

class SqlManager:
    # Klasa za upravljanje bazama podataka

    database = 'liste_dolazaka.db'
    script_path = os.path.abspath(__file__)
    script_directory = os.path.dirname(script_path)
    database_same_dir = os.path.join(script_directory, database)
    
    # Provjera da li postoji datoteka baze podataka
    def check_database(self):    
        return os.path.exists(self.database)
    
    # Provjera da li postoji tablica unutar datoteke baze podataka
    def check_table(self):    
        try:
            sqlite_connection = sqlite3.connect(self.database_same_dir)
            cursor = sqlite_connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            cursor.close()
            return [table[0] for table in tables]
        except sqlite3.Error as e:
            print(f'Error check table - {e}')
            return []

    # Stvori bazu podataka i tablice kategorije (popis igrača i dolazaka)    
    def create_database(self, category_players, category_sessions):
        print(f'Category chosen for database func: {category_players, category_sessions}')
        query_category_database = f"""
CREATE TABLE IF NOT EXISTS {category_players}(
id INTEGER PRIMARY KEY,
ime TEXT NOT NULL,
prezime TEXT NOT NULL,
aktivan BOOLEAN DEFAULT TRUE,
UNIQUE(ime, prezime));
"""
        query_sessions_database = f"""
CREATE TABLE IF NOT EXISTS {category_sessions}(
id INTEGER PRIMARY KEY,
datum DATETIME NOT NULL UNIQUE,
trening_tekma TEXT NOT NULL,
igraci INTEGER,
FOREIGN KEY (igraci) REFERENCES {category_players}(id));
"""
        query_last_used_database = f"""
CREATE TABLE IF NOT EXISTS last_used(
id INTEGER PRIMARY KEY,
kategorija TEXT);
"""
        try:
            sqlite_connection = sqlite3.connect(self.database_same_dir)
            cursor = sqlite_connection.cursor()
            cursor.execute(query_category_database)
            cursor.execute(query_sessions_database)
            cursor.execute(query_last_used_database)
            sqlite_connection.commit()
            cursor.close()
        except sqlite3.Error as e:
            print(f'Greška create database - {e}')

    def open_category_used(self):
        try:
            sqlite_connection = sqlite3.connect(self.database_same_dir)
            cursor = sqlite_connection.cursor()
            cursor.execute(f"SELECT kategorija FROM last_used")
            category_list = cursor.fetchall()
            cursor.close()
            return [category for category in category_list]
        except sqlite3.Error as e:
            print(f'Error open used_category - {e}')
            return []
        
    def insert_category_used(self, category_chosen):
        if self.open_category_used():
            insert_query = f"""
            UPDATE last_used
            SET kategorija = ?
            WHERE id = 1
            """ 
        else:
            insert_query = f"""
            INSERT INTO last_used (kategorija) VALUES (?)
            """
        try:
            sqlite_connection = sqlite3.connect(self.database_same_dir)
            cursor = sqlite_connection.cursor()
            cursor.execute(insert_query, (category_chosen,))
            sqlite_connection.commit()
            cursor.close()
        except sqlite3.Error as e:
            print(f'Error insert category_used - {e}')
        finally:
            if sqlite_connection:
                sqlite_connection.close()

    def open_category_player_data(self, category):
        try:
            sqlite_connection = sqlite3.connect(self.database_same_dir)
            cursor = sqlite_connection.cursor()
            cursor.execute(f"SELECT id, ime, prezime, aktivan FROM {category}")
            category_players = cursor.fetchall()
            cursor.close()
            return [player for player in category_players]
        except sqlite3.Error as e:
            print(f'Error open player data - {e}')
            return []
        
    def insert_category_player_data(self, category, player_list):
        insert_query = f"""
INSERT INTO {category} (ime, prezime, aktivan) VALUES (?, ?, ?)
"""
        try:
            sqlite_connection = sqlite3.connect(self.database_same_dir)
            cursor = sqlite_connection.cursor()
            for player in player_list:
                cursor.execute(insert_query, player)
            sqlite_connection.commit()
            cursor.close()
        except sqlite3.IntegrityError as b:
            message = 'Već imaš igrača/icu s tim imenom!'
            App.get_running_app().show_error_popup(message)
            print(f'Error update training - {b}')
        except sqlite3.Error as e:
            print(f'Error insert player - {e}')
        finally:
            if sqlite_connection:
                sqlite_connection.close()

    def update_category_player_data(self, category, new_player_name, new_player_surname, new_player_active, old_player_info):
        update_query = f"""
UPDATE {category}
SET ime = ?, prezime = ?, aktivan = ?
WHERE ime = ? 
AND prezime = ?
"""
        try:
            sqlite_connection = sqlite3.connect(self.database_same_dir)
            cursor = sqlite_connection.cursor()
            cursor.execute(update_query, (new_player_name, new_player_surname, new_player_active, old_player_info[0].strip(), old_player_info[1].strip()))
            sqlite_connection.commit()
            print(category, new_player_name, new_player_surname, new_player_active, old_player_info[0], old_player_info[1])
            cursor.close()
        except sqlite3.IntegrityError as b:
            message = 'Već imaš igrača/icu s tim imenom!'
            App.get_running_app().show_error_popup(message)
            print(f'Error update player - {b}')
        except sqlite3.Error as e:
            print(f'Error update player - {e}')

        finally:
            if sqlite_connection:
                sqlite_connection.close()

    def open_category_training_data(self, category):
        try:
            sqlite_connection = sqlite3.connect(self.database_same_dir)
            cursor = sqlite_connection.cursor()
            cursor.execute(f"SELECT id, datum, trening_tekma, igraci FROM {category}")
            category_training = cursor.fetchall()
            cursor.close()
            return [training for training in category_training]
        except sqlite3.Error as e:
            print(f'Error open training data - {e}')
            return []
        
    def insert_category_training_data(self, category, date, training_match, players_list):
        players_list = json.dumps(players_list)
        insert_query = f"""
INSERT INTO {category} (datum, trening_tekma, igraci) VALUES (?, ?, ?)
"""
# Dodati popup ako već postoji određeni datum
        try:
            print(category, date, training_match, players_list)
            print(type(date), 'insert')
            sqlite_connection = sqlite3.connect(self.database_same_dir)
            cursor = sqlite_connection.cursor()
            #for training in training_list:
            cursor.execute(insert_query, (date, training_match, players_list))
            sqlite_connection.commit()
            cursor.close()
        except sqlite3.IntegrityError as b:
            message = 'Imaš dva treninga/utakmice s istim datumom!'
            App.get_running_app().show_error_popup(message)
            print(f'Error insert training - {b}')
        except sqlite3.Error as e:
            print(f'Error insert training - {e}')
        finally:
            if sqlite_connection:
                sqlite_connection.close()

    def update_category_training_data(self, category, old_date, new_date, training_match, players_list):
        print(f'players list {players_list}')
        players_list = json.dumps(players_list)
        update_query = f"""
UPDATE {category}
SET datum = ?, trening_tekma = ?, igraci = ?
WHERE datum = ?
"""
        try:
            sqlite_connection = sqlite3.connect(self.database_same_dir)
            cursor = sqlite_connection.cursor()
            cursor.execute(update_query, (new_date, training_match, players_list, old_date))
            sqlite_connection.commit()
            print(new_date, training_match, players_list, old_date)
            cursor.close()
        except sqlite3.IntegrityError as b:
            message = 'Imaš dva treninga/utakmice s istim datumom!'
            App.get_running_app().show_error_popup(message)
            print(f'Error update training - {b}')
        except sqlite3.Error as e:
            print(f'Error update training - {e}')
        

        finally:
            if sqlite_connection:
                sqlite_connection.close()

    def month_attendance(self, category, month):
        print(category, month)

        count_month_query = f"""
                SELECT COUNT(*)
                FROM {category}
                WHERE strftime('%m', datum) = '02'
"""
        try:
            sqlite_connection = sqlite3.connect(self.database_same_dir)
            cursor = sqlite_connection.cursor()
            cursor.execute(count_month_query)
            count_month = cursor.fetchone()[0]
            cursor.close()
            print(count_month)
            return count_month
            
        except sqlite3.Error as e:
            print(f'Error count attendance - {e}')
        finally:
            if sqlite_connection:
                sqlite_connection.close()

    def sql_to_pdf(self, category_players, category_sessions, target_month, target_year):
        app = App.get_running_app()
        sqlite_connection = sqlite3.connect(self.database_same_dir)
        sql_query = pd.read_sql_query(f'''
                               SELECT
                               *
                               FROM {category_players}
                               ''', sqlite_connection)

        df_igraci = pd.DataFrame(sql_query, columns = ['id', 'ime', 'prezime'])
        print (f'df_igraci \n{df_igraci}')

        sql_query = pd.read_sql_query(f'''
                                    SELECT
                                    *
                                    FROM {category_sessions}
                                    WHERE strftime('%m', datum) = '{target_month.zfill(2)}'
                                    AND strftime('%Y', datum) = '{target_year}'
                                    ''', sqlite_connection)

        df_dolasci = pd.DataFrame(sql_query, columns = ['id', 'datum', 'igraci'])
        print(f'df_dolasci \n{df_dolasci}')
        df_datumi = df_dolasci['datum']
        dates = df_datumi.tolist()
        print(f'dates \n{dates}')
        df_dates = pd.DataFrame(columns=dates)
        df_result = pd.concat([df_igraci, df_dates], axis=1)
        print(f'df_result \n{df_result}')

        for ind in df_dolasci.index:
            df_dolasci_id = df_dolasci.at[ind, 'igraci']
            print(f'df_dolasci_id \n{df_dolasci_id}')
            df_dolasci_date = df_dolasci.at[ind, 'datum']
            print(f'df_dolasci_date \n{df_dolasci_date}')
            for index, row in df_result.iterrows():
                print(f'str(row["id"]) \n{str(row["id"])}')
                if str(row['id']) in str(df_dolasci_id):
                    df_result.at[index, df_dolasci_date] = 'DA'
                else:
                    df_result.at[index, df_dolasci_date] = 'NE'
                    
        columns_to_count = df_result.columns[3:]
        sessions_count = df_result.shape[1] - 3
        attendance_count  = df_result[columns_to_count].apply(lambda row: row.str.count("DA").sum(), axis=1)
        attendance_info = attendance_count.astype(str) + ' / ' + str(sessions_count)
        df_result.insert(3, 'Dolasci', attendance_info)

        date_format = '%Y-%m-%d %H:%M:%S'  # Example format, adjust as needed
        for col in df_result.columns[4:]:
            new_col_name = dt.datetime.strptime(col, date_format).strftime('%d.%m.')
            df_result.rename(columns={col: new_col_name}, inplace=True)

        df_result.rename(columns={'ime': 'Ime', 'prezime': 'Prezime'}, inplace=True)

        print(f'df_result FINAL \n{df_result}')
        df_result.drop(['id'], axis=1, inplace=True)

        fig, ax =plt.subplots(figsize=(11.69, 8.27))
        #ax.axis('tight')
        ax.axis('off')
        the_table = ax.table(cellText=df_result.values,colLabels=df_result.columns,loc='upper left', colWidths=[0.15 for x in df_result.columns])

        for i, cell in enumerate(the_table.get_celld().values()):
            #cell.set_width(2/len(my_df.columns))
            row, col = divmod(i, len(df_result.columns))
            #value = my_df.iloc[row - 3, col]  # Adjust the row index since we start from 1 for data rows
            value = cell.get_text().get_text()
            if value == "DA":  # Check if cell value is "Alice"
                cell.set_facecolor('lightgreen')
            if row == len(df_result):  # Header row
                cell.set_text_props(weight='bold', ha='center', va='center')
                cell.set_facecolor('lightblue')
            elif row < len(df_result) and col >= 2:  # Data rows
                cell.set_text_props(ha='center', va='center')
            else:
                cell.set_text_props(ha='left', va='center')

        # Set autowidth columns
        the_table.auto_set_column_width(col=list(range(2, len(df_result.columns))))

        plt.title(f'Popis dolazaka - {app.category_chosen} - {target_month}.{target_year}', fontsize=12, loc='left')

        plt.tight_layout()

        pp = PdfPages(f"Popis dolazaka - {app.category_chosen} - {target_month}.{target_year}.pdf")
        pp.savefig(fig, bbox_inches='tight')
        pp.close()
        
class MyScreenManager(ScreenManager):
    def __init__(self, **kw):
        super(MyScreenManager, self).__init__(**kw)

class ScreenIntro(Screen):
    def __init__(self, **kw):
        super(ScreenIntro, self).__init__(**kw)

# Pitanje da li mi treba ova klasa - PROVJERA   
class BoxLayoutScroll(BoxLayout):
    pass

class ScreenAddCategory(Screen):
    category_choice = StringProperty()
    def __init__(self, **kw):
        super().__init__(**kw)
        self.category_choice = 'ODABERI KATEGORIJU'
    
    def create_category_buttons(self):
        app = App.get_running_app()
        self.category_box = self.ids.category_box
        player_categories = ('PRSTIĆI', 'ZAGIĆI', 'LIMAČI', 'MLAĐI PIONIRI', 'PIONIRI', 'KADETI', 'JUNIORI')
        self.category_box.clear_widgets()
        for category in player_categories:
            category_button = ToggleButton(text= category,
                                        group= "category_buttons", 
                                        background_color= app.button_a_color,
                                        pos_hint= {'center_x': 0.5},
                                        size_hint= [1, None],
                                        font_size= app.font_size,
                                        height= app.button_height,
                                        )
            category_button.bind(state=self.on_toggle_press)
            self.category_box.add_widget(category_button)
            print(category)

    def on_toggle_press(self, instance, value):
        app = App.get_running_app()
        if value == 'down':
            self.category_choice = instance.text
            app.save_category_button_disabled = False
        else:
            self.category_choice = 'ODABERI KATEGORIJU'
            app.save_category_button_disabled = True

class ScreenCategoryManager(Screen):
    pass

class ScreenPlayerManager(Screen):
    def __init__(self, **kw):
        super(ScreenPlayerManager, self).__init__(**kw)
        self.sql_manager = SqlManager()

 # Imam opciju da svaki put čitam bazu ili tek kad otvorim category manager učita iz baze u rječnik       
    def fetch_players(self, category):
        app = App.get_running_app()
        category_players = self.sql_manager.open_category_player_data(category)
        self.player_box = self.ids.player_box
        if category_players:
            category_players = sorted(category_players, key=lambda x: x[0])
            self.player_box.clear_widgets()
            for number, player in enumerate(category_players):
                player_label = ToggleButton(text=f'{number + 1}. {player[2]}, {player[1]}',
                                            group="player_button", 
                                            background_color= app.button_a_color,
                                            size_hint= (1, None),
                                            font_size= dp(15),
                                            height= dp(40)
                                            )
                player_label.bind(state=self.on_toggle_press)
                self.player_box.add_widget(player_label)
                print(player)
                active = 'Aktivan' if player[3] else 'Neaktivan'
                player_active = Label(text=active, height= dp(40), font_size= dp(15), size_hint= (0.4, None))
                self.player_box.add_widget(player_active)
        else:
            # provjera category chosen
            print(f'Kategorija odabrana {category}')
            self.player_box.clear_widgets()
            player_label = Label(text='Nema unesenih igrača', font_size= dp(15), height= dp(40), size_hint_y=None)
            self.player_box.add_widget(player_label)
    def on_toggle_press(self, instance, value):
        if value == 'down':
            App.get_running_app().edit_button_disabled = False
            player_to_edit = instance.text[2:].split(',')
            App.get_running_app().update_player_chosen(player_to_edit[1], player_to_edit[0])
            print(f'Op op {App.get_running_app().player_chosen}')
            #self.player_to_edit_string = ', '.join(self.player_to_edit)
        else:
            App.get_running_app().edit_button_disabled = True
            App.get_running_app().player_chosen = ''

class ScreenAddPlayer(Screen):
    def __init__(self, **kw):
        super(ScreenAddPlayer, self).__init__(**kw)
        self.sql_manager = SqlManager()

    def new_player(self, category_chosen_sql_players, second_name, name, active):
        if len(second_name) < 1 or len(name) < 1:
            message = 'Moraš unijeti ime i prezime!'
            App.get_running_app().show_error_popup(message)
        else:
            player_list = [(second_name, name, active)]
            print(player_list, App.get_running_app().category_chosen_sql_players)
            self.sql_manager.insert_category_player_data(category_chosen_sql_players, player_list)
    
    def switch_state(self, instance, value):
        if value == True:
            self.ids.activity_label.text = 'AKTIVAN'
            self.ids.activity_label.color = (1, 1, 1, 1)
            self.ids.activity_label.bold = True
        else:
            self.ids.activity_label.text = 'NEAKTIVAN'
            self.ids.activity_label.color = (0.5, 0.5, 0.5, 1)
            self.ids.activity_label.bold = False

class ScreenEditPlayer(Screen):
    def __init__(self, **kw):
        super(ScreenEditPlayer, self).__init__(**kw)
    sql_manager = SqlManager()
    
    
    def player_switch_activity(self, category):
        app = App.get_running_app()
        players_edit = self.sql_manager.open_category_player_data(category)
        for player in players_edit:
            if app.player_edit[0] == player[1] and app.player_edit[1] == player[0]:
                player_edit_active = app.player_edit[2]
                print(app.player_edit[0], player[1], app.player_edit[1], player[0])
                return True
            else:
                return True
                

    def switch_state(self, instance, value):
        if value == True:
            self.ids.activity_label.text = 'AKTIVAN'
            self.ids.activity_label.color = (1, 1, 1, 1)
            self.ids.activity_label.bold = True
        else:
            self.ids.activity_label.text = 'NEAKTIVAN'
            self.ids.activity_label.color = (0.5, 0.5, 0.5, 1)
            self.ids.activity_label.bold = False

class ScreenTrainingManager(Screen):
    def __init__(self, **kw):
        super(ScreenTrainingManager, self).__init__(**kw)

        self.sql_manager = SqlManager()

 # Imam opciju da svaki put čitam bazu ili tek kad otvorim category manager učita iz baze u rječnik       
    def fetch_training(self, category):
        app = App.get_running_app()
        self.training_box = self.ids.training_box
        if self.sql_manager.open_category_training_data(category):
            self.training_box.clear_widgets()
            data_training = self.sql_manager.open_category_training_data(category)
            data_training = sorted(data_training, key=lambda x: x[1], reverse = True)
            for training in data_training:
                date_str = training[1]
                date = dt.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                date = App.get_running_app().create_date_format(date)
                training_label = ToggleButton(text=f'{date}',
                                            group="training_button", 
                                            background_color= app.button_a_color,
                                            size_hint= (1, None),
                                            font_size= dp(15),
                                            height= dp(40)
                                            )
                training_label.bind(state=self.on_toggle_press)
                self.training_box.add_widget(training_label)
                print(training)
                t_or_m = 'Trening' if training[2] == 'trening' else 'Utakmica'
                training_match = Label(text=t_or_m, font_size= dp(15), height= dp(40), size_hint= (0.4, None))
                self.training_box.add_widget(training_match)
                
        else:
            # provjera category chosen
            print(f'Kategorija odabrana {category}')
            self.training_box.clear_widgets()
            training_label = Label(text='Nema unesenih treninga', halign='left', valign='middle', height=50, size_hint_y=None)
            self.training_box.add_widget(training_label)
    def on_toggle_press(self, instance, value):
        if value == 'down':
            App.get_running_app().edit_button_disabled = False
            training_to_edit = instance.text
            App.get_running_app().update_training_chosen(training_to_edit)
            print(f'Op op {App.get_running_app().training_chosen}')
        else:
            App.get_running_app().edit_button_disabled = True

class ScreenAddTraining(Screen):
    selected_year = StringProperty('')
    players_list = ObjectProperty()
    current_date = dt.date.today()
    day_today = '{:d}'.format(current_date.day)
    month_today = '{:d}'.format(current_date.month)
    year_today = '{:d}'.format(current_date.year)
    days_list = [str(day) for day in range(1, 32)]
    months_list = [str(month) for month in range(1, 13)]
    years_list = [str(year) for year in range(int(year_today) - 1, int(year_today) + 11)]

    def __init__(self, **kw):
        super(ScreenAddTraining, self).__init__(**kw) 
        self.sql_manager = SqlManager()
        self.players_list = []
    def fetch_players(self, category, action):
        app = App.get_running_app()
        category_players = self.sql_manager.open_category_player_data(category)
        #training_data = self.sql_manager.open_category_training_data(category)
        self.player_box = self.ids.player_box
        self.toggle_buttons = []
        
        if action == 'update':
            edit_training = self.manager.get_screen('edit training')  
            self.player_box = edit_training.ids.player_box 
        if category_players:
            category_players = sorted(category_players, key=lambda x: x[0])
            training_data = self.sql_manager.open_category_training_data(app.category_chosen_sql_training)
            self.player_box.clear_widgets()
            for number, player in enumerate(category_players):
                player_label = ToggleButton(text=f'{number + 1}. {player[2]}, {player[1]}',
                                            size_hint= (1, None),
                                            background_color= app.button_a_color,
                                            font_size= dp(15),
                                            height= dp(40),
                                            disabled = False if player[3] else True
                                            )
                player_label.bind(state=self.on_toggle_press)
                active = 'Aktivan' if player[3] else 'Neaktivan'
                player_active = Label(text=active, font_size= dp(15), height= dp(40), size_hint= (0.4, None))

                if action == 'update':
                    self.player_box.add_widget(player_label)
                    self.player_box.add_widget(player_active)
                    training_date = str(app.create_date(app.training_chosen))
                    for training in training_data:
                        if training[1] == training_date:
                            player_id = int(player_label.text.split('.')[0])
                            player_list_db = json.loads(training[3])
                            if player_id in player_list_db:
                                player_label.state = 'down'
                elif action == 'attendance_list':
                    attendance_screen = self.manager.get_screen('players training report')  
                    self.training_box = attendance_screen.ids.training_box
                    self.month_input = attendance_screen.ids.month_input.text
                    self.year_input = attendance_screen.ids.year_input.text
                    #self.training_box.clear_widgets()
                    player_label = Label(text=f'{number + 1}. {player[2]}, {player[1]}',
                                            size_hint= (1.0, None),
                                            font_size= dp(15),
                                            height= dp(40),
                                            bold= True
                                            )
                    count_attendance = 0
                    count_month = 0
                    player_id = int(player_label.text.split('.')[0])
                    for training in training_data:
                        training_month = dt.datetime.strptime(training[1], '%Y-%m-%d %H:%M:%S').month
                        training_year = dt.datetime.strptime(training[1], '%Y-%m-%d %H:%M:%S').year
                        print(training_month, training_year)
                        if training_month == int(self.month_input) and training_year == int(self.year_input):
                            count_month += 1 
                            player_list_db = json.loads(training[3])
                            if player_id in player_list_db:
                                count_attendance += 1
                    attendance_label = Label(text=f'{count_attendance} / {count_month}',
                                            size_hint= (1, None),
                                            font_size= dp(15),
                                            height= dp(40),
                                            halign = 'left'
                                            )
                        
                    self.training_box.add_widget(player_label)
                    self.training_box.add_widget(attendance_label)
                else:
                    self.player_box.add_widget(player_label)
                    self.player_box.add_widget(player_active)
                    print(player)
                self.toggle_buttons.append(player_label)
            self.selected_items = set()
        else:
            # provjera category chosen
            print(f'Kategorija odabrana {category}')
            self.player_box.clear_widgets()
            player_label = Label(text='Nema unesenih igrača', halign='left', valign='middle', height=dp(40),font_size= dp(15), size_hint_y=None)
            self.player_box.add_widget(player_label)
        

    def on_toggle_press(self, instance, value):
        player_id = int(instance.text.split('.')[0])
        if value == 'down':
            self.players_list.append(player_id)
            print(f'Op op {self.players_list}')
            #self.player_to_edit_string = ', '.join(self.player_to_edit)
        else:
            if player_id in self.players_list:
                self.players_list.remove(player_id)
                print(f'Op op {self.players_list}')

    def switch_state(self, instance, value):
        if value:
            self.ids.training_label.color = (1, 1, 1, 1)
            self.ids.training_label.bold = True
            self.ids.match_label.color = (0.5, 0.5, 0.5, 1)
            self.ids.match_label.bold = False
        else:
            self.ids.training_label.color = (0.5, 0.5, 0.5, 1)
            self.ids.training_label.bold = False
            self.ids.match_label.color = (1, 1, 1, 1)
            self.ids.match_label.bold = True

    def new_training(self, category_chosen_sql_training, day, month, year):
        date_str = f'{day}.{month}.{year}.'
        date = App.get_running_app().create_date(date_str)
        print(type(date), 'new training')
        if self.ids.training_switch.active == True:
            training_match = 'trening'
        else: 
            training_match = 'tekma'
        self.sql_manager.insert_category_training_data(category_chosen_sql_training, date, training_match, self.players_list)

class ScreenEditTraining(Screen):
    def __init__(self, **kw):
        super(ScreenEditTraining, self).__init__(**kw)
        self.sql_manager = SqlManager()        

    def update_training(self, category_chosen_sql_training, day, month, year, players_list):
        date_str = f'{day}.{month}.{year}.'
        new_date = App.get_running_app().create_date(date_str)
        old_date = str(App.get_running_app().create_date(App.get_running_app().training_chosen))
        if self.ids.training_switch.active == True:
            training_match = 'trening'
        else: 
            training_match = 'tekma'
        self.sql_manager.update_category_training_data(category_chosen_sql_training, old_date, new_date, training_match, players_list)

    def check_training_match(self, training_chosen):
        app = App.get_running_app()
        training_data = self.sql_manager.open_category_training_data(app.category_chosen_sql_training)
        training_date = str(app.create_date(training_chosen))
        print(f'trening chosen {training_date}')
        for training in training_data:
            if training[1] == training_date:
                edit_switch_match_training = True if training[2] == 'trening' else False
                print (edit_switch_match_training)
                return edit_switch_match_training

    def switch_state(self, instance, value):
        if value:
            self.ids.training_label.color = (1, 1, 1, 1)
            self.ids.training_label.bold = True
            self.ids.match_label.color = (0.5, 0.5, 0.5, 1)
            self.ids.match_label.bold = False
        else:
            self.ids.training_label.color = (0.5, 0.5, 0.5, 1)
            self.ids.training_label.bold = False
            self.ids.match_label.color = (1, 1, 1, 1)
            self.ids.match_label.bold = True

class ScreenReports(Screen):
    def __init__(self, **kw):
        super(ScreenReports, self).__init__(**kw)



class MyFootballApp(App):
    # Glavne varijable
    category_chosen = StringProperty()
    category_chosen_sql_players = StringProperty()
    category_chosen_sql_training = StringProperty()
    category_button_disabled = BooleanProperty()
    
    player_chosen = StringProperty()
    training_chosen = StringProperty()
    player_edit = ObjectProperty()
    klub = StringProperty()
    edit_button_disabled = BooleanProperty(True)
    save_category_button_disabled = BooleanProperty(True)

    button_height = dp(40)
    font_size = dp(15)
    padding = dp(40)
    spacing = dp(10)    
    button_a_color = get_color_from_hex('#3277ad')
    button_b_color = get_color_from_hex('#00004A')
    button_c_color = get_color_from_hex('#000031')
    
    def build(self): 

        self.category_chosen = 'NEMA KATEGORIJE'
        self.category_button_disabled = True
        
        self.klub = 'NK TOPLICE'
        self.sql_manager = SqlManager()
        self.screen_intro = ScreenIntro()     
        self.sql_manager_instance = SqlManager()
        self.check_table = self.sql_manager.check_table()
        self.check_category_used = self.sql_manager.open_category_used()
        # Provjera za početak - ako imamo otvorenu kategoriju, prva u bazi može biti odabrana gumbom i gumb nije isključen
        
        if self.check_category_used:
            self.category_chosen = self.check_category_used[0][0]
            self.update_category_chosen_sql(self.category_chosen)
            self.category_button_disabled = False
            self.sql_manager.insert_category_used(self.category_chosen)
# Provjera - naknadno brisanje
            print(self.category_chosen, self.category_chosen_sql_players, self.category_chosen_sql_training)
        
        kv = Builder.load_file('myfootball.kv')
        return kv  
    
    def update_player_chosen(self, player_name, player_surname):
        self.player_chosen = ", ".join([player_name, player_surname])
        self.player_edit = (player_name, player_surname)

    def update_training_chosen(self, training_date):
        self.training_chosen = training_date
    
    def update_category_chosen_sql(self, category_chosen):
        self.category_chosen_sql_players = category_chosen.lower().replace(' ','_') + '_igraci'
        self.category_chosen_sql_training = category_chosen.lower().replace(' ','_') + '_dolasci'
        self.sql_manager.insert_category_used(category_chosen)
        print(self.category_chosen, self.category_chosen_sql_players, self.category_chosen_sql_training)

    def show_error_popup(self, message):
        content = Label(text=message)
        popup = Popup(title='Greška', content=content, size_hint=(None, None), size=(400, 200))
        popup.open()

    def create_date(self, date_str):
        date = dt.datetime.strptime(date_str, '%d.%m.%Y.')
        return date
    
    def create_date_format(self, date_strp):
        date = date_strp.strftime('%d.%m.%Y.')
        print(f'Strf {type(date)}')
        return date
    
    
              

if __name__ == "__main__":
    MyFootballApp().run()