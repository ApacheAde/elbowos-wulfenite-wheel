"""Wulfenite Wheel — neon bucket-wheel ore scoop for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/WULFENITE_WHEEL_ElbowOS.mp4")
TAU = math.tau
NBUCK = 8
CX, CY, RAD = 540, 1180, 360
BG = (22, 10, 8)
AMBER = (255, 168, 42)
COPPER = (186, 84, 36)
CREAM = (255, 236, 198)
LIME = (168, 255, 74)
SLAG = (255, 64, 88)
GOLD = (255, 214, 72)
TEAL = (64, 232, 210)

class Ore:
    def __init__(self):
        self.x = random.randint(180, 900)
        self.y = random.randint(-280, -40)
        self.vy = random.uniform(7.5, 11.5)
        self.kind = random.choices(("lime", "gold", "slag"), (0.62, 0.18, 0.20))[0]
        self.alive = True
        self.spin = random.random() * TAU

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption("Wulfenite Wheel")
        self.font = pygame.font.SysFont("dejavusans", 64, bold=True)
        self.small = pygame.font.SysFont("dejavusans", 36, bold=True)
        self.tiny = pygame.font.SysFont("dejavusans", 28, bold=True)
        self.reset()

    def reset(self):
        self.angle = 0.0
        self.spin = 1.2
        self.score = 0
        self.heat = 0
        self.t = 0
        self.ores = [Ore() for _ in range(6)]
        self.pops = []
        self.sparks = [[random.randint(0, W), random.randint(0, H), random.uniform(1, 4)] for _ in range(80)]
        self.flash = 0
        self.filled = 0

    def bucket(self, i):
        a = self.angle + i * TAU / NBUCK
        return CX + math.cos(a) * RAD, CY + math.sin(a) * RAD, a

    def spawn(self):
        if len([o for o in self.ores if o.alive]) < 9:
            self.ores.append(Ore())

    def auto(self):
        band = [o for o in self.ores if o.alive and o.kind != "slag" and 500 < o.y < 980]
        if not band:
            self.spin = 1.6
            return
        c = min(band, key=lambda o: abs(o.y - (CY - RAD)))
        dx = max(-0.92, min(0.92, (c.x - CX) / RAD))
        target = -math.pi / 2 + math.asin(dx)
        best = 9.0
        for i in range(NBUCK):
            a = self.angle + i * TAU / NBUCK
            d = (a - target + math.pi) % TAU - math.pi
            if abs(d) < abs(best):
                best = d
        self.spin = max(-4.2, min(4.2, -best * 6.5))

    def step(self, keys=None):
        self.t += 1
        if keys is not None:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.spin -= 0.35
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.spin += 0.35
            if keys[pygame.K_SPACE]:
                self.spin *= 1.08
        else:
            self.auto()
        self.spin *= 0.96
        self.angle += self.spin * 0.045
        if self.t % 18 == 0:
            self.spawn()
        for o in self.ores:
            if not o.alive:
                continue
            o.y += o.vy
            o.spin += 0.08
            caught = False
            for i in range(NBUCK):
                bx, by, _ = self.bucket(i)
                if by < CY - 30 and math.hypot(o.x - bx, o.y - by) < 78:
                    caught = True
                    break
            if caught:
                o.alive = False
                if o.kind == "slag":
                    self.score = max(0, self.score - 40)
                    self.flash = 8
                    self.pops.append([o.x, o.y, "-40", SLAG, 28])
                else:
                    gain = 250 if o.kind == "gold" else 100
                    self.score += gain
                    self.filled = min(12, self.filled + 1)
                    self.pops.append([o.x, o.y, f"+{gain}", GOLD if o.kind == "gold" else LIME, 28])
            elif o.y > H + 30:
                o.alive = False
        self.ores = [o for o in self.ores if o.alive or o.y < H + 40][-14:]
        for p in self.pops:
            p[1] -= 3
            p[4] -= 1
        self.pops = [p for p in self.pops if p[4] > 0]
        for s in self.sparks:
            s[1] -= s[2]
            if s[1] < 0:
                s[0], s[1] = random.randint(0, W), H
        self.flash = max(0, self.flash - 1)
        self.heat = (self.heat + 2) % 360

    def draw(self, surf):
        surf.fill(BG)
        for y in range(0, H, 8):
            k = y / H
            pygame.draw.line(surf, (28 + int(40 * k), 12, 10 + int(18 * (1 - k))), (0, y), (W, y), 8)
        for s in self.sparks:
            pygame.draw.circle(surf, (255, 140 + int(s[2] * 20), 40), (int(s[0]), int(s[1])), 2)
        for i, col in enumerate((COPPER, AMBER, (120, 40, 28))):
            pygame.draw.arc(surf, col, (80 + i * 18, 180, 920 - i * 36, 1500), 0.3, math.pi - 0.3, 4)
        glow = 90 + int(30 * math.sin(self.t * 0.2))
        pygame.draw.circle(surf, (glow, 36, 16), (CX, CY), RAD + 28, 10)
        pygame.draw.circle(surf, (48, 22, 14), (CX, CY), RAD - 18)
        for i in range(NBUCK):
            bx, by, a = self.bucket(i)
            pygame.draw.line(surf, AMBER, (CX, CY), (int(bx), int(by)), 8)
            cup = pygame.Surface((90, 54), pygame.SRCALPHA)
            pygame.draw.ellipse(cup, (*AMBER, 230), (0, 0, 90, 54))
            pygame.draw.ellipse(cup, (*CREAM, 180), (16, 10, 58, 22))
            rot = pygame.transform.rotate(cup, -math.degrees(a) - 90)
            surf.blit(rot, rot.get_rect(center=(int(bx), int(by))))
        pygame.draw.circle(surf, GOLD, (CX, CY), 46)
        pygame.draw.circle(surf, COPPER, (CX, CY), 46, 6)
        for o in self.ores:
            if not o.alive:
                continue
            col = {"lime": LIME, "gold": GOLD, "slag": SLAG}[o.kind]
            pts = []
            for k in range(6):
                ang = o.spin + k * TAU / 6
                pts.append((o.x + math.cos(ang) * 28, o.y + math.sin(ang) * 28))
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, CREAM, pts, 3)
        pygame.draw.polygon(surf, (70, 28, 18), [(160, 250), (920, 250), (780, 420), (300, 420)])
        pygame.draw.polygon(surf, AMBER, [(160, 250), (920, 250), (780, 420), (300, 420)], 4)
        pygame.draw.rect(surf, (40, 20, 16), (120, 1680, 840, 36), border_radius=8)
        for i in range(self.filled):
            pygame.draw.rect(surf, LIME if i % 3 else GOLD, (136 + i * 66, 1688, 50, 20), border_radius=4)
        for p in self.pops:
            tag = self.small.render(p[2], True, p[3])
            surf.blit(tag, tag.get_rect(center=(int(p[0]), int(p[1]))))
        if self.flash:
            veil = pygame.Surface((W, H), pygame.SRCALPHA)
            veil.fill((255, 40, 60, 70))
            surf.blit(veil, (0, 0))
        title = self.font.render("WULFENITE WHEEL", True, AMBER)
        surf.blit(title, title.get_rect(center=(W // 2, 110)))
        sub = self.tiny.render("SCOOP THE ORE  \u00b7  DODGE SLAG", True, CREAM)
        surf.blit(sub, sub.get_rect(center=(W // 2, 172)))
        sc = self.font.render(f"{self.score:05d}", True, GOLD)
        surf.blit(sc, sc.get_rect(center=(W // 2, 1760)))
        brand = self.small.render("x.com/ElbowOS", True, TEAL)
        surf.blit(brand, brand.get_rect(center=(W // 2, 1848)))

    def play_interactive(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                    self.reset()
            self.step(pygame.key.get_pressed())
            self.draw(self.screen)
            pygame.display.flip()
            clock.tick(FPS)
        pygame.quit()

    def record(self):
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "veryfast", "-movflags", "+faststart", OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = FPS * SECS
        try:
            for _ in range(frames):
                self.step(None)
                self.draw(self.screen)
                proc.stdin.write(pygame.image.tobytes(self.screen, "RGB"))
        finally:
            proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1500:]}")
        alt = "/home/workdir/artifacts/WULFENITE_WHEEL_ElbowOS.mp4"
        if os.path.abspath(OUT) != os.path.abspath(alt):
            os.makedirs(os.path.dirname(alt), exist_ok=True)
            import shutil
            shutil.copy2(OUT, alt)
        print("wrote", OUT)
        pygame.quit()

def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
