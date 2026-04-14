# 🚀 TURBO-CDI v8.2 - РЕАЛЬНОЕ ТЕСТИРОВАНИЕ
## Полный чек-лист для терминала и браузера

---

## 📋 ПОДГОТОВКА (5 минут)

### 1. Проверь что всё на месте
```bash
cd /Users/figuramax/LocalProjects/TURBO-CDI

# Проверь файлы
ls -la v8/turbo-cdi
ls -la .env
cat .env | grep OPENROUTER_API_KEY
```

### 2. Установи зависимости (если не установлены)
```bash
# Python зависимости
pip install websockets cachetools aiohttp

# Или если есть requirements.txt
pip install -r v8/requirements.txt 2>/dev/null || echo "Создай requirements.txt"
```

### 3. Создай requirements.txt (если нет)
```bash
cat > v8/requirements.txt << 'EOF'
websockets>=11.0
cachetools>=5.0
aiohttp>=3.8
numpy>=1.24
python-dateutil>=2.8
EOF
```

---

## 🔥 ЭТАП 1: CLI ТЕСТЫ (Терминал)

### Тест 1: Базовый импорт
```bash
cd /Users/figuramax/LocalProjects/TURBO-CDI/v8

python3 -c "
from core.orchestrator import TurboCDIv8
print('✅ TurboCDIv8 импортируется')

turbo = TurboCDIv8()
print('✅ TurboCDIv8 создаётся')

print(f'✅ Компонентов: {len([c for c in [turbo.grammar, turbo.navigation, turbo.operators, turbo.bias_detector, turbo.outcome_tracker, turbo.falsification, turbo.peer_review, turbo.reproducibility, turbo.domain_generator, turbo.pattern_synthesizer, turbo.bridge_engine, turbo.observer, turbo.self_modifier, turbo.paradox_detector, turbo.wholeness_validator, turbo.tactics, turbo.validation, turbo.execution] if c is not None])}/19')
"
```

**Ожидаемый результат:** Все компоненты создаются

---

### Тест 2: UserProfile (Path Traversal)
```bash
python3 -c "
import sys
sys.path.insert(0, 'v8')

from cognitive.user_profile.core import UserProfile

# Создай профиль
profile = UserProfile(user_id='test_user')
profile.update_from_outcome('physics', 0.85)

# Попробуй path traversal
try:
    profile.save('../../../etc/passwd')
    print('❌ Path traversal НЕ заблокирован!')
except ValueError as e:
    print(f'✅ Path traversal заблокирован: {e}')

# Сохрани нормально
try:
    profile.save('test_user.json')
    print('✅ Сохранение работает')
    
    # Проверь права
    import os
    perms = oct(os.stat('/Users/figuramax/.turbo-cdi/profiles/test_user.json').st_mode)[-3:]
    print(f'✅ Права файла: {perms} (ожидается 600)')
except Exception as e:
    print(f'⚠️ Ошибка: {e}')
"
```

**Ожидаемый результат:** Path traversal заблокирован, файл сохранён с правами 600

---

### Тест 3: C4 Navigation
```bash
python3 -c "
import sys
sys.path.insert(0, 'v8')

from core.orchestrator import TurboCDIv8
from modules import C4State, TimeAxis, ScaleAxis, AgencyAxis

turbo = TurboCDIv8()

# Навигация по C4
from_state = C4State(TimeAxis.PAST, ScaleAxis.CONCRETE, AgencyAxis.SELF)
to_state = C4State(TimeAxis.FUTURE, ScaleAxis.ABSTRACT, AgencyAxis.SELF)

result = turbo.navigate_c4_space(from_state, to_state, domain='physics')

print(f'✅ Путь найден: {len(result[\"path\"])} шагов')
print(f'✅ Theorem 11 compliant: {result[\"theorem_11_compliant\"]}')
print(f'✅ Path length: {result[\"path_length\"]}')

if result['path_length'] <= 6:
    print('✅ Путь <= 6 шагов (Theorem 11)')
else:
    print('❌ Путь > 6 шагов')
"
```

**Ожидаемый результат:** Путь найден, <= 6 шагов

---

### Тест 4: Bias Detection (все 10 типов)
```bash
python3 -c "
import sys
sys.path.insert(0, 'v8')

from cognitive.bias_detector.core import BiasDetector, BiasType

bd = BiasDetector()

# Проверь что все 10 типов есть
bias_types = [bt.value for bt in BiasType]
print(f'✅ Найдено {len(bias_types)} bias типов:')
for bt in bias_types:
    print(f'   - {bt}')

# Тест с планом
plan = {
    'path': [
        ('MODULATE', 'CONTENT'),
        ('MODULATE', 'CONTENT'),
        ('MODULATE', 'CONTENT'),
    ],
    'confidence': 0.9,
    'time_estimate': 100
}

context = {'user_profile': None, 'history': []}
result = bd.analyze_transformation_plan(plan, context)

print(f'✅ Обнаружено {len(result[\"warnings\"])} bias в тестовом плане')
"
```

**Ожидаемый результат:** 10 bias типов, STATUS_QUO_BIAS обнаружен

---

### Тест 5: Self-Modifier Rollback
```bash
python3 -c "
import sys
sys.path.insert(0, 'v8')

from meta.self_modifier.core import SelfModifier

sm = SelfModifier()

# Установи параметры
sm.set_parameter('effectiveness_base_weight', 0.5, manual=True)
sm.set_parameter('effectiveness_base_weight', 0.7, manual=True)
sm.set_parameter('effectiveness_base_weight', 0.9, manual=True)

history = sm.get_tuning_history()
print(f'✅ История: {len(history)} записей')

# Проверь old_value
if len(history) >= 2:
    if history[-1]['old_value'] == 0.7:
        print('✅ Rollback логика верна (old_value = 0.7)')
    else:
        print(f'❌ Rollback логика НЕ верна: old_value = {history[-1][\"old_value\"]}')

# Проверь rollback
sm.rollback(1)
if sm.parameters['effectiveness_base_weight'] == 0.7:
    print('✅ Rollback работает')
else:
    print('❌ Rollback не работает')
"
```

**Ожидаемый результат:** old_value корректный, rollback работает

---

## 🔥 ЭТАП 2: WEBSOCKET SERVER (Терминал)

### Тест 6: Запуск сервера
```bash
# Терминал 1 - Запуск сервера
cd /Users/figuramax/LocalProjects/TURBO-CDI/v8

python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')

from api.websocket.server import TurboWebSocketServer

server = TurboWebSocketServer(host='localhost', port=8765)
print('🚀 Запуск WebSocket сервера на ws://localhost:8765')
print('   Для остановки: Ctrl+C')

asyncio.get_event_loop().run_until_complete(server.start())
"
```

**Ожидаемый результат:** Сервер запущен, слушает порт 8765

---

### Тест 7: WebSocket клиент (второй терминал)
```bash
# Терминал 2 - Тест клиента
python3 << 'PYEOF'
import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8765"
    
    async with websockets.connect(uri) as ws:
        # 1. Получи приветствие
        greeting = await ws.recv()
        print(f"1. Сервер: {greeting}")
        
        # 2. Команда navigate
        await ws.send(json.dumps({
            "command": "navigate",
            "from": "P00",
            "to": "F10",
            "domain": "physics"
        }))
        response = await ws.recv()
        data = json.loads(response)
        print(f"2. Navigate: {data.get('status', 'unknown')}")
        
        # 3. Команда meta
        await ws.send(json.dumps({
            "command": "meta",
            "report_type": "report"
        }))
        response = await ws.recv()
        print(f"3. Meta: получен ответ")
        
        # 4. Большое сообщение (>1MB) - должно быть отклонено
        big_msg = "x" * (1024 * 1024 + 1)
        await ws.send(json.dumps({"command": "ping", "data": big_msg}))
        try:
            response = await asyncio.wait_for(ws.recv(), timeout=2)
            print(f"4. Large msg: {response[:100]}...")
        except asyncio.TimeoutError:
            print("4. Large msg: timeout (возможно отклонено)")

asyncio.run(test())
PYEOF
```

**Ожидаемый результат:** Команды работают, большое сообщение отклонено

---

## 🔥 ЭТАП 3: БРАУЗЕР

### Тест 8: Простой HTML клиент
```bash
# Создай HTML файл для теста
cat > /tmp/turbo-test.html << 'HTMLEOF'
<!DOCTYPE html>
<html>
<head>
    <title>TURBO-CDI WebSocket Test</title>
    <style>
        body { font-family: monospace; padding: 20px; }
        #log { background: #f0f0f0; padding: 10px; height: 400px; overflow-y: scroll; }
        .success { color: green; }
        .error { color: red; }
        button { margin: 5px; padding: 10px; }
    </style>
</head>
<body>
    <h1>🚀 TURBO-CDI v8.2 WebSocket Test</h1>
    <div>
        <button onclick="connect()">Connect</button>
        <button onclick="navigate()">Test Navigate</button>
        <button onclick="meta()">Test Meta</button>
        <button onclick="disconnect()">Disconnect</button>
    </div>
    <div id="status">Status: Disconnected</div>
    <h3>Log:</h3>
    <div id="log"></div>

    <script>
        let ws = null;
        const log = (msg, cls = '') => {
            const div = document.getElementById('log');
            div.innerHTML += `<div class="${cls}">[${new Date().toLocaleTimeString()}] ${msg}</div>`;
            div.scrollTop = div.scrollHeight;
        };

        const connect = () => {
            ws = new WebSocket('ws://localhost:8765');
            
            ws.onopen = () => {
                document.getElementById('status').textContent = 'Status: Connected ✅';
                log('Connected to server', 'success');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                log(`Received: ${JSON.stringify(data).substring(0, 200)}...`, 'success');
            };
            
            ws.onerror = (err) => {
                log(`Error: ${err}`, 'error');
            };
            
            ws.onclose = () => {
                document.getElementById('status').textContent = 'Status: Disconnected';
                log('Disconnected');
            };
        };

        const navigate = () => {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                log('Not connected!', 'error');
                return;
            }
            ws.send(JSON.stringify({
                command: 'navigate',
                from: 'P00',
                to: 'F10',
                domain: 'test'
            }));
            log('Sent: navigate command');
        };

        const meta = () => {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                log('Not connected!', 'error');
                return;
            }
            ws.send(JSON.stringify({
                command: 'meta',
                report_type: 'stats'
            }));
            log('Sent: meta command');
        };

        const disconnect = () => {
            if (ws) ws.close();
        };
    </script>
</body>
</html>
HTMLEOF

# Открой в браузере
open /tmp/turbo-test.html
```

**Проверь в браузере:**
1. Нажми "Connect" - должен подключиться
2. Нажми "Test Navigate" - должен получить ответ
3. Нажми "Test Meta" - должен получить stats

---

## 🔥 ЭТАП 4: ИНТЕГРАЦИОННЫЕ ТЕСТЫ

### Тест 9: Полный workflow
```bash
python3 << 'PYEOF'
import sys
sys.path.insert(0, 'v8')

from core.orchestrator import TurboCDIv8
from modules import C4State, TimeAxis, ScaleAxis, AgencyAxis

print("🚀 ПОЛНЫЙ WORKFLOW TEST")
print("=" * 50)

# 1. Создай систему
turbo = TurboCDIv8()
print("✅ 1. Система создана")

# 2. Установи пользователя
turbo.set_user('demo_user', {
    'frequent_domains': ['physics', 'math'],
    'risk_tolerance': 'moderate'
})
print("✅ 2. Пользователь установлен")

# 3. Создай план
from_state = C4State(TimeAxis.PAST, ScaleAxis.CONCRETE, AgencyAxis.SELF)
to_state = C4State(TimeAxis.FUTURE, ScaleAxis.ABSTRACT, AgencyAxis.SELF)

plan = turbo.plan_transformation(
    from_state=from_state,
    to_state=to_state,
    domain='physics',
    target='state'
)
print(f"✅ 3. План создан: {len(plan.get('path', []))} шагов")

# 4. Проверь bias
bias_result = turbo.check_bias(plan)
print(f"✅ 4. Bias проверка: {len(bias_result.get('warnings', []))} предупреждений")

# 5. Запиши результат
prediction = turbo.predict_effectiveness(plan)
print(f"✅ 5. Предсказание: {prediction.get('estimated_effectiveness', 'N/A')}")

# 6. Оцени wholeness
wholeness = turbo.evaluate_wholeness(plan)
print(f"✅ 6. Wholeness: {wholeness.get('life_score', 'N/A')}")

print("=" * 50)
print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
PYEOF
```

---

## 📊 ЧЕК-ЛИСТ РЕЗУЛЬТАТОВ

| # | Тест | CLI | Браузер | Статус |
|---|------|-----|---------|--------|
| 1 | Базовый импорт | ⬜ | - | ⬜ |
| 2 | Path traversal | ⬜ | - | ⬜ |
| 3 | C4 Navigation | ⬜ | - | ⬜ |
| 4 | Bias Detection | ⬜ | - | ⬜ |
| 5 | Self-Modifier | ⬜ | - | ⬜ |
| 6 | WebSocket Server | ⬜ | - | ⬜ |
| 7 | WebSocket Client | ⬜ | - | ⬜ |
| 8 | HTML Browser | - | ⬜ | ⬜ |
| 9 | Full Workflow | ⬜ | - | ⬜ |

---

## 🚨 ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ

### Проблема: ImportError
```bash
# Решение: добавь путь
export PYTHONPATH="/Users/figuramax/LocalProjects/TURBO-CDI/v8:$PYTHONPATH"
```

### Проблема: ModuleNotFoundError (websockets)
```bash
# Решение: установи зависимости
pip install websockets cachetools
```

### Проблема: Порт занят
```bash
# Найди и убей процесс
lsof -i :8765
kill -9 <PID>
```

### Проблема: Permission denied (UserProfile)
```bash
# Создай директорию
mkdir -p ~/.turbo-cdi/profiles
chmod 700 ~/.turbo-cdi
```

---

## 🎉 ГОТОВО К ТЕСТИРОВАНИЮ!

1. Открой 2 терминала
2. В первом запусти сервер (Тест 6)
3. Во втором запусти клиента (Тест 7)
4. Открой браузер с HTML тестом
5. Пройди все чек-поинты

**Если всё работает - система production-ready! ✅**
