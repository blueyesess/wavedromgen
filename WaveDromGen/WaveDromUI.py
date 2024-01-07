# coding=utf-8

import os
import tkinter as tk
from builtins import print
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from tkinter.messagebox import showinfo, showwarning

from PIL import ImageTk, Image

import WaveDromGen.language as language_dict
from WaveDromGen.WaveDromCtrl import WaveDromCtrl
from WaveDromGen.WaveImageDB import WaveImageDB
from WaveDromGen.WaveNote import WaveNote


class WaveDromUI:
    def __init__(self):
        title = 'WaveDromGen'  # Titre de la fenêtre
        width, height = 1080, 720  # Taille de la fenêtre
        self.version = 'V1.3.0'  # Numéro version
        self.versionModified = 'V1.2.0'  # Numéro version modifiée

        self.inity = 30  # Initialisation stepy
        self.initx = 40  # Initialisation stepx

        self.stepy = 30  # Réel stepy
        self.stepx = 40  # Réel stepx

        self.scale_ratio = 1  # Valeur de la mise à l'échelle (nombre entier)

        # Création du dossier temporaire
        self.tmp_dir = 'tmp/'  # Dossiers temporaires
        if not os.path.isdir(self.tmp_dir):
            os.mkdir(self.tmp_dir)

        # Création de fichiers image
        self.asset_dir = 'tmp/asset/'
        if not os.path.isdir(self.asset_dir):
            os.mkdir(self.asset_dir)
        WaveImageDB(self.asset_dir)

        # Création de la fenêtre GUI
        root = Tk()
        root.title(title)
        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        align_str = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        root.geometry(align_str)
        root.minsize(720, 480)
        root.resizable(width=False, height=False)
        self.isResized = False
        # Icônes
        image = Image.open(self.asset_dir + 'app.ico')
        photo = ImageTk.PhotoImage(image)
        root.iconphoto(True, photo)

        # UI Variables globales
        self.root = root  # Fenêtre principale
        self.img_view = None  # Zone de dessin canvas
        self.skin = None  # Apparence
        self.scale = None  # Échelle
        self.editmenu = None  # Menu Edition (pour changer dynamiquement le paramètre de l'état d'annulation/rétablissement en global)
        self.x_line = None  # Pointeur horizontale
        self.y_line = None  # Pointeur vertical
        self.mini_img = None  # Animation des vignettes lors du déplacement des rangées
        self.ctrl_press = IntVar()  # Détection si la touche ctrl est enfoncée pour permettre de maintenir la touche ctrl enfoncée pour terminer la copie

        # Cache des icônes de couleur
        self.red = None
        self.green = None
        self.light = None
        self.blue = None
        self.orange = None
        self.yellow = None
        self.white = None

        self.icon_pool = []  # Mise en commun des images, en définissant les icônes utilisées comme des variables globales pour empêcher la libération des ressources en icônes
        self.ctrl = WaveDromCtrl()  # Initialisation du contrôleur
        self.ascii_note = None  # Objets de l'éditeur de texte
        self.img = {}  # Dictionnaire d'images, qui contient un cache d'images sans ligne
        self.cursor = IntVar()  # Active le curseur
        self.cursor.set(1)  # Activation par défaut du curseur
        self.mode = StringVar()  # Mode de travail
        self.mode.set('sig')  # Mode de signal par défaut
        self.position = StringVar()  # Position du pointeur
        self.busColor = StringVar()  # Couleur du bus
        self.busColor.set('=')  # Par défaut '=' donc couleur blanche
        self.x_name_offset = 1  # Lorsque le nom du signal devient plus long, la forme d'onde s'étend vers la droite. Cette variable varie en fonction de la longueur du nom du signal.
        self.lenRow = IntVar()  # Nombre de lignes dans la zone de dessin
        self.lenCol = IntVar()  # Nombre de colonnes dans la zone de dessin

        # Enregistrement du type de fichier
        self.filetype = [
            ('Json Files', '*.json'),
            ('PNG Files', '*.png'),
            ('SVG Files', '*.svg'),
        ]
        self.lastPos = (0, 0)  # Dernière position
        self.savefile = None  # Enregistrement du nom du fichier, si aucun, ouverture du dossier et sélection
        self.language = StringVar()  # Langage UI

        # Définition de la langue en produisant le fichier en/cn/fr sous tmp et en supprimant les autres fichiers de langue lors du changement de langue
        if os.path.isfile(self.tmp_dir + 'en'):
            self.language.set('en')
        elif os.path.isfile(self.tmp_dir + 'cn'):
            self.language.set('cn')
        elif os.path.isfile(self.tmp_dir + 'fr'):
            self.language.set('fr')
        else:
            self.language.set('en')

        # Barre de menu
        self.menubar_view(root)

        # Vue des options
        sheet = ttk.Notebook(root)
        wave_frame = Frame()
        note_frame = Frame()
        ascii_frame = Frame()
        sheet.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # Créer une feuille
        sheet.add(wave_frame, text=self.lang('waveview'))
        sheet.add(note_frame, text=self.lang('editorview'))
        sheet.add(ascii_frame, text=self.lang('asciiview'))

        self.sheet = sheet
        self.wave_frame = wave_frame

        self.statusbar_view(wave_frame)  # Barre d'état
        self.buttonbar_view(wave_frame)  # Barre de boutons
        self.wave_view(wave_frame)  # Zone de dessin
        self.note = WaveNote(frame=note_frame, asset_dir=self.asset_dir, update_wave=self.restore_json,
                             language=self.language.get())  # Zone éditable
        self.ascii_view(ascii_frame)  # Zone ascii

        # Lier les raccourcis aux évenements
        root.bind("<Control-o>", lambda x: self.load())
        root.bind("<Control-s>", lambda x: self.saveas(self.savefile))
        root.bind("<Control-S>", lambda x: self.saveas())
        root.bind("<Control-n>", lambda x: self.new())
        root.bind("<Control-z>", lambda x: self.operate('undo'))
        root.bind("<Control-Z>", lambda x: self.operate('redo'))
        root.bind("<Alt-l>", lambda x: self.operate('addRow'))
        root.bind("<Alt-c>", lambda x: self.operate('addCol'))
        root.bind("<Alt-L>", lambda x: self.mode.set('delRow'))
        root.bind("<Alt-C>", lambda x: self.mode.set('delCol'))
        root.bind("<Control-w>", lambda x: self.operate('SWAP'))
        root.bind("<Control-t>", lambda x: self.period_view(root))
        root.bind("<Control-e>", lambda x: self.mode.set('Node'))
        root.bind("<Control-r>", lambda x: self.relation_view(root))
        root.bind('<KeyPress-Control_L>', lambda x: self.ctrl_press.set(1))
        root.bind('<KeyRelease-Control_L>', lambda x: self.ctrl_press.set(0))

        # Générer un cache d'icônes global (oui/non, principalement utilisé)
        icon_y = Image.open(self.asset_dir + "y.gif")
        icon_y = icon_y.resize((20, 20), Image.ANTIALIAS)
        self.icon_y = ImageTk.PhotoImage(icon_y)

        icon_n = Image.open(self.asset_dir + "n.gif")
        icon_n = icon_n.resize((20, 20), Image.ANTIALIAS)
        self.icon_n = ImageTk.PhotoImage(icon_n)

        self.update()  # Actualisation
        root.mainloop()  # Démarrage de la fenêtre principale (root)

    def ascii_view(self, root):
        """
        Créer ascii view
        :param root: frame supérieur
        :return: None
        """

        def copy_ascii():
            """
            Copier le contenu d'une note ascii dans le presse-papiers
            :return: None
            """
            txt = ascii_note.get('1.0', tk.END)
            root.clipboard_clear()
            root.clipboard_append(txt)

        btn = Button(root, text=self.lang('copy'), relief=tk.GROOVE, bg='white', command=copy_ascii)
        x_scroll = tk.Scrollbar(root, orient=tk.HORIZONTAL)
        y_scroll = tk.Scrollbar(root)

        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        btn.pack(side=BOTTOM, fill=tk.X)  # L'ordre de mise en page affecte l'effet de l'interface
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        ascii_note = Text(root, wrap='none', font=("Courier", 10, tk.font.ROMAN))
        self.ascii_note = ascii_note

        ascii_note.pack(side=TOP, fill=tk.BOTH, expand=True)

        x_scroll.config(command=self.ascii_note.xview)
        y_scroll.config(command=self.ascii_note.yview)

        ascii_note.config(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

    def menubar_view(self, root):
        """
        Créer la barre de menu
        :param root: frame supérieur
        :return: None
        """
        # Création de la barre de Menu
        menubar = Menu(root)
        # Définition du langage
        lang = self.lang

        #  Création du menu Fichier
        filemenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=lang('file'), menu=filemenu)
        filemenu.add_command(label=lang('new'), accelerator='Ctrl+N', command=self.new)
        filemenu.add_command(label=lang('open'), accelerator='Ctrl+O', command=self.load)
        filemenu.add_command(label=lang('save'), accelerator='Ctrl+S', command=lambda: self.saveas(self.savefile))
        filemenu.add_command(label=lang('save_as'), accelerator='Ctrl+Shift+S', command=self.saveas)
        filemenu.add_separator()  # Séparateur menu
        filemenu.add_command(label=lang('exit'), accelerator='Alt+F4', command=root.quit)

        # Création du menu Éditer
        editmenu = Menu(menubar, tearoff=0)
        self.editmenu = editmenu
        menubar.add_cascade(label=lang('edit'), menu=editmenu)
        editmenu.add_command(label=lang('undo'), accelerator='Ctrl+Z', command=lambda: self.operate('undo'),
                             state=tk.DISABLED)
        editmenu.add_command(label=lang('redo'), accelerator='Ctrl+Shift+Z', command=lambda: self.operate('redo'),
                             state=tk.DISABLED)
        editmenu.add_separator()  # Séparateur menu
        editmenu.add_command(label=lang('add_row'), accelerator='Alt+L', command=lambda: self.operate('addRow'))
        editmenu.add_command(label=lang('add_col'), accelerator='Alt+C', command=lambda: self.operate('addCol'))
        editmenu.add_separator()  # Séparateur menu
        editmenu.add_command(label=lang('del_row'), accelerator='Alt+Shift+L', command=lambda: self.mode.set('delRow'))
        editmenu.add_command(label=lang('del_col'), accelerator='Alt+Shift+C', command=lambda: self.mode.set('delCol'))
        editmenu.add_separator()  # Séparateur menu
        editmenu.add_command(label=lang('copy_row'), command=lambda: self.mode.set('COPY'))
        editmenu.add_command(label=lang("swap_row"), accelerator='Ctrl+W', command=lambda: self.operate('SWAP'))
        editmenu.add_separator()  # Séparateur menu
        editmenu.add_command(label=lang('sig_early'), command=lambda: self.mode.set('earlyWave'))
        editmenu.add_command(label=lang('sig_delay'), command=lambda: self.mode.set('delayWave'))

        # Création du menu Afficher
        display_menu = Menu(menubar, tearoff=0)

        def set_color(x):
            """
            Définir la couleur du bus
            :param x: Options : '=', '3', '4', '5', '6', '7', '8', '9', correspondant à la syntaxe wavedrom
            :return: None
            """
            [st.set(0) for st in color_status]  # Réinitialisation
            color_status[color_tag.index(x)].set(1)  # Mise à jour de la valeur sélectionnée
            self.busColor.set(x)
            self.mode.set('bus')

        # Sélection de la couleur du bus
        color_tag = ['=', '3', '4', '5', '6', '7', '8', '9']
        color_status = [IntVar() for i in range(len(color_tag))]
        color_status[0].set(1)  # Valeur par défaut blanc (=)

        # Création du menu déroulant Couleur Bus
        bus_color_menu = Menu(display_menu, tearoff=0)
        display_menu.add_cascade(label=lang('bus_color'), menu=bus_color_menu)
        self.white = ImageTk.PhotoImage(Image.open(self.asset_dir + "white.gif"))
        self.yellow = ImageTk.PhotoImage(Image.open(self.asset_dir + "yellow.gif"))
        self.orange = ImageTk.PhotoImage(Image.open(self.asset_dir + "orange.gif"))
        self.blue = ImageTk.PhotoImage(Image.open(self.asset_dir + "blue.gif"))
        self.light = ImageTk.PhotoImage(Image.open(self.asset_dir + "light.gif"))
        self.green = ImageTk.PhotoImage(Image.open(self.asset_dir + "green.gif"))
        self.red = ImageTk.PhotoImage(Image.open(self.asset_dir + "red.gif"))
        bus_color_menu.add_checkbutton(image=self.white, variable=color_status[0], command=lambda: set_color('='))
        bus_color_menu.add_checkbutton(image=self.yellow, variable=color_status[1], command=lambda: set_color('3'))
        bus_color_menu.add_checkbutton(image=self.orange, variable=color_status[2], command=lambda: set_color('4'))
        bus_color_menu.add_checkbutton(image=self.blue, variable=color_status[3], command=lambda: set_color('5'))
        bus_color_menu.add_checkbutton(image=self.light, variable=color_status[4], command=lambda: set_color('6'))
        bus_color_menu.add_checkbutton(image=self.green, variable=color_status[5], command=lambda: set_color('7'))
        bus_color_menu.add_checkbutton(image=self.red, variable=color_status[6], command=lambda: set_color('9'))

        def set_skin(x):
            """
            Définir l'apparence
            :param x: 'default', 'lowkey', 'narrow'
            :return: None
            """
            [st.set(0) for st in skin_status]  # Réinitialisation
            skin_status[skin_tag.index(x)].set(1)  # Mise à jour de la valeur sélectionnée
            if x == 'narrow':  # Réinitialisation du facteur d'échelle
                self.stepx = self.initx * 0.5
                self.scale_ratio = 0.5
            else:
                set_scale(1)
            self.ctrl.set_skin(x)
            self.update()

        skin_tag = ['default', 'lowkey', 'narrow']
        skin_status = [IntVar() for i in range(len(skin_tag))]
        skin_status[0].set(1)
        self.skin = set_skin

        # Création du menu déroulant Apparence
        skin_menu = Menu(display_menu, tearoff=0)
        display_menu.add_cascade(label=lang('skin'), menu=skin_menu)
        skin_menu.add_checkbutton(label=lang('default'), variable=skin_status[0], command=lambda: set_skin('default'))
        skin_menu.add_checkbutton(label=lang('lowkey'), variable=skin_status[1], command=lambda: set_skin('lowkey'))
        skin_menu.add_checkbutton(label=lang('narrow'), variable=skin_status[2], command=lambda: set_skin('narrow'))

        def set_scale(x):
            """
            Définir le facteur de zoom
            :param x: int
            :return: None
            """
            [st.set(0) for st in scale_status]  # Réinitialisation
            scale_status[scale_tag.index(x)].set(1)  # Mise à jour de la valeur sélectionnée
            self.img_view.delete(ALL)
            # Ajuste les décalages des changements d'échelle
            self.stepx = self.initx * x
            self.scale_ratio = x
            # Mise à jour de l'image
            self.ctrl.set_scale_ratio(x)
            self.update()

        scale_tag = [1, 2, 3]
        scale_status = [IntVar() for i in range(len(scale_tag))]
        scale_status[0].set(1)
        self.scale = set_scale

        # Création du menu déroulant Echelle
        scale_menu = Menu(display_menu, tearoff=0)
        display_menu.add_cascade(label=lang('scale'), menu=scale_menu)
        scale_menu.add_checkbutton(label="1x", variable=scale_status[0], command=lambda: set_scale(1))
        scale_menu.add_checkbutton(label="2x", variable=scale_status[1], command=lambda: set_scale(2))
        scale_menu.add_checkbutton(label="3x", variable=scale_status[2], command=lambda: set_scale(3))

        display_menu.add_separator()  # Séparateur menu
        display_menu.add_command(label=lang('period'), accelerator='Ctrl+T', command=lambda: self.period_view(root))

        # Création du menu déroulant Annoter
        annotate_menu = Menu(display_menu, tearoff=0)
        annotate_menu.add_command(label=lang('edge'), accelerator='Ctrl+E', command=lambda: self.mode.set('Node'))

        annotate_menu.add_command(label=lang('relation'), accelerator='Ctrl+R', command=lambda: self.relation_view(root))
        display_menu.add_cascade(label=lang('annotate'), menu=annotate_menu)
        menubar.add_cascade(label=lang('display'), menu=display_menu)

        # Colonne des paramètres
        settings_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=lang('settings'), menu=settings_menu)

        # Création du sous menu Langages
        lang_menu = Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label=lang('language'), menu=lang_menu)
        lang_menu.add_checkbutton(label=lang('en'), variable=self.language, onvalue='en',
                                  command=lambda: self.set_language('en'))
        lang_menu.add_checkbutton(label=lang('cn'), variable=self.language, onvalue='cn',
                                  command=lambda: self.set_language('cn'))
        lang_menu.add_checkbutton(label=lang('fr'), variable=self.language, onvalue='fr',
                                  command=lambda: self.set_language('fr'))

        settings_menu.add_checkbutton(label=lang('display_cursor'), variable=self.cursor, onvalue=1)

        def resize():
            """
            Définir le redimensionnement
            :return: None
            """
            if self.isResized:
                self.isResized = False
                root.resizable(width=False, height=False)
            else:
                self.isResized = True
                root.resizable(width=True, height=True)

        settings_menu.add_checkbutton(label=lang('resize'), variable=self.isResized, onvalue=True,
                                      command=lambda: resize())

        # Création du menu d'aide
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=lang('help'), menu=help_menu)

        def doc_wd():
            """
            Ouverture doc wavedrom
            :return: None
            """
            url = 'https://wavedrom.com/'
            import webbrowser
            webbrowser.open(url, new=0, autoraise=True)

        def doc_wdgen():
            """
            Ouverture doc wavedromgen
            :return: None
            """
            url = 'https://github.com/Tamachiii/wavedromgen'
            import webbrowser
            webbrowser.open(url, new=0, autoraise=True)

        # Création du sous menu Documentations
        docs_menu = Menu(help_menu, tearoff=0)
        help_menu.add_cascade(label=lang('doc'), menu=docs_menu)
        docs_menu.add_command(label=lang('doc_wd'), command=doc_wd)
        docs_menu.add_command(label=lang('doc_wdgen'), command=doc_wdgen)

        help_menu.add_separator()  # Séparateur menu

        def about():
            """
            A propos
            :return: None
            """
            # Créer une fenêtre contextuelle
            top = Toplevel(background='white')
            top.title(self.lang('about'))
            top.iconbitmap(self.asset_dir + 'app.ico')
            screenwidth = root.winfo_screenwidth()
            screenheight = root.winfo_screenheight()
            width, height = 300, 300
            alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
            top.geometry(alignstr)
            top.resizable(width=False, height=False)

            image = Image.open(self.asset_dir + 'app.ico')
            image = image.resize((128, 128), Image.ANTIALIAS)
            self.app = ImageTk.PhotoImage(image)

            Label(top, image=self.app, background='white').pack(side=tk.TOP, pady=10)
            Label(top, text='WaveDromGen', background='white', font=("Courier", 18, tk.font.ROMAN)).pack()
            Label(top, text='Version: ' + self.version, background='white', font=("Courier", 10, tk.font.ROMAN)).pack()
            Label(top, text='  Created By Henson', background='white', font=("Courier", 8, tk.font.ROMAN)).pack()
            Label(top, text='Version: ' + self.versionModified, background='white',
                  font=("Courier", 10, tk.font.ROMAN)).pack()
            Label(top, text='  Modified By Tony Nguyen', background='white', font=("Courier", 8, tk.font.ROMAN)).pack()
            Button(top, text=self.lang('ok'), width=10, background='white', relief='groove',
                   command=lambda: top.destroy()).pack(pady=16)

        help_menu.add_command(label=lang('about'), command=about)
        root.config(menu=menubar)

    def relation_view(self, root):
        """
        Ouvre le panneau de gestion des relations
        :param root: frame supérieur
        :return: None
        """

        # Création de la fenêtre de gestion des relations
        relation_window = Toplevel(root)
        relation_window.title(self.lang('relation'))
        relation_window.iconbitmap(self.asset_dir + 'app.ico')
        width_relation = 360
        height_relation = 480
        screenwidth_relation = relation_window.winfo_screenwidth()
        screenheight_relation = relation_window.winfo_screenheight()
        geo_relation = '%dx%d+%d+%d' % (width_relation, height_relation, (screenwidth_relation - width_relation) / 2, (screenheight_relation - height_relation) / 2)
        relation_window.geometry(geo_relation)
        relation_window.resizable(width=False, height=False)

        # Création d'une frame pour contenir les widgets
        annotation_frame = Frame(relation_window)
        annotation_frame.pack(fill=BOTH, expand=True)

        # Création du titre
        title_label = Label(annotation_frame, text=self.lang('relation'))
        title_label.pack()

        # Création d'une listbox pour représenter chaque relation
        relation_listbox = Listbox(annotation_frame, font='14')
        relation_listbox.pack(fill=BOTH, expand=True)

        # Création d'une barre de défilement verticale
        v_scroll_bar = Scrollbar(relation_listbox, orient=VERTICAL)
        v_scroll_bar.pack(side=RIGHT, fill=BOTH)
        relation_listbox.config(yscrollcommand=v_scroll_bar.set)
        v_scroll_bar.config(command=relation_listbox.yview)

        # Création d'une barre de défilement horizontale
        h_scroll_bar = Scrollbar(relation_listbox, orient=HORIZONTAL)
        h_scroll_bar.pack(side=BOTTOM, fill=BOTH)
        relation_listbox.config(xscrollcommand=h_scroll_bar.set)
        h_scroll_bar.config(command=relation_listbox.xview)

        # Création d'une frame pour contenir les boutons d'ajout, de modification et de suppression
        buttons_bar_frame = Frame(annotation_frame)
        buttons_bar_frame.pack(side=BOTTOM, fill=BOTH)

        # Variables locales à la fonction relation_window()
        style_list = (
            '~', '-~', '<~>', '<-~>', '~>', '-~>', '~->', '-', '-|',
            '-|-', '<->', '<-|>', '<-|->', '->', '-|>', '-|->', '|->', '+'
        )  # Liste des styles des arrow (défini par wavedrom)
        nodes_list = []  # Liste des noeuds existants
        relations_list = []  # Liste des relations existantes
        global counter # Variable de vérification d'ouverture du panneau d'ajout/modif des relations
        counter = 0

        # Chargement des noeuds dans la variable nodes_list
        node = ''
        for y in range(self.ctrl.get_row_len()):
            node += ''.join(self.ctrl.read_node(y=y))
        nodes_list = list(node.replace('.', ''))

        # Charger une arête existante
        relations_data = self.ctrl.read_edge()
        for relation in relations_data:
            tmp, name = relation.split(' ')
            print([tmp[0], tmp[1:-1], tmp[-1], name])
            relations_list.append([tmp[0], tmp[1:-1], tmp[-1], name])

        # Cration des boutons
        add_button = Button(buttons_bar_frame, text=str(self.lang('add') + ' ' + self.lang('relation')), command=lambda: set_relation('add'))
        add_button.pack(side=LEFT, fill=BOTH, expand=True)

        mod_button = Button(buttons_bar_frame, text=str(self.lang('modify') + ' ' + self.lang('relation')), command=lambda: set_relation('modify'))
        mod_button.pack(side=LEFT, fill=BOTH, expand=True)
        mod_button.configure(state=DISABLED)

        def set_relation(mode):
            """
            Ouvre l'interface permettant d'ajouter ou de modifier une relation
            :param mode: 'add' permet d'ajouter une relation, 'modify' permet de modifier une relation
            :return:
            """

            global counter # Variable de vérification d'ouverture du panneau d'ajout/modif des relations

            if counter < 1: # Si aucun panneau est ouvert alors la variable reçoit et on continue le programme sinon on retourne rien
                counter = 1
            else:
                return

            # Création de la fenêtre permettant d'ajouter ou de modifier des relations
            panel_relation_window = Toplevel(relation_window)
            panel_relation_window.iconbitmap(self.asset_dir + 'app.ico')

            # Placement de la fenêtre au centre de l'écran
            panel_relation_window.tk.call('tk::PlaceWindow', panel_relation_window)

            # Création des titres correspondants aux widgets ci-dessous
            cb_edge1_title = Label(panel_relation_window, text=str(self.lang('edge') + ' 1'))
            cb_edge1_title.grid(row=0, column=0)
            cb_style_title = Label(panel_relation_window, text=self.lang('style'))
            cb_style_title.grid(row=0, column=1)
            cb_edge2_title = Label(panel_relation_window, text=str(self.lang('edge') + ' 1'))
            cb_edge2_title.grid(row=0, column=2)
            entry_title = Label(panel_relation_window, text=self.lang('name'))
            entry_title.grid(row=0, column=3)

            # Création des widgets caractérisants les relations
            cb_edge1 = ttk.Combobox(panel_relation_window, width=10, values=nodes_list)
            cb_edge1.grid(row=1, column=0, padx=5)
            cb_style = ttk.Combobox(panel_relation_window, width=10, values=style_list)
            cb_style.grid(row=1, column=1, padx=5)
            cb_edge2 = ttk.Combobox(panel_relation_window, width=10, values=nodes_list)
            cb_edge2.grid(row=1, column=2, padx=5)
            entry = Entry(panel_relation_window, width=20)
            entry.grid(row=1, column=3, padx=5)
            add_button = Button(panel_relation_window, width=60)
            add_button.grid(row=2, column=0, columnspan=4, padx=5, pady=5)

            # Index de référence de la listbox
            index_listbox = -1

            # Apports des modifications en mode 'modify'
            if mode == 'modify':
                panel_relation_window.title(str(self.lang('modify') + ' ' + self.lang('relation')))
                index_listbox = relation_listbox.index(relation_listbox.curselection()) # Charge l'index de référence de la listbox
                add_button.configure(text=self.lang('modify'))
                cb_edge1.configure(state=DISABLED)
                cb_edge2.configure(state=DISABLED)
                # Chargement de la relation à modifier
                relation_to_modify = relations_list[index_listbox]
                cb_edge1.set(relation_to_modify[0])
                cb_style.set(relation_to_modify[1])
                cb_edge2.set(relation_to_modify[2])
                entry.insert(END, relation_to_modify[3])
            # Apports des modifications en mode 'add'
            else:
                panel_relation_window.title(str(self.lang('add') + ' ' + self.lang('relation')))
                add_button.configure(text=self.lang('add'))

            def commit():
                """
                Validation d'ajout ou de modification d'une relation
                :return:
                """
                global counter # Variable de vérification d'ouverture du panneau d'ajout/modif des relations
                # Chargement de la relation dite temporaire : celle qui va être ajouté à la liste finale des relations
                relation_temp = [cb_edge1.get(), cb_style.get(), cb_edge2.get(), entry.get()]
                # En mode 'modify' on remplace seulement le style et le nom de la relation concernée
                if mode == 'modify':
                    relations_list[index_listbox][1] = relation_temp[1]
                    relations_list[index_listbox][3] = relation_temp[3]
                # En mode 'add' on vérifie l'entrée des données afin d'avoir une relation cohérente
                if mode == 'add':
                    # Vérification des noeuds sinon on écrit un message d'erreur
                    if relation_temp[0] in nodes_list and relation_temp[1] in style_list and relation_temp[
                        2] in nodes_list:
                        # Si la liste est vide on ajoute direct la relation car elle n'existe pas en double
                        if len(relations_list) == 0:
                            relations_list.append(relation_temp)
                        # Sinon on écrit un message d'erreur si une relation existe déjà entre deux noeuds, sinon on ajoute la relation
                        else:
                            for i in range(len(relations_list)):
                                if (relations_list[i][0] == relation_temp[0] and relations_list[i][2] == relation_temp[
                                    2]) \
                                        or (relations_list[i][2] == relation_temp[2] and relations_list[i][1] ==
                                            relation_temp[1]):
                                    tk.messagebox.showerror(title=self.lang('creation_error'),
                                                            message=self.lang('msg_existing_error'),
                                                            parent=panel_relation_window)
                                else:
                                    relations_list.append(relation_temp)
                    else:
                        tk.messagebox.showerror(title=self.lang('input_error'),
                                                message=self.lang('msg_creation_error'),
                                                parent=panel_relation_window)
                # Mise à jour de la listebox, remise à zéro de la variable 'counter' et fermeture du panneau
                update_listbox()
                counter = 0
                panel_relation_window.destroy()

            def on_closing():
                """
                Remise à éro de la variable global counter lors de la fermeture du panneau si l'ajout ou la modification de relation n'a pas été effectué
                :return:
                """
                global counter
                counter = 0
                panel_relation_window.destroy()

            add_button.configure(command=commit)

            panel_relation_window.protocol("WM_DELETE_WINDOW", on_closing)

        def delete_relation():
            """
            Supprime la relation selectionnée dans la listbox de la 'relations_list'
            :return:
            """
            relations_list.pop(relation_listbox.index(relation_listbox.curselection()))
            update_listbox()
            leave()

        del_button = Button(buttons_bar_frame, text=str(self.lang('delete') + ' ' + self.lang('relation')), command=delete_relation)
        del_button.pack(side=LEFT, fill=BOTH, expand=True)
        del_button.configure(state=DISABLED)

        def select(event):
            """
            Evenement de selection d'un item de la listbox
            :param event:
            :return:
            """
            try:
                if relation_listbox.index(relation_listbox.curselection()) >= 0:
                    mod_button.configure(state=NORMAL)
                    del_button.configure(state=NORMAL)
            except:
                mod_button.configure(state=DISABLED)
                del_button.configure(state=DISABLED)

        def leave(event=None):
            """
            Evenement de sortie de la listbox
            :param event:
            :return:
            """
            relation_listbox.selection_clear(0, END)
            mod_button.configure(state=DISABLED)
            del_button.configure(state=DISABLED)

        def update_listbox():
            """
            Mise à jour de la listbox
            :return:
            """
            relation_listbox.delete(0, END)
            ret = []
            for relation in relations_list:
                relation_listbox.insert(END, relation[0] + ' ' + relation[1] + ' ' + relation[2] + ' ' + relation[3])
                ret.append('{0}{1}{2} {3}'.format(relation[0], relation[1], relation[2], relation[3]))
            self.ctrl.write_edge(ret)
            self.update()

        # Bindings
        relation_listbox.bind('<<ListboxSelect>>', select)
        #relation_listbox.bind('<FocusOut>', leave)

        update_listbox()

    def period_view(self, root):
        """
        Ouvre le panneau de gestion des périodes et phases
        :param root: frame supérieur
        :return: None
        """

        # Création de la fenêtre de gestion des périodes et phases
        period_window = Toplevel(root)
        period_window.tk.call('tk::PlaceWindow', period_window)
        period_window.resizable(width=False, height=False)

        # Variables locales à la fonction relation_window()
        signal_list = [] # Liste des signaux
        signal_list_names = [] # Liste des noms des signaux

        # Chargement de la liste des signaux
        for i in range(self.ctrl.get_row_len()):
            name = self.ctrl.read_name(i)
            signal_list_names.append(str(i) + ' : ' + name)
            phase = self.ctrl.get_phase(i)
            period = self.ctrl.get_period(i)
            signal_list.append([name, phase, period])

        # Création du titre de l'interface
        title = Label(period_window, text=self.lang('management_periods_phases'), font=("Arial", 10))
        title.pack(padx=10, pady=10)

        # Frame central contenant le frame des labels et le frame des données à saisir
        middle_frame = Frame(period_window)
        middle_frame.pack(padx=10)

        # Frame des titres des données à saisir
        titles_frame = Frame(middle_frame)
        titles_frame.pack(side=LEFT)
        signal_title = Label(titles_frame, text=self.lang('signal'), width=10)
        signal_title.pack()
        phase_title = Label(titles_frame, text=self.lang('phase'), width=10)
        phase_title.pack()
        period_title = Label(titles_frame, text=self.lang('period'), width=10)
        period_title.pack()

        # Frame des widgets contenant les données à saisir
        datas_frame = Frame(middle_frame)
        datas_frame.pack(side=RIGHT)
        cb_signal = ttk.Combobox(datas_frame, state='readonly', values=signal_list_names, width=20)
        cb_signal.pack()
        phase_entry = Entry(datas_frame, width=23)
        phase_entry.pack()
        period_entry = Entry(datas_frame, width=23)
        period_entry.pack()

        # Frame du bas contenant la barre des boutons
        buttons_frame = Frame(period_window)
        buttons_frame.pack(padx=10, pady=10)

        def get_cb_index():
            """
            Retourne l'index de la combobox contenant correspondant aux signaux
            :return:
            """
            return cb_signal.current()

        def update_widgets():
            """
            Mise à jour des widgets contenant les données à saisir
            :return:
            """
            phase_entry.delete(0, END)
            period_entry.delete(0, END)
            index = get_cb_index()
            phase_entry.insert(END, signal_list[index][1])
            period_entry.insert(END, signal_list[index][2])

        def commit():
            """
            Soumettre les résultats des périodes et phases
            :return:
            """
            # Vérification des données appartenant aux bons domaines
            try:
                temp_phase = float(phase_entry.get())
                temp_period = int(period_entry.get())
                if temp_phase >= 0 and temp_period >= 0:
                    # Remplacement des données
                    signal_list[cb_signal.current()][1] = temp_phase
                    signal_list[cb_signal.current()][2] = temp_period
                    self.ctrl.set_phase(cb_signal.current(), temp_phase)
                    self.ctrl.set_period(cb_signal.current(), temp_period)
                    # Faire le rendu de la ligne modifiée
                    self.ctrl.renderLine([cb_signal.current()])
                    # Mise à jour
                    self.update()
                    self.note.render()  # bypass pour faire le rendu en passant par l'éditeur en json quand il y a des relations qui bloquent le programme
            except:
                tk.messagebox.showerror(title=self.lang('input_error'),
                                        message=self.lang('msg_set_period'),
                                        parent=period_window)
                # Remettre les anciennes données
                phase_entry.delete(0, END)
                period_entry.delete(0, END)
                phase_entry.insert(END, signal_list[cb_signal.current()][1])
                period_entry.insert(END, signal_list[cb_signal.current()][2])

        apply_button = Button(buttons_frame, text=self.lang('apply'), width=14, command=commit)
        apply_button.pack(side=LEFT, fill=X, padx=2)
        apply_button.configure(state=DISABLED)

        def reset():
            """
            Réinitialise les données dans les widgets ainsi que les périodes et phases du signal selectionné
            :return:
            """
            index = get_cb_index()
            signal_list[index][1] = 0
            signal_list[index][2] = 1
            update_widgets()
            commit()

        reset_button = Button(buttons_frame, text=self.lang('reset'), width=14, command=reset)
        reset_button.pack(side=RIGHT, fill=X, padx=2)
        reset_button.configure(state=DISABLED)

        def select(event):
            """
            Evenement de selection du combobox 'cb_signal'
            :param event:
            :return:
            """
            update_widgets()
            phase_entry.configure(state=NORMAL)
            period_entry.configure(state=NORMAL)
            if cb_signal.current() >= 0:
                apply_button.configure(state=NORMAL)
                reset_button.configure(state=NORMAL)

        # Bindings
        cb_signal.bind("<<ComboboxSelected>>", select)

    def buttonbar_view(self, root):
        """
        Création de la barre d'actions wavedrom
        :param root: Frame supérieur
        :return: None
        """
        button_view_root = Frame(root, bg='white')
        button_view_root.pack(side=LEFT, fill=Y, padx=2)

        items = ['clk', 'sig', 'bus', 'x', 'gap', 'z', 'SEL', 't', 'clr']

        # Étiquette vierge, utilisée comme espace réservé
        Label(button_view_root, bg='white', height=1).pack()
        # Créer les boutons
        for itm in items:
            image = Image.open(self.asset_dir + "%s.gif" % itm)
            image = image.resize((22, 22), Image.ANTIALIAS)
            icon = ImageTk.PhotoImage(image)
            # Button(button_view_root, image=icon).pack(anchor='w')
            Radiobutton(button_view_root, bg='white', image=icon, variable=self.mode, value=itm,
                        indicatoron=False).pack(anchor='w', pady=2)
            self.icon_pool.append(icon)  # Empêcher la publication d'images

    def statusbar_view(self, root):
        """
        Création de la barre de status
        :param root: Frame supérieur
        :return: None
        """
        status_view = Frame(root, bg='white')
        status_view.pack(side=BOTTOM, fill=X, pady=2)

        Label(status_view, bg='white', text='  Mode:').pack(side=LEFT)
        Label(status_view, bg='white', textvariable=self.mode, anchor=NW).pack(side=LEFT, fill=X, pady=2)

        Label(status_view, bg='white', text='  Rows:').pack(side=LEFT)
        Label(status_view, bg='white', textvariable=self.lenRow, anchor=NW).pack(side=LEFT, fill=X, pady=2)

        Label(status_view, bg='white', text='  Columns:').pack(side=LEFT)
        Label(status_view, bg='white', textvariable=self.lenCol, anchor=NW).pack(side=LEFT, fill=X, pady=2)

        Label(status_view, bg='white', textvariable=self.position, anchor=NW).pack(side=RIGHT, fill=X, pady=2)

    def wave_view(self, root):
        """
        Créer la zone d'édition des Waves
        :param root: Frame supérieur
        :return: None
        """

        # Changements de décalage dus aux changements d'échelle
        # k : coefficient d'échelle, v : valeur de décalage
        scale_offset = {
            0.5: -3,
            1: -1.5,
            2: -0.2,
            3: 0.3
        }

        def create_rectangle(x1, y1, x2, y2, fill, alpha):
            """
            Dessiner une boîte transparente
            :param x1:
            :param y1:
            :param x2:
            :param y2:
            :param fill: couleur de remplissage
            :param alpha: transparence
            :return: tk object
            """
            alpha = int(alpha * 255)
            fill = root.winfo_rgb(fill) + (alpha,)
            image = Image.new('RGBA', (x2 - x1, y2 - y1), fill)
            self.bbox = ImageTk.PhotoImage(image)
            return img_view.create_image(x1, y1, image=self.bbox, anchor='nw')

        """
            Ancienne version sans la scrollbar du canva
            def get_pos(event):
            """"""
            Get la position actuelle
            :param event:
            :return: tuple,(x, y)
            """"""
            cal = event.x / self.stepx - self.x_name_offset * 0.5 + scale_offset[self.scale_ratio]
            x = -1 if cal < 0 else int(cal)  # x décalage offset
            if x < -1:
                x = -1
            y = event.y // self.stepy
            self.position.set('(X:%2s, Y:%2s)  ' % (x, y))
            return x, y"""

        def get_pos(event):
            """
            Get la position actuelle de la souris dans le canva (wave_view) puis retourne les coordonnées à l'échelle de l'éditeur
            :param event:
            :return: tuple,(x, y)
            """
            w, eX, eY = event.widget, event.x, event.y
            cal = w.canvasx(eX) / self.stepx - self.x_name_offset * 0.5 + scale_offset[self.scale_ratio]
            x = -1 if cal < 0 else int(cal)  # x décalage offset
            if x < -1:
                x = -1
            y = int(w.canvasy(eY) // self.stepy)
            self.position.set('(X:%2s, Y:%2s)  ' % (x, y))
            return x, y

        def gen_edit_box(event, x, y, b1_motion=False, node_mode=None):
            """
            Création d'ne zone d'édition flottante
            :param event: Position de l'événement, obtenir la position de clic d'origine
            :param x: Clique sur la colonne
            :param y: Clique sur la ligne
            :param b1_motion: Lorsque le bouton gauche est enfoncé et déplacé, l'action de réponse est déclenchée
            :param node_mode: Modification des propriétés node
            :return: None
            """

            # Confirmer la soumission
            def submit(event=None):
                value = edit_box.get(0.0, "end").replace('\n', '')
                # Chargement des noeuds dans la variable nodes_list
                nodes_list = []
                node = ''
                for i in range(self.ctrl.get_row_len()):
                    node += ''.join(self.ctrl.read_node(y=i))
                nodes_list = list(node.replace('.', ''))
                if node_mode:
                    # Lorsque que la longueur de 'value' est supérieur à 1 alors on ne crée pas de node
                    if len(value) != 1:
                        value = ''
                        tk.messagebox.showwarning(title=self.lang('input_error'), message=self.lang('msg_edge_error'))
                    if value in nodes_list:
                        value = ''
                        tk.messagebox.showwarning(title=self.lang('input_error'), message=self.lang('msg_existing_node_error'))
                self.ctrl.t_mode(x=x, y=y, val=value, node_mode=node_mode)
                self.update()
                editbox_view.destroy()

            # Lorsque vous maintenez b1 enfoncé et que vous faites glisser, aucune opération n'est effectuée
            if b1_motion:
                return
            # -1 est répertorié comme nom de signal et l'attribut de nom de signal est lu lorsqu'il est sélectionné
            elif x == -1:
                val = self.ctrl.read_name(y=y)
            # En mode annotation, accéder aux propriétés du nœud
            elif node_mode:
                val = self.ctrl.read_node(x=x, y=y)
            else:
                val = self.ctrl.read_data(x=x, y=y)
            editbox_view = Frame(wave_view, bg='white')
            editbox_view.place(x=event.widget.canvasx(event.x) - self.stepx,
                               y=y * self.stepy)  # Lorsque x est négatif, pointez les coordonnées sur 0

            # Zone d'édition
            edit_box = Text(editbox_view, width=15, height=1)
            edit_box.pack(side=LEFT)
            edit_box.insert('end', val)
            edit_box.bind("<Return>", submit)  # if len(val) == 1 else 0
            # Bouton de confirmation
            Button(editbox_view, width=12, relief='groove', image=self.icon_y, command=submit).pack(side=LEFT)
            Button(editbox_view, width=12, relief='groove', image=self.icon_n,
                   command=lambda: editbox_view.destroy()).pack(side=LEFT)

            #edit_box.tk_focusFollowsMouse()  # Focalisez la souris sur la zone d'édition

        def click(event, b1_motion=False):
            """
            Cliquez sur l'événement
            :param event:
            :param b1_motion: Déclenché lorsque vous maintenez le bouton gauche enfoncé pour vous déplacer
            :return: None
            """
            mode = self.mode.get()

            # Lors du déplacement selon b1, les coordonnées actuelles ne sont pas mises à jour
            if b1_motion:
                x, y = event.widget.canvasx(event.x), event.widget.canvasy(event.y)
            else:
                x, y = get_pos(event)
            # Lorsque la longueur db est dépassée, elle ne sera exécutée que si le mode est 'SEL'
            if y >= self.ctrl.get_row_len() or x >= self.ctrl.get_col_len():
                if mode == 'SEL':
                    if y >= self.ctrl.get_row_len():
                        self.ctrl.add_row(y - self.ctrl.get_row_len() + 1)
                    if x >= self.ctrl.get_col_len():
                        self.ctrl.add_col(x - self.ctrl.get_col_len() + 1)
                else:
                    return None

            # Mode et fonction de traitement correspondante
            if mode == 'sig':
                self.ctrl.sig_mode(x, y, b1_motion=b1_motion)
            elif mode == 'clk':
                self.ctrl.clk_mode(x, y)
            elif mode == 'bus':
                self.ctrl.bus_mode(x, y, val=self.busColor.get())
            elif mode == 'x':
                self.ctrl.x_mode(x, y)
            elif mode == 'z':
                self.ctrl.z_mode(x, y)
            elif mode == 'gap':
                self.ctrl.gap_mode(x, y)
            elif mode == 't':
                gen_edit_box(event=event, x=x, y=y, b1_motion=b1_motion)
            elif mode == 'Node':
                gen_edit_box(event=event, x=x, y=y, b1_motion=b1_motion, node_mode=True)
            elif mode == 'delRow':
                self.img_view.delete(ALL)
                self.ctrl.del_row(y=y)
                # Mode de signal par défaut
                self.mode.set('sig')  # Reset pour éviter de rester en mode suppression
            elif mode == 'delCol':
                self.img_view.delete(ALL)
                self.ctrl.del_col(x=x)
                # Mode de signal par défaut
                self.mode.set('sig')  # Reset pour éviter de rester en mode suppression
            elif mode == 'clr':
                self.ctrl.clear(y=y)
            elif mode == 'earlyWave':
                self.ctrl.early_wave(x=x, y=y)
            elif mode == 'delayWave':
                self.ctrl.delay_wave(x=x, y=y)

            self.update()

            if not b1_motion:
                self.lastPos = (x, y)

        def b1motion(event):
            """
            Maintenir l'événement glisser b1 enfoncé
            :param event:
            :return: None
            """
            x, y = get_pos(event)
            # Hors de portée
            if y >= self.ctrl.get_row_len():
                return None
            # Dessiner une animation lorsque le mode est SWAP ou COPY
            elif self.mode.get() in ['SWAP', 'COPY', 'SEL']:
                if self.mini_img:  # Vignette mobile
                    img_view.moveto(self.mini_img, x=(event.widget.canvasx(event.x) - self.lastPos[0]),
                                    y=event.widget.canvasx(event.y) - self.stepy // 2)
                    img_view.moveto(self.x_line, x=0, y=event.y - self.stepy // 2)
                else:  # Sinon création d'une vignette
                    self.mini_img = self.img_view.create_image(0, event.y + self.stepy // 2, image=self.img[y],
                                                               anchor='nw')
                    self.lastPos = (event.widget.canvasx(event.x), self.lastPos[1])
            elif not self.lastPos == (x, y):  # Jugement de fonctionnement lors du glissement
                # Modifiez uniquement la valeur x et non la valeur y lorsque vous maintenez b1 enfoncé et que vous faites glisser
                event.x, event.y = x, self.lastPos[1]
                click(event, b1_motion=True)
                self.lastPos = (x, y)

            # Maj axe vertical
            img_view.moveto(self.y_line, x=event.widget.canvasx(event.x))

        def release(event):
            """
            Evénement de libération b1
            :param event:
            :return: None
            """
            mode = self.mode.get()
            x, y = get_pos(event)
            if y >= self.ctrl.get_row_len():  # Hors de portée
                pass
            elif mode == 'SEL':
                if not y == self.lastPos[1]:  # Mouvement vertical
                    if self.ctrl_press.get():
                        self.ctrl.copy_line(src=self.lastPos[1], dst=y)
                    else:
                        self.ctrl.swap_line(src=self.lastPos[1], dst=y)
                else:  # Mouvement latéral
                    x_offset = (event.widget.canvasx(event.x) - self.lastPos[0]) // self.stepx
                    if x_offset > 0:
                        self.ctrl.delay_wave(x=x - 1, y=y, num=x_offset)
                    elif x_offset < 0:
                        self.ctrl.early_wave(x=x - 1, y=y, num=abs(x_offset))
                    self.update()
            elif mode == 'SWAP':
                self.ctrl.swap_line(src=self.lastPos[1], dst=y)
            elif mode == 'COPY':
                self.ctrl.copy_line(src=self.lastPos[1], dst=y)
            # Supprimer l'image miniature
            self.img_view.delete(self.mini_img)
            self.mini_img = None
            self.update()
            self.note.render()  # bypass pour faire le rendu en passant par l'éditeur en json quand il y a des relations qui bloquent le programme

        def motion(event):
            """
            Evénement de déplacement de la souris
            :param event:
            :return: None
            """
            x, y = get_pos(event)
            img_view.moveto(self.x_line, y=y * self.stepy)
            # event.x != event.widget.canvasx(event.x)
            img_view.moveto(self.y_line, x=event.widget.canvasx(event.x))
            # self.note.render()

        def enter(event):
            """
            Evénement d'entrée de la souris
            :param event:
            :return: None
            """
            x, y = get_pos(event)
            # temp
            width_y = None
            # width_x = img_view.winfo_screenwidth()
            width_x = img_view.winfo_width()
            # width_y = img_view.winfo_screenheight()
            if (self.img_view.bbox("all")[3] < img_view.winfo_screenheight()):
                width_y = img_view.winfo_screenheight()
            else:
                width_y = self.img_view.bbox("all")[3]
            if self.cursor.get():
                # event.x != event.widget.canvasx(event.x)
                self.y_line = img_view.create_line(event.widget.canvasx(event.x), 0, event.widget.canvasx(event.x),
                                                   width_y, fill='lightgray', dash=(6, 6))
                self.x_line = create_rectangle(0, y * self.stepy, width_x, (y + 1) * self.stepy, fill='black',
                                               alpha=0.1)
            self.img_view.configure(
                scrollregion=(0, 0, (self.img_view.bbox("all")[2] + 30), (self.img_view.bbox("all")[3] + 30)))

        def leave(event):
            """
            Déclenché lorsque la souris quitte
            :param event:
            :return:
            """
            img_view.delete(self.x_line)
            img_view.delete(self.y_line)

        def scroll(event):
            """
            Permet de scroller dans le canva (img_view)
            :param event:
            :return:
            """
            img_view.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # Construire la fenêtre de dessin
        wave_view = Frame(root, bg='white')
        wave_view.pack(fill=BOTH, expand=True)
        # Création du canva
        img_view = Canvas(wave_view, bg='white')
        img_view.pack(side=LEFT, anchor=N, fill=BOTH, expand=True)
        self.img_view = img_view

        # Création des barres de défilement
        v_scroll_bar = Scrollbar(img_view, orient=VERTICAL, command=img_view.yview)
        v_scroll_bar.pack(side=RIGHT, fill=Y)
        h_scroll_bar = Scrollbar(img_view, orient=HORIZONTAL, command=img_view.xview)
        h_scroll_bar.pack(side=BOTTOM, fill=X)
        img_view.configure(xscrollcommand=h_scroll_bar.set, yscrollcommand=v_scroll_bar.set)
        img_view.configure(scrollregion=img_view.bbox("all"))

        # Liaison d'événement
        img_view.bind('<Button-1>', click)
        img_view.bind('<B1-Motion>', b1motion)
        img_view.bind('<ButtonRelease-1>', release)
        img_view.bind('<Motion>', motion)
        img_view.bind('<Enter>', enter)
        img_view.bind('<Leave>', leave)
        img_view.bind_all("<MouseWheel>", scroll)

    def restore_json(self, json_db):
        """
        Enregistrement du contenu de la boîte d'édition json db
        :param json_db:
        :return:
        """
        self.ctrl.restore_json(json_db)
        self.update()
        self.sheet.select(self.wave_frame)

    def update(self):
        """
        Mettre à jour des variables internes et les images
        :return: None
        """
        # self.ctrl.query()
        # Calculer le décalage apporté par la longueur du nom du signal
        self.x_name_offset = ((self.ctrl.get_name_len() - 4) / 2.5) + 1

        for k, v in self.ctrl.imgDB.items():
            # im = Image.open(v)
            im = v
            w, h = im.size
            self.img[k] = ImageTk.PhotoImage(im)
            # Dessinez un rectangle vierge pour supprimer l'image d'origine
            self.img_view.create_rectangle(0, k * self.stepy, w, h + k * self.stepy, fill='white', outline='white')
            # Mettre à jour du contenu de l'image
            self.img_view.create_image(0, k * self.stepy, image=self.img[k], anchor=NW)

        # Mettre à jour du texte
        self.note.set(self.ctrl.read_all())
        self.set_ascii(self.ctrl.to_ascii())

        # Mettre à jour du statut d'annulation/rétablissement
        undo_len, redo_len = self.ctrl.get_history_len()
        self.editmenu.entryconfig(0, state=tk.DISABLED if undo_len == 0 else tk.ACTIVE)
        self.editmenu.entryconfig(1, state=tk.DISABLED if redo_len == 0 else tk.ACTIVE)

        # Déplacer le curseur vers le haut
        if self.x_line:
            self.img_view.tag_raise(self.x_line)
            self.img_view.tag_raise(self.y_line)
        if self.mini_img:  # Vignette mobile
            self.img_view.tag_raise(self.mini_img)
            self.img_view.tag_raise(self.y_line)

        # Maj longueur ligne et colonne
        self.lenRow.set(self.ctrl.get_row_len())
        self.lenCol.set(self.ctrl.get_col_len())

        # Permet de faire fonctionner la fonction de défilement
        self.img_view.configure(
            scrollregion=(0, 0, (self.img_view.bbox("all")[2] + 30), (self.img_view.bbox("all")[3] + 30)))
        # self.img_view.itemconfig('window', height=(self.img_view.winfo_height() - 100), width=(self.img_view.winfo_width() - 100))  # Redéfinit la fenêtre du cadre sur la taille du canva

    def new(self):
        """
        Nouvelle fenetre
        :return: None
        """
        self.skin('default')
        self.scale(1)
        self.ctrl.init()
        self.img_view.delete(ALL)
        self.update()
        self.busColor.set('=')

    def saveas(self, fname=None):
        """
        Enregistrer sous
        :param fname: Nom de fichier, si aucun nom de fichier n'est spécifié, ouvre la fenêtre de sélection
        :return: None
        """
        if fname is None:
            f = filedialog.asksaveasfile(initialdir=".", filetypes=self.filetype, defaultextension=self.filetype)
        else:
            f = open(fname, 'w')
        # Enregistrer le document
        if f is None:
            return
        else:
            self.ctrl.save(handle=f)
        self.savefile = f.name

    def load(self, filename=None):
        """
        Charger le fichier json
        :param filename: Nom de fichier, ouvre le menu de sélection si non spécifié
        :return: None
        """
        if filename is None:
            filename = filedialog.askopenfilename(initialdir=".", filetypes=self.filetype)
            self.savefile = filename
        if not filename:
            return
        self.img_view.delete(ALL)
        self.ctrl.restore(filename=filename)
        self.update()

    def operate(self, cmd, num=1):
        """
        Analyser les commandes pour effectuer les opérations correspondantes
        :param num: Augmenter le nombre de lignes/colonnes
        :param cmd: Commande d'opération
        :return: None
        """
        if cmd == 'addRow':
            self.ctrl.add_row(num=num)
        elif cmd == 'addCol':
            self.ctrl.add_col(num=num)
        elif cmd == 'undo':
            self.ctrl.undo()
        elif cmd == 'redo':
            self.ctrl.redo()
        elif cmd == 'SWAP':
            self.mode.set('SWAP')

        self.update()

    def set_ascii(self, txt):
        """
        Écriture de la chaîne ascii dans l'interface
        :param txt: chaîne ascii
        :return: None
        """
        self.ascii_note.delete('1.0', END)
        self.ascii_note.insert(END, txt)

    def set_language(self, language):
        """
        Définition de la langue du système
        :param language: type de langue
        :return: None
        """
        # Supprimer les anciens fichiers de cache
        for i in language_dict.language:
            filename = self.tmp_dir + i
            if os.path.isfile(filename):
                os.remove(filename)
        f = open(self.tmp_dir + language, 'w')
        f.close()
        # Compte rendu
        tip = self.lang('tip')
        text = self.lang('restart_assert')
        showinfo(tip, text)

    def lang(self, id):
        """
        Obtenir le texte de l'interface utilisateur à partir de la bibliothèque de langues
        :param id:
        :return:
        """
        sel = language_dict.language[self.language.get()]
        return language_dict.lib[id][sel]


if __name__ == "__main__":
    wg = WaveDromUI()
