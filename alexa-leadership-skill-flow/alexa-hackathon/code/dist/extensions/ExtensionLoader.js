"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ExtensionLoader = void 0;
const SampleCustomExtension_1 = require("./SampleCustomExtension");
const sfb_skill_1 = require("@alexa-games/sfb-skill");
class ExtensionLoader {
    constructor(param) {
        this.registeredExtensions = [
            new sfb_skill_1.AlexaExtension(),
            new sfb_skill_1.AlexaAPLExtension(param.locale, param.configAccessor),
            new sfb_skill_1.AlexaAudioPlayerExtension(param.locale, param.configAccessor),
            new sfb_skill_1.AlexaMonetizationExtension(param.locale, param.configAccessor),
            new SampleCustomExtension_1.SampleCustomExtension()
        ];
    }
    getExtensions() {
        return this.registeredExtensions;
    }
}
exports.ExtensionLoader = ExtensionLoader;
