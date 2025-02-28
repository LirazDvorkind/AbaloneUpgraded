import Abalone
import os
import random
import sys
import variables

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button, ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, RiseInTransition

path = os.path.dirname(sys.argv[0])

Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '800')
Config.set('input', 'mouse', 'mouse, multitouch_on_demand')

chosen_cells = [False] * 61
total_cell_counter = 0
chosen_indices = []
game_state = 1
initialize_flag = False
containers = [[], []]
MOVES = 0
disable_ai = 1
allow_choosing_white = disable_ai
allow_choosing_black = True
difficulty = 1


class SideCell(ButtonBehavior, Image):
    def __init__(self, **kwargs):
        global total_cell_counter

        super(SideCell, self).__init__(**kwargs)
        self.source = os.path.join(path, 'images', 'bl.png')


class Cell(ButtonBehavior, Image):
    def __init__(self, **kwargs):
        global total_cell_counter

        super(Cell, self).__init__(**kwargs)
        self.source = os.path.join(path, 'images', 'bl.png')
        self.index = total_cell_counter
        total_cell_counter += 1

    def behave(self, touch):
        if self.source == os.path.join(path, 'images', 'w.png') and allow_choosing_white:
            self.source = os.path.join(path, 'images', 'wm.png')
        elif self.source == os.path.join(path, 'images', 'b.png') and allow_choosing_black:
            self.source = os.path.join(path, 'images', 'bm.png')
        elif self.source == os.path.join(path, 'images', 'bm.png'):
            self.source = os.path.join(path, 'images', 'b.png')
        elif self.source == os.path.join(path, 'images', 'wm.png'):
            self.source = os.path.join(path, 'images', 'w.png')
        else:
            return
        chosen_cells[touch.index] = not chosen_cells[touch.index]


class Background(FloatLayout):
    def __init__(self, **kwargs):
        super(Background, self).__init__(**kwargs)
        background_texture = Button(background_color=(1, 2, 200, 1))
        self.add_widget(background_texture)
        b = SpecialButton(disabled=False)
        b.source = os.path.join(path, 'images', 'board.png')
        b.allow_stretch = 1
        b.bind(on_press=self.behave)
        self.add_widget(b)

    def behave(self, touch, *args):
        """Handles user input through button press or code calls, runs the game and updates the board accordingly"""
        computer_play = Clock.create_trigger(self.behave)
        global chosen_indices, game_state, initialize_flag, MOVES, containers, allow_choosing_white, allow_choosing_black
        if not initialize_flag:
            for i in range(6):
                self.children[0].buttons[i].bind(on_release=self.selection)

        if game_state == 4:
            self.parent.parent.current = 'End Screen'  # i.e. manager.current = 'End Screen'
            end_msg()  # To be triggered as it shows

        if game_state == 1:  # ask to select the cells
            self.update_board()
            self.children[1].header.text = 'Choose Balls ' + ('(White)' if MOVES % 2 else '(Black)')
            if MOVES % 2 == 1 and not disable_ai:
                move = a.minimax('white', difficulty)
                chosen_indices = move[0]
                where = move[1]
                game_state = 3
            if disable_ai:
                if MOVES % 2:
                    allow_choosing_white = True
                    allow_choosing_black = False
                else:
                    allow_choosing_white = False
                    allow_choosing_black = True

        if game_state == 3:  # handle both inputs and make move
            indices = list(chosen_indices)
            for i in range(len(chosen_cells)):
                chosen_cells[i] = False
            chosen_indices = []
            if not len(indices) == 0:
                self.children[1].header.text = 'Computer Playing' if (
                            not disable_ai and MOVES % 2 == 0) else 'Choose Balls ' + (
                    '(White)' if MOVES % 2 == 0 else '(Black)')
            if isinstance(touch, str):
                where = touch
            self.update_board()

            try:
                pre_move_state = [list(a.board), dict(a.pushed_out)]
                a.move(indices, where)
                self.update_board()
                MOVES += 1
                if disable_ai:
                    temp = allow_choosing_white
                    allow_choosing_white = int(allow_choosing_black)
                    allow_choosing_black = temp
                if a.pushed_out != pre_move_state[1]:
                    variables.boring_moves = 1
                else:
                    variables.boring_moves += 1

            except Abalone.InvalidMove as im:
                print(im.message)
                self.children[1].header.text = im.message
            except IndexError as ie:
                for args in ie.args:
                    print("Exception:", args)
            finally:
                game_state = 1
                if MOVES % 2 and not disable_ai and a.pushed_out['black'] != 6 and a.pushed_out['white'] != 6:
                    computer_play()
                if a.pushed_out['black'] == 6:
                    self.children[1].header.text = 'White Wins! Press here to end the game'
                    game_state = 4
                if a.pushed_out['white'] == 6:
                    self.children[1].header.text = 'Black Wins! Press here to end the game'
                    game_state = 4

    def update_board(self):
        """Update board screen"""
        for i in range(len(a.board)):
            self.children[1].board[i].source = os.path.join(path, 'images', 'w.png') if a.board[i].value == 'white' \
                else os.path.join(path, 'images', 'b.png') if a.board[i].value == 'black' else os.path.join(path,
                                                                                                            'images',
                                                                                                            'bl.png')
        for i in range(6):
            containers[0][i].source = os.path.join(path, 'images',
                                                   'w.png' if a.pushed_out['white'] >= i + 1 else 'bl.png')
            containers[1][i].source = os.path.join(path, 'images',
                                                   'b.png' if a.pushed_out['black'] >= i + 1 else 'bl.png')

    def selection(self, touch):
        """Bounded to each of the selection buttons, handles their presses"""
        global game_state, chosen_indices
        if game_state == 1:
            if disable_ai or MOVES % 2 == 0:
                game_state = 3
                chosen_indices = [i for i in range(len(chosen_cells)) if chosen_cells[i]]
                self.behave(touch.direction)


class Board(BoxLayout):
    ARRANGEMENT = [5, 6, 7, 8, 9, 8, 7, 6, 5]

    def __init__(self, **kwargs):
        """Create the board screen overlay of invisible buttons alignment, cells & container cells"""
        super(Board, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.board = []

        def random_color():
            t = [random.uniform(0, 1) for i in range(3)]
            return tuple(t + [1])

        self.header = Label(color=(255, 255, 255, 1), text='Press to Begin the Game!',
                            font_name=os.path.join(path, 'fonts', 'header_font.otf'), font_size='45sp')
        self.add_widget(self.header)
        for ind, i in enumerate(self.ARRANGEMENT):
            a = BoxLayout(orientation='horizontal')
            self.add_widget(a)
            for j in range(9 - i + 10):
                if ind in [7, 8] and j in range(3, 6):
                    c = SideCell()
                    containers[0].append(c)
                    a.add_widget(c)
                elif ind in [7, 8] and j in range(8, 12):
                    pass
                else:
                    a.add_widget(Button(size_hint=(0.5, 1), background_color=(random_color()), opacity=0))
            for j in range(i):
                c = Cell()
                c.bind(on_press=c.behave)
                a.add_widget(c)
                self.board.append(c)
            for j in range(9 - i + 10):
                if ind in [7, 8] and 18 - i - j in range(3, 6):
                    c = SideCell()
                    containers[1].append(c)
                    a.add_widget(c)
                elif ind in [7, 8] and 18 - i - j in range(8, 12):
                    pass
                else:
                    a.add_widget(Button(size_hint=(0.5, 1), background_color=(random_color()), opacity=0))
        a = BoxLayout(orientation='horizontal')
        self.add_widget(a)


class SelectionButtons(FloatLayout):
    def __init__(self, **kwargs):
        """Position the arrow buttons (that handle user input)"""
        super(SelectionButtons, self).__init__(**kwargs)
        self.buttons = []
        for j in range(3):
            for i in reversed(range(3)):
                if i != 1:
                    b = SelectionButton()
                    b.pos = (185 + 850 - (40 * i), 650 - (60 * j))
                    if j == 1:
                        b.pos = (b.pos[0] + (1 - i) * 40, b.pos[1])
                    b.size_hint_x = 0.07
                    b.size_hint_y = 0.07
                    self.buttons.append(b)
                    b.value = len(self.buttons)
                    b.source = os.path.join(path, 'images', 'arrow_off' + str(b.value) + '.png')
                    b.direction = ['top left', 'top right', 'left', 'right', 'bottom left', 'bottom right'][b.value - 1]
                    self.add_widget(b)


class SpecialButton(ButtonBehavior, Image):
    def __init__(self, **kwargs):
        super(SpecialButton, self).__init__(**kwargs)


class SelectionButton(SpecialButton):
    def __init__(self, **kwargs):
        self.value = 0
        self.direction = ''
        super(SelectionButton, self).__init__(**kwargs)
        self.always_release = True

    def on_press(self):
        self.source = os.path.join(path, 'images', 'arrow_on' + str(self.value) + '.png')

    def on_release(self):
        self.source = os.path.join(path, 'images', 'arrow_off' + str(self.value) + '.png')


class GameScreen(Screen):
    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        global reset_game
        reset_game = Clock.create_trigger(self.reset)
        root = Background()
        root.add_widget(Board())
        root.add_widget(SelectionButtons())
        self.add_widget(root)

    def reset(self, *args):
        global game_state, containers, MOVES, allow_choosing_white, \
            difficulty, chosen_cells, chosen_indices, total_cell_counter
        game_state = 1
        MOVES = 0
        disable_ai = 1
        allow_choosing_white = disable_ai
        difficulty = 1
        variables.boring_moves = 0
        variables.boring_move_cap = 15
        chosen_cells = [False] * 61
        total_cell_counter = 0
        chosen_indices = []
        for i in containers:
            for j in i:
                j.source = os.path.join(path, 'images', 'bl.png')
        a.__init__()
        self.children[0].update_board()  # Background->update_board()
        for i in self.children[0].children[1].board:  # Background->Board->board
            i.source = os.path.join(path, 'images', 'bl.png')
        self.children[0].children[1].header.text = 'Press to Begin the Game!'  # Background->Board->header


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.manager = self.parent
        self.to_be_reset = False  # If single player was chosen, re-add (reset to) the original selection options

        base = FloatLayout()
        background = Image(source=os.path.join(path, 'images', 'background.png'), allow_stretch=True, keep_ratio=False)
        cover = BoxLayout()
        cover.orientation = 'vertical'

        def random_color():
            t = [random.uniform(0, 1) for i in range(3)]
            return tuple(t + [1])

        cover.add_widget(Button(size_hint=(0.5, 1), background_color=(random_color()), opacity=0))
        self.selection = []
        # Add the orientation invisible buttons and selection buttons, along with the title image
        for i in range(4):
            a = BoxLayout(orientation='horizontal')
            cover.add_widget(a)
            for j in range(5):
                if not ((i == 1 and j in [1, 2, 3]) or (i == 2 and j == 2) or (i == 0 and j in [1, 2, 3])):
                    a.add_widget(Button(size_hint=(0.5, 1), background_color=(random_color()), opacity=0))
                else:
                    if i == 1 and j == 1:
                        b = SpecialButton(source=os.path.join(path, 'images', 'single_player.png'),
                                          size_hint=(0.5, 1))  # Add single player button
                        b.bind(on_press=self.single_player)
                        a.add_widget(b)
                        self.selection.append(b)
                    if i == 1 and j == 2:
                        b = SpecialButton(source=os.path.join(path, 'images', '2 players.png'),
                                          size_hint=(0.5, 1))  # Add the 2 players button
                        b.bind(on_press=self.two_players)
                        a.add_widget(b)
                        self.selection.append(b)
                    if i == 1 and j == 3:
                        b = SpecialButton(source=os.path.join(path, 'images', 'rules.png'),
                                          size_hint=(0.5, 1))  # Add the rules button
                        b.bind(on_press=self.rules)
                        a.add_widget(b)
                        self.selection.append(b)
                    if i == 2 and j == 2:
                        b = SpecialButton(source=os.path.join(path, 'images', 'classic layout.png'),
                                          size_hint=(0.5, 1))  # Add the layout button
                        b.layout_type = 'Regular Layout'
                        b.bind(on_press=self.layout)
                        a.add_widget(b)
                    if i == 0 and j == 2:
                        b = Image(source=os.path.join(path, 'images', 'title.png'),
                                  size_hint=(0.5, 1))  # Add the title image
                        a.add_widget(b)
        base.add_widget(background)
        base.add_widget(cover)
        self.add_widget(base)
        global reset_home
        reset_home = Clock.create_trigger(self.reset)

    def reset(self, *args):
        """Reset home screen"""
        if self.to_be_reset:
            for i in range(3):
                self.selection[i].unbind(on_press=self.begin_game)
            self.selection[0].source = os.path.join(path, 'images', 'single_player.png')
            self.selection[0].bind(on_press=self.single_player)
            self.selection[1].source = os.path.join(path, 'images', '2 players.png')
            self.selection[1].bind(on_press=self.two_players)
            self.selection[2].source = os.path.join(path, 'images', 'rules.png')
            self.selection[2].bind(on_press=self.rules)

    def layout(self, touch):
        """Handle layout button"""
        global regular_layout
        if touch.layout_type == 'Daisy Layout':
            touch.layout_type = 'Regular Layout'
            touch.source = os.path.join(path, 'images', 'classic layout.png')
            variables.regular_layout = True
        else:
            touch.layout_type = 'Daisy Layout'
            touch.source = os.path.join(path, 'images', 'daisy layout.png')
            variables.regular_layout = False
        global a
        a = Abalone.Abalone()

    def single_player(self, touch):
        """Handle single player button - choose a difficulty and start a game against the AI"""
        self.to_be_reset = True
        global disable_ai, allow_choosing_white
        disable_ai = False
        allow_choosing_white = disable_ai
        self.selection[0].unbind(on_press=self.single_player)
        self.selection[1].unbind(on_press=self.two_players)
        self.selection[2].unbind(on_press=self.rules)
        for i in range(len(self.selection)):
            self.selection[i].source = os.path.join(path, 'images', ['Easy', 'Medium', 'Hard'][i] + '.png')
            self.selection[i].difficulty_level = str(int(i + 1))
            self.selection[i].bind(on_press=self.begin_game)

    def two_players(self, touch):
        """Handle 2 players button - start a new game, white vs black, both played by the user(s)"""
        global disable_ai, allow_choosing_white
        disable_ai = True
        allow_choosing_white = disable_ai
        self.manager.current = 'Game Screen'

    def rules(self, touch):
        """Go to the rules screen"""
        self.manager.current = 'Rules Screen'

    def begin_game(self, touch):
        """Used to begin the game after a difficulty has been chosen (bounded to the difficulty buttons)"""
        global difficulty
        difficulty = int(touch.difficulty_level)
        self.manager.current = 'Game Screen'


class RulesScreen(Screen):
    def __init__(self, **kwargs):
        """Creates rules screen: 4 images of the rules"""
        super(RulesScreen, self).__init__(**kwargs)
        base = BoxLayout()
        b = SpecialButton(source=os.path.join(path, 'images', 'rules1.png'), allow_stretch=True, keep_ratio=False)
        b.rule_page = '1'
        b.bind(on_press=self.continue_rules)
        base.add_widget(b)
        self.add_widget(base)

    def continue_rules(self, touch):
        """Change to the next image or return to home screen"""
        if touch.rule_page == '4':
            self.parent.current = 'Home Screen'
            touch.rule_page = '1'
        else:
            touch.rule_page = str(int(touch.rule_page) + 1)
        touch.source = os.path.join(path, 'images', 'rules' + touch.rule_page + '.png')


class EndScreen(Screen):
    def __init__(self, **kwargs):
        super(EndScreen, self).__init__(**kwargs)
        global end_msg
        end_msg = Clock.create_trigger(self.run)

    def run(self, *args):
        """Set up and activate the thanks for playing animation"""
        background_image = Image(source=os.path.join(path, 'images', 'end_screen_image.png'), allow_stretch=1,
                                 keep_ratio=0)
        self.add_widget(background_image)
        b = Label(text='Thanks for playing!', font_name=os.path.join(path, 'fonts', 'font.ttf'), font_size='140sp',
                  color=(205 / 255, 87 / 255, 9 / 255, 1))
        b.pos_hint = {'x': 0, 'y': -0.8}
        self.add_widget(b)
        animation = Animation(pos_hint={'x': 0, 'y': 0.8}, d=2.5)
        animation.bind(on_complete=self.end_screen_popup)
        animation.start(b)

    def end_screen_popup(self, *args):
        """Creates the end screen popup when the animation finishes"""
        self.popup = Popup(content=BoxLayout(orientation='vertical'), size_hint=(0.4, 0.6), auto_dismiss=False)
        self.popup.children[0].clear_widgets()
        self.popup.children[0].add_widget(Button(disabled=True, background_color=(0, 0, 0, 0)))
        self.popup.children[0].add_widget(
            SpecialButton(source=os.path.join(path, 'images', 'new game.png'), on_press=self.restart))
        self.popup.children[0].add_widget(
            SpecialButton(source=os.path.join(path, 'images', 'quit game.png'), on_press=self.quit))
        cookie_button = Button(text='No, I\'d prefer to play cookie clicker instead',
                               color=(0, 0, 0, 1), background_color=(255, 255, 255, 0),
                               on_press=self.cookie_clicker)
        cookie_button.cookie_count = '0'
        self.popup.children[0].add_widget(cookie_button)
        self.popup.background = os.path.join(path, 'images', 'popup.png')
        self.popup.open()

    def restart(self, touch):
        """Calls the reset functions to restart the game"""
        self.popup.dismiss()
        self.parent.current = 'Home Screen'
        reset_game()
        reset_home()

    def quit(self, touch):
        """Exit the game"""
        self.popup.dismiss()
        App.get_running_app().stop()

    def cookie_clicker(self, touch):
        if touch.cookie_count != '1000':
            touch.cookie_count = str(int(touch.cookie_count) + 1)
            touch.text = touch.cookie_count + ' cookies'
            if touch.cookie_count == '1':
                touch.text = '1 cookie'
        else:
            touch.text = 'Okay that\'s enough.\nGo play some Abalone while you\'re at it.'


class AbaloneApp(App):
    def build(self):
        """Set up the screen manager"""
        self.title = 'Abalone'
        root = ScreenManager(transition=RiseInTransition())
        root.add_widget(HomeScreen(name='Home Screen'))
        root.add_widget(RulesScreen(name='Rules Screen'))
        root.add_widget(GameScreen(name='Game Screen'))
        root.add_widget(EndScreen(name='End Screen'))
        return root


if __name__ == '__main__':
    a = Abalone.Abalone()
    AbaloneApp().run()
