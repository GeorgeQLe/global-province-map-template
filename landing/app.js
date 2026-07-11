(() => {
  const root = document.getElementById("tessellation");
  const buttons = Array.from(document.querySelectorAll(".era-btn"));
  const caption = document.getElementById("era-caption");
  const tier = document.getElementById("era-tier");

  if (!root || !buttons.length) return;

  const copy = {
    "1444": {
      caption: "EU-leaning 1444 politics over modern admin geometry",
      tier: "quality: curated-politics",
    },
    "1836": {
      caption: "Victoria-leaning 1836 major powers and elevated theaters",
      tier: "quality: curated-politics",
    },
    modern: {
      caption: "Modern baseline owners projected from parent countries",
      tier: "quality: scaffold-baseline",
    },
  };

  function setEra(era) {
    const next = copy[era] ? era : "1444";
    root.dataset.era = next;
    buttons.forEach((btn) => {
      const active = btn.dataset.era === next;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });
    if (caption) caption.textContent = copy[next].caption;
    if (tier) tier.textContent = copy[next].tier;
  }

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => setEra(btn.dataset.era));
  });

  setEra(root.dataset.era || "1444");
})();
