JUDGE_GUIDANCE = """
You are reviewing normalized dynamic-analysis findings from Valgrind Memcheck.
Use the following cues:
- Focus on severity and reproducibility.
- Highlight invalid reads/writes and use-after-free as high priority.
- Memory leaks marked DefinitelyLost are medium priority unless proven negligible.
- Correlate multiple findings by signature to avoid duplicates.
""".strip()
