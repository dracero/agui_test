// src/app/page.tsx
"use client";

import { CopilotChat } from "@copilotkit/react-ui";
import { useCopilotReadable } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import { BookOpen } from "lucide-react";
import MarkdownRenderer from "../components/MarkdownRenderer";

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
      <header className="bg-[#003D7A] text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-3 py-3 sm:px-6 lg:px-8 sm:py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 sm:space-x-3">
              <div className="bg-white rounded-lg p-1.5 sm:p-2">
                <img
                  src="/logo-fiuba.png"
                  alt="FIUBA Logo"
                  className="w-6 h-6 sm:w-8 sm:h-8 md:w-10 md:h-10 object-contain"
                />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold">Asistente de Física I</h1>
                <p className="text-blue-100 text-xs sm:text-sm hidden xs:block">Universidad de Buenos Aires</p>
              </div>
            </div>
            <div className="hidden sm:flex items-center space-x-2 bg-[#F7941D]/20 backdrop-blur-sm px-4 py-2 rounded-full">
              <div className="w-2 h-2 bg-[#F7941D] rounded-full animate-pulse"></div>
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
          AssistantMessage={({ message }) => (
            <div className="flex justify-start mb-4">
              <div className="max-w-[80%] rounded-lg px-4 py-2 bg-white border border-gray-200">
                <MarkdownRenderer content={typeof message === 'string' ? message : message.content || ''} />
              </div>
            </div>
          )}
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
              <div className="w-2 h-2 bg-[#F7941D] rounded-full"></div>
              <span className="text-xs">Conectado</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}