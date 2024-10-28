from fsrs import FSRS, Card, Rating, ReviewLog, State
from sortedcontainers import sorteddict
from datetime import datetime, timezone

class SRS:
    """
    Create FSRS object and sorted dictionary
    """
    def __init__(self):
        self.f = FSRS()
        self.words = sorteddict.SortedDict(lambda i : Card(i).due)

    """
    Creates a new card for the input word and adds both to the dictionary of words
    Represents a flashcard in the FSRS system.

    Card attributes:
        due (datetime): The date and time when the card is due next.
        stability (float): Core FSRS parameter used for scheduling.
        difficulty (float): Core FSRS parameter used for scheduling.
        elapsed_days (int): The number of days since the card was last reviewed.
        scheduled_days (int): The number of days until the card is due next.
        reps (int): The number of times the card has been reviewed in its history.
        lapses (int): The number of times the card has been lapsed in its history.
        state (State): The card's current learning state.
        last_review (datetime): The date and time of the card's last review.
    """
    def add_card(self, word : str):
        card = Card()
        self.words[word] = card

    def get_due(self, word : str):
        return self.words[word].due

    def get_stability(self, word : str):
        return self.words[word].stability

    def get_difficulty(self, word : str):
        return self.words[word].difficulty

    def get_elapsed_days(self, word : str) -> int:
        return self.words[word].elapsed_days

    def get_scheduled_days(self, word : str) -> int:
        return self.words[word].scheduled_days

    def get_reps(self, word : str) -> int:
        return self.words[word].reps

    def get_lapses(self, word : str) -> int:
        return self.words[word].lapses

    def get_state(self, word : str) -> State:
        return self.words[word].state

    def get_last_review(self, word : str) -> datetime:
        card = self.words[word]
        if card.last_review is not None:
            return self.words[word].last_review

    def remove_card(self, word : str) -> Card:
        return self.words.pop(word)

    def get_card(self, word : str) -> Card:
        return self.words[word]

    def get_words(self) -> sorteddict:
        return self.words

    """
    Reviews a word with a given rating
    Card does not need to be already registered in words
    rating must be either 'again' or 'good'
    returns the ReviewLog
    """
    def review_card(self, word: str, rating : str) -> ReviewLog:
        rating = rating.lower()
        card = self.words.get(word, Card())
        if rating == 'again':
            card, review_log = self.f.review_card(card, Rating.Again)
            self.words[word] = card # update card
            return review_log
        elif rating == 'good':
            card, review_log = self.f.review_card(card, Rating.Good)
            self.words[word] = card  # update card
            return review_log
        else:
            raise Exception("Rating was not 'again' or 'good'")

    def num_words(self) -> int:
        return len(self.words)



