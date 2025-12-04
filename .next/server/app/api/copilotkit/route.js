/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
(() => {
var exports = {};
exports.id = "app/api/copilotkit/route";
exports.ids = ["app/api/copilotkit/route"];
exports.modules = {

/***/ "(rsc)/./node_modules/@whatwg-node/fetch/dist sync recursive":
/*!****************************************************!*\
  !*** ./node_modules/@whatwg-node/fetch/dist/ sync ***!
  \****************************************************/
/***/ ((module) => {

function webpackEmptyContext(req) {
	var e = new Error("Cannot find module '" + req + "'");
	e.code = 'MODULE_NOT_FOUND';
	throw e;
}
webpackEmptyContext.keys = () => ([]);
webpackEmptyContext.resolve = webpackEmptyContext;
webpackEmptyContext.id = "(rsc)/./node_modules/@whatwg-node/fetch/dist sync recursive";
module.exports = webpackEmptyContext;

/***/ }),

/***/ "(rsc)/./node_modules/next/dist/build/webpack/loaders/next-app-loader/index.js?name=app%2Fapi%2Fcopilotkit%2Froute&page=%2Fapi%2Fcopilotkit%2Froute&appPaths=&pagePath=private-next-app-dir%2Fapi%2Fcopilotkit%2Froute.ts&appDir=%2Fhome%2Fcetec%2FAIProjects%2Fagui_test%2Fsrc%2Fapp&pageExtensions=tsx&pageExtensions=ts&pageExtensions=jsx&pageExtensions=js&rootDir=%2Fhome%2Fcetec%2FAIProjects%2Fagui_test&isDev=true&tsconfigPath=tsconfig.json&basePath=&assetPrefix=&nextConfigOutput=&preferredRegion=&middlewareConfig=e30%3D!":
/*!******************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/next/dist/build/webpack/loaders/next-app-loader/index.js?name=app%2Fapi%2Fcopilotkit%2Froute&page=%2Fapi%2Fcopilotkit%2Froute&appPaths=&pagePath=private-next-app-dir%2Fapi%2Fcopilotkit%2Froute.ts&appDir=%2Fhome%2Fcetec%2FAIProjects%2Fagui_test%2Fsrc%2Fapp&pageExtensions=tsx&pageExtensions=ts&pageExtensions=jsx&pageExtensions=js&rootDir=%2Fhome%2Fcetec%2FAIProjects%2Fagui_test&isDev=true&tsconfigPath=tsconfig.json&basePath=&assetPrefix=&nextConfigOutput=&preferredRegion=&middlewareConfig=e30%3D! ***!
  \******************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   patchFetch: () => (/* binding */ patchFetch),\n/* harmony export */   routeModule: () => (/* binding */ routeModule),\n/* harmony export */   serverHooks: () => (/* binding */ serverHooks),\n/* harmony export */   workAsyncStorage: () => (/* binding */ workAsyncStorage),\n/* harmony export */   workUnitAsyncStorage: () => (/* binding */ workUnitAsyncStorage)\n/* harmony export */ });\n/* harmony import */ var next_dist_server_route_modules_app_route_module_compiled__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! next/dist/server/route-modules/app-route/module.compiled */ \"(rsc)/./node_modules/next/dist/server/route-modules/app-route/module.compiled.js\");\n/* harmony import */ var next_dist_server_route_modules_app_route_module_compiled__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(next_dist_server_route_modules_app_route_module_compiled__WEBPACK_IMPORTED_MODULE_0__);\n/* harmony import */ var next_dist_server_route_kind__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! next/dist/server/route-kind */ \"(rsc)/./node_modules/next/dist/server/route-kind.js\");\n/* harmony import */ var next_dist_server_lib_patch_fetch__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! next/dist/server/lib/patch-fetch */ \"(rsc)/./node_modules/next/dist/server/lib/patch-fetch.js\");\n/* harmony import */ var next_dist_server_lib_patch_fetch__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(next_dist_server_lib_patch_fetch__WEBPACK_IMPORTED_MODULE_2__);\n/* harmony import */ var _home_cetec_AIProjects_agui_test_src_app_api_copilotkit_route_ts__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./src/app/api/copilotkit/route.ts */ \"(rsc)/./src/app/api/copilotkit/route.ts\");\n\n\n\n\n// We inject the nextConfigOutput here so that we can use them in the route\n// module.\nconst nextConfigOutput = \"\"\nconst routeModule = new next_dist_server_route_modules_app_route_module_compiled__WEBPACK_IMPORTED_MODULE_0__.AppRouteRouteModule({\n    definition: {\n        kind: next_dist_server_route_kind__WEBPACK_IMPORTED_MODULE_1__.RouteKind.APP_ROUTE,\n        page: \"/api/copilotkit/route\",\n        pathname: \"/api/copilotkit\",\n        filename: \"route\",\n        bundlePath: \"app/api/copilotkit/route\"\n    },\n    resolvedPagePath: \"/home/cetec/AIProjects/agui_test/src/app/api/copilotkit/route.ts\",\n    nextConfigOutput,\n    userland: _home_cetec_AIProjects_agui_test_src_app_api_copilotkit_route_ts__WEBPACK_IMPORTED_MODULE_3__\n});\n// Pull out the exports that we need to expose from the module. This should\n// be eliminated when we've moved the other routes to the new format. These\n// are used to hook into the route.\nconst { workAsyncStorage, workUnitAsyncStorage, serverHooks } = routeModule;\nfunction patchFetch() {\n    return (0,next_dist_server_lib_patch_fetch__WEBPACK_IMPORTED_MODULE_2__.patchFetch)({\n        workAsyncStorage,\n        workUnitAsyncStorage\n    });\n}\n\n\n//# sourceMappingURL=app-route.js.map//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHJzYykvLi9ub2RlX21vZHVsZXMvbmV4dC9kaXN0L2J1aWxkL3dlYnBhY2svbG9hZGVycy9uZXh0LWFwcC1sb2FkZXIvaW5kZXguanM/bmFtZT1hcHAlMkZhcGklMkZjb3BpbG90a2l0JTJGcm91dGUmcGFnZT0lMkZhcGklMkZjb3BpbG90a2l0JTJGcm91dGUmYXBwUGF0aHM9JnBhZ2VQYXRoPXByaXZhdGUtbmV4dC1hcHAtZGlyJTJGYXBpJTJGY29waWxvdGtpdCUyRnJvdXRlLnRzJmFwcERpcj0lMkZob21lJTJGY2V0ZWMlMkZBSVByb2plY3RzJTJGYWd1aV90ZXN0JTJGc3JjJTJGYXBwJnBhZ2VFeHRlbnNpb25zPXRzeCZwYWdlRXh0ZW5zaW9ucz10cyZwYWdlRXh0ZW5zaW9ucz1qc3gmcGFnZUV4dGVuc2lvbnM9anMmcm9vdERpcj0lMkZob21lJTJGY2V0ZWMlMkZBSVByb2plY3RzJTJGYWd1aV90ZXN0JmlzRGV2PXRydWUmdHNjb25maWdQYXRoPXRzY29uZmlnLmpzb24mYmFzZVBhdGg9JmFzc2V0UHJlZml4PSZuZXh0Q29uZmlnT3V0cHV0PSZwcmVmZXJyZWRSZWdpb249Jm1pZGRsZXdhcmVDb25maWc9ZTMwJTNEISIsIm1hcHBpbmdzIjoiOzs7Ozs7Ozs7Ozs7OztBQUErRjtBQUN2QztBQUNxQjtBQUNnQjtBQUM3RjtBQUNBO0FBQ0E7QUFDQSx3QkFBd0IseUdBQW1CO0FBQzNDO0FBQ0EsY0FBYyxrRUFBUztBQUN2QjtBQUNBO0FBQ0E7QUFDQTtBQUNBLEtBQUs7QUFDTDtBQUNBO0FBQ0EsWUFBWTtBQUNaLENBQUM7QUFDRDtBQUNBO0FBQ0E7QUFDQSxRQUFRLHNEQUFzRDtBQUM5RDtBQUNBLFdBQVcsNEVBQVc7QUFDdEI7QUFDQTtBQUNBLEtBQUs7QUFDTDtBQUMwRjs7QUFFMUYiLCJzb3VyY2VzIjpbIiJdLCJzb3VyY2VzQ29udGVudCI6WyJpbXBvcnQgeyBBcHBSb3V0ZVJvdXRlTW9kdWxlIH0gZnJvbSBcIm5leHQvZGlzdC9zZXJ2ZXIvcm91dGUtbW9kdWxlcy9hcHAtcm91dGUvbW9kdWxlLmNvbXBpbGVkXCI7XG5pbXBvcnQgeyBSb3V0ZUtpbmQgfSBmcm9tIFwibmV4dC9kaXN0L3NlcnZlci9yb3V0ZS1raW5kXCI7XG5pbXBvcnQgeyBwYXRjaEZldGNoIGFzIF9wYXRjaEZldGNoIH0gZnJvbSBcIm5leHQvZGlzdC9zZXJ2ZXIvbGliL3BhdGNoLWZldGNoXCI7XG5pbXBvcnQgKiBhcyB1c2VybGFuZCBmcm9tIFwiL2hvbWUvY2V0ZWMvQUlQcm9qZWN0cy9hZ3VpX3Rlc3Qvc3JjL2FwcC9hcGkvY29waWxvdGtpdC9yb3V0ZS50c1wiO1xuLy8gV2UgaW5qZWN0IHRoZSBuZXh0Q29uZmlnT3V0cHV0IGhlcmUgc28gdGhhdCB3ZSBjYW4gdXNlIHRoZW0gaW4gdGhlIHJvdXRlXG4vLyBtb2R1bGUuXG5jb25zdCBuZXh0Q29uZmlnT3V0cHV0ID0gXCJcIlxuY29uc3Qgcm91dGVNb2R1bGUgPSBuZXcgQXBwUm91dGVSb3V0ZU1vZHVsZSh7XG4gICAgZGVmaW5pdGlvbjoge1xuICAgICAgICBraW5kOiBSb3V0ZUtpbmQuQVBQX1JPVVRFLFxuICAgICAgICBwYWdlOiBcIi9hcGkvY29waWxvdGtpdC9yb3V0ZVwiLFxuICAgICAgICBwYXRobmFtZTogXCIvYXBpL2NvcGlsb3RraXRcIixcbiAgICAgICAgZmlsZW5hbWU6IFwicm91dGVcIixcbiAgICAgICAgYnVuZGxlUGF0aDogXCJhcHAvYXBpL2NvcGlsb3RraXQvcm91dGVcIlxuICAgIH0sXG4gICAgcmVzb2x2ZWRQYWdlUGF0aDogXCIvaG9tZS9jZXRlYy9BSVByb2plY3RzL2FndWlfdGVzdC9zcmMvYXBwL2FwaS9jb3BpbG90a2l0L3JvdXRlLnRzXCIsXG4gICAgbmV4dENvbmZpZ091dHB1dCxcbiAgICB1c2VybGFuZFxufSk7XG4vLyBQdWxsIG91dCB0aGUgZXhwb3J0cyB0aGF0IHdlIG5lZWQgdG8gZXhwb3NlIGZyb20gdGhlIG1vZHVsZS4gVGhpcyBzaG91bGRcbi8vIGJlIGVsaW1pbmF0ZWQgd2hlbiB3ZSd2ZSBtb3ZlZCB0aGUgb3RoZXIgcm91dGVzIHRvIHRoZSBuZXcgZm9ybWF0LiBUaGVzZVxuLy8gYXJlIHVzZWQgdG8gaG9vayBpbnRvIHRoZSByb3V0ZS5cbmNvbnN0IHsgd29ya0FzeW5jU3RvcmFnZSwgd29ya1VuaXRBc3luY1N0b3JhZ2UsIHNlcnZlckhvb2tzIH0gPSByb3V0ZU1vZHVsZTtcbmZ1bmN0aW9uIHBhdGNoRmV0Y2goKSB7XG4gICAgcmV0dXJuIF9wYXRjaEZldGNoKHtcbiAgICAgICAgd29ya0FzeW5jU3RvcmFnZSxcbiAgICAgICAgd29ya1VuaXRBc3luY1N0b3JhZ2VcbiAgICB9KTtcbn1cbmV4cG9ydCB7IHJvdXRlTW9kdWxlLCB3b3JrQXN5bmNTdG9yYWdlLCB3b3JrVW5pdEFzeW5jU3RvcmFnZSwgc2VydmVySG9va3MsIHBhdGNoRmV0Y2gsICB9O1xuXG4vLyMgc291cmNlTWFwcGluZ1VSTD1hcHAtcm91dGUuanMubWFwIl0sIm5hbWVzIjpbXSwiaWdub3JlTGlzdCI6W10sInNvdXJjZVJvb3QiOiIifQ==\n//# sourceURL=webpack-internal:///(rsc)/./node_modules/next/dist/build/webpack/loaders/next-app-loader/index.js?name=app%2Fapi%2Fcopilotkit%2Froute&page=%2Fapi%2Fcopilotkit%2Froute&appPaths=&pagePath=private-next-app-dir%2Fapi%2Fcopilotkit%2Froute.ts&appDir=%2Fhome%2Fcetec%2FAIProjects%2Fagui_test%2Fsrc%2Fapp&pageExtensions=tsx&pageExtensions=ts&pageExtensions=jsx&pageExtensions=js&rootDir=%2Fhome%2Fcetec%2FAIProjects%2Fagui_test&isDev=true&tsconfigPath=tsconfig.json&basePath=&assetPrefix=&nextConfigOutput=&preferredRegion=&middlewareConfig=e30%3D!\n");

/***/ }),

/***/ "(rsc)/./node_modules/next/dist/build/webpack/loaders/next-flight-client-entry-loader.js?server=true!":
/*!******************************************************************************************************!*\
  !*** ./node_modules/next/dist/build/webpack/loaders/next-flight-client-entry-loader.js?server=true! ***!
  \******************************************************************************************************/
/***/ (() => {



/***/ }),

/***/ "(rsc)/./src/app/api/copilotkit/route.ts":
/*!*****************************************!*\
  !*** ./src/app/api/copilotkit/route.ts ***!
  \*****************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   POST: () => (/* binding */ POST)\n/* harmony export */ });\n/* harmony import */ var _copilotkit_runtime__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @copilotkit/runtime */ \"(rsc)/./node_modules/@copilotkit/runtime/dist/index.js\");\n/* harmony import */ var _copilotkit_runtime__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_copilotkit_runtime__WEBPACK_IMPORTED_MODULE_0__);\n/* harmony import */ var _ag_ui_client__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @ag-ui/client */ \"(rsc)/./node_modules/@ag-ui/client/dist/index.mjs\");\n// src/app/api/copilotkit/route.ts\n\n\n// 1. Usar ExperimentalEmptyAdapter ya que solo usamos un agente\nconst serviceAdapter = new _copilotkit_runtime__WEBPACK_IMPORTED_MODULE_0__.ExperimentalEmptyAdapter();\n// 2. Crear la instancia de CopilotRuntime con AG-UI client\n//    para conectar con el agente ADK de Física\nconst runtime = new _copilotkit_runtime__WEBPACK_IMPORTED_MODULE_0__.CopilotRuntime({\n    agents: {\n        // URL del backend FastAPI con el agente de Física\n        // Se hace un cast a `any` para evitar el error de tipos causado por\n        // múltiples copias de @ag-ui/client en node_modules (tipos incompatibles).\n        \"asistente_fisica\": new _ag_ui_client__WEBPACK_IMPORTED_MODULE_1__.HttpAgent({\n            url: \"http://localhost:8001\" || 0\n        })\n    }\n});\n// 3. Construir el API route de Next.js que maneja las solicitudes de CopilotKit\nconst POST = async (req)=>{\n    const { handleRequest } = (0,_copilotkit_runtime__WEBPACK_IMPORTED_MODULE_0__.copilotRuntimeNextJSAppRouterEndpoint)({\n        runtime,\n        serviceAdapter,\n        endpoint: \"/api/copilotkit\"\n    });\n    return handleRequest(req);\n};\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHJzYykvLi9zcmMvYXBwL2FwaS9jb3BpbG90a2l0L3JvdXRlLnRzIiwibWFwcGluZ3MiOiI7Ozs7Ozs7QUFBQSxrQ0FBa0M7QUFLTDtBQUNhO0FBRzFDLGdFQUFnRTtBQUNoRSxNQUFNSSxpQkFBaUIsSUFBSUgseUVBQXdCQTtBQUVuRCwyREFBMkQ7QUFDM0QsK0NBQStDO0FBQy9DLE1BQU1JLFVBQVUsSUFBSUwsK0RBQWNBLENBQUM7SUFDakNNLFFBQVE7UUFDTixrREFBa0Q7UUFDbEQsb0VBQW9FO1FBQ3BFLDJFQUEyRTtRQUMzRSxvQkFBb0IsSUFBSUgsb0RBQVNBLENBQUM7WUFDaENJLEtBQUtDLHVCQUF1QixJQUFJLENBQXdCO1FBQzFEO0lBQ0Y7QUFDRjtBQUVBLGdGQUFnRjtBQUN6RSxNQUFNRyxPQUFPLE9BQU9DO0lBQ3pCLE1BQU0sRUFBRUMsYUFBYSxFQUFFLEdBQUdYLDBGQUFxQ0EsQ0FBQztRQUM5REc7UUFDQUQ7UUFDQVUsVUFBVTtJQUNaO0lBRUEsT0FBT0QsY0FBY0Q7QUFDdkIsRUFBRSIsInNvdXJjZXMiOlsiL2hvbWUvY2V0ZWMvQUlQcm9qZWN0cy9hZ3VpX3Rlc3Qvc3JjL2FwcC9hcGkvY29waWxvdGtpdC9yb3V0ZS50cyJdLCJzb3VyY2VzQ29udGVudCI6WyIvLyBzcmMvYXBwL2FwaS9jb3BpbG90a2l0L3JvdXRlLnRzXG5pbXBvcnQge1xuICBDb3BpbG90UnVudGltZSxcbiAgRXhwZXJpbWVudGFsRW1wdHlBZGFwdGVyLFxuICBjb3BpbG90UnVudGltZU5leHRKU0FwcFJvdXRlckVuZHBvaW50LFxufSBmcm9tIFwiQGNvcGlsb3RraXQvcnVudGltZVwiO1xuaW1wb3J0IHsgSHR0cEFnZW50IH0gZnJvbSBcIkBhZy11aS9jbGllbnRcIjtcbmltcG9ydCB7IE5leHRSZXF1ZXN0IH0gZnJvbSBcIm5leHQvc2VydmVyXCI7XG5cbi8vIDEuIFVzYXIgRXhwZXJpbWVudGFsRW1wdHlBZGFwdGVyIHlhIHF1ZSBzb2xvIHVzYW1vcyB1biBhZ2VudGVcbmNvbnN0IHNlcnZpY2VBZGFwdGVyID0gbmV3IEV4cGVyaW1lbnRhbEVtcHR5QWRhcHRlcigpO1xuXG4vLyAyLiBDcmVhciBsYSBpbnN0YW5jaWEgZGUgQ29waWxvdFJ1bnRpbWUgY29uIEFHLVVJIGNsaWVudFxuLy8gICAgcGFyYSBjb25lY3RhciBjb24gZWwgYWdlbnRlIEFESyBkZSBGw61zaWNhXG5jb25zdCBydW50aW1lID0gbmV3IENvcGlsb3RSdW50aW1lKHtcbiAgYWdlbnRzOiB7XG4gICAgLy8gVVJMIGRlbCBiYWNrZW5kIEZhc3RBUEkgY29uIGVsIGFnZW50ZSBkZSBGw61zaWNhXG4gICAgLy8gU2UgaGFjZSB1biBjYXN0IGEgYGFueWAgcGFyYSBldml0YXIgZWwgZXJyb3IgZGUgdGlwb3MgY2F1c2FkbyBwb3JcbiAgICAvLyBtw7psdGlwbGVzIGNvcGlhcyBkZSBAYWctdWkvY2xpZW50IGVuIG5vZGVfbW9kdWxlcyAodGlwb3MgaW5jb21wYXRpYmxlcykuXG4gICAgXCJhc2lzdGVudGVfZmlzaWNhXCI6IG5ldyBIdHRwQWdlbnQoe1xuICAgICAgdXJsOiBwcm9jZXNzLmVudi5CQUNLRU5EX1VSTCB8fCBcImh0dHA6Ly9sb2NhbGhvc3Q6ODAwMC9cIlxuICAgIH0pIGFzIHVua25vd24gYXMgYW55LFxuICB9XG59KTtcblxuLy8gMy4gQ29uc3RydWlyIGVsIEFQSSByb3V0ZSBkZSBOZXh0LmpzIHF1ZSBtYW5lamEgbGFzIHNvbGljaXR1ZGVzIGRlIENvcGlsb3RLaXRcbmV4cG9ydCBjb25zdCBQT1NUID0gYXN5bmMgKHJlcTogTmV4dFJlcXVlc3QpID0+IHtcbiAgY29uc3QgeyBoYW5kbGVSZXF1ZXN0IH0gPSBjb3BpbG90UnVudGltZU5leHRKU0FwcFJvdXRlckVuZHBvaW50KHtcbiAgICBydW50aW1lLFxuICAgIHNlcnZpY2VBZGFwdGVyLFxuICAgIGVuZHBvaW50OiBcIi9hcGkvY29waWxvdGtpdFwiLFxuICB9KTtcblxuICByZXR1cm4gaGFuZGxlUmVxdWVzdChyZXEpO1xufTsiXSwibmFtZXMiOlsiQ29waWxvdFJ1bnRpbWUiLCJFeHBlcmltZW50YWxFbXB0eUFkYXB0ZXIiLCJjb3BpbG90UnVudGltZU5leHRKU0FwcFJvdXRlckVuZHBvaW50IiwiSHR0cEFnZW50Iiwic2VydmljZUFkYXB0ZXIiLCJydW50aW1lIiwiYWdlbnRzIiwidXJsIiwicHJvY2VzcyIsImVudiIsIkJBQ0tFTkRfVVJMIiwiUE9TVCIsInJlcSIsImhhbmRsZVJlcXVlc3QiLCJlbmRwb2ludCJdLCJpZ25vcmVMaXN0IjpbXSwic291cmNlUm9vdCI6IiJ9\n//# sourceURL=webpack-internal:///(rsc)/./src/app/api/copilotkit/route.ts\n");

/***/ }),

/***/ "(ssr)/./node_modules/next/dist/build/webpack/loaders/next-flight-client-entry-loader.js?server=true!":
/*!******************************************************************************************************!*\
  !*** ./node_modules/next/dist/build/webpack/loaders/next-flight-client-entry-loader.js?server=true! ***!
  \******************************************************************************************************/
/***/ (() => {



/***/ }),

/***/ "../app-render/work-async-storage.external":
/*!*****************************************************************************!*\
  !*** external "next/dist/server/app-render/work-async-storage.external.js" ***!
  \*****************************************************************************/
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/server/app-render/work-async-storage.external.js");

/***/ }),

/***/ "./work-unit-async-storage.external":
/*!**********************************************************************************!*\
  !*** external "next/dist/server/app-render/work-unit-async-storage.external.js" ***!
  \**********************************************************************************/
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/server/app-render/work-unit-async-storage.external.js");

/***/ }),

/***/ "assert":
/*!*************************!*\
  !*** external "assert" ***!
  \*************************/
/***/ ((module) => {

"use strict";
module.exports = require("assert");

/***/ }),

/***/ "buffer":
/*!*************************!*\
  !*** external "buffer" ***!
  \*************************/
/***/ ((module) => {

"use strict";
module.exports = require("buffer");

/***/ }),

/***/ "child_process":
/*!********************************!*\
  !*** external "child_process" ***!
  \********************************/
/***/ ((module) => {

"use strict";
module.exports = require("child_process");

/***/ }),

/***/ "crypto":
/*!*************************!*\
  !*** external "crypto" ***!
  \*************************/
/***/ ((module) => {

"use strict";
module.exports = require("crypto");

/***/ }),

/***/ "events":
/*!*************************!*\
  !*** external "events" ***!
  \*************************/
/***/ ((module) => {

"use strict";
module.exports = require("events");

/***/ }),

/***/ "fs":
/*!*********************!*\
  !*** external "fs" ***!
  \*********************/
/***/ ((module) => {

"use strict";
module.exports = require("fs");

/***/ }),

/***/ "fs/promises":
/*!******************************!*\
  !*** external "fs/promises" ***!
  \******************************/
/***/ ((module) => {

"use strict";
module.exports = require("fs/promises");

/***/ }),

/***/ "http":
/*!***********************!*\
  !*** external "http" ***!
  \***********************/
/***/ ((module) => {

"use strict";
module.exports = require("http");

/***/ }),

/***/ "http2":
/*!************************!*\
  !*** external "http2" ***!
  \************************/
/***/ ((module) => {

"use strict";
module.exports = require("http2");

/***/ }),

/***/ "https":
/*!************************!*\
  !*** external "https" ***!
  \************************/
/***/ ((module) => {

"use strict";
module.exports = require("https");

/***/ }),

/***/ "module":
/*!*************************!*\
  !*** external "module" ***!
  \*************************/
/***/ ((module) => {

"use strict";
module.exports = require("module");

/***/ }),

/***/ "net":
/*!**********************!*\
  !*** external "net" ***!
  \**********************/
/***/ ((module) => {

"use strict";
module.exports = require("net");

/***/ }),

/***/ "next/dist/compiled/next-server/app-page.runtime.dev.js":
/*!*************************************************************************!*\
  !*** external "next/dist/compiled/next-server/app-page.runtime.dev.js" ***!
  \*************************************************************************/
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/compiled/next-server/app-page.runtime.dev.js");

/***/ }),

/***/ "next/dist/compiled/next-server/app-route.runtime.dev.js":
/*!**************************************************************************!*\
  !*** external "next/dist/compiled/next-server/app-route.runtime.dev.js" ***!
  \**************************************************************************/
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/compiled/next-server/app-route.runtime.dev.js");

/***/ }),

/***/ "node:async_hooks":
/*!***********************************!*\
  !*** external "node:async_hooks" ***!
  \***********************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:async_hooks");

/***/ }),

/***/ "node:buffer":
/*!******************************!*\
  !*** external "node:buffer" ***!
  \******************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:buffer");

/***/ }),

/***/ "node:crypto":
/*!******************************!*\
  !*** external "node:crypto" ***!
  \******************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:crypto");

/***/ }),

/***/ "node:diagnostics_channel":
/*!*******************************************!*\
  !*** external "node:diagnostics_channel" ***!
  \*******************************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:diagnostics_channel");

/***/ }),

/***/ "node:events":
/*!******************************!*\
  !*** external "node:events" ***!
  \******************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:events");

/***/ }),

/***/ "node:fs":
/*!**************************!*\
  !*** external "node:fs" ***!
  \**************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:fs");

/***/ }),

/***/ "node:fs/promises":
/*!***********************************!*\
  !*** external "node:fs/promises" ***!
  \***********************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:fs/promises");

/***/ }),

/***/ "node:http":
/*!****************************!*\
  !*** external "node:http" ***!
  \****************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:http");

/***/ }),

/***/ "node:https":
/*!*****************************!*\
  !*** external "node:https" ***!
  \*****************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:https");

/***/ }),

/***/ "node:os":
/*!**************************!*\
  !*** external "node:os" ***!
  \**************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:os");

/***/ }),

/***/ "node:path":
/*!****************************!*\
  !*** external "node:path" ***!
  \****************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:path");

/***/ }),

/***/ "node:stream":
/*!******************************!*\
  !*** external "node:stream" ***!
  \******************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:stream");

/***/ }),

/***/ "node:stream/promises":
/*!***************************************!*\
  !*** external "node:stream/promises" ***!
  \***************************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:stream/promises");

/***/ }),

/***/ "node:stream/web":
/*!**********************************!*\
  !*** external "node:stream/web" ***!
  \**********************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:stream/web");

/***/ }),

/***/ "node:tls":
/*!***************************!*\
  !*** external "node:tls" ***!
  \***************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:tls");

/***/ }),

/***/ "node:url":
/*!***************************!*\
  !*** external "node:url" ***!
  \***************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:url");

/***/ }),

/***/ "node:util":
/*!****************************!*\
  !*** external "node:util" ***!
  \****************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:util");

/***/ }),

/***/ "node:zlib":
/*!****************************!*\
  !*** external "node:zlib" ***!
  \****************************/
/***/ ((module) => {

"use strict";
module.exports = require("node:zlib");

/***/ }),

/***/ "os":
/*!*********************!*\
  !*** external "os" ***!
  \*********************/
/***/ ((module) => {

"use strict";
module.exports = require("os");

/***/ }),

/***/ "path":
/*!***********************!*\
  !*** external "path" ***!
  \***********************/
/***/ ((module) => {

"use strict";
module.exports = require("path");

/***/ }),

/***/ "process":
/*!**************************!*\
  !*** external "process" ***!
  \**************************/
/***/ ((module) => {

"use strict";
module.exports = require("process");

/***/ }),

/***/ "punycode":
/*!***************************!*\
  !*** external "punycode" ***!
  \***************************/
/***/ ((module) => {

"use strict";
module.exports = require("punycode");

/***/ }),

/***/ "querystring":
/*!******************************!*\
  !*** external "querystring" ***!
  \******************************/
/***/ ((module) => {

"use strict";
module.exports = require("querystring");

/***/ }),

/***/ "stream":
/*!*************************!*\
  !*** external "stream" ***!
  \*************************/
/***/ ((module) => {

"use strict";
module.exports = require("stream");

/***/ }),

/***/ "string_decoder":
/*!*********************************!*\
  !*** external "string_decoder" ***!
  \*********************************/
/***/ ((module) => {

"use strict";
module.exports = require("string_decoder");

/***/ }),

/***/ "tls":
/*!**********************!*\
  !*** external "tls" ***!
  \**********************/
/***/ ((module) => {

"use strict";
module.exports = require("tls");

/***/ }),

/***/ "tty":
/*!**********************!*\
  !*** external "tty" ***!
  \**********************/
/***/ ((module) => {

"use strict";
module.exports = require("tty");

/***/ }),

/***/ "url":
/*!**********************!*\
  !*** external "url" ***!
  \**********************/
/***/ ((module) => {

"use strict";
module.exports = require("url");

/***/ }),

/***/ "util":
/*!***********************!*\
  !*** external "util" ***!
  \***********************/
/***/ ((module) => {

"use strict";
module.exports = require("util");

/***/ }),

/***/ "worker_threads":
/*!*********************************!*\
  !*** external "worker_threads" ***!
  \*********************************/
/***/ ((module) => {

"use strict";
module.exports = require("worker_threads");

/***/ }),

/***/ "zlib":
/*!***********************!*\
  !*** external "zlib" ***!
  \***********************/
/***/ ((module) => {

"use strict";
module.exports = require("zlib");

/***/ })

};
;

// load runtime
var __webpack_require__ = require("../../../webpack-runtime.js");
__webpack_require__.C(exports);
var __webpack_exec__ = (moduleId) => (__webpack_require__(__webpack_require__.s = moduleId))
var __webpack_exports__ = __webpack_require__.X(0, ["vendor-chunks/@aws-sdk","vendor-chunks/@smithy","vendor-chunks/next","vendor-chunks/@copilotkit","vendor-chunks/zod","vendor-chunks/graphql","vendor-chunks/debug","vendor-chunks/untruncate-json","vendor-chunks/extend","vendor-chunks/ms","vendor-chunks/supports-color","vendor-chunks/has-flag","vendor-chunks/rxjs","vendor-chunks/@langchain","vendor-chunks/class-validator","vendor-chunks/validator","vendor-chunks/@graphql-tools","vendor-chunks/type-graphql","vendor-chunks/openai","vendor-chunks/graphql-scalars","vendor-chunks/semver","vendor-chunks/@anthropic-ai","vendor-chunks/langsmith","vendor-chunks/node-forge","vendor-chunks/@whatwg-node","vendor-chunks/@segment","vendor-chunks/libphonenumber-js","vendor-chunks/zod-to-json-schema","vendor-chunks/graphql-yoga","vendor-chunks/google-auth-library","vendor-chunks/jose","vendor-chunks/pino-pretty","vendor-chunks/readable-stream","vendor-chunks/@envelop","vendor-chunks/groq-sdk","vendor-chunks/class-transformer","vendor-chunks/@ag-ui","vendor-chunks/pino","vendor-chunks/@fastify","vendor-chunks/formdata-node","vendor-chunks/form-data-encoder","vendor-chunks/@graphql-yoga","vendor-chunks/@cfworker","vendor-chunks/pino-std-serializers","vendor-chunks/uuid","vendor-chunks/whatwg-url","vendor-chunks/jws","vendor-chunks/@aws-crypto","vendor-chunks/fast-json-patch","vendor-chunks/@bufbuild","vendor-chunks/thread-stream","vendor-chunks/gaxios","vendor-chunks/chalk","vendor-chunks/agentkeepalive","vendor-chunks/retry","vendor-chunks/p-queue","vendor-chunks/json-bigint","vendor-chunks/https-proxy-agent","vendor-chunks/color-convert","vendor-chunks/urlpattern-polyfill","vendor-chunks/langchain","vendor-chunks/yallist","vendor-chunks/tr46","vendor-chunks/partial-json","vendor-chunks/gcp-metadata","vendor-chunks/ecdsa-sig-formatter","vendor-chunks/agent-base","vendor-chunks/tslib","vendor-chunks/node-fetch","vendor-chunks/dset","vendor-chunks/@lukeed","vendor-chunks/sonic-boom","vendor-chunks/reflect-metadata","vendor-chunks/js-tiktoken","vendor-chunks/fast-copy","vendor-chunks/cross-inspect","vendor-chunks/colorette","vendor-chunks/@repeaterjs","vendor-chunks/wrappy","vendor-chunks/webidl-conversions","vendor-chunks/web-streams-polyfill","vendor-chunks/string_decoder","vendor-chunks/split2","vendor-chunks/secure-json-parse","vendor-chunks/safe-stable-stringify","vendor-chunks/safe-buffer","vendor-chunks/quick-format-unescaped","vendor-chunks/pump","vendor-chunks/process","vendor-chunks/pino-abstract-transport","vendor-chunks/p-timeout","vendor-chunks/p-retry","vendor-chunks/p-finally","vendor-chunks/once","vendor-chunks/on-exit-leak-free","vendor-chunks/node-domexception","vendor-chunks/lru-cache","vendor-chunks/jwa","vendor-chunks/is-stream","vendor-chunks/humanize-ms","vendor-chunks/gtoken","vendor-chunks/google-p12-pem","vendor-chunks/fast-text-encoding","vendor-chunks/fast-safe-stringify","vendor-chunks/eventemitter3","vendor-chunks/event-target-shim","vendor-chunks/end-of-stream","vendor-chunks/decamelize","vendor-chunks/dateformat","vendor-chunks/color-name","vendor-chunks/camelcase","vendor-chunks/buffer-equal-constant-time","vendor-chunks/bignumber.js","vendor-chunks/base64-js","vendor-chunks/atomic-sleep","vendor-chunks/arrify","vendor-chunks/ansi-styles","vendor-chunks/abort-controller","vendor-chunks/@pinojs","vendor-chunks/@aws"], () => (__webpack_exec__("(rsc)/./node_modules/next/dist/build/webpack/loaders/next-app-loader/index.js?name=app%2Fapi%2Fcopilotkit%2Froute&page=%2Fapi%2Fcopilotkit%2Froute&appPaths=&pagePath=private-next-app-dir%2Fapi%2Fcopilotkit%2Froute.ts&appDir=%2Fhome%2Fcetec%2FAIProjects%2Fagui_test%2Fsrc%2Fapp&pageExtensions=tsx&pageExtensions=ts&pageExtensions=jsx&pageExtensions=js&rootDir=%2Fhome%2Fcetec%2FAIProjects%2Fagui_test&isDev=true&tsconfigPath=tsconfig.json&basePath=&assetPrefix=&nextConfigOutput=&preferredRegion=&middlewareConfig=e30%3D!")));
module.exports = __webpack_exports__;

})();