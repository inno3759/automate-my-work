"""One-window GUI for people who fear terminals. Zero dependencies (Tkinter).

Launch via pythonw / .command so no console appears:  uv run pythonw gui.py
Pattern: sentence → (optional input) → one big button → log box → status.
Work runs in a thread; the button is disabled meanwhile; errors in plain words.
"""

from __future__ import annotations

import pathlib
import queue
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext

ROOT = pathlib.Path(__file__).resolve().parent
TITLE = "TODO Task name"
WHAT_IT_DOES = "TODO: One sentence. Example: Reads the spreadsheet you choose and sends each row to the site."


def do_work(path: str, say) -> None:  # noqa: ANN001
    """TODO: call your job here. say('text') prints to the window. Raise on failure."""
    say(f"Starting with {path or 'no file'} …")
    # from run import run; run(dry=False)
    say("Finished: 0 new, 0 skipped.")


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(TITLE)
        self.geometry("560x420")
        self.q: queue.Queue[str] = queue.Queue()
        tk.Label(self, text=WHAT_IT_DOES, wraplength=520, justify="left", font=("", 11)).pack(padx=16, pady=(16, 8), anchor="w")
        row = tk.Frame(self)
        row.pack(fill="x", padx=16)
        self.path = tk.StringVar()
        tk.Entry(row, textvariable=self.path).pack(side="left", fill="x", expand=True)
        tk.Button(row, text="Choose file…", command=self.pick).pack(side="left", padx=(8, 0))
        self.btn = tk.Button(self, text="RUN", font=("", 14, "bold"), height=2, command=self.start)
        self.btn.pack(fill="x", padx=16, pady=12)
        self.log = scrolledtext.ScrolledText(self, height=10, state="disabled", font=("Consolas", 10))
        self.log.pack(fill="both", expand=True, padx=16)
        self.status = tk.Label(self, text="Ready.", anchor="w")
        self.status.pack(fill="x", padx=16, pady=(4, 12))
        self.after(200, self.drain)

    def pick(self) -> None:
        p = filedialog.askopenfilename()
        if p:
            self.path.set(p)

    def say(self, text: str) -> None:
        self.q.put(text)

    def drain(self) -> None:
        while not self.q.empty():
            t = self.q.get()
            self.log.configure(state="normal")
            self.log.insert("end", t + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")
            self.status.configure(text=t[:80])
        self.after(200, self.drain)

    def start(self) -> None:
        self.btn.configure(state="disabled", text="Working…")

        def worker() -> None:
            try:
                do_work(self.path.get(), self.say)
                self.say("✓ Done.")
            except Exception as exc:  # plain words to the user, details to debug.log
                (ROOT / "logs").mkdir(exist_ok=True)
                import traceback

                (ROOT / "logs" / "debug.log").open("a", encoding="utf-8").write(traceback.format_exc())
                self.say(f"✗ It did not work: {exc}. Details saved to logs/debug.log.")
            finally:
                self.after(0, lambda: self.btn.configure(state="normal", text="RUN"))

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    App().mainloop()
