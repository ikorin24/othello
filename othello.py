#! /usr/bin/env python
# -*- encoding: utf8 -*-
import re
from argparse import ArgumentParser
import random


class Othello:

    def __init__(self):
        self.debug_auto = False
        self.EMPTY = 0
        self.WHITE = 1
        self.BLACK = 2
        self.dumped_str = {
            self.EMPTY: ' _',
            self.BLACK: ' x',
            self.WHITE: ' o'
        }
        self.cell_input_pattern = re.compile(r'[0-7],[0-7]')
        self.cells = None
        self.availables = None
        self.is_running = False
        self.next = None
        self.prev = None
        pass

    def _set_start(self):
        """
        ゲーム開始の配置に石をセット
        :return: None
        """
        self.cells = [[0 for _ in range(8)] for _ in range(8)]
        self.cells[3][4] = self.WHITE
        self.cells[4][3] = self.WHITE
        self.cells[4][4] = self.BLACK
        self.cells[3][3] = self.BLACK
        self.next = self.BLACK
        self.prev = self.WHITE
        self.availables = [[None for _ in __] for __ in self.cells]     # 置ける場所
        self._set_availables()                                          # 置ける場所を計算

    def _flatten(self, iterable):
        """
        ２重リストの平面化
        :param iterable: 2中リスト
        :return: 平面化したリスト
        """
        x = []
        for item in iterable:
            x.extend(item)
        return x

    def _another(self, player):
        if player is not self.WHITE and player is not self.BLACK:
            raise Exception()
        elif player is self.BLACK:
            return self.WHITE
        else:
            return self.BLACK

    def _can_put_at(self, row, col, player):
        """
        指定位置に指定の色の石を置けるかどうかを確認します
        :param row: 石を置く行
        :param col: 石を置く列
        :player: 置く石の色
        :return: (boolean, list) ;  boolean 石を置けるか, list ひっくり返る場所
        """

        def validate_index(r, c):
            return all([r >= 0,
                        r < len(self.cells),
                        c >= 0,
                        c < len(self.cells[0])])

        def check_next_cell(current_row, current_col, update_row, update_col):
            """
            石が置けるかを，ある方向へ再帰的にチェック
            :param current_row: 今の場所のrow
            :param current_col: 今の場所のcol
            :param update_row: 次のrowへの更新関数
            :param update_col: 次のcolへの更新関数
            :return: (boolean, list) ;  boolean 石を置けるか, list ひっくり返る場所
            """
            # 石を置く場所の1マス先(隣)が空マスor自石or盤外なら石は置けない
            reverse = []                                            # ひっくり返る場所格納用
            current_row = update_row(current_row)
            current_col = update_col(current_col)
            if validate_index(current_row, current_col) is False:
                return False, []                                    # 調べる場所が盤外ならFalse
            if self.cells[current_row][current_col] is self.EMPTY or \
               self.cells[current_row][current_col] is player:
                return False, []                                    # 調べる場所が空マスor自石ならFalse
            # 盤外or自石or空マスにつくまで1マス進み，盤外ならFalse, 自石ならTrue
            while self.cells[current_row][current_col] is self._another(player):
                reverse.append({'row': current_row, 'col': current_col})
                current_row = update_row(current_row)
                current_col = update_col(current_col)
                if validate_index(current_row, current_col) is False:
                    return False, []                                # 調べる場所が盤外ならFalse
            if self.cells[current_row][current_col] is player:
                return True, reverse                                # 自石ならTrue, 置いた位置との間のマスがひっくり返る場所
            else:
                return False, []                                    # 空マスならFalse

        # 石が置いてあるマスなら置けない
        if self.cells[row][col] is not self.EMPTY:
            return False, []
        # 8方向について，置けるかどうか走査する
        result = (
            check_next_cell(row, col, lambda y: y-1, lambda x: x),
            check_next_cell(row, col, lambda y: y-1, lambda x: x+1),
            check_next_cell(row, col, lambda y: y,   lambda x: x+1),
            check_next_cell(row, col, lambda y: y+1, lambda x: x+1),
            check_next_cell(row, col, lambda y: y+1, lambda x: x),
            check_next_cell(row, col, lambda y: y+1, lambda x: x-1),
            check_next_cell(row, col, lambda y: y,   lambda x: x-1),
            check_next_cell(row, col, lambda y: y-1, lambda x: x-1),
        )
        can_put = any(map(lambda x: x[0], result))              # 置けるかどうか
        reverse_list = self._flatten(map(lambda x: x[1], result))     # 置いたときにひっくり返る場所
        return can_put, reverse_list

    def _dump(self):
        """
        現在の全マスとゲームの状態を出力
        :return: None
        """
        print('   | 0 1 2 3 4 5 6 7')
        print('---|----------------')
        for i, line in enumerate(self.cells):
            print('{:3}|'.format(i), end='')
            for cell in line:
                print(self.dumped_str[cell], end='')
            print('')
        info = '                                          \n' \
               'Next:{next}                               \n' \
               '                                          \n' \
               .format(next=self.dumped_str[self.next])
        print(info, end='')

    def _print_help(self):
        """
        ゲームコマンドのヘルプを出力
        :return: None
        """
        help_msg = '# ----------------------------------------\n' \
                   '#  h:                                     \n' \
                   '#    Show this help                       \n' \
                   '#  q:                                     \n' \
                   '#    Quit the game                        \n' \
                   '#  s:                                     \n' \
                   '#    Show the board                       \n' \
                   '#  [row],[col]                            \n' \
                   '#    Put a stone at (row, col)            \n' \
                   '# ----------------------------------------\n'
        print(help_msg)

    def _set_availables(self):
        """
        現在の盤で置ける場所を更新
        :return: None
        """
        for row, row_line in enumerate(self.cells):
            for col, cell in enumerate(row_line):
                self.availables[row][col] = self._can_put_at(row, col, self.next)   # 置ける場所を取得

    def _parse_command(self):
        """
        ゲームコマンドを受け付け，コマンドに応じて処理を実行
        :return: boolean ゲーム継続
        """

        # ------------ for debug mode ----------------
        if self.debug_auto:
            # ここデバッグ用ね 可読性？ 知らん 自分でも読めん
            # 全自動で石を置く
            lst = [z for z in filter(lambda x: x[1][0], enumerate(self._flatten(self.availables)))]
            n, avai = lst[random.randint(0, len(lst)-1)]
            r = n//len(self.cells)
            c = n%len(self.cells[0])
            self.cells[r][c] = self.next  # 石を置く
            for rev in avai[1]:
                self.cells[rev['row']][rev['col']] = self.next  # ひっくり返す
            self.next, self.prev = self.prev, self.next  # プレイヤー交代
            self._set_availables()
            self._dump()  # 盤出力
            return True
        # ------------ for debug mode ----------------

        line = input('Input command: ')
        if line is 'q':                     # ゲーム終了
            return False
        elif line is 'h':                   # ヘルプ表示
            self._print_help()
            return True
        elif line is 's':                   # 盤表示
            self._dump()
            return True
        match = self.cell_input_pattern.match(line)
        if match is not None \
           and line is line[match.start():match.end()]:     # 置きマス入力
            pos = line.split(',')
            row = int(pos[0])
            col = int(pos[1])
            can_put, reverse_list = self.availables[row][col]
            if can_put:
                self.cells[row][col] = self.next                    # 石を置く
                for rev in reverse_list:
                    self.cells[rev['row']][rev['col']] = self.next  # ひっくり返す
                self.next, self.prev = self.prev, self.next         # プレイヤー交代
                self._set_availables()
                self._dump()                                        # 盤出力
            else:
                print('Can not put at ({row}, {col})'.format(row=row, col=col))
            return True
        else:                                                       # 未定義コマンドならエラーメッセージ
            msg = 'Invalid command.         \n' \
                  'To show help, input "h"  \n'
            print(msg)
        return True                                                 # ゲーム継続

    def _is_game_end(self):
        return all(i for i in map(lambda x: x[0] is False, self._flatten(self.availables)))

    def _end(self):
        flatten = self._flatten(self.cells)
        black_count = flatten.count(self.BLACK)
        white_count = flatten.count(self.WHITE)
        if black_count < white_count:
            winner = self.dumped_str[self.WHITE]
        elif black_count > white_count:
            winner = self.dumped_str[self.BLACK]
        else:
            winner = 'draw'
        game_result = '#--------------------------------- \n' \
                      '# RESULT                           \n' \
                      '#--------------------------------- \n' \
                      '# {b_str} : {b_count}              \n' \
                      '# {w_str} : {w_count}              \n' \
                      '#                                  \n' \
                      '#  winner : {winner}               \n' \
                      '#--------------------------------- \n' \
            .format(b_str=self.dumped_str[self.BLACK],
                    b_count=black_count,
                    w_str=self.dumped_str[self.WHITE],
                    w_count=white_count,
                    winner=winner)
        print(game_result, end='')

    def start(self):
        if self.is_running:
            raise Exception('Othello is already running')
        self.is_running = True
        self._set_start()
        self._print_help()
        self._dump()
        while self._parse_command():
            if self._is_game_end():
                self._end()
                break
        self.is_running = False
        print('Thank you for playing ')


def arg_parse():
    parser = ArgumentParser(usage='Usage: {0} [option]'.format(__file__),
                            description="Othello on the terminal",
                            add_help=True)
    parser.add_argument('-v', '--version', action='version', version='0.0.1')
    parser.add_argument('--debug-auto', action='store_true', default=False, required=False, help='debug auto')
    return parser.parse_args()


if __name__ == '__main__':
    args = arg_parse()
    othello = Othello()
    othello.debug_auto = args.debug_auto
    othello.start()
