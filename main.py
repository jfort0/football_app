
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
from kivy.graphics import Color
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout

import sqlite3
import os
import datetime as dt
import json
import pandas as pd
import reportlab

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics



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
        """tables_list = ['prstići', 'zagići', 'limači', 'mlađi pioniri', 'pioniri', 'kadeti', 'juniori', 'seniori']
        if category.lower() not in tables_list:
            print('Nema ga')
            return"""
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
igraci INTEGER UNIQUE,
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
            print(f'Error open player data - {e}')
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
            print(f'Error open used_category - {e}')
            return []
        
    def insert_category_player_data(self, category, player_list):
        insert_query = f"""
INSERT INTO {category} (ime, prezime) VALUES (?, ?)
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

    def update_category_player_data(self, category, new_player_name, new_player_surname, old_player_info):
        update_query = f"""
UPDATE {category}
SET ime = ?, prezime = ?
WHERE ime = ? AND prezime = ?
"""
        try:
            sqlite_connection = sqlite3.connect(self.database_same_dir)
            cursor = sqlite_connection.cursor()
            cursor.execute(update_query, (new_player_name, new_player_surname, old_player_info[0], old_player_info[1]))
            sqlite_connection.commit()
            print(new_player_name, new_player_surname, old_player_info[0], old_player_info[1])
            cursor.close()
        except sqlite3.IntegrityError as b:
            message = 'Već imaš igrača/icu s tim imenom!'
            App.get_running_app().show_error_popup(message)
            print(f'Error update training - {b}')
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
            print(f'Error update training - {b}')
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
                    print('DAAAA')
                    print(row[df_dolasci_date])
                    df_result.at[index, df_dolasci_date] = 'DA'
                else:
                    print('NEEEE')
                    df_result.at[index, df_dolasci_date] = 'NE'
                    
        columns_to_count = df_result.columns[3:]
        sessions_count = df_result.shape[1] - 3
        attendance_count  = df_result[columns_to_count].apply(lambda row: row.str.count("DA").sum(), axis=1)
        attendance_info = attendance_count.astype(str) + ' / ' + str(sessions_count)
        df_result.insert(3, 'Dolasci', attendance_info)

        date_format = '%Y-%m-%d %H:%M:%S'  # Example format, adjust as needed
        for col in df_result.columns[4:]:
            print(col)
            new_col_name = dt.datetime.strptime(col, date_format).strftime('%d.%m.%Y')
            print(col)
            df_result.rename(columns={col: new_col_name}, inplace=True)

        df_result.rename(columns={'ime': 'Ime', 'prezime': 'Prezime'}, inplace=True)

        print(f'df_result FINAL \n{df_result}')
        df_result.drop(['id'], axis=1, inplace=True)

        pdf = SimpleDocTemplate(f"{category_sessions} {target_month}.{target_year}.pdf", pagesize=landscape(reportlab.lib.pagesizes.A4), leftMargin=50)
        table_data = [list(df_result.columns)]
        for i, row in df_result.iterrows():
            table_data.append(list(row))

        table = Table(table_data)

        pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))  

        table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Arial'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Arial'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ])

        table.setStyle(table_style)

        pdf_table = []
        pdf_table.append(table)

        pdf.build(pdf_table)

        

        
class MyScreenManager(ScreenManager):
    def __init__(self, **kw):
        super(MyScreenManager, self).__init__(**kw)

class ScreenIntro(Screen):
    def __init__(self, **kw):
        super(ScreenIntro, self).__init__(**kw)
    
    # Metoda za promjenu atributa objekata iz drugih ekrana - možda staviti u app?
    def change_screen(self):
        other_screen = self.manager.get_screen('screen2')
        other_screen.ids.button_mijena.text = 'Bravooo'
        other_screen.ids.button_mijena.disabled= True
        screen2 = Screen2()
        print(screen2.category_text)

# Pitanje da li mi treba ova klasa - PROVJERA   
class BoxLayoutScroll(BoxLayout):
    pass

class ScreenAddCategory(Screen):
    category_choice = StringProperty()
    def __init__(self, **kw):
        super().__init__(**kw)
        self.category_choice = 'NIJE ODABRANA'
    #?????????
    new_category = StringProperty('ODABERI KATEGORIJU')

    def on_toggle_press(self, instance, value):
        if value == 'down':
            self.category_choice = instance.text
        else:
            self.category_choice = 'NIJE ODABRANA'

    #?????????
    def update_category(self, widget):
        self.new_category = widget.text
    
    #?????????
    def update_label(self, label_id, new_text):
        self.category_text = self.new_category
        self.root.ids[label_id].text = new_text
    
    #?????????
    def change_category(self, screen, widget_id, attribute, command):
        # Accessing the label widget in OtherScreen and updating its text
        other_screen = self.manager.get_screen(screen).ids[widget_id]
        setattr(other_screen, attribute, command)

class ScreenCategoryManager(Screen):
    pass

class ScreenPlayerManager(Screen):
    def __init__(self, **kw):
        super(ScreenPlayerManager, self).__init__(**kw)
        self.sql_manager = SqlManager()

 # Imam opciju da svaki put čitam bazu ili tek kad otvorim category manager učita iz baze u rječnik       
    def fetch_players(self, category):
        category_players = self.sql_manager.open_category_player_data(category)
        self.player_box = self.ids.player_box
        if category_players:
            category_players = sorted(category_players, key=lambda x: x[0])
            self.player_box.clear_widgets()
            for number, player in enumerate(category_players):
                player_label = ToggleButton(text=f'{number + 1}. {player[2]}, {player[1]}',
                                            group="player_button", 
                                            height=50,
                                            size_hint= (0.6, None),
                                            disabled = False if player[3] else True
                                            )
                player_label.bind(state=self.on_toggle_press)
                self.player_box.add_widget(player_label)
                print(player)
                active = 'Aktivan' if player[3] else 'Neaktivan'
                player_active = Label(text=active, height=50, size_hint= (0.4, None))
                self.player_box.add_widget(player_active)
        else:
            # provjera category chosen
            print(f'Kategorija odabrana {category}')
            self.player_box.clear_widgets()
            player_label = Label(text='Nema unesenih igrača', halign='left', valign='middle', height=50, size_hint_y=None)
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

    def new_player(self, category_chosen_sql_players, second_name, name):
        if len(second_name) < 1 or len(name) < 1:
            message = 'Moraš unijeti ime i prezime!'
            App.get_running_app().show_error_popup(message)
        else:
            player_list = [(second_name, name)]
            print(player_list, App.get_running_app().category_chosen_sql_players)
            self.sql_manager.insert_category_player_data(category_chosen_sql_players, player_list)

class ScreenEditPlayer(Screen):
    def __init__(self, **kw):
        super(ScreenEditPlayer, self).__init__(**kw)

class ScreenTrainingManager(Screen):
    def __init__(self, **kw):
        super(ScreenTrainingManager, self).__init__(**kw)

        self.sql_manager = SqlManager()

 # Imam opciju da svaki put čitam bazu ili tek kad otvorim category manager učita iz baze u rječnik       
    def fetch_training(self, category):
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
                                            height=50,
                                            size_hint_y= None
                                            )
                training_label.bind(state=self.on_toggle_press)
                self.training_box.add_widget(training_label)
                print(training)
                t_or_m = 'Trening' if training[2] == 'trening' else 'Utakmica'
                training_match = Label(text=t_or_m, height=50, size_hint= (0.4, None))
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
                                            height=50,
                                            size_hint_y= None,
                                            disabled = False if player[3] else True
                                            )
                player_label.bind(state=self.on_toggle_press)
                active = 'Aktivan' if player[3] else 'Neaktivan'
                player_active = Label(text=active, height=50, size_hint= (0.4, None))

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
                                            height=50,
                                            size_hint_y= None
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
                                            height=50,
                                            size_hint_y= None,
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
            player_label = Label(text='Nema unesenih igrača', halign='left', valign='middle', height=50, size_hint_y=None)
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