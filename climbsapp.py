from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.relativelayout import MDRelativeLayout
from kivy.metrics import dp
from kivy.core.window import Window
import sqlite3
from time import sleep
from time import tzname
import json
import io
import os
import numpy as np
from time import time
from datetime import datetime
from calendar import timegm
import scipy.optimize as opt
import scipy.stats as st
#import matplotlib.pyplot as plt
from math import floor
import logging
from kivy_garden.graph import Graph, MeshLinePlot



#logging.getLogger('matplotlib.font_manager').disabled = True

    
def create_settings_file():
    default_settings = {'boulder_grading':'USA','route_grading':'YDS','current_grade': 'N/A','current_slope':'N/A'}
    json_object = json.dumps(default_settings, indent=4)
    with open('settings.json','w') as settings_file:
        settings_file.write(json_object)


class MainMenuScreen(Screen):
    pass

class EntryScreen(Screen):
    def __init__(self,**kwargs):
        super(EntryScreen,self).__init__(**kwargs)
        self.types = None

class EntryChoiceScreen(Screen):
    pass

class EditScreen(Screen):
    def __init__(self,**kwargs):
        super(EditScreen,self).__init__(**kwargs)
        self.page = 0

class EditEntryScreen(Screen):
    def __init__(self,**kwargs):
        super(EditEntryScreen,self).__init__(**kwargs)
        self.row_data = None
        self.row_id = None

class SettingsScreen(Screen):
    def __init__(self,**kwargs):
        super(SettingsScreen,self).__init__(**kwargs)
        self.startupCheck()
        self.previous_screen = None
        self.boulder_setting = None
        self.route_setting = None
        self.current_grade = None
        self.current_slope = None
        self.timezone = 'EST'

        with open('settings.json','r+') as settings_file:
            settings_data = json.load(settings_file)
            self.boulder_setting = settings_data['boulder_grading']
            self.route_setting = settings_data['route_grading']
            self.current_grade = settings_data['current_grade']
            self.current_slope = settings_data['current_slope']

    def startupCheck(self):
        if os.path.isfile('settings.json') and os.access('settings.json',os.R_OK):
            pass
        else:
            create_settings_file()

    

    

class GradingScreen(Screen):
    pass
class ProgressScreen(Screen):
    def __init__(self,**kwargs):
        super(ProgressScreen,self).__init__(**kwargs)
        self.date_dict = {}
        self.bsystem, self.rsystem = self.get_grade_settings()
        self.timezone = 'EST'
        self.bodata, self.rodata =  self.get_timeline_data()
        
        
        


    def get_grade_settings(self):
        with open('settings.json','r+') as settings_file:
            settings_data = json.load(settings_file)
            bsystem= settings_data['boulder_grading'].lower()
            rsystem = settings_data['route_grading'].lower()
            return bsystem, rsystem

    def get_timeline_data(self):
        bldr_data = sqlite3.connect('boulder_data.db')
        cur = bldr_data.cursor()
        bo_datatable = self.bsystem + '_timeline'
        ro_datatable = self.rsystem + '_timeline'

        bodata_raw = cur.execute('SELECT * FROM %s' % bo_datatable).fetchall()
        rodata_raw = cur.execute('SELECT * FROM %s' % ro_datatable).fetchall()

        cur.close()
        bldr_data.close()

        bpoints = self.create_points(bodata_raw)
        rpoints = self.create_points(rodata_raw)


        return bpoints,rpoints

    def sort_by_date(self,data):
        utc_data = []
        for i in data:
            year = int(i[0][:4])
            month = int(i[0][5:7])
            day = int(i[0][8:10])
            datetime_object = datetime(year,month,day,0,0,0)
            utc = self.GMT_to_timezone(timegm(datetime_object.timetuple()),self.timezone)
            utc_data.append((utc,i[1]))

        sorted_data = sorted(utc_data)
        return sorted_data
            


    def GMT_to_timezone(self,date,timezone):
        timezone_dict = {'GMT':0,'EST':14400}
        return date + timezone_dict[timezone]

    def timestamp_to_date(self,timestamp):
        date = str(datetime.fromtimestamp(timestamp))
        return date[:10]

    def create_points(self,data):
        points = []
        if len(data)>0:
            sorted_data = self.sort_by_date(data)
            start_time = sorted_data[0][0]
            end_time = sorted_data[len(sorted_data)-1][0] + 10*86400
            days_between = int((end_time - start_time)/86400)
            for i in range(days_between):
                day_i = start_time + 86400*i
                rel_time = (day_i - start_time)/86400
                if rel_time not in self.date_dict:
                    self.date_dict[rel_time] = self.timestamp_to_date(day_i)

            for i in sorted_data:
                if i[1] != 'N/A':
                    rel_time = (i[0] - start_time)/86400
                    point = (rel_time,float(i[1]))
                    points.append(point)
        return points

class Plot(MDRelativeLayout):
    def __init__(self,types,points,x_tick_names=None,y_tick_names=None,**kwargs):
        super(Plot,self).__init__(**kwargs)
        self.types = types
        self.x_tick_names = x_tick_names
        self.y_tick_names = y_tick_names
        self.max_x,self.max_y = self.set_max_values(points)
        self.graph = Graph(x_alt_ticks=self.x_tick_names,y_alt_ticks=self.y_tick_names,xlabel="Date", ylabel="Grade", x_ticks_minor=5, x_ticks_major=5, y_ticks_major=1,
                           y_grid_label=True, x_grid_label=True, x_grid=True, y_grid=True,
                           xmin=-0, xmax=self.max_x, ymin=0, ymax=self.max_y, draw_border=False,x_ticks_angle=45)
        

        self.plot = MeshLinePlot(color=[1, 1, 1, 1])
        self.plot.points = points
        self.add_widget(self.graph)
        #print(self.graph._xlabel)

        self.graph.add_plot(self.plot)
        

    def set_max_values(self,data):

        high_x = data[len(data)-1][0]
        high_y = 0
        for i in data:
            if i[1] > high_y:
                high_y = i[1]

        max_x = high_x + (10 - (high_x % 10))
        max_y = high_y + (5 - (high_y % 5))

        return max_x,max_y


        
        

        
        
        
        
            
            
        
        

sm = ScreenManager()
sm.add_widget(MainMenuScreen(name='Main Menu'))
sm.add_widget(EntryScreen(name='Entry'))
sm.add_widget(EntryChoiceScreen(name='EntryChoice'))
sm.add_widget(EditScreen(name='Edit'))
sm.add_widget(EditEntryScreen(name='EditEntry'))
sm.add_widget(SettingsScreen(name='Settings'))
sm.add_widget(GradingScreen(name='Grading'))
sm.add_widget(ProgressScreen(name='Progress'))

#x=[1,2,3]
#y = [1,2,3]
#plt.plot(x,y)
#plt.ylabel('y')
#plt.xlabel('x')

class BoulderBuddyApp(MDApp):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        
        self.vgrades = self.create_grades_list('bouldering','USA')
        self.fontgrades = self.create_grades_list('bouldering','FONT')
        self.dangrades = self.create_grades_list('bouldering','DAN')
        self.yds = self.create_grades_list('route','YDS')
        self.fr = self.create_grades_list('route','FR')
        self.aus = self.create_grades_list('route','AUS')
        
        self.root = Builder.load_file('boulder_entry.kv')
        self.set_carousel()
        self.create_datatables()
        self.set_grade_display()

        grade_dict = self.make_grade_dict('usa')
        date_dict = self.root.get_screen('Progress').date_dict
        


        bpoints = self.root.get_screen('Progress').bodata
        self.bgraph = Plot('bouldering',bpoints,x_tick_names=date_dict,y_tick_names=grade_dict,size_hint_y=None,height=500)
        container = self.root.get_screen('Progress').ids.graph_container
        container.bind(minimum_size=container.setter('size'))
        container.add_widget(self.bgraph)

        




    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        
        return self.root

    def create_datatables(self):
        bldr_data = sqlite3.connect("boulder_data.db")
        cur = bldr_data.cursor()
        datatables = ['usa','font','dan','yds','fr','aus']
        timeline_datatables = []
        for i in datatables:
            timeline_datatables.append(i + '_timeline')
        
        for i in datatables:
            cur.execute('''CREATE TABLE IF NOT EXISTS %s
                        (id INT, date TEXT, grade TEXT, attempts INT, completed INT)''' % i)
            bldr_data.commit()

        for i in timeline_datatables:
            cur.execute('''CREATE TABLE IF NOT EXISTS %s
                        (date TEXT, grade TEXT)''' % i)
            bldr_data.commit()
        
        cur.close()
        bldr_data.close()

    def create_grades_list(self,types,system):
        grades = []
        if types == 'bouldering':
            if system == 'USA':
                for i in range(18):
                    vgrade = 'V' + str(i)
                    dropdown_item = {'viewclass': 'OneLineListItem', 'text':vgrade, 'on_release': lambda x=vgrade:self.grade_callback(x)}
                    grades.append(dropdown_item)
                    
            if system == 'FONT':
                fontgrades = ['4','4+','5','5+']
                for i in range(6,9):
                    for j in ['a','b','c']:
                        fontgrades.append(str(i)+j)
                        fontgrades.append(str(i)+j+'+')
                fontgrades.append('9a')

                for i in fontgrades:
                    dropdown_item = {'viewclass': 'OneLineListItem', 'text':i, 'on_release': lambda x=i:self.grade_callback(x)}
                    grades.append(dropdown_item)

            if system == 'DAN':
                dangrades = []
                for i in range(7):
                    kyu = str(7-i) + ' kyu'
                    dangrades.append(kyu)
                for i in range(1,7):
                    dan = str(i) + ' dan'
                    dangrades.append(dan)

                for i in dangrades:
                    dropdown_item = {'viewclass': 'OneLineListItem', 'text':i, 'on_release': lambda x=i:self.grade_callback(x)}
                    grades.append(dropdown_item)

        if types == 'route':
            if system == 'YDS':
                ydsgrades = []
                for i in range (1,10):
                    grade = '5.' + str(i)
                    ydsgrades.append(grade)
                for i in range(10,16):
                    for j in ['a','b','c','d']:
                        grade = '5.' + str(i) + j
                        ydsgrades.append(grade)

                for i in ydsgrades:
                    dropdown_item = {'viewclass': 'OneLineListItem', 'text':i, 'on_release': lambda x=i:self.grade_callback(x)}
                    grades.append(dropdown_item)

            if system == 'FR':
                frgrades = ['1','2','3','4','5a','5b','5c']
                for i in range(6,10):
                    for j in ['a','b','c']:
                        grade1 = str(i) + j
                        grade2 = str(i) + j + '+'
                        frgrades.append(grade1)
                        frgrades.append(grade2)

                for i in frgrades:
                    dropdown_item = {'viewclass': 'OneLineListItem', 'text':i, 'on_release': lambda x=i:self.grade_callback(x)}
                    grades.append(dropdown_item)

            if system == 'AUS':
                ausgrades = []
                for i in range(40):
                    ausgrades.append(str(i))

                for i in ausgrades:
                    dropdown_item = {'viewclass': 'OneLineListItem', 'text':i, 'on_release': lambda x=i:self.grade_callback(x)}
                    grades.append(dropdown_item)
                
        return grades
    
    


    def set_carousel(self):
        bogrades = {'USA':0,'FONT':1,'DAN':2}
        rogrades = {'YDS':0,'FR':1,'AUS':2}
        
        self.root.get_screen('Grading').ids.bocar.index = bogrades[self.root.get_screen('Settings').boulder_setting]
        self.root.get_screen('Grading').ids.rocar.index = rogrades[self.root.get_screen('Settings').route_setting]

    def grade_callback(self,grade):
        current_screen = self.root.current
        self.root.get_screen(current_screen).ids.grade.text = grade
        self.grade_menu.dismiss()


    def set_current_grade_system(self,types):
        settings = self.root.get_screen('Settings')
        if types == 'boulder':
            grade_systems = {'USA':self.vgrades,'FONT':self.fontgrades,'DAN':self.dangrades}
            return grade_systems[settings.boulder_setting]
        if types == 'route':
            grade_systems = {'YDS':self.yds,'FR':self.fr,'AUS':self.aus}
            return grade_systems[settings.route_setting]
    
    def open_grade_menu(self):
        current_screen = self.root.current
        current_grade_system = self.set_current_grade_system(self.root.get_screen('Entry').types)
        self.grade_menu = MDDropdownMenu(caller=self.root.get_screen(current_screen).ids.grade,items = current_grade_system,width_mult=2)
        self.grade_menu.open()

    def open_edit_grade_menu(self):
        current_screen = self.root.current
        current_grade_system = None
        if self.root.get_screen('Edit').page == 0:
            current_grade_system = self.set_current_grade_system('boulder')
        if self.root.get_screen('Edit').page == 1:
            current_grade_system = self.set_current_grade_system('route')
        self.grade_menu = MDDropdownMenu(caller=self.root.get_screen(current_screen).ids.grade,items = current_grade_system,width_mult=2)
        self.grade_menu.open()

    def update_screen(self):
        current_screen = self.root.current
        self.root.get_screen('Settings').previous_screen = current_screen
        
        
    def clear(self):
        current_screen = self.root.current
        self.root.get_screen(current_screen).ids.date.text = ""
        self.root.get_screen(current_screen).ids.grade.text = ""
        self.root.get_screen(current_screen).ids.attempts.text = ""

    def on_save(self,value,instance,date_range):
        current_screen = self.root.current
        self.root.get_screen(current_screen).ids.date.text = str(instance)

    def show_date_picker(self):
        date_dialog = MDDatePicker()
        date_dialog.bind(on_save=self.on_save)
        date_dialog.open()


    def input_data(self):
        date = self.root.get_screen('Entry').ids.date.text
        grade = self.root.get_screen('Entry').ids.grade.text
        attempts = self.root.get_screen('Entry').ids.attempts.text
        completed = self.root.get_screen('Entry').ids.complete.active

        datatable = None
        if self.root.get_screen('Entry').types == 'boulder':
            datatable = self.root.get_screen('Settings').boulder_setting.lower()
        if self.root.get_screen('Entry').types == 'route':
            datatable = self.root.get_screen('Settings').route_setting.lower()

        bldr_data = sqlite3.connect("boulder_data.db")
        cur = bldr_data.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS %s
                    (id INT, date TEXT, grade TEXT, attempts INT, completed INT)''' % datatable)
        bldr_data.commit()

        cur.execute('''SELECT * FROM %s''' % datatable)

        idnum = len(cur.fetchall()) + 1
        cur.execute('''INSERT INTO %s (id, date, grade, attempts,completed) VALUES (?,?,?,?,?)''' % datatable,(idnum,date,grade,attempts,completed))
        bldr_data.commit()

        cur.close()
        bldr_data.close()

        timezone = self.root.get_screen('Settings').timezone
        timeline_grade = self.MLE(datatable,timezone,self.date_to_utc(date))[1]
        self.update_MLE(date,timeline_grade,datatable)
        self.update_timeline_table(date,datatable)
        self.clear()

    def edit_data(self):
        idnum = self.root.get_screen('EditEntry').row_id
        date = self.root.get_screen('EditEntry').ids.date.text
        grade = self.root.get_screen('EditEntry').ids.grade.text
        attempts = self.root.get_screen('EditEntry').ids.attempts.text
        completed = self.root.get_screen('EditEntry').ids.complete.active
        old_data = self.root.get_screen('EditEntry').row_data
        new_data = (date,grade,attempts,completed)

        bldr_data = sqlite3.connect("boulder_data.db")
        cur = bldr_data.cursor()

        datatable = None
        if self.root.get_screen('Edit').page == 0:
            datatable = self.root.get_screen('Settings').boulder_setting.lower()
        if self.root.get_screen('Edit').page == 1:
            datatable = self.root.get_screen('Settings').route_setting.lower()

        cur.execute('''UPDATE %s SET date = ?, grade = ?, attempts = ?, completed = ? WHERE id = ?''' % datatable,(new_data[0],new_data[1],new_data[2],new_data[3],idnum))
        bldr_data.commit()

        cur.close()

        bldr_data.close()

        self.update_timeline_table(date,datatable)
        self.displaydatatable()
        self.root.transition.direction = 'right'
        self.root.current = 'Edit'
        
        

    def pull_data(self,datatable):
        bldr_data = sqlite3.connect("boulder_data.db")
        cur = bldr_data.cursor()
        cur.execute('SELECT * FROM %s' % datatable)
        raw_data = cur.fetchall()
        data = []
        for i in raw_data:
            date = i[1]
            grade = i[2]
            attempts = i[3]
            completed = i[4]
            dpoint = (date,grade,attempts,completed)
            data.append(dpoint)
        
        cur.close()
        bldr_data.close()
        return data


    def row_select(self,instance,row):
        rows_per_page = 5
        fake_row_num = int(row.index/len(instance.column_data))
        page_label_text = instance.children[0].children[0].children[2].text
        page_num_uncombined = []
        for i in page_label_text:
            if i != '-':
                page_num_uncombined.append(i)
            else:
                break
        page_num = floor(int(''.join(page_num_uncombined))/rows_per_page)
        row_num = fake_row_num + rows_per_page*page_num
        
        
        
        row_data = instance.row_data[row_num]
        self.root.get_screen('EditEntry').row_id = row_num + 1
        self.root.get_screen('EditEntry').row_data = row_data
        self.root.get_screen('EditEntry').ids.date.text = str(row_data[0])
        self.root.get_screen('EditEntry').ids.grade.text = str(row_data[1])
        self.root.get_screen('EditEntry').ids.attempts.text = str(row_data[2])
        self.root.get_screen('EditEntry').ids.complete.active = row_data[3]

        self.root.transition.direction = 'left'
        self.root.current = 'EditEntry'
    
    def displaydatatable(self):
        data = None
        if self.root.get_screen('Edit').page == 0:
            datatable = self.root.get_screen('Settings').boulder_setting.lower()
            data = self.pull_data(datatable)
        if self.root.get_screen('Edit').page == 1:
            datatable = self.root.get_screen('Settings').route_setting.lower()
            data = self.pull_data(datatable)
        
        bldrtable = MDDataTable(
            pos_hint = {'center_x':0.5,'center_y':0.5},
            size_hint = (0.9,0.6),
            use_pagination = True,
            pagination_menu_pos = 'auto',
            rows_num = 5,
            column_data = [
                ("Date", dp(34)),
                ("Grade",dp(34)),
                ("Attempts",dp(34)),
                ("Completed",dp(34))
            ],
            row_data = data
            )
        bldrtable.bind(on_row_press = self.row_select)
        self.root.get_screen('Edit').add_widget(bldrtable)
        
        
    #if anyone reads this code. I know this is stupid. I know this is all stupid. shut up im lazy.  
    def SettingsReturn(self):
        self.root.transition.direction = 'right'
        self.root.current = self.root.get_screen('Settings').previous_screen

    def SetGradeSettings(self):
        boulder_grade = self.root.get_screen('Grading').ids.bocar.current_slide.children[1].text
        route_grade = self.root.get_screen('Grading').ids.rocar.current_slide.children[1].text

        self.root.get_screen('Settings').boulder_setting = boulder_grade
        self.root.get_screen('Settings').route_setting = route_grade

        with open('settings.json','r+') as settings_file:
            data = json.load(settings_file)
            data['boulder_grading'] = boulder_grade
            data['route_grading'] = route_grade
            settings_file.seek(0)
            json.dump(data, settings_file, indent = 4)
            settings_file.truncate()

        self.root.transition.direction = 'right'
        self.root.current = 'Settings'

    def GMT_to_timezone(self,date,timezone):
        timezone_dict = {'GMT':0,'EST':14400}
        return date + timezone_dict[timezone]
        

    #probability of sending a climb
    def psend(self,m,c,r):
        #m is the slope, c is the climbers grade, r is the routes grade:
        return 1/(1+np.exp(m*(r-c)))

    def pnosend(self,m,c,r):
        return 1 - (1/(1+np.exp(m*(r-c))))
        

    def logL(self,log_par,send_data,nosend_data):
        m,c = np.exp(log_par)
        logL = np.sum(np.log(self.psend(m,c,send_data))) + np.sum(np.log(self.pnosend(m,c,nosend_data)))
        return logL
        

    def time_filter(self,data,timezone,start_date):
        filtered_data = []
        current_date = start_date
        for i in data:
            year = int(i[0][:4])
            month = int(i[0][5:7])
            day = int(i[0][8:10])

            date = datetime(year,month,day,0,0,0)
            utc_date = self.GMT_to_timezone(timegm(date.timetuple()),timezone)
            time_dif = current_date - utc_date
            if time_dif <= 2592000 and time_dif >= 0:
                filtered_data.append(i)
        return filtered_data
            
    def grade_to_number(self,grade,system):
        if system == 'usa':
            number = int(grade[1:])
            return number

    def number_to_grade(self,number,system):
        if type(number) is str:
            return 'N/A'
        num = round(number,1)
        if system == 'usa':
            grade = 'V' + str(num)
            return grade

    def make_grade_dict(self,system):
        grade_dict = {}
        if system == 'usa':
            for i in range(18):
                grade = self.number_to_grade(i,system)
                grade_dict[i] = grade

        return grade_dict

    def make_date_dict(self):
        pass


    def MLE(self,gsystem,timezone,date=time()):
        data = self.pull_data(gsystem)
        time_filtered_data = self.time_filter(data,timezone,date)
        send_data = []
        nosend_data = []

        for i in time_filtered_data:
            if int(i[3]) == 1:
                attempts = int(i[2])
                for j in range(attempts-1):
                    nosend_data.append(self.grade_to_number(i[1],gsystem))
                send_data.append(self.grade_to_number(i[1],gsystem))
            if int(i[3]) == 0:
                attempts = int(i[2])
                for j in range(attempts):
                    nosend_data.append(self.grade_to_number(i[1],gsystem))

        true_len = len(send_data) + len(nosend_data)
        if true_len <= 10:
            m = 'N/A'
            c = 'N/A'
            return m,c
        
        res = opt.minimize(
            fun = lambda log_params,send_data,nosend_data: -self.logL(log_params,send_data,nosend_data),
            x0 = np.array([1,1]), args = (send_data,nosend_data), method = 'BFGS')
        m,c = np.exp(res.x)
        return m,c

    def set_grade_display(self):
        gsystem = self.root.get_screen('Settings').boulder_setting.lower()
        self.root.get_screen('Main Menu').ids.currentgrade.text = self.number_to_grade(self.root.get_screen('Settings').current_grade,gsystem)

    def update_MLE(self,date,grade,gsystem):
        timezone = self.root.get_screen('Settings').timezone
        with open('settings.json','r+') as settings_file:
            data = json.load(settings_file)
            m,c = self.MLE(gsystem,timezone)
            data['current_slope'] = m
            data['current_grade'] = c
            self.root.get_screen('Main Menu').ids.currentgrade.text = self.number_to_grade(data['current_grade'],gsystem)
            self.root.get_screen('Settings').ids.current_grade = self.number_to_grade(data['current_grade'],gsystem)
            self.root.get_screen('Settings').ids.current_slope = m
            settings_file.seek(0)
            json.dump(data,settings_file,indent=4)
            settings_file.truncate()

            bldr_data = sqlite3.connect('boulder_data.db')
            cur = bldr_data.cursor()
            
            datatable = gsystem + '_timeline'
            date_list = []
            cur.execute('SELECT * FROM %s' % datatable)
            raws = cur.fetchall()
            for i in raws:
                date_list.append(i[0])
            if date not in date_list:
                cur.execute('INSERT INTO %s (date,grade) VALUES (?,?)' % datatable, (date,grade))
                bldr_data.commit()
            else:
                cur.execute('UPDATE %s SET grade = ? WHERE date = ?' % datatable, (grade,date))
                bldr_data.commit()
            
            cur.close()
            bldr_data.close()
            

            

        


    def get_gradetime_data(self,datatable,timezone='EST'):
        dates = []
        grades = []

        bldr_data = sqlite3.connect('boulder_data.db')
        cur = bldr_data.cursor()
        cur.execute('SELECT * FROM %s' % datatable)
        raw_data = cur.fetchall()


        for i in raw_data:
            if i[1] not in dates:
                year = int(i[1][:4])
                month = int(i[1][5:7])
                day = int(i[1][8:10])
                date = datetime(year,month,day,0,0,0)
                utc_date = self.GMT_to_timezone(timegm(date.timetuple()),timezone)
                grade = self.MLE('usa','EST',utc_date)[1]
                if grade != 'N/A':
                    dates.append(i[1])
                    grades.append(grade)

        cur.close()
        bldr_data.close()

        return dates,grades


    #make a way to get the exact time you submitted or edited a datapoint and then take the immediate 30 days afterwards (or however many there are) and recalculate those values
    
    def date_to_utc(self,date):
        timezone = self.root.get_screen('Settings').timezone
        year = int(date[:4])
        month = int(date[5:7])
        day = int(date[8:10])
        datetime_object = datetime(year,month,day,0,0,0)
        utc = self.GMT_to_timezone(timegm(datetime_object.timetuple()),timezone)
        return utc

    def update_timeline_table(self,date,gsystem):
        datatable = gsystem + '_timeline'
        
        timezone = self.root.get_screen('Settings').timezone
        bldr_data = sqlite3.connect('boulder_data.db')
        cur = bldr_data.cursor()
        

        cur.execute('SELECT * FROM %s' % datatable)
        raw_data = cur.fetchall()
        utc_date = self.date_to_utc(date)
        for i in raw_data:
            utc_date_data = self.date_to_utc(i[0])
            if utc_date_data - utc_date <=2592000 and utc_date_data - utc_date >=0:
                grade = self.MLE(gsystem,timezone,utc_date_data)[1]
                cur.execute('UPDATE %s SET grade = ? WHERE date = ?' % datatable, (grade,date))
                bldr_data.commit()
                    
        cur.close()
        bldr_data.close()

        prog_screen = self.root.get_screen('Progress')
        prog_screen.bodata,prog_screen.rodata = prog_screen.get_timeline_data()
        self.bgraph.plot.points = prog_screen.bodata
        
        
        
        
            


        


        
            
            
        
        #filter data for last 30 days(thats the climbing period)
        #create a list of negative log(psends) with the r variable filled in
        #create use scipy minimize to find the parameters needed for minimization

        #later this model will be updated to include a time dependent version
        #also possibly model learning rate/learning bonus effect but thats waaay down the line

        



        
def generate_fake_dataset():
    pass
    


BoulderBuddyApp().run()
Window.close()





























"""import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button


class MyGridLayout(GridLayout):
    def __init__(self,**kwargs):
        super(MyGridLayout,self).__init__(**kwargs)

        self.cols = 2

        self.add_widget(Label(text="Date: "))
        self.date = TextInput(multiline = False)
        self.add_widget(self.date)

        self.add_widget(Label(text="Grade: "))
        self.grade = TextInput(multiline = False)
        self.add_widget(self.grade)

        self.add_widget(Label(text="Attempts: "))
        self.attempts = TextInput(multiline = False)
        self.add_widget(self.attempts)
    
    

    

class Climber(App):
    def build(self):
        return MyGridLayout()


if __name__ == '__main__':
    Climber().run()
    Window.close()
"""
