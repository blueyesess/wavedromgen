# Importer la bibliothèque de classes tkinter
import tkinter.font
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Scrollbar, Checkbutton, Label, Button  # Les composants de tkk seront optimisés
from PIL import Image, ImageTk
import json
import idlelib.colorizer as idc
import idlelib.percolator as idp
import WaveDromGen.language as language_dict

class WaveNote:
    # Le nom de l'image utilisée par la barre d'outils
    icons = ["render", "copy", "paste",
             "undo", "redo", "find_text"]
    icon_res = []

    # Opération d'initialisation
    def __init__(self, frame, asset_dir, update_wave, language):
        """
        :param frame: Frame supérieur
        :param asset_dir: chemin du répertoire
        :param update_wave: maj de la fonction d'onde
        :param language: langue de l'interface utilisateur
        """
        self.asset_dir = asset_dir
        self.root = frame
        self.language = language

        # méthode d'appel
        self.context_text = None  # texte actuel
        self.line_number_bar = None  # numéro de ligne
        self.update_wave = update_wave  # mettre à jour la forme d'onde

        self.create_tool_bar()  # barre d'outils

        self.create_body()  # zone de saisie de texte

    def render(self):
        """
        rendre le contenu actuel
        :return: None
        """
        json_db = self.get()
        try:
            db = json.loads(json_db)
            self.update_wave(db)
        except json.decoder.JSONDecodeError as e:
            messagebox.showerror('Error', e.msg)


    def find_text_dialog(self):
        """
        Générer une boîte de dialogue de recherche
        :return: None
        """
        search_dialog = Toplevel(self.root)
        search_dialog.title(self.lang('find'))
        search_dialog.iconbitmap(self.asset_dir + 'app.ico')

        # Dans le centre
        max_width, max_height = self.root.winfo_screenwidth(), self.root.winfo_screenheight()  # Largeur hauteur
        align_center = "325x60+%d+%d" % ((max_width - 320) / 2, (max_height - 60) / 2)
        search_dialog.geometry(align_center)
        search_dialog.resizable(False, False)
        Label(search_dialog, text=self.lang('find_text'), width=12).grid(row=0, column=0)
        search_text = Entry(search_dialog, width=25)
        search_text.grid(row=0, column=1, padx=2, pady=2, sticky="we")
        search_text.focus_set()
        # ignorer la casse
        ignore_case_value = IntVar()
        Checkbutton(search_dialog, text=self.lang('ignore_case'), variable=ignore_case_value).grid(
            row=1, column=1, sticky='e', padx=2, pady=2
        )
        Button(search_dialog, width=10, text=self.lang('find'),
               command=lambda: self.search_result(search_text.get(), ignore_case_value.get(), search_dialog,
                                                  search_text)).grid(row=0, column=2, sticky="w" + "e", padx=10, pady=1)

        def close_search_dialog():
            """
            Fermer la boîte de dialogue Rechercher du texte
            :return: None
            """
            self.context_text.tag_remove('match', 1.0, END)
            search_dialog.destroy()

        search_dialog.protocol("WM_DELETE_WINDOW", close_search_dialog)
        return "break"

    def search_result(self, key, ignore_case, search_dialog, search_box):
        """
        Méthode de recherche
        :param key:
        :param ignore_case:
        :param search_dialog:
        :param search_box:
        :return:
        """
        self.context_text.tag_remove('match', 1.0, END)
        matches_found = 0
        if key:
            start_pos = 1.0
            while True:
                start_pos = self.context_text.search(key, start_pos,
                                                     nocase=ignore_case,
                                                     stopindex=END)
                if not start_pos:
                    break
                end_pos = "{}+{}c".format(start_pos, len(key))
                self.context_text.tag_add('match', start_pos, end_pos)
                matches_found += 1
                start_pos = end_pos
            self.context_text.tag_config('match', foreground='white',
                                         background='green')
        search_box.focus_set()
        search_dialog.title(self.lang('match_found') % matches_found)

    def select_all(self):
        """
        Toute sélectionner
        :return:
        """
        self.context_text.tag_add('sel', 1.0, END)
        return "break"

    def create_tool_bar(self):
        """
        Créer une barre d'outils
        :return: None
        """
        tool_bar = Frame(self.root, height=25, background="#ffffff")  # Frame conteneur, blanc
        # remplir l'axe des x
        tool_bar.pack(fill="x")
        # Label(tool_bar, width=4, background='white').pack(side="left")
        # Générer le fichier image et placez-le à l'emplacement correspondant
        for icon in self.icons:
            tool_icon = Image.open(self.asset_dir + "%s.gif" % icon)  # Parce que c'est un tuple, il y a une virgule
            tool_icon = tool_icon.resize((16, 16), Image.ANTIALIAS)
            tool_icon = ImageTk.PhotoImage(tool_icon)
            tool_btn = Button(tool_bar, image=tool_icon, command=self.tool_bar_action(icon))
            tool_btn.pack(side="left")  # Image alignée à gauche
            # Ajouter tool_icon à icon_res
            self.icon_res.append(tool_icon)

    def tool_bar_action(self, action_type):
        """
        Mappage des comportements de la barre d'outils
        :param action_type:
        :return:
        """
        def handle():
            if action_type == "render":
                self.render()
            elif action_type == "copy":
                self.context_text.event_generate("<<Copy>>")
            elif action_type == "paste":
                self.context_text.event_generate("<<Paste>>")
            elif action_type == "undo":
                self.context_text.event_generate("<<Undo>>")
            elif action_type == "redo":
                self.context_text.event_generate("<<Redo>>")
            elif action_type == "find_text":
                self.find_text_dialog()

        # handle traitement des retours
        return handle

    def create_body(self):
        """
        Créer une zone d'édition
        :return:
        """
        # Gauche : numéro de ligne ; Droite : barre de défilement ; Milieu : zone d'édition de texte
        # champ de numéro de ligne

        self.line_number_bar = Text(self.root, width=3, padx=3, takefocus=0, border=0, background="#f0f0f0",
                                    state="disabled", font=("Courier", 12, tkinter.font.ROMAN))  # state="disable" impossible de modifier le statut
        # Remplir tout l'axe des ordonnées à gauche
        self.line_number_bar.pack(side='left', fill='y')
        # zone d'édition de texte
        # undo=True s'il faut avoir la fonction d'annulation de texte, wrap: comment envelopper, word: retour à la ligne, expand: peut être étiré
        self.context_text = Text(self.root, wrap="word", undo=True, font=("Courier", 12, tkinter.font.ROMAN))

        # raccourci clavier
        self.context_text.bind('<Any-KeyPress>', lambda e: self.update_line_num())
        self.context_text.pack(fill='both', expand=True)

        # Définir la zone de saisie de texte
        self.context_text.tag_config("active_line", background="#ffffff")

        def scroll_wave_note(*args):
            self.context_text.yview(*args)
            self.line_number_bar.yview(*args)

        # barre de défilement
        scroll_bar = Scrollbar(self.context_text)
        scroll_bar['command'] = scroll_wave_note
        self.context_text["yscrollcommand"] = scroll_bar.set
        self.line_number_bar["yscrollcommand"] = scroll_bar.set
        scroll_bar.pack(side="right", fill="y")

        # coloration syntaxique
        p = idp.Percolator(self.context_text)
        d = idc.ColorDelegator()
        d.recolorize()
        p.insertfilter(d)

    def update_line_num(self):
        """
        traitement des numéros de ligne
        :return:
        """
        # obtenir toutes les lignes
        row, col = self.context_text.index(END).split('.')
        # Lister le numéro de ligne de chaque ligne
        line_num_content = "\n".join([str(i) for i in range(1, int(row))])
        self.line_number_bar.config(state="normal")
        self.line_number_bar.delete(1.0, END)
        self.line_number_bar.insert(1.0, line_num_content)
        self.line_number_bar.config(state='disabled')

    def set(self, dic):
        # typographie
        txt = json.dumps(dic, indent=1)
        self.context_text.delete('1.0', END)
        self.context_text.insert(END, txt)
        # mettre à jour le numéro de ligne
        self.update_line_num()

    def get(self):
        return self.context_text.get('1.0', END)

    def lang(self, id):
        """
        Obtenir le texte de l'interface utilisateur à partir de la bibliothèque de langues
        :param id:
        :return:
        """
        sel = language_dict.language[self.language]
        return language_dict.lib[id][sel]
