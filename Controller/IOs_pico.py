import machine
import time
import _thread
from machine import Pin, UART

class InOut:
    def __init__(self):
        # Pinos conforme mapeamento solicitado (GPIO do Raspberry Pi Pico)
        self.SAIDA_PWM_1 = 12
        self.SAIDA_PWM_2 = 11
        self.SAIDA_PWM_3 = 10
        self.SAIDA_PWM_4 = 7
        self.SAIDA_PWM_5 = 3
        self.SAIDA_PWM_6 = 4
        self.SAIDA_MAQUINA_PRONTA = 6

        self.ENTRADA_ACIONA_MAQUINA = 5
        self.pwm_thread_running = True

        # Configura os pinos de saída PWM
        self.pwm_pins = {
            self.SAIDA_PWM_1: Pin(self.SAIDA_PWM_1, Pin.OUT),
            self.SAIDA_PWM_2: Pin(self.SAIDA_PWM_2, Pin.OUT),
            self.SAIDA_PWM_3: Pin(self.SAIDA_PWM_3, Pin.OUT),
            self.SAIDA_PWM_4: Pin(self.SAIDA_PWM_4, Pin.OUT),
            self.SAIDA_PWM_5: Pin(self.SAIDA_PWM_5, Pin.OUT),
            self.SAIDA_PWM_6: Pin(self.SAIDA_PWM_6, Pin.OUT)
        }

        # Configura o pino de saída da máquina pronta
        self.maquina_pronta_pin = Pin(self.SAIDA_MAQUINA_PRONTA, Pin.OUT)
        self.maquina_pronta_pin.on()  # Inicializa como desligado (HIGH = desligado)

        # Configura o pino de entrada
        self.entrada_maquina_pin = Pin(self.ENTRADA_ACIONA_MAQUINA, Pin.IN, Pin.PULL_UP)

        self.pwm_period = 1.0  # Default period in seconds
        self.pwm_duty_cycles = {
            self.SAIDA_PWM_1: 0,
            self.SAIDA_PWM_2: 0,
            self.SAIDA_PWM_3: 0,
            self.SAIDA_PWM_4: 0,
            self.SAIDA_PWM_5: 0,
            self.SAIDA_PWM_6: 0
        }

        # Inicia thread PWM usando _thread (limitado a 2 cores no Pi Pico 2)
        self.pwm_lock = _thread.allocate_lock()
        try:
            _thread.start_new_thread(self._pwm_control_all, ())
            print("Thread PWM iniciada no core1")
        except Exception as e:
            print(f"Aviso PWM thread: {e}")
            print("PWM funcionará em modo síncrono")
            self.pwm_thread_running = False

    @property
    def get_aciona_maquina(self):
        if self.entrada_maquina_pin.value() == 0:  # LOW
            return 1
        else:
            return 0

    def _pwm_control_all(self):
        """Controla PWM de todos os pinos em uma única thread para economizar recursos"""
        while self.pwm_thread_running:
            self._pwm_step()
            time.sleep_ms(100)  # 100ms entre ciclos PWM

    def _pwm_step(self):
        """Executa um ciclo PWM (pode ser chamado com ou sem thread)"""
        with self.pwm_lock:
            for pin_num, duty_cycle in self.pwm_duty_cycles.items():
                pin_obj = self.pwm_pins[pin_num]
                if duty_cycle > 0:
                    on_time = self.pwm_period * (duty_cycle / 100.0)
                    off_time = self.pwm_period - on_time
                    
                    if on_time > 0:
                        pin_obj.off()  # LOW = ativo
                        time.sleep_ms(int(on_time * 1000))
                    if off_time > 0:
                        pin_obj.on()   # HIGH = inativo
                        time.sleep_ms(int(off_time * 1000))
                else:
                    pin_obj.on()  # Mantém HIGH quando duty cycle = 0

    def set_pwm_period(self, period):
        with self.pwm_lock:
            self.pwm_period = period

    def set_pwm_duty_cycle(self, pin, duty_cycle):
        if pin in self.pwm_duty_cycles:
            with self.pwm_lock:
                self.pwm_duty_cycles[pin] = max(0, min(100, duty_cycle))

    def aciona_pwm(self, duty_cycle, saida):
        if saida == 1:
            self.set_pwm_duty_cycle(self.SAIDA_PWM_1, duty_cycle)
        elif saida == 2:
            self.set_pwm_duty_cycle(self.SAIDA_PWM_2, duty_cycle)
        elif saida == 3:
            self.set_pwm_duty_cycle(self.SAIDA_PWM_3, duty_cycle)
        elif saida == 4:
            self.set_pwm_duty_cycle(self.SAIDA_PWM_4, duty_cycle)
        elif saida == 5:
            self.set_pwm_duty_cycle(self.SAIDA_PWM_5, duty_cycle)
        elif saida == 6:
            self.set_pwm_duty_cycle(self.SAIDA_PWM_6, duty_cycle)

    def cleanup(self):
        self.pwm_thread_running = False
        time.sleep_ms(100)  # Aguarda a thread PWM terminar
        # Desliga todos os pinos PWM
        for pin_obj in self.pwm_pins.values():
            pin_obj.on()  # HIGH = inativo

    def aciona_maquina_pronta(self, status):
        if status:
            self.maquina_pronta_pin.off()  # LOW = ativo
        else:
            self.maquina_pronta_pin.on()   # HIGH = inativo


class IO_MODBUS:
    def __init__(self, dado=None, uart_id=0, baudrate=9600, tx_pin=0, rx_pin=1, timeout=1.0):
        self.dado = dado
        self.fake_modbus = True
        self.timeout = timeout
        
        try:
            # Configura UART para comunicação Modbus
            self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
            self.uart.init(baudrate=baudrate, bits=8, parity=None, stop=1, timeout=int(timeout * 1000))
            print(f"UART{uart_id} configurada: TX=GP{tx_pin}, RX=GP{rx_pin}, Baud={baudrate}")
            self.fake_modbus = False
        except Exception as e:
            print(f"Erro ao configurar UART: {e}")
            print("Usando modo simulado (fake_modbus = True)")
        
        self.io_rpi = InOut()

    def crc16_modbus(self, data):
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if (crc & 0x0001):
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc

    def _get_adr_PTA(self):
        if self.fake_modbus:
            return 1  # Retorna endereço padrão em modo simulado

        broadcast = 0xFF
        id_loc = "{:02x}".format(broadcast).upper()

        hex_text = "{}0300020001".format(id_loc)
        bytes_hex = bytes.fromhex(hex_text)
        crc_result = self.crc16_modbus(bytes_hex)

        parte_superior = (crc_result >> 8) & 0xFF
        parte_inferior = crc_result & 0xFF

        for i in range(3):
            try:
                # Envia comando Modbus
                cmd = bytes([broadcast, 3, 0, 2, 0, 1, parte_inferior, parte_superior])
                self.uart.write(cmd)
                
                # Aguarda resposta
                start_time = time.ticks_ms()
                while self.uart.any() == 0:
                    if time.ticks_diff(time.ticks_ms(), start_time) > self.timeout * 1000:
                        print("Timeout: Nenhuma resposta do escravo.")
                        break
                    time.sleep_ms(10)

                if self.uart.any() > 0:
                    dados_recebidos = self.uart.read(7)
                    if dados_recebidos and len(dados_recebidos) == 7:
                        # Processa dados recebidos
                        dados_hex = dados_recebidos.hex()
                        hex_text = dados_hex[0:10]
                        bytes_hex = bytes.fromhex(hex_text)
                        crc_result = self.crc16_modbus(bytes_hex)

                        parte_superior = (crc_result >> 8) & 0xFF
                        parte_inferior = crc_result & 0xFF

                        superior_crc = int(dados_hex[12:14], 16)
                        inferior_crc = int(dados_hex[10:12], 16)

                        if superior_crc == parte_superior and inferior_crc == parte_inferior:
                            endereco = int(dados_hex[6:10], 16)
                            return endereco
                        else:
                            print("CRC inválido")
                    
            except Exception as e:
                print(f"Erro de comunicação: {e}")
                return -1
        return -1

    def config_adr_PTA(self, adr):
        if self.fake_modbus:
            return True  # Simula sucesso em modo simulado

        adr_target = "{:04x}".format(adr).upper()
        adr_device = self._get_adr_PTA()

        if adr_device == -1:
            return False

        id_device = "{:02x}".format(adr_device).upper()
        hex_text = "{}060002{}".format(id_device, adr_target)
        bytes_hex = bytes.fromhex(hex_text)
        crc_result = self.crc16_modbus(bytes_hex)

        parte_superior = (crc_result >> 8) & 0xFF
        parte_inferior = crc_result & 0xFF

        adr_target_int = int(adr_target, 16)
        msb = (adr_target_int >> 8) & 0xFF
        lsb = adr_target_int & 0xFF

        for i in range(3):
            try:
                cmd = bytes([adr_device, 6, 0, 2, msb, lsb, parte_inferior, parte_superior])
                self.uart.write(cmd)

                start_time = time.ticks_ms()
                while self.uart.any() == 0:
                    if time.ticks_diff(time.ticks_ms(), start_time) > self.timeout * 1000:
                        print("Timeout: Nenhuma resposta do escravo.")
                        break
                    time.sleep_ms(10)

                if self.uart.any() > 0:
                    dados_recebidos = self.uart.read(8)
                    if dados_recebidos and len(dados_recebidos) == 8:
                        # Verifica resposta
                        return True
                    
            except Exception as e:
                print(f"Erro de comunicação: {e}")
                return False
        return False

    def get_temperature_channel(self, adr):
        if self.fake_modbus:
            # Simula leitura de temperatura
            import urandom
            return 20.0 + urandom.randint(0, 100)  # Temperatura simulada entre 20-120°C

        # Converte endereço para hex de forma compatível com MicroPython
        id_device = "{:02x}".format(adr).upper()
        hex_text = "{}0300000001".format(id_device)
        bytes_hex = bytes.fromhex(hex_text)
        crc_result = self.crc16_modbus(bytes_hex)

        parte_superior = (crc_result >> 8) & 0xFF
        parte_inferior = crc_result & 0xFF

        for i in range(3):
            try:
                cmd = bytes([adr, 3, 0, 0, 0, 1, parte_inferior, parte_superior])
                self.uart.write(cmd)

                start_time = time.ticks_ms()
                while self.uart.any() == 0:
                    if time.ticks_diff(time.ticks_ms(), start_time) > self.timeout * 1000:
                        print("Timeout: Nenhuma resposta do escravo.")
                        break
                    time.sleep_ms(10)

                if self.uart.any() > 0:
                    dados_recebidos = self.uart.read(7)
                    if dados_recebidos and len(dados_recebidos) == 7:
                        # Processa temperatura
                        dados_hex = dados_recebidos.hex()
                        hex_text = dados_hex[0:10]
                        bytes_hex = bytes.fromhex(hex_text)
                        crc_result = self.crc16_modbus(bytes_hex)

                        parte_superior = (crc_result >> 8) & 0xFF
                        parte_inferior = crc_result & 0xFF

                        superior_crc = int(dados_hex[12:14], 16)
                        inferior_crc = int(dados_hex[10:12], 16)

                        if superior_crc == parte_superior and inferior_crc == parte_inferior:
                            temperatura_hex = dados_hex[6:10]
                            temperatura = int(temperatura_hex, 16) / 10.0  # Converte para °C
                            return temperatura
                        else:
                            print("CRC inválido")
                    
            except Exception as e:
                print(f"Erro de comunicação: {e}")
                return -1
        return -1

    def reset_serial(self):
        try:
            if hasattr(self, 'uart') and self.uart:
                self.uart.deinit()
                time.sleep_ms(500)
                self.uart.init()
                print("UART resetada com sucesso.")
        except Exception as e:
            print(f"Erro ao resetar UART: {e}")


if __name__ == '__main__':
    print("Testando IO_MODBUS para Pi Pico 2...")
    io = IO_MODBUS()
    
    while True:
        print("1. Visualizar endereço do dispositivo")
        print("2. Modificar endereço do dispositivo")
        print("3. Ler temperatura")
        print("4. Sair")
        
        try:
            opcao = input("Escolha uma opção: ")
        except:
            # No MicroPython, input() pode não estar disponível
            opcao = '4'  # Sai automaticamente

        if opcao == '1':
            endereco = io._get_adr_PTA()
            if endereco != -1:
                print(f"Endereço do dispositivo: {endereco}")
            else:
                print("Erro ao obter o endereço do dispositivo.")
        elif opcao == '2':
            try:
                novo_endereco = int(input("Digite o novo endereço do dispositivo: "))
                resultado = io.config_adr_PTA(novo_endereco)
                if resultado:
                    print(f"Endereço do dispositivo alterado para: {novo_endereco}")
                else:
                    print("Erro ao alterar o endereço do dispositivo.")
            except:
                print("Entrada inválida.")
        elif opcao == '3':
            try:
                endereco = int(input("Digite o endereço do dispositivo: "))
                temperatura = io.get_temperature_channel(endereco)
                if temperatura != -1:
                    print(f"Temperatura do dispositivo: {temperatura}°C")
                else:
                    print("Erro ao ler a temperatura do dispositivo.")
            except:
                print("Entrada inválida.")
        elif opcao == '4':
            break
        else:
            print("Opção inválida. Tente novamente.")