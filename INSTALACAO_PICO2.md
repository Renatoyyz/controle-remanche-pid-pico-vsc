# 📋 Guia de Instalação - Raspberry Pi Pico 2

Este guia detalha o processo de instalação e configuração do sistema de controle PID no Raspberry Pi Pico 2.

## 🔧 Requisitos de Hardware

### Raspberry Pi Pico 2
- **Processador**: RP2350 (Dual-core ARM Cortex-M33)
- **Memória**: 264KB SRAM
- **Flash**: 2MB
- **GPIO**: 30 pinos disponíveis
- **Comunicação**: UART, I2C, SPI

### Componentes Externos
- **Display LCD 20x4** com interface I2C (PCF8574)
- **Encoder Rotativo KY040** (com botão)
- **Sensores de temperatura** com comunicação Modbus
- **Drivers PWM** para controle de aquecimento (6 canais)
- **Fonte de alimentação** 5V (para periféricos) e 3.3V (Pico)

## 💿 Instalação do MicroPython

### 1. Download do Firmware
```bash
# Baixe o firmware MicroPython para RP2350
# URL: https://micropython.org/download/rp2-pico/
# Arquivo: rp2-pico-20240222-v1.22.2.uf2 (ou versão mais recente)
```

### 2. Instalação no Pi Pico 2
```bash
# 1. Segure o botão BOOTSEL no Pico 2
# 2. Conecte o USB ao computador (ainda segurando BOOTSEL)
# 3. Solte o BOOTSEL - aparecerá como drive USB
# 4. Copie o arquivo .uf2 para o drive
# 5. O Pico reiniciará automaticamente com MicroPython
```

### 3. Verificação da Instalação
```python
# Conecte via terminal serial (115200 baud)
# Teste básico:
>>> print("Hello Pi Pico 2!")
>>> import machine
>>> machine.freq()
133000000
```

## 📁 Estrutura de Arquivos no Pi Pico 2

```
/ (raiz da memória flash)
├── main.py              # Renomeie main_pico.py para execução automática
├── IOs_pico.py         # Módulo GPIO/PWM/UART
├── KY040_pico.py       # Módulo Encoder
├── Lcd_pico.py         # Módulo LCD I2C
├── PID_pico.py         # Módulo Controlador PID
├── Dados_pico.py       # Módulo Estados/Dados
├── test_pico2.py       # Arquivo de testes (opcional)
├── setpoint_list.json  # Configurações setpoints (criado automaticamente)
└── pid_values.json     # Configurações PID (criado automaticamente)
```

## 🔌 Conexões Hardware

### Display LCD I2C
```
LCD PCF8574    →    Pi Pico 2
VCC            →    3.3V (pino 36)
GND            →    GND (pino 38)
SDA            →    GP0 (pino 1)
SCL            →    GP1 (pino 2)
```

### Encoder KY040
```
KY040          →    Pi Pico 2
VCC            →    3.3V (pino 36)
GND            →    GND (pino 38)
CLK            →    GP14 (pino 19)
DT             →    GP15 (pino 20)
SW             →    GP16 (pino 21)
```

### Comunicação Modbus (UART)
```
Modbus Device  →    Pi Pico 2
TX             →    GP1 (pino 2) - RX do Pico
RX             →    GP0 (pino 1) - TX do Pico
GND            →    GND (pino 38)
VCC            →    5V (pino 40) ou fonte externa
```

### Saídas PWM
```
Canal PWM      →    Pi Pico 2    →    Driver/Relé
PWM 1          →    GP12 (pino 16) → Canal 1
PWM 2          →    GP11 (pino 15) → Canal 2  
PWM 3          →    GP10 (pino 14) → Canal 3
PWM 4          →    GP7 (pino 10)  → Canal 4
PWM 5          →    GP3 (pino 5)   → Canal 5
PWM 6          →    GP4 (pino 6)   → Canal 6
```

### Entradas/Saídas Digitais
```
Função               →    Pi Pico 2
Entrada Máquina      →    GP5 (pino 7)  - Pull-up interno
Saída Máquina Pronta →    GP6 (pino 9)  - Para relé/LED
```

## 🛠️ Métodos de Upload dos Arquivos

### Método 1: Thonny IDE (Recomendado)
```bash
# 1. Instale Thonny: https://thonny.org/
# 2. Configure: Tools → Options → Interpreter
# 3. Selecione: "MicroPython (Raspberry Pi Pico)"
# 4. Porta: Detecta automaticamente
# 5. Abra cada arquivo .py e salve no dispositivo (Ctrl+Shift+S)
```

### Método 2: rshell
```bash
# Instalar rshell
pip install rshell

# Conectar ao Pico
rshell -p /dev/ttyACM0  # Linux/Mac
rshell -p COM3          # Windows

# Copiar arquivos
cp *.py /pyboard/
```

### Método 3: ampy
```bash
# Instalar ampy
pip install adafruit-ampy

# Upload individual
ampy -p /dev/ttyACM0 put main_pico.py main.py
ampy -p /dev/ttyACM0 put IOs_pico.py
ampy -p /dev/ttyACM0 put KY040_pico.py
ampy -p /dev/ttyACM0 put Lcd_pico.py
ampy -p /dev/ttyACM0 put PID_pico.py
ampy -p /dev/ttyACM0 put Dados_pico.py
```

### Método 4: MicroPython Web REPL
```python
# 1. Ative WebREPL no Pico:
import webrepl_setup
# Siga as instruções para configurar WiFi e senha

# 2. Acesse via navegador:
# http://micropython.org/webrepl/
# Conecte e faça upload dos arquivos
```

## ⚙️ Configuração Inicial

### 1. Teste de Hardware
```python
# Execute o arquivo de testes
import test_pico2
# Ou execute individualmente cada teste
```

### 2. Configuração de Endereços I2C
```python
# Escaneie dispositivos I2C
from machine import I2C, Pin
i2c = I2C(0, sda=Pin(0), scl=Pin(1))
devices = i2c.scan()
print([hex(d) for d in devices])
# Exemplo: ['0x27'] - LCD encontrado
```

### 3. Ajuste de Parâmetros
```python
# Edite as configurações padrão nos arquivos:

# IOs_pico.py - Configurar UART
uart_id = 0
baudrate = 9600
tx_pin = 0  
rx_pin = 1

# PID_pico.py - Ajustar limites
output_min = 0
output_max = 100
interval = 0.5  # segundos
```

## 🚀 Execução

### Execução Manual
```python
# Via REPL ou Thonny:
import main_pico
# O programa iniciará imediatamente
```

### Execução Automática
```bash
# Renomeie main_pico.py para main.py
# O programa iniciará automaticamente ao energizar o Pico
```

### Monitoramento via Serial
```bash
# Linux/Mac
screen /dev/ttyACM0 115200

# Windows (PuTTY)
# COM Port: COMx
# Speed: 115200
# Connection Type: Serial
```

## 🔍 Diagnósticos

### Verificar Memória
```python
import gc
print(f"Memória livre: {gc.mem_free()} bytes")
print(f"Memória alocada: {gc.mem_alloc()} bytes")
```

### Verificar Arquivos
```python
import os
print("Arquivos:", os.listdir())
```

### Verificar Threading
```python
import _thread
print(f"Stack size: {_thread.stack_size()}")
```

### Reset do Sistema
```python
import machine
machine.soft_reset()  # Reset suave
machine.reset()       # Reset completo
```

## ⚠️ Troubleshooting Comum

### Erro: "OSError: [Errno 2] ENOENT"
```python
# Arquivo não encontrado - verifique upload
import os
print(os.listdir())
```

### Erro: "ImportError: no module named 'ujson'"
```python
# Use json padrão se ujson não estiver disponível
try:
    import ujson as json
except ImportError:
    import json
```

### Erro: "I2C Bus Error"
```python
# Verifique conexões físicas
# Teste com pull-up externo (4.7kΩ)
from machine import I2C, Pin
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
```

### Erro: "Memory allocation failed"
```python
# Libere memória
import gc
gc.collect()
# Reduza intervalos ou tamanho de buffers
```

### PWM não funciona corretamente
```python
# Verifique se as threads estão rodando
print(io.io_rpi.pwm_thread_running)
# Ajuste o período PWM
io.io_rpi.set_pwm_period(1.0)  # 1Hz
```

## 📊 Monitoramento de Performance

### CPU e Memória
```python
import gc, time, machine

def monitor_system():
    while True:
        print(f"CPU: {machine.freq()/1000000:.1f}MHz")
        print(f"RAM: {gc.mem_free()}B livre")
        print(f"Temp: {machine.ADC(4).read_u16() * 3.3 / 65535:.1f}V")
        time.sleep(5)
```

### Threading Status
```python
def check_threads():
    try:
        import _thread
        print("Threading disponível")
        print(f"Stack size: {_thread.stack_size()}")
    except:
        print("Threading não disponível")
```

## 🔄 Atualizações

### Backup de Configurações
```python
# Antes de atualizar, faça backup
import json
with open("backup_config.json", "w") as f:
    json.dump({
        "setpoints": setpoint_list,
        "kp": kp_list,
        "ki": ki_list, 
        "kd": kd_list
    }, f)
```

### Upload de Nova Versão
```bash
# Use rshell ou Thonny para substituir arquivos
# Mantenha arquivos de configuração .json
```

---
**💡 Dica**: Sempre teste as modificações no arquivo `test_pico2.py` antes de usar no sistema principal.