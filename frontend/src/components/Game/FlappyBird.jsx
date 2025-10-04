// src/components/Game/FlappyGame.jsx
import React, { useRef, useEffect, useState } from "react";

/**
 * Lightweight Flappy-like game using canvas.
 * - Bird floats/bobs in pre-start state until first click/space.
 * - Easy mode: larger gaps, slower pipes, lower gravity.
 * - Controls: click/tap/space to flap.
 *
 * Props:
 *  - width (optional), height (optional)
 *  - onClose() optional callback
 */
const FlappyGame = ({ width = 480, height = 360, onClose }) => {
  const canvasRef = useRef(null);
  const rafRef = useRef(null);
  const lastTimeRef = useRef(0);
  const spawnTimerRef = useRef(0);
  const [started, setStarted] = useState(false);
  const [gameOver, setGameOver] = useState(false);
  const [score, setScore] = useState(0);

  // Nice easy physics settings
  const GRAVITY = 0.22; // low gravity -> easier
  const FLAP_V = -6.8; // strong flap
  const PIPE_SPEED = 2.0; // slower pipes
  const PIPE_GAP = 180; // big gap
  const PIPE_INTERVAL = 2200; // ms between pipes
  const PIPE_WIDTH = 56;
  const BIRD_RADIUS = 14;

  // refs for mutable game state
  const stateRef = useRef({
    bird: { x: 80, y: height / 2, vy: 0, radius: BIRD_RADIUS },
    pipes: [], // { x, gapY, passed }
    running: true,
    lastSpawn: 0,
    score: 0,
  });

  // Utility: reset game
  const resetGame = () => {
    stateRef.current = {
      bird: { x: 80, y: height / 2, vy: 0, radius: BIRD_RADIUS },
      pipes: [],
      running: true,
      lastSpawn: performance.now(),
      score: 0,
    };
    setScore(0);
    setGameOver(false);
    setStarted(false);
  };

  // flap action (click/space/tap)
  const flap = () => {
    // first interaction: start the game loop in "started" state
    if (!started) setStarted(true);
    if (stateRef.current.running && !gameOver) {
      stateRef.current.bird.vy = FLAP_V;
    }
  };

  // collision detection
  const collidesWithPipe = (bird, pipe) => {
    const bx = bird.x;
    const by = bird.y;
    const r = bird.radius;
    const px = pipe.x;
    const gapY = pipe.gapY;
    // pipe rects: top (0 -> gapY), bottom (gapY+GAP -> canvas)
    const insideX = bx + r > px && bx - r < px + PIPE_WIDTH;
    if (!insideX) return false;
    if (by - r < gapY) return true;
    if (by + r > gapY + PIPE_GAP) return true;
    return false;
  };

  // game loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    // handle high DPI
    const DPR = window.devicePixelRatio || 1;
    canvas.width = width * DPR;
    canvas.height = height * DPR;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(DPR, DPR);

    // touch/click handlers
    const handlePointerDown = (e) => {
      e.preventDefault();
      flap();
    };
    const handleKeyDown = (e) => {
      if (e.code === "Space") {
        e.preventDefault();
        flap();
      }
      if (e.code === "KeyR" && gameOver) {
        resetGame();
      }
    };

    canvas.addEventListener("pointerdown", handlePointerDown);
    window.addEventListener("keydown", handleKeyDown);

    // main animation
    const step = (t) => {
      if (!lastTimeRef.current) lastTimeRef.current = t;
      const dt = t - lastTimeRef.current;
      lastTimeRef.current = t;

      const s = stateRef.current;

      // Pre-start: bird gently bob up/down, no physics
      if (!started) {
        const bob = Math.sin(t / 300) * 8;
        s.bird.y = height / 2 + bob;
      } else if (s.running && !gameOver) {
        // physics
        s.bird.vy += GRAVITY;
        s.bird.y += s.bird.vy;
        // floor/ceiling check
        if (s.bird.y + s.bird.radius >= height - 8) {
          s.bird.y = height - 8 - s.bird.radius;
          s.bird.vy = 0;
          setGameOver(true);
          s.running = false;
        }
        if (s.bird.y - s.bird.radius <= 0) {
          s.bird.y = s.bird.radius + 2;
          s.bird.vy = 0;
        }

        // spawn pipes by time
        if (t - s.lastSpawn > PIPE_INTERVAL) {
          s.lastSpawn = t;
          const minGapTop = 60;
          const maxGapTop = height - PIPE_GAP - 80;
          const gapY = minGapTop + Math.random() * Math.max(0, maxGapTop - minGapTop);
          s.pipes.push({ x: width + 20, gapY, passed: false });
        }

        // move pipes
        for (const p of s.pipes) {
          p.x -= PIPE_SPEED;
        }
        // remove offscreen
        s.pipes = s.pipes.filter((p) => p.x + PIPE_WIDTH > -10);

        // scoring and collision
        for (const p of s.pipes) {
          if (!p.passed && p.x + PIPE_WIDTH < s.bird.x) {
            p.passed = true;
            s.score += 1;
            setScore(s.score);
          }
          if (collidesWithPipe(s.bird, p)) {
            s.running = false;
            setGameOver(true);
          }
        }
      }

      // --- draw ---
      // background
      ctx.fillStyle = "#71c5cf";
      ctx.fillRect(0, 0, width, height);

      // ground
      ctx.fillStyle = "#7b4f3e";
      ctx.fillRect(0, height - 10, width, 10);

      // pipes
      for (const p of stateRef.current.pipes) {
        ctx.fillStyle = "#2e8b57";
        // top pipe
        ctx.fillRect(p.x, 0, PIPE_WIDTH, p.gapY);
        // bottom pipe
        ctx.fillRect(p.x, p.gapY + PIPE_GAP, PIPE_WIDTH, height - (p.gapY + PIPE_GAP) - 10);
        // pipe caps
        ctx.fillStyle = "#1f6b3d";
        ctx.fillRect(p.x - 2, p.gapY - 6, PIPE_WIDTH + 4, 6);
        ctx.fillRect(p.x - 2, p.gapY + PIPE_GAP, PIPE_WIDTH + 4, 6);
      }

      // bird (simple circle with eye)
      const b = stateRef.current.bird;
      ctx.beginPath();
      ctx.fillStyle = "#ffdd57";
      ctx.arc(b.x, b.y, b.radius, 0, Math.PI * 2);
      ctx.fill();
      // eye
      ctx.beginPath();
      ctx.fillStyle = "#000";
      ctx.arc(b.x + 6, b.y - 4, 3, 0, Math.PI * 2);
      ctx.fill();
      // score
      ctx.fillStyle = "#fff";
      ctx.font = "20px Inter, Arial";
      ctx.fillText(`Score: ${score}`, 12, 28);

      // Pre-start overlay text
      if (!started && !gameOver) {
        ctx.fillStyle = "rgba(0,0,0,0.4)";
        ctx.fillRect(0, 0, width, height);
        ctx.fillStyle = "#fff";
        ctx.font = "22px Inter, Arial";
        ctx.textAlign = "center";
        ctx.fillText("Click / Tap / Press Space to start", width / 2, height / 2 - 8);
        ctx.font = "14px Inter, Arial";
        ctx.fillText("Bird will float until you start", width / 2, height / 2 + 18);
        ctx.textAlign = "left";
      }

      // Game over overlay
      if (gameOver) {
        ctx.fillStyle = "rgba(0,0,0,0.55)";
        ctx.fillRect(0, 0, width, height);
        ctx.fillStyle = "#fff";
        ctx.textAlign = "center";
        ctx.font = "28px Inter, Arial";
        ctx.fillText("Game Over", width / 2, height / 2 - 8);
        ctx.font = "18px Inter, Arial";
        ctx.fillText(`Score: ${score}`, width / 2, height / 2 + 20);
        ctx.font = "14px Inter, Arial";
        ctx.fillText("Press R to restart or click Restart below", width / 2, height / 2 + 44);
      }

      // continue
      rafRef.current = requestAnimationFrame(step);
    };

    rafRef.current = requestAnimationFrame(step);

    return () => {
      cancelAnimationFrame(rafRef.current);
      canvas.removeEventListener("pointerdown", handlePointerDown);
      window.removeEventListener("keydown", handleKeyDown);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [width, height, started, gameOver]);

  // small UI below canvas
  return (
    <div style={{ textAlign: "center" }}>
      <canvas
        ref={canvasRef}
        style={{
          display: "block",
          margin: "0 auto",
          borderRadius: 8,
          boxShadow: "0 8px 20px rgba(0,0,0,0.35)",
          touchAction: "none",
          background: "#71c5cf",
        }}
        width={width}
        height={height}
      />
      <div style={{ marginTop: 8, display: "flex", justifyContent: "center", gap: 8 }}>
        <button
          onClick={() => {
            if (gameOver) {
              resetGame();
            } else {
              // emulate flap start
              if (!started) setStarted(true);
              flap();
            }
          }}
          style={{ padding: "8px 12px", borderRadius: 6 }}
        >
          {gameOver ? "Restart" : "Flap / Start"}
        </button>
        <button onClick={() => onClose && onClose()} style={{ padding: "8px 12px", borderRadius: 6 }}>
          Close
        </button>
      </div>
    </div>
  );
};

export default FlappyGame;
