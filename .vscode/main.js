/// <reference path="/home/codespace/.vscode-remote/extensions/nur.script-0.2.1/@types/api.global.d.ts" />
/// <reference path="/home/codespace/.vscode-remote/extensions/nur.script-0.2.1/@types/vscode.global.d.ts" />
//  @ts-check
//  API: https://code.visualstudio.com/api/references/vscode-api

function activate(_context) {
   window.showInformationMessage('Hello, World!');
}

function deactivate() {}

module.exports = { activate, deactivate }
