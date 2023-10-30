from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.pickers import MDDatePicker
from kivy.uix.textinput import TextInput
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.label import MDLabel
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.widget import Widget
import sqlite3
from time import sleep
from time import tzname
import json
import io
import os
import numpy as np
from time import time
from datetime import datetime, date
from calendar import timegm
import scipy.optimize as opt
import scipy.stats as st
#import matplotlib.pyplot as plt
from math import floor, ceil
import logging
from kivy_garden.graph import Graph, MeshLinePlot
from kivy.animation import Animation
from kivymd.uix.behaviors.toggle_behavior import MDToggleButton
from kivymd.uix.button import MDFlatButton
from kivy.core.text import LabelBase
from kivymd.uix.card import MDCard
from kivymd.uix.anchorlayout import MDAnchorLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.uix.image import Image
from kivy.graphics import *
from kivy.config import Config
from kivymd.uix.button import MDRoundFlatButton
LabelBase.register(name='SometypeMono',fn_regular='Fonts\SometypeMono-Regular.ttf',fn_bold='Fonts\SometypeMono-Bold.ttf')
'''Config.set('graphics','width',850)
Config.set('graphics','height',850)
Config.write()'''
x_px = 2340
y_px = 1080
dpi = 425

x_dp = x_px/(dpi/160)
y_dp = y_px/(dpi/160)
Window.size = (300,600)


#logging.getLogger('matplotlib.font_manager').disabled = True
class MyToggleButton(MDFlatButton, MDToggleButton):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.background_down = self.theme_cls.primary_color


def create_settings_file():
    default_settings = {'boulder_grading':'USA','route_grading':'YDS','current_boulder_grade': 'N/A','current_boulder_slope':'N/A','current_route_grade':'N/A','current_route_slope':'N/A'}
    json_object = json.dumps(default_settings, indent=4)
    with open('settings.json','w') as settings_file:
        settings_file.write(json_object)

        

class MainMenuScreen(Screen):
    pass

class EntryScreen(Screen):
    def __init__(self,**kwargs):
        super(EntryScreen,self).__init__(**kwargs)
        self.types = 'boulder'
        self.date = self.current_date()
        self.grade = None
        self.attempts = 1
        self.comp = 0
        self.edit = False
        self.caller = None

        self.on_widget = None

    def setup_grade_buttons(self):
        container = self.ids.gradecontainer
        container.clear_widgets()
        grade_list = []
        if self.types == 'boulder':
            bsetting = MDApp.get_running_app().root.get_screen('Settings').boulder_setting
            grade_list_raw = MDApp.get_running_app().create_grades_list(bsetting.upper())
            for i in grade_list_raw:
                grade_list.append(i['text'])
        if self.types == 'route':
            rsetting = MDApp.get_running_app().root.get_screen('Settings').route_setting
            grade_list_raw = MDApp.get_running_app().create_grades_list(rsetting.upper())
            for i in grade_list_raw:
                grade_list.append(i['text'])
        for i in grade_list:
            new_button = MDRoundFlatButton(text=i,on_press=self.gradechoice)
            new_button.font_name = 'SometypeMono'
            container.add_widget(new_button)
        
            
    def gradechoice(self,widget):
        if self.on_widget:
            self.on_widget.md_bg_color = (1,1,1,0)
        widget.md_bg_color = (1,1,1,1)
        self.on_widget = widget
        self.grade = widget.text

    def change_grade_state(self,widget):
        self.types = widget.text.lower()
        container = self.ids.gradecontainer
        container.clear_widgets()
        self.setup_grade_buttons()
        

    def current_date(self):
        cdate = date.today()
        return str(cdate)


    def clear_data(self):
        self.types = 'boulder'
        self.date = self.current_date()
        self.grade = None
        self.attempts = 1
        self.comp = 0

    def clear_display(self):
        self.clear_data()
        self.setup_grade_buttons()
        self.ids.date.text = self.date
        self.ids.bstate.state = 'down'
        self.ids.rstate.state = 'normal'
        
        if self.on_widget:
            self.on_widget.md_bg_color=(1,1,1,0)
        self.ids.attempts.text = str(self.attempts)
        self.ids.complete.active = self.comp
        

    def plus(self,widget):
        self.attempts += 1
        widget.text = str(self.attempts)

    def minus(self,widget):
        if self.attempts > 1:
            self.attempts -= 1
            widget.text = str(self.attempts)

    def on_save(self,value,instance,date_range):
        self.date = str(instance)
        self.ids.date.text = str(instance)

    def show_date_picker(self):
        date_dialog = MDDatePicker()
        date_dialog.bind(on_save=self.on_save)
        date_dialog.open()

    def get_data(self):
        return self.date,self.grade,self.attempts,self.comp,self.types
        
    def fill(self):
        self.date,self.grade,self.attempts,self.comp,self.types = self.caller.get_data()
        self.setup_grade_buttons()
        if self.types == 'route':
            self.ids.bstate.state = 'normal'
            self.ids.rstate.state = 'down'
        gradebuttons = self.ids.gradecontainer.children
        for i in gradebuttons:
            if i.text == self.caller.grade:
                self.on_widget = i
                break

        button_num = len(self.ids.gradecontainer.children)
        button_index = button_num - self.ids.gradecontainer.children.index(self.on_widget) -1 
        scroll_val = button_index/button_num
        self.ids.gradescroller.scroll_x = scroll_val
        
        self.ids.date.text = self.caller.date
        self.on_widget.md_bg_color = 1,1,1,1
        self.ids.attempts.text = str(self.caller.attempts)
        self.ids.complete.active = self.caller.comp
        
        

    def shake_check(self,widget):
        correct_format = self.check_date_format(widget)
        if correct_format == False:
            self.shake(widget)
            widget.text = ''
        

    def check_date_format(self,widget):
        date_input = widget.text
        if len(date_input) != 10:
            return False

        year = date_input[:4]
        month = date_input[5:7]
        day = date_input[8:10]
        dash1 = date_input[4]
        dash2 = date_input[7]
        day_dict = {1:31,2:29,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}
        leap_year = None
        if int(year) % 4 == 0:
            leap_year = True
        else:
            leap_year = False


        if len(year) != 4 or len(month) != 2 or len(day) != 2:
            return False
        if int(month) > 12 or int(month) < 1:
            return False
        if dash1 != '-' or dash2 != '-':
            return False

        if int(day) > day_dict[int(month)] or int(day) < 1:
            return False
        if int(day) >= 29 and not leap_year and int(month) == 2:
            return False

        return True
        
        


    def shake(self,widget,*args):
        pos_hint_x = widget.pos_hint['center_x']
        pos_hint_y = widget.pos_hint['center_y']
        animate = Animation(
            pos_hint={'center_x':pos_hint_x+0.02,'center_y':pos_hint_y},
            duration=0.04)
        animate += Animation(
            pos_hint={'center_x':pos_hint_x-0.02,'center_y':pos_hint_y},
            duration=0.04)
        animate += Animation(
            pos_hint={'center_x':pos_hint_x,'center_y':pos_hint_y},
            duration=0.04)
        animate.start(widget)

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
        self.caller = None

    def fill(self):
        self.ids.date.text = self.caller.date
        self.ids.grade.text = self.caller.grade
        self.ids.attempts.text = self.caller.attempts
        self.ids.complete.active = self.caller.comp
        

class SettingsScreen(Screen):
    def __init__(self,**kwargs):
        super(SettingsScreen,self).__init__(**kwargs)
        self.startupCheck()
        self.previous_screen = None
        self.boulder_setting = None
        self.route_setting = None
        self.current_boulder_grade = None
        self.current_boulder_slope = None
        self.current_route_grade = None
        self.current_route_slope = None
        self.timezone = 'EST'

        self.retrieve_settings()

        

    def startupCheck(self):
        if os.path.isfile('settings.json') and os.access('settings.json',os.R_OK):
            pass
        else:
            create_settings_file()

    def retrieve_settings(self):
        with open('settings.json','r+') as settings_file:
            settings_data = json.load(settings_file)
            self.boulder_setting = settings_data['boulder_grading']
            self.route_setting = settings_data['route_grading']
            self.current_boulder_grade = settings_data['current_boulder_grade']
            self.current_boulder_slope = settings_data['current_boulder_slope']
            self.current_route_grade = settings_data['current_route_grade']
            self.current_route_slope = settings_data['current_route_slope']

    def update_settings_file(self):
        with open('settings.json','r+') as settings_file:
            data = json.load(settings_file)
            data['boulder_grading'] = self.boulder_setting
            data['route_grading'] = self.route_setting
            data['current_boulder_grade'] = self.current_boulder_grade
            data['current_boulder_slope'] = self.current_boulder_slope
            data['current_route_grade'] = self.current_route_grade
            data['current_route_slope'] = self.current_route_slope
            settings_file.seek(0)
            json.dump(data, settings_file, indent = 4)
            settings_file.truncate()


    

    

class GradingScreen(Screen):
    pass
class ProgressScreen(Screen):
    def __init__(self,**kwargs):
        super(ProgressScreen,self).__init__(**kwargs)
        self.date_dict = {}
        self.bsystem, self.rsystem = self.get_grade_settings()
        self.timezone = 'EST'
        self.bodata, self.rodata =  self.get_timeline_data()
        self.gstate = 'boulder'
        
        
        


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
        raw_date = str(datetime.fromtimestamp(timestamp))
        date = raw_date[:10]
        year = date[2:4]
        month = date[5:7]
        day = date[8:10]
        pretty = month + '/' + day
        return pretty

    def create_points(self,data):
        points = []
        if len(data)>0:
            sorted_data = self.sort_by_date(data)
            start_time = sorted_data[0][0]
            end_time = sorted_data[len(sorted_data)-1][0] + 10*86400
            days_between = int((end_time - start_time)/86400)
            day_max = ceil(days_between/5)*5
            for i in range(day_max+ceil(days_between/5)+1):
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
        self.graph = Graph(x_alt_ticks=self.x_tick_names,y_alt_ticks=self.y_tick_names,xlabel='', ylabel='', x_ticks_minor=5, x_ticks_major=ceil(self.max_x/5), y_ticks_major=1,
                           y_grid_label=True, x_grid_label=True, x_grid=False, y_grid=True,
                           xmin=-0, xmax=self.max_x, ymin=0, ymax=self.max_y, draw_border=False,x_ticks_angle=0)
        self.graph.font_name = 'SometypeMono'
        self.graph.font_size = '10sp'
        

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
        
        


class EntryItem(MDCard):
    def __init__(self,idnum = None,date=None,grade=None,attempts=None,comp=None,types=None,img=None,**kwargs):
        super(EntryItem, self).__init__(**kwargs)
        self.types = types
        self.img = img
        if self.img == None:
            if types == 'boulder':
                self.img = 'Images/rock.png'
            if types == 'route':
                self.img = 'Images/snowed-mountains.png'
            
        self.idnum = idnum
        self.date = date
        self.grade = grade
        self.attempts = attempts
        self.comp = comp
        self.bind(on_release=self.show_dropdown_menu)
        edit_option = {'text':'Edit','viewclass':'OneLineListItem','on_release':lambda x='edit': self.menu_callback(x)}
        delete_option = {'text':'Delete','viewclass':'OneLineListItem','on_release':lambda x='delete': self.menu_callback(x)}
        self.menu = [edit_option,delete_option]

        grid = MDGridLayout(cols=3)
        self.add_widget(grid)


        icon_layout = MDFloatLayout()
        lbl_layout = MDGridLayout(cols=1,rows=4,spacing=0)
        att_layout = MDFloatLayout()
        grid.add_widget(icon_layout)
        grid.add_widget(lbl_layout)
        grid.add_widget(att_layout)
        
        top_blank_anchor = MDAnchorLayout()
        bottom_blank_anchor = MDAnchorLayout()
        date_anchor = MDAnchorLayout(anchor_x='left',anchor_y='bottom')
        grade_anchor = MDAnchorLayout(anchor_x='left',anchor_y='top')
        lbl_layout.add_widget(top_blank_anchor)
        lbl_layout.add_widget(date_anchor)
        lbl_layout.add_widget(grade_anchor)
        lbl_layout.add_widget(bottom_blank_anchor)

        
        self.icon = Image(source=self.img,size_hint_x=None,size_hint_y=None,keep_ratio=False,allow_stretch=True,pos_hint={'center_x':0.45,'center_y':0.5})
        self.icon.size = icon_layout.size
        icon_layout.add_widget(self.icon)

        self.date_label = MDLabel(text=self.date,halign='left',size_hint_x=None)
        self.date_label.font_size = '12sp'
        self.date_label.font_name = 'SometypeMono'
        date_anchor.add_widget(self.date_label)
        

        self.grade_label =MDLabel(text=self.grade,halign='left',size_hint_x=None)
        self.grade_label.font_size = '24sp'
        self.grade_label.font_name='SometypeMono'
        grade_anchor.add_widget(self.grade_label)

        self.att_label = MDLabel(text=str(self.attempts),halign='center',size_hint_x=None,pos_hint={'center_x':0.5,'center_y':0.375})
        self.att_label.font_size='24sp'
        self.att_label.font_name='SometypeMono'
        att_layout.add_widget(self.att_label)

        self.att_text_label = MDLabel(text='attempts',halign='center',size_hint_x=None,pos_hint={'center_x':0.5,'center_y':0.625})
        self.att_text_label.font_size='12sp'
        self.att_text_label.font_name='SometypeMono'
        att_layout.add_widget(self.att_text_label)

        
        if self.comp == 1:
            self.md_bg_color = (0.3,0.4,0.1,1)
        elif self.comp == 0:
            self.md_bg_color = (0.85,0.14,0.31,1)
        else:
            print('ERROR')

        
        
        '''with self.canvas:
            padding = 20
            spacing = 10
            win_width = dp(300)
            Color(0,0,0,1)
            Line(points=[win_width*(2/3)-(1/3)*padding,padding,win_width*(2/3)-(1/3)*padding,padding+self.size[1]],width=1.1)'''
            

    def get_data(self):
        return self.date,self.grade,self.attempts,self.comp,self.types

    def update_display(self):
        self.icon.source = self.img
        self.date_label.text = str(self.date)
        self.grade_label.text = str(self.grade)
        self.att_label.text = str(self.attempts)
        if self.comp == 1:
            self.md_bg_color = (0.3,0.4,0.1,1)
        elif self.comp == 0:
            self.md_bg_color = (0.85,0.14,0.31,1)
        else:
            print('ERROR')
        

    def update(self,ddate,ggrade,aattempts,ccomp,ttypes):
        self.date = ddate
        self.grade = ggrade
        self.attempts = aattempts
        self.comp = ccomp
        self.types = ttypes
        if self.types == 'boulder':
            self.img = 'Images/rock.png'
        if self.types == 'route':
            self.img = 'Images/snowed-mountains.png'
        self.update_display()
        

        
        
    def menu_callback(self,option):
        
        if self.parent != None:
            gsystem = None
            if self.types == 'boulder':
                with open('settings.json','r+') as s_file:                
                    data = json.load(s_file)
                    gsystem = data['boulder_grading']
            if self.types == 'route':
                with open('settings.json','r+') as s_file:
                    data = json.load(s_file)
                    gsystem = data['route_grading']
            if option == 'edit':
                editentry = MDApp.get_running_app().root.get_screen('EditEntry')
                editentry.edit = True
                editentry.caller = self
                editentry.fill()
                MDApp.get_running_app().root.current = 'EditEntry'
            elif option == 'delete':
                bldr_data = sqlite3.connect("boulder_data.db")
                cur = bldr_data.cursor()
                cur.execute('DELETE FROM %s WHERE id=%s' % (gsystem,self.idnum))
                bldr_data.commit()
                cur.close()
                bldr_data.close()

                MDApp.get_running_app().update_grade(self.types)
                MDApp.get_running_app().update_timeline_table(self.date,self.types)
                self.parent.remove_widget(self)
            else:
                print('something went wrong')
            self.ddmenu.dismiss()
            
        

    def show_dropdown_menu(self,widget):
        self.ddmenu = MDDropdownMenu(caller=widget,items=self.menu,width_mult=2)
        self.ddmenu.open()
        
        
'''class gradebutton(Widget):
    def __init__(self,radius=None,**kwargs):
        super(gradebutton,self).__init__(**kwargs)
        self.radius = radius
        self.size = (self.radius,self.radius)
        with self.canvas:
            Color(0.3,0.6,0.5,1)
            self.circ = Ellipse(size=(self.radius,self.radius),angle_start=0,angle_end=360)
            self.bind(pos=self.update_circ)

    def update_circ(self,*args):
        self.circ.pos = self.pos
        self.size = self.circ.size
        
            

    def test_callback(self,inst):
        print(inst)'''
            
            
            
            

sm = ScreenManager()
#sm.add_widget(MainMenuScreen(name='Main Menu'))
#sm.add_widget(EntryScreen(name='Entry'))
#sm.add_widget(EntryScreen(name='EditEntry'))
#sm.add_widget(SettingsScreen(name='Settings'))
#sm.add_widget(GradingScreen(name='Grading'))
#sm.add_widget(ProgressScreen(name='Progress'))



class BoulderBuddyApp(MDApp):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.vgrades = self.create_grades_list('USA')
        self.fontgrades = self.create_grades_list('FONT')
        self.dangrades = self.create_grades_list('DAN')
        self.yds = self.create_grades_list('YDS')
        self.fr = self.create_grades_list('FR')
        self.aus = self.create_grades_list('AUS')

        self.b_max_idnum = 0
        self.r_max_idnum = 0

        self.create_datatables()
        self.root = Builder.load_file('boulder_entry.kv')
        self.set_grade_carousel()
        self.update_grade('boulder')
        self.set_grade_display()
        self.setup_entries()
        self.root.get_screen('Entry').setup_grade_buttons()
        #self.root.get_screen('EditEntry').setup_grade_buttons()
        

        self.bgraph,self.rgraph = self.create_graphs()


        if self.bgraph:
            container = self.root.get_screen('Progress').ids.graph_container
            container.bind(minimum_size=container.setter('size'))
            container.add_widget(self.bgraph)
        else:
            self.set_NED_label()

        
    
        

        




    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Red"
        
        return self.root

    '''def setup_grade_buttons(self):
        bsystem = self.root.get_screen('Settings').boulder_setting
        rsystem = self.root.get_screen('Settings').route_setting
        current_system = self.root.get_screen('Entry').types
        entry_container = self.root.get_screen('Entry').gradecontainer
        edit_container = self.root.get_screen('EditEntry')
        grade_list = None
        if current_system == 'boulder':
            grade_list = self.create_grades_list(bsystem.upper())
        elif current_system == 'route':
            grade_list = self.create_grades_list(rsystem.upper())
        else:
            print('current_system')
        for i in grade_list:
            new_button = MDFloatingActionButton()
            entry_container.add_widget(new_button)'''
            
            
            
                
        

    def setup_entries(self):
        data_master = []
        bgrade = self.root.get_screen('Settings').boulder_setting
        rgrade = self.root.get_screen('Settings').route_setting
        
        bldr_data = sqlite3.connect("boulder_data.db")
        cur = bldr_data.cursor()
        
        cur.execute('SELECT * FROM %s' % bgrade)
        bdata = cur.fetchall()
        cur.execute('SELECT * FROM %s' % rgrade)
        rdata=cur.fetchall()
        
        cur.close()
        bldr_data.close()

        data_master = bdata + rdata
        data_master.sort(key=lambda dpoint: datetime.strptime(dpoint[1],'%Y-%m-%d'))
        data_master.reverse()
        
        container = self.root.get_screen('Main Menu').ids.entry_container
        if len(container.children) != 0:
            container.clear_widgets()
        
        for i in data_master:
            iidnum = i[0]
            ddate = i[1]
            ggrade = i[2]
            aattempts = i[3]
            ccompleted = i[4]
            types = None
            if i in bdata:
                types='boulder'
                if self.b_max_idnum < iidnum:
                    self.b_max_idnum = iidnum
            else:
                types = 'route'
                if self.r_max_idnum < iidnum:
                    self.r_max_idnum = iidnum
            entry = EntryItem(idnum=iidnum,
                              date=ddate,
                              grade=ggrade,
                              attempts=aattempts,
                              comp = ccompleted,
                              types = types,
                              size=('100dp','100dp'),
                              pos_hint={'center_x':0.5,'center_y':0.5},
                              size_hint_y=None)
            container.add_widget(entry)

    
        
        

        
        

    def toolbar_callbacks(self,widget):
        if widget == 'entries':
            self.update_screen()
            self.root.current = 'Main Menu'
        elif widget == 'progress':
            self.update_screen()
            self.root.current = 'Progress'
        elif widget == 'compare':
            print('compare')
        elif widget == 'settings':
            self.update_screen()
            self.root.current = 'Settings'
        elif widget == 'new entry':
            self.update_screen()
            self.current_date()
            self.root.get_screen('Entry').ids.bstate.state = 'down'
            self.root.get_screen('Entry').types = 'boulder'
            self.root.current = 'Entry'
        else:
            settings_button = widget.children[1].children[0].children[0]
            compare_button = widget.children[1].children[0].children[1]
            progress_button = widget.children[1].children[2].children[0]
            entries_button = widget.children[1].children[2].children[1]
            #settings_button.md_bg_color = [0.5,0.8,0.3,1]
            #test_button.md_bg_color = [0.5,0.8,0.3,1]
            
    

    def current_date(self):
        cdate = date.today()
        self.root.get_screen('Entry').ids.date.text = str(cdate)
        
    def set_NED_label(self):
        self.NEDLabel = MDLabel(
                            text='Not Enough Data',
                            halign='center')
        self.NEDLabel.font_size = '18sp'
        self.NEDLabel.font_name = 'SometypeMono'
        #label_container = self.root.get_screen('Progress').ids.graphsystem
        graph_container = self.root.get_screen('Progress').ids.graph_container
        graph_container.add_widget(self.NEDLabel)
    
    def create_graphs(self):
        self.NEDLabel = None
        bgrade_dict = self.make_grade_dict(self.root.get_screen('Settings').boulder_setting.lower())
        rgrade_dict = self.make_grade_dict(self.root.get_screen('Settings').route_setting.lower())
        date_dict = self.root.get_screen('Progress').date_dict
        bgraph = None
        rgraph = None
        

        win_height = dp(600)
        container_pos_hint_y = self.root.get_screen('Progress').ids.graph_container.size_hint[1]
        graph_height = win_height*container_pos_hint_y
        bpoints = self.root.get_screen('Progress').bodata
        if len(bpoints) >= 2:
            bgraph = Plot('bouldering',bpoints,x_tick_names=date_dict,y_tick_names=bgrade_dict,size_hint_y=None,height=graph_height)

        rpoints = self.root.get_screen('Progress').rodata
        if len(rpoints) >= 2:
            rgraph = Plot('routes',rpoints,x_tick_names=date_dict,y_tick_names=rgrade_dict,size_hint_y=None)
            
        return bgraph,rgraph

    def change_state(self):
        progress = self.root.get_screen('Progress')
        bstate = progress.ids.bstate.state
        rstate = progress.ids.rstate.state
        container = progress.ids.graph_container
        label_container = progress.ids.graphsystem
        
        if len(container.children) > 0:
            container.remove_widget(container.children[0])
        else:
            label_container.remove_widget(label_container.children[0])
        
        if rstate == 'down':
            progress.gstate = 'route'

            if self.rgraph:
                container.add_widget(self.rgraph)
            else:
                self.set_NED_label()
        else:
            progress.gstate = 'boulder'

            if self.bgraph:
                container.add_widget(self.bgraph)
            else:
                self.set_NED_label()
        self.set_grade_display()

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

    def create_grades_list(self,system):
        grades = []
        if system == 'USA':
            for i in range(18):
                vgrade = 'V' + str(i)
                dropdown_item = {'viewclass': 'OneLineListItem', 'text':vgrade, 'on_release': lambda x=vgrade:self.grade_callback(x)}
                grades.append(dropdown_item)
                
        elif system == 'FONT':
            fontgrades = ['4','4+','5','5+']
            for i in range(6,9):
                for j in ['a','b','c']:
                    fontgrades.append(str(i)+j)
                    fontgrades.append(str(i)+j+'+')
            fontgrades.append('9a')

            for i in fontgrades:
                dropdown_item = {'viewclass': 'OneLineListItem', 'text':i, 'on_release': lambda x=i:self.grade_callback(x)}
                grades.append(dropdown_item)

        elif system == 'DAN':
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

        elif system == 'YDS':
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

        elif system == 'FR':
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

        elif system == 'AUS':
            ausgrades = []
            for i in range(40):
                ausgrades.append(str(i))

            for i in ausgrades:
                dropdown_item = {'viewclass': 'OneLineListItem', 'text':i, 'on_release': lambda x=i:self.grade_callback(x)}
                grades.append(dropdown_item)
        else:
            print('FUCK SOMETHING IS WRONG OH GOD')
                
        return grades
    
    


    def set_grade_carousel(self):
        bogrades = {'USA':0,'FONT':1,'DAN':2}
        rogrades = {'YDS':0,'FR':1,'AUS':2}
        
        self.root.get_screen('Grading').ids.bocar.index = bogrades[self.root.get_screen('Settings').boulder_setting]
        self.root.get_screen('Grading').ids.rocar.index = rogrades[self.root.get_screen('Settings').route_setting]

    def grade_callback(self,grade):
        current_screen = self.root.current
        self.root.get_screen(current_screen).ids.grade.text = grade
        self.grade_menu.dismiss()

    def type_callback(self,types):
        current_screen = self.root.current
        if self.root.get_screen(current_screen).types != types.lower():
            self.root.get_screen(current_screen).ids.grade.text = ''
            self.root.get_screen(current_screen).types = types.lower()
        self.root.get_screen(current_screen).ids.typechoice.text = types
        self.types_menu.dismiss()


    def set_current_grade_system(self,types):
        settings = self.root.get_screen('Settings')
        if types == 'boulder':
            grade_systems = {'USA':self.vgrades,'FONT':self.fontgrades,'DAN':self.dangrades}
            return grade_systems[settings.boulder_setting]
        if types == 'route':
            grade_systems = {'YDS':self.yds,'FR':self.fr,'AUS':self.aus}
            return grade_systems[settings.route_setting]

    def open_types_menu(self):
        boulder = {'viewclass': 'OneLineListItem', 'text': 'Boulder', 'on_release': lambda x='Boulder':self.type_callback(x)}
        route = {'viewclass': 'OneLineListItem', 'text': 'Route', 'on_release': lambda x='Route':self.type_callback(x)}
        type_list = [boulder,route]
        current_screen= self.root.current
        self.types_menu = MDDropdownMenu(caller=self.root.get_screen(current_screen).ids.typechoice, items = type_list, width_mult = 2)
        self.types_menu.open()
        
        
    
    def open_grade_menu(self):
        current_screen = self.root.current
        current_grade_system = self.set_current_grade_system(self.root.get_screen('Entry').types)
        if current_grade_system:
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

    def input_fake_data(self,date,grade,attempts,completed,types):
        idnum = None
        datatable = None
        if types == 'boulder':
            datatable = self.root.get_screen('Settings').boulder_setting.lower()
            self.b_max_idnum += 1
            idnum = self.b_max_idnum
        if types == 'route':
            datatable = self.root.get_screen('Settings').route_setting.lower()
            self.r_max_idnum += 1
            idnum = self.r_max_idnum

        
        bldr_data = sqlite3.connect("boulder_data.db")
        cur = bldr_data.cursor()

        cur.execute('''CREATE TABLE IF NOT EXISTS %s
                    (id INT, date TEXT, grade TEXT, attempts INT, completed INT)''' % datatable)
        bldr_data.commit()
            
        cur.execute('''INSERT INTO %s (id, date, grade, attempts,completed) VALUES (?,?,?,?,?)''' % datatable,(idnum,date,grade,attempts,completed))
        bldr_data.commit()

        self.add_entry(idnum,date,grade,attempts,completed,types)          

        cur.close()
        bldr_data.close()

        timezone = self.root.get_screen('Settings').timezone
        timeline_grade = self.MLE(datatable,timezone,self.date_to_utc(date))[1]
        self.update_MLE(date,timeline_grade,types)
        self.update_timeline_table(date,types)
        self.update_graph_grade()
        entry_screen.clear_display()
        self.root.current = 'Main Menu'
        
        

    def input_data(self,entry_screen):
        date,grade,attempts,completed,types = entry_screen.get_data()
        idnum = None
        datatable = None
        if entry_screen.types == 'boulder':
            datatable = self.root.get_screen('Settings').boulder_setting.lower()
            self.b_max_idnum += 1
            idnum = self.b_max_idnum
        if entry_screen.types == 'route':
            datatable = self.root.get_screen('Settings').route_setting.lower()
            self.r_max_idnum += 1
            idnum = self.r_max_idnum

        
        bldr_data = sqlite3.connect("boulder_data.db")
        cur = bldr_data.cursor()

        if entry_screen.edit == False:
            cur.execute('''CREATE TABLE IF NOT EXISTS %s
                        (id INT, date TEXT, grade TEXT, attempts INT, completed INT)''' % datatable)
            bldr_data.commit()
            
            cur.execute('''INSERT INTO %s (id, date, grade, attempts,completed) VALUES (?,?,?,?,?)''' % datatable,(idnum,date,grade,attempts,completed))
            bldr_data.commit()

            self.add_entry(idnum,date,grade,attempts,completed,types)

        else:
            entry = entry_screen.caller
            idnum = entry.idnum
            cur.execute('''UPDATE %s SET date = ?, grade = ?, attempts = ?, completed = ? WHERE id = ?''' % datatable,(date,grade,attempts,completed,idnum))
            bldr_data.commit()
            entry.update(date,grade,attempts,completed,types)
            

        cur.close()
        bldr_data.close()

        timezone = self.root.get_screen('Settings').timezone
        timeline_grade = self.MLE(datatable,timezone,self.date_to_utc(date))[1]
        self.update_MLE(date,timeline_grade,types)
        self.update_timeline_table(date,types)
        self.update_graph_grade()
        entry_screen.clear_display()
        self.root.current = 'Main Menu'

    def add_entry(self,idnum,date,grade,attempts,completed,types):
        types = types.lower()
        container = self.root.get_screen('Main Menu').ids.entry_container
        new_entry= EntryItem(idnum=idnum,
                             date=date,
                              grade=grade,
                              attempts=attempts,
                              comp = completed,
                              types=types,
                              size=('100dp','100dp'),
                              pos_hint={'center_x':0.5,'center_y':0.5},
                              size_hint_y=None)
        
        true_index = 0
        date_list = []
        for i in container.children:
            date_list.append(datetime.strptime(i.date,'%Y-%m-%d'))
        date_num = datetime.strptime(date,'%Y-%m-%d')
        if len(date_list) == 0:
            pass
        elif date_num < date_list[0]:
            true_index = 0
        elif date_num >= date_list[len(date_list)-1]:
            true_index = len(date_list)
        else:
            for i in date_list:
                if i > date_num:
                    break
                true_index += 1
        
        
        container.add_widget(new_entry,index=true_index)

        
        

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

        data.reverse()
        
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

    def update_graph_grade(self):
        settings_screen = self.root.get_screen('Settings')
        progress_screen = self.root.get_screen('Progress')

        bsystem = settings_screen.boulder_setting
        rsystem = settings_screen.route_setting
        
        bgrade_dict = self.make_grade_dict(bsystem)
        rgrade_dict = self.make_grade_dict(rsystem)
        date_dict = progress_screen.date_dict

        progress_screen.bsystem,progress_screen.rsystem = progress_screen.get_grade_settings()
        progress_screen.bodata,progress_screen.rodata = progress_screen.get_timeline_data()

        container = progress_screen.ids.graph_container
        label_container = progress_screen.ids.graphsystem
        bpoints = progress_screen.bodata

        if len(container.children) > 0:
            old_plot = container.children[0]
            container.remove_widget(old_plot)
        else:
            old_NED_label = label_container.children[0]
            label_container.remove_widget(old_NED_label)
        

        self.bgraph,self.rgraph = self.create_graphs()
        if self.bgraph:
            container.bind(minimum_size=container.setter('size'))
            container.add_widget(self.bgraph)
        else:
            self.set_NED_label()

    def SetGradeSettings(self):
        boulder_grade = self.root.get_screen('Grading').ids.bocar.current_slide.children[1].text
        route_grade = self.root.get_screen('Grading').ids.rocar.current_slide.children[1].text
        timezone = self.root.get_screen('Settings').timezone
        current_boulder_slope,current_boulder_grade = self.MLE(boulder_grade.lower(),timezone)
        current_route_slope,current_route_grade = self.MLE(route_grade.lower(),timezone)

        settings_screen = self.root.get_screen('Settings')
        settings_screen.boulder_setting = boulder_grade
        settings_screen.route_setting = route_grade
        settings_screen.current_boulder_grade = current_boulder_grade
        settings_screen.current_boulder_slope = current_boulder_slope
        settings_screen.current_route_grade = current_route_grade
        settings_screen.current_route_slope = current_route_slope

        settings_screen.update_settings_file()
        

        self.update_graph_grade()
        self.update_grade(self.root.get_screen('Progress').gstate)
        self.set_grade_display()
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
        np.seterr(divide='ignore')
        m,c = np.exp(log_par)
        logL = np.sum(np.log(self.psend(m,c,send_data))) + np.sum(np.log(self.pnosend(m,c,nosend_data)))
        np.seterr(divide='warn')
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
        grade_dict = self.make_grade_dict(system)
        swapped_dict = {value: key for key, value in grade_dict.items()}
        return swapped_dict[grade]
        
    #calculated score is the number not just V0 V1
    def number_to_grade(self,number,system):
        grade_dict = self.make_grade_dict(system)
        if type(number) is str:
            return 'N/A'
        num = round(number,1)
        if system == 'usa':
            grade = 'V' + str(num)
            return grade
        else:
            #this is temporary
            num = floor(number)
            num_remainder = round(number - num,1)
            grade = str(grade_dict[num]) + ' (' + str(num_remainder) + ')'
            return grade
        
            

    def make_grade_dict(self,system):
        grade_dict = {}
        grades_list = []
        grades_list_raw = self.create_grades_list(system.upper())
        for i in grades_list_raw:
            grades_list.append(i['text'])
        for i in range(len(grades_list)):
            grade = grades_list[i]
            grade_dict[i] = grade

        return grade_dict

    def make_date_dict(self):
        pass

    def gsystem_to_types(self,gsystem):
        boulder = ['usa','font','dan']
        route = ['yds','fr','aus']
        if gsystem in boulder:
            return 'boulder'
        if gsystem in route:
            return 'route'
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
        start_m = 1
        start_c = 1
        settings_screen = self.root.get_screen('Settings')
        types = self.gsystem_to_types(gsystem)
        if types == 'boulder' and settings_screen.current_boulder_grade != 'N/A':
            start_m = np.log(float(settings_screen.current_boulder_slope))
            start_c = np.log(float(settings_screen.current_boulder_grade))
        if types == 'route' and settings_screen.current_route_grade != 'N/A':
            start_m = np.log(float(settings_screen.current_route_slope))
            start_c = np.log(float(settings_screen.current_route_grade))
        res = opt.minimize(
            fun = lambda log_params,send_data,nosend_data: -self.logL(log_params,send_data,nosend_data),
            x0 = np.array([start_m,start_c]), args = (send_data,nosend_data), method = 'BFGS')
        m,c = np.exp(res.x)
        return m,c

    def set_grade_display(self):
        progress = self.root.get_screen('Progress')
        gsystem = None
        if progress.gstate == 'boulder':
            gsystem = self.root.get_screen('Settings').boulder_setting.lower()
            progress.ids.currentgrade.text = self.number_to_grade(self.root.get_screen('Settings').current_boulder_grade,gsystem)
        else:
            gsystem = self.root.get_screen('Settings').route_setting.lower()
            progress.ids.currentgrade.text = self.number_to_grade(self.root.get_screen('Settings').current_route_grade,gsystem)
        
        

    def update_grade(self,types):
        settings_screen = self.root.get_screen('Settings')
        timezone = settings_screen.timezone
        gsystem = None
        if types == 'boulder':
            gsystem = settings_screen.boulder_setting.lower()
            m,c=self.MLE(gsystem,timezone)
            settings_screen.current_boulder_slope = m
            settings_screen.current_boulder_grade = c
            self.root.get_screen('Progress').ids.currentgrade.text = self.number_to_grade(settings_screen.current_boulder_grade,gsystem)
        else:
            gsystem = settings_screen.route_setting.lower()
            m,c=self.MLE(gsystem,timezone)
            settings_screen.current_route_slope = m
            settings_screen.current_route_grade = c
            self.root.get_screen('Progress').ids.currentgrade.text = self.number_to_grade(settings_screen.current_route_grade,gsystem)
        settings_screen.update_settings_file()
        
        
            

    def update_MLE(self,date,grade,types):
            settings_screen = self.root.get_screen('Settings')
            gsystem = None
            if types == 'boulder':
                gsystem = settings_screen.boulder_setting.lower()
            else:
                gsystem = settings_screen.route_setting.lower()
            
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
            self.update_grade(types)
            

            

        


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

    def update_timeline_table(self,date,types):
        settings_screen = self.root.get_screen('Settings')
        gsystem = None
        if types == 'boulder':
            gsystem = settings_screen.boulder_setting.lower()
        else:
            gsystem = settings_screen.route_setting.lower()
        datatable = gsystem + '_timeline'
        
        timezone = settings_screen.timezone
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
        if self.bgraph:
            self.bgraph.plot.points = prog_screen.bodata
        if self.rgraph:
            self.rgraph.plot.points = prog_screen.rodata



        
        
        
        


        


        
            
            
        
        #filter data for last 30 days(thats the climbing period)
        #create a list of negative log(psends) with the r variable filled in
        #create use scipy minimize to find the parameters needed for minimization

        #later this model will be updated to include a time dependent version
        #also possibly model learning rate/learning bonus effect but thats waaay down the line

        



    


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
