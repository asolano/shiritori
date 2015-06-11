#!/usr/bin/env python
# encoding: utf-8

import sys
if sys.version_info.major < 3:
    print('This script requires Python3. Exiting...')
    sys.exit(0)
import random
import collections
import itertools
import unicodedata


def is_hiragana(text):
    # See https://en.wikipedia.org/wiki/Hiragana_(Unicode_block)
    min_code = unicodedata.lookup('HIRAGANA LETTER SMALL A')
    max_code = unicodedata.lookup('HIRAGANA DIGRAPH YORI')
    return all(c >= min_code and c <= max_code for c in text)


def is_katakana(text):
    # See https://en.wikipedia.org/wiki/Katakana_(Unicode_block)
    min_code = unicodedata.lookup('KATAKANA-HIRAGANA DOUBLE HYPHEN')
    max_code = unicodedata.lookup('KATAKANA DIGRAPH KOTO')
    return all(c >= min_code and c <= max_code for c in text)


def katakana_to_hiragana(text):
    # Only a to n, other symbols are not changed
    h_sa = unicodedata.lookup('HIRAGANA LETTER SMALL A')
    k_sa = unicodedata.lookup('KATAKANA LETTER SMALL A')
    k_n = unicodedata.lookup('KATAKANA LETTER N')
    return ''.join(chr(ord(h_sa) + ord(c) - ord(k_sa))
                   if is_katakana(c) and ord(c) <= ord(k_n)
                   else c for c in text)


GameWord = collections.namedtuple('GameWord', 'kanji kana rank is_noun')


class InvalidWordException(Exception):
    pass


class UnknownWordException(Exception):
    pass


class Game:
    small_to_big = {
        ord('ゃ'): 'や',
        ord('ゅ'): 'ゆ',
        ord('ょ'): 'よ',
        }

    def __init__(self, words, max_rank=None):
        # TODO type checking?
        if len(words) == 0:
            raise RuntimeError('Some words are required to make a game.')
        self.words = words
        if max_rank is None:
            word = max(words, key=lambda x: x.rank)
            max_rank = word.rank
        # FIXME homophones? currently last one 'wins'
        self.known_words = {katakana_to_hiragana(w.kana): w for w in words
                            if w.rank <= max_rank}
        self.seen_words = []
        self.player_score = 0
        # Pick initial word
        # TODO combine with code in next_word?
        while True:
            key = random.choice(list(self.known_words.keys()))
            first = self.known_words[key]
            if first.is_noun and first.kana[-1] != 'ん':
                break
        self._update_seen(first)

    def _update_seen(self, word):
        self.seen_words.append(word)

    def _validate(self, text):
        # Must start with the last mora
        mora = self.seen_words[-1].kana[-1]
        mora = mora.translate(self.small_to_big)
        if text[0] != mora:
            message = 'だめ！ 「{}」の最初の音が「{}」じゃないでしょ'
            raise InvalidWordException(message.format(text, mora))
        # Must be known
        if text not in self.known_words:
            message = 'すみません、「{}」って知りませんけど'
            raise UnknownWordException(message.format(text))
        word = self.known_words[text]
        # Must not have been already seen
        if word in self.seen_words:
            message = 'はは！「{}」はもう出ました!'
            raise InvalidWordException(message.format(text))
        # Must be a noun
        if not word.is_noun:
            message = '残念! 「{}／{}」は名詞じゃありませんね'
            raise InvalidWordException(message.format(text, word.kanji))
        # Must not end with the character n
        if text.endswith('ん'):
            message = '「{}」無理でしょう、「ん」で終わりますから'
            raise InvalidWordException(message.format(text))

    def next_word(self):
        # First call only
        if len(self.seen_words) == 1:
            return self.seen_words[0]
        mora = self.seen_words[-1].kana[-1]
        mora = mora.translate(self.small_to_big)
        gen = (word for word in self.known_words.values() if
               word.kana.startswith(mora) and
               word not in self.seen_words and
               word.is_noun and
               not word.kana.endswith('ん'))
        candidates = list(itertools.islice(gen, 10))
        if candidates:
            new_word = random.choice(candidates)
            self._update_seen(new_word)
            return new_word
        else:
            raise InvalidWordException('あれ？参りましたみたい！')

    def send_word(self, text):
        # Normalize katakana
        text = katakana_to_hiragana(text)
        self._validate(text)
        word = self.known_words[text]
        self.player_score += 1
        self._update_seen(word)
        return word


def main():
    from get_data import get_data

    words = get_data()
    game = Game(words, max_rank=None)

    print('しりとり')
    print('1）ひらがなやカタカナで書いてください')
    print('2）quitを入れたら止めます')
    print('-' * 10)

    # First draw
    word = game.next_word()
    print('最初は。。 {} （{}）'.format(word.kana, word.kanji))
    while True:
        try:
            # Get answer/command from player
            answer = input('答えは？ ')
            answer = answer.strip().replace(' ', '')
            if not answer:
                print('何かを入力をしてください')
                continue
            if answer == 'quit':
                break
            # Check word
            old_word = game.send_word(answer)
            # Get new word from game
            word = game.next_word()
            print('{} （{}）ですか？じゃ。。 {} （{}）'.format(old_word.kana,
                  old_word.kanji, word.kana, word.kanji))

        except UnknownWordException as e:
            print('{} （{}）'.format(e, word.kana))
            continue

        except InvalidWordException as e:
            print('{}'.format(e))
            break

    # Show score and the word chain
    print('-' * 10)
    print('遊んでくれてありがとうございました')
    print('1）スコアは {} になります'.format(game.player_score))
    print('2) 言葉： {}'.format(' -> '.join(w.kana for w in game.seen_words)))


if __name__ == '__main__':
    main()
