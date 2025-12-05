"use strict";
/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
exports.id = "vendor-chunks/@lukeed";
exports.ids = ["vendor-chunks/@lukeed"];
exports.modules = {

/***/ "(rsc)/./node_modules/@lukeed/uuid/dist/index.mjs":
/*!**************************************************!*\
  !*** ./node_modules/@lukeed/uuid/dist/index.mjs ***!
  \**************************************************/
/***/ ((__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   v4: () => (/* binding */ v4)\n/* harmony export */ });\nvar IDX=256, HEX=[], BUFFER;\nwhile (IDX--) HEX[IDX] = (IDX + 256).toString(16).substring(1);\n\nfunction v4() {\n\tvar i=0, num, out='';\n\n\tif (!BUFFER || ((IDX + 16) > 256)) {\n\t\tBUFFER = Array(i=256);\n\t\twhile (i--) BUFFER[i] = 256 * Math.random() | 0;\n\t\ti = IDX = 0;\n\t}\n\n\tfor (; i < 16; i++) {\n\t\tnum = BUFFER[IDX + i];\n\t\tif (i==6) out += HEX[num & 15 | 64];\n\t\telse if (i==8) out += HEX[num & 63 | 128];\n\t\telse out += HEX[num];\n\n\t\tif (i & 1 && i > 1 && i < 11) out += '-';\n\t}\n\n\tIDX++;\n\treturn out;\n}\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHJzYykvLi9ub2RlX21vZHVsZXMvQGx1a2VlZC91dWlkL2Rpc3QvaW5kZXgubWpzIiwibWFwcGluZ3MiOiI7Ozs7QUFBQTtBQUNBOztBQUVPO0FBQ1A7O0FBRUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QUFFQSxRQUFRLFFBQVE7QUFDaEI7QUFDQTtBQUNBO0FBQ0E7O0FBRUE7QUFDQTs7QUFFQTtBQUNBO0FBQ0EiLCJzb3VyY2VzIjpbIi9tZWRpYS9kcmFjZXJvLzA4YzY3NjU0LTZlZDctNDcyNS1iNzRlLTUwZjI5ZWE2MGNiMi9Ob2RlUHJvamVjdHMvYWd1aV90ZXN0L25vZGVfbW9kdWxlcy9AbHVrZWVkL3V1aWQvZGlzdC9pbmRleC5tanMiXSwic291cmNlc0NvbnRlbnQiOlsidmFyIElEWD0yNTYsIEhFWD1bXSwgQlVGRkVSO1xud2hpbGUgKElEWC0tKSBIRVhbSURYXSA9IChJRFggKyAyNTYpLnRvU3RyaW5nKDE2KS5zdWJzdHJpbmcoMSk7XG5cbmV4cG9ydCBmdW5jdGlvbiB2NCgpIHtcblx0dmFyIGk9MCwgbnVtLCBvdXQ9Jyc7XG5cblx0aWYgKCFCVUZGRVIgfHwgKChJRFggKyAxNikgPiAyNTYpKSB7XG5cdFx0QlVGRkVSID0gQXJyYXkoaT0yNTYpO1xuXHRcdHdoaWxlIChpLS0pIEJVRkZFUltpXSA9IDI1NiAqIE1hdGgucmFuZG9tKCkgfCAwO1xuXHRcdGkgPSBJRFggPSAwO1xuXHR9XG5cblx0Zm9yICg7IGkgPCAxNjsgaSsrKSB7XG5cdFx0bnVtID0gQlVGRkVSW0lEWCArIGldO1xuXHRcdGlmIChpPT02KSBvdXQgKz0gSEVYW251bSAmIDE1IHwgNjRdO1xuXHRcdGVsc2UgaWYgKGk9PTgpIG91dCArPSBIRVhbbnVtICYgNjMgfCAxMjhdO1xuXHRcdGVsc2Ugb3V0ICs9IEhFWFtudW1dO1xuXG5cdFx0aWYgKGkgJiAxICYmIGkgPiAxICYmIGkgPCAxMSkgb3V0ICs9ICctJztcblx0fVxuXG5cdElEWCsrO1xuXHRyZXR1cm4gb3V0O1xufVxuIl0sIm5hbWVzIjpbXSwiaWdub3JlTGlzdCI6WzBdLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///(rsc)/./node_modules/@lukeed/uuid/dist/index.mjs\n");

/***/ })

};
;