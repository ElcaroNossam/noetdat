# Настройка высоты графика в торговом терминале

## Текущая система

Высота графика рассчитывается автоматически на основе размера окна браузера. Это обеспечивает адаптивность под разные размеры экранов.

## Где настраивается высота

### 1. JavaScript (автоматический расчет)

Файл: `templates/screener/trading_terminal.html`

Функция `calculateChartHeight()` содержит настраиваемые параметры:

```javascript
const MIN_HEIGHT = 400;        // Минимальная высота в пикселях
const MAX_HEIGHT = null;       // Максимальная высота (null = без ограничений)
const HEADER_OFFSET = 150;     // Отступ для хедера
const SIDEBAR_OFFSET = 200;    // Отступ для сайдбара
const EXTRA_PADDING = 50;      // Дополнительный отступ
```

### 2. CSS (фиксированная высота)

Файл: `static/css/style.css`

Класс `.tradingview-widget-container`:

```css
.tradingview-widget-container {
    width: 100%;
    height: calc(100vh - 250px);  /* Можно изменить это значение */
    min-height: 400px;             /* Минимальная высота */
    max-height: 90vh;              /* Максимальная высота */
    position: relative;
}
```

## Как изменить высоту

### Вариант 1: Изменить параметры в JavaScript

Откройте `templates/screener/trading_terminal.html` и найдите функцию `calculateChartHeight()`:

- **Увеличить высоту:** уменьшите `HEADER_OFFSET`, `SIDEBAR_OFFSET` или `EXTRA_PADDING`
- **Уменьшить высоту:** увеличьте эти значения
- **Установить фиксированную высоту:** верните фиксированное значение вместо расчета

Пример для фиксированной высоты 600px:
```javascript
function calculateChartHeight() {
    return 600;  // Фиксированная высота
}
```

### Вариант 2: Изменить CSS

Откройте `static/css/style.css` и найдите `.tradingview-widget-container`:

- **Увеличить высоту:** измените `calc(100vh - 250px)` на `calc(100vh - 150px)`
- **Уменьшить высоту:** увеличьте вычитаемое значение, например `calc(100vh - 350px)`
- **Фиксированная высота:** замените на `height: 600px;`

### Вариант 3: Использовать CSS переменные (рекомендуется)

Добавьте в начало `style.css`:
```css
:root {
    --chart-min-height: 400px;
    --chart-max-height: 90vh;
    --chart-offset: 250px;
}

.tradingview-widget-container {
    height: calc(100vh - var(--chart-offset));
    min-height: var(--chart-min-height);
    max-height: var(--chart-max-height);
}
```

## Примеры настроек

### Высокий график (занимает почти весь экран)
```javascript
const HEADER_OFFSET = 100;
const SIDEBAR_OFFSET = 100;
const EXTRA_PADDING = 20;
```

### Компактный график
```javascript
const HEADER_OFFSET = 200;
const SIDEBAR_OFFSET = 300;
const EXTRA_PADDING = 100;
```

### Фиксированная высота 800px
```javascript
function calculateChartHeight() {
    return 800;
}
```

## Автоматическое обновление

Высота автоматически пересчитывается при изменении размера окна браузера благодаря обработчику `resize`.

