// src/app/api/copilotkit/route.ts
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

// 1. Usar ExperimentalEmptyAdapter ya que solo usamos un agente
const serviceAdapter = new ExperimentalEmptyAdapter();

// 2. Crear la instancia de CopilotRuntime con AG-UI client
//    para conectar con el agente ADK de Física
const runtime = new CopilotRuntime({
  agents: {
    // URL del backend FastAPI con el agente de Física
    // Se hace un cast a `any` para evitar el error de tipos causado por
    // múltiples copias de @ag-ui/client en node_modules (tipos incompatibles).
    "asistente_fisica": new HttpAgent({
      url: process.env.BACKEND_URL || "http://localhost:8000/"
    }) as unknown as any,
  }
});

// 3. Construir el API route de Next.js que maneja las solicitudes de CopilotKit
export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};