"""Dark desktop workspace for comparing handwritten-digit predictions."""

from concurrent.futures import Future, ThreadPoolExecutor
from io import BytesIO
import tkinter as tk
from tkinter import filedialog, ttk

from PIL import Image, ImageDraw, ImageOps

from .inference import AUGMENTATION, MODELS, ModelResult, ModelStore

BG = "#0e1422"
PANEL = "#121c2d"
CARD = "#19263a"
EDGE = "#293a52"
INK = "#070b13"
TEXT = "#eef5ff"
MUTED = "#a5b9d4"
TEAL = "#18b8aa"
CYAN = "#66deef"
ERROR = "#ffa0a9"
SIZE = 300


class DigitStudio:
    """Coordinate the drawing tools, model selection and results."""

    def __init__(self) -> None:
        """Build the desktop window and initialize the model catalog."""
        self.root = tk.Tk()
        self.root.title("Digit Studio | Nhận dạng chữ số viết tay")
        self.root.geometry("1260x800")
        self.root.minsize(950, 660)
        self.root.configure(bg=BG)
        self.store = ModelStore()
        self.issues = {name: self.store.issue(name) for name in MODELS}
        self.selected = {name: tk.BooleanVar(value=not issue) for name, issue in self.issues.items()}
        self.worker = ThreadPoolExecutor(max_workers=1)
        self.future: Future[tuple[Image.Image, list[ModelResult]]] | None = None
        self.drawing = Image.new("L", (SIZE, SIZE))
        self.uploaded: Image.Image | None = None
        self.history: list[Image.Image] = []
        self.last_point: tuple[int, int] | None = None
        self.mode = "draw"
        self.eraser = False
        self.canvas_photo: tk.PhotoImage | None = None
        self.preview_photo: tk.PhotoImage | None = None
        self.brush = tk.IntVar(value=21)
        self.status = tk.StringVar(value="Sẵn sàng · Vẽ hoặc tải ảnh để bắt đầu.")
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _label(self, parent: tk.Misc, text: str, bg: str, *, color: str = TEXT,
               size: int = 10, bold: bool = False) -> tk.Label:
        """Create a label with the shared visual palette."""
        return tk.Label(parent, text=text, bg=bg, fg=color,
                        font=("TkDefaultFont", size, "bold" if bold else "normal"))

    def _panel(self, parent: tk.Misc, bg: str = PANEL) -> tk.Frame:
        """Create a bordered section or result card."""
        return tk.Frame(parent, bg=bg, highlightbackground=EDGE, highlightthickness=1,
                        padx=14, pady=11)

    def _build(self) -> None:
        """Arrange the main header and the input and comparison columns."""
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Tool.TButton", background=EDGE, foreground=TEXT, padding=(9, 6))
        style.map("Tool.TButton", background=[("active", "#364f6b")])
        style.configure("Run.TButton", background=TEAL, foreground=INK, padding=(10, 9),
                        font=("TkDefaultFont", 11, "bold"))
        style.map("Run.TButton", background=[("disabled", EDGE), ("active", "#4bd5c5")],
                  foreground=[("disabled", MUTED)])
        style.configure("Model.TCheckbutton", background=PANEL, foreground=TEXT, padding=(4, 4))
        style.map("Model.TCheckbutton", background=[("active", CARD)],
                  foreground=[("disabled", MUTED)])
        style.configure("Score.Horizontal.TProgressbar", troughcolor=EDGE, background=TEAL,
                        bordercolor=EDGE, lightcolor=TEAL, darkcolor=TEAL, thickness=12)
        style.configure("Results.Vertical.TScrollbar", troughcolor=PANEL, background=EDGE,
                        bordercolor=PANEL, arrowcolor=TEXT)

        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=16, pady=(12, 10))
        self._label(header, "OFFLINE · DESKTOP AI", BG, color=CYAN, size=9, bold=True).pack(anchor="w")
        self._label(header, "Digit Studio", BG, size=24, bold=True).pack(side="left")
        available = sum(not issue for issue in self.issues.values())
        self._label(header, f"{available}/{len(MODELS)} tệp mô hình có dữ liệu   ·   MNIST 28 × 28",
                    BG, color=MUTED, size=9).pack(side="right")

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=16)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)
        left = self._panel(body)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        right = self._panel(body)
        right.grid(row=0, column=1, sticky="nsew")
        self._build_input(left)
        self._build_comparison(right)
        tk.Label(self.root, textvariable=self.status, bg=BG, fg=MUTED, anchor="w").pack(
            fill="x", padx=17, pady=(6, 7))

    def _build_input(self, panel: tk.Frame) -> None:
        """Add the drawing canvas, upload action and stroke controls."""
        self._label(panel, "01   Dữ liệu đầu vào", PANEL, size=13, bold=True).pack(anchor="w")
        self._label(panel, "Vẽ một chữ số hoặc mở ảnh trên thiết bị.", PANEL,
                    color=MUTED, size=9).pack(anchor="w", pady=(3, 8))
        tabs = tk.Frame(panel, bg=PANEL)
        tabs.pack(fill="x", pady=(0, 8))
        ttk.Button(tabs, text="✎  Vẽ số", style="Tool.TButton",
                   command=self._show_drawing).pack(side="left", padx=(0, 5))
        ttk.Button(tabs, text="▣  Tải ảnh", style="Tool.TButton",
                   command=self._open_image).pack(side="left")

        self.canvas = tk.Canvas(panel, width=SIZE, height=SIZE, bg=INK,
                                highlightthickness=1, highlightbackground=EDGE, cursor="crosshair")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._start_stroke)
        self.canvas.bind("<B1-Motion>", self._stroke)
        self.canvas.bind("<ButtonRelease-1>", self._end_stroke)

        width = tk.Frame(panel, bg=PANEL)
        width.pack(fill="x", pady=(6, 4))
        self._label(width, "Cỡ nét", PANEL, color=MUTED, size=9).pack(side="left")
        self.brush_text = self._label(width, "21 px", PANEL, color=MUTED, size=9)
        self.brush_text.pack(side="right")
        ttk.Scale(width, from_=4, to=42, variable=self.brush,
                  command=self._brush_changed).pack(side="left", fill="x", expand=True, padx=8)

        controls = tk.Frame(panel, bg=PANEL)
        controls.pack(fill="x", pady=(3, 5))
        self.erase_button = ttk.Button(controls, text="Tẩy", style="Tool.TButton", command=self._toggle_eraser)
        self.erase_button.pack(side="left", fill="x", expand=True)
        ttk.Button(controls, text="Hoàn tác", style="Tool.TButton",
                   command=self._undo).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(controls, text="Xóa hết", style="Tool.TButton",
                   command=self._clear).pack(side="left", fill="x", expand=True)
        self._label(panel, "Nét trắng trên nền tối · Mỗi lần một chữ số", PANEL,
                    color=MUTED, size=9).pack(anchor="w")
        self._display(self.drawing)

    def _build_comparison(self, panel: tk.Frame) -> None:
        """Add multi-model selection, preprocessing preview and scrollable results."""
        self._label(panel, "02   Chọn mô hình", PANEL, size=13, bold=True).pack(anchor="w")
        self._label(panel, "Trọng số được đọc từ saved_models/.", PANEL, color=MUTED,
                    size=9).pack(anchor="w", pady=(3, 5))
        grid = tk.Frame(panel, bg=PANEL)
        grid.pack(fill="x")
        grid.grid_columnconfigure((0, 1), weight=1)
        self.checks = []
        for index, (name, variable) in enumerate(self.selected.items()):
            issue = self.issues[name]
            label = name if name.startswith("CNN ·") else f"{name} · {AUGMENTATION[name]}"
            if issue:
                label = f"{label} ({issue})"
            button = ttk.Checkbutton(grid, text=label, variable=variable,
                                     style="Model.TCheckbutton", command=self._invalidate)
            button.grid(row=index // 2, column=index % 2, sticky="w")
            if issue:
                button.state(["disabled"])
            self.checks.append((name, button))

        actions = tk.Frame(panel, bg=PANEL)
        actions.pack(fill="x", pady=(8, 10))
        self.run_button = ttk.Button(actions, text="✦  Nhận dạng chữ số", style="Run.TButton",
                                     command=self._recognize)
        self.run_button.pack(side="left", fill="x", expand=True)
        self.select_button = ttk.Button(actions, text="Chọn tất cả", style="Tool.TButton",
                                        command=self._select_all)
        self.select_button.pack(side="right", padx=(8, 0))

        self._label(panel, "03   Kết quả dự đoán", PANEL, size=13, bold=True).pack(anchor="w")
        preview_line = tk.Frame(panel, bg=PANEL)
        preview_line.pack(fill="x", pady=7)
        self._label(preview_line, "Ảnh sau tiền xử lý", PANEL, color=MUTED, size=9).pack(side="left")
        self.preview = tk.Canvas(preview_line, width=64, height=64, bg=INK,
                                 highlightthickness=1, highlightbackground=EDGE)
        self.preview.pack(side="left", padx=10)

        result_area = tk.Frame(panel, bg=PANEL)
        result_area.pack(fill="both", expand=True)
        self.scroll = tk.Canvas(result_area, bg=PANEL, highlightthickness=0)
        self.scroll.pack(side="left", fill="both", expand=True)
        bar = ttk.Scrollbar(result_area, orient="vertical", command=self.scroll.yview,
                            style="Results.Vertical.TScrollbar")
        bar.pack(side="right", fill="y")
        self.scroll.configure(yscrollcommand=bar.set)
        self.results = tk.Frame(self.scroll, bg=PANEL)
        window_id = self.scroll.create_window(0, 0, anchor="nw", window=self.results)
        self.results.bind("<Configure>", lambda _: self.scroll.configure(scrollregion=self.scroll.bbox("all")))
        self.scroll.bind("<Configure>", lambda event: self.scroll.itemconfigure(window_id, width=event.width))
        for event_name in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.root.bind(event_name, self._scroll_results)
        self._invalidate()

    def _scroll_results(self, event: tk.Event) -> None:
        """Scroll when the pointer is over the prediction cards."""
        x, y = self.scroll.winfo_rootx(), self.scroll.winfo_rooty()
        if x <= event.x_root < x + self.scroll.winfo_width() and y <= event.y_root < y + self.scroll.winfo_height():
            up = event.num == 4 or (event.num != 5 and event.delta > 0)
            self.scroll.yview_scroll(-2 if up else 2, "units")

    def _brush_changed(self, value: str) -> None:
        """Display the current brush width in pixels."""
        self.brush_text.configure(text=f"{round(float(value))} px")

    def _photo_image(self, image: Image.Image) -> tk.PhotoImage:
        """Load PNG bytes using Tk's native decoder."""
        with BytesIO() as buffer:
            image.save(buffer, format="PNG")
            return tk.PhotoImage(data=buffer.getvalue(), format="png", master=self.root)

    def _display(self, image: Image.Image) -> None:
        """Show a fitted copy of the drawing or uploaded image."""
        view = image.copy()
        view.thumbnail((SIZE, SIZE), Image.Resampling.LANCZOS)
        self.canvas_photo = self._photo_image(view)
        self.canvas.delete("all")
        self.canvas.create_image(SIZE // 2, SIZE // 2, image=self.canvas_photo)

    def _invalidate(self) -> None:
        """Clear results when the image or model selection changes."""
        for widget in self.results.winfo_children():
            widget.destroy()
        self.preview.delete("all")
        self.preview_photo = None
        self._label(self.results, "Kết quả của từng mô hình sẽ hiển thị ở đây.", PANEL,
                    color=MUTED).pack(anchor="w", pady=8)
        self.status.set("Sẵn sàng · Chọn mô hình và bấm Nhận dạng chữ số.")

    def _show_drawing(self) -> None:
        """Return to the current drawing."""
        if self.future is not None:
            return
        self.mode = "draw"
        self._display(self.drawing)
        self._invalidate()

    def _open_image(self) -> None:
        """Load and preview a single-digit image from the device."""
        if self.future is not None:
            return
        path = filedialog.askopenfilename(filetypes=[
            ("Ảnh", "*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff"), ("Tất cả", "*"),
        ])
        if not path:
            return
        try:
            with Image.open(path) as source:
                self.uploaded = ImageOps.exif_transpose(source).convert("RGBA")
        except (OSError, ValueError, Image.DecompressionBombError) as error:
            self.status.set(f"Không mở được ảnh · {error}")
            return
        self.mode = "upload"
        self._display(self.uploaded)
        self._invalidate()

    def _remember(self) -> None:
        """Save the drawing before a stroke or clear operation."""
        self.history.append(self.drawing.copy())
        if len(self.history) > 30:
            self.history.pop(0)

    def _start_stroke(self, event: tk.Event) -> None:
        """Start a pen or eraser stroke and record its undo state."""
        if self.future is not None:
            return
        self.mode = "draw"
        self._remember()
        self._invalidate()
        self.last_point = (event.x, event.y)
        self._stroke(event)

    def _stroke(self, event: tk.Event) -> None:
        """Connect the cursor to the previous point with a round stroke."""
        if self.last_point is None or self.future is not None:
            return
        point = (event.x, event.y)
        width = self.brush.get()
        radius = width // 2
        value = 0 if self.eraser else 255
        pen = ImageDraw.Draw(self.drawing)
        pen.line((*self.last_point, *point), fill=value, width=width)
        pen.ellipse((point[0] - radius, point[1] - radius, point[0] + radius,
                     point[1] + radius), fill=value)
        self.last_point = point
        self._display(self.drawing)

    def _end_stroke(self, event: tk.Event) -> None:
        """Finish the current pointer stroke."""
        self.last_point = None

    def _toggle_eraser(self) -> None:
        """Toggle between the white pen and the eraser."""
        if self.future is not None:
            return
        self.eraser = not self.eraser
        self.erase_button.configure(text="Bút vẽ" if self.eraser else "Tẩy")
        if self.mode != "draw":
            self._show_drawing()

    def _undo(self) -> None:
        """Restore the drawing state before the most recent edit."""
        if self.future is None and self.history:
            self.drawing = self.history.pop()
            self._show_drawing()

    def _clear(self) -> None:
        """Clear the input and allow the drawing to be restored with undo."""
        if self.future is not None:
            return
        self._remember()
        self.drawing = Image.new("L", (SIZE, SIZE))
        self.uploaded = None
        self._show_drawing()

    def _select_all(self) -> None:
        """Select every model with a nonempty checkpoint."""
        for name, variable in self.selected.items():
            variable.set(not self.issues[name])
        self._invalidate()

    def _recognize(self) -> None:
        """Run the selected models in a background worker."""
        names = tuple(name for name, value in self.selected.items() if value.get())
        if not names:
            self.status.set("Hãy chọn ít nhất một mô hình.")
            return
        image = self.drawing if self.mode == "draw" else self.uploaded
        if image is None:
            return
        self._invalidate()
        self.status.set(f"Đang dự đoán với {len(names)} mô hình…")
        self._set_busy(True)
        self.future = self.worker.submit(self.store.predict, image.copy(), names)
        self.root.after(50, self._poll)

    def _set_busy(self, busy: bool) -> None:
        """Lock comparison controls while predictions are in progress."""
        state = "disabled" if busy else "normal"
        self.run_button.configure(state=state)
        self.select_button.configure(state=state)
        for name, button in self.checks:
            button.configure(state="disabled" if self.issues[name] else state)

    def _poll(self) -> None:
        """Transfer the completed predictions to the Tk main thread."""
        if self.future is None:
            return
        if not self.future.done():
            self.root.after(50, self._poll)
            return
        try:
            preview, results = self.future.result()
        except Exception as error:
            self.status.set(str(error))
        else:
            self._show_results(preview, results)
        finally:
            self.future = None
            self._set_busy(False)

    def _show_results(self, preview: Image.Image, results: list[ModelResult]) -> None:
        """Display the prepared digit and one card per selected model."""
        self.preview_photo = self._photo_image(preview.resize((56, 56), Image.Resampling.NEAREST))
        self.preview.create_image(32, 32, image=self.preview_photo)
        for widget in self.results.winfo_children():
            widget.destroy()
        for result in results:
            self._result_card(result)
        self.scroll.yview_moveto(0)
        successes = sum(result.digit is not None for result in results)
        self.status.set(f"Hoàn tất · {successes}/{len(results)} mô hình dự đoán thành công")

    def _result_card(self, result: ModelResult) -> None:
        """Render a model label, prediction, and up to three probability bars."""
        card = self._panel(self.results, CARD)
        card.pack(fill="x", pady=(0, 7), padx=(0, 4))
        heading = tk.Frame(card, bg=CARD)
        heading.pack(fill="x")
        title = result.name if result.name.startswith("CNN ·") else f"{result.name} · {AUGMENTATION[result.name]}"
        self._label(heading, title, CARD, bold=True).pack(side="left")
        self._label(heading, str(result.digit) if result.digit is not None else "—",
                    CARD, color=CYAN, size=25, bold=True).pack(side="right")
        if result.error:
            label = self._label(card, result.error, CARD, color=ERROR, size=9)
            label.configure(wraplength=425, justify="left")
            label.pack(anchor="w")
            return
        if not result.probabilities:
            self._label(card, "Mô hình trả về nhãn dự đoán.", CARD, color=MUTED, size=9).pack(anchor="w")
            return
        predicted = dict(result.probabilities).get(result.digit)
        if predicted is not None:
            self._label(card, f"Xác suất lớp dự đoán (theo mô hình) · {predicted:.1%}",
                        CARD, color=MUTED, size=9).pack(anchor="w", pady=(0, 4))
        for digit, probability in result.probabilities[:3]:
            row = tk.Frame(card, bg=CARD)
            row.pack(fill="x", pady=2)
            self._label(row, str(digit), CARD, size=9).pack(side="left", padx=(0, 9))
            percentage = self._label(row, f"{probability:.1%}", CARD, size=9)
            percentage.configure(width=7, anchor="e")
            percentage.pack(side="right")
            ttk.Progressbar(row, style="Score.Horizontal.TProgressbar",
                            value=100 * probability).pack(side="left", fill="x", expand=True)

    def _close(self) -> None:
        """Close the desktop window and release the worker."""
        self.worker.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()

    def run(self) -> None:
        """Start the Tk event loop."""
        self.root.mainloop()
