"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    Object.defineProperty(o, k2, { enumerable: true, get: function() { return m[k]; } });
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const ask_sdk_1 = require("ask-sdk");
const sfb_skill_1 = require("@alexa-games/sfb-skill");
const path = __importStar(require("path"));
const ExtensionLoader_1 = require("./extensions/ExtensionLoader");
const projectRootPath = __dirname;
const configAccessor = new sfb_skill_1.ConfigAccessor(require(path.resolve("abcConfig", "abcConfig.json")), path.resolve(projectRootPath, 'res'));
async function handler(event, context, callback) {
    console.log(`[INFO] Request Received: ${JSON.stringify(event, null, 4)}`);
    const customExtensionLoader = new ExtensionLoader_1.ExtensionLoader({
        locale: event.request.locale,
        configAccessor
    });
    const sfbHandler = sfb_skill_1.SFBRequestHandlerFactory.create(event, context, customExtensionLoader.getExtensions(), configAccessor, projectRootPath);
    sfbHandler.canHandle = function (handlerInput) {
        return true;
    };
    const skill = ask_sdk_1.SkillBuilders.custom()
        .addRequestHandlers(sfbHandler)
        .withPersistenceAdapter(new ask_sdk_1.DynamoDbPersistenceAdapter({
        tableName: sfbHandler.getTableName(),
        createTable: true
    }))
        .withCustomUserAgent(sfb_skill_1.UserAgentHelper.createCustomUserAgent())
        .create();
    const response = await skill.invoke(event, context);
    console.log(`[INFO] Outgoing Response: ${JSON.stringify(response, null, 4)}`);
    return response;
}
exports.handler = handler;
