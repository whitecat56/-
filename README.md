# Drone Command Center — GPS + LoRa мониторинг

Красивый наземный пункт управления для связки **Arduino/Nano + u-blox NEO-6M GPS + EBYTE E22-230T30D LoRa 1W**. Программа принимает телеметрию по USB/Serial от Arduino-приёмника, показывает координаты, карту, высоту, скорость, курс, спутники, качество GPS, графики и сохраняет миссию в файлы.

## Что входит в проект

| Файл | Для чего нужен |
| --- | --- |
| `drone_command_center.py` | Главное desktop-приложение на PyQt6: карта, HUD, компас, радар, графики, запись миссий. |
| `arduino/gps_lora_transmitter/gps_lora_transmitter.ino` | Код Arduino на борту: читает NEO-6M и отправляет данные через EBYTE E22. |
| `arduino/lora_usb_receiver/lora_usb_receiver.ino` | Код Arduino у компьютера: принимает LoRa-пакеты и печатает их в USB Serial для программы. |
| `requirements.txt` | Python-зависимости. |

## Формат пакета

Передатчик отправляет одну CSV-строку в секунду после GPS fix:

```text
latitude,longitude,altitude,speed,heading,satellites
```

Пример:

```text
41.311081,69.240562,450.3,35.5,180.0,12
```

Программа также понимает расширенный профессиональный формат с радиоканалом, батареей и ориентацией:

```text
latitude,longitude,altitude,speed,heading,satellites,rssi,snr,voltage,current,mah,pitch,roll
```

Старый формат из 6 полей полностью совместим и продолжит работать.

## Подключение железа

### Бортовой Arduino — GPS + LoRa передатчик

> Важно: E22-230T30D 1W нельзя нормально питать от слабого 3.3V пина Arduino. Используй отдельный стабильный источник 3.3V с запасом по току, общий GND обязателен.

| Модуль | Пин модуля | Arduino Nano |
| --- | --- | --- |
| NEO-6M GPS | TX | D4 |
| NEO-6M GPS | RX | D3, можно не подключать |
| NEO-6M GPS | VCC | 5V или 3.3V по твоей плате GPS |
| NEO-6M GPS | GND | GND |
| E22-230T30D | TXD | D10 |
| E22-230T30D | RXD | D11 |
| E22-230T30D | VCC | внешний 3.3V |
| E22-230T30D | GND | общий GND |

Залей скетч: `arduino/gps_lora_transmitter/gps_lora_transmitter.ino`.

### Наземный Arduino — LoRa USB приёмник

| Модуль | Пин модуля | Arduino Nano |
| --- | --- | --- |
| E22-230T30D | TXD | D10 |
| E22-230T30D | RXD | D11 |
| E22-230T30D | VCC | внешний 3.3V |
| E22-230T30D | GND | общий GND |
| Arduino Nano | USB | Компьютер |

Залей скетч: `arduino/lora_usb_receiver/lora_usb_receiver.ino`.

## Установка программы на компьютере

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

На Linux для `PyQt6-WebEngine` иногда нужны системные OpenGL/WebEngine-библиотеки из твоего дистрибутива.

## Запуск

```bash
python drone_command_center.py
```

1. Нажми **SETTINGS**.
2. Выбери Serial port наземного Arduino-приёмника, например `COM5`, `/dev/ttyUSB0` или `/dev/ttyACM0`.
3. Baud оставь `9600`.
4. Нажми **SAVE SETTINGS**.
5. Нажми **CONNECT LORA**.
6. Когда NEO-6M поймает fix, на экране появятся координаты, карта, спутники, скорость, высота и курс.

Если железо ещё не подключено, нажми **DEMO GPS** — программа начнёт показывать красивую симуляцию движения, чтобы проверить интерфейс.

## Возможности интерфейса

- карта с маркером дрона, направлением носа и треком;
- режим **FOLLOW DRONE**;
- **SET HOME**, расстояние до дома и стрелка Return-To-Home;
- крупные карточки высоты, скорости, курса и спутников;
- отдельный блок точных координат и ссылка Google Maps;
- авиационный компас, artificial horizon по pitch/roll и радар HOME/DRONE;
- DJI-style signal bars, реальный RSSI/SNR при расширенном пакете E22;
- батарея: voltage, current, mAh consumed и LOW BATTERY warning;
- mission planner: кликом по карте добавляй waypoint, сохраняй и загружай mission JSON;
- offline map cache через persistent WebEngine cache;
- full screen tactical map mode;
- distance limit warning и Return-To-Home recommendation system;
- emergency LOST SIGNAL banner;
- графики высоты и скорости;
- запись миссий автоматически после GPS FIX в `missions/mission_YYYYMMDD_HHMMSS/` как CSV, JSON, GPX и KML для Google Earth;
- replay сохранённых миссий.

## Объяснение Arduino-кода коротко

### Передатчик

1. `TinyGPS++` разбирает NMEA-данные от NEO-6M.
2. `SoftwareSerial gpsSerial(4, 3)` читает GPS с пина D4.
3. `SoftwareSerial loraSerial(10, 11)` общается с E22.
4. Пока нет `gps.location.isValid()`, код пишет `Waiting GPS fix...`.
5. После fix собирается строка `lat,lon,alt,speed,course,sats`.
6. Если добавишь датчики батареи/IMU на Arduino, отправляй расширенную строку `lat,lon,alt,speed,course,sats,rssi,snr,voltage,current,mah,pitch,roll`.
7. `e22.sendMessage(message)` отправляет строку по LoRa.

### Приёмник

1. Arduino у компьютера слушает E22 через D10/D11.
2. Когда приходит пакет, `e22.receiveMessage()` получает строку.
3. Чистая CSV-строка печатается в USB Serial.
4. Python-программа читает эту строку и обновляет экран.

## Частые проблемы

- **Нет GPS fix**: вынеси GPS-антенну к окну/на улицу и подожди 1–5 минут после холодного старта.
- **LoRa не ловит**: проверь одинаковые настройки E22-модулей, общий baud `9600`, питание 3.3V и антенны.
- **Программа не видит порт**: закрой Arduino IDE Serial Monitor, выбери порт в Settings и подключись заново.
- **Странные координаты**: проверь, что в Serial летит именно CSV-строка из 6 чисел.
