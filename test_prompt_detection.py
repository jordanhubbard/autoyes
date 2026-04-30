#!/usr/bin/env python3
import unittest

from autoyes import AutoYes


class PromptDetectionTests(unittest.TestCase):
    def setUp(self):
        self.proxy = AutoYes(["true"])

    def test_detects_codex_menu_with_secondary_yes_option(self):
        prompt = """
Would you like to run the following command?

$ command bd ready

› 1. Yes, proceed (y)
  2. Yes, and don't ask again for commands that start with `command bd ready`
     (p)
  3. No, and tell Codex what to do differently (esc)
Press enter to confirm or esc to cancel
"""

        self.assertEqual(
            self.proxy.check_for_approval_prompt(prompt),
            (b"\r", "pressing Enter"),
        )

    def test_detects_codex_menu_with_yes_and_no_descriptions(self):
        prompt = """
Would you like to run the following command?

$ ssh -o ConnectTimeout=8 user@example.com 'curl -sf "$OPENAI_BASE_URL/models"'

› 1. Yes, proceed (y)
  2. No, and tell Codex what to do differently (esc)
Press enter to confirm or esc to cancel
"""

        self.assertEqual(
            self.proxy.check_for_approval_prompt(prompt),
            (b"\r", "pressing Enter"),
        )

    def test_does_not_press_enter_when_selected_numbered_option_is_no(self):
        prompt = """
Would you like to run the following command?

  1. Yes, proceed (y)
› 2. No, and tell Codex what to do differently (esc)
"""

        self.assertIsNone(self.proxy.check_for_approval_prompt(prompt))


if __name__ == "__main__":
    unittest.main()
