// src/app/page.tsx
"use client";

import { CopilotChat } from "@copilotkit/react-ui";
import { useCopilotReadable } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";

export default function ChatPage() {
  // Proporcionar contexto al agente (opcional)
  useCopilotReadable({
    description: "Información del estudiante",
    value: {
      curso: "Física I",
      universidad: "Universidad de Buenos Aires",
    },
  });

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-white/20 backdrop-blur-sm rounded-lg p-2">
                <svg
                  className="w-8 h-8"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                  />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold">Asistente de Física I</h1>
                <p className="text-blue-100 text-sm">Universidad de Buenos Aires</p>
              </div>
            </div>
            <div className="hidden sm:flex items-center space-x-2 bg-green-500/20 backdrop-blur-sm px-4 py-2 rounded-full">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium">Online</span>
            </div>
          </div>
        </div>
      </header>

      {/* Chat Container */}
      <main className="flex-1 overflow-hidden bg-gray-50">
        <CopilotChat
          className="h-full"
          labels={{
            title: "Asistente de Física",
            initial:
              "¡Hola! 👋 Soy tu asistente de Física I de la UBA.\n\n" +
              "Puedo ayudarte con:\n" +
              "• Cinemática y Dinámica\n" +
              "• Trabajo y Energía\n" +
              "• Ondas y Sonido\n" +
              "• Mecánica de Fluidos\n\n" +
              "¿Qué tema te gustaría estudiar hoy?",
            placeholder: "Pregunta sobre física...",
          }}
          instructions={
            "Eres un profesor experto en Física I de la Universidad de Buenos Aires. " +
            "Siempre usa las herramientas disponibles para clasificar consultas, " +
            "buscar en documentos relevantes y proporcionar respuestas precisas y didácticas " +
            "basadas en el material del curso."
          }
          makeSystemMessage={(systemMessage) => {
            return (
              systemMessage +
              "\n\nRecuerda siempre:\n" +
              "1. Usa la herramienta 'clasificar_consulta' primero\n" +
              "2. Luego usa 'buscar_documentos' con palabras clave relevantes\n" +
              "3. Responde basándote en los documentos encontrados\n" +
              "4. Al final, usa 'guardar_interaccion' para registrar la conversación"
            );
          }}
        />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 px-4 py-3">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center space-x-4">
              <span>💡 Sistema RAG con Google ADK</span>
              <span className="hidden sm:inline">•</span>
              <span className="hidden sm:inline">Basado en documentos del curso</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-xs">Conectado</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}