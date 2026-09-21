import tkinter as tk
import random

WIDTH, HEIGHT = 640, 480
PADDLE_W, PADDLE_H = 90, 12
BALL_R = 8
ROWS, COLS = 6, 10
BRICK_W = WIDTH // COLS
BRICK_H = 22
COLORS = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db", "#9b59b6"]


class Breakout:
    def __init__(self, root):
        self.root = root
        root.title("블럭깨기")
        root.resizable(False, False)
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="black")
        self.canvas.pack()
        self.left = self.right = False
        root.bind("<KeyPress-Left>", lambda e: self.set_dir(left=True))
        root.bind("<KeyRelease-Left>", lambda e: self.set_dir(left=False))
        root.bind("<KeyPress-Right>", lambda e: self.set_dir(right=True))
        root.bind("<KeyRelease-Right>", lambda e: self.set_dir(right=False))
        root.bind("<Motion>", self.on_mouse)
        root.bind("<space>", self.on_space)
        self.new_game()
        self.loop()

    def set_dir(self, left=None, right=None):
        if left is not None:
            self.left = left
        if right is not None:
            self.right = right

    def on_mouse(self, e):
        if self.state != "over":
            x = max(PADDLE_W / 2, min(WIDTH - PADDLE_W / 2, e.x))
            self.paddle_x = x

    def new_game(self):
        self.canvas.delete("all")
        self.score = 0
        self.lives = 3
        self.level_speed = 5
        self.bricks = {}
        for r in range(ROWS):
            for c in range(COLS):
                x1, y1 = c * BRICK_W, 40 + r * BRICK_H
                item = self.canvas.create_rectangle(
                    x1 + 1, y1 + 1, x1 + BRICK_W - 1, y1 + BRICK_H - 1,
                    fill=COLORS[r % len(COLORS)], outline="")
                self.bricks[item] = (ROWS - r) * 10
        self.paddle_x = WIDTH / 2
        self.paddle = self.canvas.create_rectangle(0, 0, 0, 0, fill="white", outline="")
        self.ball = self.canvas.create_oval(0, 0, 0, 0, fill="white", outline="")
        self.hud = self.canvas.create_text(10, 10, anchor="nw", fill="white",
                                           font=("Arial", 14), text="")
        self.msg = self.canvas.create_text(WIDTH / 2, HEIGHT / 2, fill="white",
                                           font=("Arial", 20, "bold"), text="")
        self.reset_ball()

    def reset_ball(self):
        self.state = "ready"
        self.bx, self.by = self.paddle_x, HEIGHT - 40 - BALL_R
        self.vx = random.choice([-1, 1]) * self.level_speed * 0.6
        self.vy = -self.level_speed
        self.canvas.itemconfig(self.msg, text="스페이스바를 눌러 시작\n(← → 키 또는 마우스로 이동)")

    def on_space(self, e):
        if self.state == "ready":
            self.state = "play"
            self.canvas.itemconfig(self.msg, text="")
        elif self.state == "over":
            self.new_game()

    def end(self, text):
        self.state = "over"
        self.canvas.itemconfig(self.msg, text=f"{text}\n점수: {self.score}\n스페이스바로 다시 시작")

    def update(self):
        if self.left:
            self.paddle_x = max(PADDLE_W / 2, self.paddle_x - 9)
        if self.right:
            self.paddle_x = min(WIDTH - PADDLE_W / 2, self.paddle_x + 9)
        py = HEIGHT - 30
        pl, pr = self.paddle_x - PADDLE_W / 2, self.paddle_x + PADDLE_W / 2

        if self.state == "ready":
            self.bx, self.by = self.paddle_x, py - BALL_R
        elif self.state == "play":
            self.bx += self.vx
            self.by += self.vy
            # 벽 충돌
            if self.bx < BALL_R:
                self.bx, self.vx = BALL_R, abs(self.vx)
            elif self.bx > WIDTH - BALL_R:
                self.bx, self.vx = WIDTH - BALL_R, -abs(self.vx)
            if self.by < BALL_R:
                self.by, self.vy = BALL_R, abs(self.vy)
            # 패들 충돌
            if (self.vy > 0 and py <= self.by + BALL_R <= py + PADDLE_H + self.vy
                    and pl - BALL_R <= self.bx <= pr + BALL_R):
                offset = (self.bx - self.paddle_x) / (PADDLE_W / 2)
                self.vx = offset * self.level_speed * 1.2
                self.vy = -abs(self.vy)
                self.by = py - BALL_R
            # 블럭 충돌
            hit = self.canvas.find_overlapping(self.bx - BALL_R, self.by - BALL_R,
                                               self.bx + BALL_R, self.by + BALL_R)
            for item in hit:
                if item in self.bricks:
                    x1, y1, x2, y2 = self.canvas.coords(item)
                    self.score += self.bricks.pop(item)
                    self.canvas.delete(item)
                    if x1 <= self.bx <= x2:
                        self.vy = -self.vy
                    else:
                        self.vx = -self.vx
                    break
            if not self.bricks:
                self.end("승리!")
            # 바닥
            if self.by > HEIGHT:
                self.lives -= 1
                if self.lives <= 0:
                    self.end("게임 오버")
                else:
                    self.reset_ball()

        c = self.canvas
        c.coords(self.paddle, pl, py, pr, py + PADDLE_H)
        c.coords(self.ball, self.bx - BALL_R, self.by - BALL_R,
                 self.bx + BALL_R, self.by + BALL_R)
        c.itemconfig(self.hud, text=f"점수: {self.score}   목숨: {'♥' * self.lives}")

    def loop(self):
        self.update()
        self.root.after(16, self.loop)


if __name__ == "__main__":
    root = tk.Tk()
    Breakout(root)
    root.mainloop()
