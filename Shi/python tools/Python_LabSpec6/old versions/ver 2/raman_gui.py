from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tkinter as tk
from tkinter import font as tkfont
from tkinter import filedialog, messagebox, ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


APP_TITLE = "Spontaneous Raman Spectrum Editor"
CURSOR_COLORS = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]


@dataclass
class ParsedSpectrum:
    path: Path
    x: np.ndarray
    y_raw: np.ndarray
    y_work: np.ndarray
    delimiter: str = "\t"
    header_lines: list[str] = field(default_factory=list)
    numeric_rows: list[tuple[str, str]] = field(default_factory=list)
    line_records: list[tuple[str, object]] = field(default_factory=list)


@dataclass
class CursorLine:
    label: str
    color: str
    x_value: float
    artist: object
    text: object


@dataclass
class UndoSnapshot:
    spectrum_index: int | None
    y_work: np.ndarray | None
    pick_points: list[tuple[float, float]]
    cursor_states: list[tuple[str, str, float]]
    last_baseline: np.ndarray | None


class SpectrumParser:
    @staticmethod
    def read(path: Path) -> ParsedSpectrum:
        header_lines: list[str] = []
        numeric_rows: list[tuple[str, str]] = []
        line_records: list[tuple[str, object]] = []
        xs: list[float] = []
        ys: list[float] = []
        delimiter = "\t"

        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    header_lines.append(line)
                    line_records.append(("text", line))
                    continue

                parts = SpectrumParser._split_numeric_line(stripped)
                if parts is None:
                    header_lines.append(line)
                    line_records.append(("text", line))
                    continue

                x_text, y_text, detected_delimiter = parts
                delimiter = detected_delimiter or delimiter
                xs.append(float(x_text))
                ys.append(float(y_text))
                numeric_rows.append((x_text, y_text))
                line_records.append(("numeric", (x_text, y_text)))

        if not xs:
            raise ValueError(f"No two-column numeric data was found in {path.name}.")

        x = np.asarray(xs, dtype=float)
        y = np.asarray(ys, dtype=float)
        return ParsedSpectrum(path, x, y, y.copy(), delimiter, header_lines, numeric_rows, line_records)

    @staticmethod
    def write(path: Path, spectrum: ParsedSpectrum) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            corrected_index = 0
            for record_type, payload in spectrum.line_records:
                if record_type == "text":
                    handle.write(str(payload))
                    continue
                x_text, raw_y_text = payload
                corrected = spectrum.y_work[corrected_index]
                y_text = SpectrumParser._format_like(raw_y_text, corrected)
                handle.write(f"{x_text}{spectrum.delimiter}{y_text}\n")
                corrected_index += 1

    @staticmethod
    def _split_numeric_line(line: str) -> tuple[str, str, str] | None:
        for delimiter in ("\t", ",", ";"):
            if delimiter in line:
                parts = [part.strip() for part in line.split(delimiter)]
                if len(parts) >= 2 and SpectrumParser._is_float(parts[0]) and SpectrumParser._is_float(parts[1]):
                    return parts[0], parts[1], delimiter

        parts = line.split()
        if len(parts) >= 2 and SpectrumParser._is_float(parts[0]) and SpectrumParser._is_float(parts[1]):
            return parts[0], parts[1], "\t"

        return None

    @staticmethod
    def _is_float(text: str) -> bool:
        try:
            float(text)
            return True
        except ValueError:
            return False

    @staticmethod
    def _format_like(template: str, value: float) -> str:
        if "e" in template.lower():
            decimals = SpectrumParser._decimal_count(template)
            return f"{value:.{max(decimals, 6)}e}"
        decimals = SpectrumParser._decimal_count(template)
        return f"{value:.{decimals}f}" if decimals else f"{value:.0f}"

    @staticmethod
    def _decimal_count(text: str) -> int:
        mantissa = text.lower().split("e", 1)[0]
        if "." not in mantissa:
            return 0
        return len(mantissa.split(".", 1)[1])


class RamanEditor(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1280x780")
        self.minsize(1020, 640)

        self.spectra: list[ParsedSpectrum] = []
        self.current_index: int | None = None
        self.cursor_lines: list[CursorLine] = []
        self.dragging_cursor: CursorLine | None = None
        self.pick_points: list[tuple[float, float]] = []
        self.pick_mode = tk.BooleanVar(value=False)
        self.snap_points_to_spectrum = tk.BooleanVar(value=True)
        self.show_baseline = tk.BooleanVar(value=True)
        self.show_original = tk.BooleanVar(value=True)
        self.poly_order = tk.IntVar(value=3)
        self.cursor_label = tk.StringVar(value="")
        self.cursor_x = tk.StringVar(value="")
        self.status_text = tk.StringVar(value="Open one or more Raman spectrum text files to begin.")
        self.undo_stack: list[UndoSnapshot] = []
        self._drag_start_snapshot: UndoSnapshot | None = None

        self.raw_artist = None
        self.work_artist = None
        self.baseline_artist = None
        self.point_artist = None
        self._last_baseline: np.ndarray | None = None

        self._configure_fonts()
        self._build_ui()
        self._connect_plot_events()
        self.bind_all("<Control-z>", self.undo)
        self.bind_all("<Control-Z>", self.undo)

    def _configure_fonts(self) -> None:
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont"):
            tkfont.nametofont(name).configure(size=11)
        tkfont.nametofont("TkHeadingFont").configure(size=12, weight="bold")

        style = ttk.Style(self)
        style.configure("TButton", padding=(8, 5))
        style.configure("TLabel", padding=(0, 1))
        style.configure("TLabelframe.Label", font=tkfont.nametofont("TkHeadingFont"))

    def _build_ui(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(self, padding=(10, 10, 8, 10))
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.columnconfigure(0, weight=1)

        plot_area = ttk.Frame(self, padding=(0, 8, 10, 4))
        plot_area.grid(row=0, column=1, sticky="nsew")
        plot_area.rowconfigure(0, weight=1)
        plot_area.columnconfigure(0, weight=1)

        ttk.Button(sidebar, text="Open spectra", command=self.open_files).grid(row=0, column=0, sticky="ew")
        ttk.Button(sidebar, text="Export corrected", command=self.export_current).grid(row=1, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(sidebar, text="Export all corrected", command=self.export_all).grid(row=2, column=0, sticky="ew", pady=(6, 12))
        ttk.Button(sidebar, text="Undo   Ctrl+Z", command=self.undo).grid(row=3, column=0, sticky="ew", pady=(0, 12))

        ttk.Label(sidebar, text="Loaded spectra").grid(row=4, column=0, sticky="w")
        self.spectrum_list = tk.Listbox(sidebar, height=8, width=32, exportselection=False, font=("Segoe UI", 11))
        self.spectrum_list.grid(row=5, column=0, sticky="ew", pady=(4, 10))
        self.spectrum_list.bind("<<ListboxSelect>>", self._on_spectrum_selected)
        spectra_actions = ttk.Frame(sidebar)
        spectra_actions.grid(row=6, column=0, sticky="ew", pady=(0, 10))
        spectra_actions.columnconfigure(0, weight=1)
        spectra_actions.columnconfigure(1, weight=1)
        ttk.Button(spectra_actions, text="Delete selected", command=self.delete_selected_spectrum).grid(
            row=0, column=0, sticky="ew"
        )
        ttk.Button(spectra_actions, text="Clear all", command=self.clear_all_spectra).grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

        cursor_frame = ttk.LabelFrame(sidebar, text="X-axis cursor lines", padding=8)
        cursor_frame.grid(row=7, column=0, sticky="ew", pady=(0, 10))
        cursor_frame.columnconfigure(0, weight=1)
        ttk.Button(cursor_frame, text="Add cursor", command=self.add_cursor).grid(row=0, column=0, sticky="ew")
        ttk.Button(cursor_frame, text="Remove selected", command=self.remove_selected_cursor).grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.cursor_list = tk.Listbox(cursor_frame, height=5, exportselection=False, font=("Segoe UI", 11))
        self.cursor_list.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.cursor_list.bind("<<ListboxSelect>>", self._on_cursor_selected)
        ttk.Label(cursor_frame, text="Label").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Label(cursor_frame, text="X value").grid(row=2, column=1, sticky="w", pady=(8, 0), padx=(6, 0))
        ttk.Entry(cursor_frame, textvariable=self.cursor_label, width=13).grid(row=3, column=0, sticky="ew")
        ttk.Entry(cursor_frame, textvariable=self.cursor_x, width=13).grid(row=3, column=1, sticky="ew", padx=(6, 0))
        ttk.Button(cursor_frame, text="Update selected cursor", command=self.update_selected_cursor).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )

        baseline_frame = ttk.LabelFrame(sidebar, text="Baseline correction", padding=8)
        baseline_frame.grid(row=8, column=0, sticky="ew", pady=(0, 10))
        baseline_frame.columnconfigure(1, weight=1)

        ttk.Label(baseline_frame, text="Poly order").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(baseline_frame, from_=0, to=8, textvariable=self.poly_order, width=5).grid(row=0, column=1, sticky="w")
        ttk.Button(baseline_frame, text="Fit whole spectrum", command=self.apply_polyfit).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )
        ttk.Checkbutton(
            baseline_frame,
            text="Manual point mode",
            variable=self.pick_mode,
            command=self._update_pick_status,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Checkbutton(
            baseline_frame,
            text="Snap points to spectrum",
            variable=self.snap_points_to_spectrum,
        ).grid(row=3, column=0, columnspan=2, sticky="w")
        ttk.Button(baseline_frame, text="Apply point baseline", command=self.apply_manual_baseline).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )
        ttk.Button(baseline_frame, text="Clear points", command=self.clear_points).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )
        ttk.Button(baseline_frame, text="Reset to raw", command=self.reset_current).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )
        ttk.Checkbutton(
            baseline_frame,
            text="Show raw overlay",
            variable=self.show_original,
            command=self.refresh_plot,
        ).grid(row=7, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Checkbutton(
            baseline_frame,
            text="Show baseline",
            variable=self.show_baseline,
            command=self.refresh_plot,
        ).grid(row=8, column=0, columnspan=2, sticky="w")

        help_text = (
            "Drag cursor lines on the plot.\n"
            "Manual baseline: enable point mode, click baseline points, then apply.\n"
            "Turn snap off to place points anywhere on the plot.\n"
            "Use mouse wheel or the toolbar buttons to zoom.\n"
            "Undo recent edits with Ctrl+Z.\n"
            "Polyfit subtracts the fitted baseline from the selected spectrum."
        )
        ttk.Label(sidebar, text=help_text, wraplength=250, foreground="#4a4a4a").grid(row=9, column=0, sticky="ew")

        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel("Raman shift / x-axis", fontsize=12)
        self.ax.set_ylabel("Intensity", fontsize=12)
        self.ax.tick_params(labelsize=11)
        self.ax.grid(True, alpha=0.22)

        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_area)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        toolbar_frame = ttk.Frame(plot_area)
        toolbar_frame.grid(row=1, column=0, sticky="ew")
        NavigationToolbar2Tk(self.canvas, toolbar_frame, pack_toolbar=False).grid(row=0, column=0, sticky="w")
        ttk.Button(toolbar_frame, text="Zoom in", command=self.zoom_in).grid(row=0, column=1, sticky="w", padx=(12, 0))
        ttk.Button(toolbar_frame, text="Zoom out", command=self.zoom_out).grid(row=0, column=2, sticky="w", padx=(6, 0))
        ttk.Button(toolbar_frame, text="Reset view", command=self.reset_zoom).grid(row=0, column=3, sticky="w", padx=(6, 0))

        status = ttk.Label(self, textvariable=self.status_text, anchor="w", padding=(10, 4))
        status.grid(row=1, column=0, columnspan=2, sticky="ew")

    def _connect_plot_events(self) -> None:
        self.canvas.mpl_connect("button_press_event", self._on_plot_press)
        self.canvas.mpl_connect("motion_notify_event", self._on_plot_motion)
        self.canvas.mpl_connect("button_release_event", self._on_plot_release)
        self.canvas.mpl_connect("scroll_event", self._on_scroll_zoom)

    @property
    def current(self) -> ParsedSpectrum | None:
        if self.current_index is None:
            return None
        if self.current_index < 0 or self.current_index >= len(self.spectra):
            return None
        return self.spectra[self.current_index]

    def _capture_undo_snapshot(self) -> UndoSnapshot:
        spectrum = self.current
        return UndoSnapshot(
            spectrum_index=self.current_index,
            y_work=spectrum.y_work.copy() if spectrum is not None else None,
            pick_points=list(self.pick_points),
            cursor_states=[(cursor.label, cursor.color, cursor.x_value) for cursor in self.cursor_lines],
            last_baseline=self._last_baseline.copy() if self._last_baseline is not None else None,
        )

    def _push_undo(self) -> None:
        self.undo_stack.append(self._capture_undo_snapshot())
        if len(self.undo_stack) > 80:
            self.undo_stack.pop(0)

    def _clear_undo_history(self) -> None:
        self.undo_stack.clear()
        self._drag_start_snapshot = None

    def undo(self, _event: object | None = None) -> str:
        if not self.undo_stack:
            self.status_text.set("Nothing to undo.")
            return "break"

        snapshot = self.undo_stack.pop()
        self.current_index = snapshot.spectrum_index
        if snapshot.spectrum_index is not None and snapshot.y_work is not None:
            self.spectra[snapshot.spectrum_index].y_work = snapshot.y_work.copy()
            self.spectrum_list.selection_clear(0, tk.END)
            self.spectrum_list.selection_set(snapshot.spectrum_index)
            self.spectrum_list.see(snapshot.spectrum_index)

        self.pick_points = list(snapshot.pick_points)
        self._last_baseline = snapshot.last_baseline.copy() if snapshot.last_baseline is not None else None
        self.cursor_lines.clear()
        for label, color, x_value in snapshot.cursor_states:
            self.cursor_lines.append(CursorLine(label, color, x_value, None, None))

        self.refresh_plot()
        self.status_text.set("Undid the last edit.")
        return "break"

    def open_files(self) -> None:
        file_names = filedialog.askopenfilenames(
            title="Open Raman spectra",
            filetypes=[
                ("Spectrum text files", "*.txt *.csv *.dat *.tsv"),
                ("All files", "*.*"),
            ],
        )
        if not file_names:
            return

        loaded = 0
        errors: list[str] = []
        for file_name in file_names:
            path = Path(file_name)
            try:
                spectrum = SpectrumParser.read(path)
            except Exception as exc:
                errors.append(f"{path.name}: {exc}")
                continue
            self.spectra.append(spectrum)
            self.spectrum_list.insert(tk.END, path.name)
            loaded += 1

        if loaded and self.current_index is None:
            self.spectrum_list.selection_set(0)
            self._select_spectrum(0)
        elif loaded:
            self.status_text.set(f"Loaded {loaded} spectrum file(s).")

        if errors:
            messagebox.showwarning("Some files were not loaded", "\n".join(errors))

    def delete_selected_spectrum(self) -> None:
        selection = self.spectrum_list.curselection()
        if not selection:
            messagebox.showinfo("No spectrum selected", "Select a loaded spectrum to delete.")
            return

        index = selection[0]
        removed = self.spectra.pop(index)
        self.spectrum_list.delete(index)
        self._clear_undo_history()
        self.pick_points.clear()
        self._last_baseline = None

        if not self.spectra:
            self.current_index = None
            self.cursor_lines.clear()
            self.cursor_list.delete(0, tk.END)
            self.cursor_label.set("")
            self.cursor_x.set("")
            self.refresh_plot()
            self.status_text.set(f"Deleted {removed.path.name}. No spectra are currently loaded.")
            return

        next_index = min(index, len(self.spectra) - 1)
        self.spectrum_list.selection_set(next_index)
        self._select_spectrum(next_index)
        self.status_text.set(f"Deleted {removed.path.name}.")

    def clear_all_spectra(self) -> None:
        if not self.spectra:
            self.status_text.set("No loaded spectra to clear.")
            return

        count = len(self.spectra)
        self.spectra.clear()
        self.spectrum_list.delete(0, tk.END)
        self.cursor_lines.clear()
        self.cursor_list.delete(0, tk.END)
        self.cursor_label.set("")
        self.cursor_x.set("")
        self.pick_points.clear()
        self._last_baseline = None
        self.current_index = None
        self._clear_undo_history()
        self.refresh_plot()
        self.status_text.set(f"Cleared {count} loaded spectrum file(s).")

    def export_current(self) -> None:
        spectrum = self.current
        if spectrum is None:
            messagebox.showinfo("No spectrum selected", "Open and select a spectrum first.")
            return

        default_name = f"{spectrum.path.stem}_baseline_corrected{spectrum.path.suffix or '.txt'}"
        output = filedialog.asksaveasfilename(
            title="Export corrected spectrum",
            initialfile=default_name,
            defaultextension=spectrum.path.suffix or ".txt",
            filetypes=[("Text files", "*.txt *.csv *.dat *.tsv"), ("All files", "*.*")],
        )
        if not output:
            return

        SpectrumParser.write(Path(output), spectrum)
        self.status_text.set(f"Exported corrected spectrum to {output}.")

    def export_all(self) -> None:
        if not self.spectra:
            messagebox.showinfo("No spectra loaded", "Open spectra before exporting.")
            return

        directory = filedialog.askdirectory(title="Choose folder for corrected spectra")
        if not directory:
            return

        output_dir = Path(directory)
        for spectrum in self.spectra:
            output = output_dir / f"{spectrum.path.stem}_baseline_corrected{spectrum.path.suffix or '.txt'}"
            SpectrumParser.write(output, spectrum)
        self.status_text.set(f"Exported {len(self.spectra)} corrected spectrum file(s).")

    def _on_spectrum_selected(self, _event: object) -> None:
        selection = self.spectrum_list.curselection()
        if selection:
            self._select_spectrum(selection[0])

    def _select_spectrum(self, index: int) -> None:
        self.current_index = index
        self.pick_points.clear()
        self._last_baseline = None
        self.refresh_plot(reset_view=True)
        spectrum = self.current
        if spectrum:
            self.status_text.set(f"Selected {spectrum.path.name}.")

    def add_cursor(self) -> None:
        spectrum = self.current
        if spectrum is None:
            messagebox.showinfo("No spectrum selected", "Open and select a spectrum before adding cursor lines.")
            return

        self._push_undo()
        index = len(self.cursor_lines) + 1
        color = CURSOR_COLORS[(index - 1) % len(CURSOR_COLORS)]
        x_value = float(spectrum.x[len(spectrum.x) // 2])
        artist = self.ax.axvline(x_value, color=color, linewidth=1.6, picker=6)
        text = self.ax.text(
            x_value,
            0.98,
            f"C{index}: {x_value:.2f}",
            color=color,
            rotation=90,
            va="top",
            ha="right",
            transform=self.ax.get_xaxis_transform(),
        )
        cursor = CursorLine(f"C{index}", color, x_value, artist, text)
        self.cursor_lines.append(cursor)
        self.cursor_list.insert(tk.END, f"{cursor.label}  x={cursor.x_value:.2f}")
        self.cursor_list.selection_clear(0, tk.END)
        self.cursor_list.selection_set(tk.END)
        self.cursor_label.set(cursor.label)
        self.cursor_x.set(f"{cursor.x_value:.3f}")
        self._redraw_cursor(cursor)
        self.canvas.draw_idle()

    def remove_selected_cursor(self) -> None:
        selection = self.cursor_list.curselection()
        if not selection:
            return
        self._push_undo()
        index = selection[0]
        cursor = self.cursor_lines.pop(index)
        cursor.artist.remove()
        cursor.text.remove()
        self.cursor_list.delete(index)
        self._renumber_cursors()
        self.canvas.draw_idle()

    def update_selected_cursor(self) -> None:
        selection = self.cursor_list.curselection()
        if not selection:
            return

        index = selection[0]
        cursor = self.cursor_lines[index]
        label = self.cursor_label.get().strip()
        try:
            x_value = float(self.cursor_x.get())
        except ValueError:
            messagebox.showerror("Invalid x value", "Enter a numeric x-axis value for the selected cursor.")
            return

        self._push_undo()
        if label:
            cursor.label = label
        cursor.x_value = x_value
        self._redraw_cursor(cursor)
        self._refresh_cursor_list()
        self.cursor_list.selection_set(index)
        self._highlight_selected_cursor()
        self.canvas.draw_idle()

    def apply_polyfit(self) -> None:
        spectrum = self.current
        if spectrum is None:
            return
        order = int(self.poly_order.get())
        if order >= len(spectrum.x):
            messagebox.showerror("Invalid order", "Polynomial order must be smaller than the number of data points.")
            return

        coefficients = np.polyfit(spectrum.x, spectrum.y_work, order)
        baseline = np.polyval(coefficients, spectrum.x)
        self._push_undo()
        self._apply_baseline(baseline, f"Applied polynomial baseline correction, order {order}.")

    def apply_manual_baseline(self) -> None:
        spectrum = self.current
        if spectrum is None:
            return
        if len(self.pick_points) < 2:
            messagebox.showinfo("Need more points", "Choose at least two manual baseline points.")
            return

        sorted_points = sorted(self.pick_points, key=lambda point: point[0])
        px = np.asarray([point[0] for point in sorted_points], dtype=float)
        py = np.asarray([point[1] for point in sorted_points], dtype=float)
        baseline = np.interp(spectrum.x, px, py, left=py[0], right=py[-1])
        self._push_undo()
        self._apply_baseline(baseline, f"Applied manual baseline through {len(sorted_points)} point(s).")

    def _apply_baseline(self, baseline: np.ndarray, status: str) -> None:
        spectrum = self.current
        if spectrum is None:
            return
        spectrum.y_work = spectrum.y_work - baseline
        self._last_baseline = baseline
        self.refresh_plot()
        self.status_text.set(status)

    def reset_current(self) -> None:
        spectrum = self.current
        if spectrum is None:
            return
        self._push_undo()
        spectrum.y_work = spectrum.y_raw.copy()
        self._last_baseline = None
        self.clear_points(redraw=False, record_undo=False)
        self.refresh_plot()
        self.status_text.set(f"Reset {spectrum.path.name} to raw intensity.")

    def clear_points(self, redraw: bool = True, record_undo: bool = True) -> None:
        if record_undo and self.pick_points:
            self._push_undo()
        self.pick_points.clear()
        if redraw:
            self.refresh_plot()
            self.status_text.set("Manual baseline points cleared.")

    def zoom_in(self) -> None:
        self._zoom_plot(0.75)

    def zoom_out(self) -> None:
        self._zoom_plot(1.35)

    def reset_zoom(self) -> None:
        if self.current is None:
            return
        self.refresh_plot(reset_view=True)
        self.status_text.set("Reset plot view.")

    def _zoom_plot(self, scale: float, center_x: float | None = None, center_y: float | None = None) -> None:
        if self.current is None:
            return

        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        x_center = center_x if center_x is not None else (x_min + x_max) / 2
        y_center = center_y if center_y is not None else (y_min + y_max) / 2
        new_width = (x_max - x_min) * scale
        new_height = (y_max - y_min) * scale

        self.ax.set_xlim(x_center - new_width / 2, x_center + new_width / 2)
        self.ax.set_ylim(y_center - new_height / 2, y_center + new_height / 2)
        self.canvas.draw_idle()

    def refresh_plot(self, reset_view: bool = False) -> None:
        spectrum = self.current
        self.ax.clear()
        self.ax.grid(True, alpha=0.22)
        self.ax.set_xlabel("Raman shift / x-axis", fontsize=12)
        self.ax.set_ylabel("Intensity", fontsize=12)
        self.ax.tick_params(labelsize=11)

        if spectrum is None:
            self.ax.set_title("Open Raman spectra", fontsize=13)
            self.canvas.draw_idle()
            return

        if self.show_original.get():
            self.raw_artist = self.ax.plot(
                spectrum.x,
                spectrum.y_raw,
                color="#9ca3af",
                linewidth=1.0,
                alpha=0.75,
                label="Raw",
            )[0]

        self.work_artist = self.ax.plot(
            spectrum.x,
            spectrum.y_work,
            color="#111827",
            linewidth=1.25,
            label="Current",
        )[0]

        if self.show_baseline.get() and self._last_baseline is not None:
            self.baseline_artist = self.ax.plot(
                spectrum.x,
                self._last_baseline,
                color="#ef4444",
                linewidth=1.1,
                linestyle="--",
                label="Last baseline",
            )[0]

        if self.pick_points:
            px, py = zip(*self.pick_points)
            self.point_artist = self.ax.scatter(px, py, color="#ff0011", s=36, zorder=5, label="Baseline points")

        self.ax.set_title(spectrum.path.name, fontsize=13)
        self.ax.legend(loc="upper right", fontsize=10)
        if reset_view:
            self.ax.relim()
            self.ax.autoscale_view()

        self._recreate_cursors()
        self.canvas.draw_idle()

    def _on_plot_press(self, event: object) -> None:
        if event.inaxes != self.ax or event.xdata is None:
            return

        if self.pick_mode.get():
            if self.snap_points_to_spectrum.get():
                y_value = self._nearest_y(event.xdata)
                point_source = "spectrum"
            else:
                y_value = float(event.ydata) if event.ydata is not None else None
                point_source = "free"
            if y_value is not None:
                self._push_undo()
                self.pick_points.append((float(event.xdata), y_value))
                self.refresh_plot()
                self.status_text.set(f"Added {point_source} baseline point at x={event.xdata:.2f}.")
            return

        cursor = self._nearest_cursor(event.xdata)
        if cursor is not None:
            self._drag_start_snapshot = self._capture_undo_snapshot()
            self.dragging_cursor = cursor

    def _on_plot_motion(self, event: object) -> None:
        if self.dragging_cursor is None or event.inaxes != self.ax or event.xdata is None:
            return
        self.dragging_cursor.x_value = float(event.xdata)
        self._redraw_cursor(self.dragging_cursor)
        self._refresh_cursor_list()
        selection = self.cursor_list.curselection()
        if selection and self.cursor_lines[selection[0]] is self.dragging_cursor:
            self.cursor_x.set(f"{self.dragging_cursor.x_value:.3f}")
        self.canvas.draw_idle()

    def _on_plot_release(self, _event: object) -> None:
        if self.dragging_cursor is not None and self._drag_start_snapshot is not None:
            self.undo_stack.append(self._drag_start_snapshot)
            if len(self.undo_stack) > 80:
                self.undo_stack.pop(0)
            self._drag_start_snapshot = None
        self.dragging_cursor = None

    def _on_scroll_zoom(self, event: object) -> None:
        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            return
        scale = 0.82 if event.button == "up" else 1.22
        self._zoom_plot(scale, float(event.xdata), float(event.ydata))

    def _nearest_y(self, x_value: float) -> float | None:
        spectrum = self.current
        if spectrum is None:
            return None
        index = int(np.argmin(np.abs(spectrum.x - x_value)))
        return float(spectrum.y_work[index])

    def _nearest_cursor(self, x_value: float) -> CursorLine | None:
        if not self.cursor_lines:
            return None
        x_min, x_max = self.ax.get_xlim()
        tolerance = abs(x_max - x_min) * 0.015
        nearest = min(self.cursor_lines, key=lambda cursor: abs(cursor.x_value - x_value))
        if abs(nearest.x_value - x_value) <= tolerance:
            return nearest
        return None

    def _recreate_cursors(self) -> None:
        existing = [(cursor.label, cursor.color, cursor.x_value) for cursor in self.cursor_lines]
        self.cursor_lines.clear()
        for label, color, x_value in existing:
            artist = self.ax.axvline(x_value, color=color, linewidth=1.6, picker=6)
            text = self.ax.text(
                x_value,
                0.98,
                f"{label}: {x_value:.2f}",
                color=color,
                rotation=90,
                va="top",
                ha="right",
                transform=self.ax.get_xaxis_transform(),
            )
            self.cursor_lines.append(CursorLine(label, color, x_value, artist, text))
        self._refresh_cursor_list()

    def _redraw_cursor(self, cursor: CursorLine) -> None:
        cursor.artist.set_xdata([cursor.x_value, cursor.x_value])
        cursor.text.set_x(cursor.x_value)
        cursor.text.set_text(f"{cursor.label}: {cursor.x_value:.2f}")

    def _refresh_cursor_list(self) -> None:
        selected = self.cursor_list.curselection()
        self.cursor_list.delete(0, tk.END)
        for cursor in self.cursor_lines:
            self.cursor_list.insert(tk.END, f"{cursor.label}  x={cursor.x_value:.2f}")
        if selected and selected[0] < len(self.cursor_lines):
            self.cursor_list.selection_set(selected[0])

    def _renumber_cursors(self) -> None:
        for index, cursor in enumerate(self.cursor_lines, start=1):
            cursor.label = f"C{index}"
            self._redraw_cursor(cursor)
        self._refresh_cursor_list()

    def _on_cursor_selected(self, _event: object) -> None:
        selection = self.cursor_list.curselection()
        if selection:
            cursor = self.cursor_lines[selection[0]]
            self.cursor_label.set(cursor.label)
            self.cursor_x.set(f"{cursor.x_value:.3f}")
        self._highlight_selected_cursor()

    def _highlight_selected_cursor(self) -> None:
        selection = self.cursor_list.curselection()
        selected_index = selection[0] if selection else None
        for index, cursor in enumerate(self.cursor_lines):
            cursor.artist.set_linewidth(2.5 if index == selected_index else 1.6)
        self.canvas.draw_idle()

    def _update_pick_status(self) -> None:
        if self.pick_mode.get():
            self.status_text.set("Manual point mode enabled. Click the spectrum to add baseline anchor points.")
        else:
            self.status_text.set("Manual point mode disabled. Cursor dragging is active.")


def main() -> None:
    app = RamanEditor()
    app.mainloop()


if __name__ == "__main__":
    main()
