import unittest
from unittest.mock import patch

from language_quiz_app import LanguageQuizApp


class FakeLabel(dict):
    def __init__(self, master, **kwargs):
        super().__init__(self)
        self.master = master
        self.update(**kwargs)

    def pack(self, pady=None):
        # mostly to make lint happy.
        print(f"pack received, pady:{pady}")

    def config(self, **kwargs):
        self.update(kwargs)


class TestLanguageQuizApp(unittest.TestCase):
    def setUp(self):
        self.app = LanguageQuizApp(label_factory=FakeLabel)

    @patch("language_quiz_app.os.path.exists")
    @patch("language_quiz_app.csv.DictReader")
    @patch("builtins.open")
    def test_load_word_data(
            self, _mock_open, mock_csv_dict_reader, mock_os_path_exists
    ):
        mock_csv_dict_reader.return_value = iter(
            [
                {
                    "Word": "cat",
                    "Image": "cat.jpg",
                    "Sound": "cat.mp3",
                    "Definition": "A small domesticated carnivorous mammal",
                }
            ]
        )
        mock_os_path_exists.return_value = True

        word_data = self.app.load_word_data("dummy_path")

        self.assertEqual(len(word_data), 1)
        self.assertEqual(word_data[0].word, "cat")
        self.assertEqual(word_data[0].image, "cat.jpg")
        self.assertEqual(word_data[0].sound, "cat.mp3")
        self.assertEqual(
            word_data[0].definition, "A small domesticated carnivorous mammal"
        )

    @patch("language_quiz_app.gtts.gTTS.save")
    @patch("language_quiz_app.os.path.exists")
    def test_generate_sound_if_not_found(self, mock_os_path_exists, mock_gtts_save):
        mock_os_path_exists.return_value = False

        self.app.generate_sound_if_not_found("test text", "dummy_path.mp3")

        mock_gtts_save.assert_called_once()

    @patch("language_quiz_app.random.choice")
    @patch("language_quiz_app.random.sample")
    def test_next_question(self, mock_random_sample, mock_random_choice):
        word_data = [
            self.app.WordData(
                "cat", "cat.jpg", "cat.mp3", "A small domesticated carnivorous mammal"
            )
        ]
        self.app.questions = word_data
        mock_random_choice.return_value = word_data[0]
        mock_random_sample.return_value = word_data

        self.app.next_question()

        self.assertEqual(self.app.current_question.word, "cat")
        self.assertEqual(self.app.word_label["text"], "cat")

    @patch("language_quiz_app.LanguageQuizApp.speak_text")
    def test_check_answer_correct(self, mock_speak_text):
        word_data = [
            self.app.WordData(
                "cat", "cat.jpg", "cat.mp3", "A small domesticated carnivorous mammal"
            )
        ]
        self.app.current_question = word_data[0]
        self.app.questions = word_data

        self.app.check_answer(word_data[0])

        self.assertEqual(self.app.score, 1)
        self.assertEqual(mock_speak_text.call_args[0][0], "Yes, that's correct!")
        self.assertTrue("correct" in self.app.get_message())
        self.assertFalse("incorrect" in self.app.get_message())

    @patch("language_quiz_app.LanguageQuizApp.speak_text")
    def test_check_answer_incorrect(self, mock_speak_text):
        word_data = [
            self.app.WordData(
                "cat", "cat.jpg", "cat.mp3", "A small domesticated carnivorous mammal"
            )
        ]
        self.app.current_question = word_data[0]
        self.app.questions = word_data

        self.app.check_answer(
            self.app.WordData(
                "dog", "dog.jpg", "dog.mp3", "A domesticated carnivorous mammal"
            )
        )

        self.assertEqual(self.app.score, 0)
        self.assertEqual(mock_speak_text.call_args[0][0], "Sorry, that's incorrect!")
        self.assertTrue("incorrect" in self.app.get_message())


class TestImagePathForWord(unittest.TestCase):
    def setUp(self):
        self.app = LanguageQuizApp(label_factory=FakeLabel)
        self.app.root_dir = "/test/root/dir"

    def test_image_path_for_word_valid(self):
        word_data = self.app.WordData("cat", "cat.jpg", "cat.mp3", "A feline animal")
        expected_path = "/test/root/dir/word_images/cat.jpg"
        self.assertEqual(self.app.image_path_for_word(word_data), expected_path)

    def test_image_path_for_word_no_image(self):
        word_data = self.app.WordData("dog", "", "dog.mp3", "A canine animal")
        expected_path = "/test/root/dir/word_images/"
        self.assertEqual(self.app.image_path_for_word(word_data), expected_path)

    def test_image_path_for_word_different_extension(self):
        word_data = self.app.WordData("bird", "bird.png", "bird.mp3", "A flying animal")
        expected_path = "/test/root/dir/word_images/bird.png"
        self.assertEqual(self.app.image_path_for_word(word_data), expected_path)

    @patch("os.path.join")
    def test_image_path_for_word_os_join_called(self, mock_join):
        word_data = self.app.WordData("fish", "fish.jpg", "fish.mp3", "An aquatic animal")
        self.app.image_path_for_word(word_data)
        mock_join.assert_called_once_with(self.app.root_dir, "word_images", "fish.jpg")


class TestGenerateSoundIfNotFound(unittest.TestCase):
    def setUp(self):
        self.app = LanguageQuizApp(label_factory=FakeLabel)

    @patch("language_quiz_app.os.path.exists")
    @patch("language_quiz_app.gtts.gTTS")
    def test_generate_sound_if_not_found_existing_file(self, mock_gtts, mock_exists):
        mock_exists.return_value = True
        self.app.generate_sound_if_not_found("hello", "hello.mp3")
        mock_gtts.assert_not_called()

    @patch("language_quiz_app.os.path.exists")
    @patch("language_quiz_app.gtts.gTTS")
    def test_generate_sound_if_not_found_new_file(self, mock_gtts, mock_exists):
        mock_exists.return_value = False
        mock_tts_instance = mock_gtts.return_value
        self.app.generate_sound_if_not_found("world", "world.mp3")
        mock_gtts.assert_called_once_with("world")
        mock_tts_instance.save.assert_called_once_with("world.mp3")

    @patch("language_quiz_app.os.path.exists")
    @patch("language_quiz_app.gtts.gTTS")
    def test_generate_sound_if_not_found_empty_text(self, mock_gtts, mock_exists):
        mock_exists.return_value = False
        self.app.generate_sound_if_not_found("", "empty.mp3")
        mock_gtts.assert_called_once_with("")

    @patch("language_quiz_app.os.path.exists")
    @patch("language_quiz_app.gtts.gTTS")
    def test_generate_sound_if_not_found_special_characters(self, mock_gtts, mock_exists):
        mock_exists.return_value = False
        self.app.generate_sound_if_not_found("Hello, World!", "special.mp3")
        mock_gtts.assert_called_once_with("Hello, World!")


if __name__ == "__main__":
    unittest.main()
