import sys
import math
import random
import numpy as np
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

# Variáveis para colisão
collision_detected = False
collided_planet = None

# Texturas
background_texture_id = None
sun_texture_id = None
saturn_ring_texture_id = None

# Classe para representar cada planeta
class Planet:
    def __init__(self, name, color, size, distance, orbit_speed, rotation_speed, texture_file, info):
        """
        :param name: Nome do planeta
        :param color: Cor do planeta [r, g, b]
        :param size: Tamanho do planeta (raio)
        :param distance: Distância do Sol (escala ajustada)
        :param orbit_speed: Velocidade de órbita (graus por frame)
        :param rotation_speed: Velocidade de rotação (graus por frame)
        :param texture_file: Caminho para a textura do planeta
        :param info: Informações sobre o planeta
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
        # Calcular posição baseada no ângulo de órbita
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

    def draw_rocket(self):
        glPushMatrix()
        glTranslatef(*self.position)
        glRotatef(self.yaw, 0, 1, 0)   # Rotação em Y (Yaw)

        glColor3f(0.439, 0.502, 0.565)  # Cor principal do corpo
        glutSolidCylinder(0.5, 2, 20, 20)  # Cilindro que compõe o corpo

        # Chápeu do foguete (cone)
        glPushMatrix()
        glTranslatef(0, 0, -0.001)  # Ajustando o cone
        glRotatef(180, 1, 0, 0)     # Ajustando orientação
        glColor3f(0.698, 0.133, 0.133)
        glutSolidCone(0.5, 1, 20, 20)
        glPopMatrix()

        # Rocket bottom
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

        glPopMatrix()

    def move_forward(self, distance):
        # Calcula o deslocamento baseado em yaw
        rad_yaw = math.radians(self.yaw)

        # Componentes de movimento
        dx = distance * math.sin(rad_yaw)
        dz = -distance * math.cos(rad_yaw)
        dy = 0  # Sem movimentação vertical

        self.position += np.array([dx, dy, dz])
        print(f"Movendo para frente: posição atual {self.position}")

    def rotate_right(self, angle):
        self.yaw -= angle
        if self.yaw < 0:
            self.yaw += 360
        print(f"Rotacionando para a direita: yaw = {self.yaw} graus")

    def rotate_left(self, angle):
        self.yaw += angle
        if self.yaw >= 360:
            self.yaw -= 360
        print(f"Rotacionando para a esquerda: yaw = {self.yaw} graus")

    def check_collision(self, planets):
        global collision_detected, collided_planet
        for planet in planets:
            planet_pos = np.array(planet.get_position())
            distance = np.linalg.norm(self.position - planet_pos)
            if distance < self.size + planet.size:
                print(f"Collision detected with {planet.name}")
                collision_detected = True
                collided_planet = planet
                break

# Instância do jogador
player = Player([0, 2, 50])  # Posição inicial ajustada para uma visualização melhor

# Lista de anéis (especificamente para Saturno)
rings = []

# Inicialização da cena
def init_scene():
    global planets, background_texture_id, sun_texture_id, saturn_ring_texture_id, rings
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
    planets.append(Planet(
        name="Mercúrio",
        color=[0.5, 0.5, 0.5],
        size=0.5,
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
        color=[1.0, 0.5, 0.0],
        size=0.9,
        distance=15,
        orbit_speed=0.3,
        rotation_speed=1.8,
        texture_file="textures/venus.jpg",
        info="""
Vênus é o segundo planeta do Sol e possui um diâmetro semelhante ao da Terra, com cerca de 12.104 km. É conhecido por sua densidade e composição rochosa. A atmosfera é composta predominantemente de dióxido de carbono (CO2) com nuvens de ácido sulfúrico, criando um efeito estufa extremo que eleva a temperatura de superfície a cerca de 467°C. Vênus possui uma rotação retrógrada, girando no sentido oposto ao da maioria dos planetas, completando uma rotação em aproximadamente 243 dias terrestres. Missões como a Venera da Rússia e a Akatsuki da JAXA têm estudado a atmosfera densa e as condições superficiais de Vênus.
"""
    ))
    planets.append(Planet(
        name="Terra",
        color=[0.0, 0.0, 1.0],
        size=1.0,
        distance=20,
        orbit_speed=0.2,
        rotation_speed=1.5,
        texture_file="textures/earth.jpg",
        info="""
A Terra é o terceiro planeta do Sol e o único conhecido por abrigar vida. Possui um diâmetro de aproximadamente 12.742 km e uma massa que permite a existência de uma atmosfera estável. A atmosfera terrestre é composta principalmente de nitrogênio (78%) e oxigênio (21%), com traços de argônio, dióxido de carbono e outros gases. É essencial para a vida, protegendo contra radiações nocivas e regulando a temperatura. Cerca de 71% da superfície da Terra é coberta por água, incluindo oceanos, rios, lagos e gelo polar. A água é vital para todos os seres vivos e desempenha um papel crucial no clima e na geologia do planeta. A Terra é o ponto de partida para todas as missões espaciais humanas, incluindo a Estação Espacial Internacional (ISS), e futuras explorações para a Lua, Marte e além.
"""
    ))
    planets.append(Planet(
        name="Marte",
        color=[1.0, 0.0, 0.0],
        size=0.7,
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
        color=[1.0, 0.5, 0.0],
        size=2.0,
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
        color=[1.0, 1.0, 0.0],
        size=1.8,
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
        color=[0.5, 1.0, 1.0],
        size=1.2,
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
        color=[0.0, 0.0, 0.5],
        size=1.1,
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
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))  # Usar fonte menor
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
    gluSphere(quad, 2, 50, 50)  # Tamanho do Sol ajustado
    gluDeleteQuadric(quad)

    if sun_texture_id:
        glDisable(GL_TEXTURE_2D)

    # Resetar a propriedade emissiva para evitar que outros objetos sejam afetados
    glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])

    glPopMatrix()

# Função de desenho da cena
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
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
        player.draw_rocket()

        # Desenhar o Sol com textura e emissão
        draw_sun()

        # Desenhar planetas
        for planet in planets:
            planet.draw()

        # Desenhar anéis (especificamente para Saturno)
        for ring in rings:
            ring.draw()

        # Verificar proximidade e exibir nomes
        for planet in planets:
            pos = planet.get_position()
            distance = np.linalg.norm(player.position - np.array(pos))
            if distance < planet.size + 5:  # Ajustar limiar de proximidade
                draw_text(10, window_height - 30, f"Você está próximo de {planet.name}", [1.0, 1.0, 1.0])
    else:
        # Exibir tela de informações do planeta
        draw_info_screen(collided_planet)

    glutSwapBuffers()

# Função para definir a câmera atual
def set_camera():
    global player
    if current_camera == CAMERA_FIRST_PERSON:
        # Camera posicionada um pouco em frente ao cone
        offset_distance = 0.8
        rad = math.radians(player.yaw)

        eye = player.position + np.array([offset_distance * math.sin(rad),
                                         0.5,
                                         -offset_distance * math.cos(rad)])
        center = player.position + np.array([math.sin(rad), 0.5, -math.cos(rad)])
        up = [0, 1, 0]
        gluLookAt(eye[0], eye[1], eye[2],
                  center[0], center[1], center[2],
                  up[0], up[1], up[2])

    elif current_camera == CAMERA_FIXED_1:
        distance_behind = 20.0  # Distancia do player
        height_above = 5.0      # Direção da visão sobre o player
        rad = math.radians(player.yaw)

        eye = player.position + np.array([-distance_behind * math.sin(rad),
                                         height_above,
                                         distance_behind * math.cos(rad)])
        center = player.position + np.array([math.sin(rad), 0, -math.cos(rad)])
        up = [0, 1, 0]
        gluLookAt(eye[0], eye[1], eye[2],
                  center[0], center[1], center[2],
                  up[0], up[1], up[2])

    elif current_camera == CAMERA_FIXED_2:
        height_above = 40.0  # Distancia da altura
        eye = player.position + np.array([0, height_above, 0])
        center = player.position
        up = [0, 0, -1]  # Inversão do eixo Z
        gluLookAt(eye[0], eye[1], eye[2],
                  center[0], center[1], center[2],
                  up[0], up[1], up[2])

    # Atualizar posição da luz do foguete
    glLightfv(GL_LIGHT1, GL_POSITION, [player.position[0], player.position[1], player.position[2], 1])

# Função para atualizar a cena (rotação, órbita, detecção de proximidade)
def update(value):
    global collision_detected
    if not collision_detected:
        # Atualizar planetas
        for planet in planets:
            planet.update()

        # Atualizar anéis
        for ring in rings:
            ring.update()

        # Verificar colisões
        player.check_collision(planets)

    glutPostRedisplay()
    glutTimerFunc(16, update, 0)  # Aproximadamente 60 FPS

# Função para gerenciar entrada do teclado
def keyboard(key, x, y):
    global current_camera, light_enabled, collision_detected, collided_planet
    key = key.decode('utf-8').lower()
    if not collision_detected:
        if key == 'w':
            player.move_forward(1.0)  # Mover para frente
        elif key == 'q':
            player.rotate_right(5)    # Rotacionar para a direita
        elif key == 'e':
            player.rotate_left(5)     # Rotacionar para a esquerda
        elif key == '1':
            current_camera = CAMERA_FIRST_PERSON
            print("Câmera mudada para Primeira Pessoa")
        elif key == '2':
            current_camera = CAMERA_FIXED_1
            print("Câmera mudada para Fixa 1")
        elif key == '3':
            current_camera = CAMERA_FIXED_2
            print("Câmera mudada para Fixa 2")
        elif key == 'l':
            light_enabled = not light_enabled
            print(f"Iluminação {'ligada' if light_enabled else 'desligada'}")
    else:
        if key == '\x1b':  # ESC para fechar a tela de informações
            collision_detected = False
            collided_planet = None
            print("Tela de informações fechada")

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

    # Menu de Planetas
    menu_planets = glutCreateMenu(menu_planets_func)
    for idx, planet in enumerate(planets):
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
        "Direito do Mouse: Abrir menu"
    ]
    for idx, control in enumerate(controls):
        glutAddMenuEntry(control, idx)

    # Menu Principal
    main_menu = glutCreateMenu(lambda option: None)
    glutAddSubMenu("Câmeras", menu_cameras)
    glutAddSubMenu("Iluminação", menu_lighting)
    glutAddSubMenu("Planetas", menu_planets)
    glutAddSubMenu("Curiosidades", menu_curiosities)
    glutAddSubMenu("Controles", menu_controls)
    glutAttachMenu(GLUT_RIGHT_BUTTON)

def menu_cameras_func(option):
    global current_camera
    current_camera = option
    print(f"Câmera selecionada: {current_camera}")
    glutPostRedisplay()

def menu_lighting_func(option):
    global light_enabled
    if option == LIGHT_ON:
        light_enabled = True
        print("Iluminação ligada via menu")
    elif option == LIGHT_OFF:
        light_enabled = False
        print("Iluminação desligada via menu")
    glutPostRedisplay()

def menu_planets_func(option):
    global collision_detected, collided_planet
    if 0 <= option < len(planets):
        collided_planet = planets[option]
        collision_detected = True
        print(f"Informações exibidas para o planeta: {collided_planet.name}")
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
        print("Curiosidade exibida.")
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
        "Direito do Mouse: Abrir menu"
    ]
    controls_info = "\n".join(controls)
    collided_planet = ControlsInfo(controls_info)
    collision_detected = True
    print("Controles exibidos.")
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
