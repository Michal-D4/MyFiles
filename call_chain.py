import sys
import socket
import os
import re

from PyQt5.QtWidgets import QApplication, QTreeView, QAbstractItemView
from PyQt5.QtCore import Qt, QModelIndex, QItemSelectionRange, QAbstractItemModel

from controller.table_model import TableModel
from controller.tree_model import TreeItem, TreeModel

sys._excepthook = sys.excepthook


def my_exception_hook(exctype, value, traceback):
    # Print the error and traceback
    print(exctype, value, traceback)
    # Call the normal Exception hook after
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)

sys.excepthook = my_exception_hook


class TreeModelChainUp(TreeModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.rootItem = TreeItem(data_=("",))
        self.leaves = []

    def chain_up(self, index: QModelIndex):
        chain = []
        while index.isValid():
            idx = index.parent()
            idx0 = self.index(index.row(), 0, idx)
            idx1 = self.index(index.row(), 1, idx)
            if idx0.isValid():
                method_ = self.data(idx0, role=Qt.DisplayRole)
                class_ = self.data(idx1, role=Qt.DisplayRole)
                chain.append('.'.join((class_, method_)))
            index = idx
        # chain.reverse()
        return chain, len(chain)

    def print_all_chains(self):
        print('All chains, leaves first', len(self.leaves))
        max_len = 0
        chains = []
        for leaf in self.leaves:
            chain, len_ = self.chain_up(leaf)
            max_len = max(len_, max_len)
            chains.append(chain)

        print('    max length of chain:', max_len)

        chains2 = []
        for chain in sorted(chains, key=lambda x: ''.join(x)):
            print(chain)
            chain.reverse()
            chains2.append(chain)

        print(' <-------------->')
        aux = set()
        this_max = []
        max_chains = []

        for chain in sorted(chains2, key=lambda x: ''.join(x)):
            if not aux.issubset(set(chain)):
                max_chains.append(this_max)
            this_max = chain
            aux = set(chain)
        max_chains.append(this_max)

        print('All chains, heads first', len(max_chains))
        for chain in sorted(max_chains, key=lambda x: ''.join(x)):
            print(chain)

    def set_model_data(self, rows):
        """
        it is called from __init__ of base class
        :param rows:
        :return:
        """
        id_list = []
        items_list = {0: self.rootItem}
        for row in rows:
            if not isinstance(row[0], tuple):
                row = ((row[0],),) + tuple(row[1:])
            items_list[row[1]] = TreeItem(data_=row[0], user_data=(row[1:]))
            id_list.append((row[1:3]))

        for id_ in id_list:
            if id_[1] in items_list:
                ite = items_list[id_[0]]
                items_list[id_[1]].appendChild(ite)

        for ite in items_list.values():
            if ite.parent():        # it's essential
                idx = self.createIndex(ite.row(), 0, ite)
                self.leaves.append(idx)


class MethodsTree():
    ADD, CLASS, METHOD, SKIP = range(4)

    def __init__(self, file_name):
        self.view = QTreeView()
        self.file_name = file_name
        self.view.setWindowTitle(file_name.rpartition(os.sep)[2])

        self.row_id = 0
        self.called_by = None
        self.methods = None

        model = TreeModelChainUp()
        headers = 'Method,Class,Called by'.split(',')
        model.setHeaderData(0, Qt.Horizontal, headers)
        self.view.setModel(model)

        method_body = self.extract_from_module()
        data = self.method_caller(method_body)
        self.update_model(data)

        self.view.setContentsMargins(5, 5, 5, 5)

        print(file_name)
        model.print_all_chains()

        self.view.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.view.resizeEvent = self.resize_event
        # self.view.mousePressEvent = self.my_mouse_press_event     # only as example of usage - not used here
        self.view.resize(550, 340)
        self.view.setAlternatingRowColors(True)

        self.view.show()

        self.view.selectionModel().selectionChanged.connect(self.sel_changed)

    def _expanded(self, index):
        print('--> _expanded')

    def _collapsed(self, index):
        print('--> _collapsed')

    def mouse_press_event(self, event):
        print('--> mouse_press_event', self.view.underMouse())
        event.ignore()
        return super(QTreeView, self.view).mouseMoveEvent(event)

    def sel_changed(self, sel1: QItemSelectionRange):   # , sel2: QItemSelectionRange): -2d parameter, not used
        if sel1.indexes():
            print(self.view.model().chain_up(sel1.indexes()[0]))

    # def my_mouse_press_event(self, event):
    #     print('|--> my_mouse_press_event')
    #     QTreeView.mousePressEvent(self.view, event)

    def resize_event(self, event):
        w = event.size().width()
        self.view.setColumnWidth(0, int(w/2))

    @staticmethod
    def parse_line(line):
        line = line.strip()
        qq = re.match(r'\bdef |\bclass |#|"""|if __name__', line)
        if qq:
            rr = MethodsTree._check_patterns(line, qq)
        else:
            rr = MethodsTree._check_for_skipping(line)
        return rr

    @staticmethod
    def _check_for_skipping(line):
        """
        skip lines that
        1) connect method to event
        2) continuation of doc-lines
        3) comments
        4) remove string literals
        :param line:
        :return: (action: ADD or SKIP, <line or its part> or <skipping type>)
        """
        ss = re.search(r'#|\'|"{3}|"|\bconnect\b|\bsuper\(', line)  # order of "{3} and " is important
        if ss:
            if ss.group() == '#':
                rr = [MethodsTree.ADD, line[:ss.start()]]
            elif (ss.group() == 'connect') | (ss.group() == 'super('):
                rr = [MethodsTree.SKIP, '']
            elif ss.group() == '"""':
                rr = [MethodsTree.SKIP, '"""']
            else:
                s1 = ss.end()
                pp = line[:s1]
                tt = line[s1:]
                found = False
                off = -1
                while True:
                    try:
                        off = tt.index(ss.group(), 1)
                    except ValueError:
                        break
                    if found:
                        pp = ''.join((pp, tt[:off + 1]))
                    found = not found
                    tt = tt[off:]

                pp = ''.join((pp, tt))
                rr = [MethodsTree.ADD, pp]
        else:
            rr = {MethodsTree.ADD, line}
        return rr

    @staticmethod
    def _check_patterns(line, re_match):
        """
        check for starting class, method, doc-lines, line-comment
        :param line:
        :param re_match:
        :return: (action, <method> or <class> or <skipping type>)
        """
        if re_match.group() == 'def ':
            rr = [MethodsTree.METHOD, line[4:].partition('(')[0]]
        elif re_match.group() == 'if __name__':
            rr = [MethodsTree.METHOD, '__main__']
        elif re_match.group() == 'class ':
            pp = re.split(':|\(', line[6:], maxsplit=1)
            rr = [MethodsTree.CLASS, pp[0]]
        elif re_match.group() == '#':
            rr = [MethodsTree.SKIP, '']
        elif re_match.group() == '"""':
            pp = re.search('"""', line[re_match.end():])  # if closing """ in the same line
            if pp:
                rr = [MethodsTree.SKIP, '']
            else:
                rr = [MethodsTree.SKIP, '"""']
        else:
            print('<<< something wrong >>>')
            print(line)
        return rr

    def create_tree(self, dat_, data, lev_0):
        ii = 0
        while True:
            bb = []
            for cc in lev_0:
                off = -1
                while True:
                    try:
                        off = self.called_by.index(cc[0], off + 1)  # index of cc[0] as a caller
                    except ValueError:
                        break

                    if cc[2] == data[off][3]:
                        self.row_id += 1
                        dat_.append((tuple(data[off]), self.row_id, cc[1]))
                        bb.append((self.methods[off], self.row_id, data[off][1]))

            if not bb: break
            lev_0 = bb
            ii += 1
            if ii > 15: break

    def extract_from_module(self):
        """
        extract body of each method to find the methods called from it
        :return:
        """
        text = []
        with open(self.file_name, 'r') as a_file:
            cur_class = ''
            cur_method = ''
            skip = ''
            for line in a_file:
                # if method is outside of any class
                if re.match('def', line):
                    cur_class = ''

                # search for "def", "class" extract method-class name
                # and join next lines until next def
                act, item = self.parse_line(line)
                if skip == '"""':
                    if act == MethodsTree.SKIP and item == '"""':
                        skip = ''
                else:
                    if act == MethodsTree.ADD and cur_method:
                        text[-1][2].append(item)
                    elif act == MethodsTree.CLASS:
                        cur_class = item
                    elif act == MethodsTree.METHOD:
                        cur_method = item
                        if cur_method == '__main__':
                            cur_class = ''
                        # elif cur_method == '__init__':
                        #     cur_method = cur_class
                        text.append([cur_method, cur_class, []])
                    elif act == MethodsTree.SKIP:
                        skip = item

        return text

    def method_caller(self, text):
        methods = []
        for item in text:
            item[2] = ' '.join(item[2])
            methods.append((item[0], item[1]))

        data = []
        for met in methods:
            grp3, pat = self._set_re_pattern(met)
            # print('--> met {}, grp3 {}, pat {}'.format(met, grp3, pat))
            found = False
            for item in text:
                # print('    ', item[:2])
                # recursion not allowed, method name not searched in its body
                if (item[0] != met[0]) | (item[1] != met[1]):
                    ss = re.search(pat, item[2])
                    if ss:
                        # print('   group: {}'.format(ss.group()))
                        if ss.group() == grp3:
                            if (met[1] == '') | (met[1] != item[1]):
                                data.append((met[0], met[1], item[0], item[1]))
                                found = True
                        else:
                            if (met[1] == item[1]) | (item[1] == ''):
                                data.append((met[0], met[1], item[0], item[1]))
                                found = True
            if not found:
                data.append((met[0], met[1], '***', 'Unknown'))

        return sorted(data, key=lambda x: x[0])

    def _set_re_pattern(self, met):
        rb = r'\b'
        rs = r'\('
        grp3 = ''.join((met[0], '('))
        if met[1]:
            if met[0] == '__init__':
                pat = ''.join((rb, met[1], rs))  # <class>(
                grp3 = ''.join((met[1], '('))
            else:
                pat1 = ''.join((rb, met[1], '.', met[0], rb))  # <class>.<method>
                pat2 = ''.join((rb, '.', met[0], rb))  # .<method>
                pat3 = ''.join((rb, met[0], rs))  # <method>(
                pat = '|'.join((pat1, pat2, pat3))
        else:  # method is outside of any class
            pat = ''.join((rb, met[0], rs))  # <method>(

        return grp3, pat

    def _cur_row_changed(self, curr_idx):
        print('--> _cur_row_changed', curr_idx.row())

    def update_model(self, data):
        self.methods = [x[0] for x in data]
        self.called_by = [x[2] for x in data]
        level_0 = []
        dat_ = []
        for i in range(len(self.called_by)):
            if self.called_by[i] not in self.methods:  # external calling methods
                self.row_id += 1
                dat_.append((tuple(data[i]), self.row_id, 0))
                level_0.append((self.methods[i], self.row_id, data[i][1]))

        self.create_tree(dat_, data, level_0)

        data = sorted(dat_, key=lambda x: x[2], reverse=True)

        self.view.model().set_model_data(data)
        self.view.selectionModel().currentRowChanged.connect(self._cur_row_changed)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    dir_h = r'/home/michal/myWork/py/wfiles/MyFiles'    # Home
    dir_w = r'D:\Users\PycharmProjects\MyFiles'   # Work

    # todo if there are methods with the same name in different class
    file_ = 'controller/my_controller.py'
    # file_ = 'controller/places.py'
    # file_ = 'controller/table_model.py'
    # file_ = 'controller/tree_model.py'
    # file_ = 'model/file_info.py'
    # file_ = 'model/utilities.py'
    # file_ = 'model/utils/create_db.py'
    # file_ = 'model/utils/load_db_data.py'
    # file_ = 'view/input_date.py'
    # file_ = 'view/item_edit.py'
    # file_ = 'view/main_window.py'
    # file_ = 'view/db_choice.py'
    # file_ = 'view/sel_opt.py'
    # file_ = 'view/set_fields.py'
    # file_ = 'call_chain.py'
    # file_ = 'TreeModel.ed.py'
    # file_ = 'TreeItem.ed.py'
    # file_ = 'TreeModel.py'
    # file_ = 'TreeItem.py'
    # file_ = 'tmp.py'

    dir_ = dir_h if socket.gethostname() == 'michal-pc' else dir_w
    full_file_name = os.path.join(dir_, file_)

    # infinite loop
    # full_file_name = r'd:\Users\mihal\PycharmProjects\Examples\AbsrtactModel\editable\editabletreemodel.py'

    mt = MethodsTree(full_file_name)


    sys.exit(app.exec_())

