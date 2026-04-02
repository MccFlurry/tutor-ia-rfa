#!/bin/bash
# Ejecutar UNA SOLA VEZ antes del primer docker compose up
# Requiere que el contenedor de Ollama esté corriendo

echo "Descargando modelo LLM: qwen2.5:7b-instruct-q4_K_M (~4.5GB)..."
docker exec tutor_ollama ollama pull qwen2.5:7b-instruct-q4_K_M

echo "Descargando modelo de embeddings: mxbai-embed-large (~670MB)..."
docker exec tutor_ollama ollama pull mxbai-embed-large

echo "Modelos descargados. Verificando..."
docker exec tutor_ollama ollama list
