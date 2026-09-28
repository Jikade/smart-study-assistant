let birdsEffect = null;

export function initVantaBirds() {
  const target = document.getElementById("vanta-birds-bg");

  if (!target || birdsEffect) {
    return Boolean(birdsEffect);
  }

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return false;
  }

  if (!window.THREE || !window.VANTA?.BIRDS) {
    return false;
  }

  const mobile = window.matchMedia("(max-width: 768px)").matches;

  try {
    birdsEffect = window.VANTA.BIRDS({
      el: target,

      mouseControls: true,
      touchControls: true,
      gyroControls: false,

      minHeight: 200,
      minWidth: 200,

      scale: 1,
      scaleMobile: 1,

      // Không thay đổi màu nền hiện tại.
      backgroundColor: 0xf5f0e8,
      backgroundAlpha: 0,

      // Màu chim hợp palette hiện tại.
      color1: 0x6755b9,
      color2: 0xff9db4,
      colorMode: "variance",

      birdSize: mobile ? 0.85 : 1.05,
      wingSpan: mobile ? 18 : 24,
      speedLimit: mobile ? 2.8 : 3.5,

      separation: 28,
      alignment: 18,
      cohesion: 18,

      quantity: mobile ? 2 : 3,
    });

    document.documentElement.classList.add("vanta-birds-ready");

    return true;
  } catch (error) {
    console.warn("[VANTA] Birds effect unavailable:", error);

    return false;
  }
}

export function destroyVantaBirds() {
  if (!birdsEffect) return;

  birdsEffect.destroy();
  birdsEffect = null;
}
