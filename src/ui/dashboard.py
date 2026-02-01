import customtkinter as ctk
from PIL import Image, ImageTk

# -------------------------------------------------
# UI CONFIG
# -------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class FireDetectionDashboard(ctk.CTk):
    """
    UI layer only:
    - Displays video
    - Displays logs
    - Emits user actions to controller
    """

    def __init__(self, event_logger=None):
        super().__init__()

        self.title("Intelligent Fire Detection System")
        self.geometry("1200x650")
        self.resizable(True, True)

        # External dependencies
        self.event_logger = event_logger

        # Callbacks (wired in main.py)
        self.on_start_stream = None
        self.on_deactivate_buzzer = None
        self.on_stop_system = None

        # UI state
        self.alert_active = False
        self.system_running = True

        # Build UI
        self._build_main_layout()

        # Load previous logs
        self.after(200, self._load_existing_logs)

        # Auto-start camera
        self.after(300, self._auto_start_camera)

    # -------------------------------------------------
    # MAIN LAYOUT
    # -------------------------------------------------
    def _build_main_layout(self):
        header = ctk.CTkLabel(
            self,
            text="INTELLIGENT FIRE DETECTION SYSTEM",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        header.pack(pady=10)

        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=15, pady=10)

        self.main_container.grid_columnconfigure(0, weight=4)
        self.main_container.grid_columnconfigure(1, weight=3)

        self._build_left_panel()
        self._build_right_panel()

    # -------------------------------------------------
    # LEFT PANEL (VIDEO + INPUT)
    # -------------------------------------------------
    def _build_left_panel(self):
        self.left_panel = ctk.CTkFrame(self.main_container)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            self.left_panel,
            text="Live Video Feed",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=5)

        self.video_label = ctk.CTkLabel(
            self.left_panel,
            text="Starting camera...",
            width=620,
            height=305,
            fg_color="black",
            corner_radius=10
        )
        self.video_label.pack(padx=10, pady=10)

        ctk.CTkLabel(
            self.left_panel,
            text="Video Input Source",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 5))

        self.source_option = ctk.CTkOptionMenu(
            self.left_panel,
            values=["Camera", "Local Video", "URL"],
            command=self._on_source_change
        )
        self.source_option.pack(pady=5)

        self.source_entry = ctk.CTkEntry(
            self.left_panel,
            placeholder_text="File path or URL",
            width=400
        )
        self.source_entry.pack(pady=5)

        self.start_button = ctk.CTkButton(
            self.left_panel,
            text="Start Stream",
            command=self._start_stream_clicked
        )
        self.start_button.pack(pady=10)

        self._on_source_change("Camera")

    # -------------------------------------------------
    # RIGHT PANEL (STATUS + LOG + ACTIONS)
    # -------------------------------------------------
    def _build_right_panel(self):
        self.right_panel = ctk.CTkFrame(self.main_container)
        self.right_panel.grid(row=0, column=1, sticky="nsew")

        status_frame = ctk.CTkFrame(self.right_panel)
        status_frame.pack(fill="x", padx=10, pady=10)

        self.system_status_label = ctk.CTkLabel(
            status_frame,
            text="System: RUNNING",
            text_color="green",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.system_status_label.pack(anchor="w", padx=10)

        self.alert_status_label = ctk.CTkLabel(
            status_frame,
            text="Alert: INACTIVE",
            text_color="gray",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.alert_status_label.pack(anchor="w", padx=10)

        ctk.CTkLabel(
            self.right_panel,
            text="Detection Events Log",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 5))

        self.event_log = ctk.CTkTextbox(
            self.right_panel,
            height=280,
            state="disabled"
        )
        self.event_log.pack(fill="x", padx=10)

        action_frame = ctk.CTkFrame(self.right_panel)
        action_frame.pack(fill="x", padx=10, pady=15)

        self.deactivate_button = ctk.CTkButton(
            action_frame,
            text="Deactivate Buzzer",
            fg_color="darkred",
            hover_color="red",
            command=self._deactivate_buzzer_clicked
        )
        self.deactivate_button.pack(fill="x", pady=5)

        self.stop_button = ctk.CTkButton(
            action_frame,
            text="Stop System",
            fg_color="gray",
            command=self._stop_system_clicked
        )
        self.stop_button.pack(fill="x", pady=5)

    # -------------------------------------------------
    # VIDEO SOURCE LOGIC
    # -------------------------------------------------
    def _on_source_change(self, source_type):
        if source_type == "Camera":
            self.source_entry.configure(state="disabled")
            self.start_button.configure(state="disabled")
        else:
            self.source_entry.configure(state="normal")
            self.start_button.configure(state="normal")

    def _auto_start_camera(self):
        if self.on_start_stream:
            self.on_start_stream("Camera", "0")

    def _start_stream_clicked(self):
        if not self.on_start_stream:
            return

        source_type = self.source_option.get()
        source_value = self.source_entry.get().strip()

        if not source_value:
            return

        self.on_start_stream(source_type, source_value)

    # -------------------------------------------------
    # DISPLAY METHODS (NO LOGIC)
    # -------------------------------------------------
    def update_video_frame(self, frame_bgr):
        frame_rgb = frame_bgr[:, :, ::-1]
        img = Image.fromarray(frame_rgb).resize((620, 305))
        imgtk = ImageTk.PhotoImage(image=img)

        self.video_label.configure(image=imgtk, text="")
        self.video_label.image = imgtk

    def display_log(self, timestamp, message):
        self.event_log.configure(state="normal")
        self.event_log.insert("end", f"[{timestamp}] {message}\n")
        self.event_log.see("end")
        self.event_log.configure(state="disabled")

    def fire_detected(self, confidence):
        self.alert_active = True
        self.alert_status_label.configure(
            text="Alert: FIRE DETECTED",
            text_color="red"
        )

    def clear_alert(self):
        self.alert_active = False
        self.alert_status_label.configure(
            text="Alert: INACTIVE",
            text_color="gray"
        )

    # -------------------------------------------------
    # USER ACTIONS (EVENT EMISSION)
    # -------------------------------------------------
    def _deactivate_buzzer_clicked(self):
        if self.on_deactivate_buzzer:
            self.on_deactivate_buzzer()

    def _stop_system_clicked(self):
        self.system_running = False
        self.system_status_label.configure(
            text="System: STOPPED",
            text_color="red"
        )

        if self.on_stop_system:
            self.on_stop_system()

    # -------------------------------------------------
    # LOAD LOGS
    # -------------------------------------------------
    def _load_existing_logs(self):
        if not self.event_logger:
            return

        for ts, msg in self.event_logger.read_all(limit=100):
            self.display_log(ts, msg)

    # -------------------------------------------------
    # THREAD-SAFE ENTRY POINTS
    # -------------------------------------------------
    def update_frame_from_thread(self, frame):
        self.after(0, lambda: self.update_video_frame(frame))

    def trigger_fire_from_thread(self, confidence):
        self.after(0, lambda: self.fire_detected(confidence))
