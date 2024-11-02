# 🌌 Sistema Solar Interativo 3D 🌌

![Sistema Solar](textures/milky_way.jpg)

## 👥 Equipe
| Nome                     | Matrícula |
|--------------------------|-----------|
| Caio Teixeira da Silva   | 22112243  |
| Noemy Torres Pereira     | 22112110  |

## 📚 Disciplina
**Computação Gráfica**  
**Professor:** Rômulo Nunes

---

## 📝 Descrição do Trabalho
Este projeto consiste em um ambiente virtual interativo desenvolvido em OpenGL, com o tema **Jogos Educativos**, focado na representação do Sistema Solar. Utilizamos diversos conceitos abordados no curso de Computação Gráfica, incluindo câmeras, iluminação, colisões, texturas e animações. A proposta é oferecer uma experiência educativa e imersiva, onde o usuário pode explorar o Sistema Solar de uma maneira divertida e visualmente interessante.

### 🎮 Funcionalidades Implementadas
| Funcionalidade               | Descrição |
|------------------------------|-----------|
| **📷 Câmeras Múltiplas**      | O usuário pode alternar entre uma câmera em primeira pessoa e duas câmeras fixas, com visão de diferentes ângulos do Sistema Solar. |
| **💡 Iluminação**             | A cena possui uma luz fixa representando o Sol e uma luz dinâmica que o usuário pode ativar e desativar. |
| **🚀 Sensor de Proximidade**  | Um sensor de colisão detecta quando o foguete está próximo de um planeta e exibe informações detalhadas sobre ele. |
| **🎨 Cores e Texturização**   | Cores vibrantes e texturas realistas foram aplicadas para enriquecer a visualização gráfica dos planetas e anéis de Saturno. |
| **🔄 Animações**              | Planetas orbitam em torno do Sol e giram sobre si mesmos. O foguete, controlado pelo usuário, também possui movimentos e rotações. |

---

## 🔍 Explicação do Código
O projeto é estruturado em classes para uma melhor organização e controle dos elementos na cena. Abaixo, detalhamos as principais classes e suas funções:

### 🌍 Classe `Planet`
Cada planeta é uma instância da classe `Planet`, com as seguintes propriedades:
- **`name`**: Nome do planeta.
- **`size`**: Tamanho (raio) do planeta.
- **`distance`**: Distância em relação ao Sol.
- **`orbit_speed`** e **`rotation_speed`**: Velocidades de órbita e rotação.
- **`texture_file`**: Arquivo de textura para uma visualização realista.

### 🪐 Classe `Ring`
Usada especificamente para os anéis de Saturno:
- **`inner_radius`** e **`outer_radius`**: Raio interno e externo dos anéis.
- **`rotation_speed`**: Velocidade de rotação dos anéis.

### 🚀 Classe `Player`
Representa o foguete controlado pelo usuário, com as propriedades:
- **`position`** e **`yaw`**: Posição e orientação.
- **Métodos de movimento**: Permitem ao usuário mover e rotacionar o foguete, além de verificar colisões com os planetas.

### 🎞️ Fluxo de Execução
1. **Inicialização (`init`)**: Configura a renderização, iluminação, e carrega as texturas e planetas.
2. **Renderização (`display`)**: Atualiza a cena com câmeras, iluminação e objetos.
3. **Atualização (`update`)**: Move planetas e anéis, e verifica colisões.
4. **Interação do Usuário**: As teclas e o menu de contexto permitem o controle do foguete e alternância de câmeras.

---

## 🕹️ Controles

| Tecla/Mouse         | Função                                       |
|---------------------|----------------------------------------------|
| `W`                 | Mover o foguete para frente                 |
| `Q`                 | Rotacionar o foguete para a direita         |
| `E`                 | Rotacionar o foguete para a esquerda        |
| `1`                 | Alternar para câmera em primeira pessoa     |
| `2`, `3`            | Alternar para câmeras fixas                 |
| `L`                 | Ativar/desativar iluminação adicional       |
| **Botão Direito**   | Abrir menu de contexto                      |
| `ESC`               | Fechar a tela de informações                |

---

## 🚀 Como Executar

### Requisitos
- **Linguagem:** Python 3.x
- **Bibliotecas:** PyOpenGL, PyOpenGL_accelerate, Pillow, NumPy

### Instalação das Dependências
```bash
pip install PyOpenGL PyOpenGL_accelerate Pillow numpy
```
### Estrutura de Pastas
- Certifique-se de organizar as texturas no diretório textures/ conforme abaixo:
```bash
/SistemaSolar3D
│
├── textures/
│   ├── milky_way.jpg
│   ├── sun.jpg
│   ├── mercury.jpg
│   ├── venus.jpg
│   ├── earth.jpg
│   ├── mars.jpg
│   ├── jupiter.jpg
│   ├── saturn.jpg
│   ├── saturn_ring.png
│   ├── uranus.jpg
│   └── neptune.jpg
│
├── main.py
└── README.md
```

### Executando o Projeto

- Execute o script principal com o comando:

```bash
python solar_system.py
```