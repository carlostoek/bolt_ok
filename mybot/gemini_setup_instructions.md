# Configuración y Uso de la CLI de Gemini

## Estado Actual
La CLI de Google Cloud (gcloud) ha sido instalada exitosamente en el sistema. La funcionalidad de Gemini está disponible a través de Vertex AI Model Garden, pero requiere autenticación para su uso.

## PATH
El Google Cloud SDK ha sido agregado al PATH permanentemente en el archivo `~/.bash_profile`.

## Comandos Disponibles
Los modelos de Gemini pueden ser accedidos a través de los siguientes comandos:

```bash
# Listar los modelos disponibles en Model Garden
gcloud ai model-garden models list

# Ver la configuración de despliegue de un modelo
gcloud ai model-garden models list-deployment-config --model="publisher/models/model-name"

# Desplegar un modelo (requiere configuración adicional)
gcloud ai model-garden models deploy --model="publisher/models/model-name" --endpoint="endpoint-name"
```

## Autenticación Requerida
Para usar los modelos de Gemini, debes autenticarte con tu cuenta de Google:

```bash
gcloud auth login
```

Este comando abrirá una página web en tu navegador donde podrás iniciar sesión con tu cuenta de Google. Una vez autenticado, podrás usar todos los comandos de Vertex AI Model Garden.

## Autenticación en Servidores sin GUI
Si estás trabajando en un servidor remoto sin interfaz gráfica, puedes usar el flujo de autenticación con código:

1. Ejecuta `gcloud auth login`
2. Copia la URL que se muestra en la consola
3. Pega la URL en un navegador en tu máquina local
4. Inicia sesión con tu cuenta de Google
5. Copia el código de verificación que se muestra
6. Pégalo en la consola del servidor

## Configurar Proyecto
Antes de usar los modelos, asegúrate de configurar tu proyecto de Google Cloud:

```bash
# Lista tus proyectos
gcloud projects list

# Establece tu proyecto por defecto
gcloud config set project YOUR_PROJECT_ID
```

## Verificación de Instalación
Para verificar que todo esté correctamente instalado:

```bash
gcloud --version
```

Esto debería mostrar la versión del Google Cloud SDK.