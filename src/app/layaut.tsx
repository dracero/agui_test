// src/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import "@copilotkit/react-ui/styles.css";
import { CopilotKit } from "@copilotkit/react-core";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Asistente de Física I - UBA",
  description: "Sistema RAG con agentes ADK para consultas de Física I de la Universidad de Buenos Aires",
  keywords: ["física", "UBA", "educación", "RAG", "IA"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className={inter.className}>
        <CopilotKit
          runtimeUrl="/api/copilotkit"
          agent="asistente_fisica"
        >
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}