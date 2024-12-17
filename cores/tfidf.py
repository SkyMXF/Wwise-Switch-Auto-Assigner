import math

from log import LOGGER


class SentenceIndex(object):

    def __init__(self):
        self.sentence_dict: dict[any, list[str]] = {}

        # word freq of every word
        self.word_freq_dict: dict[str, int] = {}

        # doc freq of every word
        self.doc_freq_dict: dict[str, int] = {}

        # tf-idf of every word
        self.tf_idf_dict: dict[str, float] = {}

    # add a sentence to the index
    def add_sentence(self, key, sentence: list[str]):
        if key in self.sentence_dict:
            LOGGER.error(f"Key {key} already exists in the index.")

        self.sentence_dict[key] = sentence

        word_set = set(sentence)
        for word in sentence:
            if word not in self.word_freq_dict:
                self.word_freq_dict[word] = 0
            self.word_freq_dict[word] += 1

        for word in word_set:
            if word not in self.doc_freq_dict:
                self.doc_freq_dict[word] = 0
            self.doc_freq_dict[word] += 1

    # calculate tf-idf of every word after all sentences are added
    def generate_index(self) -> None:
        for word, freq in self.word_freq_dict.items():
            self.tf_idf_dict[word] = freq * math.log(len(self.sentence_dict) / self.doc_freq_dict[word])

    # calculate similarity of a query sentence and sentence with given key
    def get_similarity(self, query_sentence: list[str], key: any) -> float:
        similarity: float = 0.0
        value_sentence = self.sentence_dict.get(key, [])

        word_intersection = set(query_sentence) & set(value_sentence)

        for word in word_intersection:
            similarity += self.tf_idf_dict.get(word, 0)

        return similarity
