# -*- coding: utf-8 -*-

import re
from collections import OrderedDict

from nltk.stem.snowball import RussianStemmer


class TermSearch(object):

    # No process words
    STOP_WORDS = []

    EXCEPTIONS = []
    CASE_SENSITIVE = True

    # Inside this tags replace allowed
    ALLOWED_TAGS = ["h1", "h2", "h3", "h4", "p", "li"]

    def __init__(self, text, terms, exceptions=False, stop_words=False, hint_code=''):
        self.stop_indexes = tuple()
        self.allowed_indexes = tuple()
        self.text = text
        self.target_terms = self.sort_by_key_lenght(terms)
        self.hint_code = hint_code
        self.stop_pattern = self._get_stop_pattern()
        self.allowed_pattern = self._get_allowed_pattern()
        self.searched_terms = tuple()
        self.stemmer = RussianStemmer()

    # Order
    @staticmethod
    def sort_by_key_lenght(dct):
        return OrderedDict(sorted(dct.items(), key=lambda item: len(item[0]), reverse=True))

    @staticmethod
    def _get_stop_pattern():
        return u'<a.*?a>|<iframe.*?/iframe>|<img.*?>'

    def _get_allowed_pattern(self):
        item_pattern = u"<{0}>.*?</{0}>"
        return "|".join(item_pattern.format(tag) for tag in self.ALLOWED_TAGS)

    def prepare_text(self, text):
        return text.replace('\n', '').replace('\r', '')

    # Main method, generate allow and stop indexes, apply hints to text
    def process(self):
        self.allowed_indexes = self.search_by_pattern(self.allowed_pattern)
        self.stop_indexes = self.search_by_pattern(self.stop_pattern)
        target_patterns = self.get_patterns_list()

        if not self.allowed_indexes:
            return

        for pattern in target_patterns:
            print pattern
            self.search(pattern)

        return self.replace()

    def search_by_pattern(self, pattern):
        result = ()
        for m in re.finditer(pattern, self.text, flags=re.DOTALL | re.UNICODE):
            result += ((m.start(), m.end()),)
        return result

    # For improve perfomance
    def get_patterns_list(self):
        patterns = tuple()
        for term, other in self.target_terms.items():
            words = term.strip(" ").split(" ")
            words_cnt = len(words)
            if words_cnt > 1:
                patterns += ((self.get_stemmed_regex_pattern_extended(words), term, other[0], other[1],
                              self.CASE_SENSITIVE),)
            elif words_cnt == 1:
                if len(words[0]) < 3 or words[0].lower() in self.STOP_WORDS:
                    continue

                if words[0].lower() in self.EXCEPTIONS:
                    patterns += ((self.get_regex_pattern_strict(words[0]), term, other[0], other[1],
                                  not self.CASE_SENSITIVE),)
                    continue

                patterns += ((self.get_stemmed_regex_pattern_strict(words[0]), term, other[0], other[1],
                             self.CASE_SENSITIVE),)
        return patterns

    # Extened pattern for phrases (Russian language conditions)
    def get_stemmed_regex_pattern_extended(self, words):
        result = []
        for word in words:
            stemmed_word = self.stemmer.stem(word)
            delta = self.calculate_delta(word, stemmed_word)
            stemmed_word = word[:len(stemmed_word)]
            result.append(self.escaping(stemmed_word) + u'[А-ЯA-Z]{{0,{0}}}'.format(delta+2))
        item = " ".join(result)
        return self.general_pattern(item)

    def get_regex_pattern_strict(self, word):
        word = self.escaping(word)
        return self.general_pattern(word)

    @staticmethod
    def escaping(word):
        return word.replace("(", "\(").replace(")", "\)").replace("&", "&amp;").replace("+", "\+")

    def general_pattern(self, word):
        return u"(^|\s|>|\()({0})({1})".format(word, u"[\)\;\:\?\!\,\.\s]{1}")

    # Strict pattern with many conditions for Russian
    def get_stemmed_regex_pattern_strict(self, word):
        if len(word) >= 4:
            delta = True

            stemmed_word = self.stemmer.stem(word)
            if (len(word) - len(stemmed_word)) == 0:
                delta = False

            if re.match(u"([а-я]{{{0}}})".format(len(word)), word.lower()):
                if delta:
                    word = self.escaping(word[:-1]) + u"[а-я]{0,1}(ами|ы|ов|и|а|ом|ой|ий|ями|ей){0,1}"
                else:
                    word = self.escaping(word) + u"(ами|ы|ов|и|а|ом|ой|ий|ями|ей){0,1}"
            else:
                word = self.escaping(word[:-1]) + u"[А-ЯA-Z]{{1,{0}}}".format(4)
        return self.general_pattern(word)

    @staticmethod
    def calculate_delta(word, stemmed_word):
        delta = len(word) - len(stemmed_word)
        delta = 0 if delta <= 1 else delta
        return delta + 2

    # Create tuple for term with index, finded term, basic-term-form and hint text
    def search(self, pattern):
        flags = re.IGNORECASE | re.UNICODE if pattern[4] else re.UNICODE
        searched = ()
        previous_index = 0
        for searched_item in re.finditer(pattern[0], self.text, flags=flags | re.DOTALL):
            # Checking stop index and also finded indexes
            is_index = self.check_number_range(self.searched_terms, searched_item) \
                        and self.check_number_range(self.stop_indexes, searched_item)

            print "Is_index", is_index

            # Pass terms in first 150 symbols and pass terms with distance between < 150
            if is_index and (searched_item.start(2) - previous_index > 150):
                    previous_index = searched_item.start(2)

                    searched += ((searched_item.start(2), searched_item.end(2),
                                  searched_item.group(2), pattern[1], pattern[2], pattern[3]),)

        if searched:
            ln = len(searched)
            if ln > 3:
                # Remove words that repeat more than 3 times. Need only first, middle, last word
                filtered_search = (searched[0],) + (searched[-1],) + (searched[int(ln/(ln/2))],)
                searched = filtered_search

            self.searched_terms += searched

    def check_number_range(self, indexes, element):
        index = True
        for number_range in indexes:
            if (number_range[0] <= element.start(2) <= number_range[1]) and (
                        number_range[0] <= element.end(2) <= number_range[1]):
                index = False
                break

        return index

    def replace(self):
        searched_terms = (sorted(self.searched_terms, key=lambda x: x[0], reverse=True))
        for item in searched_terms:
            replacer = self.hint_code.format(item[5], item[4], item[2])

            self.text = self.text[:item[0]] + replacer + self.text[item[1]:]
        return self.text

