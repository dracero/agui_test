// src/app/layout.tsx
import { Inter } from "next/font/google";
import "./globals.css";
import "@copilotkit/react-ui/styles.css";
import { CopilotKit } from "@copilotkit/react-core";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Asistente de Física I - UBA",
  description: "Sistema RAG con agentes ADK para consultas de Física I de la Universidad de Buenos Aires",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className={inter.className}>
        <CopilotKit
          publicLicenseKey="ck_pub_71b6980a1be205bfab840fa8ec445f15"
          runtimeUrl="/api/copilotkit"
          agent="asistente_fisica"
        >
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}