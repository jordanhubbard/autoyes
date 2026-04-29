#!/usr/bin/env python3
import os
import pty
import unittest
from unittest import mock

from autoyes import AutoYes, get_fd_winsize, set_fd_winsize


class TerminalSizeTests(unittest.TestCase):
    def test_set_and_get_winsize_on_pty(self):
        master_fd, slave_fd = pty.openpty()
        try:
            self.assertTrue(set_fd_winsize(slave_fd, (33, 101)))
            self.assertEqual(get_fd_winsize(slave_fd), (33, 101))
            self.assertEqual(get_fd_winsize(master_fd), (33, 101))
        finally:
            os.close(master_fd)
            os.close(slave_fd)

    def test_proxy_syncs_parent_winsize_to_child_pty(self):
        master_fd, slave_fd = pty.openpty()
        try:
            proxy = AutoYes(["true"])
            proxy.master_fd = master_fd
            proxy.get_parent_winsize = lambda: (41, 119)

            self.assertTrue(proxy.sync_pty_winsize())
            self.assertEqual(get_fd_winsize(slave_fd), (41, 119))
        finally:
            os.close(master_fd)
            os.close(slave_fd)

    def test_parent_winsize_falls_back_to_environment_or_default(self):
        with mock.patch("autoyes.get_fd_winsize", return_value=None):
            with mock.patch("autoyes.shutil.get_terminal_size", return_value=os.terminal_size((132, 43))):
                self.assertEqual(AutoYes(["true"]).get_parent_winsize(), (43, 132))

            with mock.patch("autoyes.shutil.get_terminal_size", return_value=os.terminal_size((0, 0))):
                self.assertEqual(AutoYes(["true"]).get_parent_winsize(), (24, 80))


if __name__ == "__main__":
    unittest.main()
