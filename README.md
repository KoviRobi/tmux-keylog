# TMUX keylogger for ascii casts

Inspired by [@alanxoc3 at
https://xoc3.io/blog/2021-11-22](https://xoc3.io/blog/2021-11-22)
but largely rewritten now. (The lengths I go to, to avoid using `sudo`
on random programs...)

It requires [`pynput`](https://pypi.org/project/pynput/). Only tested
on Linux, using Python 3.13 but should work anywhere pynput works,
and requires Python >=3.8 (f-strings, uv builder).
