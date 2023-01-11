# coding=utf-8
import json


class WaveDromDB:
    def __init__(self):
        init_colum = 20

        # Pour l'accès externe aux variables
        self.rowLen = 0
        self.colLen = 0
        self.nameLen = 0
        self.undoLen = 0
        self.redoLen = 0

        # Variable privée
        self.special = ['=', '2', '3', '4', '5', '6', '7', '8', '9']  # Variable spéciale pour la description du bus
        self.__undo_list = []
        self.__redo_list = []
        self.history_depth = 5  # history buffer深度
        self.__db = {}  # Base de données principale
        # Contenu initial de la base de données
        self.__init_db = {
            'signal': [
                {
                    'name': 'clk',
                    'wave': 'p' + '.' * (init_colum - 1),
                    'node': '.' * init_colum,
                    'data': '',
                    'phase': 0,
                    'period': 1
                },
                {
                    'name': 'rstn',
                    'wave': '01' + '.' * (init_colum - 2),
                    'node': '.' * init_colum,
                    'data': '',
                    'phase': 0,
                    'period': 1
                },
                {
                    'name': 'signal',
                    'wave': '0' + '.' * (init_colum - 1),
                    'node': '.' * init_colum,
                    'data': '',
                    'phase': 0,
                    'period': 1
                },

            ],
            'edge': [],
            'config': {
                'hscale': 1,
                'skin': 'default'
            },
            # 'head': {
            #     'text': '',
            #     'tick': 0,
            #     'every': 1
            # },
        }

        # Initialisation
        self.init()

    def init(self):
        """
        Initialisation
        :return: None
        """
        self.write_all(self.__init_db)
        self.__update()

    def write(self, typ, val, k=None, y=None, x=None, insert_mode=False):
        """
        Initialisation et écriture des données, et convertion automatique des données virtuelles en données réelles lors de l'écriture sur 'wave'
        :param typ: Type de configuration : signal，edge，config
        :param val: Valeur à écrire
        :param k: key
        :param y: Numéro de ligne
        :param x: Numéro de colonne
        :param insert_mode: Insérer un élément à la position spécifiée, sinon, remplacer l'élément à cette position
        :return: None
        """
        if typ == 'signal':
            db = self.__db['signal'][y][k]
            if x is None:  # Ecrire toute la ligne sans x
                self.__db['signal'][y][k] = val
            else:  # Écrire un nombre précis lorsqu'il y a x
                if insert_mode:
                    self.__db['signal'][y][k] = db[:x] + val + db[x:]
                else:
                    self.__db['signal'][y][k] = db[:x] + val + db[x + 1:]

            if k == 'name':  # Lors de l'écriture d'un nom de signal, maj de la longueur du nom
                self.nameLen = max(len(i['name']) for i in self.__db['signal'])
            elif k == 'wave':  # Lors de l'écriture d'une forme d'onde, effectuez une conversion virtuelle -> physique
                self.__db['signal'][y][k] = self.__decode(y)
                # print(111, self.__db[typ][y][k])
        elif typ == 'edge':
            self.__db['edge'] = val
        elif typ == 'config':
            self.__db['config'][k] = val

    def read(self, typ, k=None, y=None, x=None, pop_mode=False):
        """
        Lecture des données
        :param typ: Type de configuration : signal，edge，config
        :param k: key
        :param y: Numéro de ligne
        :param x: Numéro de colonne
        :param pop_mode: Pop l'élément à la position spécifiée, sinon, l'élément à la position sera lu
        :return: str
        """
        if typ == 'signal':
            if k == 'wave':  # Lors de l'écriture d'une forme d'onde, effectuez une conversion physique -> virtuelle
                if pop_mode:
                    if x == 0:
                        self.__db['signal'][y][k] = self.__db['signal'][y][k][x + 1:]
                    else:
                        self.__db['signal'][y][k] = self.__db['signal'][y][k][:x - 1] + self.__db['signal'][y][k][x:]
                else:
                    virtual = self.__code(y)
                    return virtual if x is None else virtual[x]
            else:
                return self.__db['signal'][y][k] if x is None else self.__db['signal'][y][k][x]
        elif typ == 'edge':
            return self.__db['edge']
        elif typ == 'config':
            return self.__db['config'][k]

    def write_all(self, val):
        """
        Ecriture dans toute la base de données
        :param val: Dictionnaire de données
        :return: None
        """
        self.__db = val
        self.__update()

    def read_all(self):
        """
        Lecture de toute la base de données
        :return: dict
        """
        return self.__db.copy()

    def insert_row(self, num):
        """
        Insertion d'une ligne en fin de ligne
        :param num: Insérer le nombre de lignes
        :return:
        """
        new = {
            'name': 'signal',
            'wave': '0' + '.' * (self.colLen - 1),
            'node': '.' * self.colLen,
            'data': '',
            'phase': 0,
            'period': 1
        }
        for i in range(num):
            self.__db['signal'].append(new.copy())
        self.rowLen += num

    def insert_col(self, num):
        """
        Insertion d'une colonne en fin de colonne
        :param num: Insérer le nombre de colonnes
        :return: None
        """
        for i in range(self.rowLen):
            wave = self.__init_db['signal'][i]['wave']
            node = self.__init_db['signal'][i]['node']
            self.__init_db['signal'][i]['wave'] = wave + '.' * num
            self.__init_db['signal'][i]['node'] = node + '.' * num
        self.colLen += num
        self.__update()

    def swap_line(self, typ, src, dst, copy_mode=False):
        """
        Échange le contenu de la ligne src avec le contenu de la ligne dst
        :param typ: Type de données
        :param src: Index de ligne source
        :param dst: Index de la ligne de destination
        :param copy_mode: Copiera la ligne src sur la ligne dst et ajoutera 1 ligne supplémentaire
        :return: None
        """
        if copy_mode:
            tmp = self.__db[typ][src].copy()
        else:
            tmp = self.__db[typ].pop(src)
        self.__db[typ].insert(dst, tmp)
        self.__update()

    def del_row(self, typ, y):
        """
        Suppression de la ligne
        :param typ: Type de données
        :param y: Indice de ligne
        :return: None
        """
        result = self.__db[typ].pop(y)
        # Suppression de toutes les relations en rapport avec les nodes présentaient dans la ligne y
        for character in result['node']:
            if character != '.':
                if character in result['node']:
                    for relation in self.__db['edge']:
                        if character in relation:
                            index_relation = self.__db['edge'].index(relation)
                            self.__db['edge'].pop(index_relation)
        self.__update()

    def del_col(self, typ, x):
        """
        Suppression de la colonne
        :param typ:Type de données
        :param x: Indice de colonne
        :return: None
        """
        for i in range(self.rowLen):
            wave = self.__db[typ][i]['wave']
            node = self.__db[typ][i]['node']
            self.__db[typ][i]['wave'] = wave[:x] + wave[x + 1:]
            self.__db[typ][i]['node'] = node[:x] + node[x + 1:]
        self.__update()

    def __update(self):
        """
        Maj des variables de membre de classe
        :return:
        """
        self.rowLen = len(self.__db['signal'])
        self.colLen = len(self.__db['signal'][0]['wave'])
        self.nameLen = max(len(i['name']) for i in self.__db['signal'])

    def __code(self, y):
        """
        Convertir les données 'wave' du réel au virtuel, c'est-à-dire convertir "." en une valeur réelle
        Exemple : Réel -> Virtuel
            1..0..1 -> 1110001
        :param y: Indice de ligne
        :return: str
        """
        wave = self.__db['signal'][y]['wave']
        sign = '.'
        ret = ''
        for i in wave:
            if not i == '.':
                sign = i
            ret += i if sign in self.special else sign
        return ret

    def __decode(self, y):
        """
        Convertissement des données d'onde du virtuel au réel, c'est-à-dire convertir les valeurs répétées en '.'
        Exemple : virtuel -> réel
            1110011 -> 1.。0.1.
        :param y: Indice de ligne
        :return: str
        """
        wave = self.__code(y)
        sign = '.'
        ret = ''
        for i in wave:
            if sign in self.special and i in ['.'] + self.special:
                ret += i
            elif i == sign:
                ret += '.'
            else:
                sign = i
                ret += sign
        return ret

    def record(self):
        """
        Enregistrez la base de données actuelle dans le tampon d'historique pour implémenter la logique d'annulation
        """
        self.__redo_list.clear()  # Effacer la liste de rétablissement lors de l'enregistrement de l'étape précédente
        self.__undo_list.append(json.dumps(self.__db))
        while len(self.__undo_list) > self.history_depth:
            self.__undo_list.pop(0)
        # Mettre à jour le statut du membre, et s'il peut être annulé/rétabli peut être connu par la longueur
        self.undoLen = len(self.__undo_list)
        self.redoLen = len(self.__redo_list)

    def undo(self):
        """
        Annulation de l'opération, restauration de l'état précédent
        :return:
        """
        last = self.__undo_list.pop(-1)
        self.__redo_list.append(json.dumps(self.__db))
        json_db = json.loads(last)
        self.write_all(json_db)
        # Maj du statut du membre, et s'il peut être annulé/rétabli peut être connu par la longueur
        self.undoLen = len(self.__undo_list)
        self.redoLen = len(self.__redo_list)

    def redo(self):
        """
        Rétablir la dernière action
        :return: None
        """
        last = self.__redo_list.pop(-1)
        self.__undo_list.append(json.dumps(self.__db))
        json_db = json.loads(last)
        self.write_all(json_db)
        # Maj du statut du membre, et s'il peut être annulé/rétabli peut être connu par la longueur
        self.undoLen = len(self.__undo_list)
        self.redoLen = len(self.__redo_list)


if __name__ == '__main__':
    wdb = WaveDromDB()
    # print(wdb.colLen)

    # print(wdb.readAll())

    wdb.write(typ='signal', k='wave', y=0, val='xxxxxx=.=xxxxxxx')
    print(wdb.read_all())
