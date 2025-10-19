import time
from machine import Pin

class KY040:
    def __init__(self, clk_pin=14, dt_pin=15, sw_pin=16, val_min=1, val_max=10, pull=Pin.PULL_UP):
        # Pinos do Raspberry Pi Pico (GPIO numbers)
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        self.val_min = val_min
        self.val_max = val_max

        self.counter = 0
        self.test_counter = 0
        self.sw_status = 1

        # Configura os pinos
        self.clk = Pin(self.clk_pin, Pin.IN, pull)
        self.dt = Pin(self.dt_pin, Pin.IN, pull)
        self.sw = Pin(self.sw_pin, Pin.IN, pull)

        self.last_clk_state = self.clk.value()
        self.last_sw_state = self.sw.value()
        
        # No MicroPython do Pi Pico, usamos IRQ em vez de event_detect
        self.clk.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._clk_callback)
        self.sw.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._sw_callback)

    def _clk_callback(self, pin):
        """Callback para rotação do encoder"""
        clk_state = self.clk.value()
        dt_state = self.dt.value()
        
        if clk_state != self.last_clk_state:
            if dt_state != clk_state:
                self.test_counter += 1
                if self.test_counter % 2 == 0:
                    self.counter += 1
                if self.counter > self.val_max:
                    self.counter = self.val_min
            else:
                self.test_counter -= 1
                if self.test_counter % 2 == 0:
                    self.counter -= 1

                if self.counter < self.val_min:
                    self.counter = self.val_max

            self.last_clk_state = clk_state

    def _sw_callback(self, pin):
        """Callback para botão do encoder"""
        # Debounce simples
        time.sleep_ms(50)
        current_state = self.sw.value()
        
        # Só atualiza se o estado realmente mudou
        if current_state != self.last_sw_state:
            self.sw_status = current_state
            self.last_sw_state = current_state

    def get_counter(self):
        return self.counter
    
    def set_counter(self, value):
        """Permite definir o contador externamente"""
        if self.val_min <= value <= self.val_max:
            self.counter = value

    def set_limits(self, val_min, val_max):
        """Permite alterar os limites do contador"""
        self.val_min = val_min
        self.val_max = val_max
        
        # Ajusta o counter se estiver fora dos novos limites
        if self.counter < self.val_min:
            self.counter = self.val_min
        elif self.counter > self.val_max:
            self.counter = self.val_max

    @property
    def get_sw_status(self):
        return self.sw_status

    def cleanup(self):
        """Limpa os recursos e interrupções"""
        try:
            # Remove as interrupções
            self.clk.irq(handler=None)
            self.sw.irq(handler=None)
            print("KY040 cleanup concluído.")
        except Exception as e:
            print(f"Erro durante cleanup: {e}")


# Exemplo de uso
if __name__ == "__main__":
    from IOs_pico import IO_MODBUS
    
    print("Testando KY040 no Pi Pico 2...")
    
    # Cria instância do encoder
    ky040 = KY040(clk_pin=14, dt_pin=15, sw_pin=16, val_min=1, val_max=10)
    
    try:
        last_counter = -1
        last_sw = -1
        
        print("Gire o encoder ou pressione o botão. Ctrl+C para sair.")
        
        while True:
            current_counter = ky040.get_counter()
            current_sw = ky040.get_sw_status
            
            # Só imprime se houver mudança
            if current_counter != last_counter:
                print(f"Counter: {current_counter}")
                last_counter = current_counter
            
            if current_sw != last_sw:
                print(f"SW Status: {'Pressionado' if current_sw == 0 else 'Liberado'}")
                last_sw = current_sw
                
            time.sleep_ms(100)  # Pequeno delay para não sobrecarregar
            
    except KeyboardInterrupt:
        print("\nEncerrando...")
        ky040.cleanup()
    except Exception as e:
        print(f"Erro: {e}")
        ky040.cleanup()