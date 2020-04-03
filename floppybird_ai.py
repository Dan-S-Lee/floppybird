import random
import pygame
import pathlib
import neat
# from pipes import Pipes
from background import Background
import os
import numpy as np

pipe_image = pygame.image.load('images/pipe.png')
pipe_up = pipe_image
pipe_down = pygame.transform.flip(pipe_image, False, True)

'''
Global NEAT variables
'''


class Bird(pygame.sprite.Sprite):
    """player character bird class"""

    def __init__(self, screen):
        """constructor"""

        pygame.sprite.Sprite.__init__(self)
        self.screen = screen

        # Get background image and rect of screen and image
        floppy1_img_path = str(pathlib.Path('images/floppy.png').expanduser().resolve())
        self.image = pygame.transform.rotozoom(pygame.image.load(floppy1_img_path).convert_alpha(), 0, .55)
        floppy2_img_path = str(pathlib.Path('images/floppyup.png').expanduser().resolve())
        self.image_up = pygame.transform.rotozoom(pygame.image.load(floppy2_img_path).convert_alpha(), 0, .55)
        floppy3_img_path = str(pathlib.Path('images/floppydown.png').expanduser().resolve())
        self.image_down = pygame.transform.rotozoom(pygame.image.load(floppy3_img_path).convert_alpha(), 0, .55)
        self.rect = self.image.get_rect(topleft=(300, 100))
        # self.screen_rect = self.screen.get_rect()
        self.gravity = 4
        self.max_gravity = 10
        self.jump_height = 12

        self.score = 0

    def get_mask(self):
        return pygame.mask.from_surface(self.image)

    def get_top_mask(self):
        return pygame.mask.from_surface(self.image_up)

    def get_btm_mask(self):
        return pygame.mask.from_surface(self.image_down)

    def get_xy(self):
        return self.rect.left, self.rect.top

    def draw(self, screen):
        if self.gravity < 0:
            screen.blit(self.image_up, self.rect)
        elif self.gravity == 0:
            screen.blit(self.image, self.rect)
        elif self.gravity > 0:
            screen.blit(self.image_down, self.rect)

    def move(self):
        if self.gravity < self.max_gravity:
            self.gravity += 1
        elif self.gravity > self.max_gravity:
            self.gravity = self.max_gravity

        self.rect.top += self.gravity
        if self.rect.top <= 0:
            self.rect.top = 0

    def jump(self):
        self.gravity = -self.jump_height

class Pipes():
    GAP = 200

    def __init__(self, screen):
        super().__init__()
        self.screen = screen
        """Initialize attributes of the pipes"""
        self.top = 0
        self.bottom = 0
        self.height = 0
        self.x = screen.get_size()[0]
        self.PIPE_TOP = pipe_down
        self.PIPE_BTM = pipe_up
        self.top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        self.btm_mask = pygame.mask.from_surface(self.PIPE_BTM)

        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 500)
        self.top = self.height - self.PIPE_TOP.get_height()
        # print(self.top)
        # print(self.PIPE_TOP.get_height())
        self.bottom = self.height + self.GAP

    def draw(self, screen):
        """Draw pipe"""

        screen.blit(self.PIPE_TOP, (self.x, self.top))
        screen.blit(self.PIPE_BTM, (self.x, self.bottom))

    def move(self, speed):
        self.x -= speed

    def collide(self, bird, grav):
        if grav < 0:
            bird_mask = bird.get_top_mask()
        elif grav == 0:
            bird_mask = bird.get_mask()
        elif grav > 0:
            bird_mask = bird.get_btm_mask()

        # bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        btm_mask = pygame.mask.from_surface(self.PIPE_BTM)
        bird_x, bird_y = bird.get_xy()
        top_offset = (self.x - bird_x, self.top - round(bird_y))
        btm_offset = (self.x - bird_x, self.bottom - round(bird_y))
        b_point = bird_mask.overlap(btm_mask, btm_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)
        if b_point or t_point:
            return True
        return False


class FloppyBird:
    """main game class"""

    def __init__(self, genomes, networks, ge):
        """constructor"""
        pygame.init()

        self.screen_width = 1300
        self.screen_height = 700
        pygame.display.set_caption('FloppyBird')
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.delta_time = 0
        self.fps_limit = 60
        self.game_speed = 8

        self.run = True
        self.jump = False
        self.debug = False
        self.anglebool = True
        # intro BS
        self.intro = False
        self.button_height, self.button_width = 50, 250
        self.floppyfont = pygame.font.Font('freesansbold.ttf', 128)
        self.title = self.floppyfont.render('Floppy Bird', True, (255, 255, 0))
        self.title_rect = self.title.get_rect()
        self.title_rect.center = (self.screen_width // 2, 150)

        self.pipegroup = []

        self.clock = pygame.time.Clock()
        self.birds = []
        self.background = Background(self.screen, self.screen_width, self.game_speed)
        self.point_font = pygame.font.Font('freesansbold.ttf', 32)
        self.points = 0
        self.score = self.point_font.render(str(self.points), True, (0, 0, 0))
        self.score_rect = self.score.get_rect()
        self.score_rect.center = (self.screen_width // 2, 50)

        '''for AI'''
        self.nets = networks
        self.genomes = genomes
        self.ge = ge

        for _, g in self.genomes:
            self.birds.append(Bird(self.screen))

        # pygame.display.set_icon(pygame.image.load())
        self.flopdabird()

    def flopdabird(self):
        """Function which is responsible for running the game"""
        self.clock.tick(self.fps_limit)
        while self.intro:
            self.screen.fill((0, 0, 0))
            self.draw_introBS()
            pygame.display.flip()
            self.eventmanager()
        while self.run:
            self.update()
            self.draw()
            self.pipe_controls()
            self.eventmanager()
            self.movement()
            self.pointcalc()
            if not self.debug:
                self.collision()
            pygame.display.flip()
            self.delta_time = self.clock.tick(self.fps_limit) / 1000.0
            # print(self.delta_time)
        # pygame.quit()

    def draw_introBS(self):
        pygame.draw.rect(self.screen, (255, 0, 0), (
            (self.screen_width // 2) - (self.button_width // 2), (self.screen_height // 2) - (self.button_height // 2),
            self.button_width, self.button_height))
        self.screen.blit(self.title, self.title_rect)

    def eventmanager(self):
        """handles events"""
        space_pressed = False
        if not self.intro:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        space_pressed = True

            if space_pressed:
                for bird in self.birds:
                    bird.jump()
        elif self.intro:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                    self.intro = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.run = False
                        self.intro = False
                # if event.type == pygame.MOUSEBUTTONUP:
                #     if event.button == 1:
                #         if
        if space_pressed:
            for bird in self.birds:
                bird.jump()

    def update(self):
        self.background.update(self.delta_time)

    def pointcalc(self):

        for i, bird in enumerate(self.birds):
            if self.pipegroup[0].x == bird.rect.left:
                self.ge[i].fitness += 5
                bird.score += 1
        score_list = [bird.score for bird in self.birds]
        self.score = self.point_font.render(str(score_list and max(score_list)), True, (0, 0, 0))

    def collision(self):
        for pipe in self.pipegroup:
            for i, bird in enumerate(self.birds):
                if pipe.collide(bird, bird.gravity):
                    self.ge[i].fitness -= 1
                    self.birds.pop(i)
                    self.nets.pop(i)

                    print('collision triggered')
                    #FloppyBird()

    def movement(self):
        """movement logic"""
        pipe_ind = 0
        if len(self.birds) > 0:
            if len(self.pipegroup) > 0 and self.birds[0].rect.left > self.pipegroup[0].x + self.pipegroup[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            self.run = False
        for i, bird in enumerate(self.birds):
            bird.move()
            self.ge[i].fitness += 0.1
            bird_x, bird_y = bird.get_xy()
            output = self.nets[i].activate((np.log(bird_y),
                                            np.log(abs(bird_y - self.pipegroup[pipe_ind].height)),
                                            np.log(abs(bird_y - self.pipegroup[pipe_ind].bottom))))
            if output[0] > 0.5:
                bird.jump()
            # end game if bird hits ground
            if bird.rect.bottom >= self.screen_height:
                self.birds.pop(i)
                self.ge.pop(i)
                self.nets.pop(i)
            if bird.rect.top <= 0:
                self.birds.pop(i)
                self.ge.pop(i)
                self.nets.pop(i)


    def draw(self):
        """handles drawing"""

        self.background.blitme()
        for bird in self.birds:
            bird.draw(self.screen)

        if self.pipegroup:
            for pipe in self.pipegroup:
                pipe.draw(self.screen)
        self.screen.blit(self.score, self.score_rect)

    def getrandomcolor(self):
        """pick a color at random from the colors list"""

        colors = [
            (255, 0, 0),
            (255, 128, 0),
            (255, 255, 0),
            (128, 255, 0),
            (0, 255, 0),
            (0, 255, 128),
            (0, 255, 255),
            (0, 128, 255),
            (0, 0, 255),
            (128, 0, 255),
            (255, 0, 255),
            (255, 0, 128)
        ]
        return colors[random.randint(0, len(colors) - 1)]

    def pipe_controls(self):
        """create, remove, and move the pipes"""

        pipe_width = 105

        for pipe in self.pipegroup:
            pipe.move(self.game_speed)

        for pipe in self.pipegroup:
            if pipe.x <= -pipe_width:
                self.pipegroup.remove(pipe)

        if len(self.pipegroup) == 2:
            if self.pipegroup[1].x <= self.screen_width // 2:
                self.pipegroup.append(Pipes(self.screen))

        elif not self.pipegroup:
            # for adjusting pipes
            space = random.randint(200, 300)
            top_height = random.randint(50, self.screen_height - space)

            # no need to modify below
            color = self.getrandomcolor()
            x = self.screen_width
            bottom_y = top_height + space
            bottom_height = self.screen_height - top_height - space
            for i in range(0, 2):
                self.pipegroup.append(Pipes(self.screen))
                self.pipegroup[i].x = self.screen_width + i * (self.screen_width // 2)

def simulate(genomes, config):
    networks = []
    ge = []
    for _, genome in genomes:
        genome.fitness = 0
        network = neat.nn.FeedForwardNetwork.create(genome, config)
        networks.append(network)
        ge.append(genome)

    run = True
    FloppyBird(genomes, networks, ge)

def run_neat(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file)
    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(simulate, 50)
    print(winner)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run_neat(config_path)
    #FloppyBird()