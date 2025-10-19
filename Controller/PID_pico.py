import _thread
import time
from Controller.IOs_pico import IO_MODBUS

class PIDController:
    def __init__(self, kp_list=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0], ki_list=[0.5, 0.5, 0.5, 0.5, 0.5, 0.5], 
                 kd_list=[0.05, 0.05, 0.05, 0.05, 0.05, 0.05], setpoint_list=[180, 180, 180, 180, 180, 180], 
                 io_modbus=None, adr=[1, 2, 3, 4, 5, 6]):
        self.kp_list = kp_list
        self.ki_list = ki_list
        self.kd_list = kd_list
        self.setpoint_list = setpoint_list
        self.value_temp = [0, 0, 0, 0, 0, 0]

        # Validação para evitar None
        if io_modbus is None:
            raise ValueError("io_modbus não pode ser None. Passe uma instância de IO_MODBUS.")
        self.io_modbus = io_modbus
        self.adr = adr
        self.integral = [0] * len(adr)
        self.previous_error = [0] * len(adr)
        self.previous_time = [time.ticks_ms()] * len(adr)
        self._running = False
        self._control_flag = False
        self._thread_id = None
        self._use_thread = False  # Flag para indicar se está usando thread
        
        # Limites para anti-windup
        self.output_min = 0
        self.output_max = 100
        self.integral_min = [-50] * len(adr)  # Limites do termo integral
        self.integral_max = [50] * len(adr)
        
        # Lock para sincronização (Pi Pico 2 tem 2 cores)
        self._lock = _thread.allocate_lock()

    def compute(self, current_value, index):
        current_time = time.ticks_ms()
        dt = time.ticks_diff(current_time, self.previous_time[index]) / 1000.0  # Converte para segundos
        
        if dt <= 0:
            dt = 0.001  # Evita divisão por zero
        
        # Controle PID direto com o setpoint final
        error = self.setpoint_list[index] - current_value
        
        # Termo Proporcional
        proportional = self.kp_list[index] * error
        
        # Termo Integral com anti-windup
        self.integral[index] += error * dt
        # Limita o termo integral para evitar windup
        self.integral[index] = max(self.integral_min[index], min(self.integral_max[index], self.integral[index]))
        integral_term = self.ki_list[index] * self.integral[index]
        
        # Termo Derivativo
        derivative = (error - self.previous_error[index]) / dt
        derivative_term = self.kd_list[index] * derivative
        
        # Saída PID
        output = proportional + integral_term + derivative_term
        
        # Limita a saída e implementa anti-windup
        output_limited = max(self.output_min, min(self.output_max, output))
        
        # Anti-windup: se a saída está saturada, não acumula mais no integral
        if output != output_limited:
            # Remove o excesso do integral
            if output > output_limited and error > 0:
                self.integral[index] -= error * dt
            elif output < output_limited and error < 0:
                self.integral[index] -= error * dt
        
        # Atualiza valores anteriores
        self.previous_error[index] = error
        self.previous_time[index] = current_time

        return output_limited

    def control_pwm(self):
        """Função de controle PWM executada na thread"""
        if self._control_flag and self.io_modbus is not None:
            try:
                with self._lock:
                    for i, adr in enumerate(self.adr):
                        self.value_temp[i] = self.io_modbus.get_temperature_channel(adr)
                        
                        pid_output = self.compute(self.value_temp[i], i)
                        pwm_value = pid_output  # A saída já está limitada na função compute
                        self.io_modbus.io_rpi.aciona_pwm(duty_cycle=pwm_value, saida=adr)

                    # Verifica se todos os canais atingiram o setpoint dentro da faixa permitida
                    all_channels_ready = True
                    for j, setpoint in enumerate(self.setpoint_list):
                        if not (setpoint * 0.92 <= self.value_temp[j] <= setpoint * 1.08):  # Faixa de 92% a 108% do setpoint
                            all_channels_ready = False
                            break

                    # Aciona a saída de máquina pronta se todos os canais estiverem prontos
                    if all_channels_ready:
                        self.io_modbus.io_rpi.aciona_maquina_pronta(False)
                    else:
                        self.io_modbus.io_rpi.aciona_maquina_pronta(True)
            except Exception as e:
                print(f"Erro no controle PWM: {e}")
        else:
            # Set PWM to 0 when control flag is False or io_modbus is None
            if self.io_modbus is not None:
                try:
                    pwm_value = 0
                    for adr in self.adr:
                        self.io_modbus.io_rpi.aciona_pwm(duty_cycle=pwm_value, saida=adr)
                except Exception as e:
                    print(f"Erro ao desligar PWM: {e}")

    def start(self, interval=1):
        """Inicia o controle PID em uma thread separada"""
        if not self._running:
            self._running = True
            self.interval = interval
            try:
                # Tenta usar o segundo core, se falhar usa modo sem thread
                self._thread_id = _thread.start_new_thread(self._run, (interval,))
                print("Thread PID iniciada no core1")
                self._use_thread = True
            except Exception as e:
                print(f"Aviso thread PID: {e}")
                print("Executando PID no core principal (sem thread separada)")
                self._use_thread = False
                # Em vez de thread, usamos timer ou execução manual
                
    def control_step(self):
        """Executa um passo do controle PID (para uso sem thread)"""
        if not self._use_thread and self._running:
            self.control_pwm()

    def stop(self):
        """Para o controle PID"""
        if self._running:
            self._running = False
            if hasattr(self, '_use_thread') and self._use_thread:
                print("Thread PID parando...")
                # No MicroPython não temos join(), então apenas marcamos para parar
                time.sleep_ms(100)  # Pequena pausa para a thread terminar
            else:
                print("PID parando (modo sem thread)")

    def _run(self, interval):
        """Função principal da thread PID"""
        print(f"Thread PID rodando com intervalo de {interval}s")
        
        while self._running:
            try:
                self.control_pwm()
                time.sleep(interval)
            except Exception as e:
                print(f"Erro na thread PID: {e}")
                time.sleep(interval)  # Continua executando mesmo com erro
        
        print("Thread PID finalizada")

    def set_control_flag(self, flag):
        """Define se o controle está ativo ou não"""
        with self._lock:
            self._control_flag = flag

            # Atualiza as temperaturas atuais antes de verificar o flag
            if self.io_modbus is not None:
                try:
                    for i, adr in enumerate(self.adr):
                        self.value_temp[i] = self.io_modbus.get_temperature_channel(adr)
                except Exception as e:
                    print(f"Erro ao ler temperaturas: {e}")

            if not flag:
                # Resetar estados internos ao desativar o controle
                self.integral = [0] * len(self.adr)
                self.previous_error = [0] * len(self.adr)
                self.previous_time = [time.ticks_ms()] * len(self.adr)
                print("Controle PID desativado e estados resetados")
            else:
                print("Controle PID ativado")

    def update_parameters(self, kp_list=None, ki_list=None, kd_list=None, setpoint_list=None):
        """Atualiza os parâmetros PID em tempo real"""
        with self._lock:
            if kp_list is not None:
                self.kp_list = kp_list[:]
            if ki_list is not None:
                self.ki_list = ki_list[:]
            if kd_list is not None:
                self.kd_list = kd_list[:]
            if setpoint_list is not None:
                self.setpoint_list = setpoint_list[:]
            print("Parâmetros PID atualizados")

    def get_status(self):
        """Retorna o status atual do controlador"""
        with self._lock:
            return {
                'running': self._running,
                'control_active': self._control_flag,
                'temperatures': self.value_temp[:],
                'setpoints': self.setpoint_list[:],
                'kp': self.kp_list[:],
                'ki': self.ki_list[:],
                'kd': self.kd_list[:]
            }


# Exemplo de uso
if __name__ == "__main__":
    print("Testando PIDController no Pi Pico 2...")
    
    try:
        io_modbus = IO_MODBUS()

        kp_list = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
        ki_list = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
        kd_list = [0.05, 0.06, 0.07, 0.08, 0.09, 0.1]
        setpoint_list = [180, 180, 180, 180, 180, 180]

        pid_controller = PIDController(
            kp_list=kp_list, 
            ki_list=ki_list, 
            kd_list=kd_list, 
            setpoint_list=setpoint_list, 
            io_modbus=io_modbus,  # Agora sempre passamos uma instância válida
            adr=[1, 2, 3, 4, 5, 6]
        )

        # Start control loop in a separate thread
        pid_controller.start(interval=1)

        # Activate control
        pid_controller.set_control_flag(True)

        print("PID Controller rodando. Pressione Ctrl+C para parar.")
        
        # Mostra status periodicamente
        for i in range(30):  # Roda por 30 segundos
            status = pid_controller.get_status()
            print(f"Tempo: {i}s - Temperaturas: {status['temperatures']}")
            time.sleep(1)

        # Deactivate control
        pid_controller.set_control_flag(False)

        # Stop the control loop
        pid_controller.stop()
        
        print("Teste finalizado com sucesso")

    except KeyboardInterrupt:
        print("\nParando PID Controller...")
        try:
            pid_controller.set_control_flag(False)
            pid_controller.stop()
        except:
            pass
        print("PID Controller parado")
        
    except Exception as e:
        print(f"Erro no teste: {e}")
        try:
            pid_controller.set_control_flag(False)
            pid_controller.stop()
        except:
            pass