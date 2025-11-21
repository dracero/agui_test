"use strict";
/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
exports.id = "vendor-chunks/is-alphanumerical";
exports.ids = ["vendor-chunks/is-alphanumerical"];
exports.modules = {

/***/ "(ssr)/./node_modules/is-alphanumerical/index.js":
/*!*************************************************!*\
  !*** ./node_modules/is-alphanumerical/index.js ***!
  \*************************************************/
/***/ ((module, __unused_webpack_exports, __webpack_require__) => {

eval("\n\nvar alphabetical = __webpack_require__(/*! is-alphabetical */ \"(ssr)/./node_modules/is-alphabetical/index.js\")\nvar decimal = __webpack_require__(/*! is-decimal */ \"(ssr)/./node_modules/is-decimal/index.js\")\n\nmodule.exports = alphanumerical\n\n// Check if the given character code, or the character code at the first\n// character, is alphanumerical.\nfunction alphanumerical(character) {\n  return alphabetical(character) || decimal(character)\n}\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHNzcikvLi9ub2RlX21vZHVsZXMvaXMtYWxwaGFudW1lcmljYWwvaW5kZXguanMiLCJtYXBwaW5ncyI6IkFBQVk7O0FBRVosbUJBQW1CLG1CQUFPLENBQUMsc0VBQWlCO0FBQzVDLGNBQWMsbUJBQU8sQ0FBQyw0REFBWTs7QUFFbEM7O0FBRUE7QUFDQTtBQUNBO0FBQ0E7QUFDQSIsInNvdXJjZXMiOlsiL21lZGlhL2RyYWNlcm8vMDhjNjc2NTQtNmVkNy00NzI1LWI3NGUtNTBmMjllYTYwY2IyL05vZGVQcm9qZWN0cy9hZ3VpX3Rlc3Qvbm9kZV9tb2R1bGVzL2lzLWFscGhhbnVtZXJpY2FsL2luZGV4LmpzIl0sInNvdXJjZXNDb250ZW50IjpbIid1c2Ugc3RyaWN0J1xuXG52YXIgYWxwaGFiZXRpY2FsID0gcmVxdWlyZSgnaXMtYWxwaGFiZXRpY2FsJylcbnZhciBkZWNpbWFsID0gcmVxdWlyZSgnaXMtZGVjaW1hbCcpXG5cbm1vZHVsZS5leHBvcnRzID0gYWxwaGFudW1lcmljYWxcblxuLy8gQ2hlY2sgaWYgdGhlIGdpdmVuIGNoYXJhY3RlciBjb2RlLCBvciB0aGUgY2hhcmFjdGVyIGNvZGUgYXQgdGhlIGZpcnN0XG4vLyBjaGFyYWN0ZXIsIGlzIGFscGhhbnVtZXJpY2FsLlxuZnVuY3Rpb24gYWxwaGFudW1lcmljYWwoY2hhcmFjdGVyKSB7XG4gIHJldHVybiBhbHBoYWJldGljYWwoY2hhcmFjdGVyKSB8fCBkZWNpbWFsKGNoYXJhY3Rlcilcbn1cbiJdLCJuYW1lcyI6W10sImlnbm9yZUxpc3QiOlswXSwic291cmNlUm9vdCI6IiJ9\n//# sourceURL=webpack-internal:///(ssr)/./node_modules/is-alphanumerical/index.js\n");

/***/ })

};
;