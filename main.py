#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from obspy import read, Stream
from tkinter import filedialog, Tk
from collections import defaultdict
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk
)
import tkinter as tk

DEFAULT_FOLDER = "/media/iarv/Samsung/"

def select_mseed_paths():
    """Αν δεν δοθεί argument, ζητάει επιλογή μέσω GUI."""
    root = Tk()
    root.withdraw()
    paths = filedialog.askopenfilenames(
        initialdir=DEFAULT_FOLDER,
        title="Επιλέξτε αρχεία .mseed ή έναν φάκελο..."
    )
    if len(paths) == 1 and os.path.isdir(paths[0]):
        folder = paths[0]
        return [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".mseed")]
    return list(paths)

def plot_traces(stream: Stream, source_name: str):
    root = tk.Tk()
    root.title("Προβολή Seismic Traces")

    fig, ax = plt.subplots(figsize=(14, 6))
    canvas = FigureCanvasTkAgg(fig, master=root)
    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()

    # --- Κουμπί κανονικοποίησης ---
    normalize_state = {"active": False}

    def toggle_normalization():
        """Εναλλαγή μεταξύ κανονικοποιημένων και αρχικών τιμών."""
        normalize_state["active"] = not normalize_state["active"]
        ax.clear()

        # Επανασχεδίαση όλων των traces
        for tr in stream:
            data = tr.data.astype(float)
            if normalize_state["active"]:
                max_val = np.max(np.abs(data))
                if max_val != 0:
                    data = data / max_val

            times = tr.times("matplotlib")
            ax.plot(times, data, linewidth=0.8, color="black", label=tr.id)

        # Μορφοποίηση
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=90)
        ax.set_xlabel("Χρόνος (Ώρα:Λεπτά:Δευτερόλεπτα)")
        ax.set_ylabel("Πλάτος (Κανονικοποιημένο)" if normalize_state["active"] else "Πλάτος")
        ax.grid(True)
        ax.legend(fontsize=8, loc="upper right")
        ax.set_title(
            f"Προβολή Seismic Traces από: {source_name} "
            f"{'(Normalized)' if normalize_state['active'] else ''}",
            fontsize=12
        )

        fig.tight_layout()
        canvas.draw()

    # Προσθήκη κουμπιού
    norm_button = tk.Button(toolbar, text="🔄 Normalize", command=toggle_normalization)
    norm_button.pack(side=tk.LEFT, padx=4, pady=2)

    # --- Αρχική σχεδίαση δεδομένων ---
    for tr in stream:
        times = tr.times("matplotlib")
        ax.plot(times, tr.data, linewidth=0.8, color="black", label=tr.id)

    # Μορφοποίηση χρόνου & labels
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=90)
    ax.set_title(f"Προβολή Seismic Traces από: {source_name}", fontsize=12)
    ax.set_xlabel("Χρόνος (Ώρα:Λεπτά:Δευτερόλεπτα)")
    ax.set_ylabel("Πλάτος")
    ax.grid(True)
    ax.legend(fontsize=8, loc="upper right")

    fig.tight_layout()
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    root.mainloop()


def load_stream_from_paths(paths):
    merged_stream = Stream()
    for path in paths:
        try:
            st = read(path)
            merged_stream += st
        except Exception as e:
            print(f"⚠️ Σφάλμα στο {path}: {e}")
    merged_stream.sort()
    return merged_stream

def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if os.path.isfile(arg) and arg.endswith(".mseed"):
            paths = [arg]
        elif os.path.isdir(arg):
            paths = [os.path.join(arg, f) for f in os.listdir(arg) if f.endswith(".mseed")]
        else:
            print("❌ Το argument δεν είναι ούτε .mseed αρχείο ούτε φάκελος.")
            return
    else:
        paths = select_mseed_paths()

    if not paths:
        print("❌ Δεν επιλέχθηκαν αρχεία.")
        return

    print(f"📥 Φόρτωση {len(paths)} αρχείων MiniSEED...")

    stream = load_stream_from_paths(paths)
    if not stream:
        print("❌ Δεν φορτώθηκαν έγκυρα δεδομένα.")
        return

    source_name = os.path.basename(paths[0]) if len(paths) == 1 else f"{len(paths)} αρχεία"
    plot_traces(stream, source_name)

if __name__ == "__main__":
    main()
