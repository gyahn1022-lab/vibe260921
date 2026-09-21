import random
import tkinter as tk
from collections import deque

CELL = 20
COLS = 30
ROWS = 20
DELAY = 110  # ms per move

DIRS = {
    "Up": (0, -1),
    "Down": (0, 1),
    "Left": (-1, 0),
    "Right": (1, 0),
}
OPPOSITE = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}


class Snake:
    def __init__(self, start, direction, head_color, body_color, name):
        x, y = start
        dx, dy = DIRS[OPPOSITE[direction]]
        self.body = [(x + dx * i, y + dy * i) for i in range(3)]
        self.direction = direction
        self.pending = direction
        self.head_color = head_color
        self.body_color = body_color
        self.name = name
        self.score = 0
        self.alive = True


class SnakeGame:
    def __init__(self, root):
        self.root = root
        root.title("Snake: You vs AI")
        root.resizable(False, False)
        self.score_var = tk.StringVar()
        tk.Label(root, textvariable=self.score_var, font=("Arial", 14)).pack()
        self.canvas = tk.Canvas(
            root, width=COLS * CELL, height=ROWS * CELL, bg="#111"
        )
        self.canvas.pack()
        root.bind("<Key>", self.on_key)
        self.reset()

    def reset(self):
        self.player = Snake((5, ROWS // 2 + 4), "Right", "#a5d6a7", "#66bb6a", "You")
        self.ai = Snake((COLS - 6, ROWS // 2 - 4), "Left", "#90caf9", "#42a5f5", "AI")
        self.game_over = False
        self.place_food()
        self.update_score()
        self.tick()

    def update_score(self):
        self.score_var.set(f"You: {self.player.score}    AI: {self.ai.score}")

    def place_food(self):
        taken = set(self.player.body) | set(self.ai.body)
        free = [
            (x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in taken
        ]
        self.food = random.choice(free) if free else None

    # ---------- input ----------
    def on_key(self, event):
        key = event.keysym
        wasd = {"w": "Up", "s": "Down", "a": "Left", "d": "Right"}
        key = wasd.get(key.lower(), key)
        if key in DIRS and key != OPPOSITE[self.player.direction]:
            self.player.pending = key
        elif key.lower() == "r" and self.game_over:
            self.reset()

    # ---------- AI ----------
    def in_bounds(self, p):
        return 0 <= p[0] < COLS and 0 <= p[1] < ROWS

    def ai_choose(self):
        ai, pl = self.ai, self.player
        head = ai.body[0]
        # tails will move away, so they are not obstacles
        blocked = set(ai.body[:-1]) | set(pl.body[:-1])
        # avoid cells the human head could step into next turn
        px, py = pl.body[0]
        danger = {
            (px + dx, py + dy)
            for d, (dx, dy) in DIRS.items()
            if d != OPPOSITE[pl.direction]
        }

        def neighbors(p, avoid):
            for d, (dx, dy) in DIRS.items():
                q = (p[0] + dx, p[1] + dy)
                if self.in_bounds(q) and q not in blocked and q not in avoid:
                    yield d, q

        def bfs_first_step(avoid):
            queue = deque()
            seen = {head}
            for d, q in neighbors(head, avoid):
                if d == OPPOSITE[ai.direction]:
                    continue
                queue.append((q, d))
                seen.add(q)
            while queue:
                p, first = queue.popleft()
                if p == self.food:
                    return first
                for _, q in neighbors(p, avoid):
                    if q not in seen:
                        seen.add(q)
                        queue.append((q, first))
            return None

        def area(start, avoid):
            seen = {start}
            stack = [start]
            while stack:
                p = stack.pop()
                for _, q in neighbors(p, avoid):
                    if q not in seen:
                        seen.add(q)
                        stack.append(q)
            return len(seen)

        # 1) shortest path to food, avoiding human head reach if possible
        for avoid in (danger - {self.food}, set()):
            step = bfs_first_step(avoid)
            if step:
                # make sure we do not seal ourselves into a tiny pocket
                dx, dy = DIRS[step]
                nxt = (head[0] + dx, head[1] + dy)
                if area(nxt, avoid) >= len(ai.body):
                    return step
        # 2) otherwise go to the move with the most open space
        best, best_area = ai.direction, -1
        for d, q in neighbors(head, set()):
            if d == OPPOSITE[ai.direction]:
                continue
            a = area(q, set())
            if a > best_area:
                best, best_area = d, a
        return best

    # ---------- game loop ----------
    def tick(self):
        if self.game_over:
            return
        pl, ai = self.player, self.ai
        pl.direction = pl.pending
        ai.direction = self.ai_choose()

        heads = {}
        for s in (pl, ai):
            dx, dy = DIRS[s.direction]
            hx, hy = s.body[0]
            heads[s] = (hx + dx, hy + dy)

        # move both snakes
        for s in (pl, ai):
            s.body.insert(0, heads[s])
        eaters = [s for s in (pl, ai) if heads[s] == self.food]
        for s in (pl, ai):
            if s not in eaters:
                s.body.pop()
        # if both reach the food at once, nobody scores (head-on collision anyway)
        for s in eaters:
            s.score += 1

        # collisions
        for s in (pl, ai):
            h = s.body[0]
            other = ai if s is pl else pl
            if (
                not self.in_bounds(h)
                or h in s.body[1:]
                or h in other.body[1:]
                or h == other.body[0]
            ):
                s.alive = False

        if eaters and pl.alive and ai.alive:
            self.place_food()
        self.update_score()
        self.draw()

        if not (pl.alive and ai.alive):
            self.end()
            return
        self.root.after(DELAY, self.tick)

    def draw(self):
        c = self.canvas
        c.delete("all")
        if self.food:
            fx, fy = self.food
            c.create_oval(
                fx * CELL + 2, fy * CELL + 2,
                (fx + 1) * CELL - 2, (fy + 1) * CELL - 2,
                fill="#e53935", outline="",
            )
        for s in (self.player, self.ai):
            for i, (x, y) in enumerate(s.body):
                c.create_rectangle(
                    x * CELL + 1, y * CELL + 1,
                    (x + 1) * CELL - 1, (y + 1) * CELL - 1,
                    fill=s.body_color if i else s.head_color, outline="",
                )

    def end(self):
        self.game_over = True
        pl, ai = self.player, self.ai
        if pl.alive and not ai.alive:
            msg = "You Win!"
        elif ai.alive and not pl.alive:
            msg = "AI Wins!"
        elif pl.score != ai.score:
            msg = "You Win!" if pl.score > ai.score else "AI Wins!"
        else:
            msg = "Draw"
        cx, cy = COLS * CELL // 2, ROWS * CELL // 2
        self.canvas.create_text(
            cx, cy - 15, text=msg, fill="white", font=("Arial", 28, "bold")
        )
        self.canvas.create_text(
            cx, cy + 25, text="Press R to restart", fill="white", font=("Arial", 14)
        )


if __name__ == "__main__":
    root = tk.Tk()
    SnakeGame(root)
    root.mainloop()
