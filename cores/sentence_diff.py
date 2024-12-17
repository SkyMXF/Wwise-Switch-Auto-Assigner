class WordFreqCounter(object):

    def __init__(self):
        self.word_freq_dict: dict[str, int] = {}

    def add_words(self, words: list[str] | str) -> None:
        if isinstance(words, str):
            words = [words]

        for word in words:
            if word not in self.word_freq_dict:
                self.word_freq_dict[word] = 0
            self.word_freq_dict[word] += 1


# create a mapping dict of word -> sign
class WordDict(object):

    LOWER_CASE_LETTER_SIGN_LIST = [f"{chr(i)}" for i in range(ord("a"), ord("z") + 1)]
    UPPER_CASE_LETTER_SIGN_LIST = [f"{chr(i)}" for i in range(ord("A"), ord("Z") + 1)]
    DIGIT_SIGN_LIST = [f"{i}" for i in range(10)]
    SPECIAL_SIGN_LIST_A = [f"{chr(i)}" for i in range(ord("!"), ord("/") + 1)]
    SPECIAL_SIGN_LIST_B = [f"{chr(i)}" for i in range(ord(":"), ord("@") + 1)]
    SPECIAL_SIGN_LIST_C = [f"{chr(i)}" for i in range(ord("["), ord("`") + 1)]
    SPECIAL_SIGN_LIST_D = [f"{chr(i)}" for i in range(ord("{"), ord("~") + 1)]

    def __init__(
        self,
        non_word_sign: str = " ",
        sign_list: list[str] = None
    ):
        self.non_word_sign = non_word_sign
        self.available_sign_set = set()
        if sign_list is not None:
            self.available_sign_set.update(sign_list)
        else:
            for signs in [
                WordDict.LOWER_CASE_LETTER_SIGN_LIST,
                WordDict.UPPER_CASE_LETTER_SIGN_LIST,
                WordDict.DIGIT_SIGN_LIST,
                WordDict.SPECIAL_SIGN_LIST_A,
                WordDict.SPECIAL_SIGN_LIST_B,
                WordDict.SPECIAL_SIGN_LIST_C,
                WordDict.SPECIAL_SIGN_LIST_D
            ]:
                self.available_sign_set.update(signs)

        self.word_freq_counter: WordFreqCounter = WordFreqCounter()
        self.word_sign_dict: dict[str, str] = {}

    # append new words to the dict
    def add_words(self, words: list[str] | str) -> None:
        if isinstance(words, str):
            words = [words]

        self.word_freq_counter.add_words(words)

    # create word -> sign mapping
    def create_mapping(self) -> None:

        # sort words by frequency
        sorted_word_list: list[tuple[str, int]] = sorted(
            self.word_freq_counter.word_freq_dict.items(),
            key=lambda x: x[1],
            reverse=False
        )

        # remove most frequent words until the sign set is enough
        while len(sorted_word_list) > len(self.available_sign_set):
            sorted_word_list.pop(-1)

        # create mapping
        for word, _ in sorted_word_list:
            sign = self.available_sign_set.pop()
            self.word_sign_dict[word] = sign

    # get sign str of a sentence
    def encode_sentence(self, sentence_word_list: list[str]) -> str:
        encoded_sentence = ""
        for word in sentence_word_list:
            encoded_sentence += self.word_sign_dict.get(word, self.non_word_sign)
        return encoded_sentence

    # calculate sentence similarity
    # intersection / union
    # intersection: accept same sign in one sentence
    @staticmethod
    def cal_sentence_similarity(
        word_dict: "WordDict",
        sentence_a: list[str],
        sentence_b: list[str],
    ) -> float:
        encoded_sentence_a = word_dict.encode_sentence(sentence_a)
        encoded_sentence_b = word_dict.encode_sentence(sentence_b)
        if len(word_dict.non_word_sign) > 0:
            # remove non-word sign in encoded sentence
            encoded_sentence_a = encoded_sentence_a.replace(word_dict.non_word_sign, "")
            encoded_sentence_b = encoded_sentence_b.replace(word_dict.non_word_sign, "")

        if len(encoded_sentence_a) == 0 or len(encoded_sentence_b) == 0:
            return 0

        # count word freq of sentence b
        sentence_b_sign_freq_counter = WordFreqCounter()
        sentence_b_sign_freq_counter.add_words([sign for sign in encoded_sentence_b])
        sentence_b_sign_freq_dict = sentence_b_sign_freq_counter.word_freq_dict

        # count intersection
        intersection_count = 0
        for sign_in_a in encoded_sentence_a:
            if sign_in_a in sentence_b_sign_freq_dict:
                intersection_count += 1
                sentence_b_sign_freq_dict[sign_in_a] -= 1
                if sentence_b_sign_freq_dict[sign_in_a] == 0:
                    sentence_b_sign_freq_dict.pop(sign_in_a)

        # count union
        union_count = len(encoded_sentence_a) + len(encoded_sentence_b) - intersection_count

        return intersection_count / union_count

    # calculate sentence inclusion rate
    # return: intersection length / subset length, subset length
    @staticmethod
    def cal_sentence_inclusion_rate(
        word_dict: "WordDict",
        subset_sentence: list[str],
        superset_sentence: list[str],
    ) -> tuple[float, int]:
        encoded_subset_sentence = word_dict.encode_sentence(subset_sentence)
        encoded_superset_sentence = word_dict.encode_sentence(superset_sentence)
        if len(word_dict.non_word_sign) > 0:
            # remove non-word sign in encoded sentence
            encoded_subset_sentence = encoded_subset_sentence.replace(word_dict.non_word_sign, "")
            encoded_superset_sentence = encoded_superset_sentence.replace(word_dict.non_word_sign, "")

        if len(encoded_subset_sentence) == 0:
            return 0, 0

        # encoded sentence -> sign set
        subset_sign_set: set[str] = set([sign for sign in encoded_subset_sentence])
        superset_sign_set: set[str] = set([sign for sign in encoded_superset_sentence])

        # intersection / subset length, subset length
        return len(subset_sign_set & superset_sign_set) / len(subset_sign_set), len(subset_sign_set)
