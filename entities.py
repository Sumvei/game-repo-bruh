from math import pi, sin, cos, atan, ceil, atan2, floor, radians, sqrt
from random import random, randint

import pygame

from items import *
from main import FPS, BACKGROUND


class Entity:  # Used to create and control entities
    def __init__(self, screen, pos, color=pygame.Color('white'), size=(10, 10), velocity=30, hp=100):  # Init
        self.screen = screen
        self.x = pos[0]
        self.y = pos[1]
        self.w, self.h = size
        self.size = size
        self.hp = hp
        self.color = color
        self.hitbox = pygame.rect.Rect([round(self.x) - self.w // 2, round(self.y) - self.h // 2,
                                        self.w, self.h])
        self.velocity = velocity
        self.attack_speed = 1
        self.look_angle = 0
        self.weapon = Weapon('bruher', 30, attack_speed=50, attack_range=50, attack_width=30)
        self.target = None
        self.timers = {'sleep_timer': Timer(100),
                       'base_attack_time': Timer(10000 // (self.attack_speed + self.weapon.attack_speed) // 10,
                                                 target=self.attack, args=(self.target,)),
                       'attack_time': Timer(10000 // (self.attack_speed + self.weapon.attack_speed),
                                            target=self.attack, args=(self.target,)),
                       'clear_attack': Timer(10, target=self.clear_attack_animation)}

    def attack(self, target):
        if self.x <= target.x:
            d = 0
        else:
            d = 1
        attack_box = pygame.rect.Rect(
            [self.x - d * self.weapon.attack_range, self.y - self.weapon.attack_width, self.weapon.attack_range,
             2 * self.weapon.attack_width])
        pygame.draw.rect(self.screen, pygame.Color('grey'), attack_box)
        self.timers['clear_attack'].args = (attack_box, d)
        self.timers['clear_attack'].start()
        if type(target) != list and type(target) != tuple:
            if attack_box.colliderect(target.hitbox):
                target.hurt(self.weapon.damage)
        else:
            for t in target:
                if attack_box.colliderect(t.hitbox):
                    t.hurt(self.weapon.damage)

    def try_to_attack(self):
        if type(self.target) is Player and self.target.invul:
            return
        if self.x <= self.target.x:
            d = 0
        else:
            d = 1
        attack_box = pygame.rect.Rect(
            [self.x - d * self.weapon.attack_range, self.y - self.weapon.attack_width, self.weapon.attack_range,
             2 * self.weapon.attack_width])
        if attack_box.colliderect(self.target.hitbox):
            if not self.timers['base_attack_time'].is_started():
                self.timers['base_attack_time'].args = (self.target,)
                self.timers['base_attack_time'].start(10000 // (self.attack_speed + self.weapon.attack_speed) // 10)
    
    def clear_attack_animation(self, attack_box, d):
        x, y = attack_box.x, attack_box.y
        self.screen.blit(BACKGROUND, (x, y),
                         (x, y, self.weapon.attack_range,
                          2 * self.weapon.attack_width))
    
    def clear_prev(self):  # Clears previous position sprite
        d = ceil(self.velocity / FPS) + 1
        self.screen.blit(BACKGROUND, (self.x - d - self.w // 2, self.y - d - self.h // 2),
                         (self.x - d - self.w // 2, self.y - d - self.h // 2,
                          self.w + d * 2, self.h + d * 2))

    def collision(self, other):  # Checks for collision with point / entity / entity list
        if type(other) == tuple:
            return self.hitbox.collidepoint(*other)
        if type(other) == Entity:
            return self.hitbox.colliderect(other.hitbox)
        if type(other) == list and len(other) > 1:
            return self.hitbox.collidelist(other.hitbox)

    def distance(self, pos):  # Returns distance between self and pos
        return sqrt((self.x - pos[0]) * (self.x - pos[0]) + (self.y - pos[1]) * (self.y - pos[1]))

    def get_hp(self):  # Returns self health points
        return self.hp

    def get_pos(self):  # Returns self pos
        return self.x, self.y

    def get_velocity(self):  # Returns self velocity
        return self.velocity

    def get_x(self):  # Returns self x
        return self.x

    def get_y(self):  # Returns self y
        return self.y

    def get_width(self):  # Returns self width
        return self.w

    def get_height(self):  # Returns self height
        return self.h

    def get_size(self):  # Returns self size (width, height)
        return self.w, self.h

    def draw(self):  # Draws self on self.screen
        self.clear_prev()
        self.update_hitbox()
        pygame.draw.rect(self.screen, self.color, self.hitbox)

    def is_sleep(self):  # Returns True if self is sleeping
        return self.timers['sleep_timer'].is_started()

    def move(self, dx, dy, entities=(), force_move=False):  # Changes self x, y to dx, dy
        x1, y1 = self.get_pos()
        velocity = self.get_velocity()

        x2 = x1 + dx * velocity / FPS
        y2 = y1 + dy * velocity / FPS
        if type(self) is Player:
            if dx > 0:
                self.look_angle = 0
            elif dx < 0:
                self.look_angle = 180
        if not force_move:
            if not (self.w // 2 <= x2 + self.w // 2 <= self.screen.get_width()
                    and self.h // 2 <= y2 + self.h // 2 <= self.screen.get_height()):
                return False
            for entity in entities:
                if entity is not self and not entity.is_sleep():
                    if self.collision(entity):
                        return False

        self.x = x2
        self.y = y2
        self.draw()
        return True

    def kill(self):  # Kills self
        self.hp = 0

    def hurt(self, damage):  # Gets damaged
        self.hp = max(0, self.hp - damage)
        if self.hp == 0:
            if self.x <= self.target.x:
                d = 0
            else:
                d = 1
            attack_box = pygame.rect.Rect(
                [self.x - d * self.weapon.attack_range, self.y - self.weapon.attack_width, self.weapon.attack_range,
                 2 * self.weapon.attack_width])
            self.clear_attack_animation(attack_box, d)
            self.kill()

    def move_to(self, pos, entities=(), force_move=False):  # Tries to move self to pos
        dx, dy = 0, 0
        if self.y != pos[1]:
            if abs(self.y - pos[1]) < self.velocity / FPS + 1:
                self.y = pos[1]
                dx = 1 if self.x - pos[0] < 0 else -1
                dy = 0
            else:
                angle = pi / 2 - atan((self.x - pos[0]) / (self.y - pos[1]))
                dx = cos(angle)
                dy = sin(angle)
                if self.y > pos[1]:
                    dy *= -1
                    dx *= -1
        elif self.x != pos[0]:
            if abs(self.x - pos[0]) < self.velocity / FPS + 1:
                self.x = pos[0]
                dx = 0
            else:
                dx = 1 if self.x - pos[0] < 0 else -1
        self.move(dx, 0, entities, force_move)
        self.move(0, dy, entities, force_move)

    def update(self):  # Updates self
        self.update_hitbox()
        self.draw()

    def update_hitbox(self):  # Updates self hitbox
        self.hitbox = pygame.rect.Rect([round(self.x) - self.w // 2, round(self.y) - self.h // 2,
                                        self.w, self.h])

    def set_attribute(self, attribute, value):
        assert hasattr(self, attribute), f'{self.__class__} has no attribute named {attribute}'
        setattr(self, attribute, value)

    def get_attribute(self, attribute=None):
        if attribute is not None:
            assert hasattr(self, attribute), f'{self.__class__} has no attribute named {attribute}'
            return getattr(self, attribute)
        else:
            return [(attr, self.get_attribute(attr)) for attr in self.__dict__]


class Player(Entity):  # Player class
    def __init__(self, screen, pos, color=pygame.Color('white'), size=(20, 20), velocity=300):
        super().__init__(screen, pos, color, size, velocity)
        self.timers['invul_frames'] = Timer(40, target=self.invul)
        self.invul = False
        self.attack_angle = 0

    def attack(self, target):
        if self.attack_angle == 0:
            d = 0
        else:
            d = 1
        attack_box = pygame.rect.Rect(
            [self.x - d * self.weapon.attack_range, self.y - self.weapon.attack_width, self.weapon.attack_range,
             2 * self.weapon.attack_width])
        pygame.draw.rect(self.screen, pygame.Color('grey'), attack_box)
        self.timers['clear_attack'].args = (attack_box, d)
        self.timers['clear_attack'].start()
        if type(target) != list and type(target) != tuple:
            if attack_box.colliderect(target.hitbox):
                target.hurt(self.weapon.damage)
        else:
            for t in target:
                if attack_box.colliderect(t.hitbox):
                    t.hurt(self.weapon.damage)

    def start_attacking(self, enemies):
        if not self.timers['base_attack_time'].is_started():
            self.timers['base_attack_time'].args = (enemies, )
            self.timers['base_attack_time'].start(10000 // (self.attack_speed + self.weapon.attack_speed) // 10)
    
    def hurt(self, damage):  # Gets damaged
        self.hp = max(0, self.hp - damage)
        self.invul = True
        self.timers['invul_frames'].start()

    def update(self):
        for timer in self.timers.values():
            if timer.is_started():
                timer.tick()

    def invul(self):
        self.invul = False


class Enemy(Entity):  # Enemy class
    def __init__(self, screen, pos, color=pygame.Color('white'), size=(20, 20), velocity=30, hp=100, player=None,
                 team=1):
        super().__init__(screen, pos, color, size, velocity, hp)
        self.player = player
        self.fov = 60
        self.view_range = 150
        self.team = team
        self.target = self.player
        self.attacking = False
        self.timers['player_near'] = Timer(100, self.aggro)

    def aggro(self):
        self.color = pygame.Color('red')
        self.attacking = True

    def check_for_player(self):  # Checks for player in self line-of-sight
        if self.attacking:
            return
        if self.distance(self.player.get_pos()) <= 50:
            if not self.timers['player_near'].is_started():
                self.timers['player_near'].start()
        else:
            self.timers['player_near'].stop()
            self.timers['player_near'].reset()
        if (self.target.get_x() - self.x) * (self.target.get_x() - self.x) + (self.target.get_y() - self.y) * (
                self.target.get_y() - self.y) <= self.view_range * self.view_range:
            dist_orient = atan2(-(self.target.get_x() - self.x), self.target.get_y() - self.y) * (180 / pi)
            ang_dist = dist_orient - (self.look_angle - 90) % 360
            ang_dist = ang_dist - 360 * floor((ang_dist + 180) * (1 / 360))
            if abs(ang_dist) <= self.fov:
                self.aggro()

    def rotate(self, angle):  # Rotates self
        self.look_angle = (self.look_angle + angle) % 360

    def move_forward(self):  # Moves self toward looking direction
        dx = cos(radians(self.look_angle))
        dy = sin(radians(self.look_angle))
        moved = self.move(dx, dy)
        if not moved:
            self.rotate(180)

    def move_to_target(self):  # Moves self toward target
        self.move_to(self.target.get_pos())

    def update(self):  # Updates self
        for timer in self.timers.values():
            if timer.is_started():
                timer.tick()

        if not self.is_sleep():
            if self.attacking:
                if self.get_pos() != self.target.get_pos():
                    self.move_to_target()
                    self.try_to_attack()
            else:
                r = random()
                if r > 0.999:
                    angle = randint(-90, 90)
                    self.rotate(angle)
                self.move_forward()
                self.check_for_player()

        self.draw()

    def sleep(self, time=100):  # Sleeps for given time
        self.timers['sleep_timer'].start(time)

    def hurt(self, damage):  # Gets damaged
        self.aggro()
        self.hp = max(0, self.hp - damage)
        if self.hp == 0:
            self.kill()


class Timer:  # Timer class
    def __init__(self, time, target=None, args=tuple(), mode=0):
        self.default_time = time
        self.time = time
        self.started = False
        self.mode = mode
        self.target = target
        self.args = args

    def get_time(self):
        return self.time

    def tick(self, time=1):
        if self.time > 0:
            self.time -= time
        else:
            if self.mode == 0:
                self.stop()
            if self.args:
                self.target(*self.args)
            else:
                self.target()
            self.reset()
            return True

    def reset(self):
        self.time = self.default_time

    def start(self, time=0):
        self.started = True
        if time != 0:
            self.time = time

    def stop(self):
        self.started = False

    def is_started(self):
        return self.started
