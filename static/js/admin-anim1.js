document.addEventListener("DOMContentLoaded", function () {
    const titleText = document.querySelector("#site-name a span");
    if (!titleText) return;

    let glow = 0;
    let increasing = true;

    function animateGlow() {
        if (increasing) {
            glow += 0.15;
            if (glow >= 8) increasing = false;
        } else {
            glow -= 0.15;
            if (glow <= 0) increasing = true;
        }

        titleText.style.textShadow = `0 0 ${glow}px rgba(76, 175, 80, 0.6)`;
        requestAnimationFrame(animateGlow);
    }

    animateGlow();
});
