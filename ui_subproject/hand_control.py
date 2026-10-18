#!/usr/bin/env python3
"""Simple RH56 dexterous-hand control UI (tkinter + pyserial)."""

from __future__ import annotations

import struct
import sys
import tkinter as tk
from tkinter import ttk

import serial
from PIL import ImageTk
from serial import SerialException

from hand_art import FINGER_X, HAND_HEIGHT, HAND_WIDTH, build_hand_frames, index_pose

BAUD = 115200
HEADER = bytes((0xEB, 0x90))
WRITE_FLAG = 0x12
READ_FLAG = 0x11
ANGLE_SET_BASE = 1486  # ANGLE_SET(0); 2 bytes per DOF
FORCE_SET_BASE = 1498  # FORCE_SET(0); 2 bytes per DOF
SPEED_SET_BASE = 1522  # SPEED_SET(0); 2 bytes per DOF
FORCE_ACT_BASE = 1582  # FORCE_ACT(0); 2 bytes per DOF
INDEX_FORCE_DOF = 3
THUMB_FORCE_DOF = 4
ANGLE_MIN = 0
ANGLE_MAX = 1000
SEND_DELAY_MS = 40
POLL_MS = 200
THUMB_ROTATE_DOF = 5
INDEX_DOF = 3
LEVELS = (1, 2, 3, 4, 5)
# FORCE_SET / SPEED_SET range is 0–1000. Five radio steps, evenly spaced.
LEVEL_VALUES = {level: level * 200 for level in LEVELS}

BEND_FINGERS = (
    ("Little", 0),
    ("Ring", 1),
    ("Middle", 2),
    ("Index", 3),
    ("Thumb bend", 4),
)
ALL_DOFS = BEND_FINGERS + (("Thumb rotate", THUMB_ROTATE_DOF),)

# Shift sliders off the bone centre into the gap beside each finger.
SLIDER_X_SHIFT = {
    0: -0.042,  # little: left / outer
    1: -0.038,  # ring
    2: -0.038,  # middle
    3: -0.038,  # index
    4: 0.048,  # thumb: right / outer
}

DEFAULT_PORT = "COM3" if sys.platform == "win32" else "/dev/ttyUSB0"


def checksum(payload: bytes) -> int:
    """Low byte of the sum of all frame bytes after the header."""
    return sum(payload) & 0xFF


def write_register_frame(hand_id: int, address: int, data: bytes) -> bytes:
    payload = bytes(
        (
            hand_id,
            len(data) + 3,
            WRITE_FLAG,
            address & 0xFF,
            (address >> 8) & 0xFF,
        )
    ) + data
    return HEADER + payload + bytes((checksum(payload),))


def read_register_frame(hand_id: int, address: int, length: int) -> bytes:
    payload = bytes(
        (
            hand_id,
            0x04,
            READ_FLAG,
            address & 0xFF,
            (address >> 8) & 0xFF,
            length,
        )
    )
    return HEADER + payload + bytes((checksum(payload),))


def angle_set_frame(hand_id: int, dof: int, angle: int) -> bytes:
    address = ANGLE_SET_BASE + dof * 2
    return write_register_frame(hand_id, address, struct.pack("<h", angle))


def angle_set_all_frame(hand_id: int, angles: list[int]) -> bytes:
    data = b"".join(struct.pack("<h", angle) for angle in angles)
    return write_register_frame(hand_id, ANGLE_SET_BASE, data)


def force_set_frame(hand_id: int, dof: int, force: int) -> bytes:
    address = FORCE_SET_BASE + dof * 2
    return write_register_frame(hand_id, address, struct.pack("<h", force))


def speed_set_all_frame(hand_id: int, speed: int) -> bytes:
    data = struct.pack("<6h", *(speed,) * 6)
    return write_register_frame(hand_id, SPEED_SET_BASE, data)


def slider_x(dof: int) -> int:
    frac = FINGER_X[dof] + SLIDER_X_SHIFT.get(dof, 0.0)
    return int(HAND_WIDTH * max(0.04, min(0.96, frac)))


class TipMeter:
    """Horizontal bar for a live FORCE_ACT fingertip reading (0–1000)."""

    def __init__(self, parent: ttk.Frame, title: str) -> None:
        self.frame = ttk.Frame(parent)
        ttk.Label(self.frame, text=title).pack(anchor="w")
        self.canvas = tk.Canvas(
            self.frame, width=210, height=22, bg="#1a1a1a", highlightthickness=0
        )
        self.canvas.pack(fill="x", pady=(2, 0))
        self.bar = self.canvas.create_rectangle(0, 0, 0, 22, fill="#4a4", outline="")
        self.value = ttk.Label(self.frame, text="0")
        self.value.pack(anchor="e")

    def set_value(self, raw: int) -> None:
        value = max(0, min(ANGLE_MAX, int(raw)))
        width = int(210 * value / ANGLE_MAX)
        self.canvas.coords(self.bar, 0, 0, width, 22)
        if value < 400:
            color = "#4a4"
        elif value < 750:
            color = "#cc3"
        else:
            color = "#c44"
        self.canvas.itemconfigure(self.bar, fill=color)
        self.value.configure(text=str(value))


class HandApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("RH56 Hand Control")
        self.resizable(False, False)

        self.ser: serial.Serial | None = None
        self._send_jobs: dict[int, str] = {}
        self._poll_job: str | None = None
        self._resetting = False
        self._angles = {dof: ANGLE_MAX for _, dof in ALL_DOFS}
        self._forces = {dof: LEVEL_VALUES[3] for _, dof in BEND_FINGERS}
        self._speed = LEVEL_VALUES[3]
        self._index_pose = 0
        self._hand_photos: list[ImageTk.PhotoImage] = []
        self._hand_item: int | None = None

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.close_app)

    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=(10, 8, 10, 4))
        top.pack(fill="x")

        ttk.Label(top, text="RH56 Hand Control").pack(side="left")
        ttk.Button(top, text="Reset", command=self.reset_open, width=8).pack(
            side="right"
        )

        conn = ttk.Frame(self, padding=(10, 4, 10, 4))
        conn.pack(fill="x")

        ttk.Label(conn, text="Port").grid(row=0, column=0, sticky="w")
        self.port_var = tk.StringVar(value=DEFAULT_PORT)
        self.port_entry = ttk.Entry(conn, textvariable=self.port_var, width=18)
        self.port_entry.grid(row=0, column=1, padx=(6, 12))

        ttk.Label(conn, text="Hand ID").grid(row=0, column=2, sticky="w")
        self.hand_id_var = tk.StringVar(value="5")
        ttk.Entry(conn, textvariable=self.hand_id_var, width=5).grid(
            row=0, column=3, padx=(6, 12)
        )

        self.connect_btn = ttk.Button(conn, text="Connect", command=self.toggle_connect)
        self.connect_btn.grid(row=0, column=4)

        self.status_var = tk.StringVar(value="Disconnected")
        ttk.Label(self, textvariable=self.status_var, padding=(10, 0, 10, 4)).pack(
            anchor="w"
        )

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        left = ttk.Frame(body)
        left.pack(side="left", fill="y")
        right = ttk.Frame(body)
        right.pack(side="left", fill="y", padx=(12, 0))

        pos = ttk.LabelFrame(left, text="Finger position", padding=(10, 6, 10, 10))
        pos.pack(fill="x")

        self.slider_vars: dict[int, tk.IntVar] = {}
        self.scales: dict[int, ttk.Scale] = {}
        self._value_items: dict[int, int] = {}

        try:
            pil_frames = build_hand_frames()
        except (FileNotFoundError, OSError) as exc:
            pil_frames = []
            self.status_var.set(f"Hand art not loaded: {exc}")

        if pil_frames:
            self._build_hand_sliders(pos, pil_frames)
        else:
            self._build_plain_sliders(pos)

        ttk.Label(
            pos,
            text="Angle 0–1000  ·  top = open  ·  bottom = closed",
            foreground="#666",
        ).pack(pady=(8, 6))

        rotate = ttk.Frame(pos)
        rotate.pack(fill="x", pady=(2, 0))
        ttk.Label(rotate, text="Thumb rotate").pack(side="left")
        ttk.Label(rotate, text="0", foreground="#666").pack(side="left", padx=(12, 4))

        rotate_var = tk.IntVar(value=ANGLE_MAX)
        self.slider_vars[THUMB_ROTATE_DOF] = rotate_var
        rotate_scale = ttk.Scale(
            rotate,
            from_=ANGLE_MIN,
            to=ANGLE_MAX,
            orient="horizontal",
            length=280,
            variable=rotate_var,
            command=lambda _v: self._on_slider(THUMB_ROTATE_DOF),
            state="normal",
        )
        rotate_scale.pack(side="left", fill="x", expand=True)
        self.scales[THUMB_ROTATE_DOF] = rotate_scale

        rotate_value = ttk.Label(rotate, text=str(ANGLE_MAX), width=5, anchor="center")
        rotate_value.pack(side="left", padx=4)
        rotate_var.trace_add(
            "write",
            lambda *_a: rotate_value.config(
                text=str(self._current_angle(THUMB_ROTATE_DOF))
            ),
        )
        ttk.Label(rotate, text="1000", foreground="#666").pack(side="left")

        self._build_speed_panel(left)
        self._build_force_panel(right)
        self._build_live_force_panel(right)

    def _build_speed_panel(self, parent: ttk.Frame) -> None:
        speed = ttk.LabelFrame(parent, text="Speed", padding=(10, 6, 10, 8))
        speed.pack(fill="x", pady=(8, 0))
        ttk.Label(
            speed,
            text="All fingers  ·  1 = 200  ·  5 = 1000",
            foreground="#666",
        ).pack(anchor="w", pady=(0, 4))

        row = ttk.Frame(speed)
        row.pack(anchor="w")
        self.speed_var = tk.IntVar(value=3)
        self.speed_radios: list[ttk.Radiobutton] = []
        for level in LEVELS:
            radio = ttk.Radiobutton(
                row,
                text=str(level),
                variable=self.speed_var,
                value=level,
                command=self._on_speed,
                state="disabled",
            )
            radio.pack(side="left", padx=(0, 8))
            self.speed_radios.append(radio)

    def _build_force_panel(self, parent: ttk.Frame) -> None:
        force = ttk.LabelFrame(parent, text="Force Output", padding=(10, 6, 10, 10))
        force.pack(fill="x")
        ttk.Label(
            force,
            text="Grip threshold  ·  1 = 200  ·  5 = 1000",
            foreground="#666",
        ).pack(anchor="w", pady=(0, 6))

        grid = ttk.Frame(force)
        grid.pack(anchor="w")

        self.force_vars: dict[int, tk.IntVar] = {}
        self.force_radios: list[ttk.Radiobutton] = []

        ttk.Label(grid, text="").grid(row=0, column=0, sticky="w")
        for col, level in enumerate(LEVELS, start=1):
            ttk.Label(grid, text=str(level), width=3, anchor="center").grid(
                row=0, column=col
            )

        for row, (name, dof) in enumerate(BEND_FINGERS, start=1):
            ttk.Label(grid, text=name).grid(
                row=row, column=0, sticky="w", padx=(0, 8), pady=2
            )
            var = tk.IntVar(value=3)
            self.force_vars[dof] = var
            for col, level in enumerate(LEVELS, start=1):
                radio = ttk.Radiobutton(
                    grid,
                    variable=var,
                    value=level,
                    command=lambda d=dof: self._on_force(d),
                    state="disabled",
                )
                radio.grid(row=row, column=col)
                self.force_radios.append(radio)

    def _build_live_force_panel(self, parent: ttk.Frame) -> None:
        live = ttk.LabelFrame(parent, text="Fingertip Force Reading", padding=(10, 6, 10, 10))
        live.pack(fill="x", pady=(8, 0))
        ttk.Label(
            live,
            text="Live sensor  ·  0–1000",
            foreground="#666",
        ).pack(anchor="w", pady=(0, 6))
        self.index_meter = TipMeter(live, "Index fingertip")
        self.index_meter.frame.pack(fill="x", pady=(0, 8))
        self.thumb_meter = TipMeter(live, "Thumb fingertip")
        self.thumb_meter.frame.pack(fill="x")

    def _build_hand_sliders(self, parent: ttk.LabelFrame, pil_frames: list) -> None:
        self._hand_photos = [ImageTk.PhotoImage(frame) for frame in pil_frames]
        stage = tk.Frame(parent, bg="#000000")
        stage.pack()

        names = tk.Canvas(
            stage,
            width=HAND_WIDTH,
            height=22,
            bg="#000000",
            highlightthickness=0,
        )
        names.pack()
        for name, dof in BEND_FINGERS:
            names.create_text(
                slider_x(dof),
                11,
                text=name,
                fill="#dddddd",
                font=("TkDefaultFont", 9),
            )

        canvas = tk.Canvas(
            stage,
            width=HAND_WIDTH,
            height=HAND_HEIGHT,
            bg="#000000",
            highlightthickness=0,
        )
        canvas.pack()
        self.hand_canvas = canvas
        self._hand_item = canvas.create_image(
            0, 0, anchor="nw", image=self._hand_photos[0]
        )

        slider_top = int(HAND_HEIGHT * 0.04)
        slider_len = int(HAND_HEIGHT * 0.42)
        for name, dof in BEND_FINGERS:
            var = tk.IntVar(value=ANGLE_MAX)
            self.slider_vars[dof] = var
            scale = ttk.Scale(
                canvas,
                from_=ANGLE_MAX,
                to=ANGLE_MIN,
                orient="vertical",
                length=slider_len,
                variable=var,
                command=lambda _v, d=dof: self._on_slider(d),
                state="normal",
            )
            x = slider_x(dof)
            canvas.create_window(x, slider_top, anchor="n", window=scale)
            self.scales[dof] = scale
            self._value_items[dof] = canvas.create_text(
                x,
                slider_top + slider_len + 12,
                text=str(ANGLE_MAX),
                fill="#dddddd",
                font=("TkDefaultFont", 9),
            )

    def _build_plain_sliders(self, parent: ttk.LabelFrame) -> None:
        sliders = ttk.Frame(parent)
        sliders.pack()
        for col, (name, dof) in enumerate(BEND_FINGERS):
            col_frame = ttk.Frame(sliders)
            col_frame.grid(row=0, column=col, padx=10)
            ttk.Label(col_frame, text=name, anchor="center").pack()
            var = tk.IntVar(value=ANGLE_MAX)
            self.slider_vars[dof] = var
            scale = ttk.Scale(
                col_frame,
                from_=ANGLE_MAX,
                to=ANGLE_MIN,
                orient="vertical",
                length=220,
                variable=var,
                command=lambda _v, d=dof: self._on_slider(d),
                state="normal",
            )
            scale.pack(pady=4)
            self.scales[dof] = scale
            value_label = ttk.Label(
                col_frame, text=str(ANGLE_MAX), width=5, anchor="center"
            )
            value_label.pack()
            var.trace_add(
                "write",
                lambda *_a, d=dof, lbl=value_label: lbl.config(
                    text=str(self._current_angle(d))
                ),
            )

    def _current_angle(self, dof: int) -> int:
        return int(round(self.slider_vars[dof].get()))

    def _hand_id(self) -> int | None:
        try:
            hand_id = int(self.hand_id_var.get().strip())
        except ValueError:
            return None
        if not 1 <= hand_id <= 254:
            return None
        return hand_id

    def toggle_connect(self) -> None:
        if self.ser and self.ser.is_open:
            self.disconnect()
            return
        self.connect()

    def connect(self) -> None:
        port = self.port_var.get().strip()
        if not port:
            self.status_var.set("Enter a serial port")
            return
        if self._hand_id() is None:
            self.status_var.set("Hand ID must be 1–254")
            return
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=BAUD,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.15,
            )
        except SerialException as exc:
            self.ser = None
            self.status_var.set(f"Connect failed: {exc}")
            return

        self.port_entry.configure(state="disabled")
        self.connect_btn.configure(text="Disconnect")
        self._set_controls_enabled(True)
        self.status_var.set(f"Connected  {port}  {BAUD} 8N1")
        self._start_poll()

    def disconnect(self) -> None:
        self._stop_poll()
        for job in self._send_jobs.values():
            self.after_cancel(job)
        self._send_jobs.clear()
        if self.ser is not None:
            try:
                self.ser.close()
            except SerialException:
                pass
            self.ser = None
        self.port_entry.configure(state="normal")
        self.connect_btn.configure(text="Connect")
        self._set_controls_enabled(False)
        self.index_meter.set_value(0)
        self.thumb_meter.set_value(0)
        self.status_var.set("Disconnected")

    def _set_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for radio in self.force_radios:
            radio.configure(state=state)
        for radio in self.speed_radios:
            radio.configure(state=state)

    def _write_frame(self, frame: bytes) -> bool:
        if self.ser is None or not self.ser.is_open:
            return False
        try:
            self.ser.reset_input_buffer()
            self.ser.write(frame)
            leftover = self.ser.in_waiting
            if leftover:
                self.ser.read(leftover)
        except SerialException as exc:
            self.status_var.set(f"Write failed: {exc}")
            self.disconnect()
            return False
        return True

    def _read_registers(self, address: int, length: int) -> bytes | None:
        if self.ser is None or not self.ser.is_open:
            return None
        hand_id = self._hand_id()
        if hand_id is None:
            return None
        frame = read_register_frame(hand_id, address, length)
        try:
            self.ser.reset_input_buffer()
            self.ser.write(frame)
            # Response: 7-byte header/meta + data + checksum.
            reply = self.ser.read(8 + length)
        except SerialException:
            return None
        if len(reply) < 8 + length:
            return None
        if reply[0:2] != bytes((0x90, 0xEB)):
            return None
        if reply[4] != READ_FLAG:
            return None
        return reply[7 : 7 + length]

    def _start_poll(self) -> None:
        self._stop_poll()
        self._poll_live_force()

    def _stop_poll(self) -> None:
        if self._poll_job is not None:
            self.after_cancel(self._poll_job)
            self._poll_job = None

    def _poll_live_force(self) -> None:
        if self.ser is None or not self.ser.is_open:
            return
        if not self._send_jobs:
            data = self._read_registers(FORCE_ACT_BASE, 12)
            if data is not None and len(data) == 12:
                forces = struct.unpack("<6h", data)
                self.index_meter.set_value(forces[INDEX_FORCE_DOF])
                self.thumb_meter.set_value(forces[THUMB_FORCE_DOF])
        self._poll_job = self.after(POLL_MS, self._poll_live_force)

    def _refresh_index_art(self) -> None:
        if not self._hand_photos or self._hand_item is None:
            return
        pose = index_pose(self._angles[INDEX_DOF])
        if pose == self._index_pose:
            return
        self._index_pose = pose
        self.hand_canvas.itemconfigure(self._hand_item, image=self._hand_photos[pose])

    def reset_open(self) -> None:
        self._resetting = True
        try:
            for dof, _angle in list(self._angles.items()):
                self._angles[dof] = ANGLE_MAX
                self.slider_vars[dof].set(ANGLE_MAX)
                if dof in self._value_items:
                    self.hand_canvas.itemconfigure(
                        self._value_items[dof], text=str(ANGLE_MAX)
                    )
            self._refresh_index_art()
        finally:
            self._resetting = False
            self._send_jobs.clear()
        hand_id = self._hand_id()
        if hand_id is None or self.ser is None or not self.ser.is_open:
            self.status_var.set("Reset to open")
            return
        angles = [self._angles[dof] for dof in range(6)]
        if not self._write_frame(angle_set_all_frame(hand_id, angles)):
            return
        self.status_var.set("Reset to open")

    def _on_slider(self, dof: int) -> None:
        angle = max(ANGLE_MIN, min(ANGLE_MAX, self._current_angle(dof)))
        self._angles[dof] = angle
        if dof in self._value_items:
            self.hand_canvas.itemconfigure(self._value_items[dof], text=str(angle))
        if dof == INDEX_DOF:
            self._refresh_index_art()
        if self._resetting:
            return
        previous = self._send_jobs.pop(dof, None)
        if previous is not None:
            self.after_cancel(previous)
        self._send_jobs[dof] = self.after(SEND_DELAY_MS, lambda: self._send_angle(dof))

    def _send_angle(self, dof: int) -> None:
        self._send_jobs.pop(dof, None)
        hand_id = self._hand_id()
        if hand_id is None:
            self.status_var.set("Hand ID must be 1–254")
            return
        if not self._write_frame(angle_set_frame(hand_id, dof, self._angles[dof])):
            return
        self.status_var.set(f"Set DOF {dof} angle {self._angles[dof]}")

    def _on_force(self, dof: int) -> None:
        level = int(self.force_vars[dof].get())
        self._forces[dof] = LEVEL_VALUES[level]
        if self.ser is None or not self.ser.is_open:
            return
        self._send_force(dof)

    def _send_force(self, dof: int) -> None:
        hand_id = self._hand_id()
        if hand_id is None:
            self.status_var.set("Hand ID must be 1–254")
            return
        force = self._forces[dof]
        if not self._write_frame(force_set_frame(hand_id, dof, force)):
            return
        self.status_var.set(f"Set DOF {dof} force {force}")

    def _on_speed(self) -> None:
        level = int(self.speed_var.get())
        self._speed = LEVEL_VALUES[level]
        if self.ser is None or not self.ser.is_open:
            return
        hand_id = self._hand_id()
        if hand_id is None:
            self.status_var.set("Hand ID must be 1–254")
            return
        if not self._write_frame(speed_set_all_frame(hand_id, self._speed)):
            return
        self.status_var.set(f"Set all-finger speed {self._speed}")

    def close_app(self) -> None:
        self.disconnect()
        self.destroy()


def main() -> None:
    app = HandApp()
    app.mainloop()


if __name__ == "__main__":
    main()
