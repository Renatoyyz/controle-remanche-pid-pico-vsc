from machine import I2C, Pin
import time

# Configurações I2C para Pi Pico
I2C_ID = 0  # I2C0 do Pi Pico
SDA_PIN = 0  # GPIO 0
SCL_PIN = 1  # GPIO 1

class i2c_device:
    def __init__(self, addr, i2c_bus):
        self.addr = addr
        self.i2c = i2c_bus

    def write_cmd(self, cmd):
        try:
            self.i2c.writeto(self.addr, bytes([cmd]))
            time.sleep_us(100)
        except Exception as e:
            print(f"Erro I2C write_cmd: {e}")

    def write_cmd_arg(self, cmd, data):
        try:
            self.i2c.writeto(self.addr, bytes([cmd, data]))
            time.sleep_us(100)
        except Exception as e:
            print(f"Erro I2C write_cmd_arg: {e}")

    def write_block_data(self, cmd, data):
        try:
            write_data = bytes([cmd]) + bytes(data)
            self.i2c.writeto(self.addr, write_data)
            time.sleep_us(100)
        except Exception as e:
            print(f"Erro I2C write_block_data: {e}")

    def read(self):
        try:
            return self.i2c.readfrom(self.addr, 1)[0]
        except Exception as e:
            print(f"Erro I2C read: {e}")
            return 0

    def read_data(self, cmd):
        try:
            self.i2c.writeto(self.addr, bytes([cmd]))
            return self.i2c.readfrom(self.addr, 1)[0]
        except Exception as e:
            print(f"Erro I2C read_data: {e}")
            return 0

    def read_block_data(self, cmd):
        try:
            self.i2c.writeto(self.addr, bytes([cmd]))
            return list(self.i2c.readfrom(self.addr, 32))  # Lê até 32 bytes
        except Exception as e:
            print(f"Erro I2C read_block_data: {e}")
            return []


# Comandos LCD
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# Flags para modo de entrada
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# Flags para controle do display
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# Flags para movimento do display/cursor
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# Flags para configuração de função
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS = 0x00

# Flags para controle do backlight
LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x00

En = 0b00000100  # Enable bit
Rw = 0b00000010  # Read/Write bit
Rs = 0b00000001  # Register select bit

class Lcd:
    def __init__(self, sda_pin=SDA_PIN, scl_pin=SCL_PIN, i2c_id=I2C_ID):
        self.i2c_bus = I2C(i2c_id, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=100000)
        self.addresses = self.find_i2c_address()
        
        if not self.addresses:
            raise Exception(f"LCD não encontrado. Endereços disponíveis: {self.addresses}")
        
        # Usa o primeiro endereço encontrado
        self.lcd_device = i2c_device(self.addresses[0], self.i2c_bus)
        print(f"LCD encontrado no endereço: 0x{self.addresses[0]:02X}")

        # Inicializa o LCD
        self._initialize_lcd()

    def _initialize_lcd(self):
        """Inicializa o LCD seguindo a sequência padrão"""
        try:
            time.sleep_ms(50)  # Aguarda LCD estabilizar
            
            self.lcd_write(0x03)
            time.sleep_ms(5)
            self.lcd_write(0x03)
            time.sleep_ms(5)
            self.lcd_write(0x03)
            time.sleep_ms(1)
            self.lcd_write(0x02)
            time.sleep_ms(1)

            self.lcd_write(LCD_FUNCTIONSET | LCD_2LINE | LCD_5x8DOTS | LCD_4BITMODE)
            self.lcd_write(LCD_DISPLAYCONTROL | LCD_DISPLAYON)
            self.lcd_write(LCD_CLEARDISPLAY)
            self.lcd_write(LCD_ENTRYMODESET | LCD_ENTRYLEFT)
            time.sleep_ms(200)
            print("LCD inicializado com sucesso")
        except Exception as e:
            print(f"Erro na inicialização do LCD: {e}")

    def find_i2c_address(self):
        """Escaneia os endereços I2C disponíveis"""
        try:
            addresses = self.i2c_bus.scan()
            print(f"Endereços I2C encontrados: {[hex(addr) for addr in addresses]}")
            return addresses
        except Exception as e:
            print(f"Erro ao escanear I2C: {e}")
            return []

    def lcd_strobe(self, data):
        """Pulso no pino Enable para validar comando"""
        try:
            self.lcd_device.write_cmd(data | En | LCD_BACKLIGHT)
            time.sleep_us(500)
            self.lcd_device.write_cmd(((data & ~En) | LCD_BACKLIGHT))
            time.sleep_us(100)
        except Exception as e:
            print(f"Erro lcd_strobe: {e}")

    def lcd_write_four_bits(self, data):
        """Escreve 4 bits para o LCD"""
        try:
            self.lcd_device.write_cmd(data | LCD_BACKLIGHT)
            self.lcd_strobe(data)
        except Exception as e:
            print(f"Erro lcd_write_four_bits: {e}")

    def lcd_write(self, cmd, mode=0):
        """Escreve um comando para o LCD"""
        try:
            self.lcd_write_four_bits(mode | (cmd & 0xF0))
            self.lcd_write_four_bits(mode | ((cmd << 4) & 0xF0))
        except Exception as e:
            print(f"Erro lcd_write: {e}")

    def lcd_write_char(self, charvalue, mode=1):
        """Escreve um caractere para o LCD"""
        try:
            self.lcd_write_four_bits(mode | (charvalue & 0xF0))
            self.lcd_write_four_bits(mode | ((charvalue << 4) & 0xF0))
        except Exception as e:
            print(f"Erro lcd_write_char: {e}")

    def lcd_display_string(self, string, line=1, pos=0):
        """Exibe uma string na posição especificada"""
        try:
            if line == 1:
                pos_new = pos
            elif line == 2:
                pos_new = 0x40 + pos
            elif line == 3:
                pos_new = 0x14 + pos
            elif line == 4:
                pos_new = 0x54 + pos
            else:
                return

            self.lcd_write(0x80 + pos_new)

            for char in string:
                self.lcd_write(ord(char), Rs)
        except Exception as e:
            print(f"Erro lcd_display_string: {e}")

    def lcd_clear(self):
        """Limpa o LCD e volta para home"""
        try:
            self.lcd_write(LCD_CLEARDISPLAY)
            self.lcd_write(LCD_RETURNHOME)
            time.sleep_ms(2)  # Comando clear precisa de mais tempo
        except Exception as e:
            print(f"Erro lcd_clear: {e}")

    def backlight(self, state):
        """Controla o backlight: 1 = ligado, 0 = desligado"""
        try:
            if state == 1:
                self.lcd_device.write_cmd(LCD_BACKLIGHT)
            elif state == 0:
                self.lcd_device.write_cmd(LCD_NOBACKLIGHT)
        except Exception as e:
            print(f"Erro backlight: {e}")

    def lcd_load_custom_chars(self, fontdata):
        """Carrega caracteres customizados (0-7)"""
        try:
            self.lcd_write(0x40)
            for char in fontdata:
                for line in char:
                    self.lcd_write_char(line)
        except Exception as e:
            print(f"Erro lcd_load_custom_chars: {e}")

    def lcd_display_string_inverter(self, string, line=1, pos=0):
        """Exibe string com fundo invertido (simulado)"""
        try:
            if line == 1:
                pos_new = pos
            elif line == 2:
                pos_new = 0x40 + pos
            elif line == 3:
                pos_new = 0x14 + pos
            elif line == 4:
                pos_new = 0x54 + pos
            else:
                return

            self.lcd_write(0x80 + pos_new)

            # Simula inversão desligando o backlight temporariamente
            self.backlight(0)
            for char in string:
                self.lcd_write(ord(char), Rs)
            time.sleep_ms(100)
            self.backlight(1)
        except Exception as e:
            print(f"Erro lcd_display_string_inverter: {e}")


if __name__ == "__main__":
    print("Testando LCD no Pi Pico 2...")
    
    try:
        # Cria instância do LCD
        lcd = Lcd()

        # Exibe informações iniciais
        lcd.lcd_display_string("Pi Pico 2 LCD Test", 1, 1)
        lcd.lcd_display_string("Renato Oliveira", 2, 1)
        
        # Mostra uma string com fundo invertido
        lcd.lcd_display_string_inverter("Katia Amor", 3, 1)
        time.sleep(4)

        # Loop principal
        try:
            counter = 0
            while True:
                # Mostra data/hora simulada
                lcd.lcd_display_string(f"Count: {counter:06d}", 4, 1)
                counter += 1
                time.sleep(1)
                
        except KeyboardInterrupt:
            lcd.lcd_clear()
            print("Fim do programa")
            
    except Exception as e:
        print(f"Erro no programa principal: {e}")