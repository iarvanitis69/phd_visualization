#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from obspy import read, Stream, UTCDateTime
from tkinter import filedialog, Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
import json

DEFAULT_FOLDER = "/media/iarv/Samsung/"

# -------------------------------------------------------------
# JSON HELPERS
# -------------------------------------------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# -------------------------------------------------------------
# (ΠΡΟΑΙΡΕΤΙΚΟ) PATH PARSER – ΔΕΝ ΧΡΗΣΙΜΟΠΟΙΕΙΤΑΙ ΠΛΕΟΝ
# -------------------------------------------------------------
def extract_event_info_from_path(mseed_path):
    """
    Εξάγει year, event, station (NET.STA) και channel (HHZ κλπ)
    Πρέπει ο φάκελος να είναι:
        .../<YEAR>/<EVENT>/<STATION>/<mseed>
    """
    parts = mseed_path.split(os.sep)

    station = parts[-2]       # HL.APE
    event_name = parts[-3]    # 20100507T.....
    year = parts[-4]          # 2010

    filename = parts[-1]
    channel = filename.split("..")[-1].split("__")[0]  # HHZ

    return year, event_name, station, channel

# -------------------------------------------------------------
# LOAD MARKERS FROM PS_BOUNDARIES.JSON (ΜΟΝΟ ΑΠΟ PATH)
# -------------------------------------------------------------
def load_event_markers(mseed_path):
    """
    Βρίσκει το PS_boundaries.json ανεβαίνοντας 3 επίπεδα από τον φάκελο
    στον οποίο βρίσκεται το .mseed αρχείο, και διαβάζει:

      start_of_event_datetime
      peak_amplitude_datetime
      end_of_peak_segment_datetime
      end_of_event_time

    Υποθέτουμε δομή τύπου:

        ROOT/
            Logs/PS_boundaries.json
            <YEAR>/<EVENT>/<STATION>/<mseed>
    """

    # Φάκελος που περιέχει το mseed (STATION)
    station_dir = os.path.dirname(mseed_path)        # .../<EVENT>/<STATION>
    event_dir = os.path.dirname(station_dir)         # .../<YEAR>/<EVENT>
    year_dir = os.path.dirname(event_dir)            # .../<YEAR>
    root_dir = os.path.dirname(year_dir)             # .../ROOT

    # Logs/PS_boundaries.json στο ROOT
    logs_dir = os.path.join(root_dir, "Logs")
    json_path = os.path.join(logs_dir, "PS_boundaries.json")

    if not os.path.exists(json_path):
        print(f"❌ Δεν βρέθηκε το {json_path}")
        print(f"🔍 Υπολογισμένο ROOT: {root_dir}")
        return None

    data = load_json(json_path)

    # Προσδιορισμός year, event, station, channel από το path
    year = os.path.basename(year_dir)
    event_name = os.path.basename(event_dir)
    station = os.path.basename(station_dir)
    filename = os.path.basename(mseed_path)
    channel = filename.split("..")[-1].split("__")[0]  # π.χ. HHZ

    # Πλοήγηση στη δομή του JSON
    if year not in data:
        return None
    if event_name not in data[year]:
        return None
    if station not in data[year][event_name]:
        return None
    # if channel not in data[year][event_name][station]:
    #     return None

    info = data[year][event_name][station]["HHZ"]

    return {
        "start": info.get("start_of_event_datetime"),
        "peak": info.get("peak_amplitude_datetime"),
        "end_peak_seg": info.get("end_of_peak_segment_datetime"),
        "end_event": info.get("end_of_event_time")
    }

# -------------------------------------------------------------
# DRAW MARKERS ON AX
# -------------------------------------------------------------
def add_vertical_markers(ax, markers):
    if markers is None:
        return

    colors = {
        "start": "green",
        "peak": "red",
        "end_peak_seg": "orange",
        "end_event": "blue"
    }

    for key, tstring in markers.items():
        if tstring is None:
            continue
        try:
            t = UTCDateTime(tstring).datetime
            t_mat = mdates.date2num(t)
            ax.axvline(t_mat, color=colors[key], linestyle="--", linewidth=1.4, label=key)
        except Exception:
            continue

# -------------------------------------------------------------
# FILE SELECTION
# -------------------------------------------------------------
def select_mseed_paths():
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

# -------------------------------------------------------------
# MAIN PLOT GUI
# -------------------------------------------------------------
def plot_traces(stream: Stream, source_name: str, paths):
    root = tk.Tk()
    root.title("Προβολή Seismic Traces με Markers")

    fig, ax = plt.subplots(figsize=(14, 6))
    canvas = FigureCanvasTkAgg(fig, master=root)
    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()

    # ---------------------------------------------------------
    # Normalize button
    # ---------------------------------------------------------
    normalize_state = {"active": False}

    def toggle_normalization():
        normalize_state["active"] = not normalize_state["active"]
        ax.clear()

        for tr, path in zip(stream, paths):
            data = tr.data.astype(float)

            if normalize_state["active"]:
                max_val = np.max(np.abs(data))
                if max_val != 0:
                    data = data / max_val

            times = tr.times("matplotlib")
            ax.plot(times, data, linewidth=0.8, color="black", label=tr.id)

            # Φόρτωση markers μόνο από το path
            markers = load_event_markers(path)
            add_vertical_markers(ax, markers)

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

    norm_button = tk.Button(toolbar, text="🔄 Normalize", command=toggle_normalization)
    norm_button.pack(side=tk.LEFT, padx=4, pady=2)

    # ---------------------------------------------------------
    # Initial plot
    # ---------------------------------------------------------
    for tr, path in zip(stream, paths):
        times = tr.times("matplotlib")
        ax.plot(times, tr.data, linewidth=0.8, color="black", label=tr.id)

        # Φόρτωση και σχεδίαση markers ΜΟΝΟ από το path
        markers = load_event_markers(path)
        add_vertical_markers(ax, markers)

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

# -------------------------------------------------------------
def load_stream_from_paths(paths):
    merged_stream = Stream()
    for path in paths:
        try:
            st = read(path)
            for tr in st:
                tr.stats._filepath = path  # store original filepath (αν το χρειαστείς αργότερα)
            merged_stream += st
        except Exception as e:
            print(f"⚠️ Σφάλμα στο {path}: {e}")
    merged_stream.sort()
    return merged_stream

# -------------------------------------------------------------
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
    plot_traces(stream, source_name, paths)

if __name__ == "__main__":
    main()
