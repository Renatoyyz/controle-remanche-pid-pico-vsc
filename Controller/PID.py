import time

# cross-platform thread module + lock factory
try:
    import _thread as _thread_mod  # MicroPython (RP2040)
    allocate_lock = _thread_mod.allocate_lock
    THREAD_MODE = 'micropython'
except Exception:
    import threading as _thread_mod  # CPython
    allocate_lock = _thread_mod.Lock
    THREAD_MODE = 'threading'

from Controller.IOs import IO_MODBUS


class PIDController:
    def __init__(self, kp_list=None, ki_list=None, kd_list=None,
                 setpoint_list=None, io_modbus=None, adr=None):
        # defaults
        if kp_list is None:
            kp_list = [1.0] * 6
        if ki_list is None:
            ki_list = [0.5] * 6
        if kd_list is None:
            kd_list = [0.05] * 6
        if setpoint_list is None:
            setpoint_list = [180.0] * 6
        if adr is None:
            adr = [1, 2, 3, 4, 5, 6]

        self.kp_list = [float(x) for x in kp_list]
        self.ki_list = [float(x) for x in ki_list]
        self.kd_list = [float(x) for x in kd_list]
        self.setpoint_list = [float(x) for x in setpoint_list]

        # setpoint stages (25%,50%,75%,100%)
        self.setpoint_stages = [[sp * 0.25, sp * 0.50, sp * 0.75, sp] for sp in self.setpoint_list]

        # use None for "no reading yet"
        self.value_temp = [None] * len(adr)  # type: list[float | None]
        self.io_modbus = io_modbus or IO_MODBUS()
        self.adr = adr

        # PID internal states (floats)
        self.integral = [0.0] * len(adr)            # type: list[float]
        self.previous_error = [0.0] * len(adr)      # type: list[float]
        self.current_stage = [0] * len(self.setpoint_list)  # type: list[int]
        # None means timer not started for stage hold
        self.stage_start_time = [None] * len(self.setpoint_list)  # type: list[float | None]

        # thread/control flags
        self._running = False
        self._control_flag = False
        self._thread_alive = False

        # synchronization
        self._lock = allocate_lock()

    def compute(self, current_value, index):
        """
        Compute PID output for channel index.
        If current_value is None, returns 0.0 (no actuation).
        """
        if current_value is None:
            return 0.0

        try:
            cur = float(current_value)
        except Exception:
            return 0.0

        target = self.setpoint_stages[index][self.current_stage[index]]
        error = target - cur

        # integral windup and deadband handling
        if abs(error) < 0.5:
            self.integral[index] = 0.0
        else:
            self.integral[index] += error
            # clamp integral to reasonable bounds
            if self.integral[index] > 100.0:
                self.integral[index] = 100.0
            elif self.integral[index] < -100.0:
                self.integral[index] = -100.0

        derivative = error - self.previous_error[index]

        output = (
            self.kp_list[index] * error +
            self.ki_list[index] * self.integral[index] +
            self.kd_list[index] * derivative
        )

        self.previous_error[index] = error
        return float(output)

    def control_pwm(self):
        """
        Read temperatures, update stages and compute PWM outputs.
        Handles None readings and avoids optional-member access issues by
        narrowing io_rpi/local vars before calling methods.
        """
        io_rpi = getattr(self.io_modbus, "io_rpi", None)

        for i, adr in enumerate(self.adr):
            # read temperature (may set None on error)
            try:
                temp = self.io_modbus.get_temperature_channel(adr)
            except Exception:
                temp = None
            self.value_temp[i] = temp

            # advance stage if within tolerance for configured time
            try:
                target = self.setpoint_stages[i][self.current_stage[i]]
                if temp is not None:
                    try:
                        temp_f = float(temp)
                    except Exception:
                        temp_f = None

                    if temp_f is not None and abs(temp_f - target) <= 5.0:
                        # narrow start to local var to satisfy type-checkers
                        start = self.stage_start_time[i]
                        if start is None:
                            self.stage_start_time[i] = time.time()
                        else:
                            # start is float here
                            if (time.time() - start) >= 60.0:
                                self.current_stage[i] = min(self.current_stage[i] + 1,
                                                            len(self.setpoint_stages[i]) - 1)
                                self.stage_start_time[i] = None
                    else:
                        self.stage_start_time[i] = None
                else:
                    # no reading -> reset timer so we don't advance incorrectly
                    self.stage_start_time[i] = None
            except Exception:
                # protect against index errors or bad data
                self.stage_start_time[i] = None

            # compute PID and write PWM (clamped 0..100)
            pid_output = self.compute(self.value_temp[i], i)
            try:
                pwm_value = int(max(0, min(100, round(pid_output))))
            except Exception:
                pwm_value = 0

            # call hardware only if io_rpi is present (narrowed local var)
            if io_rpi is not None:
                try:
                    # ensure methods exist before calling (defensive)
                    aciona = getattr(io_rpi, "aciona_pwm", None)
                    if callable(aciona):
                        aciona(duty_cycle=pwm_value, saida=adr)
                except Exception:
                    # ignore hardware errors
                    pass

        # check if all channels reached last stage (approx)
        all_ready = True
        for j, stages in enumerate(self.setpoint_stages):
            target = stages[-1]
            temp = self.value_temp[j]
            if temp is None:
                all_ready = False
                break
            try:
                if not (target * 0.92 <= float(temp) <= target * 1.08):
                    all_ready = False
                    break
            except Exception:
                all_ready = False
                break

        # notify machine-ready only if io_rpi is present and method available
        if io_rpi is not None:
            try:
                notify = getattr(io_rpi, "aciona_maquina_pronta", None)
                if callable(notify):
                    notify(all_ready)
            except Exception:
                pass

    def _run(self, interval):
        """
        Background loop. Narrow io_rpi on each iteration to avoid optional-member
        access warnings and only call methods when present and callable.
        """
        self._thread_alive = True
        try:
            while self._running:
                # refresh narrowed local reference each loop in case io_rpi appears/disappears
                io_rpi = getattr(self.io_modbus, "io_rpi", None)

                if self._control_flag:
                    with self._lock:
                        self.control_pwm()
                else:
                    # ensure PWMs off if hardware interface is available
                    if io_rpi is not None:
                        aciona = getattr(io_rpi, "aciona_pwm", None)
                        if callable(aciona):
                            for adr in self.adr:
                                try:
                                    aciona(duty_cycle=0, saida=adr)
                                except Exception:
                                    pass
                time.sleep(interval)
        finally:
            self._thread_alive = False

    def start(self, interval=1.0):
        """Start background PID loop (non-blocking if threads available)."""
        if self._running:
            return
        self._running = True

        # Use local imports per-branch so type-checkers see correct symbols
        if THREAD_MODE == 'micropython':
            try:
                # MicroPython: _thread provides start_new_thread
                import _thread as _mp_thread  # local import narrows type for linters
                _mp_thread.start_new_thread(self._run, (interval,))
            except Exception:
                # fallback to blocking run if thread creation fails
                self._run(interval)
        else:
            try:
                # CPython: threading.Thread
                import threading as _th  # local import narrows type for linters
                t = _th.Thread(target=self._run, args=(interval,))
                t.daemon = True
                t.start()
            except Exception:
                # fallback to blocking run if thread creation fails
                self._run(interval)

    def stop(self, wait_timeout=2.0):
        """Stop background loop and wait up to wait_timeout seconds."""
        if not self._running:
            return
        self._running = False
        start = time.time()
        while self._thread_alive and (time.time() - start) < wait_timeout:
            time.sleep(0.01)

    def set_control_flag(self, flag):
        """
        Enable/disable PID control. When enabling, determines initial stage
        based on current readings. When disabling, resets PID internal state.
        """
        with self._lock:
            self._control_flag = bool(flag)

            # refresh readings when toggling
            for i, adr in enumerate(self.adr):
                try:
                    self.value_temp[i] = self.io_modbus.get_temperature_channel(adr)
                except Exception:
                    self.value_temp[i] = None

            if not flag:
                # reset PID internal states
                self.integral = [0.0] * len(self.adr)
                self.previous_error = [0.0] * len(self.adr)
                self.stage_start_time = [None] * len(self.adr)
                self.current_stage = [0] * len(self.adr)
            else:
                # determine starting stage from current readings (if available)
                for i, temp in enumerate(self.value_temp):
                    stage_found = 0
                    try:
                        if temp is not None:
                            tval = float(temp)
                            for stage, sp in enumerate(self.setpoint_stages[i]):
                                if tval >= sp:
                                    stage_found = stage
                    except Exception:
                        stage_found = 0
                    self.current_stage[i] = stage_found

# Example usage (kept for testing; on Pico run via REPL or main script)
if __name__ == "__main__":
    io_modbus = IO_MODBUS()

    kp_list = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
    ki_list = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    kd_list = [0.05, 0.06, 0.07, 0.08, 0.09, 0.1]
    setpoint_list = [180, 180, 180, 180, 180, 180]

    pid_controller = PIDController(kp_list=kp_list, ki_list=ki_list, kd_list=kd_list,
                                   setpoint_list=setpoint_list, io_modbus=io_modbus, adr=[1,2,3,4,5,6])

    pid_controller.start(interval=1)
    pid_controller.set_control_flag(True)

    # exemplo de execução por 5 minutos
    time.sleep(300)

    pid_controller.set_control_flag(False)
    pid_controller.stop()
#