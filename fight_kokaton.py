import os
import random
import sys
import time
import math
import pygame as pg

# 定数設定
WIDTH = 1100
HEIGHT = 650
NUM_OF_BOMBS = 5
GAME_TIME = 60  # 制限時間（秒）

os.chdir(os.path.dirname(os.path.abspath(__file__)))


# 画面外判定関数
def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内か外かを判定して返す
    戻り値：(横方向内か, 縦方向内か)
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


# こうかとんクラス
class Bird:
    """
    こうかとんに関するクラス
    """
    delta = {  # 押下キーと移動量の対応辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }

    # こうかとんの回転済み画像辞書
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
        self.rct = self.img.get_rect(center=xy)
        self.dire = (+5, 0)
        self.is_happy = False      # 喜び状態フラグ
        self.happy_timer = 0       # 喜び持続時間

    def change_img(self, num: int, screen: pg.Surface):
        """画像を指定番号に切り替える"""
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def set_happy(self, duration=20):
        """喜びエフェクトを一定時間発動"""
        self.is_happy = True
        self.happy_timer = duration
        self.img = pg.transform.rotozoom(pg.image.load("fig/6.png"), 0, 0.9)  # 喜び画像

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        こうかとんの位置・画像を更新して描画
        """
        sum_mv = [0, 0]
        for k, mv in Bird.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]

        # 位置更新
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])

        # 向き更新
        if sum_mv != [0, 0]:
            self.img = Bird.imgs[tuple(sum_mv)]
            self.dire = tuple(sum_mv)

        # 喜びエフェクト中ならタイマー減算
        if self.is_happy:
            self.happy_timer -= 1
            if self.happy_timer <= 0:
                self.is_happy = False
                # 通常向きに戻す
                self.img = Bird.imgs[self.dire]

        screen.blit(self.img, self.rct)

# ビームクラス
class Beam:
    """
    こうかとんが撃つビーム
    """
    def __init__(self, bird: Bird):
        self.img0 = pg.image.load("fig/beam.png")
        vx, vy = bird.dire
        self.vx, self.vy = vx, vy
        angle = math.degrees(math.atan2(-vy, vx))
        self.img = pg.transform.rotozoom(self.img0, angle, 1.0)
        self.rct = self.img.get_rect()
        self.rct.centerx = bird.rct.centerx + bird.rct.width * vx / 5
        self.rct.centery = bird.rct.centery + bird.rct.height * vy / 5

    def update(self, screen: pg.Surface):
        """ビームを移動・描画"""
        self.rct.move_ip(self.vx, self.vy)
        if check_bound(self.rct) == (True, True):
            screen.blit(self.img, self.rct)

# 爆弾クラス
class Bomb:
    """
    爆弾クラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect(center=(random.randint(0, WIDTH), random.randint(0, HEIGHT)))
        self.vx, self.vy = random.choice([-5, 5]), random.choice([-5, 5])

    def update(self, screen: pg.Surface):
        """爆弾の移動と跳ね返り"""
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)

# 爆発エフェクトクラス
class Explosion:
    """
    爆発エフェクト
    """
    def __init__(self, center: tuple[int, int]):
        self.imgs = [
            pg.image.load("fig/explosion.gif"),
            pg.transform.flip(pg.image.load("fig/explosion.gif"), True, True)
        ]
        self.img = self.imgs[0]
        self.rct = self.img.get_rect(center=center)
        self.life = 20  # 表示時間

    def update(self, screen: pg.Surface):
        """エフェクト描画（点滅交互）"""
        self.life -= 1
        self.img = self.imgs[self.life % 2]
        screen.blit(self.img, self.rct)

# スコア表示クラス
class Score:
    """
    スコア表示
    """
    def __init__(self):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.score = 0
        self.rct = pg.Rect(50, HEIGHT - 60, 200, 50)

    def add(self, amount=1):
        """スコアを加算"""
        self.score += amount

    def update(self, screen: pg.Surface):
        """スコアを描画"""
        img = self.font.render(f"Score: {self.score}", 0, self.color)
        screen.blit(img, self.rct)

# タイマー表示クラス
class Timer:
    """
    制限時間を管理・表示するクラス
    """
    def __init__(self, total_time: int):
        self.total_time = total_time
        self.start_ticks = pg.time.get_ticks()
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (255, 0, 0)
        self.rct = pg.Rect(WIDTH - 200, 50, 150, 50)
        self.stopped = False
        self.stop_time = None

    def stop(self):
        """タイマー停止"""
        if not self.stopped:
            self.stopped = True
            self.stop_time = pg.time.get_ticks()

    def update(self, screen: pg.Surface) -> bool:
        """
        残り時間を表示
        戻り値: True → 継続 / False → 時間切れ
        """
        if self.stopped:
            remaining = self.total_time - (self.stop_time - self.start_ticks) / 1000
        else:
            elapsed_ms = pg.time.get_ticks() - self.start_ticks
            remaining = self.total_time - elapsed_ms / 1000
        if remaining < 0:
            remaining = 0
        img = self.font.render(f"Time: {int(remaining)}", 0, self.color)
        screen.blit(img, self.rct)
        return remaining > 0


# 終了画面表示関数
def show_end_screen(screen, text, color=(255, 0, 0), score_val=0):
    """Game Over / Clear / Time Up の終了画面を表示"""
    font_big = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 80)
    font_small = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 50)
    txt1 = font_big.render(text, True, color)
    txt2 = font_small.render(f"Score: {score_val}", True, color)
    rect1 = txt1.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
    rect2 = txt2.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
    screen.blit(txt1, rect1)
    screen.blit(txt2, rect2)
    pg.display.update()
    time.sleep(2)


# メイン関数
def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    beams = []
    explosions = []
    score = Score()
    timer = Timer(GAME_TIME)
    clock = pg.time.Clock()

    while True:
        # イベント処理
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.append(Beam(bird))

        # 背景描画
        screen.blit(bg_img, [0, 0])

        # こうかとん,爆弾
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                bird.change_img(8, screen)
                pg.display.update()
                show_end_screen(screen, "GAME OVER", (255, 0, 0), score.score)
                return

        # ビーム,爆弾
        for beam in beams:
            for i, bomb in enumerate(bombs):
                if beam and bomb and beam.rct.colliderect(bomb.rct):
                    explosions.append(Explosion(bomb.rct.center))
                    beams[beams.index(beam)] = None
                    bombs[i] = None
                    score.add(1)
                    bird.set_happy(20)  # ←喜びエフェクト発動

        # リスト整理
        beams = [b for b in beams if b and check_bound(b.rct)[0]]
        bombs = [b for b in bombs if b]
        explosions = [e for e in explosions if e.life > 0]

        # 全爆弾破壊 → クリア
        if len(bombs) == 0:
            timer.stop()
            bird.set_happy(30)
            bird.update(pg.key.get_pressed(), screen)
            show_end_screen(screen, "GAME CLEAR!", (0, 255, 0), score.score)
            return

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

        # タイマー更新
        if not timer.update(screen):
            show_end_screen(screen, "TIME UP!", (255, 128, 0), score.score)
            return

        pg.display.update()
        clock.tick(50)

# 実行部
if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
