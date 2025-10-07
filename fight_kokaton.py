import os
import random
import sys
import time
import math
import pygame as pg


WIDTH = 1100
HEIGHT = 650
NUM_OF_BOMBS = 5
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    delta = {
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)
    imgs = {
        (+5, 0): img,
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),
        (-5, 0): img0,
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),
    }

    def __init__(self, xy: tuple[int, int]):
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)  # ★ 向きベクトル（初期値：右向き）★

    def change_img(self, num: int, screen: pg.Surface):
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
            self.dire = tuple(sum_mv)  # ★ 移動方向を記録 ★
        screen.blit(self.img, self.rct)


class Beam:
    def __init__(self, bird: "Bird"):
        self.img0 = pg.image.load("fig/beam.png")
        vx, vy = bird.dire  # ★ こうかとんの向きに応じた速度ベクトル ★
        self.vx, self.vy = vx, vy

        # ★ 向きに応じて画像を回転 ★
        angle = math.degrees(math.atan2(-vy, vx))
        self.img = pg.transform.rotozoom(self.img0, angle, 1.0)

        # ★ 初期位置（こうかとんの中心から少し前）★
        self.rct = self.img.get_rect()
        self.rct.centerx = bird.rct.centerx + bird.rct.width * vx / 5
        self.rct.centery = bird.rct.centery + bird.rct.height * vy / 5

    def update(self, screen: pg.Surface):
        self.rct.move_ip(self.vx, self.vy)
        if check_bound(self.rct) == (True, True):
            screen.blit(self.img, self.rct)


class Bomb:
    def __init__(self, color: tuple[int, int, int], rad: int):
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Explosion:
    def __init__(self, center: tuple[int, int]):
        self.imgs = [
            pg.image.load("fig/explosion.gif"),
            pg.transform.flip(pg.image.load("fig/explosion.gif"), True, True)
        ]
        self.img = self.imgs[0]
        self.rct = self.img.get_rect(center=center)
        self.life = 20

    def update(self, screen: pg.Surface):
        self.life -= 1
        self.img = self.imgs[self.life % 2]
        screen.blit(self.img, self.rct)


class Score:
    def __init__(self):
        self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.score = 0
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        self.rct = self.img.get_rect()
        self.rct.center = (100, HEIGHT - 50)

    def add_score(self, amount: int = 1):
        self.score += amount

    def update(self, screen: pg.Surface):
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.img, self.rct)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    beams = []
    explosions = []
    score = Score()
    clock = pg.time.Clock()

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.append(Beam(bird))

        screen.blit(bg_img, [0, 0])

        # 衝突判定（こうかとん vs 爆弾）
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                bird.change_img(8, screen)
                pg.display.update()
                time.sleep(1)
                return

        # 衝突判定（ビーム vs 爆弾）
        for beam in beams:
            for i, bomb in enumerate(bombs):
                if beam is not None and bomb is not None:
                    if beam.rct.colliderect(bomb.rct):
                        explosions.append(Explosion(bomb.rct.center))
                        beams[beams.index(beam)] = None
                        bombs[i] = None
                        score.add_score(1)

        # リスト整理
        beams = [b for b in beams if b is not None and check_bound(b.rct)[0]]
        bombs = [b for b in bombs if b is not None]
        explosions = [ex for ex in explosions if ex.life > 0]

        # 更新処理
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        for beam in beams:
            beam.update(screen)
        for bomb in bombs:
            bomb.update(screen)
        for ex in explosions:
            ex.update(screen)
        score.update(screen)

        pg.display.update()
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
