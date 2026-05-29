const RELATIONSHIP_START_DATE = "2025-10-29T00:00:00";

const quotes = [
    "Ты — мой самый красивый случай.",
    "С тобой даже тишина звучит как любовь.",
    "Если счастье имеет имя, для меня оно похоже на твоё.",
    "Моё любимое место — рядом с тобой.",
    "7 месяцев — и каждый день я выбираю тебя снова."
];

const noteMessages = [
    "Ты делаешь мой мир мягче.",
    "Я улыбаюсь, когда думаю о тебе.",
    "В тебе есть магия, которую невозможно объяснить.",
    "Спасибо за тепло, которое ты даришь.",
    "Ты — мой дом, даже когда мы далеко.",
    "С тобой хочется строить будущее."
];

const $ = (selector, scope = document) => scope.querySelector(selector);
const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];

window.addEventListener("load", () => {
    setTimeout(() => $(".preloader")?.classList.add("is-hidden"), 900);
});

document.addEventListener("DOMContentLoaded", () => {
    initRevealAnimations();
    initRelationshipCounter();
    initAmbientHearts();
    initParticles();
    initStarfield();
    initCursor();
    initGalleryModal();
    initMusicPlayer();
    initLoveExplosion();
    initMemoryBook();
    initLoveNotes();
    initRomanticQuotes();
    initSecretEasterEggs();
});

function initRevealAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("is-visible");
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.16 });

    $$(".reveal").forEach((element, index) => {
        element.style.transitionDelay = `${Math.min(index * 45, 260)}ms`;
        observer.observe(element);
    });
}

function initRelationshipCounter() {
    const startDate = new Date(RELATIONSHIP_START_DATE);
    const units = {
        days: $('[data-unit="days"]'),
        hours: $('[data-unit="hours"]'),
        minutes: $('[data-unit="minutes"]'),
        seconds: $('[data-unit="seconds"]')
    };

    const update = () => {
        const diff = Math.max(Date.now() - startDate.getTime(), 0);
        const totalSeconds = Math.floor(diff / 1000);
        const days = Math.floor(totalSeconds / 86400);
        const hours = Math.floor((totalSeconds % 86400) / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;

        units.days.textContent = days;
        units.hours.textContent = String(hours).padStart(2, "0");
        units.minutes.textContent = String(minutes).padStart(2, "0");
        units.seconds.textContent = String(seconds).padStart(2, "0");
    };

    update();
    setInterval(update, 1000);
}

function initAmbientHearts() {
    const container = $("#floatingHearts");
    const createHeart = () => {
        const heart = document.createElement("span");
        heart.className = "heart";
        heart.textContent = Math.random() > 0.5 ? "❤️" : "♡";
        heart.style.left = `${Math.random() * 100}vw`;
        heart.style.fontSize = `${14 + Math.random() * 26}px`;
        heart.style.animationDuration = `${8 + Math.random() * 8}s`;
        heart.style.setProperty("--x-drift", `${-60 + Math.random() * 120}px`);
        container.appendChild(heart);
        setTimeout(() => heart.remove(), 17000);
    };

    Array.from({ length: 18 }, createHeart);
    setInterval(createHeart, 620);
}

function initParticles() {
    const container = $("#particles");
    const createParticle = () => {
        const particle = document.createElement("span");
        particle.className = "particle";
        particle.style.left = `${Math.random() * 100}vw`;
        particle.style.animationDuration = `${5 + Math.random() * 8}s`;
        particle.style.setProperty("--x-drift", `${-30 + Math.random() * 60}px`);
        container.appendChild(particle);
        setTimeout(() => particle.remove(), 13000);
    };

    Array.from({ length: 35 }, createParticle);
    setInterval(createParticle, 260);
}

function initStarfield() {
    const canvas = $("#starsCanvas");
    const context = canvas.getContext("2d");
    let stars = [];

    const resize = () => {
        canvas.width = window.innerWidth * window.devicePixelRatio;
        canvas.height = window.innerHeight * window.devicePixelRatio;
        stars = Array.from({ length: Math.min(180, Math.floor(window.innerWidth / 7)) }, () => ({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            radius: Math.random() * 1.8 + 0.4,
            alpha: Math.random(),
            speed: Math.random() * 0.018 + 0.006
        }));
    };

    const draw = () => {
        context.clearRect(0, 0, canvas.width, canvas.height);
        stars.forEach((star) => {
            star.alpha += star.speed;
            const glow = 0.35 + Math.abs(Math.sin(star.alpha)) * 0.65;
            context.beginPath();
            context.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
            context.fillStyle = `rgba(255, 245, 252, ${glow})`;
            context.fill();
        });
        requestAnimationFrame(draw);
    };

    resize();
    draw();
    window.addEventListener("resize", resize);
}

function initCursor() {
    const cursor = $("#cursorHeart");
    window.addEventListener("pointermove", (event) => {
        cursor.style.left = `${event.clientX}px`;
        cursor.style.top = `${event.clientY}px`;
    });
}

function initGalleryModal() {
    const modal = $("#imageModal");
    const modalImage = $("img", modal);
    const close = () => {
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
    };

    $$(".polaroid img").forEach((image) => {
        image.addEventListener("click", () => {
            modalImage.src = image.src;
            modalImage.alt = image.alt;
            modal.classList.add("is-open");
            modal.setAttribute("aria-hidden", "false");
        });
    });

    $(".modal__close", modal).addEventListener("click", close);
    modal.addEventListener("click", (event) => {
        if (event.target === modal) close();
    });
    window.addEventListener("keydown", (event) => {
        if (event.key === "Escape") close();
    });
}

function initMusicPlayer() {
    const audio = $("#romanticAudio");
    const toggle = $("#musicToggle");
    const label = $("#musicToggleText");
    let isPlaying = false;
    let ambientSynth = null;

    const createAmbientSynth = () => {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return null;

        const context = new AudioContext();
        const gain = context.createGain();
        const delay = context.createDelay();
        const feedback = context.createGain();
        const notes = [261.63, 329.63, 392.0, 493.88];
        const oscillators = notes.map((frequency, index) => {
            const oscillator = context.createOscillator();
            const voiceGain = context.createGain();
            oscillator.type = index % 2 ? "triangle" : "sine";
            oscillator.frequency.value = frequency / 2;
            voiceGain.gain.value = 0.035;
            oscillator.connect(voiceGain).connect(delay);
            oscillator.start();
            return oscillator;
        });

        delay.delayTime.value = 0.32;
        feedback.gain.value = 0.28;
        gain.gain.value = 0.0;
        delay.connect(feedback).connect(delay);
        delay.connect(gain).connect(context.destination);

        return { context, gain, oscillators };
    };

    const play = async () => {
        audio.volume = 0.42;
        try {
            await audio.play();
        } catch {
            ambientSynth = ambientSynth || createAmbientSynth();
            await ambientSynth?.context.resume();
            ambientSynth?.gain.gain.setTargetAtTime(0.38, ambientSynth.context.currentTime, 0.6);
        }
        isPlaying = true;
        label.textContent = "Музыка играет";
        toggle.classList.add("is-playing");
    };

    const pause = () => {
        audio.pause();
        ambientSynth?.gain.gain.setTargetAtTime(0.0, ambientSynth.context.currentTime, 0.35);
        isPlaying = false;
        label.textContent = "Включить музыку";
        toggle.classList.remove("is-playing");
    };

    toggle.addEventListener("click", () => {
        if (isPlaying) pause();
        else play();
    });

    document.addEventListener("pointerdown", (event) => {
        audio.volume = 0.42;
        if (!isPlaying && event.target !== toggle && !toggle.contains(event.target)) {
            play();
        }
    }, { once: true });
}

function initLoveExplosion() {
    const overlay = $("#loveOverlay");
    const button = $("#loveExplosionBtn");

    button.addEventListener("click", () => {
        overlay.classList.add("is-open");
        overlay.setAttribute("aria-hidden", "false");
        createBurst(120);
        setTimeout(() => {
            overlay.classList.remove("is-open");
            overlay.setAttribute("aria-hidden", "true");
        }, 3600);
    });
}

function createBurst(count = 60) {
    for (let index = 0; index < count; index += 1) {
        const heart = document.createElement("span");
        heart.className = "burst-heart";
        heart.textContent = ["❤️", "💖", "💕", "🌹"][Math.floor(Math.random() * 4)];
        heart.style.setProperty("--tx", `${-50 + Math.random() * 100}vw`);
        heart.style.setProperty("--ty", `${-50 + Math.random() * 100}vh`);
        heart.style.animationDelay = `${Math.random() * 0.35}s`;
        document.body.appendChild(heart);
        setTimeout(() => heart.remove(), 2600);
    }
}

function initMemoryBook() {
    const pages = $$(".book__page");
    let current = 0;
    $("#nextPageBtn").addEventListener("click", () => {
        pages[current].classList.remove("is-active");
        current = (current + 1) % pages.length;
        pages[current].classList.add("is-active");
    });
}

function initLoveNotes() {
    const container = $("#loveNotes");
    noteMessages.forEach((message, index) => {
        const note = document.createElement("article");
        note.className = "note reveal";
        note.textContent = message;
        note.style.left = `${(index % 3) * 32 + Math.random() * 7}%`;
        note.style.top = `${Math.floor(index / 3) * 145 + Math.random() * 38}px`;
        note.style.animationDelay = `${index * 0.3}s`;
        container.appendChild(note);
    });

    initRevealAnimations();
}

function initRomanticQuotes() {
    const quote = $("#randomQuote");
    let index = 0;
    setInterval(() => {
        index = (index + 1) % quotes.length;
        quote.animate([{ opacity: 1 }, { opacity: 0, transform: "translateY(8px)" }], { duration: 260 }).onfinish = () => {
            quote.textContent = quotes[index];
            quote.animate([{ opacity: 0, transform: "translateY(8px)" }, { opacity: 1, transform: "translateY(0)" }], { duration: 420 });
        };
    }, 4200);
}

function initSecretEasterEggs() {
    const secretButton = $("#secretButton");
    let typed = "";

    secretButton.addEventListener("click", () => showSecretMessage());
    document.addEventListener("keydown", (event) => {
        typed = `${typed}${event.key.toLowerCase()}`.slice(-6);
        if (typed.includes("love")) showSecretMessage();
    });
}

function showSecretMessage() {
    const message = document.createElement("div");
    message.className = "love-overlay is-open";
    message.innerHTML = '<div class="love-overlay__message">Ты — лучшее, что случилось со мной ❤️</div>';
    document.body.appendChild(message);
    createBurst(80);
    setTimeout(() => message.remove(), 3200);
}
