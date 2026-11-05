# Koza-TTP

Proyecto que aplica el modelo de Programación Genética propuesto por John Koza (1992) para optimizar la planificación de calendarios en temporadas de béisbol.

**Autora:** Leslie Dickinson · *Tesis publicada como Leslie Pamela Brenes Valencia.*

---

## Cómo citar este trabajo / Citation

Si utilizas este código o los métodos de la investigación en tu propio proyecto científico o académico, por favor otorga el crédito correspondiente citando la tesis original. La cita usa el nombre con el que se registró la tesis en el ITAM:

### Formato APA
> Brenes Valencia, L. P. (2026). *Programación genética en la planificación de temporadas de béisbol* (Tesis de Ingeniería en Computación). Instituto Tecnológico Autónomo de México (ITAM), Ciudad de México, México.

### Formato BibTeX (para LaTeX)
```bibtex
@thesis{brenesvalencia2026programacion,
  author       = {Brenes Valencia, Leslie Pamela},
  title        = {Programación genética en la planificación de temporadas de béisbol},
  school       = {Instituto Tecnológico Autónomo de México (ITAM)},
  year         = {2026},
  type         = {Tesis de Ingeniería en Computación},
  address      = {Ciudad de México, México},
  url          = {https://github.com/lespam/koza-ttp}
}
```

## Licencia

Código bajo **GPL-3.0** (texto oficial en [`LICENSE`](LICENSE); resumen en inglés en [`LICENSE.md`](LICENSE.md#english-summary)). Puedes usarlo, estudiarlo y modificarlo, también para proyectos escolares. Si distribuyes una versión modificada, debe seguir siendo GPL-3.0, conservar el crédito a la autora y citar la tesis. Detalles, adenda del ITAM y término de reconocimiento: [`LICENSE.md`](LICENSE.md).

# Pasos para replicar
Crea una máquina virtual. Antes de instalar los paquetes, asegurate de hacer
```
# Update your package index
sudo apt update
sudo apt upgrade -y
# Install Python 3.10 and development tools
sudo apt install -y python3.10 python3.10-venv python3.10-dev
sudo apt install -y build-essential
# Set Python 3.10 as the default python3
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
sudo update-alternatives --set python3 /usr/bin/python3.10
# Create virtual environment
python3.10 -m venv env
# Install repository
sudo apt install -y git
git clone https://github.com/lespam/koza-ttp.git
# Activate virtual environment
source env/bin/activate
sudo apt-get install -y graphviz graphviz-dev libgraphviz-dev
pip install pygraphviz==1.9
pip install -r requirements.txt
```
## En Windows, sin compilador de C

`pygraphviz` necesita compilar código en C, y en Windows eso pide Microsoft C++ Build Tools. Si solo necesitas tareas que no dibujan el árbol, como traducir el sitio, instala todo menos `pygraphviz`:

```
findstr /v pygraphviz requirements.txt > requirements-windows.txt
pip install -r requirements-windows.txt
python manage.py translate_site
```

El dibujo del árbol (al ejecutar la optimización) sí necesita `pygraphviz`.
