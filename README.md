# Personal AI Agent

Un agente personal modular, determinista y confiable, diseñado con estándares de ingeniería de producción.

## Estructura del Proyecto

*   `agent/`: Bucle de control ReAct principal e instrucciones del sistema.
*   `skills/`: Módulos de habilidades del agente con schemas estrictos de entrada/salida (Pydantic).
*   `evals/`: Suite automatizada de pruebas para medir exactitud y rendimiento.
*   `ui/`: Interfaz para interactuar y monitorear el agente.

## Setup Inicial

1.  Crea un entorno virtual e instala las dependencias:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  Crea un archivo `.env` en la raíz del proyecto y agrega tu API Key de Google AI Studio:
    ```env
    GEMINI_API_KEY=tu_api_key_aqui
    ```

3.  Ejecuta el prototipo básico del agente en consola:
    ```bash
    python main.py
    ```
