(function initProfessionPortfolioBubbles() {
  const SIM_SIZE = 1000;
  const ORIGIN_X = SIM_SIZE / 2;
  const ORIGIN_Y = SIM_SIZE / 2;
  const FIT_MARGIN = 36;

  const TOPIC_COLORS = {
    database: { main: "#5eb8d4", light: "#d4f0f7" },
    engineering: { main: "#e8a84a", light: "#f8e7c8" },
    "code-analysis": { main: "#9b7ad6", light: "#e8dff8" },
    apps: { main: "#5cc98a", light: "#d8f5e4" },
    tools: { main: "#f08a62", light: "#fde2d8" },
    default: { main: "#fa842b", light: "#ffe8d4" },
  };

  const SVG_NS = "http://www.w3.org/2000/svg";

  const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;

  const topicPalette = (topic) => TOPIC_COLORS[topic] || TOPIC_COLORS.default;

  const readLabelLineHeight = (arena) => {
    const raw = getComputedStyle(arena)
      .getPropertyValue("--bubbles-label-line-height")
      .trim();
    const parsed = Number.parseFloat(raw);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : 12;
  };

  const appendGradientStop = (gradient, offset, color, opacity) => {
    const stop = document.createElementNS(SVG_NS, "stop");
    stop.setAttribute("offset", offset);
    stop.setAttribute("stop-color", color);
    if (opacity !== undefined) {
      stop.setAttribute("stop-opacity", String(opacity));
    }
    gradient.appendChild(stop);
  };

  const ensureBubbleDefs = (defs) => {
    if (defs.getAttribute("data-bubble-defs-ready")) {
      return;
    }
    defs.setAttribute("data-bubble-defs-ready", "1");

    const reflectionLight = document.createElementNS(SVG_NS, "radialGradient");
    reflectionLight.setAttribute("id", "bubble-reflection-light");
    reflectionLight.setAttribute("fy", "10%");
    appendGradientStop(reflectionLight, "60%", "black", 0);
    appendGradientStop(reflectionLight, "90%", "white", 0.25);
    appendGradientStop(reflectionLight, "100%", "black", 1);
    defs.appendChild(reflectionLight);

    const reflectionMaskBottom = document.createElementNS(SVG_NS, "mask");
    reflectionMaskBottom.setAttribute("id", "bubble-mask-reflection-bottom");
    reflectionMaskBottom.setAttribute("maskContentUnits", "objectBoundingBox");
    const reflectionRectBottom = document.createElementNS(SVG_NS, "rect");
    reflectionRectBottom.setAttribute("width", "1");
    reflectionRectBottom.setAttribute("height", "1");
    reflectionRectBottom.setAttribute("fill", "url(#bubble-reflection-light)");
    reflectionMaskBottom.appendChild(reflectionRectBottom);
    defs.appendChild(reflectionMaskBottom);

    const reflectionMaskTop = document.createElementNS(SVG_NS, "mask");
    reflectionMaskTop.setAttribute("id", "bubble-mask-reflection-top");
    reflectionMaskTop.setAttribute("maskContentUnits", "objectBoundingBox");
    const reflectionRectTop = document.createElementNS(SVG_NS, "rect");
    reflectionRectTop.setAttribute("width", "1");
    reflectionRectTop.setAttribute("height", "1");
    reflectionRectTop.setAttribute("fill", "url(#bubble-reflection-light)");
    reflectionRectTop.setAttribute("transform", "rotate(180, 0.5, 0.5)");
    reflectionMaskTop.appendChild(reflectionRectTop);
    defs.appendChild(reflectionMaskTop);

    const surfaceTransparency = document.createElementNS(SVG_NS, "radialGradient");
    surfaceTransparency.setAttribute("id", "bubble-surface-transparency");
    surfaceTransparency.setAttribute("fx", "25%");
    surfaceTransparency.setAttribute("fy", "25%");
    appendGradientStop(surfaceTransparency, "0%", "black", 1);
    appendGradientStop(surfaceTransparency, "30%", "black", 0.2);
    appendGradientStop(surfaceTransparency, "97%", "white", 0.35);
    appendGradientStop(surfaceTransparency, "100%", "black", 1);
    defs.appendChild(surfaceTransparency);

    const surfaceMask = document.createElementNS(SVG_NS, "mask");
    surfaceMask.setAttribute("id", "bubble-mask-surface");
    surfaceMask.setAttribute("maskContentUnits", "objectBoundingBox");
    const surfaceMaskRect = document.createElementNS(SVG_NS, "rect");
    surfaceMaskRect.setAttribute("width", "1");
    surfaceMaskRect.setAttribute("height", "1");
    surfaceMaskRect.setAttribute("fill", "url(#bubble-surface-transparency)");
    surfaceMask.appendChild(surfaceMaskRect);
    defs.appendChild(surfaceMask);

    const spotGradient = document.createElementNS(SVG_NS, "radialGradient");
    spotGradient.setAttribute("id", "bubble-spot-gradient");
    spotGradient.setAttribute("gradientUnits", "objectBoundingBox");
    spotGradient.setAttribute("cx", "0.5");
    spotGradient.setAttribute("cy", "0.5");
    spotGradient.setAttribute("r", "0.5");
    spotGradient.setAttribute("fx", "0.35");
    spotGradient.setAttribute("fy", "0.2");
    appendGradientStop(spotGradient, "10%", "white", 0.7);
    appendGradientStop(spotGradient, "70%", "white", 0);
    defs.appendChild(spotGradient);
  };

  const createTopicSurfaceGradient = (defs, gradientId, palette) => {
    const gradient = document.createElementNS(SVG_NS, "linearGradient");
    gradient.setAttribute("id", gradientId);
    gradient.setAttribute("x1", "0%");
    gradient.setAttribute("y1", "100%");
    gradient.setAttribute("x2", "100%");
    gradient.setAttribute("y2", "0%");
    appendGradientStop(gradient, "0%", palette.main);
    appendGradientStop(gradient, "52%", palette.light);
    appendGradientStop(gradient, "100%", palette.main);
    defs.appendChild(gradient);
  };

  const createSoapBubbleLayers = (group, defs, palette, index, documentPath) => {
    const surfaceGradientId = `bubble-surface-${index}`;
    createTopicSurfaceGradient(defs, surfaceGradientId, palette);

    const clipPathEl = document.createElementNS(SVG_NS, "clipPath");
    clipPathEl.setAttribute("id", `bubble-clip-${index}`);
    const clipCircle = document.createElementNS(SVG_NS, "circle");
    clipCircle.setAttribute("cx", "0");
    clipCircle.setAttribute("cy", "0");
    clipPathEl.appendChild(clipCircle);
    defs.appendChild(clipPathEl);

    const bubbleBody = document.createElementNS(SVG_NS, "g");
    bubbleBody.setAttribute("clip-path", `url(#bubble-clip-${index})`);
    group.appendChild(bubbleBody);

    const bottomSpot = document.createElementNS(SVG_NS, "ellipse");
    bottomSpot.setAttribute("class", "profession-portfolio-bubbles__bubble-layer");
    bottomSpot.setAttribute("fill", "url(#bubble-spot-gradient)");

    const bottomReflection = document.createElementNS(SVG_NS, "circle");
    bottomReflection.setAttribute("class", "profession-portfolio-bubbles__bubble-layer");
    bottomReflection.setAttribute("fill", palette.main);
    bottomReflection.setAttribute("mask", "url(#bubble-mask-reflection-bottom)");

    const topReflection = document.createElementNS(SVG_NS, "circle");
    topReflection.setAttribute("class", "profession-portfolio-bubbles__bubble-layer");
    topReflection.setAttribute("fill", palette.light);
    topReflection.setAttribute("mask", "url(#bubble-mask-reflection-top)");

    const topSpot = document.createElementNS(SVG_NS, "ellipse");
    topSpot.setAttribute("class", "profession-portfolio-bubbles__bubble-layer");
    topSpot.setAttribute("fill", "url(#bubble-spot-gradient)");

    const surface = document.createElementNS(SVG_NS, "circle");
    surface.setAttribute("class", "profession-portfolio-bubbles__bubble-layer");
    surface.setAttribute("fill", `url(#${surfaceGradientId})`);
    surface.setAttribute("mask", "url(#bubble-mask-surface)");

    const hitCircle = document.createElementNS(SVG_NS, "circle");
    hitCircle.setAttribute("class", "profession-portfolio-bubbles__circle");
    hitCircle.setAttribute("fill", "transparent");
    hitCircle.setAttribute("stroke", "none");

    if (documentPath) {
      hitCircle.classList.add("profession-portfolio-bubbles__circle--link");
      hitCircle.setAttribute("tabindex", "0");
      hitCircle.dataset.documentUrl = documentPath.startsWith("/")
        ? documentPath
        : `/static/${documentPath.replace(/^\/+/, "")}`;
    }

    const shapes = [
      bottomSpot,
      bottomReflection,
      topReflection,
      topSpot,
      surface,
      hitCircle,
    ];
    shapes.forEach((shape) => bubbleBody.appendChild(shape));

    return { hitCircle, bubbleShapes: shapes, clipCircle };
  };

  const updateSoapBubbleShapes = (shapes, radius, clipCircle) => {
    if (!shapes) {
      return;
    }

    const visible = radius > 0;
    shapes.forEach((shape) => {
      shape.setAttribute("visibility", visible ? "visible" : "hidden");
    });
    if (!visible) {
      return;
    }

    const [
      bottomSpot,
      bottomReflection,
      topReflection,
      topSpot,
      surface,
      hitCircle,
    ] = shapes;

    [bottomReflection, topReflection, surface, hitCircle].forEach((circle) => {
      circle.setAttribute("cx", "0");
      circle.setAttribute("cy", "0");
      circle.setAttribute("r", String(radius));
    });

    if (clipCircle) {
      clipCircle.setAttribute("r", String(radius));
    }

    const bottomSpotX = radius * 0.5;
    const bottomSpotY = radius * 0.5;
    bottomSpot.setAttribute("cx", String(bottomSpotX));
    bottomSpot.setAttribute("cy", String(bottomSpotY));
    bottomSpot.setAttribute("rx", String(radius * 0.4));
    bottomSpot.setAttribute("ry", String(radius * 0.2));
    bottomSpot.setAttribute(
      "transform",
      `rotate(-225, ${bottomSpotX}, ${bottomSpotY})`
    );

    const topSpotX = -radius * 0.45;
    const topSpotY = -radius * 0.45;
    topSpot.setAttribute("cx", String(topSpotX));
    topSpot.setAttribute("cy", String(topSpotY));
    topSpot.setAttribute("rx", String(radius * 0.55));
    topSpot.setAttribute("ry", String(radius * 0.25));
    topSpot.setAttribute("transform", `rotate(-45, ${topSpotX}, ${topSpotY})`);
  };

  const easeInQuad = (value) => value * value;

  const easeOutQuad = (value) => 1 - (1 - value) * (1 - value);

  const lerp = (from, to, progress) => from + (to - from) * progress;

  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

  const growSpeedFromId = (id) => {
    const text = String(id ?? "");
    let hash = 5381;
    for (let charIndex = 0; charIndex < text.length; charIndex += 1) {
      hash = (hash * 33) ^ text.charCodeAt(charIndex);
    }
    return 0.5 + (Math.abs(hash) % 501) / 1000;
  };

  const resolveGrowSpeed = (item, animation) => {
    const raw = Number(item.bubbleGrowSpeed);
    const minSpeed = Number(animation.growSpeedMin ?? 0.05);
    const maxSpeed = Number(animation.growSpeedMax ?? 1);
    if (Number.isFinite(raw) && raw > 0) {
      return clamp(raw, minSpeed, maxSpeed);
    }

    const spread = growSpeedFromId(item.id);
    return lerp(minSpeed, maxSpeed, (spread - 0.5) / 0.5);
  };

  const nodeGrowProgress = (elapsed, growDurationMs, growSpeed) =>
    easeOutQuad(Math.min(1, elapsed / (growSpeed * growDurationMs)));

  const computeScale = (items) => {
    let maxReach = 0;
    items.forEach((item) => {
      const relX = Number(item.bubbleX) || 0;
      const relY = Number(item.bubbleY) || 0;
      const diameter = Number(item.bubbleDiameter) || 1;
      maxReach = Math.max(maxReach, Math.hypot(relX, relY) + diameter / 2);
    });
    if (maxReach <= 0) {
      return 1;
    }
    return (SIM_SIZE / 2 - FIT_MARGIN) / maxReach;
  };

  const layoutToSim = (relX, relY, diameter, scale) => ({
    targetX: ORIGIN_X + relX * scale,
    targetY: ORIGIN_Y - relY * scale,
    targetRadius: (diameter * scale) / 2,
  });

  const resolveCollisions = (nodes, padding, repulsion) => {
    for (let index = 0; index < nodes.length; index += 1) {
      for (let nextIndex = index + 1; nextIndex < nodes.length; nextIndex += 1) {
        const first = nodes[index];
        const second = nodes[nextIndex];
        let deltaX = second.x - first.x;
        let deltaY = second.y - first.y;
        let distance = Math.hypot(deltaX, deltaY);
        if (!distance) {
          distance = 0.001;
          deltaX = (Math.random() - 0.5) * 0.02;
          deltaY = (Math.random() - 0.5) * 0.02;
          distance = Math.hypot(deltaX, deltaY) || 0.001;
        }

        const minDistance = first.radius + second.radius + padding;
        if (distance >= minDistance) {
          continue;
        }

        const overlap = minDistance - distance;
        const normalX = deltaX / distance;
        const normalY = deltaY / distance;
        const correction = overlap * 0.5 * repulsion;
        first.x -= normalX * correction;
        first.y -= normalY * correction;
        second.x += normalX * correction;
        second.y += normalY * correction;
      }
    }
  };

  const applyGravity = (nodes, strength) => {
    nodes.forEach((node) => {
      node.vx += (ORIGIN_X - node.x) * strength;
      node.vy += (ORIGIN_Y - node.y) * strength;
    });
  };

  const relaxCluster = (nodes, padding, repulsion, gravity, iterations) => {
    for (let step = 0; step < iterations; step += 1) {
      applyGravity(nodes, gravity);
      nodes.forEach((node) => {
        node.vx *= 0.72;
        node.vy *= 0.72;
        node.x += node.vx;
        node.y += node.vy;
      });
      for (let pass = 0; pass < 4; pass += 1) {
        resolveCollisions(nodes, padding, repulsion);
      }
    }
    nodes.forEach((node) => {
      node.vx = 0;
      node.vy = 0;
    });
  };

  const wrapLabel = (title, radius) => {
    const maxChars = Math.max(8, Math.floor(radius / 3.8));
    const maxLines = 4;
    const lines = [];

    String(title || "")
      .split("\n")
      .forEach((segment) => {
        const words = segment.trim().split(/\s+/).filter(Boolean);
        if (!words.length) {
          return;
        }

        let current = words[0];
        for (let index = 1; index < words.length; index += 1) {
          const candidate = `${current} ${words[index]}`;
          if (candidate.length <= maxChars) {
            current = candidate;
          } else {
            lines.push(current);
            current = words[index];
          }
        }
        lines.push(current);
      });

    if (!lines.length) {
      return [""];
    }
    return lines.slice(0, maxLines);
  };

  const buildChart = (arena, items, scale, animation = {}) => {
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("class", "profession-portfolio-bubbles__chart");
    svg.setAttribute("role", "img");
    svg.setAttribute("overflow", "hidden");
    svg.setAttribute("viewBox", `0 0 ${SIM_SIZE} ${SIM_SIZE}`);
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    svg.setAttribute("aria-label", arena.getAttribute("aria-label") || "Portfolio");

    const defs = document.createElementNS(SVG_NS, "defs");
    const clipPath = document.createElementNS(SVG_NS, "clipPath");
    clipPath.setAttribute("id", "bubble-arena-clip");
    const clipRect = document.createElementNS(SVG_NS, "rect");
    clipRect.setAttribute("x", "0");
    clipRect.setAttribute("y", "0");
    clipRect.setAttribute("width", String(SIM_SIZE));
    clipRect.setAttribute("height", String(SIM_SIZE));
    clipPath.appendChild(clipRect);
    defs.appendChild(clipPath);
    ensureBubbleDefs(defs);
    svg.appendChild(defs);

    const layer = document.createElementNS(SVG_NS, "g");
    layer.setAttribute("clip-path", "url(#bubble-arena-clip)");
    svg.appendChild(layer);

    const nodes = items.map((item, index) => {
      const topic = item.topic || "default";
      const palette = topicPalette(topic);
      const relX = Number(item.bubbleX) || 0;
      const relY = Number(item.bubbleY) || 0;
      const diameter = Number(item.bubbleDiameter) || 1;
      const layout = layoutToSim(relX, relY, diameter, scale);

      const documentPath = item.documentUrl || item.documentPath;
      const group = document.createElementNS(SVG_NS, "g");
      group.setAttribute("class", "profession-portfolio-bubbles__node");
      const { hitCircle, bubbleShapes, clipCircle } = createSoapBubbleLayers(
        group,
        defs,
        palette,
        index,
        documentPath
      );

      const label = document.createElementNS(SVG_NS, "text");
      label.setAttribute("class", "profession-portfolio-bubbles__label");
      label.setAttribute("data-topic", topic);
      label.setAttribute("text-anchor", "middle");
      label.setAttribute("dominant-baseline", "middle");

      const lines = wrapLabel(item.title, layout.targetRadius * 2);
      const lineHeight = readLabelLineHeight(arena);
      const startY = -((lines.length - 1) * lineHeight) / 2;
      lines.forEach((line, lineIndex) => {
        const tspan = document.createElementNS(SVG_NS, "tspan");
        tspan.setAttribute("x", "0");
        tspan.setAttribute("y", String(startY + lineIndex * lineHeight));
        tspan.textContent = line;
        label.appendChild(tspan);
      });

      group.appendChild(label);
      layer.appendChild(group);

      return {
        item,
        relX,
        relY,
        hitCircle,
        bubbleShapes,
        clipCircle,
        label,
        group,
        ...layout,
        growSpeed: resolveGrowSpeed(item, animation),
        radius: 0,
        x: ORIGIN_X,
        y: ORIGIN_Y,
        vx: 0,
        vy: 0,
      };
    });

    const title = arena.querySelector(".profession-portfolio-bubbles__title");
    const footer = arena.querySelector(".profession-portfolio-bubbles__footer");
    arena.textContent = "";
    if (title) {
      arena.appendChild(title);
    }
    arena.appendChild(svg);
    if (footer) {
      arena.appendChild(footer);
    }

    return { svg, nodes };
  };

  const applyNodeGeometry = (nodes) => {
    nodes.forEach((node) => {
      const radius = Math.max(0, node.radius);
      node.group.setAttribute("transform", `translate(${node.x} ${node.y})`);
      updateSoapBubbleShapes(node.bubbleShapes, radius, node.clipCircle);
      node.label.style.opacity =
        radius > 0 ? String(Math.max(0, Math.min(1, node.labelOpacity ?? 0))) : "0";
      node.group.dataset.bubbleId = node.item.id || "";
    });
  };

  const freezeAtActualPosition = (nodes) => {
    nodes.forEach((node) => {
      node.radius = node.targetRadius;
      node.vx = 0;
      node.vy = 0;
      node.labelOpacity = 1;
    });
    applyNodeGeometry(nodes);
  };

  const snapToLayout = (nodes, animation) => {
    nodes.forEach((node) => {
      node.x = node.targetX;
      node.y = node.targetY;
      node.radius = node.targetRadius;
      node.vx = 0;
      node.vy = 0;
      node.labelOpacity = 1;
    });
    relaxCluster(
      nodes,
      Number(animation.padding ?? 4),
      Number(animation.repulsion ?? 1),
      Number(animation.gravity ?? 0.022) * 1.4,
      Number(animation.settlePasses ?? 80)
    );
    applyNodeGeometry(nodes);
  };

  const initSpawnState = (nodes, spawnFactor, approachStrength) => {
    nodes.forEach((node) => {
      node.x = ORIGIN_X + (node.targetX - ORIGIN_X) * spawnFactor;
      node.y = ORIGIN_Y + (node.targetY - ORIGIN_Y) * spawnFactor;
      node.radius = 0;
      node.labelOpacity = 0;
      node.vx = (node.targetX - node.x) * approachStrength;
      node.vy = (node.targetY - node.y) * approachStrength;
    });
  };

  const runIntroAnimation = (nodes, animation) => {
    const settleDurationMs = Number(animation.settleDurationMs ?? 3000);
    const growDurationMs = Number(animation.growDurationMs ?? 2000);
    const spawnFactor = Number(animation.spawnFactor ?? 0.85);
    const gravity = Number(animation.gravity ?? 0.022);
    const repulsion = Number(animation.repulsion ?? 1);
    const padding = Number(animation.padding ?? 4);
    const damping = Number(animation.damping ?? 0.88);
    const settleDamping = Number(animation.settleDamping ?? 0.52);
    const approachStrength = Number(animation.approachStrength ?? 0.035);
    const collisionPasses = Number(animation.collisionPasses ?? 6);
    const settleWindowMs = Math.max(0, settleDurationMs - growDurationMs);

    initSpawnState(nodes, spawnFactor, approachStrength);
    applyNodeGeometry(nodes);

    const startTime = performance.now();

    const tick = (now) => {
      const elapsed = now - startTime;

      if (elapsed >= settleDurationMs) {
        freezeAtActualPosition(nodes);
        return;
      }

      const inSettlePhase = elapsed >= growDurationMs && settleWindowMs > 0;
      const settleProgress = inSettlePhase
        ? easeInQuad(Math.min(1, (elapsed - growDurationMs) / settleWindowMs))
        : 0;

      const vectorProgress =
        spawnFactor + (1 - spawnFactor) * Math.min(1, elapsed / settleDurationMs);

      const approachScale = inSettlePhase
        ? approachStrength * (1 - settleProgress)
        : approachStrength;

      const gravityScale = inSettlePhase ? 1 - settleProgress * 0.35 : 1;
      const effectiveDamping = inSettlePhase
        ? lerp(damping, settleDamping, settleProgress)
        : damping;

      const labelOpacity = Math.min(1, elapsed / growDurationMs);

      nodes.forEach((node) => {
        node.radius =
          node.targetRadius *
          nodeGrowProgress(elapsed, growDurationMs, node.growSpeed);
        node.labelOpacity = labelOpacity;

        const idealX = ORIGIN_X + (node.targetX - ORIGIN_X) * vectorProgress;
        const idealY = ORIGIN_Y + (node.targetY - ORIGIN_Y) * vectorProgress;

        node.vx += (idealX - node.x) * approachScale;
        node.vy += (idealY - node.y) * approachScale;
        node.vx += (ORIGIN_X - node.x) * gravity * gravityScale;
        node.vy += (ORIGIN_Y - node.y) * gravity * gravityScale;

        node.vx *= effectiveDamping;
        node.vy *= effectiveDamping;

        if (inSettlePhase) {
          const velocityFade = 1 - settleProgress * 0.92;
          node.vx *= velocityFade;
          node.vy *= velocityFade;
        }

        node.x += node.vx;
        node.y += node.vy;
      });

      for (let pass = 0; pass < collisionPasses; pass += 1) {
        resolveCollisions(nodes, padding, repulsion);
      }

      applyNodeGeometry(nodes);
      window.requestAnimationFrame(tick);
    };

    window.requestAnimationFrame(tick);
  };

  const start = () => {
    const payload = window.__PORTFOLIO_BUBBLES__;
    if (!payload || !Array.isArray(payload.items) || !payload.items.length) {
      return;
    }

    const arena = document.querySelector("[data-bubble-arena]");
    if (!arena) {
      return;
    }

    const animation =
      payload.animation && typeof payload.animation === "object"
        ? payload.animation
        : {};

    const scale = computeScale(payload.items);
    const { nodes } = buildChart(arena, payload.items, scale, animation);

    if (prefersReducedMotion) {
      snapToLayout(nodes, animation);
      return;
    }

    runIntroAnimation(nodes, animation);

    const openDocument = (url) => {
      if (!url) {
        return;
      }
      window.open(url, "_blank", "noopener,noreferrer");
    };

    arena.addEventListener("click", (event) => {
      const target = event.target.closest(".profession-portfolio-bubbles__circle--link");
      if (!target) {
        return;
      }
      openDocument(target.dataset.documentUrl);
    });

    arena.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") {
        return;
      }
      const target = event.target.closest(".profession-portfolio-bubbles__circle--link");
      if (!target) {
        return;
      }
      event.preventDefault();
      openDocument(target.dataset.documentUrl);
    });
  };

  let started = false;

  const startOnce = () => {
    if (started) {
      return;
    }
    started = true;
    start();
  };

  const scheduleStartWhenVisible = () => {
    const portfolioSection = document.querySelector("[data-bubble-portfolio]");
    const arena = document.querySelector("[data-bubble-arena]");
    const observeTarget = portfolioSection || arena;

    if (!observeTarget) {
      return;
    }

    const payload = window.__PORTFOLIO_BUBBLES__;
    if (!payload || !Array.isArray(payload.items) || !payload.items.length) {
      return;
    }

    if (typeof IntersectionObserver === "undefined") {
      startOnce();
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const isVisible = entries.some(
          (entry) => entry.isIntersecting && entry.intersectionRatio > 0
        );
        if (!isVisible) {
          return;
        }
        observer.disconnect();
        startOnce();
      },
      {
        root: null,
        rootMargin: "0px",
        threshold: [0, 0.08],
      }
    );

    observer.observe(observeTarget);
  };

  const boot = () => {
    scheduleStartWhenVisible();
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
