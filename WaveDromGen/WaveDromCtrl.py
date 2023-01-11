# coding=utf-8
import os
import json
import wavedrom
from PIL import Image
import time
import cairosvg
from WaveDromGen.WaveDromDB import WaveDromDB
from WaveDromGen.WavedromASCII import WavedromASCII


class WaveDromCtrl:
    def __init__(self):
        # Paramètres configurables
        self.tmpDir = 'tmp/'  # Dossier temporaire

        # Variables accessibles en externe, mises à jour à chaque changement de données
        self.__wdb = None  # Base de données sous-jacente
        self.__lineChange = []  # Index de ligne où les modifications de données sont enregistrées
        self.imgDB = {}  # Stocker des images de rendu distriuées
        self.lastNameLen = 0
        self.stepy = 30
        self.curVal = 0  # Valeur de fonctionnement actuelle

        # Initialisation
        self.init()

    def init(self):
        """
        Initialisation
        :return: None
        """
        if not os.path.isdir(self.tmpDir):
            os.mkdir(self.tmpDir)

        self.__wdb = WaveDromDB()
        self.__render_dispatch(full_render=True)  # Rendu complet
        self.lastNameLen = self.__wdb.nameLen

    def write_wave(self, x, y, val):
        """
        Ecriture de la valeur dans une wave
        :param x: Indice de colonne
        :param y: Indice de ligne
        :param val: Valeur à écrire
        :return: None
        """
        # print(self.__wdb.read(typ='signal', k='wave', y=y))
        self.__wdb.write(typ='signal', k='wave', x=x, y=y, val=val)
        # if val in self.__wdb.special:  # Lors de l'écriture sur le bus, des 'data' seront créées
        #     self.write_data(x=x, y=y, val='0')
        # print(self.readAll())
        # print(self.__wdb.read(typ='signal', k='wave', y=y))

    def delay_wave(self, x, y, num=1):
        """
        Retarder la forme d'onde de num battements
        :param x: Numéro de ligne
        :param y: Numéro de colonne
        :param num: Le nombre de battements de retard, quand il est 1, le signal peut être élargi, et quand il est supérieur à 1, le signal sera retardé de 'num' dans son ensemble
        :return: None
        """
        self.__wdb.record()

        if num == 1:
            self.__wdb.read(typ='signal', k='wave', x=self.get_col_len(), y=y, pop_mode=True)
            self.__wdb.write(typ='signal', k='wave', x=x, y=y, val='.', insert_mode=True)
        else:
            for i in range(num):
                # Sortez le dernier puis insérez-le pour vous assurer que la longueur totale reste la même
                self.__wdb.read(typ='signal', k='wave', x=self.get_col_len(), y=y, pop_mode=True)
                self.__wdb.write(typ='signal', k='wave', x=1, y=y, val='.', insert_mode=True)
        self.__lineChange.append(y)
        self.__update()

    def early_wave(self, x, y, num=1):
        """
        Retarder la forme d'onde de 'num' battements
        :param x: Numéro de ligne
        :param y: Numéro de colonne
        :param num: Le nombre de battements à l'avance, lorsqu'il est de 1, le signal peut être élargi, lorsqu'il est supérieur à 1, le signal sera avancé de 'num' dans son ensemble
        :return: None
        """
        self.__wdb.record()

        if num == 1:
            self.__wdb.write(typ='signal', k='wave', x=self.get_col_len(), y=y, val='.', insert_mode=True)
            line = self.__wdb.read(typ='signal', k='wave', y=y)
            line = line[:x] + line[x + 1:]
            self.__wdb.write(typ='signal', k='wave', y=y, val=line)
        else:
            line = self.__wdb.read(typ='signal', k='wave', y=y)
            for i in range(num):
                line = line[0:1] + line[2:] + '.'
            self.__wdb.write(typ='signal', k='wave', y=y, val=line)
        self.__lineChange.append(y)
        self.__update()

    def write_data(self, x, y, val):
        """
        Ecriture de la valeur dans les 'data'
        :param x: Numéro de ligne
        :param y: Numéro de colonne
        :param val: Valeur à écrire
        :return: None
        """
        wave = self.__wdb.read(typ='signal', k='wave', y=y)
        try:
            data = self.__wdb.read(typ='signal', k='data', y=y).split(' ')
        except KeyError:
            data = []
        # Trouver l'index auquel les 'data' peuvent être définies
        idx = [i for i in range(self.get_col_len()) if wave[i] in self.__wdb.special]
        # Enregistrez la quantité de données pour '='
        num = len(idx)
        # Lorsque le montant '=' n'est pas égal aux 'data', ajoutez '0'
        # if not len(data) == num:
        #     data.append('0')
        # Trouver l'index le plus proche avant x
        index = [i for i in range(x, -1, -1) if i in idx]
        if index:  # L'écriture n'est autorisée que lorsqu'il y a un '=' courant
            i = idx.index(index.pop(0))
            # print(self.readAll())
            try:
                data[i] = val
            except IndexError:
                data.append(val)
        # Réponse
        self.__wdb.write(typ='signal', k='data', y=y, val=' '.join(data))

    def read_data(self, x, y):
        """
        Lecture 'data'
        :param x: Numéro de ligne
        :param y: Numéro de colonne
        :return: str
        """
        wave = self.__wdb.read(typ='signal', k='wave', y=y)
        data = self.__wdb.read(typ='signal', k='data', y=y).split(' ')
        # Trouver l'index auquel les 'data' peuvent être définies
        idx = [i for i in range(self.get_col_len()) if wave[i] in self.__wdb.special]
        # Trouver l'index le plus proche avant x
        idx = idx.index([i for i in range(x, -1, -1) if i in idx].pop(0))
        try:
            return data[idx]
        except IndexError:
            return ''

    def read_wave(self, x, y):
        """
        Lecture 'wave'
        :param x: Numéro de ligne
        :param y: Numéro de colonne
        :return: str
        """
        return self.__wdb.read(typ='signal', k='wave', x=x, y=y)

    def write_name(self, y, val):
        """
        Ecrire de la valeur dans 'name'
        :param y: Numéro de colonne
        :param val: Valeur à écrire
        :return: None
        """
        self.__wdb.write(typ='signal', k='name', y=y, val=val)

    def read_name(self, y):
        """
        Ecriture 'name'
        :param y: Numéro de colonne
        :return: None
        """
        return self.__wdb.read(typ='signal', k='name', y=y)

    # Ecrire une valeur de 'node'
    def write_node(self, x, y, val):
        """
        Ecriture 'node'
        :param x: Numéro de ligne
        :param y: Numéro de colonne
        :param val: 写入值
        :return: None
        """
        self.__wdb.write(typ='signal', k='node', y=y, x=x, val=val)

    def read_node(self, y, x=None):
        """
        Lecture 'node'
        :param x: Numéro de ligne
        :param y: Numéro de colonne，lire toute la ligne lorsque 'None'
        :return: str
        """
        ret = self.__wdb.read(typ='signal', k='node', y=y, x=x)
        return '' if ret == '.' else ret

    def read_edge(self):
        """
        Lecture 'edge'
        :return: str
        """
        return self.__wdb.read(typ='edge')

    def write_edge(self, val):
        """
        Ecriture 'edge'
        :param val: Valeur à écrire
        :return: None
        """
        self.__wdb.write(typ='edge', val=val)
        self.__render_dispatch(full_render=True)  # Compte rendu

    def read_all(self):
        """
        Lecture de toute la base de données
        :return: dict
        """
        return self.__wdb.read_all()

    def get_col_len(self):
        """
        Obtenir le nombre de colonnes
        :return: int
        """
        return self.__wdb.colLen

    def get_row_len(self):
        """
        Obtenir le nombre de lignes
        :return: int
        """
        return self.__wdb.rowLen

    def get_name_len(self):
        """
        Obtenir la longueur du nom
        :return: int
        """
        return self.__wdb.nameLen

    def set_scale_ratio(self, val):
        """
        Définir la valeur de mise à l'échelle
        :param val: int, Nombre proportionnel
        :return: None
        """
        self.__wdb.record()

        self.__wdb.write(typ='config', k='hscale', val=val)
        self.__render_dispatch(full_render=True)  # Compte rendu

    def set_skin(self, skin):
        """
        Définir de l'apparence de la forme d'onde
        :param skin: str，Nom de l'apparence
        :return: None
        """
        self.__wdb.record()

        self.__wdb.write(typ='config', k='skin', val=skin)
        self.__render_dispatch(full_render=True)  # Compte rendu

    def set_phase(self, y, val):
        """
        Définition de la phase
        :param y: Numéro de colonne
        :param val: Valeur à écrire
        :return: None
        """
        self.__wdb.record()

        self.__wdb.write(typ='signal', k='phase', y=y, val=val)

    def get_phase(self, y):
        """
        Obtenir la phase
        :param y: 行索引
        :return: int
        """
        return self.__wdb.read(typ='signal', k='phase', y=y)

    def set_period(self, y, val):
        """
        Définition du cycle
        :param y: Indice de ligne
        :param val: int Valeur de période
        :return: None
        """
        self.__wdb.record()
        self.__wdb.write(typ='signal', k='period', y=y, val=val)

    def get_period(self, y):
        """
        Obtenir la période
        :param y: Indice de ligne
        :return: int
        """
        return self.__wdb.read(typ='signal', k='period', y=y)

    def sig_mode(self, x, y, b1_motion=False):
        """
        Mode de signal à bit unique, si la valeur actuelle est 0 lors du déclenchement, écrivez 1, si c'est 1, écrivez 0
        :param x: Numéro de ligne
        :param y: Numéro de colonne
        :param b1_motion: 安装b1拖动，按住b1拖动时将连续写入
        :return: None
        """
        self.__wdb.record()

        if x == -1 or x > (self.get_col_len() - 1):
            return
        if not b1_motion:
            self.curVal = self.read_wave(x=x, y=y)
        nxt_val = '1' if self.curVal == '0' else '0'

        self.write_wave(x=x, y=y, val=nxt_val)
        self.__lineChange.append(y)
        self.__update()

    def clk_mode(self, x, y):
        """
        Mode 'clk' (horloge)
        :param x: Indice de ligne
        :param y: Indice de colonne
        :return: None
        """
        self.__wdb.record()

        if x == -1 or x > (self.get_col_len() - 1):
            return
        cur_val = self.read_wave(x=x, y=y)
        # Basculement de l'état de la valeur p -> P -> n -> N
        if cur_val == 'p':
            self.write_wave(x=x, y=y, val='P')
        elif cur_val == 'P':
            self.write_wave(x=x, y=y, val='n')
        elif cur_val == 'n':
            self.write_wave(x=x, y=y, val='N')
        elif cur_val == 'N':
            self.write_wave(x=x, y=y, val='p')
        else:
            self.write_wave(x=x, y=y, val='p')

        # Tous les points de la ligne courante deviendront '.'
        for i in range(x + 1, self.__wdb.colLen):
            self.write_wave(x=i, y=y, val='.')

        self.__lineChange.append(y)
        self.__update()

    def bus_mode(self, x, y, val='='):
        """
        Mode bus (signal multibit)
        :param x: Indice de colonne
        :param y: Indice de ligne
        :param val: Valeur à écrire
        :return: None
        """
        self.__wdb.record()

        if x == -1 or x > (self.get_col_len() - 1):
            return

        cur_val = self.read_wave(x=x, y=y)
        self.write_wave(x=x, y=y, val='.' if cur_val == val else val)

        self.__lineChange.append(y)
        self.__update()

    def x_mode(self, x, y):
        """
        Mode x (produit un état indéterminé)
        :param x: Indice de colonne
        :param y: Indice de ligne
        :return: None
        """
        self.__wdb.record()

        if x == -1 or x > (self.get_col_len() - 1):
            return

        # preVal = self.__forwardQuery(x=x, y=y, val='x')
        cur_val = self.read_wave(x=x, y=y)
        self.write_wave(x=x, y=y, val='.' if cur_val == 'x' else 'x')

        self.__lineChange.append(y)
        self.__update()

    def z_mode(self, x, y):
        """
        Mode z (résultant en un état à haute impédance)
        :param x: Indice de colonne
        :param y: Indice de ligne
        :return: None
        """
        self.__wdb.record()

        if x == -1 or x > (self.get_col_len() - 1):
            return

        # preVal = self.__forwardQuery(x=x, y=y, val='x')
        cur_val = self.read_wave(x=x, y=y)
        self.write_wave(x=x, y=y, val='.' if cur_val == 'z' else 'z')

        self.__lineChange.append(y)
        self.__update()

    def gap_mode(self, x, y):
        """
        Mode 'gap' (insérer |)
        :param x: Indice de ligne
        :param y: Indice de colonne
        :return: None
        """
        self.__wdb.record()

        if x == -1 or x > (self.get_col_len() - 1):
            return

        # preVal = self.__forwardQuery(x=x, y=y, val='|')
        cur_val = self.read_wave(x=x, y=y)
        self.write_wave(x=x, y=y, val='.' if cur_val == '|' else '|')

        self.__lineChange.append(y)
        self.__update()

    def t_mode(self, x, y, val, node_mode=None):
        """
        Mode texte
        :param x: Indice de colonne
        :param y: Indice de ligne
        :param val: Valeur à écrire
        :param node_mode: Mode node, la valeur d'écriture est le 'node'
        :return: None
        """
        self.__wdb.record()

        if x == -1:  # Modifier le nom
            self.write_name(y=y, val=val)
        elif node_mode:  # Editer node
            self.write_node(x=x, y=y, val=val)
        else:  # Modifier les données
            self.write_data(x=x, y=y, val=val)

        # Lorsque la longueur du nom du signal change de plus de 2, le contenu complet est restitué
        if abs(self.__wdb.nameLen - self.lastNameLen) > 0:
            self.__lineChange.append((0, self.__wdb.rowLen))
            self.lastNameLen = self.__wdb.nameLen
        else:
            self.__lineChange.append(y)
        self.__update()

    def add_row(self, num):
        """
        Ajoute une ligne en fin de ligne
        :param num: Augmente le nombre de lignes
        :return: None
        """
        self.__wdb.record()

        row_len = self.get_row_len()
        self.__wdb.insert_row(num=num)
        self.__lineChange.append((row_len, row_len + num))
        self.__update()

    def add_col(self, num):
        """
        Ajoute une colonne en fin de colonne
        :param num: Augmente le nombre de colonnes
        :return: None
        """
        self.__wdb.record()

        self.__wdb.insert_col(num=num)
        self.__render_dispatch(full_render=True)
        self.__update()

    def del_row(self, y):
        """
        Suppression de la ligne spécifiée
        :param y: Index de ligne
        :return: None
        """
        self.__wdb.record()
        if (self.get_row_len() > 1):
            self.__wdb.del_row(typ='signal', y=y)
            self.__render_dispatch(full_render=True)
        else:
            self.clear(y)
        self.__update()

    def del_col(self, x):
        """
        Suppression la colonne spécifiée
        :param x: Indince de colonne
        :return: None
        """
        self.__wdb.record()

        if (self.get_col_len() > 1):
            self.__wdb.del_col(typ='signal', x=x)
            self.__render_dispatch(full_render=True)
        else:
            self.clear(x)
        self.__update()

    def swap_line(self, src, dst):
        """
        Échange la ligne src avec la ligne dst
        :param src: source -> indice de ligne
        :param dst: destination -> indice de ligne
        :return: None
        """
        self.__wdb.record()
        self.__wdb.swap_line(typ='signal', src=src, dst=dst)
        self.__lineChange = range(min(src, dst), max(src, dst) + 1)
        self.__update()

    def copy_line(self, src, dst):
        """
        copier la ligne, copier le contenu de la ligne 'src' à l'emplacement 'dst'
        :param src: source -> Ligne
        :param dst: destination -> Ligne
        :return: None
        """
        self.__wdb.record()
        self.__wdb.swap_line(typ='signal', src=src, dst=dst, copy_mode=True)
        self.__render_dispatch(full_render=True)
        self.__update()

    def clear(self, y):
        """
        Effacement de toutes les données de la ligne spécifiée sans supprimer la ligne
        :param y: Indice de ligne
        :return: None
        """
        self.__wdb.record()

        # Rendu global lorsque le nom du signal de ligne clair est max name_len
        name_len = len(self.read_name(y))

        val = '.' * self.__wdb.colLen
        self.__wdb.write(typ='signal', k='name', y=y, val='')
        self.__wdb.write(typ='signal', k='data', y=y, val='')
        self.__wdb.write(typ='signal', k='node', y=y, val=val)
        self.__wdb.write(typ='signal', k='wave', y=y, val=val)

        if name_len > self.get_name_len():
            self.__render_dispatch(full_render=True)
        else:
            self.__lineChange.append(y)
        self.__update()

    def __update(self):
        """
        S'il y a une mise à jour de ligne, le moteur de rendu sera appelé pour rendre l'image
        :return:
        """
        if len(self.__lineChange) > 0:
            self.__render_dispatch()

    def save(self, handle):
        """
        Enregistrer fichier
        :param handle: Descripteur de fichier, le type de sauvegarde est déterminé en fonction du suffixe du descripteur
        :return: None
        """
        out = self.__wdb.read_all()
        fname = handle.name
        if fname.endswith('.png'):
            fname = fname.rstrip('.png')
            self.__render(dic=self.read_all(), fname=fname)
            os.remove(fname + '.svg')
        elif fname.endswith('.svg'):
            fname = fname.rstrip('.svg')
            self.__render(dic=self.read_all(), fname=fname)
            os.remove(fname + '.png')
        else:
            json.dump(out, handle)
        handle.close()

    def restore(self, filename):
        """
        Récupération de données
        :param filename: 存档文件位置
        :return: None
        """
        f = open(filename)
        db = json.load(f)
        self.init()
        self.__wdb.write_all(db)
        self.__render_dispatch(full_render=True)
        self.__update()

    def restore_json(self, json_db):
        """
        Rendre json db en tant que forme d'onde, appelée par l'éditeur, pour obtenir le rendu après l'édition de texte
        :param json_db: Forme d'onde 'dict'
        :return: None
        """
        self.init()
        self.__wdb.write_all(json_db)
        self.__render_dispatch(full_render=True)
        self.__update()

    def renderLine(self, lineList):
        """
        Affichage de la ligne spécifiée pour les appels externes
        :param lineList: list，Index de ligne à rendre
        :return: None
        """
        self.__lineChange = lineList
        self.__update()

    def __render(self, dic, fname):
        """
        Rendu, après que pywavedrom génère un fichier svg, utilisez cairosvg pour convertir en png
        :param dic: wavedrom dict
        :param fname: Génére le nom du fichier
        :return: None
        """
        svg = str(dic)
        try:
            wavedrom.render(svg).saveas(fname + ".svg")
        except:
            print("Catch exception: Veuillez lancer le rendu WaveNote.")
        # print(svg)
        # convert svg to png
        from_img = fname + ".svg"
        to_img = fname + '.png'
        cairosvg.svg2png(url=from_img, write_to=to_img)

    # Allocateur de rendu, données fractionnées, aucun contenu de mise à jour ne sera rendu
    # fullRender: Rendu global, rendu du début à la fin
    def __render_dispatch(self, full_render=False):
        """
        Allocation de rendu, rendu des images selon la liste __lineChange record data, prend en charge 3 modes :
            -   Rendu complet : rend tout le contenu de la ligne
            -   Rendu combiné : lorsque les lignes à rendre sont continues (le contenu de __lineChange est un tuple), les lignes à rendre seront rendues ensemble
            -   Rendu séparé : lorsque la ligne à rendre est une seule ligne (le contenu de __lineChange est int), une seule ligne sera rendue
        Une fois le rendu terminé, le résultat est enregistré dans self.imgDB
        :param full_render: bool，True -> en mode rendu complet
        :return: None
        """
        st = time.time()
        self.imgDB.clear()
        array = self.read_all()['signal']
        # Afin d'éviter que des noms de signaux de différentes longueurs n'affectent les résultats du rendu pendant le rendu, une ligne 'dummy' sera insérée au début de la ligne et la ligne 'dummy' sera supprimée après imgSplit
        dummy = {"name": ("Q" * self.__wdb.nameLen)}
        if full_render:  # Rendu complet
            db = self.read_all()
            wave = db['signal'].copy()  # Remappage
            wave.append(dummy)
            db['signal'] = wave

            fname = self.tmpDir + 'tmp0'
            self.__render(dic=db, fname=fname)  # Effectuer le rendu
            sub_img_list = self.__img_split(fname + '.png')  # Image fractionnée
            sub_img_list.pop(-1)  # supprimer la ligne 'dummy'
            for sub_idx in range(self.get_row_len()):
                self.imgDB[sub_idx] = sub_img_list.pop(0)
        else:
            for i in self.__lineChange:
                if type(i) == tuple:  # Rendu combiné
                    # i est un tuple lorsque plusieurs lignes sont fusionnées et rendues, telles que (1, 10) représentent respectivement la ligne de début et la ligne de fin
                    start_idx = i[0]
                    end_idx = i[1]
                    db = self.read_all()
                    db['signal'] = array[start_idx:end_idx] + [dummy]
                    fname = self.tmpDir + 'tmp%s' % start_idx

                    self.__render(dic=db, fname=fname)  # Effectuer le rendu
                    sub_img_list = self.__img_split(fname + '.png')  # Image fractionnée
                    sub_img_list.pop(-1)  # Supprimer la ligne 'dummy'
                    for sub_idx in range(start_idx, end_idx):
                        self.imgDB[sub_idx] = sub_img_list.pop(0)
                else:  # Rendu seul
                    # i est un nombre lors du rendu d'une seule ligne, tel que 1 représente la ligne de rendu actuelle
                    db = self.read_all()
                    db['signal'] = [array[i], dummy]
                    fname = self.tmpDir + 'tmp%s' % i
                    self.__render(dic=db, fname=fname)  # Effectuer le rendu
                    sub_img_list = self.__img_split(fname + '.png')  # Image fractionnée
                    sub_img_list.pop(-1)  # Supprimer la ligne 'dummy'
                    self.imgDB[i] = sub_img_list.pop(0)

        print('Ligne d\'opération', self.__lineChange, '; Temps de rendu %.2fs' % (time.time() - st))
        self.__lineChange = []

    def __img_split(self, fname):
        """
        Segmentation d'image, qui divise l'image rendue en une seule rangée d'images
        :param fname: Nom du fichier d'entrée
        :return: list
        """
        ret = []
        img = Image.open(fname)
        width, height = img.size
        for i in range(height // self.stepy):  # Fractionner les images en fonction de la hauteur de l'image et de la hauteur du step
            cropped = img.crop((0, i * self.stepy, width, (i + 1) * self.stepy))  # (left, upper, right, lower)
            ret.append(cropped.copy())
        return ret

    def undo(self):
        """
        Annulation
        :return: None
        """
        self.__wdb.undo()
        self.__render_dispatch(full_render=True)
        self.__update()

    def redo(self):
        """
        Rétablissement
        :return: None
        """
        self.__wdb.redo()
        self.__render_dispatch(full_render=True)
        self.__update()

    def get_history_len(self):
        """
        Obtenir la longueur de la liste d'annulation/rétablissement
        :return:tuple，(longueur de la liste 'undo', longueur de la liste de 'reundo')
        """
        return self.__wdb.undoLen, self.__wdb.redoLen

    def to_ascii(self):
        """
        Convertir la forme d'onde en caractères 'ascii'
        :return: str
        """
        wave = self.read_all()
        return WavedromASCII.from_dict(wave)


if __name__ == '__main__':
    wdc = WaveDromCtrl()
    ret = wdc.to_ascii()
