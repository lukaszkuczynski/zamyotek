from unittest import TestCase
from unittest import main, TestCase

from rekognition_node import LabelChoiceRememberingStrategy, LabelChoiceStrategyFirst


class LabelChoiceStrategyTestCase(TestCase):
    def test_simple_choice_select_first(self):
        labels_and_confidence = [("cat", 99), ("dog", 90)]
        strategy = LabelChoiceStrategyFirst()
        label_chosen = strategy.choose_label(labels_and_confidence)
        assert label_chosen == "cat"

    def test_simple_choice_always_selects_first(self):
        labels_and_confidence = [("cat", 99), ("dog", 90)]
        strategy = LabelChoiceStrategyFirst()
        label_chosen_1 = strategy.choose_label(labels_and_confidence)
        label_chosen_2 = strategy.choose_label(labels_and_confidence)
        assert label_chosen_1 == label_chosen_2

    def test_remembering_strategy_chooses_new_stuff(self):
        labels_and_confidence = [("cat", 99), ("dog", 90)]
        strategy = LabelChoiceRememberingStrategy()
        label_chosen_1 = strategy.choose_label(labels_and_confidence)
        label_chosen_2 = strategy.choose_label(labels_and_confidence)
        assert label_chosen_1 == "cat"
        assert label_chosen_2 == "dog"

    def test_remembering_strategy_chooses_first_if_all_remembered(self):
        labels_and_confidence = [("cat", 99), ("dog", 90)]
        strategy = LabelChoiceRememberingStrategy()
        strategy.choose_label(labels_and_confidence)
        strategy.choose_label(labels_and_confidence)
        label_chosen_3 = strategy.choose_label(labels_and_confidence)
        assert label_chosen_3 == "cat"


if __name__ == "__main__":
    main()
