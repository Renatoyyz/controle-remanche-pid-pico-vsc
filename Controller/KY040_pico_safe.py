import time
from machine import Pin

class FakeKY040:
    """Encoder simulado para testes sem hardware"""
    def __init__(self, clk_pin=14, dt_pin=15, sw_pin=16, val_min=1, val_max=10):
        print(f"🕹️  FakeKY040 inicializado (simulação)")
        print(f"   Pinos: CLK=GP{clk_pin}, DT=GP{dt_pin}, SW=GP{sw_pin}")
        print(f"   Range: {val_min} - {val_max}")
        
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        self.val_min = val_min
        self.val_max = val_max
        
        self.counter = val_min
        self.sw_status = 1  # 1 = liberado, 0 = pressionado
        self.last_update = time.ticks_ms()
        
    def get_counter(self):
        """Simula variação automática do contador para teste"""
        # Varia o contador automaticamente a cada 5 segundos
        elapsed = time.ticks_diff(time.ticks_ms(), self.last_update)
        if elapsed > 5000:  # 5 segundos
            self.counter += 1
            if self.counter > self.val_max:
                self.counter = self.val_min
            self.last_update = time.ticks_ms()
            print(f"🕹️  FakeEncoder: Counter = {self.counter}")
        return self.counter
    
    def set_counter(self, value):
        """Permite definir o contador externamente"""
        if self.val_min <= value <= self.val_max:
            self.counter = value
            print(f"🕹️  FakeEncoder: Counter definido para {value}")

    def set_limits(self, val_min, val_max):
        """Permite alterar os limites do contador"""
        self.val_min = val_min
        self.val_max = val_max
        print(f"🕹️  FakeEncoder: Limites alterados para {val_min} - {val_max}")
        
        # Ajusta o counter se estiver fora dos novos limites
        if self.counter < self.val_min:
            self.counter = self.val_min
        elif self.counter > self.val_max:
            self.counter = self.val_max

    @property
    def get_sw_status(self):
        """Simula pressionamento do botão a cada 10 segundos"""
        # Simula pressionamento automático para teste
        elapsed = time.ticks_diff(time.ticks_ms(), self.last_update)
        if elapsed > 10000:  # 10 segundos
            # Simula um pressionamento rápido
            print("🕹️  FakeEncoder: Botão simulado pressionado!")
            return 0  # Pressionado
        return 1  # Liberado

    def cleanup(self):
        """Limpa os recursos (simulado)"""
        print("🕹️  FakeEncoder: Cleanup concluído (simulado)")

class KY040:
    def __init__(self, clk_pin=14, dt_pin=15, sw_pin=16, val_min=1, val_max=10, pull=Pin.PULL_UP, fake_mode=False):
        """
        Inicializa encoder real ou simulado
        
        Args:
            fake_mode (bool): Se True, usa encoder simulado para testes sem hardware
        """
        if fake_mode:
            print("🕹️  Modo simulado ativado - usando FakeKY040")
            self.fake_encoder = FakeKY040(clk_pin, dt_pin, sw_pin, val_min, val_max)
            self.is_fake = True
            return
            
        # Pinos do Raspberry Pi Pico (GPIO numbers)
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        self.val_min = val_min
        self.val_max = val_max
        self.is_fake = False

        self.counter = 0
        self.test_counter = 0
        self.sw_status = 1

        try:
            # Configura os pinos
            self.clk = Pin(self.clk_pin, Pin.IN, pull)
            self.dt = Pin(self.dt_pin, Pin.IN, pull)
            self.sw = Pin(self.sw_pin, Pin.IN, pull)

            self.last_clk_state = self.clk.value()
            self.last_sw_state = self.sw.value()
            
            # No MicroPython do Pi Pico, usamos IRQ em vez de event_detect
            self.clk.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._clk_callback)
            self.sw.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._sw_callback)
            
            print(f"KY040 inicializado: CLK=GP{clk_pin}, DT=GP{dt_pin}, SW=GP{sw_pin}")
            
        except Exception as e:
            print(f"⚠️  Erro ao inicializar encoder real: {e}")
            print("🕹️  Ativando modo simulado...")
            self.fake_encoder = FakeKY040(clk_pin, dt_pin, sw_pin, val_min, val_max)
            self.is_fake = True

    def _clk_callback(self, pin):
        """Callback para rotação do encoder"""
        if self.is_fake:
            return
            
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
        if self.is_fake:
            return
            
        # Debounce simples
        time.sleep_ms(50)
        current_state = self.sw.value()
        
        # Só atualiza se o estado realmente mudou
        if current_state != self.last_sw_state:
            self.sw_status = current_state
            self.last_sw_state = current_state

    def get_counter(self):
        if self.is_fake:
            return self.fake_encoder.get_counter()
        return self.counter
    
    def set_counter(self, value):
        """Permite definir o contador externamente"""
        if self.is_fake:
            self.fake_encoder.set_counter(value)
            return
            
        if self.val_min <= value <= self.val_max:
            self.counter = value

    def set_limits(self, val_min, val_max):
        """Permite alterar os limites do contador"""
        if self.is_fake:
            self.fake_encoder.set_limits(val_min, val_max)
            return
            
        self.val_min = val_min
        self.val_max = val_max
        
        # Ajusta o counter se estiver fora dos novos limites
        if self.counter < self.val_min:
            self.counter = self.val_min
        elif self.counter > self.val_max:
            self.counter = self.val_max

    @property
    def get_sw_status(self):
        if self.is_fake:
            return self.fake_encoder.get_sw_status
        return self.sw_status

    def cleanup(self):
        """Limpa os recursos e interrupções"""
        if self.is_fake:
            self.fake_encoder.cleanup()
            return
            
        try:
            # Remove as interrupções
            self.clk.irq(handler=None)
            self.sw.irq(handler=None)
            print("KY040 cleanup concluído.")
        except Exception as e:
            print(f"Erro durante cleanup: {e}")


# Exemplo de uso
if __name__ == "__main__":
    print("Testando KY040 no Pi Pico 2...")
    
    # Testa primeiro modo real, depois simulado se falhar
    try:
        ky040 = KY040(clk_pin=14, dt_pin=15, sw_pin=16, val_min=1, val_max=10, fake_mode=False)
    except:
        print("Falha no encoder real, usando modo simulado...")
        ky040 = KY040(clk_pin=14, dt_pin=15, sw_pin=16, val_min=1, val_max=10, fake_mode=True)
    
    try:
        last_counter = -1
        last_sw = -1
        
        print("Gire o encoder ou pressione o botão. Ctrl+C para sair.")
        print("(No modo simulado, valores mudam automaticamente)")
        
        for i in range(50):  # Limita a 50 iterações para teste
            current_counter = ky040.get_counter()
            current_sw = ky040.get_sw_status
            
            # Só imprime se houver mudança
            if current_counter != last_counter:
                print(f"Counter: {current_counter}")
                last_counter = current_counter
            
            if current_sw != last_sw:
                print(f"SW Status: {'Pressionado' if current_sw == 0 else 'Liberado'}")
                last_sw = current_sw
                
            time.sleep_ms(200)  # 200ms entre verificações
            
    except KeyboardInterrupt:
        print("\nEncerrando...")
        ky040.cleanup()
    except Exception as e:
        print(f"Erro: {e}")
        ky040.cleanup()