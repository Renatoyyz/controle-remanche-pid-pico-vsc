# 🚨 Guia de Resolução de Problemas - Pi Pico 2

Este documento explica os avisos que aparecem quando o sistema é executado sem hardware físico conectado.

## 🔍 **Análise dos Avisos Encontrados**

### 1. **"Endereços I2C encontrados: []"**
```
Endere��os I2C encontrados: []
```

**Causa**: O sistema escaneia o barramento I2C procurando dispositivos conectados (display LCD).
**Solução**: Normal quando não há hardware conectado. O display LCD deveria aparecer em `0x27` ou `0x3F`.

### 2. **"Erro crítico: LCD não encontrado"**
```
Erro cr��tico: LCD n��o encontrado. Endere��os dispon��veis: []
```

**Causa**: O código para a execução porque o LCD é obrigatório para a interface.
**Solução**: Use a versão "safe" que detecta automaticamente e ativa modo simulado.

### 3. **"Erro durante cleanup: local variable referenced before assignment"**
```
Erro durante cleanup: local variable referenced before assignment
```

**Causa**: Como o LCD falhou na inicialização, a variável `lcd` não foi criada, mas o cleanup tenta usá-la.
**Solução**: Verificação `if 'lcd' in locals()` antes do cleanup.

## 🛠️ **Soluções Implementadas**

### **Versões "Safe" dos Módulos**

Criei versões que funcionam sem hardware:

- `Lcd_pico_safe.py` - LCD com modo simulado
- `KY040_pico_safe.py` - Encoder com modo simulado  
- `main_pico_safe.py` - Main com detecção automática de hardware

### **Como Usar sem Hardware**

```python
# Execute a versão segura
import main_pico_safe

# Ou force o modo simulado individualmente
from Controller.Lcd_pico_safe import Lcd
from Controller.KY040_pico_safe import KY040

lcd = Lcd(fake_mode=True)
encoder = KY040(fake_mode=True)
```

## 🧪 **Modo Teste (Simulação)**

Quando não há hardware conectado, o sistema automaticamente:

1. **Detecta ausência de dispositivos I2C**
2. **Ativa modo simulado automaticamente**
3. **Simula todas as funcionalidades**:
   - LCD mostra saídas no console
   - Encoder varia automaticamente
   - Temperaturas são simuladas
   - PWM é controlado virtualmente

### **Saída do Modo Simulado**

```
🧪 === MODO TESTE ATIVADO ===
⚠️  Executando sem hardware físico conectado
📱 As funcionalidades serão simuladas

💾 Setpoints carregados de setpoint_list.json
💾 Valores PID carregados de pid_values.json
🔧 Inicializando componentes simulados...

🖥️  FakeLCD inicializado (simulação)
   Configurado para I2C0: SDA=GP0, SCL=GP1

UART0 configurada: TX=GP0, RX=GP1, Baud=9600
Usando modo simulado (fake_modbus = True)

🕹️  FakeKY040 inicializado (simulação)
   Pinos: CLK=GP14, DT=GP15, SW=GP16
   Range: 1 - 2

Thread PID iniciada
✅ Sistema inicializado. Executando simulação por 30 segundos...

LCD L1: **** QUALIFIX ****  
LCD L2: Iniciar             
LCD L3: Configuracoes       
🎮 Simulando: Iniciando execução...
🖥️  LCD: Tela limpa
LCD L1: **** AGUARDE ****   
Está na tela: EXECUCAO
Controle PID ativado
🖥️  LCD: Tela limpa
LCD L1: Execucao            
LCD L2: 1:87.0 4:34.0       
LCD L3: 2:109.0 5:78.0      
LCD L4: 3:54.0 6:92.0       
```

## 🔧 **Configuração de Hardware Real**

Para usar com hardware físico:

### **Conexões I2C (Display LCD)**
```
LCD PCF8574    →    Pi Pico 2
VCC            →    3.3V (pino 36)
GND            →    GND (pino 38)  
SDA            →    GP0 (pino 1)
SCL            →    GP1 (pino 2)
```

### **Verificação do Hardware**
```python
# Teste manual do I2C
from machine import I2C, Pin

i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
devices = i2c.scan()
print(f"Dispositivos encontrados: {[hex(d) for d in devices]}")

# Deve retornar algo como: ['0x27'] para LCD
```

### **Endereços I2C Comuns**
- **LCD 20x4**: `0x27` ou `0x3F`
- **OLED**: `0x3C` ou `0x3D`
- **RTC**: `0x68`

## 🚀 **Como Executar**

### **1. Teste sem Hardware (Recomendado)**
```python
# Execute no Pi Pico 2
import main_pico_safe

# Sistema detecta automaticamente ausência de hardware
# e ativa modo simulação
```

### **2. Forçar Modo Simulado**
```python
# Se quiser forçar simulação mesmo com hardware
from Controller.Lcd_pico_safe import Lcd
from Controller.KY040_pico_safe import KY040

lcd = Lcd(fake_mode=True)  # Força modo simulado
encoder = KY040(fake_mode=True)  # Força modo simulado
```

### **3. Hardware Real**
```python
# Quando tiver hardware conectado
import main_pico  # Versão original

# Ou use a versão safe que detecta automaticamente
import main_pico_safe  # Detecta hardware e usa modo real
```

## 🔍 **Diagnósticos**

### **Verificar Arquivos no Pi Pico**
```python
import os
print("Arquivos:", os.listdir())
# Deve mostrar: setpoint_list.json, pid_values.json, etc.
```

### **Verificar Memória**
```python
import gc
print(f"RAM livre: {gc.mem_free()} bytes")
print(f"RAM usada: {gc.mem_alloc()} bytes")
```

### **Verificar I2C**
```python
from machine import I2C, Pin
try:
    i2c = I2C(0, sda=Pin(0), scl=Pin(1))
    devices = i2c.scan()
    print(f"I2C OK: {devices}")
except Exception as e:
    print(f"I2C Error: {e}")
```

## 📋 **Checklist de Problemas**

- [ ] **Arquivos carregados?** `setpoint_list.json` e `pid_values.json` existem?
- [ ] **I2C funcionando?** Scan retorna dispositivos?
- [ ] **Pinos corretos?** SDA=GP0, SCL=GP1 para I2C0?
- [ ] **Alimentação OK?** 3.3V para LCD, 5V se necessário?
- [ ] **Cabos OK?** Conexões firmes e sem curto?

## 🎯 **Resumo**

Os avisos que você viu são **normais** quando executa sem hardware. O sistema:

1. ✅ **Carregou as configurações** (JSON)
2. ❌ **Não encontrou LCD** (esperado sem hardware)
3. ❌ **Falhou no cleanup** (variável não criada)

**Solução**: Use `main_pico_safe.py` que detecta automaticamente e simula o hardware ausente.

---

**💡 Dica**: O modo simulado é perfeito para desenvolver e testar a lógica do sistema antes de conectar o hardware real!