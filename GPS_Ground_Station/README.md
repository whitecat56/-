# GPS Ground Station для Arduino + HC-12

Профессиональная наземная станция на Python 3 для Windows 10/11. Программа подключается к Arduino по COM-порту, принимает GPS телеметрию от HC-12, показывает координаты, высоту, маршрут и приборную панель в современном темном интерфейсе.

## Возможности

- PyQt6 интерфейс с темной темой, стеклянными панелями, градиентами и анимированными индикаторами.
- Интерактивная Leaflet/Folium карта внутри приложения через PyQt6 WebEngine.
- Спутниковый слой Esri World Imagery и обычная карта OpenStreetMap.
- Автоматическое центрирование по координатам, маркер дрона и линия маршрута.
- Левая телеметрическая панель: latitude, longitude, altitude, speed, packet counter, last update.
- Правая панель связи: статус, COM-порт, connect/disconnect, качество связи, лог.
- Приборы: высотомер, компас, качество связи, счетчик пакетов.
- Автопоиск COM-портов и сохранение последнего выбранного порта.
- Экспорт маршрута в CSV и GPX.
- Запись операторского лога в `logs/ground_station.log`.
- Обработка ошибок COM-порта, парсинга и потери GPS сигнала.
- Готовность к расширению: скорость, направление, батарея, RSSI HC-12.

## Формат входных данных

Основной формат — бинарная структура Arduino/C++ размером 12 байт:

```cpp
struct GPSData {
  float latitude;
  float longitude;
  float altitude;
};
```

Также поддерживается текстовый CSV-формат для будущей телеметрии:

```text
latitude,longitude,altitude,speed,heading,battery_voltage,rssi
```

Минимальный текстовый вариант:

```text
55.751244,37.618423,148.5
```

## Установка Python на Windows 10/11

1. Откройте официальный сайт: <https://www.python.org/downloads/windows/>.
2. Скачайте Python 3.11 или 3.12 для Windows x64.
3. Запустите установщик.
4. Обязательно включите галочку **Add python.exe to PATH**.
5. Нажмите **Install Now**.
6. Проверьте установку в PowerShell:

```powershell
python --version
pip --version
```

## Установка проекта

Откройте PowerShell в папке проекта:

```powershell
cd GPS_Ground_Station
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Если PowerShell блокирует активацию виртуального окружения, выполните один раз:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Запуск

```powershell
cd GPS_Ground_Station
.\.venv\Scripts\Activate.ps1
python main.py
```

## Как выбрать COM-порт

1. Подключите Arduino-приемник к USB.
2. Откройте **Device Manager / Диспетчер устройств**.
3. Найдите устройство в разделе **Ports (COM & LPT)**, например `COM5`.
4. Запустите приложение.
5. Нажмите **Refresh COM**.
6. Выберите найденный порт в выпадающем списке.
7. Нажмите **Connect**.

Приложение сохраняет последний выбранный порт и автоматически выбирает его при следующем запуске, если он доступен.

## Как подключить Arduino

Типовая схема:

```text
HC-12 RX  -> Arduino TX передатчика
HC-12 TX  -> Arduino RX приемника
HC-12 VCC -> 5V или 3.3V согласно вашему модулю
HC-12 GND -> GND
Arduino приемник -> USB -> Windows PC
```

Важно:

- Скорость COM-порта в приложении по умолчанию `9600` baud.
- Убедитесь, что прошивка Arduino-приемника отправляет в USB Serial те же 12 байт структуры или CSV-строку.
- Для бинарного режима обе платы должны использовать одинаковый порядок полей и тип `float` 4 байта, как на Arduino AVR/ESP32.

## Экспорт маршрута

- **Export CSV** сохраняет таблицу с timestamp, latitude, longitude, altitude и расширенными полями.
- **Export GPX** сохраняет трек для GIS, навигационных программ и картографических сервисов.

## Назначение файлов

- `main.py` — главное окно, компоновка UI, подключение сигналов, обработка телеметрии, экспорт и предупреждение о потере GPS.
- `serial_handler.py` — поток чтения COM-порта, автопоиск портов, сохранение последнего порта, декодирование binary/CSV телеметрии, файловый логгер.
- `map_widget.py` — Folium/Leaflet карта, спутниковый слой, маркер дрона, маршрут, экспорт CSV/GPX.
- `dashboard.py` — отрисовка высотомера, компаса, индикатора качества связи и счетчика пакетов.
- `widgets/status_widgets.py` — анимированный светящийся LED и карточки метрик.
- `ui/theme.py` — единая темная тема Qt с градиентами, стеклянными панелями и стилизацией элементов.
- `assets/drone.svg` — SVG-иконка дрона для дальнейшего использования в интерфейсе.
- `requirements.txt` — зависимости Python.

## Назначение основных функций и классов

### `serial_handler.py`

- `TelemetryPacket` — объект одной телеметрической точки. Хранит координаты, высоту, скорость, направление, батарею, RSSI и время приема.
- `TelemetryPacket.is_valid_gps()` — проверяет диапазоны широты и долготы.
- `SerialWorker.available_ports()` — возвращает список доступных COM-портов.
- `SerialWorker.save_last_port()` — сохраняет последний порт в системные настройки Qt.
- `SerialWorker.load_last_port()` — загружает сохраненный порт.
- `SerialWorker.run()` — открывает COM-порт и читает данные в отдельном потоке.
- `SerialWorker.stop()` — безопасно останавливает поток и закрывает порт.
- `SerialWorker._consume()` — разделяет входящий поток на бинарные кадры или текстовые строки.
- `SerialWorker._parse_binary_frame()` — декодирует 12 байт структуры `float,float,float`.
- `SerialWorker._parse_text_line()` — декодирует CSV-строки расширенной телеметрии.
- `configure_file_logger()` — создает лог-файл `logs/ground_station.log`.

### `map_widget.py`

- `MapWidget._create_initial_map()` — генерирует HTML-карту Folium с OpenStreetMap и спутниковым слоем.
- `MapWidget.update_position()` — добавляет точку маршрута и обновляет маркер через JavaScript.
- `MapWidget.clear_route()` — очищает маршрут и пересоздает карту.
- `MapWidget.export_csv()` — сохраняет маршрут в CSV.
- `MapWidget.export_gpx()` — сохраняет маршрут в GPX.

### `dashboard.py`

- `Gauge` — универсальный круговой прибор.
- `Gauge.paintEvent()` — рисует шкалу, градиентную дугу и значение.
- `Compass` — наследник `Gauge`, дополнительно рисует стрелку направления.
- `Dashboard.update_values()` — обновляет высоту, направление, качество связи и количество пакетов.

### `widgets/status_widgets.py`

- `GlowIndicator` — светящийся анимированный индикатор связи/GPS.
- `GlowIndicator.set_connected()` — переключает цвет между зеленым и красным.
- `MetricCard` — стеклянная карточка для одного параметра телеметрии.
- `MetricCard.set_value()` — обновляет отображаемое значение.

### `main.py`

- `GroundStationWindow._build_ui()` — создает левую панель, карту, правую панель, кнопки и приборы.
- `GroundStationWindow._refresh_ports()` — обновляет список COM-портов.
- `GroundStationWindow._connect_serial()` — запускает поток чтения выбранного COM-порта.
- `GroundStationWindow._disconnect_serial()` — останавливает поток и закрывает порт.
- `GroundStationWindow._on_packet()` — обновляет интерфейс, карту, приборы и лог при новом GPS пакете.
- `GroundStationWindow._check_gps_timeout()` — показывает красное предупреждение, если пакеты не приходят дольше 5 секунд.
- `GroundStationWindow._export_csv()` — выбирает путь и экспортирует CSV.
- `GroundStationWindow._export_gpx()` — выбирает путь и экспортирует GPX.
- `GroundStationWindow._log()` — пишет сообщение в UI-лог и файл.
- `GroundStationWindow._error()` — показывает критическую ошибку и записывает ее в лог.
- `main()` — запускает QApplication и главное окно.
