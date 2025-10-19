# 🧵 Threading no Raspberry Pi Pico 2 - Problemas e Soluções

## 🚨 **Problema: "core1 in use"**

### 📋 **Causa do Erro**

O erro `core1 in use` acontece porque:

1. **Pi Pico 2 tem apenas 2 cores** (core0 e core1)
2. **MicroPython usa core0** para o programa principal
3. **Apenas uma thread pode rodar no core1** simultaneamente
4. **Nosso sistema tenta criar 2 threads**:
   - Thread PWM (IOs_pico.py)
   - Thread PID (PID_pico.py)

### 🔍 **Log de Erro Analisado**

```
🚀 Iniciando controle PID...
Erro ao iniciar thread PID: core1 in use
```

**Sequência dos eventos**:
1. ✅ IO_MODBUS inicializa InOut
2. ✅ InOut cria thread PWM no core1 
3. ❌ PIDController tenta criar thread PID no core1 → **FALHA**

## 🛠️ **Soluções Implementadas**

### **1. Threading Resiliente**

#### **IOs_pico.py**
```python
try:
    _thread.start_new_thread(self._pwm_control_all, ())
    print("Thread PWM iniciada no core1")
except Exception as e:
    print(f"Aviso PWM thread: {e}")
    print("PWM funcionará em modo síncrono")
    self.pwm_thread_running = False
```

#### **PID_pico.py** 
```python
try:
    self._thread_id = _thread.start_new_thread(self._run, (interval,))
    print("Thread PID iniciada no core1")
    self._use_thread = True
except Exception as e:
    print(f"Aviso thread PID: {e}")
    print("Executando PID no core principal (sem thread separada)")
    self._use_thread = False
```

### **2. Modo Híbrido**

O sistema agora funciona em **3 modos**:

| Modo | PWM Thread | PID Thread | Desempenho |
|------|------------|------------|------------|
| **Otimal** | ✅ Core1 | ❌ Core0 | Alto |
| **Degradado** | ❌ Core0 | ❌ Core0 | Médio |
| **Manual** | ❌ Síncrono | ❌ Manual | Baixo |

### **3. Controle Manual**

Quando threads falham, o sistema usa controle manual:

```python
# No main loop
if not hasattr(pid, '_use_thread') or not pid._use_thread:
    if time.ticks_diff(current_time, last_pid_update) >= 2000:  # 2s
        pid.control_step()  # Executa PID manualmente
        last_pid_update = current_time
```

## 🎯 **Estratégias de Threading**

### **Prioridade 1: PWM Thread**
- **Mais crítico** - controla saídas físicas
- **Primeira tentativa** de usar core1
- **Fallback**: PWM síncrono no core0

### **Prioridade 2: PID Manual**  
- **Menos crítico** - cálculos podem ser esporádicos
- **Usa core0** se core1 ocupado
- **Fallback**: Execução manual via `control_step()`

## 📊 **Performance Comparativa**

### **Com Thread PWM (Ideal)**
```
Core0: Main Loop + PID manual
Core1: PWM contínuo
Timeline: |PWM|PWM|PWM|PWM|PWM|PWM|
         |Main+PID |Main+PID |Main+PID |
```

### **Sem Threads (Degradado)**
```
Core0: Main + PWM + PID (tudo junto)
Core1: Idle
Timeline: |Main|PWM|PID|Main|PWM|PID|
```

## 🔧 **Configurações de Timing**

### **Thread PWM**
```python
self.pwm_period = 1.0  # 1 segundo por ciclo
time.sleep_ms(100)     # 100ms entre verificações
```

### **PID Manual**
```python
pid_interval = 2000    # 2 segundos entre cálculos PID
time.sleep_ms(500)     # 500ms no main loop
```

## 🐛 **Troubleshooting Threading**

### **Verificar Estado das Threads**
```python
# Verificar PWM
print(f"PWM Thread Running: {io.io_rpi.pwm_thread_running}")

# Verificar PID
print(f"PID Using Thread: {pid._use_thread}")
print(f"PID Running: {pid._running}")
```

### **Forçar Modo Manual**
```python
# Forçar PWM síncrono
io.io_rpi.pwm_thread_running = False

# Forçar PID manual
pid._use_thread = False
```

### **Monitorar Performance**
```python
import gc
import time

start = time.ticks_ms()
# ... código ...
elapsed = time.ticks_diff(time.ticks_ms(), start)
print(f"Loop time: {elapsed}ms")
print(f"Free RAM: {gc.mem_free()} bytes")
```

## 📋 **Checklist de Threading**

- [ ] **PWM Thread** iniciou com sucesso?
- [ ] **Core1** disponível ou ocupado?
- [ ] **PID** funcionando (thread ou manual)?
- [ ] **Timing** adequado (não muito rápido)?
- [ ] **Memória** suficiente para threads?

## 🔍 **Logs de Diagnóstico**

### **Sucesso Total**
```
Thread PWM iniciada no core1
Thread PID iniciada no core1  ❌ IMPOSSÍVEL (só 1 thread/core)
```

### **Sucesso Parcial (Esperado)**
```
Thread PWM iniciada no core1
Aviso thread PID: core1 in use
Executando PID no core principal (sem thread separada)
```

### **Falha Total**
```
Aviso PWM thread: core1 in use
PWM funcionará em modo síncrono
Aviso thread PID: core1 in use  
Executando PID no core principal (sem thread separada)
```

## 💡 **Otimizações Futuras**

### **1. Threading Coordenado**
- Usar apenas 1 thread para PWM+PID
- Coordenar timing entre sistemas

### **2. Timer-based Control**
- Usar `machine.Timer` em vez de threads
- Melhor controle de timing

### **3. PWM Hardware**
- Usar `machine.PWM` para frequências >10Hz
- Liberar core1 para PID

---

**🎯 Resumo**: O erro "core1 in use" é **normal e esperado** no Pi Pico 2. O sistema foi projetado para **degradar graciosamente** e continuar funcionando mesmo com limitações de threading.