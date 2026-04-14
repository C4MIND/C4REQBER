# TURBO-CDI v6.0 Canvas Module

**Интерактивный визуальный canvas для TURBO-CDI**

## Что это?

Модуль `canvas` — это слой визуализации для TURBO-CDI v6.0, который автоматически генерирует:

- **C4 Visual Map** — 3D изометрическая проекция 27 когнитивных состояний
- **Architecture Diagrams** — UML/C4 диаграммы из гипотез
- **Simulation Results** — Small multiples для сравнения результатов
- **Infographics** — для презентаций и публикаций

## Быстрый старт

```bash
cd v6/canvas
npm install
npm run dev
```

Откроется `http://localhost:3001` с демо C4 Visual Map.

## Архитектура

```
canvas/
├── src/
│   ├── components/
│   │   ├── Canvas.tsx           # Базовый SVG canvas
│   │   ├── C4VisualMap.tsx      # 3D изометрическая сетка C4
│   │   └── index.ts             # Экспорты
│   ├── types/
│   │   └── index.ts             # TypeScript типы
│   ├── utils/
│   │   └── svg.ts               # SVG утилиты (isometric, etc.)
│   └── demo.tsx                 # Демо страница
├── public/
│   └── index.html
└── package.json
```

## Компоненты

### C4VisualMap

Интерактивная 3D визуализация 27 состояний C4 (Z₃³).

```tsx
import { C4VisualMap } from './components'

function App() {
  const [selected, setSelected] = useState('111')
  
  return (
    <C4VisualMap
      width={1000}
      height={700}
      selectedState={selected}
      onStateSelect={(state) => setSelected(state.code)}
      showTransitions={true}
    />
  )
}
```

**Фичи:**
- Изометрическая проекция 27 кубов
- Цветовое кодирование по времени (Past=blue, Present=green, Future=purple)
- Hover для подробной информации
- Click для выбора
- Drag to pan, scroll to zoom
- Анимированные переходы между состояниями

### Canvas (базовый)

Базовый SVG canvas с viewport management.

```tsx
import { Canvas } from './components'

<Canvas
  width={800}
  height={600}
  nodes={nodes}
  edges={edges}
  viewport={{ x: 0, y: 0, zoom: 1 }}
  onEvent={(e) => console.log(e)}
/>
```

## Технологии

- **React 18** — UI framework
- **TypeScript** — type safety
- **SVG** — векторная графика
- **Vite** — build tool

## Цветовая схема

| Цвет | Значение | HEX |
|------|----------|-----|
| Background | Фон | `#0f0f1a` |
| Primary | Акцент | `#4ECDC4` |
| Secondary | Алерт | `#FF6B6B` |
| Accent | Подсветка | `#FFE66D` |
| Past | C4 время | `#3498db` |
| Present | C4 время | `#2ecc71` |
| Future | C4 время | `#9b59b6` |

## Roadmap

### Phase 1 (Недели 1-3) — Готово!
- ✅ C4 Visual Map
- ✅ Базовый Canvas
- ✅ Isometric projection

### Phase 2 (Недели 4-6)
- [ ] Architecture Diagram Generator
- [ ] UML auto-generation from hypotheses
- [ ] C4 Model diagrams (Context/Container/Component)

### Phase 3 (Недели 7-8)
- [ ] Small Multiples для симуляций
- [ ] Sparklines для confidence trends
- [ ] Infographic templates

### Phase 4 (Недели 9-12)
- [ ] Интеграция с Simulation Engine
- [ ] Real-time updates
- [ ] Export to PNG/PDF

## Изометрическая проекция

Формула для 3D → 2D:
```
x' = x_center + (x - z) * cos(30°)
y' = y_center + (x + z) * sin(30°) - y
```

Каждое C4 состояние — это куб в 3D пространстве:
- X: Agency (-1, 0, 1)
- Y: Scale (-1, 0, 1)
- Z: Time (-1, 0, 1)

## Символика

- `◈` — Primary / C4
- `◉` — Status / TRIZ
- `●` — Complete
- `○` — Pending
- `◔` — Clock

## Лицензия

MIT
