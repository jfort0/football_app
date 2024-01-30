from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.uix.popup import Popup
import sqlite3
import os

from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.spinner import Spinner

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
aktivan BOOLEAN DEFAULT TRUE);
"""
        query_sessions_database = f"""
CREATE TABLE IF NOT EXISTS {category_sessions}(
id INTEGER PRIMARY KEY,
datum DATE NOT NULL,
trening_tekma TEXT NOT NULL,
igraci TEXT);
"""
        try:
            sqlite_connection = sqlite3.connect(self.database_same_dir)
            cursor = sqlite_connection.cursor()
            cursor.execute(query_category_database)
            cursor.execute(query_sessions_database)
            sqlite_connection.commit()
            cursor.close()
        except sqlite3.Error as e:
            print(f'Greška create database - {e}')

    def open_category_player_data(self, category):
        try:
            sqlite_connection = sqlite3.connect(self.database_same_dir)
            cursor = sqlite_connection.cursor()
            cursor.execute(f"SELECT id, ime, prezime FROM {category}")
            category_players = cursor.fetchall()
            cursor.close()
            return [player for player in category_players]
        except sqlite3.Error as e:
            print(f'Error open player data - {e}')
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
        except sqlite3.Error as e:
            print(f'Error insert player - {e}')
        finally:
            if sqlite_connection:
                sqlite_connection.close()

    def update_category_player_data(self, category, new_player_name, new_player_surname, old_player_name, old_player_surname):
        update_query = f"""
UPDATE {category}
SET ime = ?, prezime = ?
WHERE ime = ? AND prezime = ?
"""
        try:
            sqlite_connection = sqlite3.connect(self.database_same_dir)
            cursor = sqlite_connection.cursor()
            cursor.execute(update_query, (new_player_name, new_player_surname, old_player_name, old_player_surname))
            sqlite_connection.commit()
            print(new_player_name, new_player_surname, old_player_name, old_player_surname)
            cursor.close()
        except sqlite3.Error as e:
            print(f'Error update player - {e}')

        finally:
            if sqlite_connection:
                sqlite_connection.close()

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
    def on_enter(self, *args):
        app = App.get_running_app()
        self.sql_manager = SqlManager()
        app.player_name_to_edit = StringProperty()
        app.player_surname_to_edit = StringProperty()
        #self.category_chosen_sql_players = self.category_chosen_sql_players

    def on_kv_post(self, base_widget):
        pass
 # Imam opciju da svaki put čitam bazu ili tek kad otvorim category manager učita iz baze u rječnik       
    def fetch_players(self, category):
        self.player_box = self.ids.player_box
        if self.sql_manager.open_category_player_data(category):
            self.player_box.clear_widgets()
            for number, player in enumerate(self.sql_manager.open_category_player_data(category)):
                player_label = ToggleButton(text=f'{number + 1}. {player[2]}, {player[1]}',
                                            group="player_button", 
                                            height=50,
                                            text_size=(self.width - 130, None),
                                            size_hint_y=None)
                player_label.bind(on_press=self.on_toggle_press)
#                player_label.bind(on_state=self.on_toggle_state)
                self.player_box.add_widget(player_label)
                print(player)
        else:
            # provjera category chosen
            print(f'Kategorija odabrana {category}')
            self.player_box.clear_widgets()
            player_label = Label(text='Nema unesenih igrača', halign='left', valign='middle', height=50, size_hint_y=None)
            self.player_box.add_widget(player_label)
    def on_toggle_press(self, instance):
        player_to_edit = instance.text[2:].replace(',', '').split()
        self.player_name_to_edit = player_to_edit[1]
        self.player_surname_to_edit = player_to_edit[0]
        print(f'Op op {self.player_surname_to_edit, self.player_name_to_edit}')
        #self.player_to_edit_string = ', '.join(self.player_to_edit)
        return self.player_surname_to_edit, self.player_name_to_edit
        
"""    def on_toggle_state(self):
        for child in self.player_box.children:
            if isinstance(child, ToggleButton) and child.state == 'down':
                App.get_running_app().edit_button_disabled = True  # At least one toggle button is pressed
            App.get_running_app().edit_button_disabled = False  # None of the toggle buttons are pressed
        print(widget.state)
        print(self.edit_button_disabled)
        if widget.state == 'DOWN':
            self.edit_button_disabled = False
            print(self.edit_button_disabled)
        else:
            self.edit_button_disabled = True
            print(self.edit_button_disabled) """

class ScreenAddPlayer(Screen):
    def __init__(self, **kw):
        super(ScreenAddPlayer, self).__init__(**kw)
        self.sql_manager = SqlManager()

    def new_player(self, category_chosen_sql_players, second_name, name):
        player_list = [(second_name, name)]
        print(player_list, App.get_running_app().category_chosen_sql_players)
        self.sql_manager.insert_category_player_data(category_chosen_sql_players, player_list)

class ScreenEditPlayer(Screen):
    def __init__(self, **kw):
        super(ScreenEditPlayer, self).__init__(**kw)
        app = App.get_running_app()
        #player_name_to_edit = app.player_name_to_edit
        #player_surname_to_edit = app.player_surname_to_edit


class ScreenTrainingManager(Screen):
    def __init__(self, **kw):
        super(ScreenTrainingManager, self).__init__(**kw)

class ScreenAddTraining(Screen):
    def __init__(self, **kw):
        super(ScreenAddTraining, self).__init__(**kw)

class ScreenEditTraining(Screen):
    def __init__(self, **kw):
        super(ScreenEditTraining, self).__init__(**kw)

class ScreenReports(Screen):
    def __init__(self, **kw):
        super(ScreenReports, self).__init__(**kw)

class MyScreenManager(ScreenManager):
    pass

class MyFootballApp(App):
    # Glavne varijable - možda se može i maknuti property?
    category_chosen = StringProperty()
    category_chosen_sql_players = StringProperty()
    category_chosen_sql_sessions = StringProperty()
    category_button_disabled = BooleanProperty()
    klub = StringProperty()
    edit_button_disabled = BooleanProperty(False)
    
    def build(self): 
        self.category_chosen = 'NEMA KATEGORIJE'
        self.category_button_disabled = True
        self.klub = 'NK TOPLICE'
        self.sql_manager = SqlManager()
        self.screen_intro = ScreenIntro()
                
        self.sql_manager_instance = SqlManager()
        screen_intro = ScreenIntro()
        
        self.check_table = self.sql_manager.check_table()
        # Provjera za početak - ako imamo otvorenu kategoriju, prva u bazi može biti odabrana gumbom i gumb nije isključen
        
        if self.check_table:
            self.category_chosen = self.check_table[0].replace('_igraci', '').upper().replace('_', ' ')
            self.category_chosen_sql_players = self.check_table[0]
            self.category_chosen_sql_sessions = self.check_table[1]
            self.category_button_disabled = False
# Provjera - naknadno brisanje
            print(self.category_chosen, self.category_chosen_sql_players, self.category_chosen_sql_sessions)
        kv = Builder.load_file('myfootball.kv')
        return kv   
    
    def update_category_chosen_sql(self, category_chosen):
        self.category_chosen_sql_players = category_chosen.lower().replace(' ','_') + '_igraci'
        self.category_chosen_sql_sessions = category_chosen.lower().replace(' ','_') + '_dolasci'
        print(self.category_chosen, self.category_chosen_sql_players, self.category_chosen_sql_sessions)
    
              

if __name__ == "__main__":
    MyFootballApp().run()