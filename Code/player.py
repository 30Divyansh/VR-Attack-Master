import pygame
import cv2
from cvzone.HandTrackingModule import HandDetector
import numpy as np
from laser import Laser

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, cwidth, speed, vwidth, screen, height):
        super().__init__()
        self.image0 = pygame.image.load('../Resources/player.png').convert_alpha()
        self.image = pygame.transform.scale(self.image0, (30 / 1, 15 / 1))
        self.rect = self.image.get_rect(midtop=pos)

        self.speed = speed
        self.max_x_constraint = cwidth + vwidth
        self.ready_to_shoot = True
        self.ready_to_flip = True
        self.laser_time = 0
        self.laser_cooldown = 300
        self.flip_time = 0
        self.flip_cooldown = 300

        self.lasers = pygame.sprite.Group()

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.detector = HandDetector(detectionCon=0.8, maxHands=1)
        self.vwidth = vwidth

        self.fingers = None
        self.img = None
        self.in_scope = False

        self.screen = screen
        self.flipped = False
        self.ww = cwidth + vwidth
        self.wh = height

        self.laser_sound = pygame.mixer.Sound('../Resources/laser.wav')
        self.laser_sound.set_volume(0.01)

        self.game_state = 0

    def constraint(self):
        if self.rect.left <= self.vwidth:
            self.rect.left = self.vwidth
        if self.rect.right >= self.max_x_constraint:
            self.rect.right = self.max_x_constraint

    def shoot_laser(self):
        if self.flipped:
            self.lasers.add(Laser(self.rect.center, 25, 700))
        else:
            self.lasers.add(Laser(self.rect.center, -25, self.rect.bottom))

    def flip(self):
        self.flipped = not self.flipped

    def read_fingers(self):
        _, img = self.cap.read()
        img = cv2.flip(img, 1)
        self.img = img

        hands = self.detector.findHands(img, draw=False, flipType=False)[0]
        if hands:
            hand = hands[0]
            if isinstance(hand, dict) and 'bbox' in hand:
                x, y, w, h = hand['bbox']
                x1 = x + w // 2
                x1 = np.clip(x1, 100, 1150)

                map = x1 - 100
                map = map * (self.max_x_constraint - self.vwidth)
                map = map // 1150
                self.rect.x = map + self.vwidth

                self.fingers = self.detector.fingersUp(hand)

                if self.fingers[1] == 1:
                    cv2.rectangle(img, (x - 20, y - 20), (x + w + 20, y + h + 20), (0, 0, 200), 10)
                    cv2.putText(img, 'SHOOT', (x - 30, y - 30), cv2.FONT_HERSHEY_PLAIN, 7, (0, 0, 200), 10)
                elif self.fingers == [0, 0, 0, 0, 1]:
                    cv2.rectangle(img, (x - 20, y - 20), (x + w + 20, y + h + 20), (0, 200, 0), 10)
                    cv2.putText(img, 'FLIP', (x - 30, y - 30), cv2.FONT_HERSHEY_PLAIN, 7, (0, 200, 0), 10)
                else:
                    cv2.rectangle(img, (x - 20, y - 20), (x + w + 20, y + h + 20), (200, 0, 0), 10)
                    cv2.putText(img, 'MOVE', (x - 30, y - 30), cv2.FONT_HERSHEY_PLAIN, 7, (200, 0, 0), 10)

                return True
        return False

    def get_input(self):
        if self.fingers and self.fingers[1] == 1 and self.ready_to_shoot:
            self.laser_sound.play()
            self.shoot_laser()
            self.ready_to_shoot = False
            self.laser_time = pygame.time.get_ticks()

        if self.fingers == [0, 0, 0, 0, 1] and self.ready_to_flip:
            self.flip()
            self.ready_to_flip = False
            self.flip_time = pygame.time.get_ticks()

    def recharge_shoot(self):
        if not self.ready_to_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_time >= self.laser_cooldown and (not self.fingers or self.fingers[1] != 1):
                self.ready_to_shoot = True

    def recharge_flip(self):
        if not self.ready_to_flip:
            current_time = pygame.time.get_ticks()
            if current_time - self.flip_time >= self.flip_cooldown and self.fingers != [0, 0, 0, 0, 1]:
                self.ready_to_flip = True

    def update(self):
        if self.read_fingers():
            self.in_scope = True

            if self.fingers[1] == 1:
                shoot1 = pygame.image.load("../Resources/shoot1.png").convert_alpha()
                shoot1 = pygame.transform.scale(shoot1, (330, 90))
                self.screen.blit(shoot1, (17, 305))
            elif self.fingers == [0, 0, 0, 0, 1]:
                if self.game_state == 0:
                    self.game_state = 1
                if self.game_state == 2 or self.game_state == 4:
                    self.game_state = 3
                flip1 = pygame.image.load("../Resources/flip1.png").convert_alpha()
                flip1 = pygame.transform.scale(flip1, (330, 90))
                self.screen.blit(flip1, (17, 400))
            else:
                move1 = pygame.image.load("../Resources/move1.png").convert_alpha()
                move1 = pygame.transform.scale(move1, (330, 90))
                self.screen.blit(move1, (17, 210))
        else:
            self.in_scope = False

        try:
            self.constraint()
            self.lasers.update()
            self.get_input()
        except Exception as e:
            print("Update Error:", e)

        self.recharge_flip()
        self.recharge_shoot()

        if self.flipped:
            self.screen.blit(pygame.transform.flip(self.image, False, True), self.rect)
        else:
            self.screen.blit(self.image, self.rect)

    def get_image(self):
        return self.img
