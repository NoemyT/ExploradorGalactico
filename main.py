import sys
import math
import random
import numpy as np
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
current_camera = CAMERA_FIRST_PERSON
cameras = {
    CAMERA_FIRST_PERSON: {'eye': [0, 2, 50], 'center': [0, 2, 0], 'up': [0, 1, 0]},
    CAMERA_FIXED_1: {'eye': [100, 70, 100], 'center': [0, 0, 0], 'up': [0, 1, 0]},
    CAMERA_FIXED_2: {'eye': [-100, 70, 100], 'center': [0, 0, 0], 'up': [0, 1, 0]},
}

# Iluminação
light_enabled = True

# Lista de planetas
planets = []

# Lista de nomes de planetas coletados
collected_planets = []

# Classe para representar cada planeta
class Planet:
    def __init__(self, name, color, size, distance, orbit_speed, rotation_speed):
        """
        :param name: Nome do planeta
        :param color: Cor do planeta [r, g, b]
        :param size: Tamanho do planeta (raio)
        :param distance: Distância do Sol (escala ajustada)
        :param orbit_speed: Velocidade de órbita (graus por frame)
        :param rotation_speed: Velocidade de rotação (graus por frame)
        """
        self.name = name
        self.color = color
        self.size = size
        self.distance = distance
        self.orbit_speed = orbit_speed
        self.rotation_speed = rotation_speed
        self.orbit_angle = random.uniform(0, 360)  # Ângulo inicial aleatório
        self.rotation_angle = random.uniform(0, 360)  # Ângulo de rotação inicial aleatório

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
        glColor3f(*self.color)
        glutSolidSphere(self.size, 50, 50)
        glPopMatrix()

# Classe para representar o jogador
class Player:
    global planets

    def __init__(self, position):
        self.position = np.array(position, dtype='float64')  # [x, y, z]
        self.angle = 0  # Rotação em torno do eixo Y
        self.size = 1.5

    def draw_rocket(self):
        glPushMatrix()
        glTranslatef(*self.position)
        glRotatef(self.angle, 0, 1, 0)
        glColor3f(0.275, 0.510, 0.706)  # Red for the main body

        # Rocket body (cylinder)
        glutSolidCylinder(0.5, 2, 20, 20)  # Adjust radius and height

        # Rocket nose (cone)
        glPushMatrix()
        glTranslatef(0, 0, -0.001)  # Move to top of the cylinder
        glRotatef(180, 1, 0, 0)
        glColor3f(0.698, 0.133, 0.133)
        glutSolidCone(0.5, 1, 20, 20)
        glPopMatrix()

        glPopMatrix()   

    def move_forward(self, distance):
        rad = math.radians(self.angle)
        self.position[0] += distance * math.sin(rad)
        self.position[2] -= distance * math.cos(rad)

    def move_backward(self, distance):
        self.move_forward(-distance)

    def strafe_left(self, distance):
        rad = math.radians(self.angle - 90)
        self.position[0] += distance * math.sin(rad)
        self.position[2] -= distance * math.cos(rad)

    def strafe_right(self, distance):
        self.strafe_left(-distance)

    def rotate_left(self, angle):
        self.angle += angle
        if self.angle >= 360:
            self.angle -= 360

    def rotate_right(self, angle):
        self.rotate_left(-angle)

    def check_collision(self, planets):
        for planet in planets:
            planet_pos = np.array(planet.get_position())
            distance = np.linalg.norm(self.position - planet_pos)
            if distance < self.size + planet.size:
                print(f"Collision detected with {planet.name}")
                # Handle collision (e.g., stop movement, reduce health)

# Instância do jogador
player = Player([0, 2, 50])  # Posição inicial ajustada para uma visualização melhor

# Inicialização da cena
def init_scene():
    global planets
    # Definir luzes
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)  # Luz do Sol
    glEnable(GL_LIGHT1)  # Luz adicional
    glLightfv(GL_LIGHT0, GL_POSITION, [0, 0, 0, 1])  # Luz fixa no Sol
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1, 1, 1, 1])
    glLightfv(GL_LIGHT1, GL_POSITION, [100, 100, 100, 1])  # Luz adicional
    glLightfv(GL_LIGHT1, GL_DIFFUSE, [1, 1, 1, 1])

    # Habilitar cor material
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    # Criar planetas com escala ajustada e velocidades mais lentas
    # Parâmetros: nome, cor, tamanho, distância do Sol, velocidade de órbita, velocidade de rotação
    planets.append(Planet("Mercúrio", [0.5, 0.5, 0.5], 0.5, 10, 0.5, 2))
    planets.append(Planet("Vênus", [1.0, 0.5, 0.0], 0.9, 15, 0.3, 1.8))
    planets.append(Planet("Terra", [0.0, 0.0, 1.0], 1.0, 20, 0.2, 1.5))
    planets.append(Planet("Marte", [1.0, 0.0, 0.0], 0.7, 25, 0.15, 1.2))
    planets.append(Planet("Júpiter", [1.0, 0.5, 0.0], 2.0, 35, 0.1, 1.0))
    planets.append(Planet("Saturno", [1.0, 1.0, 0.0], 1.8, 45, 0.08, 0.9))
    planets.append(Planet("Urano", [0.5, 1.0, 1.0], 1.2, 55, 0.05, 0.7))
    planets.append(Planet("Netuno", [0.0, 0.0, 0.5], 1.1, 65, 0.04, 0.6))

# Função de desenho da cena
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    # Definir a câmera
    set_camera()

    # Configurar iluminação
    if light_enabled:
        glEnable(GL_LIGHT1)
    else:
        glDisable(GL_LIGHT1)

    #Desenhar Player
    player.draw_rocket()

    # Desenhar o Sol
    glPushMatrix()
    glColor3f(1.0, 1.0, 0.0)  # Amarelo
    glutSolidSphere(2, 50, 50)  # Tamanho do Sol ajustado
    glPopMatrix()

    # Desenhar planetas
    for planet in planets:
        planet.draw()

    # Verificar proximidade e exibir nomes
    for planet in planets:
        pos = planet.get_position()
        distance = np.linalg.norm(player.position - np.array(pos))
        if distance < planet.size + 5:  # Ajustar limiar de proximidade
            draw_text(10, window_height - 30, f"Você está próximo de {planet.name}", [1.0, 1.0, 1.0])

    glutSwapBuffers()

# Função para definir a câmera atual
def set_camera():
    global player
    if current_camera == CAMERA_FIRST_PERSON:
        eye = player.position
        center = player.position + np.array([math.sin(math.radians(player.angle)),
                                            0,
                                            -math.cos(math.radians(player.angle))])
        up = [0, 1, 0]
        gluLookAt(eye[0], eye[1], eye[2],
                  center[0], center[1], center[2],
                  up[0], up[1], up[2])
        
    elif current_camera == CAMERA_FIXED_1:
        # Corrected Third-Person Camera (capturing the back of the rocket)
        distance_behind = 30.0  # Distance behind the player
        height_above = 5.0      # Slight height above the player
        rad = math.radians(player.angle)
        
        # Position camera behind the player, aligned with player's orientation
        eye = player.position + np.array([-distance_behind * math.sin(rad),
                                          height_above,
                                          distance_behind * math.cos(rad)])
        center = player.position + np.array([math.sin(rad), 0, -math.cos(rad)])
        up = [0, 1, 0]
        gluLookAt(eye[0], eye[1], eye[2],
                  center[0], center[1], center[2],
                  up[0], up[1], up[2])

    elif current_camera == CAMERA_FIXED_2:
        # Top-Down Camera (above the player)
        height_above = 60.0  # Adjust for desired altitude
        eye = player.position + np.array([0, height_above, 0])
        center = player.position
        up = [0, 0, -1]  # Inverted Z-axis for top-down view
        gluLookAt(eye[0], eye[1], eye[2],
                  center[0], center[1], center[2],
                  up[0], up[1], up[2])

    else:
        cam = cameras[current_camera]
        gluLookAt(cam['eye'][0], cam['eye'][1], cam['eye'][2],
                  cam['center'][0], cam['center'][1], cam['center'][2],
                  cam['up'][0], cam['up'][1], cam['up'][2])

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
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# Função para atualizar a cena (rotação, órbita, detecção de proximidade)
def update(value):
    # Atualizar planetas
    for planet in planets:
        planet.update()

    player.check_collision(planets)

    glutPostRedisplay()
    glutTimerFunc(16, update, 0)  # Aproximadamente 60 FPS

# Função para gerenciar entrada do teclado
def keyboard(key, x, y):
    global current_camera, light_enabled
    key = key.decode('utf-8').lower()
    if key == 'w':
        player.move_forward(1.0)  # Aumentar a distância por movimento para cobrir mais espaço
    elif key == 's':
        player.move_backward(1.0)
    elif key == 'a':
        player.strafe_left(1.0)
    elif key == 'd':
        player.strafe_right(1.0)
    elif key == 'q':
        player.rotate_left(5)
    elif key == 'e':
        player.rotate_right(5)
    elif key == '1':
        current_camera = CAMERA_FIRST_PERSON
    elif key == '2':
        current_camera = CAMERA_FIXED_1
    elif key == '3':
        current_camera = CAMERA_FIXED_2
    elif key == 'l':
        light_enabled = not light_enabled
    elif key == '\x1b':  # ESC para sair
        sys.exit()
    glutPostRedisplay()

# Função para criar menus
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

    # Menu Principal
    main_menu = glutCreateMenu(lambda option: None)
    glutAddSubMenu("Câmeras", menu_cameras)
    glutAddSubMenu("Iluminação", menu_lighting)
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
