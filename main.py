import sys
import math
import random
import numpy as np
import time
from PIL import Image
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# Constantes para menus
LIGHT_ON = 0
LIGHT_OFF = 1
CAMERA_FIRST_PERSON = 0
CAMERA_FIXED_1 = 1
CAMERA_FIXED_2 = 2

# Variáveis globais
window_width = 800
window_height = 600
start_time = time.time()
game_over = False
final_time = 0
tempo_antes_pausa = 0

# Câmeras
current_camera = CAMERA_FIXED_1  # Inicializar com uma câmera fixa para facilitar testes
cameras = {
    CAMERA_FIRST_PERSON: {'eye': [0, 2, 50], 'center': [0, 2, 0], 'up': [0, 1, 0]},
    CAMERA_FIXED_1: {'eye': [100, 70, 100], 'center': [0, 0, 0], 'up': [0, 1, 0]},
    CAMERA_FIXED_2: {'eye': [-100, 70, 100], 'center': [0, 0, 0], 'up': [0, 1, 0]},
}

# Iluminação
light_enabled = True

# Lista de planetas
planets = []

# Lista de luas
moons = []  # Nova lista para luas

# Variáveis para colisão
collision_detected = False
collided_planet = None

# Texturas
background_texture_id = None
sun_texture_id = None
saturn_ring_texture_id = None

# Variável para pausar o jogo
paused = False  # Nova variável para controlar pausa

# Classe para representar cada planeta
class Planet:
    def __init__(self, name, color, size, distance, orbit_speed, rotation_speed, texture_file, info, parent=None):
        """
        :param name: Nome do planeta
        :param color: Cor do planeta [r, g, b]
        :param size: Tamanho do planeta (raio)
        :param distance: Distância do Sol ou do planeta pai (escala ajustada)
        :param orbit_speed: Velocidade de órbita (graus por frame)
        :param rotation_speed: Velocidade de rotação (graus por frame)
        :param texture_file: Caminho para a textura do planeta
        :param info: Informações sobre o planeta
        :param parent: Planeta ao qual este planeta está orbitando (para luas)
        """
        self.name = name
        self.color = color
        self.size = size
        self.distance = distance
        self.orbit_speed = orbit_speed
        self.rotation_speed = rotation_speed
        self.texture_file = texture_file
        self.info = info
        self.orbit_angle = random.uniform(0, 360)  # Ângulo inicial aleatório
        self.rotation_angle = random.uniform(0, 360)  # Ângulo de rotação inicial aleatório
        self.texture_id = self.load_texture()
        self.parent = parent  # Planeta pai

    def load_texture(self):
        try:
            image = Image.open(self.texture_file)
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
            img_mode = image.mode
            if img_mode == "RGBA":
                img_data = image.convert("RGBA").tobytes()
                format = GL_RGBA
            else:
                img_data = image.convert("RGB").tobytes()
                format = GL_RGB
            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            gluBuild2DMipmaps(GL_TEXTURE_2D, format, image.width, image.height, format, GL_UNSIGNED_BYTE, img_data)
            return texture_id
        except Exception as e:
            print(f"Erro ao carregar textura para {self.name}: {e}")
            return None

    def update(self):
        # Atualizar ângulo de órbita
        self.orbit_angle += self.orbit_speed
        if self.orbit_angle >= 360:
            self.orbit_angle -= 360

        # Atualizar ângulo de rotação
        self.rotation_angle += self.rotation_speed
        if self.rotation_angle >= 360:
            self.rotation_angle -= 360

    def get_position(self):
        if self.parent:
            # Obter a posição do planeta pai
            parent_pos = np.array(self.parent.get_position())
            rad = math.radians(self.orbit_angle)
            x = parent_pos[0] + self.distance * math.cos(rad)
            z = parent_pos[2] + self.distance * math.sin(rad)
            y = parent_pos[1]  # Manter a mesma altura que o planeta pai
            return [x, y, z]
        else:
            # Calcular posição baseada no ângulo de órbita em relação ao Sol
            rad = math.radians(self.orbit_angle)
            x = self.distance * math.cos(rad)
            z = self.distance * math.sin(rad)
            return [x, self.size, z]

    def draw(self):
        glPushMatrix()
        pos = self.get_position()
        glTranslatef(*pos)
        glRotatef(self.rotation_angle, 0, 1, 0)
        if self.texture_id:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            glColor3f(1.0, 1.0, 1.0)  # Resetar a cor para branco antes de aplicar a textura
        else:
            glColor3f(*self.color)
        quad = gluNewQuadric()
        if self.texture_id:
            gluQuadricTexture(quad, GL_TRUE)
            gluQuadricNormals(quad, GLU_SMOOTH)
        else:
            gluQuadricNormals(quad, GLU_SMOOTH)
        gluSphere(quad, self.size, 50, 50)
        gluDeleteQuadric(quad)
        if self.texture_id:
            glDisable(GL_TEXTURE_2D)
        glPopMatrix()

# Classe para representar os anéis de um planeta (especificamente Saturno)
class Ring:
    def __init__(self, planet, texture_file, inner_radius, outer_radius, rotation_speed=0):
        """
        :param planet: Instância da classe Planet à qual os anéis estão associados
        :param texture_file: Caminho para a textura dos anéis
        :param inner_radius: Raio interno dos anéis
        :param outer_radius: Raio externo dos anéis
        :param rotation_speed: Velocidade de rotação dos anéis (graus por frame)
        """
        self.planet = planet
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.rotation_speed = rotation_speed
        self.rotation_angle = random.uniform(0, 360)
        self.texture_file = texture_file
        self.texture_id = self.load_texture()

    def load_texture(self):
        try:
            image = Image.open(self.texture_file)
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
            img_mode = image.mode
            if img_mode == "RGBA":
                img_data = image.convert("RGBA").tobytes()
                format = GL_RGBA
            else:
                img_data = image.convert("RGB").tobytes()
                format = GL_RGB
            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            gluBuild2DMipmaps(GL_TEXTURE_2D, format, image.width, image.height, format, GL_UNSIGNED_BYTE, img_data)
            return texture_id
        except Exception as e:
            print(f"Erro ao carregar textura dos anéis para {self.planet.name}: {e}")
            return None

    def update(self):
        # Atualizar ângulo de rotação
        self.rotation_angle += self.rotation_speed
        if self.rotation_angle >= 360:
            self.rotation_angle -= 360

    def draw(self):
        if self.texture_id is None:
            return  # Não há textura para os anéis

        glPushMatrix()
        pos = self.planet.get_position()
        glTranslatef(*pos)
        glRotatef(self.planet.rotation_angle, 0, 1, 0)  # Alinhar com a rotação do planeta
        glRotatef(self.rotation_angle, 0, 0, 1)  # Rotação adicional dos anéis

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(1.0, 1.0, 1.0, 0.8)  # Ajustar a transparência conforme necessário

        num_segments = 100
        theta = 0
        delta_theta = 2 * math.pi / num_segments

        glBegin(GL_TRIANGLE_STRIP)
        for i in range(num_segments + 1):
            theta = i * delta_theta
            x_inner = self.inner_radius * math.cos(theta)
            z_inner = self.inner_radius * math.sin(theta)
            x_outer = self.outer_radius * math.cos(theta)
            z_outer = self.outer_radius * math.sin(theta)
            glTexCoord2f(i / num_segments, 0)
            glVertex3f(x_inner, 0, z_inner)
            glTexCoord2f(i / num_segments, 1)
            glVertex3f(x_outer, 0, z_outer)
        glEnd()

        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)
        glPopMatrix()

# Classe para representar o jogador
class Player:
    def __init__(self, position):
        self.position = np.array(position, dtype='float64')  # [x, y, z]
        self.yaw = 0    # Rotação em torno do eixo Y (em graus)
        self.size = 1.5
        self.planetas_coletados = []
        self.flame_animation_time = 0  # Tempo para animação das chamas
        self.is_moving = False        # Nova variável para controlar se está se movendo

    def draw_rocket(self):
        glPushMatrix()
        glTranslatef(*self.position)
        glRotatef(self.yaw, 0, 1, 0)   # Rotação em Y (Yaw)

        # Corpo do foguete
        glColor3f(0.439, 0.502, 0.565)  # Cor principal do corpo
        glutSolidCylinder(0.5, 2, 20, 20)  # Cilindro que compõe o corpo

        # Chápeu do foguete (cone)
        glPushMatrix()
        glTranslatef(0, 0, -0.001)  # Ajustando o cone
        glRotatef(180, 1, 0, 0)     # Ajustando orientação
        glColor3f(0.698, 0.133, 0.133)
        glutSolidCone(0.5, 1, 20, 20)
        glPopMatrix()

        # Parte inferior do foguete
        glPushMatrix()
        glTranslatef(0, 0, 2.1)
        glRotatef(-180, 1.0, 0.0, 0.0)
        glRotatef(-45, 0.0, 0.0, 1.0)
        glColor3f(0.098, 0.098, 0.439)
        glutSolidCone(0.6, 0.75, 32, 32)
        glPopMatrix()

        # Asa direita
        glPushMatrix()
        glTranslatef(.4, 0, 1.7)  # Posição
        glRotatef(180, 1, 0, 0)   # Ajustando orientação
        glColor3f(0.698, 0.133, 0.133)
        glutSolidCone(0.4, 1.0, 4, 4)
        glPopMatrix()

        # Asa esquerda
        glPushMatrix()
        glTranslatef(-.4, 0, 1.7)  # Posição
        glRotatef(180, 1, 0, 0)    # Ajustando orientação
        glColor3f(0.698, 0.133, 0.133)
        glutSolidCone(0.4, 1.0, 4, 4)
        glPopMatrix()

        # Janela
        glPushMatrix()
        glTranslatef(0, .5, .5)
        glRotatef(90, 1.0, 0.0, 0.0)
        glColor3f(0.098, 0.098, 0.439)
        glutSolidCone(.3, .1, 32, 32)
        glPopMatrix()

        # Desenhar as chamas somente se estiver se movendo
        if self.is_moving:
            self.draw_flames()

        glPopMatrix()

    def draw_flames(self):
        # Atualizar tempo de animação
        self.flame_animation_time += 0.05
        flame_scale = 1.0 + 0.1 * math.sin(self.flame_animation_time)
        flame_position_offset = 0.2 * math.sin(self.flame_animation_time * 2)

        glPushMatrix()
        # Posicionar as chamas na base do foguete
        glTranslatef(0, 0, 2.1 + flame_position_offset)
        glRotatef(-180, 1.0, 0.0, 0.0)  # Ajustar orientação para apontar para baixo

        # Configurar blending para transparência
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Configurar cor das chamas com transparência
        glColor4f(1.0, 0.5, 0.0, 0.8)  # Laranja com 80% de opacidade

        # Desenhar as chamas como cones
        glPushMatrix()
        glScalef(flame_scale, flame_scale, flame_scale)
        glutSolidCone(0.5, 1.0, 20, 20)
        glPopMatrix()

        # Opcional: adicionar múltiplas camadas de chamas para maior realismo
        glPushMatrix()
        glScalef(flame_scale * 0.8, flame_scale * 0.8, flame_scale * 0.8)
        glColor4f(1.0, 0.7, 0.0, 0.6)  # Amarelo com 60% de opacidade
        glutSolidCone(0.4, 1.0, 20, 20)
        glPopMatrix()

        glDisable(GL_BLEND)
        glPopMatrix()

    """
    def move_forward(self, distance):
        # Calcula o deslocamento baseado em yaw
        rad_yaw = math.radians(self.yaw)

        # Componentes de movimento
        dx = distance * math.sin(rad_yaw)
        dz = -distance * math.cos(rad_yaw)
        dy = 0  # Sem movimentação vertical

        self.position += np.array([dx, dy, dz])
        self.is_moving = True  # Ativa o estado de movimento
        print(f"Movendo para frente: posição atual {self.position}")
    """

    def move_player(self, forward, right):
        rad = math.radians(player.yaw)
        move_vector = np.array([right * math.cos(rad) + forward * math.sin(rad),
                            0,
                            right * math.sin(rad) - forward * math.cos(rad)])
        self.position += move_vector * 1.0  # Adjust speed as needed
        self.is_moving = True

    def rotate_right(self, angle):
        self.yaw -= angle
        if self.yaw < 0:
            self.yaw += 360

    def rotate_left(self, angle):
        self.yaw += angle
        if self.yaw >= 360:
            self.yaw -= 360

    def check_collision(self, celestial_bodies):
        global collision_detected, collided_planet, game_over

        # Check for collision with the Sun
        sun_position = np.array([0, 0, 0])  # Assuming Sun is at origin
        distance_to_sun = np.linalg.norm(self.position - sun_position)
        
        if distance_to_sun < self.size + 5:  # Aumentado o tamanho do Sol para 5
            game_over = True
            end_game()  # End the game instantly
            return  # Exit the function to avoid further checks

        for body in celestial_bodies:
            if body.name in self.planetas_coletados:
                continue

            body_pos = np.array(body.get_position())
            distance = np.linalg.norm(self.position - body_pos)

            if distance < self.size + body.size:
                collision_detected = True
                collided_planet = body
                self.planetas_coletados.append(body.name)
                if len(self.planetas_coletados) == len(planets):
                    end_game()
                break

# Instância do jogador
player = Player([0, 2, 50])  # Posição inicial ajustada para uma visualização melhor

# Lista de anéis (especificamente para Saturno)
rings = []

# Inicialização da cena
def init_scene():
    global planets, moons, background_texture_id, sun_texture_id, saturn_ring_texture_id, rings
    # Definir luzes
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)  # Luz do Sol
    glEnable(GL_LIGHT1)  # Luz adicional (foguete)

    # Luz do Sol
    glLightfv(GL_LIGHT0, GL_POSITION, [0, 0, 0, 1])  # Luz fixa no Sol
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1])  # Luz difusa
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1])   # Luz ambiente
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1])  # Luz especular

    # Luz do foguete (Camera First Person)
    glLightfv(GL_LIGHT1, GL_DIFFUSE, [1.0, 0.2, 0.2, 1])  # Luz difusa
    glLightfv(GL_LIGHT1, GL_AMBIENT, [0.4, 0.1, 0.1, 1])  # Luz ambiente
    glLightfv(GL_LIGHT1, GL_SPECULAR, [0.5, 0.1, 0.1, 1]) # Luz especular

    # Habilitar cor material
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    # Habilitar mapeamento de textura
    glEnable(GL_TEXTURE_2D)

    # Carregar Textura de Background
    try:
        image = Image.open("textures/milky_way.jpg")  # Certifique-se de que o arquivo esteja no diretório correto
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        img_mode = image.mode
        if img_mode == "RGBA":
            img_data = image.convert("RGBA").tobytes()
            format = GL_RGBA
        else:
            img_data = image.convert("RGB").tobytes()
            format = GL_RGB
        background_texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, background_texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, format, image.width, image.height,
                     0, format, GL_UNSIGNED_BYTE, img_data)
    except Exception as e:
        print(f"Erro ao carregar textura de fundo: {e}")
        background_texture_id = None

    # Carregar Textura do Sol
    try:
        image = Image.open("textures/sun.jpg")  # Certifique-se de que o arquivo esteja no diretório correto
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        img_mode = image.mode
        if img_mode == "RGBA":
            img_data = image.convert("RGBA").tobytes()
            format = GL_RGBA
        else:
            img_data = image.convert("RGB").tobytes()
            format = GL_RGB
        sun_texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, sun_texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        gluBuild2DMipmaps(GL_TEXTURE_2D, format, image.width, image.height, format, GL_UNSIGNED_BYTE, img_data)
    except Exception as e:
        print(f"Erro ao carregar textura do Sol: {e}")
        sun_texture_id = None

    # Carregar Textura dos Anéis de Saturno
    try:
        image = Image.open("textures/saturn_ring.png")  # Certifique-se de que o arquivo esteja no diretório correto
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        img_mode = image.mode
        if img_mode == "RGBA":
            img_data = image.convert("RGBA").tobytes()
            format = GL_RGBA
        else:
            img_data = image.convert("RGB").tobytes()
            format = GL_RGB
        saturn_ring_texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, saturn_ring_texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        gluBuild2DMipmaps(GL_TEXTURE_2D, format, image.width, image.height, format, GL_UNSIGNED_BYTE, img_data)
    except Exception as e:
        print(f"Erro ao carregar textura dos anéis de Saturno: {e}")
        saturn_ring_texture_id = None

    # Criar planetas com descrições detalhadas (sem tópicos)
    # Parâmetros: nome, cor, tamanho, distância do Sol, velocidade de órbita, velocidade de rotação, arquivo de textura, informações
    # Aumentando os tamanhos dos planetas multiplicando por 1.5
    planets.append(Planet(
        name="Mercúrio",
        color=[0.75, 0.75, 0.75],
        size=0.75,  # Aumentado de 0.5 para 0.75
        distance=10,
        orbit_speed=0.5,
        rotation_speed=2,
        texture_file="textures/mercury.jpg",
        info="""
Mercúrio é o planeta mais próximo do Sol, com uma órbita que completa em cerca de 88 dias terrestres. Seu tamanho é menor que o da Terra, com um diâmetro de aproximadamente 4.880 km. Possui uma atmosfera extremamente tênue composta principalmente de oxigênio, sódio, hidrogênio, hélio e potássio. A superfície é coberta por crateras, semelhantes à da Lua, devido à falta de uma atmosfera significativa que possa proteger contra impactos de meteoros. Missões como a MESSENGER e a BepiColombo da ESA têm estudado Mercúrio para entender melhor sua composição e histórico geológico.
"""
    ))
    planets.append(Planet(
        name="Vênus",
        color=[1.5, 0.75, 0.0],  # Aumentado para refletir tamanho maior
        size=1.35,  # Aumentado de 0.9 para 1.35
        distance=15,
        orbit_speed=0.3,
        rotation_speed=1.8,
        texture_file="textures/venus.jpg",
        info="""
Vênus é o segundo planeta do Sol e possui um diâmetro semelhante ao da Terra, com cerca de 12.104 km. É conhecido por sua densidade e composição rochosa. A atmosfera é composta predominantemente de dióxido de carbono (CO2) com nuvens de ácido sulfúrico, criando um efeito estufa extremo que eleva a temperatura de superfície a cerca de 467°C. Vênus possui uma rotação retrógrada, girando no sentido oposto ao da maioria dos planetas, completando uma rotação em aproximadamente 243 dias terrestres. Missões como a Venera da Rússia e a Akatsuki da JAXA têm estudado a atmosfera densa e as condições superficiais de Vênus.
"""
    ))
    terra = Planet(
        name="Terra",
        color=[0.0, 0.0, 1.5],  # Aumentado para refletir tamanho maior
        size=1.5,  # Aumentado de 1.0 para 1.5
        distance=20,
        orbit_speed=0.2,
        rotation_speed=1.5,
        texture_file="textures/earth.jpg",
        info="""
A Terra é o terceiro planeta do Sol e o único conhecido por abrigar vida. Possui um diâmetro de aproximadamente 12.742 km e uma massa que permite a existência de uma atmosfera estável. A atmosfera terrestre é composta principalmente de nitrogênio (78%) e oxigênio (21%), com traços de argônio, dióxido de carbono e outros gases. É essencial para a vida, protegendo contra radiações nocivas e regulando a temperatura. Cerca de 71% da superfície da Terra é coberta por água, incluindo oceanos, rios, lagos e gelo polar. A água é vital para todos os seres vivos e desempenha um papel crucial no clima e na geologia do planeta. A Terra é o ponto de partida para todas as missões espaciais humanas, incluindo a Estação Espacial Internacional (ISS), e futuras explorações para a Lua, Marte e além.
"""
    )
    planets.append(terra)
    planets.append(Planet(
        name="Marte",
        color=[1.5, 0.0, 0.0],  # Aumentado para refletir tamanho maior
        size=1.05,  # Aumentado de 0.7 para 1.05
        distance=25,
        orbit_speed=0.15,
        rotation_speed=1.2,
        texture_file="textures/mars.jpg",
        info="""
Marte é o quarto planeta do Sol, conhecido como o Planeta Vermelho devido à presença de óxido de ferro em sua superfície. Possui um diâmetro de aproximadamente 6.779 km. A atmosfera marciana é composta principalmente de dióxido de carbono (95,3%), com pequenas quantidades de nitrogênio e argônio. É extremamente fina em comparação com a da Terra. Marte apresenta uma variedade de características geológicas, incluindo vulcões, vales, desertos e calotas polares. Olympus Mons, o maior vulcão do sistema solar, está localizado em Marte. Evidências sugerem que Marte teve água líquida no passado, e há indicações de água em estado líquido sob a superfície atual. Missões como a Mars Rover e a Perseverance estão explorando sinais de vida passada e presente. Várias missões robóticas têm explorado Marte, incluindo rovers como Spirit, Opportunity, Curiosity e Perseverance, além de orbitadores que estudam a atmosfera e a superfície do planeta.
"""
    ))
    planets.append(Planet(
        name="Júpiter",
        color=[1.5, 0.75, 0.0],  # Aumentado para refletir tamanho maior
        size=3.0,  # Aumentado de 2.0 para 3.0
        distance=35,
        orbit_speed=0.1,
        rotation_speed=1.0,
        texture_file="textures/jupiter.jpg",
        info="""
Júpiter é o quinto planeta do Sol e o maior do sistema solar, com um diâmetro de aproximadamente 139.820 km. Possui uma massa que representa cerca de 70% da massa total dos planetas do sistema solar. É um gigante gasoso composto principalmente de hidrogênio (cerca de 90%) e hélio (cerca de 10%), com traços de metano, vapor de água, amônia e outros compostos. Uma das características mais icônicas de Júpiter é a Grande Mancha Vermelha, uma tempestade gigante maior que a Terra, que existe há pelo menos 350 anos. Júpiter possui um sistema de anéis tênues e mais de 79 luas conhecidas, incluindo as galileanas: Io, Europa, Ganimedes e Calisto. Missões como a Galileo e a Juno têm estudado a composição atmosférica, o campo magnético e as luas de Júpiter, contribuindo para o entendimento dos gigantes gasosos.
"""
    ))
    planets.append(Planet(
        name="Saturno",
        color=[1.5, 1.5, 0.0],  # Aumentado para refletir tamanho maior
        size=2.7,  # Aumentado de 1.8 para 2.7
        distance=45,
        orbit_speed=0.08,
        rotation_speed=0.9,
        texture_file="textures/saturn.jpg",
        info="""
Saturno é o sexto planeta do Sol e é conhecido por seu extenso sistema de anéis. Possui um diâmetro de aproximadamente 116.460 km, sendo o segundo maior planeta do sistema solar. Assim como Júpiter, Saturno é um gigante gasoso composto principalmente de hidrogênio (cerca de 96%) e hélio (cerca de 3%), com traços de outros compostos como metano e amônia. Saturno possui o sistema de anéis mais visível e complexo do sistema solar, composto por bilhões de partículas de gelo e rocha de tamanhos variados. Os anéis são divididos em diferentes seções (A, B, C, etc.) com características distintas. Saturno tem mais de 80 luas conhecidas, incluindo Titã, a segunda maior lua do sistema solar, que possui uma atmosfera densa e lagos de metano líquido. Missões como Cassini-Huygens proporcionaram uma compreensão detalhada de Saturno, seus anéis e luas, revelando dados sobre sua atmosfera, estrutura interna e dinâmica dos anéis.
"""
    ))
    planets.append(Planet(
        name="Urano",
        color=[0.75, 1.5, 1.5],  # Aumentado para refletir tamanho maior
        size=1.8,  # Aumentado de 1.2 para 1.8
        distance=55,
        orbit_speed=0.05,
        rotation_speed=0.7,
        texture_file="textures/uranus.jpg",
        info="""
Urano é o sétimo planeta do Sol e é classificado como um gigante gasoso ou gigante de gelo. Possui um diâmetro de aproximadamente 50.724 km. Urano é único entre os planetas, pois gira quase de lado, com uma inclinação axial de cerca de 98 graus. Isso resulta em estações extremas que duram cerca de 20 anos cada. A composição de Urano inclui hidrogênio, hélio e metano. A presença de metano na atmosfera confere ao planeta sua coloração azulada. Urano possui 13 anéis conhecidos e 27 luas confirmadas, com nomes inspirados em personagens das obras de Shakespeare e Alexander Pope. A única missão a visitar Urano foi a Voyager 2 da NASA em 1986, que forneceu dados valiosos sobre sua atmosfera, anéis e luas. Missões futuras estão planejadas para explorar mais detalhadamente este gigante de gelo.
"""
    ))
    planets.append(Planet(
        name="Netuno",
        color=[0.0, 0.0, 0.75],  # Aumentado para refletir tamanho maior
        size=1.65,  # Aumentado de 1.1 para 1.65
        distance=65,
        orbit_speed=0.04,
        rotation_speed=0.6,
        texture_file="textures/neptune.jpg",
        info="""
Netuno é o oitavo e último planeta do Sol, sendo um gigante gasoso com um diâmetro de aproximadamente 49.244 km. É conhecido por suas cores azuladas intensas. Netuno é composto principalmente de hidrogênio, hélio e metano. A presença de metano na atmosfera confere ao planeta sua tonalidade azul. Netuno possui os ventos mais rápidos do sistema solar, com velocidades que podem atingir até 2.100 km/h. Essas tempestades gigantes impulsionam as nuvens de alta altitude. Netuno possui 5 anéis tênues e 14 luas conhecidas, sendo Tritão a maior delas. Tritão é única por sua órbita retrógrada, sugerindo que pode ser um objeto capturado do cinturão de Kuiper. A única missão a visitar Netuno foi a Voyager 2 em 1989, que forneceu informações detalhadas sobre sua atmosfera, anéis e luas. Missões futuras estão sendo consideradas para explorar este distante gigante gasoso.
"""
    ))

    # Adicionar anéis para Saturno
    for planet in planets:
        if planet.name.lower() == "saturno":
            ring = Ring(
                planet=planet,
                texture_file="textures/saturn_ring.png",
                inner_radius=planet.size + 0.5,
                outer_radius=planet.size + 3.0,
                rotation_speed=0.2  # Pode ajustar conforme necessário
            )
            rings.append(ring)
            break  # Encontrou Saturno, pode parar o loop

    # Adicionar a Lua orbitando a Terra
    moon = Planet(
        name="Lua",
        color=[0.8, 0.8, 0.8],
        size=0.4,  # Tamanho menor que os planetas
        distance=3,  # Distância em relação à Terra
        orbit_speed=2.0,  # Velocidade de órbita mais rápida
        rotation_speed=5.0,  # Rotação mais rápida para a Lua
        texture_file="textures/moon.jpg",
        info="""
A Lua é o único satélite natural da Terra e o quinto maior do sistema solar. Possui um diâmetro de aproximadamente 3.474 km e uma superfície marcada por crateras, planícies e montanhas. A Lua desempenha um papel crucial nas marés terrestres e tem sido objeto de exploração humana, incluindo as missões Apollo da NASA. A Lua influencia muitos aspectos da Terra, incluindo ciclos biológicos e estabilidade axial.
""",
        parent=terra  # Define a Terra como o planeta pai
    )
    moons.append(moon)

# Função para desenhar texto na tela
def draw_text(x, y, text, color):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(*color)
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))  # Usar fonte maior para melhor legibilidade
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# Função para desenhar a tela de informações do planeta
def draw_info_screen(planet):
    glDisable(GL_LIGHTING)
    glDisable(GL_LIGHT0)
    glDisable(GL_LIGHT1)
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_DEPTH_TEST)

    # Fundo semi-transparente
    glColor4f(0, 0, 0, 0.8)
    glBegin(GL_QUADS)
    glVertex2f(50, 50)
    glVertex2f(750, 50)
    glVertex2f(750, 550)
    glVertex2f(50, 550)
    glEnd()

    # Margens internas
    glColor4f(1, 1, 1, 1)
    glBegin(GL_LINE_LOOP)
    glVertex2f(50, 50)
    glVertex2f(750, 50)
    glVertex2f(750, 550)
    glVertex2f(50, 550)
    glEnd()

    # Texto informativo
    glColor3f(1.0, 1.0, 1.0)

    # Posição inicial ajustada para começar abaixo do topo
    x_start = 60
    y_start = 520  # Um pouco abaixo do topo da janela
    y_offset = y_start
    line_height = 15  # Espaçamento vertical entre linhas

    # Dividir o texto em múltiplas linhas se necessário
    info_lines = split_text(planet.info, max_length=60)

    for line in info_lines:
        if line.strip() == "":
            y_offset -= (line_height + 5)  # Espaço extra para separar parágrafos
            continue
        draw_text(x_start, y_offset, line, [1.0, 1.0, 1.0])
        y_offset -= line_height

        # Verificar se a próxima linha ainda está dentro da área visível
        if y_offset < 80:
            break  # Pare de desenhar se chegar perto da parte inferior

    # Instrução para fechar
    draw_text(x_start, 70, "Pressione ESC para fechar.", [1.0, 1.0, 1.0])

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_LIGHTING)
    if light_enabled:
        glEnable(GL_LIGHT0)
    if light_enabled:
        glEnable(GL_LIGHT1)

# Função auxiliar para dividir texto em linhas
def split_text(text, max_length=60):
    """
    Divide o texto em linhas com base no comprimento máximo de caracteres.
    Considera quebras de linha existentes no texto.
    """
    paragraphs = text.strip().split('\n')
    lines = []
    for para in paragraphs:
        words = para.strip().split(' ')
        current_line = ""
        for word in words:
            if len(current_line + " " + word) <= max_length:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        # Adicionar uma linha vazia para separar parágrafos
        lines.append("")
    return lines

# Função para desenhar o background
def draw_background():
    if background_texture_id is None:
        return  # Não há textura de background carregada

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glEnable(GL_TEXTURE_2D)

    glBindTexture(GL_TEXTURE_2D, background_texture_id)
    glColor3f(1.0, 1.0, 1.0)  # Cor branca para não alterar a textura

    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex2f(0, 0)
    glTexCoord2f(1.0, 0.0)
    glVertex2f(window_width, 0)
    glTexCoord2f(1.0, 1.0)
    glVertex2f(window_width, window_height)
    glTexCoord2f(0.0, 1.0)
    glVertex2f(0, window_height)
    glEnd()

    glDisable(GL_TEXTURE_2D)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# Função para desenhar o Sol com textura e emissão
def draw_sun():
    glPushMatrix()
    glTranslatef(0, 0, 0)  # O Sol está no centro

    if sun_texture_id:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, sun_texture_id)
        glColor3f(1.0, 1.0, 1.0)  # Resetar a cor para branco antes de aplicar a textura
    else:
        glColor3f(1.0, 1.0, 0.0)  # Amarelo

    # Definir material emissivo para o Sol
    glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, [1.0, 1.0, 1.0, 1.0])

    quad = gluNewQuadric()
    if sun_texture_id:
        gluQuadricTexture(quad, GL_TRUE)
        gluQuadricNormals(quad, GLU_SMOOTH)
    else:
        gluQuadricNormals(quad, GLU_SMOOTH)
    gluSphere(quad, 5, 50, 50)  # Aumentado de 2 para 5
    gluDeleteQuadric(quad)

    if sun_texture_id:
        glDisable(GL_TEXTURE_2D)

    # Resetar a propriedade emissiva para evitar que outros objetos sejam afetados
    glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])

    glPopMatrix()

# Função de desenho da cena
def display():
    global start_time
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    if game_over:
        draw_end_game_screen()

    else:
        # Desenhar Background
        draw_background()

        glLoadIdentity()

        if not collision_detected:
            # Definir a câmera
            set_camera()

            # Configurar iluminação
            if light_enabled:
                glEnable(GL_LIGHT0)
            else:
                glDisable(GL_LIGHT0)

            # Desenhar Player (Foguete)
            if current_camera != CAMERA_FIRST_PERSON:
                player.draw_rocket()

            # Desenhar o Sol com textura e emissão
            draw_sun()

            # Desenhar planetas
            for planet in planets:
                planet.draw()

            # Desenhar luas
            for moon in moons:
                moon.draw()

            # Desenhar anéis (especificamente para Saturno)
            for ring in rings:
                ring.draw()

            # Verificar proximidade e exibir nomes
            for body in planets + moons:
                pos = body.get_position()
                distance = np.linalg.norm(player.position - np.array(pos))
                if distance < body.size + 5:  # Ajustar limiar de proximidade
                    draw_text(10, window_height - 30, f"Você está próximo de {body.name}", [1.0, 1.0, 1.0])
        else:
            # Exibir tela de informações do planeta
            draw_info_screen(collided_planet)

        # Tempo passado e planetas coletados
        if game_over:
            timer_text = f"Final Time: {int(final_time)}s"
        elif paused:
            timer_text = f"Time: {int(tempo_antes_pausa)}s"
        else:
            # Live timer durante a gameplay
            elapsed_time = time.time() - start_time
            timer_text = f"Time: {int(elapsed_time)}s"

        draw_text(10, window_height - 50, timer_text, [1.0, 1.0, 1.0])

        collected_text = f"Planetas Visitados: {len(player.planetas_coletados)} / {len(planets)}"
        draw_text(10, window_height - 80, collected_text, [1.0, 1.0, 1.0])

    glutSwapBuffers()

# Função para definir a câmera atual
def set_camera():
    global player
    rad = math.radians(player.yaw)

    if current_camera == CAMERA_FIRST_PERSON:
        # Câmera em primeira pessoa
        offset_distance = 0.8
        eye = player.position + np.array([offset_distance * math.sin(rad),
                                         0.5,
                                         -offset_distance * math.cos(rad)])
        center = player.position + np.array([math.sin(rad), 0.5, -math.cos(rad)])
        up = [0, 1, 0]
        gluLookAt(eye[0], eye[1], eye[2],
                  center[0], center[1], center[2],
                  up[0], up[1], up[0])

    elif current_camera == CAMERA_FIXED_1:
        # Câmera fixa 1: posição fixa atrás e acima da nave, seguindo o yaw
        offset_distance_back = 20.0
        offset_height = 10.0

        eye_x = player.position[0] - offset_distance_back * math.sin(rad)
        eye_z = player.position[2] + offset_distance_back * math.cos(rad)
        eye_y = player.position[1] + offset_height

        eye = np.array([eye_x, eye_y, eye_z])
        center = player.position
        up = [0, 1, 0]
        gluLookAt(eye[0], eye[1], eye[2],
                  center[0], center[1], center[2],
                  up[0], up[1], up[2])

    elif current_camera == CAMERA_FIXED_2:
        # Câmera fixa 2: posição fixa de cima, seguindo o yaw
        offset_height = 50.0
        eye = player.position + np.array([0, offset_height, 0])
        center = player.position
        up = [0, 0, -1]  # Fixed up vector to avoid flipping
        gluLookAt(eye[0], eye[1], eye[2], center[0], center[1], center[2], up[0], up[1], up[2])

    # Atualizar posição da luz do foguete
    glLightfv(GL_LIGHT1, GL_POSITION, [player.position[0], player.position[1], player.position[2], 1])

# Função para atualizar a cena (rotação, órbita, detecção de proximidade)
def update(value):
    global collision_detected
    if not collision_detected and not paused:  # Verificar se não está pausado
        # Atualizar planetas
        for planet in planets:
            planet.update()

        # Atualizar luas
        for moon in moons:
            moon.update()

        # Atualizar anéis
        for ring in rings:
            ring.update()

        # Verificar colisões
        player.check_collision(planets + moons)

        # Resetar movimento
        player.is_moving = False  # Reseta o estado de movimento após a atualização

    glutPostRedisplay()
    glutTimerFunc(16, update, 0)  # Aproximadamente 60 FPS

# Função para gerenciar entrada do teclado
def keyboard(key, x, y):
    global current_camera, light_enabled, collision_detected, collided_planet, game_over, paused, tempo_antes_pausa, start_time
    key = key.decode('utf-8').lower()

    if game_over:
        if key == '\x1b':  # ESC para fechar o jogo
            glutLeaveMainLoop()
        elif key == '\r':  # ENTER para reiniciar o jogo
            restart_game()
    else:
        if not collision_detected:
            if key == 'w':
                player.move_player(1, 0)  # Mover para frente
            elif key == 's':
                player.move_player(-1, 0)
            elif key == 'a':
                player.move_player(0, -1)
            elif key == 'd':
                player.move_player(0, 1)
            elif key == 'q':
                player.rotate_right(5)    # Rotacionar para a direita
            elif key == 'e':
                player.rotate_left(5)     # Rotacionar para a esquerda
            elif key == '1':
                current_camera = CAMERA_FIRST_PERSON
            elif key == '2':
                current_camera = CAMERA_FIXED_1
            elif key == '3':
                current_camera = CAMERA_FIXED_2
            elif key == 'l':
                light_enabled = not light_enabled
            elif key == 'p':
                paused = not paused  # Alternar estado de pausa
                if paused:
                    tempo_antes_pausa = time.time() - start_time
                else:
                    start_time = time.time() - tempo_antes_pausa
        else:
            if key == '\x1b':  # ESC para fechar a tela de informações
                collision_detected = False
                collided_planet = None

    glutPostRedisplay()

# Função para criar menus aprimorados
def create_menus():
    # Menu de Câmeras
    menu_cameras = glutCreateMenu(menu_cameras_func)
    glutAddMenuEntry("Primeira Pessoa", CAMERA_FIRST_PERSON)
    glutAddMenuEntry("Câmera Fixa 1", CAMERA_FIXED_1)
    glutAddMenuEntry("Câmera Fixa 2", CAMERA_FIXED_2)

    # Menu de Iluminação
    menu_lighting = glutCreateMenu(menu_lighting_func)
    glutAddMenuEntry("Luz Ligada", LIGHT_ON)
    glutAddMenuEntry("Luz Desligada", LIGHT_OFF)

    # Menu de Planetas e Luas
    menu_planets = glutCreateMenu(menu_planets_func)
    for idx, planet in enumerate(planets + moons):  # Incluir luas no menu
        glutAddMenuEntry(planet.name, idx)  # Usa o índice como identificador

    # Menu de Curiosidades
    menu_curiosities = glutCreateMenu(menu_curiosities_func)
    curiosities = [
        "O Sol contém 99,86% da massa do sistema solar.",
        "Mercúrio não possui atmosfera significativa.",
        "Vênus tem uma rotação retrógrada.",
        "Terra é o único planeta conhecido com vida.",
        "Marte possui o maior vulcão do sistema solar.",
        "Júpiter tem uma Grande Mancha Vermelha, uma tempestade eterna.",
        "Saturno é conhecido por seus impressionantes anéis.",
        "Urano gira de lado, com uma inclinação axial extrema.",
        "Netuno possui os ventos mais rápidos do sistema solar."
    ]
    for idx, fact in enumerate(curiosities):
        glutAddMenuEntry(f"Curiosidade {idx+1}", idx)

    # Menu de Controles
    menu_controls = glutCreateMenu(menu_controls_func)
    controls = [
        "W: Mover para frente",
        "Q: Rotacionar para a direita",
        "E: Rotacionar para a esquerda",
        "1, 2, 3: Mudar câmera",
        "L: Alternar iluminação",
        "P: Pausar/Despausar planetas",
        "Direito do Mouse: Abrir menu"
    ]
    for idx, control in enumerate(controls):
        glutAddMenuEntry(control, idx)

    # Menu Principal
    main_menu = glutCreateMenu(lambda option: None)
    glutAddSubMenu("Câmeras", menu_cameras)
    glutAddSubMenu("Iluminação", menu_lighting)
    glutAddSubMenu("Planetas e Luas", menu_planets)  # Atualizado para incluir luas
    glutAddSubMenu("Curiosidades", menu_curiosities)
    glutAddSubMenu("Controles", menu_controls)
    glutAttachMenu(GLUT_RIGHT_BUTTON)

def menu_cameras_func(option):
    global current_camera
    current_camera = option
    glutPostRedisplay()

def menu_lighting_func(option):
    global light_enabled
    if option == LIGHT_ON:
        light_enabled = True
    elif option == LIGHT_OFF:
        light_enabled = False
    glutPostRedisplay()

def menu_planets_func(option):
    global collision_detected, collided_planet
    if 0 <= option < len(planets + moons):
        collided_planet = (planets + moons)[option]
        collision_detected = True
        glutPostRedisplay()

def menu_curiosities_func(option):
    global collision_detected, collided_planet
    # Criar um "planeta virtual" para exibir a curiosidade
    class CuriosityPlanet:
        def __init__(self, fact):
            self.name = "Curiosidade"
            self.info = fact

    curiosities = [
        "O Sol contém 99,86% da massa do sistema solar.",
        "Mercúrio não possui atmosfera significativa.",
        "Vênus tem uma rotação retrógrada.",
        "Terra é o único planeta conhecido com vida.",
        "Marte possui o maior vulcão do sistema solar.",
        "Júpiter tem uma Grande Mancha Vermelha, uma tempestade eterna.",
        "Saturno é conhecido por seus impressionantes anéis.",
        "Urano gira de lado, com uma inclinação axial extrema.",
        "Netuno possui os ventos mais rápidos do sistema solar."
    ]
    if 0 <= option < len(curiosities):
        collided_planet = CuriosityPlanet(curiosities[option])
        collision_detected = True
        glutPostRedisplay()

def menu_controls_func(option):
    # Exibir controles na tela de informações
    global collision_detected, collided_planet
    class ControlsInfo:
        def __init__(self, controls):
            self.name = "Controles"
            self.info = controls

    controls = [
        "W: Mover para frente",
        "Q: Rotacionar para a direita",
        "E: Rotacionar para a esquerda",
        "1, 2, 3: Mudar câmera",
        "L: Alternar iluminação",
        "P: Pausar/Despausar planetas",
        "Direito do Mouse: Abrir menu"
    ]
    controls_info = "\n".join(controls)
    collided_planet = ControlsInfo(controls_info)
    collision_detected = True
    glutPostRedisplay()

# Função de redimensionamento da janela
def reshape(width, height):
    global window_width, window_height
    window_width = width
    window_height = height
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, float(width)/float(height), 1.0, 200.0)  # Ajustar a perspectiva para maior distância
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

# Inicialização geral
def init():
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(0.0, 0.0, 0.0, 1.0)  # Preto como espaço
    init_scene()
    create_menus()
    glutTimerFunc(16, update, 0)  # Iniciar loop de atualização

# Função de fim de jogo
def end_game():
    global game_over, final_time
    game_over = True
    if final_time == 0:
        final_time = time.time() - start_time  # Record final elapsed time

def draw_end_game_screen():
    global final_time
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    # Semi-transparent background
    glColor4f(0, 0, 0, 0.8)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(window_width, 0)
    glVertex2f(window_width, window_height)
    glVertex2f(0, window_height)
    glEnd()

    # Display final time and collected planets
    glColor3f(1.0, 1.0, 1.0)
    draw_text(window_width // 2 - 150, window_height // 2 + 100, "Game Over!", [1.0, 1.0, 1.0])
    draw_text(window_width // 2 - 180, window_height // 2 + 60, f"Final Time: {int(final_time)}s", [1.0, 1.0, 1.0])
    collected_text = "Planetas Coletados: " + ", ".join(player.planetas_coletados)
    draw_text(window_width // 2 - 200, window_height // 2 + 30, collected_text, [1.0, 1.0, 1.0])

    # Display instructions to restart or exit
    draw_text(window_width // 2 - 200, window_height // 2 - 30, "'ENTER' para Recomeçar", [1.0, 1.0, 1.0])
    draw_text(window_width // 2 - 200, window_height // 2 - 60, "'ESC' para Sair", [1.0, 1.0, 1.0])

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

def restart_game():
    global start_time, game_over, final_time, collision_detected, collided_planet
    start_time = time.time()
    game_over = False
    final_time = 0
    collision_detected = False
    collided_planet = None
    player.position = np.array([0, 2, 50], dtype='float64')  # Reset player position
    player.planetas_coletados.clear()       # Clear collected planets
    player.yaw = 0                          # Reset player rotation if needed

# Função principal
def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(window_width, window_height)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Sistema Solar Interativo 3D")
    init()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutMainLoop()

if __name__ == "__main__":
    main()
