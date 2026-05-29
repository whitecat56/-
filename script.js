const RELATIONSHIP_START_DATE = "2025-10-29T00:00:00";

const introFrames = [
    "Для самой прекрасной девушки ❤️",
    "У меня есть история...",
    "Наша история..."
];

const mediaConfig = {
    images: [
        "images/love-1.svg", "images/love-2.svg", "images/love-3.svg", "images/love-4.svg",
        "images/photo-1.jpg", "images/photo-2.jpg", "images/photo-3.jpg", "images/photo-4.jpg",
        "images/photo-5.jpg", "images/photo-6.jpg", "images/photo-7.jpg", "images/photo-8.jpg",
        "images/memory-1.jpg", "images/memory-2.jpg", "images/together-1.jpg", "images/together-2.jpg"
    ],
    videos: [
        "videos/video-1.mp4", "videos/video-2.mp4", "videos/video-3.mp4", "videos/video-4.mp4",
        "videos/circle-1.mp4", "videos/circle-2.mp4", "videos/memory-1.mp4", "videos/memory-2.mp4"
    ]
};

const messageMoments = [
    "Доброе утро, Парижон ☀️",
    "Ты сегодня улыбалась?",
    "Я жду 19:35...",
    "Напиши, когда будешь свободна ❤️",
    "С тобой день становится лучше"
];

const futureLetter = "Парижон, если ты читаешь это через 7 лет, знай: я всё ещё помню, как начиналась наша история. Я всё ещё благодарен за твой голос, улыбку, заботу и за то, что однажды ты стала моим самым любимым человеком. Я надеюсь, что мы улыбаемся этому письму вместе — уже с ещё большим количеством воспоминаний, мечт и любви. Я выбирал тебя тогда, выбираю сейчас и буду выбирать дальше. ❤️";

const reasons = [
    "За твою улыбку, которая делает день светлее.",
    "За твои глаза, в которых хочется теряться.",
    "За твою доброту к людям.",
    "За то, как ты умеешь заботиться.",
    "За твой нежный голос.",
    "За твою искренность.",
    "За то, что рядом с тобой спокойно.",
    "За твоё чувство юмора.",
    "За то, как ты поддерживаешь.",
    "За твою красоту без усилий.",
    "За то, что ты умеешь слушать.",
    "За твоё терпение.",
    "За твою сильную сторону.",
    "За твою мягкость.",
    "За то, что ты делаешь обычные дни особенными.",
    "За твои сообщения, которых я жду.",
    "За то, как ты улыбаешься глазами.",
    "За твоё тепло.",
    "За твою верность.",
    "За то, что с тобой хочется становиться лучше.",
    "За наши разговоры.",
    "За твою заботу в мелочах.",
    "За твою честность.",
    "За твою женственность.",
    "За твоё сердце.",
    "За то, что ты умеешь радоваться простому.",
    "За твой характер.",
    "За твою нежность.",
    "За то, что ты стала моей привычкой.",
    "За то, что я скучаю по тебе даже после разговора.",
    "За твою поддержку в трудные дни.",
    "За твою красоту утром, днём и вечером.",
    "За твоё имя, которое звучит как музыка.",
    "За то, как ты меня вдохновляешь.",
    "За наши маленькие секреты.",
    "За то, что ты настоящая.",
    "За твою заботливую душу.",
    "За то, что с тобой я чувствую себя нужным.",
    "За твой смех.",
    "За то, что ты умеешь быть милой.",
    "За твою ревность, в которой тоже есть любовь.",
    "За то, что ты особенная.",
    "За твою скромность.",
    "За твою энергию.",
    "За твою мечтательность.",
    "За то, что ты веришь в нас.",
    "За наши прогулки.",
    "За воспоминания, которые мы уже создали.",
    "За те воспоминания, которые ещё будут.",
    "За то, что рядом с тобой хочется улыбаться.",
    "За твою заботу о моём настроении.",
    "За твою красоту в деталях.",
    "За то, как ты говоришь моё имя.",
    "За то, что ты стала моим домом.",
    "За твоё доверие.",
    "За то, что ты умеешь быть сильной.",
    "За то, что ты умеешь быть нежной.",
    "За твою любовь.",
    "За то, как ты меня понимаешь.",
    "За твои милые привычки.",
    "За то, что ты не похожа ни на кого.",
    "За твою заботу словами.",
    "За твою заботу поступками.",
    "За то, что ты умеешь ждать.",
    "За то, что я жду тебя.",
    "За 19:35.",
    "За Ташкент в нашей истории.",
    "За встречи в авиации.",
    "За момент с рукой.",
    "За первые намёки.",
    "За признание.",
    "За каждый день этих 7 месяцев.",
    "За то, что ты стала самым важным человеком.",
    "За твою улыбку в сообщениях.",
    "За твою заботу, даже когда далеко.",
    "За то, что ты умеешь делать меня счастливым.",
    "За твоё спокойствие.",
    "За твою искру.",
    "За твою красоту внутри.",
    "За твою красоту снаружи.",
    "За то, что ты моя любимая.",
    "За то, что я могу думать о будущем с тобой.",
    "За мечты, которые связаны с тобой.",
    "За твою нежную душу.",
    "За то, как ты волнуешься.",
    "За то, как ты радуешься.",
    "За твою заботу о нас.",
    "За то, что ты рядом сердцем.",
    "За каждую минуту с тобой.",
    "За каждую секунду ожидания.",
    "За то, что любовь с тобой настоящая.",
    "За то, что ты стала моей историей.",
    "За то, что ты делаешь меня мягче.",
    "За то, что ты делаешь меня смелее.",
    "За твою веру в хорошее.",
    "За твоё внимание.",
    "За твой свет.",
    "За то, что ты — Парижон.",
    "За то, что я могу сказать: я люблю тебя.",
    "За то, что это только начало."
];

const $ = (selector, scope = document) => scope.querySelector(selector);
const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];

let ambientSynth;
let isAudioPlaying = false;
let bookSwiper;

window.addEventListener("DOMContentLoaded", () => {
    document.body.classList.add("is-locked");
    initIntro();
    initLibraries();
    initRelationshipCounter();
    initMessageStream();
    initStarfield();
    initFallingEffects();
    initMediaGallery();
    initReasonGenerator();
    initFutureCapsule();
    initAudio();
    initEasterEggs();
    initSceneAnimations();
    initVideoPlayback();
    initFinale();
    initConfession();
});

function initIntro() {
    const intro = $("#cinemaIntro");
    const copy = $("#introCopy");
    const skip = $("#introSkip");
    let frameIndex = 0;

    const nextFrame = () => {
        frameIndex += 1;
        if (frameIndex >= introFrames.length) return;
        animateTextSwap(copy, introFrames[frameIndex]);
    };

    const timer = setInterval(nextFrame, 1800);

    skip.addEventListener("click", () => {
        clearInterval(timer);
        startAudio();
        intro.classList.add("is-hidden");
        document.body.classList.remove("is-locked");
        setTimeout(() => intro.remove(), 1300);
    });
}

function animateTextSwap(element, text) {
    if (window.gsap) {
        gsap.to(element, { opacity: 0, y: 16, duration: 0.45, onComplete: () => {
            element.textContent = text;
            gsap.fromTo(element, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.7 });
        }});
    } else {
        element.textContent = text;
    }
}

function initLibraries() {
    if (window.AOS) {
        AOS.init({ duration: 900, easing: "ease-out-cubic", once: false, mirror: true });
    }

    if (window.Lenis) {
        const lenis = new Lenis({ lerp: 0.08, smoothWheel: true, syncTouch: true });
        const raf = (time) => {
            lenis.raf(time);
            requestAnimationFrame(raf);
        };
        requestAnimationFrame(raf);
    }

    if (window.Swiper) {
        bookSwiper = new Swiper(".book-swiper", {
            effect: "cards",
            grabCursor: true,
            pagination: { el: ".book-swiper .swiper-pagination", clickable: true }
        });
    }
}

function initSceneAnimations() {
    if (!window.gsap || !window.ScrollTrigger) return;

    gsap.registerPlugin(ScrollTrigger);
    gsap.utils.toArray(".story-scene").forEach((scene) => {
        gsap.fromTo(scene.querySelector(".scene-card, .section-heading, .final-photo"),
            { scale: 0.94, opacity: 0.72 },
            { scale: 1, opacity: 1, duration: 1, ease: "power2.out", scrollTrigger: { trigger: scene, start: "top 70%", end: "center center", scrub: 0.8 } }
        );
    });

    gsap.utils.toArray(".scene-card").forEach((card) => {
        gsap.to(card, { yPercent: -4, scrollTrigger: { trigger: card, start: "top bottom", end: "bottom top", scrub: true } });
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
        units.days.textContent = Math.floor(totalSeconds / 86400);
        units.hours.textContent = String(Math.floor((totalSeconds % 86400) / 3600)).padStart(2, "0");
        units.minutes.textContent = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, "0");
        units.seconds.textContent = String(totalSeconds % 60).padStart(2, "0");
    };

    update();
    setInterval(update, 1000);
}

function initMessageStream() {
    const stream = $("#messageStream");
    messageMoments.forEach((message, index) => {
        const bubble = document.createElement("span");
        bubble.textContent = message;
        bubble.style.animationDelay = `${index * 0.18}s`;
        stream.appendChild(bubble);
    });
}

function initStarfield() {
    const canvas = $("#starsCanvas");
    const context = canvas.getContext("2d");
    let stars = [];

    const resize = () => {
        const ratio = window.devicePixelRatio || 1;
        canvas.width = window.innerWidth * ratio;
        canvas.height = window.innerHeight * ratio;
        stars = Array.from({ length: Math.min(220, Math.floor(window.innerWidth / 3.2)) }, () => ({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            radius: Math.random() * 1.7 + 0.35,
            phase: Math.random() * Math.PI * 2,
            speed: Math.random() * 0.018 + 0.006
        }));
    };

    const draw = () => {
        context.clearRect(0, 0, canvas.width, canvas.height);
        stars.forEach((star) => {
            star.phase += star.speed;
            const glow = 0.25 + Math.abs(Math.sin(star.phase)) * 0.75;
            context.beginPath();
            context.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
            context.fillStyle = `rgba(255, 247, 252, ${glow})`;
            context.shadowBlur = glow * 14;
            context.shadowColor = "rgba(255, 209, 102, 0.65)";
            context.fill();
        });
        requestAnimationFrame(draw);
    };

    resize();
    draw();
    window.addEventListener("resize", resize);
}

function initFallingEffects() {
    createFallingLoop("#heartLayer", ["❤️", "♡", "💕"], 820, 16, 30);
    createFallingLoop("#petalLayer", ["🌹", "❦"], 1450, 18, 34);
    createFallingLoop("#sparkLayer", ["✦", "✧", "✨"], 540, 10, 20);
    createButterflies();
}

function createFallingLoop(selector, items, interval, minSize, maxSize) {
    const layer = $(selector);
    const create = () => {
        const item = document.createElement("span");
        item.className = "fall-item";
        item.textContent = items[Math.floor(Math.random() * items.length)];
        item.style.left = `${Math.random() * 100}vw`;
        item.style.fontSize = `${minSize + Math.random() * (maxSize - minSize)}px`;
        item.style.setProperty("--drift", `${-60 + Math.random() * 120}px`);
        item.style.setProperty("--rotate", `${180 + Math.random() * 380}deg`);
        item.style.animationDuration = `${7 + Math.random() * 8}s`;
        layer.appendChild(item);
        setTimeout(() => item.remove(), 16000);
    };

    Array.from({ length: 10 }, create);
    setInterval(create, interval);
}

function createButterflies() {
    const layer = $("#butterflies");
    const create = () => {
        const butterfly = document.createElement("span");
        butterfly.className = "butterfly";
        butterfly.textContent = "🦋";
        butterfly.style.left = `${Math.random() * 90}vw`;
        butterfly.style.fontSize = `${18 + Math.random() * 18}px`;
        butterfly.style.setProperty("--drift", `${-90 + Math.random() * 180}px`);
        butterfly.style.animationDuration = `${11 + Math.random() * 6}s`;
        layer.appendChild(butterfly);
        setTimeout(() => butterfly.remove(), 18000);
    };

    Array.from({ length: 4 }, create);
    setInterval(create, 3600);
}

function initMediaGallery() {
    const wrapper = $("#mediaGallery");
    const addImage = (src, index) => {
        const slide = document.createElement("div");
        slide.className = "swiper-slide";
        slide.innerHTML = `<figure class="media-card"><img src="${src}" alt="Воспоминание ${index + 1}" loading="lazy"><figcaption class="media-caption">Воспоминание ${index + 1}</figcaption></figure>`;
        const image = $("img", slide);
        image.addEventListener("error", () => slide.remove());
        wrapper.appendChild(slide);
    };

    const addVideo = (src, index) => {
        const slide = document.createElement("div");
        slide.className = "swiper-slide";
        slide.innerHTML = `<figure class="media-card"><video src="${src}" muted loop playsinline preload="metadata"></video><figcaption class="media-caption">Видео-воспоминание ${index + 1}</figcaption></figure>`;
        const video = $("video", slide);
        video.addEventListener("error", () => slide.remove());
        wrapper.appendChild(slide);
    };

    mediaConfig.images.forEach(addImage);
    mediaConfig.videos.forEach(addVideo);

    window.setTimeout(() => {
        if (!window.Swiper) return;
        new Swiper(".media-swiper", {
            slidesPerView: 1.08,
            centeredSlides: true,
            spaceBetween: 16,
            grabCursor: true,
            pagination: { el: ".media-swiper .swiper-pagination", clickable: true },
            breakpoints: { 760: { slidesPerView: 1.35, spaceBetween: 24 } }
        });
        initVideoPlayback();
    }, 500);
}

function initVideoPlayback() {
    const videos = $$('video');
    if (!videos.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            const video = entry.target;
            if (entry.isIntersecting) {
                video.play().catch(() => undefined);
            } else {
                video.pause();
            }
        });
    }, { threshold: 0.55 });

    videos.forEach((video) => observer.observe(video));
}

function initReasonGenerator() {
    const display = $("#reasonDisplay");
    const count = $("#reasonCount");
    let current = 0;
    const shuffled = [...reasons].sort(() => Math.random() - 0.5);

    $("#reasonBtn").addEventListener("click", () => {
        display.classList.remove("is-changing");
        void display.offsetWidth;
        display.classList.add("is-changing");
        display.textContent = shuffled[current % shuffled.length];
        current += 1;
        count.textContent = `${Math.min(current, shuffled.length)} / ${shuffled.length}`;
        createHeartRain(12);
    });
}

function initFutureCapsule() {
    const button = $("#futureBtn");
    const letter = $("#futureLetter");
    let opened = false;

    button.addEventListener("click", () => {
        if (opened) return;
        opened = true;
        button.textContent = "Письмо открыто";
        typeText(letter, futureLetter, 24);
    });
}

function typeText(element, text, speed) {
    element.textContent = "";
    let index = 0;
    const timer = setInterval(() => {
        element.textContent += text[index];
        index += 1;
        if (index >= text.length) clearInterval(timer);
    }, speed);
}

function initAudio() {
    const toggle = $("#audioToggle");
    toggle.addEventListener("click", () => {
        if (isAudioPlaying) stopAudio();
        else startAudio();
    });
}

async function startAudio() {
    const audio = $("#pianoAudio");
    const toggle = $("#audioToggle");
    const label = $("#audioLabel");
    audio.volume = 0.42;

    try {
        await audio.play();
    } catch {
        ambientSynth = ambientSynth || createAmbientPiano();
        await ambientSynth?.context.resume();
        ambientSynth?.gain.gain.setTargetAtTime(0.34, ambientSynth.context.currentTime, 0.8);
    }

    isAudioPlaying = true;
    toggle.classList.add("is-playing");
    label.textContent = "Играет";
}

function stopAudio() {
    const audio = $("#pianoAudio");
    const toggle = $("#audioToggle");
    const label = $("#audioLabel");
    audio.pause();
    ambientSynth?.gain.gain.setTargetAtTime(0, ambientSynth.context.currentTime, 0.5);
    isAudioPlaying = false;
    toggle.classList.remove("is-playing");
    label.textContent = "Музыка";
}

function createAmbientPiano() {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return null;

    const context = new AudioContext();
    const gain = context.createGain();
    const delay = context.createDelay();
    const feedback = context.createGain();
    const frequencies = [261.63, 329.63, 392, 523.25];

    gain.gain.value = 0;
    delay.delayTime.value = 0.42;
    feedback.gain.value = 0.24;
    delay.connect(feedback).connect(delay);
    delay.connect(gain).connect(context.destination);

    frequencies.forEach((frequency, index) => {
        const oscillator = context.createOscillator();
        const voice = context.createGain();
        oscillator.type = index % 2 ? "triangle" : "sine";
        oscillator.frequency.value = frequency / 2;
        voice.gain.value = 0.032;
        oscillator.connect(voice).connect(delay);
        oscillator.start(index * 0.08);
    });

    return { context, gain };
}

function initEasterEggs() {
    const secretHeart = $("#secretHeart");
    let taps = 0;
    let typed = "";

    secretHeart.addEventListener("click", () => {
        taps += 1;
        createHeartRain(8);
        if (taps >= 5) {
            taps = 0;
            showModal("Ты лучшее, что случилось в моей жизни ❤️");
        }
    });

    document.addEventListener("keydown", (event) => {
        typed = `${typed}${event.key.toUpperCase()}`.slice(-4);
        if (typed === "LOVE") unlockHiddenChapter();
    });
}

function unlockHiddenChapter() {
    const chapter = $("#hiddenChapter");
    chapter.classList.add("is-unlocked");
    showModal("Скрытая глава открыта: LOVE ❤️");
    if (bookSwiper) {
        bookSwiper.update();
        bookSwiper.slideTo(7, 700);
    }
}

function showModal(text) {
    const modal = $("#modalMessage");
    const message = $("#modalMessageText");
    message.textContent = text;
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
    createHeartRain(50);
    setTimeout(() => {
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
    }, 3200);
}

function createHeartRain(count) {
    for (let index = 0; index < count; index += 1) {
        const heart = document.createElement("span");
        heart.className = "fall-item";
        heart.textContent = ["❤️", "💖", "💕", "🌹"][Math.floor(Math.random() * 4)];
        heart.style.left = `${Math.random() * 100}vw`;
        heart.style.fontSize = `${18 + Math.random() * 24}px`;
        heart.style.setProperty("--drift", `${-90 + Math.random() * 180}px`);
        heart.style.setProperty("--rotate", `${240 + Math.random() * 360}deg`);
        heart.style.animationDuration = `${3 + Math.random() * 3}s`;
        document.body.appendChild(heart);
        setTimeout(() => heart.remove(), 6500);
    }
}

function initConfession() {
    $("#confessionBtn").addEventListener("click", () => {
        $("#confessionText").classList.add("is-open");
        createHeartRain(35);
    });
}

function initFinale() {
    const finale = $("#finale");
    const lines = $$(".final-lines p");
    let played = false;

    const observer = new IntersectionObserver((entries) => {
        if (!entries[0].isIntersecting || played) return;
        played = true;
        lines.forEach((line, index) => {
            setTimeout(() => line.classList.add("is-visible"), index * 1700);
        });
        setTimeout(() => createHeartRain(160), lines.length * 1700);
    }, { threshold: 0.62 });

    observer.observe(finale);
}
